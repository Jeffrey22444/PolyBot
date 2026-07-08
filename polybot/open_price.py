from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from polybot.market_data import CaptureRecord
from polybot.market_discovery import sample_payload, select_session


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
) -> dict[str, Any]:
    selection = session_config.get("selection", session_config)
    if not isinstance(selection, dict):
        raise ValueError("session config must contain a selection object")
    result = select_open_price(records, parse_datetime(selection["market_start_time"]), max_delay_seconds)
    enriched = {**selection, **result}
    return {"selection": enriched, "skip_reason": None if result["open_price_capture_status"] == "captured" else result["skip_reason"]}


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

    valid = enrich_session_config(
        session_config,
        [
            sample_record("99.90", start_ms - 1),
            sample_record("100.01", start_ms),
            sample_record("100.02", start_ms + 1000),
        ],
        5,
    )
    pre_start = enrich_session_config(session_config, [sample_record("99.90", start_ms - 1)], 5)
    stale = enrich_session_config(session_config, [sample_record("100.01", start_ms + 6000)], 5)
    invalid = enrich_session_config(
        session_config,
        [sample_record("0", start_ms), sample_record("not-a-number", start_ms + 1000)],
        5,
    )

    assert valid["selection"]["open_price"] == 100.01
    assert valid["selection"]["open_price_capture_status"] == "captured"
    assert pre_start["skip_reason"] == "no_post_start_record"
    assert stale["skip_reason"] == "stale_open_price_record"
    assert invalid["skip_reason"] == "invalid_open_price"

    write_json(output, valid)
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
