from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import websockets


POLYMARKET_MARKET_WS = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
BINANCE_BTC_TRADE_WS = "wss://stream.binance.com:9443/ws/btcusdt@trade"


@dataclass(frozen=True)
class CaptureRecord:
    source: str
    event_type: str
    source_timestamp_ms: int | None
    local_receive_timestamp: str
    payload: dict[str, Any]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def source_timestamp_ms(payload: dict[str, Any]) -> int | None:
    for key in ("timestamp", "E", "T"):
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def build_record(source: str, event_type: str, payload: dict[str, Any]) -> CaptureRecord:
    return CaptureRecord(
        source=source,
        event_type=event_type,
        source_timestamp_ms=source_timestamp_ms(payload),
        local_receive_timestamp=utc_now().isoformat(),
        payload=payload,
    )


def write_jsonl(path: Path, records: Iterable[CaptureRecord]) -> None:
    with path.open("a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(asdict(record), sort_keys=True) + "\n")


async def capture_polymarket_market(
    asset_ids: list[str],
    seconds: float,
    limit: int,
) -> list[CaptureRecord]:
    if not asset_ids:
        return []

    records: list[CaptureRecord] = []
    deadline = asyncio.get_running_loop().time() + seconds
    subscription = {
        "assets_ids": asset_ids,
        "type": "market",
        "custom_feature_enabled": True,
    }

    async with websockets.connect(POLYMARKET_MARKET_WS) as websocket:
        await websocket.send(json.dumps(subscription))
        while len(records) < limit:
            timeout = deadline - asyncio.get_running_loop().time()
            if timeout <= 0:
                break
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                break
            payload = json.loads(message)
            if isinstance(payload, list):
                records.extend(
                    build_record("polymarket", item.get("event_type", "unknown"), item)
                    for item in payload
                    if isinstance(item, dict)
                )
            elif isinstance(payload, dict):
                records.append(
                    build_record("polymarket", payload.get("event_type", "unknown"), payload)
                )
    return records[:limit]


async def capture_btc_reference(seconds: float, limit: int) -> list[CaptureRecord]:
    records: list[CaptureRecord] = []
    deadline = asyncio.get_running_loop().time() + seconds

    async with websockets.connect(BINANCE_BTC_TRADE_WS) as websocket:
        while len(records) < limit:
            timeout = deadline - asyncio.get_running_loop().time()
            if timeout <= 0:
                break
            payload = json.loads(await asyncio.wait_for(websocket.recv(), timeout=timeout))
            records.append(build_record("binance_btcusdt_trade", payload.get("e", "unknown"), payload))
    return records


async def run_demo(args: argparse.Namespace) -> int:
    if args.self_check:
        _self_check()
        print("market data self-check passed")
        return 0

    all_records: list[CaptureRecord] = []
    notes: list[str] = []

    if args.polymarket_asset_id:
        try:
            before_count = len(all_records)
            all_records.extend(
                await capture_polymarket_market(
                    args.polymarket_asset_id,
                    args.seconds,
                    args.limit,
                )
            )
            if len(all_records) == before_count:
                notes.append("polymarket_connected_no_event_before_timeout")
        except Exception as exc:
            notes.append(f"polymarket_blocked={type(exc).__name__}: {exc}")
    else:
        notes.append("polymarket_blocked=missing --polymarket-asset-id")

    try:
        all_records.extend(await capture_btc_reference(args.seconds, args.limit))
    except Exception as exc:
        notes.append(f"btc_reference_blocked={type(exc).__name__}: {exc}")

    if args.output and all_records:
        write_jsonl(args.output, all_records)

    print(json.dumps({"records": len(all_records), "notes": notes}, sort_keys=True))
    for record in all_records:
        print(json.dumps(asdict(record), sort_keys=True))
    return 0 if all_records else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Short Phase 2 WebSocket capture demo.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--polymarket-asset-id", action="append", default=[])
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--output", type=Path)
    return parser


def _self_check() -> None:
    record = build_record(
        "example",
        "trade",
        {"E": "1783327175287", "p": "62863.17"},
    )
    assert record.source == "example"
    assert record.event_type == "trade"
    assert record.source_timestamp_ms == 1783327175287
    assert record.local_receive_timestamp.endswith("+00:00")
    assert record.payload["p"] == "62863.17"

    polymarket_record = build_record(
        "polymarket",
        "book",
        {"event_type": "book", "timestamp": "1783327698002"},
    )
    assert polymarket_record.source_timestamp_ms == 1783327698002


def main() -> int:
    return asyncio.run(run_demo(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
