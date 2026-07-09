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
from polybot.market_discovery import sample_payload, select_session
from polybot.open_price import POLYMARKET_CHAINLINK_SOURCE
from polybot.paper import PaperTradeRecord, SkippedTradeRecord
from polybot.runtime_config import configured_move_threshold_pct
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
        if record.source != POLYMARKET_CHAINLINK_SOURCE:
            continue
        price = record.payload.get("p")
        if price is not None:
            return float(price)
    return None


def latest_book(records: list[CaptureRecord]) -> CaptureRecord | None:
    for record in reversed(records):
        if record.source == "polymarket" and record.event_type == "book":
            return record
    return None


def session_selection(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    selection = data.get("selection", data) if isinstance(data, dict) else None
    if not isinstance(selection, dict):
        raise ValueError("session config must contain a selection object")
    return selection


def session_summary(selection: dict[str, Any]) -> dict[str, Any]:
    return {
        "market_id": selection.get("market_id"),
        "event_id": selection.get("event_id"),
        "market_slug": selection.get("market_slug"),
        "event_slug": selection.get("event_slug"),
    }


def selected_token(selection: dict[str, Any], signal: Signal) -> dict[str, str | None]:
    if signal == Signal.UP:
        side = "UP"
        token_id = selection.get("up_token_id")
    elif signal == Signal.DOWN:
        side = "DOWN"
        token_id = selection.get("down_token_id")
    else:
        return {"side": None, "token_id": None, "label": None}
    labels = selection.get("selected_side_labels") or {}
    return {"side": side, "token_id": token_id, "label": labels.get(side, side)}


def session_open_price(cli_open_price: float | None, session: dict[str, Any]) -> float:
    value = cli_open_price if cli_open_price is not None else session.get("open_price")
    if value is None:
        raise ValueError("missing_open_price")
    return float(value)


def parse_entry_remain_seconds(value: str) -> tuple[int, ...]:
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


async def run_session_once(
    session: dict[str, Any],
    open_price: float,
    stake: float,
    output: Path,
    seconds: float,
    caller_supplied_p_hat: float | None,
    market_records: list[CaptureRecord] | None = None,
    btc_records: list[CaptureRecord] | None = None,
    now: datetime | None = None,
    entry_remain_seconds: tuple[int, ...] = (180, 240),
    *,
    move_threshold_pct: float,
    observe_start_remaining_seconds: int | None = 300,
    p_hat_filter_enabled: bool = True,
    market_seconds: float | None = None,
    btc_seconds: float | None = None,
) -> dict[str, Any]:
    session_meta = session_summary(session)
    append_jsonl(output, "runtime_note", {"note": "session_runner_started", "session": session_meta})

    if btc_records is None:
        try:
            btc_records = await capture_btc_reference(btc_seconds if btc_seconds is not None else seconds, limit=5)
        except Exception as exc:
            append_jsonl(output, "runtime_note", {"note": "btc_capture_failed", "session": session_meta, "error": f"{type(exc).__name__}: {exc}"})
            btc_records = []

    for record in btc_records:
        append_jsonl(output, "runtime_note", {"note": "market_data_record", "session": session_meta, "record": record})

    current_price = latest_btc_price(btc_records)
    if current_price is None:
        append_jsonl(output, "runtime_note", {"note": "missing_btc_reference_price", "session": session_meta})
        return {"status": "skipped", "reason": "missing_btc_reference_price"}

    signal_now = now or utc_now()
    signal_record = build_signal_record(
        open_price=open_price,
        current_price=current_price,
        market_end_time=parse_datetime(session["market_end_time"]),
        now=signal_now,
        entry_remain_seconds=entry_remain_seconds,
        move_threshold_pct=move_threshold_pct,
        observe_start_remaining_seconds=observe_start_remaining_seconds,
    )
    append_jsonl(output, "signal_record", {"session": session_meta, "record": signal_record})

    token = selected_token(session, signal_record.signal)
    if signal_record.signal == Signal.NO_SIGNAL:
        append_jsonl(output, "runtime_note", {"note": "no_signal_no_token_selected", "session": session_meta, "selected_token": token})
        return {"status": "no_signal", "signal_record": signal_record}
    if not token["token_id"]:
        append_jsonl(output, "runtime_note", {"note": "missing_token_id", "session": session_meta, "selected_token": token})
        skipped = SkippedTradeRecord(signal_record.signal, "missing_token_id", stake)
        append_jsonl(output, "skipped_trade_record", {"session": session_meta, "selected_token": token, "record": skipped})
        return {"status": "skipped", "reason": "missing_token_id", "signal_record": signal_record, "decision": skipped, "selected_token": token}

    append_jsonl(output, "runtime_note", {"note": "selected_token", "session": session_meta, "selected_token": token})
    if market_records is None:
        try:
            market_records = await capture_polymarket_market([str(token["token_id"])], market_seconds if market_seconds is not None else seconds, limit=5)
        except Exception as exc:
            append_jsonl(output, "runtime_note", {"note": "market_capture_failed", "session": session_meta, "selected_token": token, "error": f"{type(exc).__name__}: {exc}"})
            market_records = []

    for record in market_records:
        append_jsonl(output, "runtime_note", {"note": "market_data_record", "session": session_meta, "selected_token": token, "record": record})

    book = latest_book(market_records)
    if book is None:
        append_jsonl(output, "runtime_note", {"note": "missing_polymarket_book", "session": session_meta, "selected_token": token})
        skipped = SkippedTradeRecord(signal_record.signal, "missing_polymarket_book", stake)
        append_jsonl(output, "skipped_trade_record", {"session": session_meta, "selected_token": token, "record": skipped})
        return {"status": "skipped", "reason": "missing_polymarket_book", "signal_record": signal_record, "decision": skipped, "selected_token": token}

    decision = evaluate_marketability(
        signal=signal_record.signal,
        market_record=book,
        stake=stake,
        caller_supplied_p_hat=caller_supplied_p_hat,
        p_hat_filter_enabled=p_hat_filter_enabled,
    )
    record_type = "paper_trade_record" if isinstance(decision, PaperTradeRecord) else "skipped_trade_record"
    append_jsonl(output, record_type, {"session": session_meta, "selected_token": token, "record": decision})
    if isinstance(decision, PaperTradeRecord):
        return {"status": "paper_opened", "signal_record": signal_record, "decision": decision, "selected_token": token}
    return {"status": "skipped", "reason": decision.skip_reason, "signal_record": signal_record, "decision": decision, "selected_token": token}


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
    threshold = configured_move_threshold_pct()
    return sample_btc_records_with_price(str(100.0 * (1 + (threshold + 0.01) / 100)))


def sample_btc_records_with_price(price: str) -> list[CaptureRecord]:
    return [
        CaptureRecord(
            source=POLYMARKET_CHAINLINK_SOURCE,
            event_type="chainlink_candle",
            source_timestamp_ms=1783327175287,
            local_receive_timestamp="2026-07-06T08:39:35.291306+00:00",
            payload={"p": price},
        )
    ]


async def self_check() -> Path:
    return await session_self_check()


async def session_self_check() -> Path:
    output = Path(tempfile.gettempdir()) / "polybot_phase7_session_runner_self_check.jsonl"
    output.write_text("", encoding="utf-8")
    threshold = configured_move_threshold_pct()
    up_price = str(100.0 * (1 + (threshold + 0.01) / 100))
    down_price = str(100.0 * (1 - (threshold + 0.01) / 100))
    no_signal_price = str(100.0 * (1 + max(threshold - 0.01, 0.0) / 100))
    session = select_session(
        sample_payload(),
        datetime(2026, 7, 6, 12, 5, tzinfo=timezone.utc),
        20,
        "current",
        paper_stake=9.0,
        caller_supplied_p_hat=0.55,
    )["selection"]
    assert session is not None

    await run_session_once(
        session=session,
        open_price=100.0,
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=0.55,
        market_records=sample_market_records(),
        btc_records=sample_btc_records_with_price(up_price),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
        move_threshold_pct=threshold,
    )
    await run_session_once(
        session=session,
        open_price=100.0,
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=None,
        p_hat_filter_enabled=False,
        market_records=sample_market_records(),
        btc_records=sample_btc_records_with_price(up_price),
        now=datetime(2026, 7, 6, 12, 10, tzinfo=timezone.utc),
        observe_start_remaining_seconds=300,
        move_threshold_pct=threshold,
    )
    await run_session_once(
        session=session,
        open_price=100.0,
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=0.55,
        market_records=sample_market_records(),
        btc_records=sample_btc_records_with_price(down_price),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
        move_threshold_pct=threshold,
    )
    await run_session_once(
        session=session,
        open_price=100.0,
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=0.55,
        market_records=sample_market_records(),
        btc_records=sample_btc_records_with_price(no_signal_price),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
        move_threshold_pct=threshold,
    )
    missing_down = {**session, "down_token_id": None}
    await run_session_once(
        session=missing_down,
        open_price=100.0,
        stake=9.0,
        output=output,
        seconds=1.0,
        caller_supplied_p_hat=0.55,
        market_records=sample_market_records(),
        btc_records=sample_btc_records_with_price(down_price),
        now=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
        move_threshold_pct=threshold,
    )

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    selected = [record["selected_token"] for record in records if record.get("note") == "selected_token"]
    assert selected[0]["side"] == "UP"
    assert selected[0]["token_id"] == "up-token-current"
    assert selected[1]["side"] == "UP"
    assert selected[1]["token_id"] == "up-token-current"
    assert selected[2]["side"] == "DOWN"
    assert selected[2]["token_id"] == "down-token-current"
    assert any(record.get("note") == "no_signal_no_token_selected" for record in records)
    assert not any(record["record_type"] == "paper_trade_record" and record.get("record", {}).get("signal") == "NO_SIGNAL" for record in records)
    assert any(record.get("note") == "missing_token_id" for record in records)
    assert any(record["record_type"] == "paper_trade_record" and record.get("record", {}).get("caller_supplied_p_hat") is None for record in records)
    assert session_open_price(None, {**session, "open_price": 101.0}) == 101.0
    assert session_open_price(102.0, {**session, "open_price": 101.0}) == 102.0
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-market paper runner.")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--session-self-check", action="store_true")
    parser.add_argument("--session-config", type=Path)
    parser.add_argument("--open-price", type=float)
    parser.add_argument("--stake", type=float)
    parser.add_argument("--p-hat", type=float)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--entry-remain-seconds", default="180,240")
    parser.add_argument("--observe-start-remaining-seconds", type=int, default=300)
    parser.add_argument("--move-threshold-pct", type=float)
    parser.add_argument("--output", type=Path)
    return parser


async def async_main(args: argparse.Namespace) -> int:
    if args.self_check:
        output = await self_check()
        print(json.dumps({"self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0
    if args.session_self_check:
        output = await session_self_check()
        print(json.dumps({"session_self_check": "passed", "output": str(output)}, sort_keys=True))
        return 0

    if args.session_config:
        required = {
            "--output": args.output,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise SystemExit(f"missing required args: {', '.join(missing)}")
        session = session_selection(args.session_config)
        try:
            open_price = session_open_price(args.open_price, session)
        except ValueError:
            raise SystemExit("missing required open price: pass --open-price or include open_price in session config")
        stake = args.stake if args.stake is not None else session.get("paper_stake")
        if stake is None:
            raise SystemExit("missing required stake: pass --stake or include paper_stake in session config")
        p_hat = args.p_hat if args.p_hat is not None else session.get("caller_supplied_p_hat")
        move_threshold_pct = args.move_threshold_pct
        if move_threshold_pct is None:
            move_threshold_pct = session.get("move_threshold_pct")
        if move_threshold_pct is None:
            move_threshold_pct = configured_move_threshold_pct()
        args.output.write_text("", encoding="utf-8")
        await run_session_once(
            session=session,
            open_price=open_price,
            stake=float(stake),
            output=args.output,
            seconds=args.seconds,
            caller_supplied_p_hat=p_hat,
            entry_remain_seconds=parse_entry_remain_seconds(args.entry_remain_seconds),
            move_threshold_pct=float(move_threshold_pct),
            observe_start_remaining_seconds=args.observe_start_remaining_seconds,
        )
        print(json.dumps({"output": str(args.output)}, sort_keys=True))
        return 0

    raise SystemExit("missing required args: --session-config")


def main() -> int:
    return asyncio.run(async_main(build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
