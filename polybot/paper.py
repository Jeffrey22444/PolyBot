from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from polybot.signal import Signal


@dataclass(frozen=True)
class PaperSignalRecord:
    signal_time: datetime
    market_end_time: datetime
    open_price: float
    current_price: float
    signal: Signal


@dataclass(frozen=True)
class PaperTradeRecord:
    signal: Signal
    stake: float
    shares: float
    executable_avg_ask: float
    caller_supplied_p_hat: float
    trade_edge: float
    kelly_fraction_reference: float


@dataclass(frozen=True)
class SkippedTradeRecord:
    signal: Signal
    skip_reason: str
    stake: float
    executable_avg_ask: float | None = None
    caller_supplied_p_hat: float | None = None
    trade_edge: float | None = None


def signal_only_report(records: Iterable[PaperSignalRecord]) -> dict[str, int]:
    counts = {Signal.UP.value: 0, Signal.DOWN.value: 0, Signal.NO_SIGNAL.value: 0}
    for record in records:
        counts[record.signal.value] += 1
    return counts


def tradable_signal_report(
    records: Iterable[PaperTradeRecord | SkippedTradeRecord],
) -> dict[str, object]:
    filled = 0
    skip_reasons: dict[str, int] = {}
    for record in records:
        if isinstance(record, PaperTradeRecord):
            filled += 1
        else:
            skip_reasons[record.skip_reason] = skip_reasons.get(record.skip_reason, 0) + 1
    return {"filled": filled, "skip_reasons": skip_reasons}
