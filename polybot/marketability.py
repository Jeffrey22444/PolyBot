from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from polybot.market_data import CaptureRecord
from polybot.paper import (
    PaperSignalRecord,
    PaperTradeRecord,
    SkippedTradeRecord,
    signal_only_report,
    tradable_signal_report,
)
from polybot.signal import Signal


@dataclass(frozen=True)
class AskLevel:
    price: float
    size: float


@dataclass(frozen=True)
class FillSimulation:
    rejected: bool
    skip_reason: str | None
    stake: float
    shares: float
    executable_avg_ask: float | None


def ask_levels_from_market_record(record: CaptureRecord) -> list[AskLevel]:
    return [
        AskLevel(float(level["price"]), float(level["size"]))
        for level in record.payload.get("asks", [])
        if float(level.get("price", 0)) > 0 and float(level.get("size", 0)) > 0
    ]


def simulate_ask_depth_fill(asks: Iterable[AskLevel], stake: float) -> FillSimulation:
    if stake <= 0:
        return FillSimulation(True, "invalid_stake", stake, 0.0, None)

    remaining = stake
    spent = 0.0
    shares = 0.0

    for level in sorted(asks, key=lambda item: item.price):
        level_cost = level.price * level.size
        spend = min(remaining, level_cost)
        if spend <= 0:
            continue
        spent += spend
        shares += spend / level.price
        remaining -= spend
        if remaining <= 1e-9:
            break

    if shares == 0:
        return FillSimulation(True, "no_ask_depth", stake, 0.0, None)
    if remaining > 1e-9:
        return FillSimulation(True, "insufficient_ask_depth", stake, shares, spent / shares)
    return FillSimulation(False, None, stake, shares, spent / shares)


def kelly_fraction_reference(caller_supplied_p_hat: float, executable_avg_ask: float) -> float:
    return (caller_supplied_p_hat - executable_avg_ask) / (1 - executable_avg_ask)


def evaluate_marketability(
    signal: Signal,
    market_record: CaptureRecord,
    stake: float,
    caller_supplied_p_hat: float | None,
    p_hat_filter_enabled: bool = True,
) -> PaperTradeRecord | SkippedTradeRecord:
    if signal not in (Signal.UP, Signal.DOWN):
        return SkippedTradeRecord(signal, "no_valid_signal", stake)

    fill = simulate_ask_depth_fill(ask_levels_from_market_record(market_record), stake)
    if fill.rejected:
        return SkippedTradeRecord(signal, fill.skip_reason or "fill_rejected", stake)

    if not p_hat_filter_enabled:
        return PaperTradeRecord(
            signal=signal,
            stake=stake,
            shares=fill.shares,
            executable_avg_ask=fill.executable_avg_ask,
            caller_supplied_p_hat=caller_supplied_p_hat,
            trade_edge=None,
            kelly_fraction_reference=None,
        )

    if caller_supplied_p_hat is None:
        return SkippedTradeRecord(signal, "missing_p_hat", stake, fill.executable_avg_ask)
    if not 0 <= caller_supplied_p_hat <= 1:
        return SkippedTradeRecord(
            signal,
            "invalid_p_hat",
            stake,
            fill.executable_avg_ask,
            caller_supplied_p_hat,
        )

    trade_edge = caller_supplied_p_hat - fill.executable_avg_ask
    if trade_edge <= 0:
        return SkippedTradeRecord(
            signal,
            "non_positive_trade_edge",
            stake,
            fill.executable_avg_ask,
            caller_supplied_p_hat,
            trade_edge,
        )

    return PaperTradeRecord(
        signal=signal,
        stake=stake,
        shares=fill.shares,
        executable_avg_ask=fill.executable_avg_ask,
        caller_supplied_p_hat=caller_supplied_p_hat,
        trade_edge=trade_edge,
        kelly_fraction_reference=kelly_fraction_reference(
            caller_supplied_p_hat,
            fill.executable_avg_ask,
        ),
    )


def _book_record(asks: list[dict[str, str]]) -> CaptureRecord:
    return CaptureRecord(
        source="polymarket",
        event_type="book",
        source_timestamp_ms=1783327698002,
        local_receive_timestamp="2026-07-06T08:48:29.309337+00:00",
        payload={"event_type": "book", "timestamp": "1783327698002", "asks": asks},
    )


def _self_check() -> dict[str, object]:
    record = _book_record(
        [
            {"price": "0.40", "size": "10"},
            {"price": "0.50", "size": "20"},
        ]
    )
    fill = simulate_ask_depth_fill(ask_levels_from_market_record(record), 9.0)
    assert not fill.rejected
    assert round(fill.executable_avg_ask or 0, 6) == round(9.0 / 20.0, 6)

    insufficient = simulate_ask_depth_fill(ask_levels_from_market_record(record), 20.0)
    assert insufficient.rejected
    assert insufficient.skip_reason == "insufficient_ask_depth"

    missing_p_hat = evaluate_marketability(Signal.UP, record, 9.0, None)
    assert isinstance(missing_p_hat, SkippedTradeRecord)
    assert missing_p_hat.skip_reason == "missing_p_hat"
    assert missing_p_hat.trade_edge is None

    rejected = evaluate_marketability(Signal.UP, record, 9.0, 0.44)
    assert isinstance(rejected, SkippedTradeRecord)
    assert rejected.signal == Signal.UP
    assert rejected.skip_reason == "non_positive_trade_edge"

    accepted = evaluate_marketability(Signal.UP, record, 9.0, 0.55)
    assert isinstance(accepted, PaperTradeRecord)
    assert accepted.signal == Signal.UP
    assert round(accepted.trade_edge, 6) == round(0.55 - accepted.executable_avg_ask, 6)

    no_p_hat_filter = evaluate_marketability(Signal.UP, record, 9.0, None, p_hat_filter_enabled=False)
    assert isinstance(no_p_hat_filter, PaperTradeRecord)
    assert no_p_hat_filter.caller_supplied_p_hat is None
    assert no_p_hat_filter.trade_edge is None

    signal_report = signal_only_report(
        [
            PaperSignalRecord(
                signal_time=datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc),
                market_end_time=datetime(2026, 7, 6, 12, 15, tzinfo=timezone.utc),
                open_price=100.0,
                current_price=100.1,
                signal=Signal.UP,
            )
        ]
    )
    tradable_report = tradable_signal_report([accepted, missing_p_hat])
    assert signal_report == {"UP": 1, "DOWN": 0, "NO_SIGNAL": 0}
    assert tradable_report == {"filled": 1, "skip_reasons": {"missing_p_hat": 1}}
    return {
        "fill_executable_avg_ask": accepted.executable_avg_ask,
        "insufficient_depth_skip_reason": insufficient.skip_reason,
        "missing_p_hat_skip_reason": missing_p_hat.skip_reason,
        "missing_p_hat_trade_edge": missing_p_hat.trade_edge,
        "p_hat_filter_disabled_filled": isinstance(no_p_hat_filter, PaperTradeRecord),
        "signal_after_rejection": rejected.signal.value,
        "signal_only": signal_report,
        "tradable_signal": tradable_report,
    }


if __name__ == "__main__":
    print(json.dumps(_self_check(), sort_keys=True))
