from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from polybot.long_run import run_long_run
from polybot.market_data import CaptureRecord, capture_btc_reference, write_jsonl
from polybot.market_discovery import GAMMA_EVENTS_URL
from polybot.market_discovery import discover_session, fetch_json, select_session
from polybot.open_price import POLYMARKET_CHAINLINK_SOURCE, chainlink_price_record, enrich_session_config
from polybot.paper_runner import parse_datetime, run_session_once
from polybot.resolution_ingestion import GAMMA_MARKETS_URL, extract_market, ingest_metadata
from polybot.runtime_config import configured_move_threshold_pct
from polybot.run_artifacts import build_run_artifacts, read_json, write_json
from polybot.signal import Signal
from polybot.supervisor_results import batch_close
from polybot.trade_ledger import DEFAULT_LEDGER_PATH, equity_fraction_stake, record_result, rows as ledger_rows, upsert_trade


BEIJING_TZ = timezone(timedelta(hours=8), "CST")
ET_TZ = ZoneInfo("America/New_York")
BEIJING_DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def records_to_jsonl(path: Path, records: list[CaptureRecord]) -> None:
    path.write_text("", encoding="utf-8")
    if records:
        write_jsonl(path, records)


def beijing_day_text(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(BEIJING_TZ).date().isoformat()


def next_beijing_midnight(value: datetime | None = None) -> datetime:
    local = (value or datetime.now(timezone.utc)).astimezone(BEIJING_TZ)
    tomorrow = local.date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=BEIJING_TZ).astimezone(timezone.utc)


def is_daily_run_dir(path: Path) -> bool:
    return bool(BEIJING_DAY_RE.fullmatch(path.name))


def resolve_run_dir(path: Path | None, now: datetime | None = None) -> Path:
    if path is not None:
        return path
    return Path("runs/paper-btc-15m") / beijing_day_text(now)


def update_latest_run_pointers(run_dir: Path) -> None:
    if run_dir.parent.name != "paper-btc-15m":
        return
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    (run_dir.parent / "latest_run_dir.txt").write_text(str(run_dir) + "\n", encoding="utf-8")
    latest = run_dir.parent / "latest"
    tmp = run_dir.parent / ".latest.tmp"
    if tmp.exists() or tmp.is_symlink():
        tmp.unlink()
    tmp.symlink_to(run_dir.name, target_is_directory=True)
    os.replace(tmp, latest)


DEFAULT_CONFIG: dict[str, Any] = {
    "strategy": {
        "market_type": "btc_up_down_15m",
        "observe_start_remaining_seconds": 300,
        "move_threshold_pct": configured_move_threshold_pct(),
        "max_entries_per_market": 1,
    },
    "paper": {"stake": None, "stake_fraction": 0.05, "initial_bankroll": 1000.0, "ledger_path": str(DEFAULT_LEDGER_PATH)},
    "marketability": {"p_hat_filter_enabled": True, "p_hat": 0.55},
    "discovery": {
        "search_query": "bitcoin up down 15m",
        "mode": "next",
        "max_pages": 10,
        "limit": 100,
        "lookahead_minutes": 90,
    },
    "timing": {
        "max_wait_to_open_seconds": 900.0,
        "max_wait_to_observation_seconds": 900.0,
        "max_open_price_delay_seconds": 5.0,
    },
    "capture": {
        "open_price_seconds": 8.0,
        "capture_limit": 5,
        "observation_tick_seconds": 1.0,
        "runner_seconds": 8.0,
    },
    "runtime": {
        "max_sessions": 96,
        "max_runtime_seconds": 90000.0,
        "retry_limit": 1,
        "retry_backoff_seconds": 5.0,
        "heartbeat_interval_seconds": 30.0,
    },
    "operator_output": {"enabled": True, "format": "text"},
}


CONFIG_ARG_MAP = {
    "search_query": ("discovery", "search_query"),
    "mode": ("discovery", "mode"),
    "max_pages": ("discovery", "max_pages"),
    "limit": ("discovery", "limit"),
    "lookahead_minutes": ("discovery", "lookahead_minutes"),
    "max_wait_to_open_seconds": ("timing", "max_wait_to_open_seconds"),
    "max_wait_to_observation_seconds": ("timing", "max_wait_to_observation_seconds"),
    "max_open_price_delay_seconds": ("timing", "max_open_price_delay_seconds"),
    "capture_seconds": ("capture", "open_price_seconds"),
    "capture_limit": ("capture", "capture_limit"),
    "observation_tick_seconds": ("capture", "observation_tick_seconds"),
    "runner_seconds": ("capture", "runner_seconds"),
    "max_sessions": ("runtime", "max_sessions"),
    "max_runtime_seconds": ("runtime", "max_runtime_seconds"),
    "retry_limit": ("runtime", "retry_limit"),
    "retry_backoff_seconds": ("runtime", "retry_backoff_seconds"),
    "heartbeat_interval_seconds": ("runtime", "heartbeat_interval_seconds"),
    "paper_stake": ("paper", "stake"),
    "stake_fraction": ("paper", "stake_fraction"),
    "initial_bankroll": ("paper", "initial_bankroll"),
    "ledger_path": ("paper", "ledger_path"),
    "p_hat": ("marketability", "p_hat"),
    "p_hat_filter_enabled": ("marketability", "p_hat_filter_enabled"),
    "move_threshold_pct": ("strategy", "move_threshold_pct"),
    "observe_start_remaining_seconds": ("strategy", "observe_start_remaining_seconds"),
    "operator_output_enabled": ("operator_output", "enabled"),
}


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return merge_config(DEFAULT_CONFIG, {})
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise SystemExit("PyYAML is required for --config; install requirements.txt") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("config must be a YAML mapping")
    return merge_config(DEFAULT_CONFIG, data)


def apply_config(args: argparse.Namespace) -> argparse.Namespace:
    config = load_config(args.config)
    for arg_name, path in CONFIG_ARG_MAP.items():
        value = getattr(args, arg_name)
        if value is not None:
            section, key = path
            config[section][key] = str(value) if isinstance(value, Path) else value

    validate_config(config)
    args.effective_config = config
    args.search_query = config["discovery"]["search_query"]
    args.mode = config["discovery"]["mode"]
    args.max_pages = int(config["discovery"]["max_pages"])
    args.limit = int(config["discovery"]["limit"])
    args.lookahead_minutes = int(config["discovery"]["lookahead_minutes"])
    args.max_wait_to_open_seconds = float(config["timing"]["max_wait_to_open_seconds"])
    args.max_wait_to_observation_seconds = float(config["timing"]["max_wait_to_observation_seconds"])
    args.max_open_price_delay_seconds = float(config["timing"]["max_open_price_delay_seconds"])
    args.capture_seconds = float(config["capture"]["open_price_seconds"])
    args.capture_limit = int(config["capture"]["capture_limit"])
    args.observation_tick_seconds = float(config["capture"]["observation_tick_seconds"])
    args.runner_seconds = float(config["capture"]["runner_seconds"])
    args.max_sessions = int(config["runtime"]["max_sessions"])
    args.max_runtime_seconds = float(config["runtime"]["max_runtime_seconds"])
    args.retry_limit = int(config["runtime"]["retry_limit"])
    args.retry_backoff_seconds = float(config["runtime"]["retry_backoff_seconds"])
    args.heartbeat_interval_seconds = float(config["runtime"]["heartbeat_interval_seconds"])
    args.paper_stake = None if config["paper"]["stake"] is None else float(config["paper"]["stake"])
    args.stake_fraction = float(config["paper"]["stake_fraction"])
    args.initial_bankroll = float(config["paper"]["initial_bankroll"])
    args.ledger_path = Path(config["paper"]["ledger_path"])
    args.p_hat = None if config["marketability"]["p_hat"] is None else float(config["marketability"]["p_hat"])
    args.p_hat_filter_enabled = bool(config["marketability"]["p_hat_filter_enabled"])
    args.move_threshold_pct = float(config["strategy"]["move_threshold_pct"])
    args.observe_start_remaining_seconds = int(config["strategy"]["observe_start_remaining_seconds"])
    args.max_entries_per_market = int(config["strategy"]["max_entries_per_market"])
    args.operator_output_enabled = bool(config["operator_output"]["enabled"])
    args.config_snapshot = config
    return args


def validate_config(config: dict[str, Any]) -> None:
    checks = [
        (config["paper"]["stake"] is None or float(config["paper"]["stake"]) > 0, "paper.stake must be > 0 when set"),
        (float(config["paper"]["stake_fraction"]) > 0, "paper.stake_fraction must be > 0"),
        (float(config["paper"]["initial_bankroll"]) > 0, "paper.initial_bankroll must be > 0"),
        (float(config["strategy"]["move_threshold_pct"]) >= 0, "strategy.move_threshold_pct must be >= 0"),
        (int(config["strategy"]["observe_start_remaining_seconds"]) > 0, "strategy.observe_start_remaining_seconds must be > 0"),
        (int(config["strategy"]["max_entries_per_market"]) == 1, "strategy.max_entries_per_market must be 1"),
        (float(config["timing"]["max_wait_to_open_seconds"]) >= 0, "timing.max_wait_to_open_seconds must be >= 0"),
        (float(config["timing"]["max_wait_to_observation_seconds"]) >= 0, "timing.max_wait_to_observation_seconds must be >= 0"),
        (float(config["timing"]["max_open_price_delay_seconds"]) >= 0, "timing.max_open_price_delay_seconds must be >= 0"),
        (float(config["capture"]["open_price_seconds"]) >= 0, "capture.open_price_seconds must be >= 0"),
        (int(config["capture"]["capture_limit"]) >= 0, "capture.capture_limit must be >= 0"),
        (float(config["capture"]["observation_tick_seconds"]) >= 0, "capture.observation_tick_seconds must be >= 0"),
        (float(config["capture"]["runner_seconds"]) >= 0, "capture.runner_seconds must be >= 0"),
        (int(config["runtime"]["max_sessions"]) > 0, "runtime.max_sessions must be > 0"),
        (float(config["runtime"]["max_runtime_seconds"]) >= 0, "runtime.max_runtime_seconds must be >= 0"),
        (int(config["runtime"]["retry_limit"]) >= 0, "runtime.retry_limit must be >= 0"),
        (float(config["runtime"]["retry_backoff_seconds"]) >= 0, "runtime.retry_backoff_seconds must be >= 0"),
        (float(config["runtime"]["heartbeat_interval_seconds"]) >= 0, "runtime.heartbeat_interval_seconds must be >= 0"),
    ]
    if config["marketability"]["p_hat_filter_enabled"]:
        p_hat = config["marketability"]["p_hat"]
        checks.append((p_hat is not None and 0 <= float(p_hat) <= 1, "marketability.p_hat must be between 0 and 1 when filter is enabled"))
    for ok, message in checks:
        if not ok:
            raise SystemExit(message)


def load_public_payload(args: argparse.Namespace) -> tuple[Any, str | None, str]:
    if args.input_json:
        return json.loads(args.input_json.read_text(encoding="utf-8")), None, str(args.input_json)
    return None, None, args.source_url or "documented_public_discovery_sources"


def skipped_batch(supervisor_jsonl: Path, session: dict[str, Any], reason: str) -> dict[str, Any]:
    append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": session, "skip_reason": reason})
    return batch_close(supervisor_jsonl, {})


def append_downstream_skips(report: dict[str, Any], reason: str) -> None:
    for step in ("open_price", "signal", "paper_runner", "result_closing"):
        report["steps"].append({"step": step, "status": "skipped", "reason": f"not_reached_after_{reason}"})
    report["steps"].append({"step": "resolution", "status": "pending", "reason": f"not_reached_after_{reason}"})


def session_meta(session: dict[str, Any]) -> dict[str, Any]:
    return {key: session.get(key) for key in ("market_id", "market_slug", "market_start_time", "market_end_time")}


def resolution_url(session: dict[str, Any]) -> str:
    return f"{GAMMA_EVENTS_URL}?{urlencode({'limit': 1, 'slug': session.get('market_slug') or session.get('market_id')})}"


def market_resolution_url(market_id: str) -> str:
    return f"{GAMMA_MARKETS_URL}?{urlencode({'limit': 1, 'id': market_id})}"


def safe_artifact_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:120] or "unknown"


def paper_stake_for_session(args: argparse.Namespace) -> float:
    if args.paper_stake is not None:
        return args.paper_stake
    return equity_fraction_stake(args.ledger_path, args.initial_bankroll, args.stake_fraction)


def extract_resolution_market(payload: Any, session: dict[str, Any]) -> dict[str, Any]:
    market_id = str(session.get("market_id") or "")
    market_slug = str(session.get("market_slug") or "")
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    events = data if isinstance(data, list) else [data]
    matches: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        for market in event.get("markets", []):
            if isinstance(market, dict) and (str(market.get("id")) == market_id or str(market.get("slug")) == market_slug):
                matches.append(market)
    if len(matches) == 1:
        return matches[0]
    return extract_market(payload)


def pending_ledger_resolution_retry(args: argparse.Namespace, source_dir: Path, fetcher: Any = fetch_json) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    resolved = 0
    still_pending = 0
    skipped = 0
    for row in ledger_rows(args.ledger_path):
        if row.get("result") != "PENDING":
            continue
        market_id = str(row.get("market_id") or "")
        if not market_id:
            continue
        safe_id = safe_artifact_name(market_id)
        raw_path = source_dir / f"pending_resolution_raw_{safe_id}.json"
        resolution_path = source_dir / f"pending_resolution_{safe_id}.json"
        step = {"step": "pending_resolution_retry", "market_id": market_id}
        try:
            payload, source_timestamp = fetcher(market_resolution_url(market_id))
            market = extract_market(payload)
            write_json(raw_path, market)
            resolution_summary = ingest_metadata(market)
            write_json(resolution_path, resolution_summary)
            winning_side = resolution_summary["resolutions"].get(market_id)
            if winning_side and row.get("side") in (Signal.UP.value, Signal.DOWN.value) and row.get("stake") is not None and row.get("shares") is not None:
                stake = float(row["stake"])
                shares = float(row["shares"])
                pnl = shares - stake if row["side"] == winning_side else -stake
                result = "WIN" if pnl > 0 else "LOSS"
                stats = record_result(args.ledger_path, market_id, result, args.initial_bankroll, winning_side=winning_side, paper_pnl=pnl)
                attempts.append({**step, "status": "resolved", "result": result, "winning_side": winning_side, "paper_pnl": pnl, "equity_after": stats["equity_after"], "resolution_path": str(resolution_path), "raw_resolution_path": str(raw_path), "source_timestamp": source_timestamp})
                resolved += 1
                continue
            if winning_side:
                reason = "missing_opened_trade_fields"
            else:
                reason = resolution_summary["skipped"][0].get("skip_reason", "resolution_skipped")
            upsert_trade(args.ledger_path, market_id=market_id, result="PENDING", skip_reason=reason)
            status = "pending" if reason in ("not_closed", "unresolved_resolution_status") else "skipped"
            attempts.append({**step, "status": status, "reason": reason, "resolution_path": str(resolution_path), "raw_resolution_path": str(raw_path), "source_timestamp": source_timestamp})
            if status == "pending":
                still_pending += 1
            else:
                skipped += 1
        except Exception as exc:
            reason = f"public_resolution_blocked={type(exc).__name__}: {exc}"
            attempts.append({**step, "status": "blocker", "reason": reason})
            still_pending += 1
    return {"attempts": attempts, "resolved": resolved, "pending": still_pending, "skipped": skipped}


def precise_resolution_summary(summary: dict[str, Any], resolution_skips: dict[str, str]) -> dict[str, Any]:
    if not resolution_skips:
        return summary
    skipped_reasons: dict[str, int] = {}
    for item in summary.get("per_session", []):
        if item.get("status") != "skipped":
            continue
        market_id = str((item.get("session") or {}).get("market_id"))
        if market_id in resolution_skips:
            item["skip_reason"] = resolution_skips[market_id]
        reason = item.get("skip_reason", "skipped")
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
    summary["skipped_reasons"] = skipped_reasons
    return summary


def attempt_public_resolutions(report: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    resolution_map: dict[str, str] = {}
    resolution_paths: dict[str, Path] = {}
    raw_resolution_paths: dict[str, Path] = {}
    resolution_skips: dict[str, str] = {}
    attempts: list[dict[str, Any]] = []

    for session_report in report.get("sessions", []):
        if session_report.get("status") != "completed" or not session_report.get("runner_output"):
            continue
        index = int(session_report["session_index"])
        session = session_report["session"]
        market_id = str(session.get("market_id") or "")
        step = {"step": "resolution", "session_index": index, "session": session_meta(session)}
        if not market_id:
            reason = "missing_market_id"
            resolution_skips[market_id] = reason
            attempts.append({**step, "status": "skipped", "reason": reason})
            continue

        raw_path = source_dir / f"resolution_raw_{index}_{market_id}.json"
        resolution_path = source_dir / f"resolution_{index}_{market_id}.json"
        try:
            payload, source_timestamp = fetch_json(resolution_url(session))
            market = extract_resolution_market(payload, session)
            write_json(raw_path, market)
            resolution_summary = ingest_metadata(market)
            write_json(resolution_path, resolution_summary)
            raw_resolution_paths[market_id] = raw_path
            resolution_paths[market_id] = resolution_path
            if resolution_summary["resolutions"]:
                resolution_map.update(resolution_summary["resolutions"])
                attempts.append({**step, "status": "resolved", "resolution_path": str(resolution_path), "raw_resolution_path": str(raw_path), "source_timestamp": source_timestamp})
            else:
                reason = resolution_summary["skipped"][0].get("skip_reason", "resolution_skipped")
                resolution_skips[market_id] = reason
                status = "pending" if reason in ("not_closed", "unresolved_resolution_status") else "skipped"
                attempts.append({**step, "status": status, "reason": reason, "resolution_path": str(resolution_path), "raw_resolution_path": str(raw_path), "source_timestamp": source_timestamp})
        except Exception as exc:
            reason = f"public_resolution_blocked={type(exc).__name__}: {exc}"
            resolution_skips[market_id] = reason
            attempts.append({**step, "status": "blocker", "reason": reason})

    return {
        "resolutions": resolution_map,
        "resolution_paths": resolution_paths,
        "raw_resolution_paths": raw_resolution_paths,
        "resolution_skips": resolution_skips,
        "attempts": attempts,
    }


async def wait_to_open(session: dict[str, Any], max_wait_seconds: float) -> dict[str, Any]:
    start = parse_datetime(session["market_start_time"])
    now = datetime.now(timezone.utc)
    wait_seconds = (start - now).total_seconds()
    step = {
        "step": "wait_to_open",
        "session_start": start.isoformat(),
        "local_timestamp": now.isoformat(),
        "wait_seconds": wait_seconds,
        "max_wait_seconds": max_wait_seconds,
    }
    if wait_seconds > max_wait_seconds:
        return {**step, "status": "skipped", "reason": "wait_to_open_budget_exceeded"}
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
        return {**step, "status": "success"}
    return {**step, "status": "no_wait_needed"}


async def wait_to_observation(
    session: dict[str, Any],
    observe_start_remaining_seconds: int,
    max_wait_seconds: float,
) -> dict[str, Any]:
    end = parse_datetime(session["market_end_time"])
    observation_at = end - timedelta(seconds=observe_start_remaining_seconds)
    now = datetime.now(timezone.utc)
    wait_seconds = max((observation_at - now).total_seconds(), 0.0)
    step = {
        "step": "wait_to_observation",
        "local_timestamp": now.isoformat(),
        "observation_timestamp": observation_at.isoformat(),
        "observe_start_remaining_seconds": observe_start_remaining_seconds,
        "max_wait_seconds": max_wait_seconds,
        "wait_seconds": wait_seconds,
    }
    if now > end:
        return {**step, "status": "skipped", "reason": "observation_window_missed"}
    if wait_seconds > max_wait_seconds:
        return {**step, "status": "skipped", "reason": "wait_to_observation_budget_exceeded"}
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
        return {**step, "status": "success"}
    return {**step, "status": "no_wait_needed"}


def operator_print(args: argparse.Namespace, message: str) -> None:
    if args.operator_output_enabled:
        print(f"[{beijing_time_text()}] {message}", flush=True)


def fmt(value: Any) -> str:
    return "None" if value is None else str(value)


def fmt_money(value: Any) -> str:
    try:
        return f"{float(value):+.2f}"
    except (TypeError, ValueError):
        return "None"


def fmt_amount(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "None"


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value):.3f}%"
    except (TypeError, ValueError):
        return "None"


def fmt_minutes(value: Any) -> str:
    try:
        return f"{float(value) / 60:.1f}m"
    except (TypeError, ValueError):
        return "None"


def beijing_time_text(value: datetime | None = None) -> str:
    dt = value or datetime.now(timezone.utc)
    return dt.astimezone(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def operator_time(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, datetime):
        return beijing_time_text(value)
    if isinstance(value, str):
        try:
            return beijing_time_text(parse_datetime(value))
        except ValueError:
            return value
    return str(value)


def session_window_text(session: dict[str, Any]) -> str:
    try:
        start = parse_datetime(str(session.get("market_start_time"))).astimezone(ET_TZ)
        end = parse_datetime(str(session.get("market_end_time"))).astimezone(ET_TZ)
    except (TypeError, ValueError):
        return "unknown_window"
    if start.date() == end.date():
        return f"{start:%H:%M}-{end:%H:%M} ET"
    return f"{start:%Y-%m-%d %H:%M}-{end:%Y-%m-%d %H:%M} ET"


def watch_line(session: dict[str, Any]) -> str:
    return f"[WATCH] {session_window_text(session)}"


def open_line(session: dict[str, Any], price: Any, source: Any) -> str:
    return f"[OPEN] {session_window_text(session)} price={fmt_amount(price)} source={fmt(source)}"


def bet_line(side: Any, move: Any, remaining_seconds: Any, avg: Any, stake: Any) -> str:
    return f"[BET] {fmt(side)} move={fmt_pct(move)} remaining={fmt_minutes(remaining_seconds)} avg={fmt_amount(avg)} stake={fmt_amount(stake)}"


def no_bet_line(reason: Any, move: Any = None) -> str:
    if reason in ("no_signal", "observation_window_no_signal"):
        return "[NO_BET] no trigger; next market"
    suffix = "" if move is None else f" move={fmt_pct(move)}"
    return f"[NO_BET] {fmt(reason)}{suffix}"


def settled_line(side: Any, result: str, pnl: Any, equity: Any) -> str:
    return f"[SETTLED] {result} pnl={fmt_money(pnl)}"


def pending_line(reason: Any) -> str:
    return "[PENDING] awaiting settlement"


def market_slug(session: dict[str, Any]) -> str:
    return str(session.get("market_slug") or session.get("market_id") or "unknown")


def ledger_row(args: argparse.Namespace, market_id: str) -> dict[str, Any]:
    return next((row for row in ledger_rows(args.ledger_path) if row.get("market_id") == market_id), {})


def current_report_market_ids(report: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for session_report in report.get("sessions", []):
        market_id = (session_report.get("session") or {}).get("market_id")
        if market_id:
            ids.add(str(market_id))
    return ids


def emit_market_results(args: argparse.Namespace, summary: dict[str, Any], allowed_market_ids: set[str] | None = None) -> None:
    emitted = getattr(args, "_emitted_result_keys", set())
    for item in summary.get("per_session", []):
        session = item.get("session") or {}
        market_id = str(session.get("market_id") or "")
        if not market_id:
            continue
        if allowed_market_ids is not None and market_id not in allowed_market_ids:
            continue
        reason = item.get("skip_reason")
        result_key = (market_id, item.get("status"), item.get("winning_side"), reason)
        if result_key in emitted:
            continue
        emitted.add(result_key)
        row = ledger_row(args, market_id)
        if item.get("status") == "closed":
            paper_pnl = (item.get("summary", {}).get("tradable_signal", {}).get("paper_pnl") or [])
            first = paper_pnl[0] if paper_pnl else {}
            pnl = first.get("paper_pnl", 0)
            result = "WIN" if pnl > 0 else "LOSS" if paper_pnl else "SKIPPED"
            stats = record_result(args.ledger_path, market_id, result, args.initial_bankroll, winning_side=item.get("winning_side"), paper_pnl=pnl)
            operator_print(args, settled_line(first.get("signal") or row.get("side"), result, pnl, stats["equity_after"]))
            continue
        result = "PENDING" if reason in ("missing_resolution", "not_closed") else "SKIPPED"
        if reason == "observation_window_no_signal":
            result = "NO_TRADE"
        stats = record_result(args.ledger_path, market_id, result, args.initial_bankroll, skip_reason=reason)
        if result == "PENDING":
            operator_print(args, pending_line(reason))
        elif result in ("NO_TRADE", "SKIPPED"):
            operator_print(args, no_bet_line(reason))
    args._emitted_result_keys = emitted


async def process_session(
    args: argparse.Namespace,
    session: dict[str, Any],
    source_dir: Path,
    supervisor_jsonl: Path,
    index: int,
    remaining_runtime_seconds: float,
) -> dict[str, Any]:
    meta = session_meta(session)
    session_report: dict[str, Any] = {"session_index": index, "session": meta, "steps": [], "runner_output": None, "status": "attempted"}
    market_id = str(session.get("market_id") or "")
    session_stake = paper_stake_for_session(args)
    operator_print(args, watch_line(session))
    if market_id:
        upsert_trade(
            args.ledger_path,
            market_id=market_id,
            market_start_time=session.get("market_start_time"),
            market_end_time=session.get("market_end_time"),
            threshold_pct=args.move_threshold_pct,
            observe_start_remaining_seconds=args.observe_start_remaining_seconds,
            stake=session_stake,
            result="PENDING",
        )

    wait_step = await wait_to_open(session, min(args.max_wait_to_open_seconds, max(0.0, remaining_runtime_seconds)))
    session_report["steps"].append(wait_step)
    if wait_step["status"] == "skipped":
        reason = wait_step["reason"]
        session_report["steps"].append({"step": "btc_reference_capture", "status": "skipped", "reason": f"not_reached_after_{reason}"})
        session_report["steps"].append({"step": "open_price", "status": "skipped", "reason": f"not_reached_after_{reason}"})
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "skip_reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        if market_id:
            record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=reason)
        operator_print(args, no_bet_line(reason))
        return session_report

    btc_records: list[CaptureRecord] = []
    try:
        btc_records = await capture_btc_reference(args.capture_seconds, args.capture_limit)
        records_to_jsonl(source_dir / f"btc_reference_{index}.jsonl", btc_records)
        session_report["steps"].append({"step": "btc_reference_capture", "status": "success" if btc_records else "skipped", "record_count": len(btc_records)})
    except Exception as exc:
        session_report["steps"].append({"step": "btc_reference_capture", "status": "blocker", "reason": f"{type(exc).__name__}: {exc}"})

    enriched = enrich_session_config({"selection": session}, btc_records, args.max_open_price_delay_seconds)
    if enriched.get("raw_payload") is not None:
        write_json(source_dir / f"chainlink_reference_{index}.json", {"payload": enriched["raw_payload"]})
    if enriched.get("skip_reason"):
        reason = enriched["skip_reason"]
        session_report["steps"].append({"step": "open_price", "status": "skipped", "reason": reason})
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "skip_reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        if market_id:
            record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=reason)
        operator_print(args, no_bet_line(reason))
        return session_report

    enriched_session = enriched["selection"]
    if market_id:
        upsert_trade(
            args.ledger_path,
            market_id=market_id,
            open_price=enriched_session.get("open_price"),
            open_price_source=enriched_session.get("open_price_source"),
        )
    session_report["steps"].append({"step": "open_price", "status": "captured", "open_price": enriched_session["open_price"], "open_price_timestamp": enriched_session["open_price_timestamp"]})
    operator_print(args, open_line(enriched_session, enriched_session["open_price"], enriched_session["open_price_source"]))
    runner_output = source_dir / f"runner_{index}.jsonl"
    runner_output.write_text("", encoding="utf-8")
    session_report["runner_output"] = str(runner_output)

    observation_step = await wait_to_observation(
        enriched_session,
        args.observe_start_remaining_seconds,
        min(args.max_wait_to_observation_seconds, max(0.0, remaining_runtime_seconds)),
    )
    session_report["steps"].append(observation_step)
    if observation_step["status"] == "skipped":
        reason = observation_step["reason"]
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
        session_report["steps"].append({"step": "paper_runner", "status": "skipped", "runner_output": str(runner_output), "reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        if market_id:
            record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=reason)
        operator_print(args, no_bet_line(reason))
        return session_report
    end = parse_datetime(enriched_session["market_end_time"])
    observation_checks = 0
    last_signal_record = None
    try:
        while datetime.now(timezone.utc) <= end:
            runner_now = datetime.now(timezone.utc)
            current = enrich_session_config({"selection": enriched_session}, [], args.max_open_price_delay_seconds)
            if current.get("raw_payload") is not None:
                write_json(source_dir / f"chainlink_reference_{index}_{observation_checks + 1}.json", {"payload": current["raw_payload"]})
            if current.get("skip_reason"):
                reason = current["skip_reason"]
                append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
                session_report["steps"].append({"step": "paper_runner", "status": "skipped", "runner_output": str(runner_output), "reason": reason, "observation_checks": observation_checks})
                session_report.update({"status": "skipped", "skip_reason": reason})
                if market_id:
                    record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=reason)
                operator_print(args, no_bet_line(reason))
                return session_report
            current_selection = current["selection"]
            current_records = [
                chainlink_price_record(
                    float(current_selection["current_price"]),
                    str(current_selection["current_price_timestamp"]),
                )
            ]
            result = await run_session_once(
                session=enriched_session,
                open_price=float(enriched_session["open_price"]),
                stake=session_stake,
                output=runner_output,
                seconds=args.runner_seconds,
                caller_supplied_p_hat=args.p_hat,
                now=runner_now,
                observe_start_remaining_seconds=args.observe_start_remaining_seconds,
                move_threshold_pct=args.move_threshold_pct,
                p_hat_filter_enabled=args.p_hat_filter_enabled,
                btc_seconds=args.observation_tick_seconds,
                market_seconds=args.runner_seconds,
                btc_records=current_records,
            )
            observation_checks += 1
            signal_record = result.get("signal_record")
            if signal_record is not None:
                last_signal_record = signal_record
            if result["status"] == "no_signal":
                await asyncio.sleep(max(args.observation_tick_seconds, 0.001))
                continue
            if result["status"] == "skipped" and signal_record is None:
                await asyncio.sleep(max(args.observation_tick_seconds, 0.001))
                continue

            decision = result.get("decision")
            if signal_record is not None and market_id:
                upsert_trade(
                    args.ledger_path,
                    market_id=market_id,
                    decision_time=signal_record.now.isoformat(),
                    decision_remaining_seconds=signal_record.remaining_seconds,
                    decision_move_pct=signal_record.ret_pct,
                    signal=signal_record.signal.value,
                    side=signal_record.signal.value if signal_record.signal in (Signal.UP, Signal.DOWN) else None,
                    stake=getattr(decision, "stake", None),
                    entry_avg_ask=getattr(decision, "executable_avg_ask", None),
                    shares=getattr(decision, "shares", None),
                    result="PENDING" if result["status"] == "paper_opened" else "SKIPPED",
                    skip_reason=result.get("reason"),
                )
            if result["status"] == "paper_opened":
                operator_print(
                    args,
                    bet_line(decision.signal.value, signal_record.ret_pct if signal_record else None, signal_record.remaining_seconds if signal_record else None, decision.executable_avg_ask, decision.stake),
                )
            else:
                if market_id:
                    record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=result.get("reason"))
                operator_print(args, no_bet_line(result.get("reason"), signal_record.ret_pct if signal_record else None))
            append_jsonl(supervisor_jsonl, {"record_type": "session_runner_finished", "session": meta, "runner_output": str(runner_output)})
            session_report["steps"].append({"step": "paper_runner", "status": "completed", "runner_output": str(runner_output), "observation_checks": observation_checks})
            session_report["status"] = "completed"
            return session_report

        reason = "observation_window_no_signal"
        if market_id:
            upsert_trade(
                args.ledger_path,
                market_id=market_id,
                decision_time=last_signal_record.now.isoformat() if last_signal_record else None,
                decision_remaining_seconds=last_signal_record.remaining_seconds if last_signal_record else None,
                decision_move_pct=last_signal_record.ret_pct if last_signal_record else None,
                signal=last_signal_record.signal.value if last_signal_record else None,
                result="NO_TRADE",
                skip_reason=reason,
            )
            record_result(args.ledger_path, market_id, "NO_TRADE", args.initial_bankroll, skip_reason=reason)
        operator_print(args, no_bet_line("no_signal", last_signal_record.ret_pct if last_signal_record else None))
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
        session_report["steps"].append({"step": "paper_runner", "status": "skipped", "runner_output": str(runner_output), "reason": reason, "observation_checks": observation_checks})
        session_report.update({"status": "skipped", "skip_reason": reason})
    except Exception as exc:
        reason = f"runner_blocked={type(exc).__name__}: {exc}"
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
        session_report["steps"].append({"step": "paper_runner", "status": "blocker", "reason": reason})
        session_report.update({"status": "blocker", "skip_reason": reason})
        if market_id:
            record_result(args.ledger_path, market_id, "SKIPPED", args.initial_bankroll, skip_reason=reason)
        operator_print(args, no_bet_line(reason))
    return session_report


def start_run_report(args: argparse.Namespace, run_dir: Path) -> tuple[dict[str, Any], Path, Path]:
    update_latest_run_pointers(run_dir)
    source_dir = run_dir / "_source"
    source_dir.mkdir(parents=True, exist_ok=True)
    supervisor_jsonl = source_dir / "supervisor.jsonl"
    if not supervisor_jsonl.exists():
        supervisor_jsonl.write_text("", encoding="utf-8")
    report: dict[str, Any] = {
        "task_id": "polybot-paper-phase-14-public-data-e2e-dry-run",
        "config": args.config_snapshot,
        "public_data_source": None,
        "steps": [],
        "blockers": [],
        "sessions": [],
        "beijing_day": run_dir.name if is_daily_run_dir(run_dir) else None,
    }
    return report, source_dir, supervisor_jsonl


def refresh_resolution(args: argparse.Namespace, report: dict[str, Any], source_dir: Path, supervisor_jsonl: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resolution_result = {
        "resolutions": {},
        "resolution_paths": {},
        "raw_resolution_paths": {},
        "resolution_skips": {},
        "attempts": [],
        "pending_retry": {"attempts": [], "resolved": 0, "pending": 0, "skipped": 0},
    }
    if args.attempt_public_resolution:
        pending_retry = pending_ledger_resolution_retry(args, source_dir)
        resolution_result = attempt_public_resolutions(report, source_dir)
        resolution_result["pending_retry"] = pending_retry
        report["steps"].extend(pending_retry["attempts"])
        report["steps"].extend(resolution_result["attempts"])
    summary = precise_resolution_summary(batch_close(supervisor_jsonl, resolution_result["resolutions"]), resolution_result["resolution_skips"])
    emit_market_results(args, summary, current_report_market_ids(report))
    return resolution_result, summary


def finalize_run(
    args: argparse.Namespace,
    run_dir: Path,
    source_dir: Path,
    supervisor_jsonl: Path,
    report: dict[str, Any],
    stop_reason: str,
    *,
    status: str,
) -> dict[str, Any]:
    resolution_result, summary = refresh_resolution(args, report, source_dir, supervisor_jsonl)
    if args.attempt_public_resolution and not resolution_result["attempts"] and not resolution_result["pending_retry"]["attempts"]:
        report["steps"].append({"step": "resolution", "status": "skipped", "reason": "no_completed_runner_output"})

    report["attempted_session_count"] = len(report["sessions"])
    report["processed_session_count"] = sum(1 for session in report["sessions"] if session.get("status") == "completed")
    report["final_stop_reason"] = stop_reason
    report["resolution_attempted_count"] = len(resolution_result["attempts"])
    report["pending_resolution_retry"] = resolution_result["pending_retry"]
    report["sessions_closed"] = summary["sessions_closed"]
    report["sessions_pending_or_skipped"] = summary["sessions_skipped"]
    if args.attempt_public_resolution:
        report["steps"].append(
            {
                "step": "resolution_result",
                "status": "closed" if summary["sessions_closed"] else "pending_or_skipped",
                "resolution_attempted_count": report["resolution_attempted_count"],
                "pending_resolution_retry": report["pending_resolution_retry"],
                "sessions_closed": summary["sessions_closed"],
                "sessions_pending_or_skipped": summary["sessions_skipped"],
                "skipped_reasons": summary["skipped_reasons"],
            }
        )
    else:
        report["steps"].append({"step": "resolution_result", "status": "pending", "reason": "public_resolution_not_requested"})

    paths = build_run_artifacts(
        run_dir,
        supervisor_jsonl,
        summary,
        run_id=args.run_id,
        mode="public_data_e2e_dry_run",
        status=status,
        config_snapshot=report["config"],
        raw_resolution_paths=resolution_result["raw_resolution_paths"],
        resolution_paths=resolution_result["resolution_paths"],
        resolution_skips=resolution_result["resolution_skips"],
    )
    session_index = read_json(paths["session_index"])
    long_status = run_long_run(
        run_dir,
        session_index["sessions"],
        resume=True,
        max_sessions=args.max_sessions,
        max_runtime_seconds=args.max_runtime_seconds,
        retry_limit=args.retry_limit,
        retry_backoff_seconds=args.retry_backoff_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
    )
    report.update(
        {
            "run_dir": str(run_dir),
            "manifest": str(paths["manifest"]),
            "session_index": str(paths["session_index"]),
            "summary": str(paths["summary"]),
            "final_status": long_status["status"],
        }
    )
    write_json(run_dir / "dry_run_report.json", report)
    return report


async def run_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = resolve_run_dir(args.run_dir, parse_datetime(args.now) if args.now else None)
    daily_base = run_dir.parent if is_daily_run_dir(run_dir) else None
    report, source_dir, supervisor_jsonl = start_run_report(args, run_dir)

    payload, source_timestamp, data_source = load_public_payload(args)
    report["public_data_source"] = data_source
    refresh_resolution(args, report, source_dir, supervisor_jsonl)
    started = time.monotonic()
    cursor = parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    processed_ids: set[str] = set()
    stop_reason = "max_sessions_safety_cap_reached"
    discovery_attempts = 0

    try:
        while len(processed_ids) < args.max_sessions:
            if daily_base is not None and datetime.now(timezone.utc) >= next_beijing_midnight(parse_datetime(f"{run_dir.name}T00:00:00+08:00")):
                finalize_run(args, run_dir, source_dir, supervisor_jsonl, report, "beijing_day_rollover", status="completed")
                run_dir = daily_base / beijing_day_text()
                report, source_dir, supervisor_jsonl = start_run_report(args, run_dir)
                report["public_data_source"] = data_source

            elapsed = time.monotonic() - started
            remaining_runtime = args.max_runtime_seconds - elapsed
            if remaining_runtime <= 0:
                stop_reason = "max_runtime_seconds_exceeded"
                break

            discovery_attempts += 1
            try:
                if args.input_json:
                    result = select_session(payload, cursor, args.lookahead_minutes, args.mode, paper_stake=paper_stake_for_session(args), caller_supplied_p_hat=args.p_hat, source_timestamp=source_timestamp)
                else:
                    result = discover_session(args, cursor, fetch_json)
                    source_timestamp = next((stamp for stamp in result.get("diagnostics", {}).get("source_timestamps", []) if stamp), None)
                discovery_step = {"step": "discovery_fetch", "status": "success", "source_timestamp": source_timestamp, "cursor": cursor.isoformat(), "attempt": discovery_attempts}
                report["steps"].append(discovery_step)
            except Exception as exc:
                reason = f"public_discovery_blocked={type(exc).__name__}: {exc}"
                report["steps"].append({"step": "discovery_fetch", "status": "blocker", "reason": reason, "cursor": cursor.isoformat(), "attempt": discovery_attempts})
                report["blockers"].append(reason)
                append_downstream_skips(report, "discovery_fetch_blocker")
                append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": {"market_id": "public-discovery", "market_slug": None}, "skip_reason": reason})
                stop_reason = reason
                break

            session = result.get("selection")
            if not session:
                reason = result.get("skip_reason", "no_valid_candidate")
                report["steps"].append({"step": "session_discovery", "status": "skipped", "reason": reason, "details": result, "cursor": cursor.isoformat(), "attempt": discovery_attempts})
                append_downstream_skips(report, "session_discovery_skip")
                append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": {"market_id": "public-session-discovery", "market_slug": None}, "skip_reason": reason})
                stop_reason = reason
                break

            if daily_base is not None:
                session_day = beijing_day_text(parse_datetime(session["market_start_time"]))
                if session_day != run_dir.name:
                    finalize_run(args, run_dir, source_dir, supervisor_jsonl, report, "beijing_day_rollover", status="completed")
                    run_dir = daily_base / session_day
                    report, source_dir, supervisor_jsonl = start_run_report(args, run_dir)
                    report["public_data_source"] = data_source

            market_id = str(session.get("market_id"))
            if market_id in processed_ids:
                report["steps"].append({"step": "session_discovery", "status": "skipped", "reason": "duplicate_session", "session": session_meta(session), "cursor": cursor.isoformat(), "attempt": discovery_attempts})
                cursor = parse_datetime(session["market_start_time"])
                if discovery_attempts > args.max_sessions * 3:
                    stop_reason = "duplicate_session"
                    break
                continue

            processed_ids.add(market_id)
            report["steps"].append({"step": "session_discovery", "status": "success", "session": session_meta(session), "cursor": cursor.isoformat(), "attempt": discovery_attempts})
            session_report = await process_session(args, session, source_dir, supervisor_jsonl, len(report["sessions"]) + 1, remaining_runtime)
            report["sessions"].append(session_report)
            report["steps"].extend({"session_index": session_report["session_index"], **step} for step in session_report["steps"])
            refresh_resolution(args, report, source_dir, supervisor_jsonl)
            cursor = parse_datetime(session["market_start_time"])
    except KeyboardInterrupt:
        stop_reason = "interrupted"
        return finalize_run(args, run_dir, source_dir, supervisor_jsonl, report, stop_reason, status="interrupted")

    return finalize_run(args, run_dir, source_dir, supervisor_jsonl, report, stop_reason, status="completed" if not report["blockers"] else "blocked")


def close_existing_run(args: argparse.Namespace) -> dict[str, Any]:
    source_run = args.close_existing_run_dir
    run_dir = args.run_dir or Path(tempfile.mkdtemp(prefix="polybot_phase20_resolution_close_")) / "run"
    source_dir = run_dir / "_source"
    source_dir.mkdir(parents=True, exist_ok=True)
    report = read_json(source_run / "dry_run_report.json")
    report["task_id"] = "polybot-paper-phase-20-public-resolution-closing"
    report["source_run_dir"] = str(source_run)
    report["steps"] = list(report.get("steps", []))
    supervisor_jsonl = source_run / "_source" / "supervisor.jsonl"

    resolution_result = attempt_public_resolutions(report, source_dir)
    report["steps"].extend(resolution_result["attempts"])
    summary = precise_resolution_summary(batch_close(supervisor_jsonl, resolution_result["resolutions"]), resolution_result["resolution_skips"])
    emit_market_results(args, summary)
    report["resolution_attempted_count"] = len(resolution_result["attempts"])
    report["sessions_closed"] = summary["sessions_closed"]
    report["sessions_pending_or_skipped"] = summary["sessions_skipped"]
    report["steps"].append(
        {
            "step": "resolution_result",
            "status": "closed" if summary["sessions_closed"] else "pending_or_skipped",
            "resolution_attempted_count": report["resolution_attempted_count"],
            "sessions_closed": summary["sessions_closed"],
            "sessions_pending_or_skipped": summary["sessions_skipped"],
            "skipped_reasons": summary["skipped_reasons"],
        }
    )

    paths = build_run_artifacts(
        run_dir,
        supervisor_jsonl,
        summary,
        run_id=args.run_id,
        mode="public_resolution_closing",
        status="completed",
        config_snapshot=report.get("config", {}),
        raw_resolution_paths=resolution_result["raw_resolution_paths"],
        resolution_paths=resolution_result["resolution_paths"],
        resolution_skips=resolution_result["resolution_skips"],
    )
    report.update({"run_dir": str(run_dir), "manifest": str(paths["manifest"]), "session_index": str(paths["session_index"]), "summary": str(paths["summary"])})
    write_json(run_dir / "dry_run_report.json", report)
    return report


def self_check() -> Path:
    run_dir = Path(tempfile.mkdtemp(prefix="polybot_phase14_e2e_self_check_")) / "run"
    supervisor_jsonl = run_dir / "_source" / "supervisor.jsonl"
    summary = skipped_batch(supervisor_jsonl, {"market_id": "public-session-discovery"}, "no_valid_candidate")
    paths = build_run_artifacts(run_dir, supervisor_jsonl, summary, run_id="self-check", mode="public_data_e2e_dry_run", status="completed", config_snapshot={"max_sessions": 1})
    run_long_run(run_dir, read_json(paths["session_index"])["sessions"], resume=True, max_sessions=1, max_runtime_seconds=1.0, retry_limit=0, retry_backoff_seconds=0.0, heartbeat_interval_seconds=0.0)
    report = {"final_status": "stopped", "steps": [{"step": "session_discovery", "status": "skipped", "reason": "no_valid_candidate"}]}
    write_json(run_dir / "dry_run_report.json", report)
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "session_index.json").exists()
    assert (run_dir / "status.json").exists()
    assert (run_dir / "heartbeat.jsonl").exists()
    assert read_json(run_dir / "dry_run_report.json")["steps"][0]["reason"] == "no_valid_candidate"
    assert beijing_time_text(datetime(2026, 7, 8, 4, 0, tzinfo=timezone.utc)) == "2026-07-08 12:00:00 CST"
    assert operator_time("2026-07-08T04:15:00+00:00") == "2026-07-08 12:15:00 CST"
    assert beijing_day_text(datetime(2026, 7, 8, 15, 59, tzinfo=timezone.utc)) == "2026-07-08"
    assert beijing_day_text(datetime(2026, 7, 8, 16, 0, tzinfo=timezone.utc)) == "2026-07-09"
    assert next_beijing_midnight(datetime(2026, 7, 8, 15, 59, tzinfo=timezone.utc)) == datetime(2026, 7, 8, 16, 0, tzinfo=timezone.utc)
    concise_lines = [
        watch_line({"market_start_time": "2026-07-09T10:00:00+00:00", "market_end_time": "2026-07-09T10:15:00+00:00", "market_id": "hidden"}),
        open_line({"market_start_time": "2026-07-09T10:00:00+00:00", "market_end_time": "2026-07-09T10:15:00+00:00"}, 62863.06311005423, POLYMARKET_CHAINLINK_SOURCE),
        bet_line("DOWN", -0.158, 282, 0.95, 50.68),
        no_bet_line("no_signal", 0.08),
        settled_line("DOWN", "WIN", 10.98, 1010.98),
        pending_line("awaiting_public_resolution"),
    ]
    assert concise_lines[0] == "[WATCH] 06:00-06:15 ET"
    assert concise_lines[1] == "[OPEN] 06:00-06:15 ET price=62863.06 source=polymarket_chainlink"
    assert concise_lines[2] == "[BET] DOWN move=-0.158% remaining=4.7m avg=0.95 stake=50.68"
    assert concise_lines[3] == "[NO_BET] no trigger; next market"
    assert concise_lines[4] == "[SETTLED] WIN pnl=+10.98"
    assert concise_lines[5] == "[PENDING] awaiting settlement"
    assert all("market_id=" not in line for line in concise_lines)
    assert all("btc-updown-15m-" not in line and "http" not in line and "{" not in line for line in concise_lines)
    assert current_report_market_ids({"sessions": [{"session": {"market_id": "fresh"}}, {"session": {"market_id": ""}}, {}]}) == {"fresh"}

    chainlink_start = datetime.fromtimestamp(1783582200, tz=timezone.utc)
    chainlink_session = {
        "market_id": "btc-updown-15m-1783582200",
        "market_slug": "btc-updown-15m-1783582200",
        "market_start_time": chainlink_start.isoformat(),
        "market_end_time": (chainlink_start + timedelta(minutes=15)).isoformat(),
        "up_token_id": "up-chainlink",
        "down_token_id": "down-chainlink",
        "selected_side_labels": {"UP": "Up", "DOWN": "Down"},
    }

    def fake_chainlink_fetch(_url: str) -> tuple[dict[str, Any], str]:
        return {"candles": [{"time": 1783582200, "open": 62863.06311005423, "high": 62900, "low": 62800, "close": 62820.69}]}, "fixture-chainlink"

    aligned = enrich_session_config({"selection": chainlink_session}, [], 5, fake_chainlink_fetch)
    assert aligned["skip_reason"] is None
    aligned_session = aligned["selection"]
    assert aligned_session["open_price"] == 62863.06311005423
    assert aligned_session["open_price_source"] == POLYMARKET_CHAINLINK_SOURCE
    aligned_runner = asyncio.run(
        run_session_once(
            session=aligned_session,
            open_price=float(aligned_session["open_price"]),
            stake=50.0,
            output=run_dir / "_source" / "chainlink_fixture_runner.jsonl",
            seconds=1.0,
            caller_supplied_p_hat=None,
            market_records=[],
            btc_records=[chainlink_price_record(float(aligned_session["current_price"]), str(aligned_session["current_price_timestamp"]))],
            now=parse_datetime(aligned_session["market_end_time"]) - timedelta(seconds=282),
            move_threshold_pct=0.15,
            p_hat_filter_enabled=False,
        )
    )
    assert aligned_runner["status"] == "no_signal"
    assert round(aligned_runner["signal_record"].ret_pct, 4) == -0.0674
    assert aligned_runner["signal_record"].signal == Signal.NO_SIGNAL

    fallback_only = enrich_session_config(
        {"selection": chainlink_session},
        [
            CaptureRecord(
                source="binance_btcusdt_trade",
                event_type="trade",
                source_timestamp_ms=1783582200000,
                local_receive_timestamp=chainlink_start.isoformat(),
                payload={"p": "62920.01"},
            )
        ],
        5,
        lambda _url: ({"candles": []}, "fixture-empty"),
    )
    assert fallback_only["skip_reason"] == "binance_btcusdt_fallback_not_allowed_for_signal"
    fallback_runner = asyncio.run(
        run_session_once(
            session=chainlink_session,
            open_price=62920.01,
            stake=50.0,
            output=run_dir / "_source" / "fallback_fixture_runner.jsonl",
            seconds=1.0,
            caller_supplied_p_hat=None,
            market_records=[],
            btc_records=[
                CaptureRecord(
                    source="binance_btcusdt_trade",
                    event_type="trade",
                    source_timestamp_ms=1783582200000,
                    local_receive_timestamp=chainlink_start.isoformat(),
                    payload={"p": "62820.69"},
                )
            ],
            now=parse_datetime(chainlink_session["market_end_time"]) - timedelta(seconds=282),
            move_threshold_pct=0.15,
            p_hat_filter_enabled=False,
        )
    )
    assert fallback_runner["status"] == "skipped"
    assert fallback_runner["reason"] == "missing_btc_reference_price"
    assert fallback_runner.get("signal_record") is None
    wait_step = asyncio.run(wait_to_open({"market_start_time": (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()}, 0.0))
    assert wait_step["reason"] == "wait_to_open_budget_exceeded"
    config_root = Path(tempfile.mkdtemp(prefix="polybot_config_self_check_"))
    config_path = config_root / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "paper:",
                "  stake: 3",
                "  initial_bankroll: 500",
                f"  ledger_path: {config_root / 'config-ledger.sqlite3'}",
                "marketability:",
                "  p_hat_filter_enabled: false",
                "  p_hat: null",
                "runtime:",
                "  max_sessions: 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config_args = apply_config(
        build_parser().parse_args(
            [
                "--config",
                str(config_path),
                "--paper-stake",
                "4",
                "--no-operator-output-enabled",
            ]
        )
    )
    assert config_args.paper_stake == 4.0
    assert config_args.initial_bankroll == 500.0
    assert config_args.ledger_path == config_root / "config-ledger.sqlite3"
    assert config_args.p_hat_filter_enabled is False
    assert config_args.p_hat is None
    assert config_args.max_sessions == 2

    fraction_root = Path(tempfile.mkdtemp(prefix="polybot_stake_fraction_self_check_"))
    fraction_args = apply_config(
        build_parser().parse_args(
            [
                "--ledger-path",
                str(fraction_root / "paper_trades.sqlite3"),
                "--initial-bankroll",
                "1000",
                "--no-operator-output-enabled",
            ]
        )
    )
    assert fraction_args.paper_stake is None
    assert fraction_args.stake_fraction == 0.05
    assert paper_stake_for_session(fraction_args) == 50.0
    record_result(fraction_args.ledger_path, "stake-win", "WIN", fraction_args.initial_bankroll, winning_side="UP", paper_pnl=11.0)
    assert round(paper_stake_for_session(fraction_args), 6) == 50.55

    threshold_args = apply_config(build_parser().parse_args(["--no-operator-output-enabled"]))
    assert threshold_args.move_threshold_pct == configured_move_threshold_pct()

    multi_payload = [
        {
            "id": "event-next-one",
            "title": "Bitcoin Up or Down one",
            "active": True,
            "closed": False,
            "markets": [
                {
                    "id": "market-next-one",
                    "slug": "btc-15m-next-one",
                    "question": "Bitcoin Up or Down - one",
                    "active": True,
                    "closed": False,
                    "acceptingOrders": True,
                    "startDate": "2026-07-06T12:15:00+00:00",
                    "endDate": "2026-07-06T12:30:00+00:00",
                    "outcomes": '["Up", "Down"]',
                    "clobTokenIds": '["up-one", "down-one"]',
                }
            ],
        },
        {
            "id": "event-next-two",
            "title": "Bitcoin Up or Down two",
            "active": True,
            "closed": False,
            "markets": [
                {
                    "id": "market-next-two",
                    "slug": "btc-15m-next-two",
                    "question": "Bitcoin Up or Down - two",
                    "active": True,
                    "closed": False,
                    "acceptingOrders": True,
                    "startDate": "2026-07-06T12:30:00+00:00",
                    "endDate": "2026-07-06T12:45:00+00:00",
                    "outcomes": '["Up", "Down"]',
                    "clobTokenIds": '["up-two", "down-two"]',
                }
            ],
        },
    ]
    multi_root = Path(tempfile.mkdtemp(prefix="polybot_phase19_multi_self_check_"))
    input_json = multi_root / "payload.json"
    input_json.write_text(json.dumps(multi_payload, sort_keys=True) + "\n", encoding="utf-8")
    multi_args = apply_config(
        build_parser().parse_args(
            [
                "--input-json",
                str(input_json),
                "--mode",
                "next",
                "--max-sessions",
                "2",
                "--max-runtime-seconds",
                "5",
                "--lookahead-minutes",
                "60",
                "--max-wait-to-open-seconds",
                "0",
                "--max-wait-to-observation-seconds",
                "0",
                "--heartbeat-interval-seconds",
                "0",
                "--no-operator-output-enabled",
                "--now",
                "2026-07-06T12:05:00+00:00",
                "--run-dir",
                str(multi_root / "run"),
                "--ledger-path",
                str(multi_root / "paper_trades.sqlite3"),
            ]
        )
    )
    multi_report = asyncio.run(run_dry_run(multi_args))
    assert multi_report["attempted_session_count"] == 2
    starts = [session["session"]["market_start_time"] for session in multi_report["sessions"]]
    assert starts == sorted(starts)
    assert {session["session"]["market_id"] for session in multi_report["sessions"]} == {"market-next-one", "market-next-two"}
    ledger = ledger_rows(multi_args.ledger_path)
    assert len(ledger) == 2
    assert {row["market_id"] for row in ledger} == {"market-next-one", "market-next-two"}
    assert {row["result"] for row in ledger} == {"SKIPPED"}
    assert all(row["side"] is None for row in ledger)
    assert all(row["skip_reason"] for row in ledger)

    close_root = Path(tempfile.mkdtemp(prefix="polybot_phase20_resolution_self_check_"))
    close_source = close_root / "run" / "_source"
    close_source.mkdir(parents=True, exist_ok=True)
    close_runner = close_source / "runner_1.jsonl"
    close_runner.write_text(json.dumps({"record_type": "signal_record", "record": {"signal": "NO_SIGNAL"}}, sort_keys=True) + "\n", encoding="utf-8")
    close_supervisor = close_source / "supervisor.jsonl"
    append_jsonl(
        close_supervisor,
        {
            "record_type": "session_runner_finished",
            "session": {"market_id": "market-pending", "market_slug": "btc-pending"},
            "runner_output": str(close_runner),
        },
    )
    close_resolution = close_source / "resolution_1_market-pending.json"
    close_raw = close_source / "resolution_raw_1_market-pending.json"
    write_json(close_resolution, {"resolutions": {}, "skipped": [{"market_id": "market-pending", "status": "skipped", "skip_reason": "not_closed"}]})
    write_json(close_raw, {"id": "market-pending", "closed": False})
    close_summary = precise_resolution_summary(batch_close(close_supervisor, {}), {"market-pending": "not_closed"})
    close_paths = build_run_artifacts(
        close_root / "run",
        close_supervisor,
        close_summary,
        run_id="phase20-self-check",
        mode="public_data_e2e_dry_run",
        resolution_paths={"market-pending": close_resolution},
        raw_resolution_paths={"market-pending": close_raw},
        resolution_skips={"market-pending": "not_closed"},
    )
    close_index = read_json(close_paths["session_index"])
    assert close_index["sessions"][0]["resolution_status"] == "skipped"
    assert close_index["sessions"][0]["resolution_path"] == "sessions/01_market-pending/resolution.json"
    assert close_index["sessions"][0]["resolution_raw_path"] == "sessions/01_market-pending/resolution_raw.json"
    assert close_index["sessions"][0]["skip_reason"] == "not_closed"

    settle_root = Path(tempfile.mkdtemp(prefix="polybot_daily_settlement_self_check_"))
    settle_run = settle_root / "2026-07-08"
    settle_report, settle_source, settle_supervisor = start_run_report(multi_args, settle_run)
    settle_runner_closed = settle_source / "runner_closed.jsonl"
    settle_runner_pending = settle_source / "runner_pending.jsonl"
    settle_runner_closed.write_text(
        "\n".join(
            [
                json.dumps({"record_type": "signal_record", "record": {"signal": "UP"}}, sort_keys=True),
                json.dumps({"record_type": "paper_trade_record", "record": {"signal": "UP", "stake": 9.0, "shares": 20.0}}, sort_keys=True),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    settle_runner_pending.write_text(json.dumps({"record_type": "signal_record", "record": {"signal": "UP"}}, sort_keys=True) + "\n", encoding="utf-8")
    for market_id in ("market-closed", "market-pending"):
        upsert_trade(multi_args.ledger_path, market_id=market_id, result="PENDING")
    append_jsonl(settle_supervisor, {"record_type": "session_runner_finished", "session": {"market_id": "market-closed"}, "runner_output": str(settle_runner_closed)})
    append_jsonl(settle_supervisor, {"record_type": "session_runner_finished", "session": {"market_id": "market-pending"}, "runner_output": str(settle_runner_pending)})
    settle_summary = precise_resolution_summary(batch_close(settle_supervisor, {"market-closed": "UP"}), {"market-pending": "not_closed"})
    emit_market_results(multi_args, settle_summary)
    settle_rows = {row["market_id"]: row for row in ledger_rows(multi_args.ledger_path)}
    assert settle_rows["market-closed"]["result"] == "WIN"
    assert settle_rows["market-pending"]["result"] == "PENDING"

    pending_root = Path(tempfile.mkdtemp(prefix="polybot_pending_retry_self_check_"))
    pending_args = apply_config(
        build_parser().parse_args(
            [
                "--ledger-path",
                str(pending_root / "paper_trades.sqlite3"),
                "--initial-bankroll",
                "1000",
                "--no-operator-output-enabled",
            ]
        )
    )
    pending_source = pending_root / "_source"
    pending_source.mkdir(parents=True, exist_ok=True)
    upsert_trade(pending_args.ledger_path, market_id="pending-clear", result="PENDING", side="UP", stake=50.0, shares=80.0)
    upsert_trade(pending_args.ledger_path, market_id="pending-open", result="PENDING", side="DOWN", stake=50.0, shares=80.0)

    def fake_pending_fetch(url: str) -> tuple[dict[str, Any], str]:
        if "pending-clear" in url:
            return {"id": "pending-clear", "closed": True, "outcomes": '["Up", "Down"]', "outcomePrices": '["1", "0"]'}, "fixture-clear"
        return {"id": "pending-open", "closed": False, "outcomes": '["Up", "Down"]', "outcomePrices": '["0.5", "0.5"]'}, "fixture-open"

    pending_retry = pending_ledger_resolution_retry(pending_args, pending_source, fake_pending_fetch)
    pending_rows = {row["market_id"]: row for row in ledger_rows(pending_args.ledger_path)}
    assert pending_retry["resolved"] == 1
    assert pending_retry["pending"] == 1
    assert pending_rows["pending-clear"]["result"] == "WIN"
    assert pending_rows["pending-clear"]["paper_pnl"] == 30.0
    assert pending_rows["pending-open"]["result"] == "PENDING"
    assert pending_rows["pending-open"]["skip_reason"] == "not_closed"

    finalize_report = finalize_run(multi_args, settle_run, settle_source, settle_supervisor, settle_report, "interrupted", status="interrupted")
    assert read_json(Path(finalize_report["manifest"]))["status"] in ("interrupted", "stopped")
    assert read_json(settle_run / "dry_run_report.json")["final_stop_reason"] == "interrupted"
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Beijing-day rolling public-data end-to-end paper dry run.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id", default="phase14-public-data-dry-run")
    parser.add_argument("--source-url")
    parser.add_argument("--search-query")
    parser.add_argument("--source-kind", choices=("events", "markets", "both"), default="both")
    parser.add_argument("--tag-id")
    parser.add_argument("--slug")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--mode", choices=("current", "next"))
    parser.add_argument("--lookahead-minutes", type=int)
    parser.add_argument("--max-sessions", type=int, help="safety cap; normal run boundary is Beijing midnight")
    parser.add_argument("--max-runtime-seconds", type=float)
    parser.add_argument("--paper-stake", type=float)
    parser.add_argument("--stake-fraction", type=float)
    parser.add_argument("--initial-bankroll", type=float)
    parser.add_argument("--ledger-path", type=Path)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--p-hat-filter-enabled", action=argparse.BooleanOptionalAction)
    parser.add_argument("--move-threshold-pct", type=float)
    parser.add_argument("--observe-start-remaining-seconds", type=int)
    parser.add_argument("--capture-seconds", type=float)
    parser.add_argument("--capture-limit", type=int)
    parser.add_argument("--observation-tick-seconds", type=float)
    parser.add_argument("--max-wait-to-open-seconds", type=float)
    parser.add_argument("--max-wait-to-observation-seconds", type=float)
    parser.add_argument("--max-open-price-delay-seconds", type=float)
    parser.add_argument("--runner-seconds", type=float)
    parser.add_argument("--retry-limit", type=int)
    parser.add_argument("--retry-backoff-seconds", type=float)
    parser.add_argument("--heartbeat-interval-seconds", type=float)
    parser.add_argument("--operator-output-enabled", action=argparse.BooleanOptionalAction)
    parser.add_argument("--now")
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--attempt-public-resolution", action="store_true")
    parser.add_argument("--close-existing-run-dir", type=Path)
    return parser


def main() -> int:
    args = apply_config(build_parser().parse_args())
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "run_dir": str(output)}, sort_keys=True))
        return 0
    report = close_existing_run(args) if args.close_existing_run_dir else asyncio.run(run_dry_run(args))
    print(json.dumps({"run_dir": report.get("run_dir"), "final_status": report.get("final_status"), "steps": report.get("steps"), "blockers": report.get("blockers")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
