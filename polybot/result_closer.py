from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from polybot.signal import Signal


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def parse_winning_side(value: str) -> str:
    side = value.upper()
    if side not in (Signal.UP.value, Signal.DOWN.value):
        raise ValueError("winning side must be UP or DOWN")
    return side


def close_results(records: list[dict[str, Any]], winning_side: str) -> dict[str, Any]:
    winning_side = parse_winning_side(winning_side)
    signal_counts = {Signal.UP.value: 0, Signal.DOWN.value: 0, Signal.NO_SIGNAL.value: 0}
    skipped_reasons: dict[str, int] = {}
    paper_pnl: list[dict[str, float | str]] = []

    for event in records:
        record_type = event.get("record_type")
        record = event.get("record", {})
        if record_type == "signal_record":
            signal = record.get("signal")
            if signal in signal_counts:
                signal_counts[signal] += 1
        elif record_type == "paper_trade_record":
            signal = record["signal"]
            stake = float(record["stake"])
            shares = float(record["shares"])
            pnl = shares - stake if signal == winning_side else -stake
            paper_pnl.append({"signal": signal, "stake": stake, "shares": shares, "paper_pnl": pnl})
        elif record_type == "skipped_trade_record":
            reason = record.get("skip_reason", "unknown")
            skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1

    total_paper_pnl = sum(item["paper_pnl"] for item in paper_pnl)
    return {
        "winning_side": winning_side,
        "signal_only": {
            "counts": signal_counts,
            "winning_side_count": signal_counts[winning_side],
            "losing_side_count": signal_counts[Signal.DOWN.value if winning_side == Signal.UP.value else Signal.UP.value],
            "no_signal_count": signal_counts[Signal.NO_SIGNAL.value],
        },
        "tradable_signal": {
            "filled_count": len(paper_pnl),
            "skipped_reasons": skipped_reasons,
            "paper_pnl": paper_pnl,
            "total_paper_pnl": total_paper_pnl,
        },
    }


def write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")


def self_check() -> Path:
    runner_jsonl = Path(tempfile.gettempdir()) / "polybot_phase5_runner_sample.jsonl"
    output = Path(tempfile.gettempdir()) / "polybot_phase5_result_summary.json"
    sample = [
        {"record_type": "signal_record", "record": {"signal": "UP"}},
        {"record_type": "signal_record", "record": {"signal": "DOWN"}},
        {"record_type": "signal_record", "record": {"signal": "NO_SIGNAL"}},
        {"record_type": "paper_trade_record", "record": {"signal": "UP", "stake": 9.0, "shares": 20.0}},
        {"record_type": "paper_trade_record", "record": {"signal": "DOWN", "stake": 4.0, "shares": 8.0}},
        {"record_type": "skipped_trade_record", "record": {"signal": "UP", "skip_reason": "missing_p_hat", "stake": 9.0}},
    ]
    runner_jsonl.write_text("\n".join(json.dumps(record, sort_keys=True) for record in sample) + "\n", encoding="utf-8")
    summary = close_results(load_jsonl(runner_jsonl), "UP")
    write_summary(output, summary)

    assert summary["signal_only"]["counts"] == {"UP": 1, "DOWN": 1, "NO_SIGNAL": 1}
    assert summary["tradable_signal"]["filled_count"] == 2
    assert summary["tradable_signal"]["skipped_reasons"] == {"missing_p_hat": 1}
    assert summary["tradable_signal"]["paper_pnl"][0]["paper_pnl"] == 11.0
    assert summary["tradable_signal"]["paper_pnl"][1]["paper_pnl"] == -4.0
    assert summary["tradable_signal"]["total_paper_pnl"] == 7.0
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Close Phase 4 paper runner results.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--runner-jsonl", type=Path)
    parser.add_argument("--winning-side")
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    required = {
        "--runner-jsonl": args.runner_jsonl,
        "--winning-side": args.winning_side,
        "--output": args.output,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")

    summary = close_results(load_jsonl(args.runner_jsonl), args.winning_side)
    write_summary(args.output, summary)
    print(json.dumps({"output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
