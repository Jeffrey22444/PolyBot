from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Collection


DEFAULT_ENTRY_REMAIN_SECONDS = (180, 240)


class Signal(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NO_SIGNAL = "NO_SIGNAL"


@dataclass(frozen=True)
class SignalRecord:
    now: datetime
    market_end_time: datetime
    open_price: float
    current_price: float
    remaining_seconds: int
    ret_pct: float
    signal: Signal


def generate_signal(
    open_price: float,
    current_price: float,
    market_end_time: datetime,
    now: datetime,
    entry_remain_seconds: Collection[int] = DEFAULT_ENTRY_REMAIN_SECONDS,
    move_threshold_pct: float = 0.05,
    observe_start_remaining_seconds: int | None = None,
) -> Signal:
    if open_price <= 0 or current_price <= 0:
        return Signal.NO_SIGNAL

    remaining_seconds = int((market_end_time - now).total_seconds())
    if observe_start_remaining_seconds is None:
        eligible = remaining_seconds in entry_remain_seconds
    else:
        eligible = 0 <= remaining_seconds <= observe_start_remaining_seconds
    if not eligible:
        return Signal.NO_SIGNAL

    ret_pct = (current_price - open_price) / open_price * 100
    if abs(ret_pct) < move_threshold_pct:
        return Signal.NO_SIGNAL
    if ret_pct > 0:
        return Signal.UP
    if ret_pct < 0:
        return Signal.DOWN
    return Signal.NO_SIGNAL


def build_signal_record(
    open_price: float,
    current_price: float,
    market_end_time: datetime,
    now: datetime,
    entry_remain_seconds: Collection[int] = DEFAULT_ENTRY_REMAIN_SECONDS,
    move_threshold_pct: float = 0.05,
    observe_start_remaining_seconds: int | None = None,
) -> SignalRecord:
    ret_pct = 0.0
    if open_price > 0 and current_price > 0:
        ret_pct = (current_price - open_price) / open_price * 100

    return SignalRecord(
        now=now,
        market_end_time=market_end_time,
        open_price=open_price,
        current_price=current_price,
        remaining_seconds=int((market_end_time - now).total_seconds()),
        ret_pct=ret_pct,
        signal=generate_signal(
            open_price,
            current_price,
            market_end_time,
            now,
            entry_remain_seconds,
            move_threshold_pct,
            observe_start_remaining_seconds,
        ),
    )


def _self_check() -> None:
    end = datetime(2026, 7, 6, 12, 15, tzinfo=timezone.utc)
    now_3m = datetime(2026, 7, 6, 12, 12, tzinfo=timezone.utc)
    now_4m = datetime(2026, 7, 6, 12, 11, tzinfo=timezone.utc)

    assert generate_signal(100.0, 100.06, end, now_3m, (180, 240), 0.05) == Signal.UP
    assert generate_signal(100.0, 100.06, end, now_4m, (180, 240), 0.05) == Signal.UP
    assert generate_signal(100.0, 99.94, end, now_3m, (180, 240), 0.05) == Signal.DOWN
    assert (
        generate_signal(100.0, 100.04, end, now_3m, (180, 240), 0.05)
        == Signal.NO_SIGNAL
    )
    assert (
        generate_signal(
            100.0,
            100.06,
            end,
            datetime(2026, 7, 6, 12, 10, tzinfo=timezone.utc),
            (180, 240),
            0.05,
        )
        == Signal.NO_SIGNAL
    )
    assert (
        generate_signal(
            100.0,
            100.06,
            end,
            datetime(2026, 7, 6, 12, 10, tzinfo=timezone.utc),
            move_threshold_pct=0.05,
            observe_start_remaining_seconds=300,
        )
        == Signal.UP
    )
    assert build_signal_record(100.0, 100.06, end, now_3m).signal == Signal.UP


if __name__ == "__main__":
    _self_check()
    print("signal self-check passed")
