# Polymarket Paper Trader v1 Consensus

## Status

This document is the current source of truth for strategy behavior.

- Build paper trading first.
- Do not build live trading in the current phase set.
- Preserve the root signal logic.
- Keep signal generation separate from marketability checks and paper execution.

## Root Strategy Logic

The root strategy is intentionally small:

```text
In a 15-minute BTC Up/Down market,
when the market has 3 or 4 minutes remaining,
if BTC has moved beyond the configured percentage threshold from the market open,
enter in the direction of that move.
```

Direction:

```text
ret_pct > 0  -> UP
ret_pct < 0  -> DOWN
ret_pct == 0 -> no signal
```

The current strategy is about signal generation first, not about proving immediate live profitability.

## Confirmed Principles

- WebSocket-first data capture. Do not design this around low-frequency polling.
- Use real ask and ask-side depth for tradability checks.
- `trade_edge` must be based on executable ask-side pricing, not midpoint or last trade.
- Kelly is `1/5` and is only a risk cap or reference, not the primary sizing engine.
- Actual stake should default to a fixed small paper size.
- Do not add new trading rules unless Planning explicitly approves them.

## Locked Separation

### Signal

Signal decides only:

- remaining time
- move threshold
- direction from price move

Signal must not depend on:

- Polymarket ask
- orderbook depth
- spread
- Kelly
- account size
- `p_hat`
- `trade_edge`

### Marketability

Marketability decides only whether a valid signal is tradable at the current real ask.

It may reject a signal, but it must not create or modify one.

### Paper Execution

Paper execution simulates fills and records outcomes.

It must not place live orders.

## Current Undecided Items

These are not open for `执行区` to decide silently:

- persistent storage shape beyond the minimum needed for the assigned phase
- exact Polymarket market discovery path if docs and runtime disagree
- exact BTC reference source when more than one source is plausible
- `p_hat` definition before the phase that explicitly introduces it
- any new entry timing, multi-entry, stop-loss, take-profit, reverse, or averaging rules

If an assigned task depends on one of these, stop and route back to `规划区`.

## Phase 1 Boundaries

Phase 1 is about the root signal module and the smallest paper-trading skeleton.

Phase 1 uses Python standard library only.

Phase 1 must not:

- connect live WebSocket feeds
- simulate ask-depth fills
- define final `p_hat`
- place orders
- optimize parameters
- add new strategy factors

## Reporting Rule

Later phases must preserve two result views:

```text
signal-only:
    did the root signal direction resolve correctly?

tradable-signal:
    after real ask/depth checks, was the paper trade still valid and profitable?
```

This separation is mandatory so marketability filters do not hide whether the root signal itself works.
