from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LEDGER_PATH = Path("data/paper_trades.sqlite3")
SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trades (
  market_id TEXT PRIMARY KEY,
  market_start_time TEXT,
  market_end_time TEXT,
  open_price REAL,
  open_price_source TEXT,
  threshold_pct REAL,
  observe_start_remaining_seconds INTEGER,
  decision_time TEXT,
  decision_remaining_seconds INTEGER,
  decision_move_pct REAL,
  signal TEXT,
  side TEXT,
  stake REAL,
  entry_avg_ask REAL,
  shares REAL,
  result TEXT,
  winning_side TEXT,
  paper_pnl REAL,
  cumulative_pnl REAL,
  equity_after REAL,
  return_pct REAL,
  skip_reason TEXT,
  created_at TEXT,
  updated_at TEXT
)
"""

COLUMNS = [
    "market_id",
    "market_start_time",
    "market_end_time",
    "open_price",
    "open_price_source",
    "threshold_pct",
    "observe_start_remaining_seconds",
    "decision_time",
    "decision_remaining_seconds",
    "decision_move_pct",
    "signal",
    "side",
    "stake",
    "entry_avg_ask",
    "shares",
    "result",
    "winning_side",
    "paper_pnl",
    "cumulative_pnl",
    "equity_after",
    "return_pct",
    "skip_reason",
    "created_at",
    "updated_at",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def upsert_trade(path: Path, **fields: Any) -> None:
    if not fields.get("market_id"):
        return
    now = utc_now()
    fields = {key: value for key, value in fields.items() if key in COLUMNS and value is not None}
    fields.setdefault("created_at", now)
    fields["updated_at"] = now
    columns = list(fields)
    placeholders = ", ".join("?" for _ in columns)
    updates = ", ".join(f"{column}=excluded.{column}" for column in columns if column not in ("market_id", "created_at"))
    sql = f"""
    INSERT INTO paper_trades ({", ".join(columns)}) VALUES ({placeholders})
    ON CONFLICT(market_id) DO UPDATE SET {updates}
    """
    with connect(path) as conn:
        conn.execute(sql, [fields[column] for column in columns])


def stats(path: Path, initial_bankroll: float) -> dict[str, Any]:
    with connect(path) as conn:
        rows = conn.execute("SELECT result, paper_pnl FROM paper_trades").fetchall()
    total_markets = len(rows)
    settled = [row for row in rows if row["result"] in ("WIN", "LOSS")]
    wins = sum(1 for row in settled if row["result"] == "WIN")
    cumulative_pnl = sum(float(row["paper_pnl"] or 0.0) for row in settled)
    equity = initial_bankroll + cumulative_pnl
    return {
        "total_markets": total_markets,
        "settled_count": len(settled),
        "win_rate": (wins / len(settled) * 100) if settled else 0.0,
        "cumulative_pnl": cumulative_pnl,
        "equity_after": equity,
        "return_pct": (cumulative_pnl / initial_bankroll * 100) if initial_bankroll else 0.0,
    }


def record_result(
    path: Path,
    market_id: str,
    result: str,
    initial_bankroll: float,
    winning_side: str | None = None,
    paper_pnl: float | None = None,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    upsert_trade(
        path,
        market_id=market_id,
        result=result,
        winning_side=winning_side,
        paper_pnl=paper_pnl if result in ("WIN", "LOSS") else None,
        skip_reason=skip_reason,
    )
    summary = stats(path, initial_bankroll)
    upsert_trade(
        path,
        market_id=market_id,
        cumulative_pnl=summary["cumulative_pnl"],
        equity_after=summary["equity_after"],
        return_pct=summary["return_pct"],
    )
    return summary


def rows(path: Path) -> list[dict[str, Any]]:
    with connect(path) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM paper_trades ORDER BY market_id")]


def self_check() -> dict[str, Any]:
    path = Path(tempfile.mkdtemp(prefix="polybot_trade_ledger_")) / "paper_trades.sqlite3"
    initial = 1000.0
    upsert_trade(path, market_id="m1", market_start_time="2026-07-08T00:00:00+00:00", result="PENDING")
    upsert_trade(path, market_id="m1", side="UP", stake=9.0, entry_avg_ask=0.84, shares=10.71)
    assert len(rows(path)) == 1
    win = record_result(path, "m1", "WIN", initial, winning_side="UP", paper_pnl=1.71)
    upsert_trade(path, market_id="m2", result="NO_TRADE", skip_reason="observation_window_no_signal", decision_remaining_seconds=19, decision_move_pct=0.0305)
    record_result(path, "m3", "LOSS", initial, winning_side="DOWN", paper_pnl=-9.0)
    record_result(path, "m4", "PENDING", initial, winning_side=None, paper_pnl=None)
    record_result(path, "m5", "SKIPPED", initial, skip_reason="not_closed")
    all_rows = rows(path)
    assert len(all_rows) == 5
    assert win["equity_after"] == 1001.71
    final = stats(path, initial)
    assert final["total_markets"] == 5
    assert final["settled_count"] == 2
    assert round(final["win_rate"], 6) == 50.0
    assert round(final["cumulative_pnl"], 6) == -7.29
    raw_names = {item[1] for item in sqlite3.connect(path).execute("PRAGMA table_info(paper_trades)").fetchall()}
    assert not {"raw_orderbook", "raw_tick", "raw_payload", "token_id"} & raw_names
    return {"path": str(path), "stats": final, "rows": all_rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal local paper trade ledger.")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        print(json.dumps(self_check(), sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
