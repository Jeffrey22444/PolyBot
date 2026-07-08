from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from polybot.long_run import run_long_run
from polybot.market_data import CaptureRecord, capture_btc_reference, write_jsonl
from polybot.market_discovery import GAMMA_EVENTS_URL
from polybot.market_discovery import discover_session, fetch_json, select_session
from polybot.open_price import enrich_session_config
from polybot.paper_runner import parse_datetime, parse_entry_remain_seconds, run_session_once
from polybot.resolution_ingestion import extract_market, ingest_metadata
from polybot.run_artifacts import build_run_artifacts, read_json, write_json
from polybot.supervisor_results import batch_close


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def records_to_jsonl(path: Path, records: list[CaptureRecord]) -> None:
    path.write_text("", encoding="utf-8")
    if records:
        write_jsonl(path, records)


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


async def wait_to_entry(
    session: dict[str, Any],
    entry_remain_seconds: tuple[int, ...],
    max_wait_seconds: float,
    tolerance_seconds: float,
) -> dict[str, Any]:
    end = parse_datetime(session["market_end_time"])
    now = datetime.now(timezone.utc)
    candidates = sorted((end - timedelta(seconds=seconds), seconds) for seconds in entry_remain_seconds)
    step = {
        "step": "wait_to_entry",
        "local_timestamp": now.isoformat(),
        "candidate_entry_timestamps": [timestamp.isoformat() for timestamp, _ in candidates],
        "max_wait_seconds": max_wait_seconds,
        "tolerance_seconds": tolerance_seconds,
    }
    usable = [(timestamp, seconds) for timestamp, seconds in candidates if (timestamp + timedelta(seconds=tolerance_seconds)) >= now]
    if not usable:
        return {**step, "status": "skipped", "reason": "entry_window_missed"}

    entry_at, remain_seconds = usable[0]
    wait_seconds = max((entry_at - now).total_seconds(), 0.0)
    selected = {
        **step,
        "selected_entry_timestamp": entry_at.isoformat(),
        "selected_entry_remain_seconds": remain_seconds,
        "wait_seconds": wait_seconds,
    }
    if wait_seconds > max_wait_seconds:
        return {**selected, "status": "skipped", "reason": "wait_to_entry_budget_exceeded"}

    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
    wake = datetime.now(timezone.utc)
    lateness = (wake - entry_at).total_seconds()
    finished = {**selected, "wake_timestamp": wake.isoformat(), "lateness_seconds": lateness}
    if lateness > tolerance_seconds:
        return {**finished, "status": "skipped", "reason": "entry_window_missed"}
    return {**finished, "status": "success" if wait_seconds > 0 else "no_wait_needed"}


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

    wait_step = await wait_to_open(session, min(args.max_wait_to_open_seconds, max(0.0, remaining_runtime_seconds)))
    session_report["steps"].append(wait_step)
    if wait_step["status"] == "skipped":
        reason = wait_step["reason"]
        session_report["steps"].append({"step": "btc_reference_capture", "status": "skipped", "reason": f"not_reached_after_{reason}"})
        session_report["steps"].append({"step": "open_price", "status": "skipped", "reason": f"not_reached_after_{reason}"})
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "skip_reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        return session_report

    btc_records: list[CaptureRecord] = []
    try:
        btc_records = await capture_btc_reference(args.capture_seconds, args.capture_limit)
        records_to_jsonl(source_dir / f"btc_reference_{index}.jsonl", btc_records)
        session_report["steps"].append({"step": "btc_reference_capture", "status": "success" if btc_records else "skipped", "record_count": len(btc_records)})
    except Exception as exc:
        session_report["steps"].append({"step": "btc_reference_capture", "status": "blocker", "reason": f"{type(exc).__name__}: {exc}"})

    enriched = enrich_session_config({"selection": session}, btc_records, args.max_open_price_delay_seconds)
    if enriched.get("skip_reason"):
        reason = enriched["skip_reason"]
        session_report["steps"].append({"step": "open_price", "status": "skipped", "reason": reason})
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "skip_reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        return session_report

    enriched_session = enriched["selection"]
    session_report["steps"].append({"step": "open_price", "status": "captured", "open_price": enriched_session["open_price"], "open_price_timestamp": enriched_session["open_price_timestamp"]})
    runner_output = source_dir / f"runner_{index}.jsonl"
    runner_output.write_text("", encoding="utf-8")
    session_report["runner_output"] = str(runner_output)

    entry_remain_seconds = parse_entry_remain_seconds(args.entry_remain_seconds)
    entry_step = await wait_to_entry(
        enriched_session,
        entry_remain_seconds,
        min(args.max_wait_to_entry_seconds, max(0.0, remaining_runtime_seconds)),
        args.entry_window_tolerance_seconds,
    )
    session_report["steps"].append(entry_step)
    if entry_step["status"] == "skipped":
        reason = entry_step["reason"]
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
        session_report["steps"].append({"step": "paper_runner", "status": "skipped", "runner_output": str(runner_output), "reason": reason})
        session_report.update({"status": "skipped", "skip_reason": reason})
        return session_report

    runner_now = parse_datetime(entry_step["selected_entry_timestamp"])
    try:
        await run_session_once(
            session=enriched_session,
            open_price=float(enriched_session["open_price"]),
            stake=args.paper_stake,
            output=runner_output,
            seconds=args.runner_seconds,
            caller_supplied_p_hat=args.p_hat,
            now=runner_now,
            entry_remain_seconds=entry_remain_seconds,
            move_threshold_pct=args.move_threshold_pct,
        )
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_finished", "session": meta, "runner_output": str(runner_output)})
        session_report["steps"].append({"step": "paper_runner", "status": "completed", "runner_output": str(runner_output)})
        session_report["status"] = "completed"
    except Exception as exc:
        reason = f"runner_blocked={type(exc).__name__}: {exc}"
        append_jsonl(supervisor_jsonl, {"record_type": "session_runner_skipped", "session": meta, "runner_output": str(runner_output), "skip_reason": reason})
        session_report["steps"].append({"step": "paper_runner", "status": "blocker", "reason": reason})
        session_report.update({"status": "blocker", "skip_reason": reason})
    return session_report


async def run_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir or Path(tempfile.mkdtemp(prefix="polybot_phase14_e2e_dry_run_")) / "run"
    source_dir = run_dir / "_source"
    source_dir.mkdir(parents=True, exist_ok=True)
    supervisor_jsonl = source_dir / "supervisor.jsonl"
    supervisor_jsonl.write_text("", encoding="utf-8")
    report: dict[str, Any] = {
        "task_id": "polybot-paper-phase-14-public-data-e2e-dry-run",
        "config": {
            "max_sessions": args.max_sessions,
            "max_runtime_seconds": args.max_runtime_seconds,
            "paper_stake": args.paper_stake,
            "caller_supplied_p_hat": args.p_hat,
            "move_threshold_pct": args.move_threshold_pct,
            "entry_remain_seconds": args.entry_remain_seconds,
            "lookahead_minutes": args.lookahead_minutes,
            "capture_seconds": args.capture_seconds,
            "max_wait_to_open_seconds": args.max_wait_to_open_seconds,
            "max_wait_to_entry_seconds": args.max_wait_to_entry_seconds,
            "entry_window_tolerance_seconds": args.entry_window_tolerance_seconds,
            "attempt_public_resolution": args.attempt_public_resolution,
        },
        "public_data_source": None,
        "steps": [],
        "blockers": [],
    }

    payload, source_timestamp, data_source = load_public_payload(args)
    report["public_data_source"] = data_source
    report["sessions"] = []
    started = time.monotonic()
    cursor = parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    processed_ids: set[str] = set()
    stop_reason = "reached_max_sessions"
    discovery_attempts = 0

    while len(report["sessions"]) < args.max_sessions:
        elapsed = time.monotonic() - started
        remaining_runtime = args.max_runtime_seconds - elapsed
        if remaining_runtime <= 0:
            stop_reason = "max_runtime_seconds_exceeded"
            break

        discovery_attempts += 1
        try:
            if args.input_json:
                result = select_session(payload, cursor, args.lookahead_minutes, args.mode, paper_stake=args.paper_stake, caller_supplied_p_hat=args.p_hat, source_timestamp=source_timestamp)
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
        cursor = parse_datetime(session["market_start_time"])

    resolution_result = {
        "resolutions": {},
        "resolution_paths": {},
        "raw_resolution_paths": {},
        "resolution_skips": {},
        "attempts": [],
    }
    if args.attempt_public_resolution:
        resolution_result = attempt_public_resolutions(report, source_dir)
        report["steps"].extend(resolution_result["attempts"])
        if not resolution_result["attempts"]:
            report["steps"].append({"step": "resolution", "status": "skipped", "reason": "no_completed_runner_output"})

    summary = precise_resolution_summary(batch_close(supervisor_jsonl, resolution_result["resolutions"]), resolution_result["resolution_skips"])
    report["attempted_session_count"] = len(report["sessions"])
    report["processed_session_count"] = sum(1 for session in report["sessions"] if session.get("status") == "completed")
    report["final_stop_reason"] = stop_reason
    report["resolution_attempted_count"] = len(resolution_result["attempts"])
    report["sessions_closed"] = summary["sessions_closed"]
    report["sessions_pending_or_skipped"] = summary["sessions_skipped"]
    if args.attempt_public_resolution:
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
    else:
        report["steps"].append({"step": "resolution_result", "status": "pending", "reason": "public_resolution_not_requested"})

    paths = build_run_artifacts(
        run_dir,
        supervisor_jsonl,
        summary,
        run_id=args.run_id,
        mode="public_data_e2e_dry_run",
        status="completed" if not report["blockers"] else "blocked",
        config_snapshot=report["config"],
        raw_resolution_paths=resolution_result["raw_resolution_paths"],
        resolution_paths=resolution_result["resolution_paths"],
        resolution_skips=resolution_result["resolution_skips"],
    )
    session_index = read_json(paths["session_index"])
    status = run_long_run(
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
            "final_status": status["status"],
        }
    )
    write_json(run_dir / "dry_run_report.json", report)
    return report


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
    wait_step = asyncio.run(wait_to_open({"market_start_time": (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()}, 0.0))
    assert wait_step["reason"] == "wait_to_open_budget_exceeded"
    entry_step = asyncio.run(
        wait_to_entry(
            {"market_end_time": (datetime.now(timezone.utc) + timedelta(seconds=181)).isoformat()},
            (180, 240),
            0.0,
            2.0,
        )
    )
    assert entry_step["reason"] == "wait_to_entry_budget_exceeded"

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
    multi_args = build_parser().parse_args(
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
            "--heartbeat-interval-seconds",
            "0",
            "--now",
            "2026-07-06T12:05:00+00:00",
            "--run-dir",
            str(multi_root / "run"),
        ]
    )
    multi_report = asyncio.run(run_dry_run(multi_args))
    assert multi_report["attempted_session_count"] == 2
    starts = [session["session"]["market_start_time"] for session in multi_report["sessions"]]
    assert starts == sorted(starts)
    assert {session["session"]["market_id"] for session in multi_report["sessions"]} == {"market-next-one", "market-next-two"}

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
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded public-data end-to-end paper dry run.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--run-id", default="phase14-public-data-dry-run")
    parser.add_argument("--source-url")
    parser.add_argument("--search-query")
    parser.add_argument("--source-kind", choices=("events", "markets", "both"), default="both")
    parser.add_argument("--tag-id")
    parser.add_argument("--slug")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--mode", choices=("current", "next"), default="current")
    parser.add_argument("--lookahead-minutes", type=int, default=30)
    parser.add_argument("--max-sessions", type=int, default=1)
    parser.add_argument("--max-runtime-seconds", type=float, default=30.0)
    parser.add_argument("--paper-stake", type=float, default=9.0)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--move-threshold-pct", type=float, default=0.05)
    parser.add_argument("--entry-remain-seconds", default="180,240")
    parser.add_argument("--capture-seconds", type=float, default=3.0)
    parser.add_argument("--capture-limit", type=int, default=3)
    parser.add_argument("--max-wait-to-open-seconds", type=float, default=0.0)
    parser.add_argument("--max-wait-to-entry-seconds", type=float, default=0.0)
    parser.add_argument("--entry-window-tolerance-seconds", type=float, default=2.0)
    parser.add_argument("--max-open-price-delay-seconds", type=float, default=5.0)
    parser.add_argument("--runner-seconds", type=float, default=3.0)
    parser.add_argument("--retry-limit", type=int, default=0)
    parser.add_argument("--retry-backoff-seconds", type=float, default=0.0)
    parser.add_argument("--heartbeat-interval-seconds", type=float, default=0.0)
    parser.add_argument("--now")
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--attempt-public-resolution", action="store_true")
    parser.add_argument("--close-existing-run-dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "run_dir": str(output)}, sort_keys=True))
        return 0
    report = close_existing_run(args) if args.close_existing_run_dir else asyncio.run(run_dry_run(args))
    print(json.dumps({"run_dir": report.get("run_dir"), "final_status": report.get("final_status"), "steps": report.get("steps"), "blockers": report.get("blockers")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
