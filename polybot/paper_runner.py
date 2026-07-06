from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from polybot.market_data import CaptureRecord, capture_btc_reference, capture_polymarket_market
from polybot.marketability import evaluate_marketability
from polybot.paper import PaperTradeRecord, SkippedTradeRecord
from polybot.signal import Signal, build_signal_record


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value


def append_jsonl(path: Path, record_type: str, payload: dict[str, Any]) -> None:
    record = {
        "record_type": record_type,
        "local_timestamp": utc_now().isoformat(),
        **jsonable(payload),
    }
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")


def latest_btc_price(records: list[CaptureRecord]) -> float | None:
    for record in reversed(records):
        price = record.payload.get("p")
        if price is not None:
            return float(price)
    return None


def latest_book(records: list[CaptureRecord]) -> CaptureRecord | None:
    for record in reversed(records):
        if record.source == "polymarket" and record.event_type == "book":
            return record
    return None


async def capture_session(asset_id: str, seconds: float, limit: int) -> tuple[list[CaptureRecord], list[CaptureRecord]]:
    market_task = capture_polymarket_market([asset_id], seconds, limit)
    btc_task = capture_btc_reference(seconds, limit)
    return await asyncio.gather(market_task, btc_task)


async def run_once(
    asset_id: str,
    open_price: float,
    market_end_time: datetime,
    stake: float,
    output: Path,
    seconds: float,
    caller_supplied_p_hat: float | None,
    market_records: list[CaptureRecord] | None = None,
    btc_records: list[CaptureRecord] | None = None,
    now: datetime | None = None,
) -> None:
    append_jsonl(output, "runtime_note", {"note": "runner_started", "asset_id": asset_id})

    if market_records is None or btc_records is None:
        try:
            market_records, btc_records = await capture_session(asset_id, seconds, limit=5)
        except Exception as exc:
            append_jsonl(output, "runtime_note", {"note": "capture_failed", "error": f"{type(exc).__name__}: {exc}"})
            market_records = market_records or []
            btc_records = btc_records or []

    for record in market_records + btc_records:
        append_jsonl(output, "runtime_note", {"note": "market_data_record", "record": record})

    current_price = latest_btc_price(btc_records)
    if current_price is None:
        append_jsonl(output, "runtime_note", {"note": "missing_btc_reference_price"})
        return

    signal_record = build_signal_record(
        open_price=open_price,
        current_price=current_price,
        market_end_time=market_end_time,
        now=now or utc_now(),
    )
    append_jsonl(output, "signal_record", {"record": signal_record})

    book = latest_book(market_records)
    if book is None:
        append_jsonl(output, "runtime_note", {"note": "missing_polymarket_book"})
        if signal_record.signal in (Signal.UP, Signal.DOWN):
            skipped = SkippedTradeRecord(signal_record.signal, "missing_polymarket_book", stake)
            append_jsonl(output, "skipped_trade_record", {"record": skipped})
        return

    decision = evaluate_marketability(
        signal=signal_record.signal,
        market_record=book,
        stake=stake,
        caller_supplied_p_hat=caller_supplied_p_hat,
    )
    if isinstance(decision, PaperTradeRecord):
        append_jsonl(output, "paper_trade_record", {"record": decision})
    else:
        append_jsonl(output, "skipped_trade_record", {"record": decision})


def sample_market_records() -> list[CaptureRecord]:
    return [
        CaptureRecord(
            source="polymarket",
            event_type="book",
            source_timestamp_ms=1783327698002,
            local_receive_timestamp="2026-07-06T08:48:29.309337+00:00",
            payload={
                "event_type": "book",
                "timestamp": "1783327698002",
                "asks": [{"price": "0.40", "size": "10"}, {"price": "0.50", "size": "20"}],
            },
        )
    ]


def sample_btc_records() -> list[CaptureRecord]:
    return [
        CaptureRecord(
            source="binance_btcusdt_trade",
            event_type="trade",
            source_timestamp_ms=1783327175287,
            local_receive_timestamp="2026-07-06T08:39:35.291306+00:00",
            payload={"e": "trade", "E": 1783327175287, "p": "100.06"},
        )
    ]


async def self_check() -> Path:
    output = Path(tempfile.gettempdir()) / "polybot_phase4_runner_self_check.jsonl"
    output.write_text("", encoding="utf-8")
    await run_once(
        asset_id="sample-asset",
        open_price=100.0,
        market_end_time=datetime(2026, 7, 6, 12, 15, tzinfo=timezone.utc),
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=0.55,
        market_records=sample_market_records(),
        btc_records=sample_btc_records(),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
    )
    await run_once(
        asset_id="sample-asset",
        open_price=100.0,
        market_end_time=datetime(2026, 7, 6, 12, 15, tzinfo=timezone.utc),
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=None,
        market_records=sample_market_records(),
        btc_records=sample_btc_records(),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
    )
    record_types = [json.loads(line)["record_type"] for line in output.read_text(encoding="utf-8").splitlines()]
    assert "runtime_note" in record_types
    assert "signal_record" in record_types
    assert "paper_trade_record" in record_types
    assert "skipped_trade_record" in record_types
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-market paper runner.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--polymarket-asset-id")
    parser.add_argument("--open-price", type=float)
    parser.add_argument("--market-end-time")
    parser.add_argument("--stake", type=float)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--output", type=Path)
    return parser


async def async_main(args: argparse.Namespace) -> int:
    if args.self_check:
        output = await self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    required = {
        "--polymarket-asset-id": args.polymarket_asset_id,
        "--open-price": args.open_price,
        "--market-end-time": args.market_end_time,
        "--stake": args.stake,
        "--output": args.output,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")

    args.output.write_text("", encoding="utf-8")
    await run_once(
        asset_id=args.polymarket_asset_id,
        open_price=args.open_price,
        market_end_time=parse_datetime(args.market_end_time),
        stake=args.stake,
        output=args.output,
        seconds=args.seconds,
        caller_supplied_p_hat=args.p_hat,
    )
    print(json.dumps({"output": str(args.output)}, sort_keys=True))
    return 0


def main() -> int:
    return asyncio.run(async_main(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
