# Decisions

## ADR-001 Zone-Based Collaboration

- Date: 2026-07-05
- Status: Accepted

Use four collaboration zones for this workspace:

- `规划区`
- `执行区`
- `验收区`
- `维护区`

Reason:

- Keep planning, implementation, review, and maintenance separated.
- Reduce prompt repetition by keeping stable rules in tracked docs.
- Make execution evidence and acceptance review cheaper in future turns.

## ADR-002 Polymarket Paper-First Delivery And Review Split

- Date: 2026-07-06
- Status: Accepted

Use paper trading as the only active delivery track for the Polymarket BTC
strategy until planning explicitly opens a live-trading phase.

Required rules:

- Keep root signal logic separate from marketability, sizing, and paper execution.
- Give `执行区` a bounded task plus a required execution evidence report shape.
- Give `验收区` the Acceptance Contract plus execution evidence plus current diff, not the full execution task by default.
- Use phase gates so later tasks do not silently absorb unresolved earlier decisions.

Reason:

- Prevent execution from silently inventing missing strategy rules.
- Prevent acceptance from repeating execution work and wasting tokens.
- Keep strategy validation and tradability validation separable.

## ADR-003 Phase 1 Runtime

- Date: 2026-07-06
- Status: Accepted

Use Python standard library for Phase 1 only.

Required rules:

- Create a minimal `polybot/` package only if needed for the signal module.
- Do not add third-party dependencies in Phase 1.
- Provide a runnable signal self-check with `python -m polybot.signal` or an equally small standard-library test path.
- Keep Phase 1 as pure local logic: no network, no environment variables, no file reads for strategy inputs, no Polymarket API calls.

Reason:

- Phase 1 needs only pure signal logic and local self-checks.
- Python standard library is the smallest useful runtime choice for this greenfield skeleton.
- Deferring dependency choices keeps WebSocket/API decisions in later phases.

## ADR-004 Phase 2 WebSocket Capture Runtime

- Date: 2026-07-06
- Status: Accepted

Continue using Python for Phase 2 market-data capture.

Required rules:

- WebSocket is the primary capture path.
- REST may be used only for startup snapshots, reconnect recovery, or API verification.
- If Python standard library is not enough for WebSocket, Phase 2 may add exactly one WebSocket client dependency after checking the current environment.
- Do not add Polymarket order placement, wallet signing, or trading SDK dependencies in Phase 2.

Reason:

- Phase 2 validates live data capture, not trading.
- A narrow WebSocket dependency is justified because Python standard library does not provide a practical WebSocket client.
- Keeping trading dependencies out prevents accidental live-order paths.

## ADR-005 Unattended Paper Trading Path

- Date: 2026-07-06
- Status: Accepted

Build toward unattended continuous paper trading in staged gates:

1. Single-market paper runner.
2. Settlement and result closing.
3. Market discovery and 15-minute session rotation.
4. Operational hardening for continuous runs.

Required rules:

- Do not skip directly from paper-fill primitives to unattended market rotation.
- Do not add live order placement, wallet signing, or credentials.
- Do not let market discovery invent strategy rules.
- Keep `p_hat` caller-supplied until a planning phase explicitly defines a model.

Reason:

- The current modules are working primitives, not yet a continuous simulator.
- A single-market runner proves the data flow before adding discovery and scheduling.
- Unattended operation needs recovery, skip reasons, and durable records before it is useful.

## ADR-007 Phase 3 p_hat Boundary

- Date: 2026-07-06
- Status: Accepted

Phase 3 may compute `trade_edge` only from a caller-supplied `p_hat`.

Required rules:

- Do not estimate, train, smooth, bucket, or persist a `p_hat` model in Phase 3.
- Do not infer `p_hat` from recent market outcomes.
- Use test/demo `p_hat` values only as explicit inputs.
- Keep final `p_hat` design in Planning until a later phase explicitly introduces it.

Reason:

- Phase 3 is about ask-depth tradability and paper fill mechanics.
- Estimating true win probability is a separate strategy research task.
- This prevents a temporary probability guess from becoming a hidden trading rule.

## ADR-005 Minimum Required Read Set

- Date: 2026-07-06
- Status: Accepted

Execution and acceptance task cards should name only the minimum required read
set for the current phase, then route other docs behind explicit "read if needed"
conditions.

Required rules:

- Keep `先读` to the smallest set that is truly required to execute safely.
- Do not require rereading unchanged product, architecture, or implementation docs when the current task does not depend on them.
- Use explicit on-demand routing such as "if you need to confirm strategy boundaries, read X".
- Keep stable workflow rules in `AGENTS.md` and `zone_operating_model.md`, not repeated across every task card.

Reason:

- Re-reading unchanged docs across zones wastes tokens without improving safety.
- A smaller mandatory read set preserves momentum while still allowing targeted verification when needed.

## ADR-006 Two-Hop Execution And Acceptance Flow

- Date: 2026-07-06
- Status: Accepted

Use `docs/project_notes/issues.md` as the default evidence handoff between `执行区`
and `验收区`.

Required rules:

- `执行区` writes its evidence report into the latest matching task block in `issues.md`.
- `验收区` must not require the user to manually relay execution evidence by default.
- `验收区` reads `Current Summary`, the current task ID's latest log block in `issues.md`, and the current diff.
- No zone should read all of `issues.md` by default.

Reason:

- This removes one manual copy step from the planning -> execution -> acceptance loop.
- Reading only the current task block keeps `issues.md` usable as it grows.

## ADR-008 Phase 5 Settlement Boundary

- Date: 2026-07-06
- Status: Accepted

Phase 5 closes recorded paper-runner output only.

Required rules:

- Winning side must be explicit input or come from a verified resolution record.
- Do not discover current/next markets in Phase 5.
- Do not rotate 15-minute sessions in Phase 5.
- Do not estimate or train `p_hat`.
- Do not place live orders or add wallet/signing/credential paths.

Reason:

- Phase 4 produces JSONL simulation records but does not score completed markets.
- Result closing is the smallest next step toward unattended paper trading.
- Market discovery and rotation are separate reliability problems and should not be mixed into settlement.
