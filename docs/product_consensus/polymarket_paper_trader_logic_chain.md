# Polymarket Paper Trader Logic Chain

## Purpose

This document explains the paper BTC 15m trading logic in human terms.

It is not an operator runbook and it is not a live-trading design. For run
commands, status checks, logs, and local supervision, use:

- `docs/operator_runbook.md`
- `docs/local_process_supervision.md`

## Current Strategy In One Paragraph

The bot watches a 15-minute BTC Up/Down Polymarket session. It records the BTC
price at the market open, waits until the market has either 4 minutes or 3
minutes left, then compares the current BTC price with the recorded open price.
If BTC has moved at least `0.05%`, the bot creates a directional signal in the
same direction as the move. After that, it checks whether the matching
Polymarket UP or DOWN token is actually tradable at the ask side with the fixed
paper stake. If the executable ask price is worse than the caller-supplied
`p_hat`, the bot skips the paper trade instead of pretending the signal was
tradable.

## Strategy Parameters

These are the current parameters that directly affect the strategy decision or
paper trade decision:

| Parameter | Current value | Meaning |
| --- | ---: | --- |
| Market type | BTC Up/Down | Only BTC binary direction markets are in scope. |
| Market duration | 15 minutes | The root strategy is calibrated around 15-minute sessions. |
| Entry remaining time | `240` or `180` seconds | Evaluate the signal when the market has 4 or 3 minutes left. |
| Entry tolerance | `3` seconds | Small scheduling tolerance around the entry timestamp. |
| Move threshold | `0.05%` | BTC must move at least this far from market open to create a signal. |
| Paper stake | `9` USDC-equivalent | Fixed simulated spend per accepted paper trade. |
| `p_hat` | `0.55` | Caller-supplied win-probability input; not a model. |
| Open-price capture window | `8` seconds | Time budget to capture BTC trades around market open. |
| Max open-price delay | `5` seconds | The open price must be fresh enough after market start. |
| Runner capture window | `8` seconds | Time budget to capture the entry-time BTC/orderbook data. |
| Heartbeat interval | `30` seconds | Local runtime status heartbeat, not price polling. |

## Step By Step Logic

### 1. Find The Next BTC 15m Market

The run searches public Polymarket metadata for BTC 15-minute Up/Down markets.
The current search phrase is:

```text
bitcoin up down 15m
```

The bot only proceeds when it can identify one valid next session and map the
UP and DOWN token ids unambiguously. If the public metadata is missing,
ambiguous, closed, archived, or not accepting orders, the bot records a skip
reason and does not guess.

### 2. Record The BTC Open Price

At the selected market's start time, the bot captures BTC trade data from the
Binance WebSocket.

The open price is the first valid BTC trade price after the market start. If the
bot cannot capture a valid fresh post-start price, it skips that session. This
matters because every later signal compares against this open price.

### 3. Wait For The Entry Moment

The strategy does not evaluate continuously. It waits for one of the configured
entry moments:

```text
4 minutes remaining
3 minutes remaining
```

Those are represented as:

```text
240 seconds
180 seconds
```

If the bot cannot reach one of those moments within the wait budget, or wakes up
outside the allowed tolerance, the session is skipped.

### 4. Measure BTC Movement From Open

At the entry moment, the bot compares the current BTC price with the recorded
market-open BTC price:

```text
move_pct = (current_btc_price - open_btc_price) / open_btc_price * 100
```

Human reading:

- `move_pct` is positive when BTC is above the market-open price.
- `move_pct` is negative when BTC is below the market-open price.
- The absolute size of `move_pct` must be at least `0.05%`.

### 5. Create The Root Signal

The signal rule is deliberately small:

- If BTC is up by at least `0.05%`, signal `UP`.
- If BTC is down by at least `0.05%`, signal `DOWN`.
- If BTC moved less than `0.05%` in either direction, signal `NO_SIGNAL`.

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

It simulates spending the fixed paper stake (`9`) against the cheapest available
asks first. This gives the executable average ask price for the whole simulated
fill.

The paper trade is rejected when:

- no ask depth is available
- ask depth cannot fill the fixed paper stake
- the selected token id is missing
- the Polymarket book cannot be captured

This keeps the result honest: a correct signal still counts as untradable if
the public order book cannot support the simulated buy.

### 8. Apply The `p_hat` Edge Check

The current `p_hat` is supplied by the caller as `0.55`. It is not trained,
inferred, smoothed, or backfilled by the bot.

The edge check is:

```text
trade_edge = p_hat - executable_avg_ask
```

The paper trade is accepted only when:

- `p_hat` is between `0` and `1`
- `trade_edge` is greater than `0`
- the fixed paper stake can be filled from ask depth

Example:

- If `p_hat = 0.55` and executable average ask is `0.52`, edge is positive, so
  the paper trade can be accepted.
- If `p_hat = 0.55` and executable average ask is `0.58`, edge is negative, so
  the bot skips the paper trade.

Kelly may be recorded as a reference value, but it does not size the current
paper stake.

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

## What The Strategy Does Not Do

The current logic intentionally does not include:

- live orders, wallet signing, or real funds
- a trained `p_hat` model
- stop-loss, take-profit, averaging, reversal, or multi-entry rules
- midpoint, last-trade, or spread-based edge checks
- continuous price polling as the signal engine
- database storage or cloud deployment assumptions

## Required Result Split

Reviews must keep these two views separate:

- Signal-only view: whether the root BTC direction signal was right.
- Tradable-signal view: whether that signal could pass ask-depth and edge
  checks as a paper trade.

This split is important because a good or bad directional signal should not be
hidden by marketability failures, and an untradable signal should not be counted
as if it were actually executable.
