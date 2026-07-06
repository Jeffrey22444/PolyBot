# Implementation Plan

## Delivery Strategy

Build a thin paper-trading slice first.

Do not mix these concerns in the same phase:

- root signal generation
- live market capture
- marketability at real ask/depth
- paper fill and reporting

Each phase ends with a gate. If the gate is not met, the next phase should not start.

Target operating shape:

- unattended paper trading
- continuous operation across every 15-minute BTC market
- no live orders until a future planning phase explicitly opens live trading

## Phase 1: Root Signal And Paper Skeleton

Runtime:

- Python standard library only
- no third-party dependencies
- no network access

Deliver:

- minimal `polybot/` package only if needed for the signal module
- one pure signal module
- one minimal record shape for signal or paper events
- one minimal test or self-check path for signal behavior, such as `python -m polybot.signal`

Verify:

- signal returns `UP` for positive move above threshold inside the target time window
- signal returns `DOWN` for negative move above threshold inside the target time window
- signal returns `NO_SIGNAL` when move is below threshold
- signal code has no dependency on ask, depth, spread, Kelly, `p_hat`, or account balance

Gate:

- a reviewer can point to one isolated signal module and one runnable signal verification path
- no WebSocket, live order, or marketability logic has leaked into the phase

## Phase 2: WebSocket-First Market Capture

Deliver:

- Polymarket market-data capture using WebSocket first
- BTC reference price capture using WebSocket first where available
- timestamped raw records with data-age fields
- REST startup or reconnect fallback only

Verify:

- live capture produces Polymarket market data records
- live capture produces BTC reference price records
- records include source timestamps and local receive timestamps
- no order placement path exists

Gate:

- Phase 3 can consume captured market/orderbook data without redefining capture logic
- unresolved API mismatches are documented instead of silently worked around

## Phase 3: Marketability And Paper Fill

Rules:

- `p_hat` is caller-supplied only.
- Do not implement a `p_hat` model.
- Do not place live orders.

Deliver:

- marketability module that consumes a valid signal
- ask-depth fill simulation
- fixed small paper stake with Kelly cap/reference
- skip reasons for rejected paper trades
- separate `signal-only` and `tradable-signal` reports

Verify:

- fill simulation uses ask-side depth, not midpoint or last trade
- a signal can exist even when the paper trade is skipped
- rejected trades store a reason
- reports preserve separate signal-only and tradable-signal views
- `p_hat` is not estimated inside Phase 3

Gate:

- signal logic remains unchanged except for integration wiring
- no live order path exists

## Phase 4: Single-Market Paper Runner

Rules:

- Run one explicitly configured market/session only.
- Do not discover or rotate markets yet.
- Do not estimate `p_hat`; accept a caller-supplied value or skip marketability when missing.
- Do not calculate final settlement PnL yet.

Deliver:

- one paper runner module
- CLI/config inputs for token IDs, open price, market end time, stake, and caller-supplied `p_hat`
- a short live loop that wires Signal, Market Data, Marketability, and Paper Fill
- JSONL records for signals, fills, skips, and runtime notes

Verify:

- runner can run for a short configured duration
- runner records a signal or explicit no-signal state
- runner records filled/skipped paper-trade decisions when orderbook data is available
- no order placement path exists

Gate:

- a known market can be monitored without manual code edits
- Phase 5 can consume runner JSONL records without redefining signal or fill logic

## Phase 5: Settlement And Result Closing

Rules:

- Close recorded paper-runner trades only.
- Winning side must be explicit input or come from a verified resolution record.
- Do not discover markets or rotate sessions.
- Do not estimate `p_hat`.
- Do not place live orders.

Deliver:

- result closer for runner records
- winning-side input from verified market resolution data or an explicit manual override path
- PnL calculation for paper trades
- signal-only and tradable-signal result output

Verify:

- a sample runner JSONL can be closed with explicit winning side
- filled paper trades produce win/loss and PnL
- skipped trades remain skipped and do not affect PnL
- signal-only and tradable-signal outputs stay separate

Gate:

- a completed market can be closed and scored from recorded paper-runner data

## Phase 6: Market Discovery And Session Rotation

Deliver:

- current/next BTC 15-minute market discovery
- token/outcome mapping validation
- open/end time extraction
- unattended session rotation
- safe skip reasons when discovery or resolution rules are unclear

Gate:

- runner can move from one 15-minute BTC market to the next without manual market IDs

## Unresolved Before Later Phases

Do not let execution answer these silently:

- final `p_hat` model
- long-run storage schema beyond assigned phase needs
- live trading path
- optimizer or parameter sweep
- pause or stop-trading automation
- multi-entry or richer position management
