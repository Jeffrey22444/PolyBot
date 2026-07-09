# Polymarket Paper Trader Logic Chain

This document is the shared human-readable strategy reference for the PolyBot
BTC 15m paper trader.

When any zone discusses BTC 15m paper-trading behavior, entry timing,
configuration, `p_hat`, operator output, or acceptance criteria, read this file
before making recommendations or code changes.

## Source Of Truth

- Active strategy consensus: this file.
- Operator commands: `docs/operator_runbook.md`.
- Local supervision: `docs/local_process_supervision.md`.
- Current task surface: `docs/project_notes/current_task.md`.

Do not infer current strategy behavior from older phase notes.

## Current Purpose

The current goal is to run local paper trading for BTC 15-minute Up/Down
Polymarket sessions, then use recorded paper results for review and future
strategy decisions.

This is not a live-trading design. The bot does not place real orders, use
wallet signing, or move real funds.

Each BTC 15-minute market should be treated as one independent paper-trade
record. The long-term review source should be a minimal local ledger with one
row per market, not only end-of-run artifacts.

## Current Strategy In One Paragraph

The bot watches a BTC 15-minute Up/Down Polymarket session. It records the BTC
price at market open. When the market enters the final configurable observation
window, defaulting to the last 300 seconds, it continuously observes BTC price
movement from that open price. If the absolute move reaches the configured
threshold, defaulting to `0.15%`, the bot creates one directional signal in the
same direction as the move. After a signal exists, it checks whether the matching
UP or DOWN token is tradable at real ask-side depth with the fixed paper stake.
An optional `p_hat` marketability filter may reject trades whose executable ask
price is too expensive. The bot then records the paper trade or skip reason and
later scores the paper result from public resolution data when available.

## Current Parameters

These are the current parameters that directly affect strategy or paper-trade
decisions. They are intended to be configurable through the active YAML task.

| Parameter | Current default | Meaning |
| --- | ---: | --- |
| Market type | BTC Up/Down | Only BTC binary direction markets are in scope. |
| Market duration | 15 minutes | The root strategy is calibrated around 15-minute sessions. |
| Observation window start | `300` seconds remaining | Start continuous signal observation when the market has 5 minutes left. |
| Move threshold | `0.15%` | BTC must move at least this far from market open to create a signal. |
| Max entries per market | `1` | The first valid threshold crossing can create one paper entry. |
| Paper stake | `5%` of settled simulated equity | Default simulated spend per accepted paper trade; with initial equity `1000`, the first stake is `50`. |
| Manual paper stake override | unset | `--paper-stake` can pin a fixed simulated spend for a run. |
| `p_hat` filter | disabled | Optional marketability filter, not part of the root signal. |
| `p_hat` value | `0.55` | Caller-supplied win-probability input only when the filter is enabled. |
| Open-price capture window | `8` seconds | Time budget to capture BTC trades around market open. |
| Max open-price delay | `5` seconds | The open price must be fresh enough after market start. |
| Observation tick | `1` second | Intended cadence for checking threshold crossing inside the window. |
| Runner capture window | `8` seconds | Time budget to capture entry-time BTC/orderbook data. |
| Heartbeat interval | `30` seconds | Local runtime status heartbeat, not terminal spam. |

## Step By Step Logic

### 1. Find The Next BTC 15m Market

The run searches public Polymarket metadata for BTC 15-minute Up/Down markets.
The current search phrase is:

```text
bitcoin up down 15m
```

The bot proceeds only when it can identify one valid next session and map the UP
and DOWN token ids unambiguously. If the public metadata is missing, ambiguous,
closed, archived, or not accepting orders, the bot records a skip reason and
does not guess.

### 2. Record The BTC Open Price

At the selected market's start time, the bot should use a Polymarket-aligned
open/reference price when that public source is available.

If a Polymarket-aligned open/reference price is not available from public data,
the bot may use a clearly labeled fallback source. The fallback source must be
recorded; it must not be presented as a Polymarket open price. Every later
signal compares against the recorded open price and its source.

### 3. Start The Observation Window

The strategy observes continuously during the final configurable window of the
15-minute market. The current default is:

```text
observe_start_remaining_seconds = 300
```

Human reading: when the market has 5 minutes left, start watching BTC movement
from the recorded open price.

### 4. Watch For A Threshold Crossing

During the observation window, the bot repeatedly compares current BTC price
with the recorded market-open BTC price:

```text
move_pct = (current_btc_price - open_btc_price) / open_btc_price * 100
```

Human reading:

- `move_pct` is positive when BTC is above the market-open price.
- `move_pct` is negative when BTC is below the market-open price.
- The absolute size of `move_pct` must reach the configured threshold.

### 5. Create One Root Signal

The signal rule is deliberately small:

- If BTC is up by at least the threshold, signal `UP`.
- If BTC is down by at least the threshold, signal `DOWN`.
- If BTC never reaches the threshold before the market ends, signal `NO_SIGNAL`
  and do not enter.

The first valid threshold crossing creates at most one paper entry for that
market.

The signal step does not look at Polymarket ask prices, liquidity, `p_hat`,
Kelly, paper PnL, wallet state, or execution details. It only answers: "Has BTC
moved enough from open, and in which direction?"

### 6. Select The Matching Polymarket Token

Only after the root signal exists does the runner choose a Polymarket token:

- `UP` signal uses the UP token id.
- `DOWN` signal uses the DOWN token id.
- `NO_SIGNAL` selects no token and creates no paper trade.

### 7. Check Whether The Signal Is Tradable

A valid signal is not automatically a paper trade. The bot next checks the
selected token's real ask-side order book.

It simulates spending the fixed paper stake against the cheapest available asks
first. This gives the executable average ask price for the whole simulated fill.

The paper trade is rejected when:

- no ask depth is available
- ask depth cannot fill the fixed paper stake
- the selected token id is missing
- the Polymarket book cannot be captured

This keeps the result honest: a correct signal still counts as untradable if the
public order book cannot support the simulated buy.

### 8. Optionally Apply The `p_hat` Filter

`p_hat` is a caller-supplied marketability filter. It is not trained, inferred,
smoothed, or backfilled by the bot.

When the filter is enabled, the edge check is:

```text
trade_edge = p_hat - executable_avg_ask
```

The paper trade is accepted only when:

- `p_hat` is between `0` and `1`
- `trade_edge` is greater than `0`
- the fixed paper stake can be filled from ask depth

When the filter is disabled, the bot still requires a valid signal, mapped
token, and sufficient ask depth. It simply does not reject the trade because of
missing or non-positive `p_hat` edge.

Kelly may be recorded as a reference value when `p_hat` is enabled, but it does
not size the current paper stake.

By default, the current paper stake is `current settled simulated equity *
paper.stake_fraction`. Settled equity is `paper.initial_bankroll` plus
cumulative PnL from `WIN` and `LOSS` ledger rows only; `PENDING`, `SKIPPED`, and
`NO_TRADE` rows do not change equity. A manual `--paper-stake` value overrides
that fraction for the run.

### 9. Resolve And Score Paper Results

When public Polymarket metadata later shows an unambiguous binary result, the
bot maps the winning outcome back to UP or DOWN.

For accepted paper trades:

```text
if signal direction equals winning side:
    paper_pnl = shares - stake
else:
    paper_pnl = -stake
```

If public resolution is ambiguous, disputed, not closed, non-binary, or missing
clean terminal prices, the bot records a skip reason instead of inferring the
winner.

Existing ledger rows with result `PENDING` are retried when a paper run starts,
after each session, and during final/interrupted run close. The retry path uses
public market metadata by `market_id` and the same conservative resolution logic
above. If the public metadata is still unclear, the ledger row remains
`PENDING`; the bot does not infer settlement from frontend display text or BTC
close movement.

## Minimal Review Ledger

The local paper system should keep one minimal record per 15-minute market so a
future review can use however many markets have completed so far.

The ledger should support these questions without storing raw market noise:

- overall win rate over a period
- total paper PnL over a period
- simulated equity and return percentage from a configurable initial bankroll,
  defaulting to `1000`
- failure conditions, especially remaining time, move percentage, threshold,
  side, price source, and skip reason

The ledger should not store raw WebSocket ticks, full order books, full public
payloads, or UI-oriented details.

The simulated bankroll is accounting-only. It must not change signal
generation, marketability, or paper fill behavior. Its current approved sizing
use is only the default `paper.stake_fraction` calculation described above.

## What The Strategy Does Not Do

The current logic intentionally does not include:

- live orders, wallet signing, account API usage, or real funds
- a trained `p_hat` model
- stop-loss, take-profit, averaging, reversal, grid, or multi-entry rules
- midpoint, last-trade, or spread-based edge checks
- cloud database or cloud deployment assumptions

## Required Result Split

Reviews must keep these two views separate:

- Signal-only view: whether the root BTC direction signal was right.
- Tradable-signal view: whether that signal could pass ask-depth and optional
  `p_hat` filtering as a paper trade.

This split is important because a good or bad directional signal should not be
hidden by marketability failures, and an untradable signal should not be counted
as if it were actually executable.
