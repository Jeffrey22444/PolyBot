from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from polybot.supervisor_results import batch_close, load_resolution_map


SCHEMA_VERSION = "phase12_run_artifacts_v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_key(value: Any) -> str:
    text = str(value or "session").strip().lower()
    return re.sub(r"[^a-z0-9_.-]+", "-", text).strip("-") or "session"


def rel(run_dir: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    return path.relative_to(run_dir).as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_file(source: Path | None, dest: Path) -> Path | None:
    if source is None or not source.exists():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != dest.resolve():
        shutil.copyfile(source, dest)
    return dest


def session_key(position: int, session: dict[str, Any]) -> str:
    return f"{position:02d}_{safe_key(session.get('market_id') or session.get('market_slug') or position)}"


def build_session_entry(
    run_dir: Path,
    position: int,
    item: dict[str, Any],
    raw_resolution_paths: dict[str, Path] | None = None,
    resolution_paths: dict[str, Path] | None = None,
    resolution_skips: dict[str, str] | None = None,
) -> dict[str, Any]:
    session = item.get("session") or {}
    key = session_key(position, session)
    session_dir = run_dir / "sessions" / key
    market_id = session.get("market_id")

    runner_source = Path(item["runner_output"]) if item.get("runner_output") else None
    runner_path = copy_file(runner_source, session_dir / "runner.jsonl")

    resolution_path = None
    raw_path = None
    result_path = None
    paper_pnl = None
    resolution_status = "missing"
    result_status = item.get("status", "unknown")
    skip_reason = item.get("skip_reason")

    if item.get("status") == "closed":
        resolution_status = "resolved"
        paper_pnl = float(item["summary"]["tradable_signal"]["total_paper_pnl"])
        resolution_path = session_dir / "resolution.json"
        write_json(
            resolution_path,
            {
                "market_id": market_id,
                "resolution_key": item.get("resolution_key"),
                "winning_side": item.get("winning_side"),
            },
        )
        raw_path = copy_file((raw_resolution_paths or {}).get(str(market_id)), session_dir / "resolution_raw.json")
        result_path = session_dir / "result.json"
        write_json(result_path, item)
    elif skip_reason:
        result_status = "skipped"
        if market_id is not None and str(market_id) in (resolution_skips or {}):
            resolution_status = "skipped"
            resolution_path = copy_file((resolution_paths or {}).get(str(market_id)), session_dir / "resolution.json")
            raw_path = copy_file((raw_resolution_paths or {}).get(str(market_id)), session_dir / "resolution_raw.json")
            skip_reason = (resolution_skips or {})[str(market_id)]

    return {
        "session_key": key,
        "market_id": market_id,
        "market_slug": session.get("market_slug"),
        "market_start_time": session.get("market_start_time"),
        "market_end_time": session.get("market_end_time"),
        "runner_output": rel(run_dir, runner_path),
        "runner_status": "finished" if runner_path else "skipped",
        "resolution_status": resolution_status,
        "resolution_path": rel(run_dir, resolution_path),
        "resolution_raw_path": rel(run_dir, raw_path),
        "result_status": result_status,
        "result_path": rel(run_dir, result_path),
        "skip_reason": skip_reason,
        "paper_pnl": paper_pnl,
    }


def build_run_artifacts(
    run_dir: Path,
    supervisor_jsonl: Path,
    batch_summary: dict[str, Any],
    *,
    run_id: str,
    mode: str,
    config_snapshot: dict[str, Any] | None = None,
    raw_resolution_paths: dict[str, Path] | None = None,
    resolution_paths: dict[str, Path] | None = None,
    resolution_skips: dict[str, str] | None = None,
    status: str = "completed",
) -> dict[str, Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    supervisor_path = copy_file(supervisor_jsonl, run_dir / "supervisor.jsonl")
    summary_path = run_dir / "summary.json"
    session_index_path = run_dir / "session_index.json"
    manifest_path = run_dir / "run_manifest.json"

    sessions = [
        build_session_entry(run_dir, index, item, raw_resolution_paths, resolution_paths, resolution_skips)
        for index, item in enumerate(batch_summary.get("per_session", []), start=1)
    ]
    write_json(session_index_path, {"schema_version": SCHEMA_VERSION, "sessions": sessions})
    compact_summary = {key: value for key, value in batch_summary.items() if key != "per_session"}
    compact_summary["supervisor_jsonl"] = rel(run_dir, supervisor_path)
    write_json(summary_path, compact_summary)

    timestamp = utc_now()
    write_json(
        manifest_path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "mode": mode,
            "config_snapshot": config_snapshot or {},
            "supervisor_jsonl": rel(run_dir, supervisor_path),
            "session_index": rel(run_dir, session_index_path),
            "summary": rel(run_dir, summary_path),
            "status": status,
        },
    )
    return {"run_dir": run_dir, "manifest": manifest_path, "session_index": session_index_path, "summary": summary_path}


def self_check() -> Path:
    root = Path(tempfile.mkdtemp(prefix="polybot_phase12_run_artifacts_"))
    source_dir = root / "source"
    run_dir = root / "run"
    source_dir.mkdir(parents=True, exist_ok=True)

    runner_one = source_dir / "session_1_market-current.jsonl"
    runner_one.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True)
            for record in [
                {"record_type": "signal_record", "record": {"signal": "UP"}},
                {"record_type": "paper_trade_record", "record": {"signal": "UP", "stake": 9.0, "shares": 20.0}},
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    supervisor_jsonl = source_dir / "supervisor.jsonl"
    supervisor_jsonl.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True)
            for record in [
                {
                    "record_type": "session_runner_finished",
                    "session": {
                        "market_id": "market-current",
                        "market_slug": "btc-15m-current",
                        "market_start_time": "2026-07-06T12:00:00+00:00",
                        "market_end_time": "2026-07-06T12:15:00+00:00",
                    },
                    "runner_output": str(runner_one),
                },
                {
                    "record_type": "session_runner_skipped",
                    "session": {
                        "market_id": "market-next",
                        "market_slug": "btc-15m-next",
                        "market_start_time": "2026-07-06T12:15:00+00:00",
                        "market_end_time": "2026-07-06T12:30:00+00:00",
                    },
                    "skip_reason": "stale_open_price_record",
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    resolution_map = source_dir / "resolution_map.json"
    resolution_map.write_text(json.dumps({"resolutions": {"market-current": "UP"}}, sort_keys=True) + "\n", encoding="utf-8")
    raw_resolution = source_dir / "resolution_raw_market-current.json"
    raw_resolution.write_text(json.dumps({"id": "market-current", "closed": True}, sort_keys=True) + "\n", encoding="utf-8")

    summary = batch_close(supervisor_jsonl, load_resolution_map(resolution_map))
    paths = build_run_artifacts(
        run_dir,
        supervisor_jsonl,
        summary,
        run_id="self-check-run",
        mode="self_check",
        config_snapshot={"max_sessions": 2},
        raw_resolution_paths={"market-current": raw_resolution},
    )

    manifest = read_json(paths["manifest"])
    index = read_json(paths["session_index"])
    compact_summary = read_json(paths["summary"])
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["status"] == "completed"
    assert (run_dir / manifest["supervisor_jsonl"]).exists()
    assert len(index["sessions"]) == 2
    closed = index["sessions"][0]
    skipped = index["sessions"][1]
    assert closed["result_status"] == "closed"
    assert closed["runner_output"] == "sessions/01_market-current/runner.jsonl"
    assert closed["resolution_path"] == "sessions/01_market-current/resolution.json"
    assert closed["resolution_raw_path"] == "sessions/01_market-current/resolution_raw.json"
    assert closed["result_path"] == "sessions/01_market-current/result.json"
    assert closed["paper_pnl"] == 11.0
    assert skipped["result_status"] == "skipped"
    assert skipped["skip_reason"] == "stale_open_price_record"
    assert compact_summary["sessions_closed"] == 1
    assert "per_session" not in compact_summary
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build stable local run artifacts around paper-run outputs.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--supervisor-jsonl", type=Path)
    parser.add_argument("--batch-summary", type=Path)
    parser.add_argument("--run-id", default="paper-run")
    parser.add_argument("--mode", default="paper")
    parser.add_argument("--config-json", type=Path)
    parser.add_argument("--status", default="completed")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "run_dir": str(output)}, sort_keys=True))
        return 0

    required = {
        "--run-dir": args.run_dir,
        "--supervisor-jsonl": args.supervisor_jsonl,
        "--batch-summary": args.batch_summary,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")

    config = read_json(args.config_json) if args.config_json else {}
    paths = build_run_artifacts(
        args.run_dir,
        args.supervisor_jsonl,
        read_json(args.batch_summary),
        run_id=args.run_id,
        mode=args.mode,
        config_snapshot=config,
        status=args.status,
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
