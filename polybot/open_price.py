from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from polybot.market_data import CaptureRecord
from polybot.market_discovery import fetch_json, sample_payload, select_session


POLYMARKET_CHAINLINK_CANDLES_URL = "https://polymarket.com/api/chainlink-candles"
POLYMARKET_CHAINLINK_SOURCE = "polymarket_chainlink"


def parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def record_time(record: CaptureRecord) -> datetime:
    if record.source_timestamp_ms is not None:
        return datetime.fromtimestamp(record.source_timestamp_ms / 1000, tz=timezone.utc)
    return parse_datetime(record.local_receive_timestamp)


def record_price(record: CaptureRecord) -> float | None:
    try:
        price = float(record.payload.get("p"))
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def chainlink_candles_url(symbol: str = "BTC", interval: str = "15m", limit: int = 30) -> str:
    return f"{POLYMARKET_CHAINLINK_CANDLES_URL}?{urlencode({'symbol': symbol, 'interval': interval, 'limit': limit})}"


def extract_candles(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("candles", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def candle_time(value: Any) -> datetime | None:
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            numeric = float(value)
            if numeric > 10_000_000_000:
                numeric = numeric / 1000
            return datetime.fromtimestamp(numeric, tz=timezone.utc)
        if isinstance(value, str):
            return parse_datetime(value)
    except (OSError, ValueError):
        return None
    return None


def positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def chainlink_session_prices(
    session: dict[str, Any],
    fetcher: Any = fetch_json,
) -> dict[str, Any]:
    payload, source_timestamp = fetcher(chainlink_candles_url())
    start = parse_datetime(session["market_start_time"])
    end = parse_datetime(session["market_end_time"])
    for candle in extract_candles(payload):
        timestamp = candle_time(candle.get("time") or candle.get("timestamp"))
        if timestamp is None or not (start <= timestamp < end):
            continue
        open_price = positive_float(candle.get("open"))
        current_price = positive_float(candle.get("close"))
        if open_price is None:
            return {"skip_reason": "invalid_chainlink_open_price", "raw_payload": payload, "source_timestamp": source_timestamp}
        if current_price is None:
            return {"skip_reason": "invalid_chainlink_current_price", "raw_payload": payload, "source_timestamp": source_timestamp}
        timestamp_text = timestamp.isoformat()
        return {
            "open_price_capture_status": "captured",
            "open_price": open_price,
            "open_price_timestamp": timestamp_text,
            "open_price_source": POLYMARKET_CHAINLINK_SOURCE,
            "current_price": current_price,
            "current_price_timestamp": timestamp_text,
            "current_price_source": POLYMARKET_CHAINLINK_SOURCE,
            "raw_payload": payload,
            "source_timestamp": source_timestamp,
        }
    return {"skip_reason": "missing_chainlink_session_candle", "raw_payload": payload, "source_timestamp": source_timestamp}


def chainlink_price_record(price: float, timestamp: str) -> CaptureRecord:
    parsed = parse_datetime(timestamp)
    return CaptureRecord(
        source=POLYMARKET_CHAINLINK_SOURCE,
        event_type="chainlink_candle",
        source_timestamp_ms=int(parsed.timestamp() * 1000),
        local_receive_timestamp=datetime.now(timezone.utc).isoformat(),
        payload={"p": str(price), "source": POLYMARKET_CHAINLINK_SOURCE},
    )


def select_open_price(
    records: list[CaptureRecord],
    market_start_time: datetime,
    max_delay_seconds: float,
) -> dict[str, Any]:
    post_start = sorted(
        (record for record in records if record_time(record) >= market_start_time),
        key=record_time,
    )
    if not post_start:
        return {"open_price_capture_status": "skipped", "skip_reason": "no_post_start_record"}

    for record in post_start:
        timestamp = record_time(record)
        delay = (timestamp - market_start_time).total_seconds()
        if delay > max_delay_seconds:
            return {"open_price_capture_status": "skipped", "skip_reason": "stale_open_price_record"}
        price = record_price(record)
        if price is None:
            continue
        return {
            "open_price_capture_status": "captured",
            "open_price": price,
            "open_price_timestamp": timestamp.isoformat(),
            "open_price_source": record.source,
            "open_price_max_delay_seconds": max_delay_seconds,
        }
    return {"open_price_capture_status": "skipped", "skip_reason": "invalid_open_price"}


def enrich_session_config(
    session_config: dict[str, Any],
    records: list[CaptureRecord],
    max_delay_seconds: float,
    chainlink_fetcher: Any = fetch_json,
) -> dict[str, Any]:
    selection = session_config.get("selection", session_config)
    if not isinstance(selection, dict):
        raise ValueError("session config must contain a selection object")
    try:
        result = chainlink_session_prices(selection, chainlink_fetcher)
    except Exception as exc:
        result = {"skip_reason": f"chainlink_price_blocked={type(exc).__name__}: {exc}"}
    if result.get("open_price_capture_status") == "captured":
        clean_result = {key: value for key, value in result.items() if key != "raw_payload"}
        clean_result["open_price_max_delay_seconds"] = max_delay_seconds
        return {"selection": {**selection, **clean_result}, "skip_reason": None, "raw_payload": result.get("raw_payload")}
    chainlink_reason = result.get("skip_reason") or "missing_chainlink_aligned_open_price"
    fallback_result = select_open_price(records, parse_datetime(selection["market_start_time"]), max_delay_seconds)
    fallback_reason = chainlink_reason
    if fallback_result["open_price_capture_status"] == "captured":
        fallback_reason = "binance_btcusdt_fallback_not_allowed_for_signal"
    enriched = {**selection, **fallback_result, "open_price_source": "binance_btcusdt_fallback" if fallback_result["open_price_capture_status"] == "captured" else None}
    return {"selection": enriched, "skip_reason": fallback_reason}


def load_records(path: Path) -> list[CaptureRecord]:
    records: list[CaptureRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        records.append(
            CaptureRecord(
                source=item["source"],
                event_type=item["event_type"],
                source_timestamp_ms=item.get("source_timestamp_ms"),
                local_receive_timestamp=item["local_receive_timestamp"],
                payload=item["payload"],
            )
        )
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def sample_record(price: str, timestamp_ms: int) -> CaptureRecord:
    return CaptureRecord(
        source="binance_btcusdt_trade",
        event_type="trade",
        source_timestamp_ms=timestamp_ms,
        local_receive_timestamp=datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat(),
        payload={"e": "trade", "E": timestamp_ms, "p": price},
    )


def sample_chainlink_fetcher(start_timestamp: int) -> Any:
    def fetcher(url: str) -> tuple[dict[str, Any], str]:
        return {
            "candles": [
                {"time": start_timestamp, "open": 100.05, "high": 100.2, "low": 99.8, "close": 100.01},
                {"time": start_timestamp + 900, "open": 101.05, "high": 101.2, "low": 100.8, "close": 101.01},
            ]
        }, "fixture"

    return fetcher


def empty_chainlink_fetcher(url: str) -> tuple[dict[str, Any], str]:
    return {
        "candles": []
    }, "fixture"


def self_check() -> Path:
    output = Path(tempfile.gettempdir()) / "polybot_phase8_enriched_session_config.json"
    session_config = select_session(
        sample_payload(),
        datetime(2026, 7, 6, 12, 5, tzinfo=timezone.utc),
        20,
        "current",
        paper_stake=9.0,
        caller_supplied_p_hat=0.55,
    )
    start_ms = int(parse_datetime(session_config["selection"]["market_start_time"]).timestamp() * 1000)

    polymarket_valid = enrich_session_config(session_config, [], 5, sample_chainlink_fetcher(start_ms // 1000))
    fallback_session = {"selection": {**session_config["selection"], "polymarket_open_price": None, "polymarket_open_price_source": None}}
    valid = enrich_session_config(
        fallback_session,
        [
            sample_record("99.90", start_ms - 1),
            sample_record("100.01", start_ms),
            sample_record("100.02", start_ms + 1000),
        ],
        5,
        empty_chainlink_fetcher,
    )
    pre_start = enrich_session_config(fallback_session, [sample_record("99.90", start_ms - 1)], 5, empty_chainlink_fetcher)
    stale = enrich_session_config(fallback_session, [sample_record("100.01", start_ms + 6000)], 5, empty_chainlink_fetcher)
    invalid = enrich_session_config(
        fallback_session,
        [sample_record("0", start_ms), sample_record("not-a-number", start_ms + 1000)],
        5,
        empty_chainlink_fetcher,
    )

    assert polymarket_valid["selection"]["open_price"] == 100.05
    assert polymarket_valid["selection"]["current_price"] == 100.01
    assert polymarket_valid["selection"]["open_price_source"] == POLYMARKET_CHAINLINK_SOURCE
    assert valid["skip_reason"] == "binance_btcusdt_fallback_not_allowed_for_signal"
    assert valid["selection"]["open_price_source"] == "binance_btcusdt_fallback"
    assert pre_start["skip_reason"] == "missing_chainlink_session_candle"
    assert stale["skip_reason"] == "missing_chainlink_session_candle"
    assert invalid["skip_reason"] == "missing_chainlink_session_candle"

    write_json(output, polymarket_valid)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enrich one session config with BTC open price.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--session-config", type=Path)
    parser.add_argument("--records-jsonl", type=Path)
    parser.add_argument("--max-open-price-delay-seconds", type=float, default=5.0)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_check:
        output = self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    required = {
        "--session-config": args.session_config,
        "--records-jsonl": args.records_jsonl,
        "--output": args.output,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise SystemExit(f"missing required args: {', '.join(missing)}")

    session_config = json.loads(args.session_config.read_text(encoding="utf-8"))
    enriched = enrich_session_config(
        session_config,
        load_records(args.records_jsonl),
        args.max_open_price_delay_seconds,
    )
    write_json(args.output, enriched)
    print(json.dumps({"output": str(args.output), "skip_reason": enriched.get("skip_reason")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
