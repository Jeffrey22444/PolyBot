# Architecture

## Goal

Keep the code structure aligned with the strategy split already agreed in planning.

The first architecture rule is separation, not sophistication.

## Required Module Boundaries

### 1. Signal

Inputs:

- market timing
- market open reference price
- current reference price
- configured entry remaining seconds
- configured move threshold

Outputs:

- `UP`
- `DOWN`
- `NO_SIGNAL`

Must not import or depend on:

- Polymarket orderbook data
- best ask / spread
- depth walking
- Kelly logic
- account balance
- `p_hat`
- execution records

### 2. Market Data

Purpose:

- hold raw external state needed by later phases

Examples:

- market metadata
- orderbook snapshots
- BTC reference price snapshots
- timestamps and data age

This layer does not generate strategy signals.

### 3. Marketability

Purpose:

- decide whether a valid signal is tradable at the current real ask

Examples:

- best ask
- ask depth
- executable average ask
- spread
- data freshness
- optional `p_hat`

This layer must consume a signal; it must not create one.

### 4. Paper Execution

Purpose:

- simulate a trade after signal and marketability checks pass

Examples:

- fixed paper stake
- Kelly cap/reference
- simulated fill price
- recorded skip reason
- PnL record

This layer must never place a live order in the current project phase set.

### 5. Reporting

Purpose:

- produce separate signal-only and tradable-signal outputs

This layer must not backflow new rules into Signal.

## Dependency Direction

Required direction:

```text
Signal -> pure strategy decision
Market Data -> raw external state
Marketability -> consumes Signal + Market Data
Paper Execution -> consumes Signal + Marketability
Reporting -> consumes records from earlier layers
```

Forbidden shortcuts:

- Signal importing Marketability
- Signal importing Paper Execution
- Paper Execution redefining signal rules
- Reporting mutating strategy decisions

## Architecture Stop Rule

If an implementation task requires a new shared abstraction, new service layer,
or broad repo structure before a thin slice works, stop and route it back to
planning unless an existing local pattern clearly justifies it.
