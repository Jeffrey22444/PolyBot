from __future__ import annotations

import argparse
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from polybot.run_artifacts import SCHEMA_VERSION, read_json, write_json


STATUS_JSON = "status.json"
HEARTBEAT_JSONL = "heartbeat.jsonl"


class RecoverableRunError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def artifact_paths(run_dir: Path) -> dict[str, Path]:
    return {
        "manifest": run_dir / "run_manifest.json",
        "session_index": run_dir / "session_index.json",
        "status": run_dir / STATUS_JSON,
        "heartbeat": run_dir / HEARTBEAT_JSONL,
    }


def load_session_index(run_dir: Path) -> dict[str, Any]:
    path = artifact_paths(run_dir)["session_index"]
    if path.exists():
        return read_json(path)
    return {"schema_version": SCHEMA_VERSION, "sessions": []}


def update_manifest(run_dir: Path, status: str, **fields: Any) -> dict[str, Any]:
    path = artifact_paths(run_dir)["manifest"]
    manifest = read_json(path) if path.exists() else {"schema_version": SCHEMA_VERSION, "created_at": utc_now()}
    manifest.update(fields)
    manifest["status"] = status
    manifest["updated_at"] = utc_now()
    write_json(path, manifest)
    return manifest


def write_status(run_dir: Path, status: str, **fields: Any) -> dict[str, Any]:
    payload = {"schema_version": "phase13_long_run_v1", "status": status, "updated_at": utc_now(), **fields}
    write_json(artifact_paths(run_dir)["status"], payload)
    return payload


def heartbeat(run_dir: Path, status: str, **fields: Any) -> None:
    append_jsonl(artifact_paths(run_dir)["heartbeat"], {"timestamp": utc_now(), "status": status, **fields})


def done_keys(index: dict[str, Any]) -> set[str]:
    return {
        str(session.get("session_key"))
        for session in index.get("sessions", [])
        if session.get("result_status") in ("closed", "skipped")
    }


def add_or_replace_session(index: dict[str, Any], session: dict[str, Any]) -> None:
    sessions = index.setdefault("sessions", [])
    key = session.get("session_key")
    for offset, current in enumerate(sessions):
        if current.get("session_key") == key:
            sessions[offset] = session
            return
    sessions.append(session)


def run_step(session: dict[str, Any], failures_left: dict[str, int]) -> dict[str, Any]:
    key = str(session.get("session_key"))
    remaining = failures_left.get(key, 0)
    if remaining > 0:
        failures_left[key] = remaining - 1
        raise RecoverableRunError(session.get("fail_reason", "recoverable_error"))
    return {key: value for key, value in session.items() if key not in ("fail_attempts", "fail_reason")}


def run_long_run(
    run_dir: Path,
    planned_sessions: list[dict[str, Any]],
    *,
    resume: bool,
    max_sessions: int,
    max_runtime_seconds: float | None,
    retry_limit: int,
    retry_backoff_seconds: float,
    heartbeat_interval_seconds: float,
    stop_after_sessions: int | None = None,
    end_time: datetime | None = None,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    index = load_session_index(run_dir) if resume else {"schema_version": SCHEMA_VERSION, "sessions": []}
    completed = done_keys(index)
    failures_left = {str(session.get("session_key")): int(session.get("fail_attempts", 0)) for session in planned_sessions}
    processed = 0
    last_error = None
    last_session = None

    update_manifest(run_dir, "running", heartbeat_jsonl=HEARTBEAT_JSONL, status_json=STATUS_JSON)
    write_status(run_dir, "running", processed_sessions=0)
    heartbeat(run_dir, "running", processed_sessions=0)

    for session in planned_sessions:
        key = str(session.get("session_key"))
        if key in completed:
            heartbeat(run_dir, "resume_skipped", session_key=key, reason="already_closed_or_skipped")
            continue
        if processed >= max_sessions:
            break
        if max_runtime_seconds is not None and (time.monotonic() - started) >= max_runtime_seconds:
            break
        if end_time is not None and datetime.now(timezone.utc) >= end_time:
            break

        attempts = 0
        while True:
            try:
                result = run_step(session, failures_left)
                add_or_replace_session(index, result)
                completed.add(key)
                processed += 1
                last_session = key
                write_json(artifact_paths(run_dir)["session_index"], index)
                heartbeat(run_dir, "session_recorded", session_key=key, result_status=result.get("result_status"))
                write_status(run_dir, "running", processed_sessions=processed, last_session=last_session, last_error=last_error)
                break
            except RecoverableRunError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                attempts += 1
                heartbeat(run_dir, "recoverable_error", session_key=key, attempt=attempts, error=last_error)
                if attempts > retry_limit:
                    skipped = {
                        "session_key": key,
                        "market_id": session.get("market_id"),
                        "market_slug": session.get("market_slug"),
                        "market_start_time": session.get("market_start_time"),
                        "market_end_time": session.get("market_end_time"),
                        "runner_status": "skipped",
                        "resolution_status": "missing",
                        "result_status": "skipped",
                        "skip_reason": "retry_limit_reached",
                        "paper_pnl": None,
                    }
                    add_or_replace_session(index, skipped)
                    completed.add(key)
                    processed += 1
                    last_session = key
                    write_json(artifact_paths(run_dir)["session_index"], index)
                    heartbeat(run_dir, "retry_limit_reached", session_key=key, error=last_error)
                    write_status(run_dir, "running", processed_sessions=processed, last_session=last_session, last_error=last_error)
                    break
                if retry_backoff_seconds > 0:
                    time.sleep(retry_backoff_seconds)

        if heartbeat_interval_seconds >= 0:
            heartbeat(run_dir, "heartbeat", processed_sessions=processed, last_session=last_session)
        if stop_after_sessions is not None and processed >= stop_after_sessions:
            write_json(artifact_paths(run_dir)["session_index"], index)
            update_manifest(run_dir, "interrupted", last_session=last_session, processed_sessions=processed, last_error=last_error)
            status = write_status(run_dir, "interrupted", processed_sessions=processed, last_session=last_session, last_error=last_error)
            heartbeat(run_dir, "interrupted", processed_sessions=processed, last_session=last_session)
            return status

    write_json(artifact_paths(run_dir)["session_index"], index)
    status = write_status(run_dir, "stopped", processed_sessions=processed, last_session=last_session, last_error=last_error)
    update_manifest(run_dir, "stopped", last_session=last_session, processed_sessions=processed, last_error=last_error)
    heartbeat(run_dir, "stopped", processed_sessions=processed, last_session=last_session)
    return status


def sample_sessions() -> list[dict[str, Any]]:
    return [
        {
            "session_key": "01_market-current",
            "market_id": "market-current",
            "market_slug": "btc-15m-current",
            "market_start_time": "2026-07-06T12:00:00+00:00",
            "market_end_time": "2026-07-06T12:15:00+00:00",
            "runner_status": "finished",
            "resolution_status": "resolved",
            "result_status": "closed",
            "skip_reason": None,
            "paper_pnl": 11.0,
        },
        {
            "session_key": "02_market-next",
            "market_id": "market-next",
            "market_slug": "btc-15m-next",
            "market_start_time": "2026-07-06T12:15:00+00:00",
            "market_end_time": "2026-07-06T12:30:00+00:00",
            "runner_status": "skipped",
            "resolution_status": "missing",
            "result_status": "skipped",
            "skip_reason": "stale_open_price_record",
            "paper_pnl": None,
        },
        {
            "session_key": "03_market-retry",
            "market_id": "market-retry",
            "market_slug": "btc-15m-retry",
            "market_start_time": "2026-07-06T12:30:00+00:00",
            "market_end_time": "2026-07-06T12:45:00+00:00",
            "runner_status": "finished",
            "resolution_status": "resolved",
            "result_status": "closed",
            "skip_reason": None,
            "paper_pnl": 3.0,
            "fail_attempts": 1,
            "fail_reason": "simulated_open_price_timeout",
        },
        {
            "session_key": "04_market-fail",
            "market_id": "market-fail",
            "market_slug": "btc-15m-fail",
            "market_start_time": "2026-07-06T12:45:00+00:00",
            "market_end_time": "2026-07-06T13:00:00+00:00",
            "fail_attempts": 3,
            "fail_reason": "simulated_runner_error",
        },
    ]


def self_check() -> Path:
    run_dir = Path(tempfile.mkdtemp(prefix="polybot_phase13_long_run_")) / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    first_status = run_long_run(
        run_dir,
        sample_sessions(),
        resume=False,
        max_sessions=4,
        max_runtime_seconds=None,
        end_time=None,
        retry_limit=1,
        retry_backoff_seconds=0.0,
        heartbeat_interval_seconds=0.0,
        stop_after_sessions=2,
    )
    assert first_status["status"] == "interrupted"
    index_after_stop = read_json(artifact_paths(run_dir)["session_index"])
    assert len(index_after_stop["sessions"]) == 2

    second_status = run_long_run(
        run_dir,
        sample_sessions(),
        resume=True,
        max_sessions=4,
        max_runtime_seconds=None,
        end_time=None,
        retry_limit=1,
        retry_backoff_seconds=0.0,
        heartbeat_interval_seconds=0.0,
    )
    index = read_json(artifact_paths(run_dir)["session_index"])
    keys = [session["session_key"] for session in index["sessions"]]
    assert second_status["status"] == "stopped"
    assert keys == ["01_market-current", "02_market-next", "03_market-retry", "04_market-fail"]
    assert keys.count("01_market-current") == 1
    assert next(session for session in index["sessions"] if session["session_key"] == "04_market-fail")["skip_reason"] == "retry_limit_reached"
    manifest = read_json(artifact_paths(run_dir)["manifest"])
    assert manifest["status"] == "stopped"
    assert read_json(artifact_paths(run_dir)["status"])["status"] == "stopped"
    events = read_jsonl(artifact_paths(run_dir)["heartbeat"])
    assert any(event["status"] == "interrupted" for event in events)
    assert any(event["status"] == "resume_skipped" and event["session_key"] == "01_market-current" for event in events)
    assert any(event["status"] == "recoverable_error" for event in events)
    assert any(event["status"] == "retry_limit_reached" for event in events)
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process-local resumable paper long-run helper.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--session-plan-json", type=Path)
    parser.add_argument("--max-sessions", type=int, default=1)
    parser.add_argument("--max-runtime-seconds", type=float)
    parser.add_argument("--end-time")
    parser.add_argument("--heartbeat-interval-seconds", type=float, default=30.0)
    parser.add_argument("--retry-limit", type=int, default=1)
    parser.add_argument("--retry-backoff-seconds", type=float, default=1.0)
    parser.add_argument("--stop-after-sessions", type=int)
    return parser


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "run_dir": str(output)}, sort_keys=True))
        return 0

    if args.run_dir is None:
        raise SystemExit("missing required args: --run-dir")
    sessions = read_json(args.session_plan_json) if args.session_plan_json else []
    if not isinstance(sessions, list):
        raise SystemExit("--session-plan-json must contain a JSON list")
    status = run_long_run(
        args.run_dir,
        sessions,
        resume=args.resume,
        max_sessions=args.max_sessions,
        max_runtime_seconds=args.max_runtime_seconds,
        end_time=parse_datetime(args.end_time),
        retry_limit=args.retry_limit,
        retry_backoff_seconds=args.retry_backoff_seconds,
        heartbeat_interval_seconds=args.heartbeat_interval_seconds,
        stop_after_sessions=args.stop_after_sessions,
    )
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
