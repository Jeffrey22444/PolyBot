from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from polybot.result_closer import close_results, load_jsonl, parse_winning_side, write_summary
from polybot.signal import Signal


def load_resolution_map(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping = data.get("resolutions", data) if isinstance(data, dict) else {}
    if not isinstance(mapping, dict):
        raise ValueError("resolution map must be a JSON object")
    return {str(key): str(value) for key, value in mapping.items()}


def resolution_for(session: dict[str, Any], runner_output: str, resolutions: dict[str, str]) -> tuple[str | None, str | None]:
    market_id = (session or {}).get("market_id")
    key = str(market_id) if market_id is not None else None
    if key and key in resolutions:
        return resolutions[key], key
    if runner_output in resolutions:
        return resolutions[runner_output], runner_output
    return None, None


def empty_counts() -> dict[str, int]:
    return {Signal.UP.value: 0, Signal.DOWN.value: 0, Signal.NO_SIGNAL.value: 0}


def add_counts(total: dict[str, int], counts: dict[str, int]) -> None:
    for side in total:
        total[side] += int(counts.get(side, 0))


def batch_close(supervisor_jsonl: Path, resolutions: dict[str, str]) -> dict[str, Any]:
    supervisor_records = load_jsonl(supervisor_jsonl)
    base_dir = supervisor_jsonl.parent
    per_session: list[dict[str, Any]] = []
    skipped_reasons: dict[str, int] = {}
    aggregate_counts = empty_counts()
    aggregate_pnl = 0.0

    def skip(event: dict[str, Any], reason: str, runner_output: str | None = None) -> None:
        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
        per_session.append(
            {
                "status": "skipped",
                "skip_reason": reason,
                "session": event.get("session", {}),
                "runner_output": runner_output,
            }
        )

    for event in supervisor_records:
        record_type = event.get("record_type")
        if record_type == "session_runner_skipped":
            skip(event, event.get("skip_reason", "runner_skipped"), event.get("runner_output"))
            continue
        if record_type != "session_runner_finished":
            continue

        runner_output = event.get("runner_output")
        if not runner_output:
            skip(event, "missing_runner_output")
            continue

        runner_path = Path(runner_output)
        if not runner_path.is_absolute():
            runner_path = base_dir / runner_path
        if not runner_path.exists():
            skip(event, "missing_runner_file", str(runner_path))
            continue

        winning_side, resolution_key = resolution_for(event.get("session", {}), str(runner_output), resolutions)
        if winning_side is None:
            skip(event, "missing_resolution", str(runner_path))
            continue
        try:
            winning_side = parse_winning_side(winning_side)
        except ValueError:
            skip(event, "invalid_winning_side", str(runner_path))
            continue

        summary = close_results(load_jsonl(runner_path), winning_side)
        add_counts(aggregate_counts, summary["signal_only"]["counts"])
        aggregate_pnl += float(summary["tradable_signal"]["total_paper_pnl"])
        per_session.append(
            {
                "status": "closed",
                "session": event.get("session", {}),
                "runner_output": str(runner_path),
                "resolution_key": resolution_key,
                "winning_side": winning_side,
                "summary": summary,
            }
        )

    closed = [item for item in per_session if item["status"] == "closed"]
    skipped = [item for item in per_session if item["status"] == "skipped"]
    return {
        "supervisor_jsonl": str(supervisor_jsonl),
        "sessions_seen": len(per_session),
        "sessions_closed": len(closed),
        "sessions_skipped": len(skipped),
        "skipped_reasons": skipped_reasons,
        "per_session": per_session,
        "aggregate_signal_only_counts": aggregate_counts,
        "aggregate_tradable_paper_pnl": aggregate_pnl,
    }


def self_check() -> Path:
    output_dir = Path(tempfile.gettempdir()) / "polybot_phase10_supervisor_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_one = output_dir / "session_1_market-current.jsonl"
    runner_two = output_dir / "session_2_market-next.jsonl"
    supervisor_jsonl = output_dir / "supervisor.jsonl"
    resolution_json = output_dir / "resolutions.json"
    output = output_dir / "batch_summary.json"

    runner_one.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True)
            for record in [
                {"record_type": "signal_record", "record": {"signal": "UP"}},
                {"record_type": "signal_record", "record": {"signal": "DOWN"}},
                {"record_type": "paper_trade_record", "record": {"signal": "UP", "stake": 9.0, "shares": 20.0}},
                {"record_type": "paper_trade_record", "record": {"signal": "DOWN", "stake": 4.0, "shares": 8.0}},
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner_two.write_text(
        json.dumps({"record_type": "signal_record", "record": {"signal": "DOWN"}}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    supervisor_jsonl.write_text(
        "\n".join(
            json.dumps(record, sort_keys=True)
            for record in [
                {"record_type": "session_runner_finished", "session": {"market_id": "market-current"}, "runner_output": str(runner_one)},
                {"record_type": "session_runner_finished", "session": {"market_id": "market-next"}, "runner_output": str(runner_two)},
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    resolution_json.write_text(json.dumps({"market-current": "UP"}, sort_keys=True) + "\n", encoding="utf-8")

    summary = batch_close(supervisor_jsonl, load_resolution_map(resolution_json))
    write_summary(output, summary)

    assert summary["sessions_seen"] == 2
    assert summary["sessions_closed"] == 1
    assert summary["sessions_skipped"] == 1
    assert summary["skipped_reasons"] == {"missing_resolution": 1}
    assert summary["aggregate_signal_only_counts"] == {"UP": 1, "DOWN": 1, "NO_SIGNAL": 0}
    assert summary["aggregate_tradable_paper_pnl"] == 7.0
    assert summary["per_session"][0]["summary"]["signal_only"]["counts"] == {"UP": 1, "DOWN": 1, "NO_SIGNAL": 0}
    assert summary["per_session"][0]["summary"]["tradable_signal"]["total_paper_pnl"] == 7.0
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Close Phase 9 supervisor runner outputs with explicit resolutions.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--supervisor-jsonl", type=Path)
    parser.add_argument("--resolution-map", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    required = {
        "--supervisor-jsonl": args.supervisor_jsonl,
        "--resolution-map": args.resolution_map,
        "--output": args.output,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")

    summary = batch_close(args.supervisor_jsonl, load_resolution_map(args.resolution_map))
    write_summary(args.output, summary)
    print(json.dumps({"output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
