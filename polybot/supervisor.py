from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from polybot.market_data import CaptureRecord
from polybot.market_discovery import load_payload, plan_rotation, sample_payload, select_session
from polybot.open_price import enrich_session_config, load_records, sample_record
from polybot.paper_runner import append_jsonl, parse_datetime, run_session_once


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def session_meta(session: dict[str, Any] | None) -> dict[str, Any]:
    if not session:
        return {}
    return {
        "market_id": session.get("market_id"),
        "market_slug": session.get("market_slug"),
        "market_start_time": session.get("market_start_time"),
        "market_end_time": session.get("market_end_time"),
    }


def stop_reason(started_at: datetime, max_runtime_seconds: float | None, end_time: datetime | None) -> str | None:
    now = utc_now()
    if max_runtime_seconds is not None and (now - started_at).total_seconds() >= max_runtime_seconds:
        return "reached_max_runtime"
    if end_time is not None and now >= end_time:
        return "reached_end_time"
    return None


async def run_supervisor(
    payload: Any,
    output_dir: Path,
    supervisor_jsonl: Path,
    max_sessions: int,
    lookahead_minutes: int,
    max_open_price_delay_seconds: float,
    paper_stake: float,
    runner_seconds: float,
    caller_supplied_p_hat: float | None = None,
    max_runtime_seconds: float | None = None,
    end_time: datetime | None = None,
    now: datetime | None = None,
    open_price_records: list[CaptureRecord] | None = None,
    open_price_records_by_market: dict[str, list[CaptureRecord]] | None = None,
    runner_market_records: list[CaptureRecord] | None = None,
    runner_btc_records: list[CaptureRecord] | None = None,
    runner_now: datetime | None = None,
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    supervisor_jsonl.write_text("", encoding="utf-8")
    started_at = utc_now()
    cursor_now = now or utc_now()
    append_jsonl(supervisor_jsonl, "supervisor_started", {"max_sessions": max_sessions, "output_dir": str(output_dir)})

    try:
        result = select_session(
            payload,
            cursor_now,
            lookahead_minutes,
            "current",
            paper_stake=paper_stake,
            caller_supplied_p_hat=caller_supplied_p_hat,
        )
    except Exception as exc:
        append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "unrecoverable_error", "error": f"{type(exc).__name__}: {exc}", "processed_sessions": 0})
        return "unrecoverable_error"
    processed = 0
    current_session: dict[str, Any] | None = None

    while processed < max_sessions:
        bound_stop = stop_reason(started_at, max_runtime_seconds, end_time)
        if bound_stop:
            append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": bound_stop, "processed_sessions": processed})
            return bound_stop

        session = result.get("selection") if isinstance(result, dict) else None
        if not session:
            reason = result.get("skip_reason", "no_valid_candidate") if isinstance(result, dict) else "no_valid_candidate"
            append_jsonl(supervisor_jsonl, "session_skipped", {"skip_reason": reason, "details": result})
            append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "no_next_session", "processed_sessions": processed})
            return "no_next_session"

        processed += 1
        current_session = session
        append_jsonl(supervisor_jsonl, "session_discovered", {"session": session_meta(session), "session_index": processed})

        records = (open_price_records_by_market or {}).get(str(session.get("market_id")), open_price_records or [])
        try:
            enriched = enrich_session_config({"selection": session}, records, max_open_price_delay_seconds)
        except Exception as exc:
            append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "unrecoverable_error", "error": f"{type(exc).__name__}: {exc}", "processed_sessions": processed})
            return "unrecoverable_error"
        enriched_session = enriched.get("selection")
        if enriched.get("skip_reason"):
            append_jsonl(
                supervisor_jsonl,
                "open_price_skipped",
                {"session": session_meta(session), "skip_reason": enriched["skip_reason"]},
            )
            append_jsonl(
                supervisor_jsonl,
                "session_runner_skipped",
                {"session": session_meta(session), "skip_reason": enriched["skip_reason"]},
            )
        else:
            append_jsonl(supervisor_jsonl, "open_price_captured", {"session": session_meta(enriched_session), "open_price": enriched_session["open_price"]})
            runner_output = output_dir / f"session_{processed}_{session['market_id']}.jsonl"
            runner_output.write_text("", encoding="utf-8")
            append_jsonl(supervisor_jsonl, "session_runner_started", {"session": session_meta(session), "runner_output": str(runner_output)})
            try:
                await run_session_once(
                    session=enriched_session,
                    open_price=float(enriched_session["open_price"]),
                    stake=paper_stake,
                    output=runner_output,
                    seconds=runner_seconds,
                    caller_supplied_p_hat=caller_supplied_p_hat,
                    market_records=runner_market_records,
                    btc_records=runner_btc_records,
                    now=runner_now,
                )
                append_jsonl(supervisor_jsonl, "session_runner_finished", {"session": session_meta(session), "runner_output": str(runner_output)})
            except Exception as exc:
                append_jsonl(
                    supervisor_jsonl,
                    "session_runner_skipped",
                    {"session": session_meta(session), "runner_output": str(runner_output), "skip_reason": f"{type(exc).__name__}: {exc}"},
                )

        if processed >= max_sessions:
            append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "reached_max_sessions", "processed_sessions": processed})
            return "reached_max_sessions"

        cursor_now = parse_datetime(session["market_start_time"])
        try:
            result = plan_rotation(current_session, payload, cursor_now, lookahead_minutes)
        except Exception as exc:
            append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "unrecoverable_error", "error": f"{type(exc).__name__}: {exc}", "processed_sessions": processed})
            return "unrecoverable_error"
        append_jsonl(supervisor_jsonl, "rotation_planned", {"from_session": session_meta(current_session), "result": result})

    append_jsonl(supervisor_jsonl, "supervisor_stopped", {"stop_reason": "reached_max_sessions", "processed_sessions": processed})
    return "reached_max_sessions"


def load_supervisor_payload(args: argparse.Namespace) -> tuple[Any, str | None]:
    if args.sample_fixture:
        return sample_payload(), None
    return load_payload(args)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def self_check() -> Path:
    output_dir = Path(tempfile.gettempdir()) / "polybot_phase9_supervisor"
    supervisor_jsonl = output_dir / "supervisor.jsonl"
    payload = sample_payload()
    now = datetime(2026, 7, 6, 12, 5, tzinfo=timezone.utc)
    current = select_session(payload, now, 20, "current")["selection"]
    next_session = select_session(payload, now, 20, "next")["selection"]
    current_start = int(parse_datetime(current["market_start_time"]).timestamp() * 1000)
    next_start = int(parse_datetime(next_session["market_start_time"]).timestamp() * 1000)

    stop = await run_supervisor(
        payload=payload,
        output_dir=output_dir,
        supervisor_jsonl=supervisor_jsonl,
        max_sessions=2,
        lookahead_minutes=20,
        max_open_price_delay_seconds=5,
        paper_stake=9.0,
        runner_seconds=1.0,
        caller_supplied_p_hat=0.55,
        now=now,
        open_price_records_by_market={
            "market-current": [sample_record("100.00", current_start)],
            "market-next": [sample_record("101.00", next_start + 6000)],
        },
        runner_market_records=[
            CaptureRecord(
                source="polymarket",
                event_type="book",
                source_timestamp_ms=current_start + 1,
                local_receive_timestamp=datetime.fromtimestamp((current_start + 1) / 1000, tz=timezone.utc).isoformat(),
                payload={"event_type": "book", "timestamp": str(current_start + 1), "asks": [{"price": "0.40", "size": "10"}]},
            )
        ],
        runner_btc_records=[sample_record("100.06", current_start + 12 * 60 * 1000)],
        runner_now=parse_datetime(current["market_end_time"]) - timedelta(minutes=3),
    )
    records = read_jsonl(supervisor_jsonl)
    runner_outputs = [record["runner_output"] for record in records if record["record_type"] == "session_runner_finished"]

    assert stop == "reached_max_sessions"
    assert sum(record["record_type"] == "session_discovered" for record in records) == 2
    assert any(record["record_type"] == "open_price_skipped" and record["skip_reason"] == "stale_open_price_record" for record in records)
    assert any(record["record_type"] == "rotation_planned" for record in records)
    assert records[0]["record_type"] == "supervisor_started"
    assert records[-1]["record_type"] == "supervisor_stopped"
    assert runner_outputs and Path(runner_outputs[0]).exists()
    return supervisor_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bounded paper-session supervisor.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--sample-fixture", action="store_true")
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--source-url")
    parser.add_argument("--tag-id")
    parser.add_argument("--slug")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--lookahead-minutes", type=int, default=30)
    parser.add_argument("--max-sessions", type=int, default=2)
    parser.add_argument("--max-runtime-seconds", type=float)
    parser.add_argument("--end-time")
    parser.add_argument("--max-open-price-delay-seconds", type=float, default=5.0)
    parser.add_argument("--btc-records-jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--supervisor-jsonl", type=Path)
    parser.add_argument("--paper-stake", type=float)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--runner-seconds", type=float, default=10.0)
    parser.add_argument("--now")
    return parser


async def async_main(args: argparse.Namespace) -> int:
    if args.self_check:
        output = await self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    required = {
        "--output-dir": args.output_dir,
        "--supervisor-jsonl": args.supervisor_jsonl,
        "--paper-stake": args.paper_stake,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")
    if args.max_sessions <= 0:
        raise SystemExit("--max-sessions must be positive")

    payload, _source_timestamp = load_supervisor_payload(args)
    stop = await run_supervisor(
        payload=payload,
        output_dir=args.output_dir,
        supervisor_jsonl=args.supervisor_jsonl,
        max_sessions=args.max_sessions,
        lookahead_minutes=args.lookahead_minutes,
        max_open_price_delay_seconds=args.max_open_price_delay_seconds,
        paper_stake=args.paper_stake,
        runner_seconds=args.runner_seconds,
        caller_supplied_p_hat=args.p_hat,
        max_runtime_seconds=args.max_runtime_seconds,
        end_time=parse_datetime(args.end_time) if args.end_time else None,
        now=parse_datetime(args.now) if args.now else None,
        open_price_records=load_records(args.btc_records_jsonl) if args.btc_records_jsonl else [],
    )
    print(json.dumps({"supervisor_jsonl": str(args.supervisor_jsonl), "stop_reason": stop}, sort_keys=True))
    return 0


def main() -> int:
    return asyncio.run(async_main(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
