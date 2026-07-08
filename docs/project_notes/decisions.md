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

## ADR-009 Phase 6 Discovery And Rotation Boundary

- Date: 2026-07-06
- Status: Accepted

Phase 6 resolves current/next BTC 15-minute markets and prepares runner inputs.

Required rules:

- Use public market metadata for discovery; no wallet, signing, credentials, or order APIs.
- Prefer current official Polymarket market-data docs when endpoint shape is unclear.
- Auto-select a market only when exactly one candidate passes configured validation.
- If discovery is ambiguous or token/outcome mapping is unclear, record a skip reason and do not run the session.
- Do not add automatic settlement, final `p_hat` modeling, or a long-running daemon in Phase 6.

Reason:

- Unattended paper trading needs market/session discovery before continuous operation.
- Discovery errors can corrupt results, so ambiguous candidates must be skipped instead of guessed.
- Daemon hardening and result settlement remain separate reliability phases.

## ADR-010 Local Workflow Docs As Default Rule Source

- Date: 2026-07-06
- Status: Accepted

After a deliberate `zone-memory` resync, local workflow docs become the default
rule source for this workspace.

Required rules:

- Read `AGENTS.md`, `zone_operating_model.md`, `key_facts.md`, and `issues.md` before reopening the `zone-memory` skill.
- Do not reread the `zone-memory` skill on normal task turns when the needed workflow rules already exist locally.
- Reopen `zone-memory` only for explicit workflow resyncs or when local docs appear stale, incomplete, or contradictory.
- When a resync changes durable behavior, write the change into local docs and record it in `issues.md`.

Reason:

- The skill is a bootstrap and calibration source, not the cheapest per-turn source.
- Using local docs first reduces token and read overhead while keeping workspace behavior stable.

## ADR-011 Phase 7 Session Config Runner Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 7 wires Phase 6 session config into one paper-runner session.

Required rules:

- Run one configured/discovered session only.
- Select `up_token_id` or `down_token_id` only after the root signal direction is known.
- Keep open price as an explicit input in Phase 7 unless automatic open-price capture is separately planned.
- Record selected side, selected token id, and session identifiers in runner JSONL.
- Do not add continuous daemon behavior, automatic settlement, final `p_hat` modeling, wallet/signing, or live orders.

Reason:

- Phase 6 produces UP/DOWN token mapping, while the current runner still accepts one explicit asset id.
- Continuous unattended operation is unsafe until the runner consumes session config without manual token-id selection.
- Open-price capture and daemon supervision are separate reliability problems.

## ADR-012 Phase 8 Open-Price Capture Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 8 captures the BTC reference open price for one session config.

Required rules:

- Use the existing BTC reference WebSocket source already used by the market-data layer.
- Define `open_price` as the first valid BTC reference trade at or after `market_start_time` within a configured max delay.
- Ignore pre-start trades for open-price selection.
- If no valid post-start trade arrives before the max delay, record a skip reason and do not guess.
- Do not add continuous supervisor behavior, automatic settlement, final `p_hat` modeling, wallet/signing, or live orders.

Reason:

- The root signal depends on market open reference price.
- Phase 7 removed manual token selection, but still requires manual open price.
- A deterministic open-price capture gate is needed before continuous unattended sessions.

## ADR-013 Phase 9 Bounded Continuous Supervisor Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 9 chains existing paper-trading steps across more than one session, but
only within explicit run bounds.

Required rules:

- Use existing discovery, open-price enrichment, session runner, and rotation behavior.
- Stop after a configured max session count, max runtime, or end time.
- Record each supervisor step and skip/failure reason to JSONL.
- Continue to the next planned session after a recoverable skip when bounds allow.
- Do not add an unbounded daemon, OS/process supervisor, restart policy, automatic settlement, final `p_hat` modeling, wallet/signing, or live orders.

Reason:

- The project now has enough one-session pieces to test unattended multi-session flow.
- A bounded supervisor proves orchestration without committing to daemon operations.
- Long-running durability and automatic settlement are separate reliability phases.

## ADR-014 Phase 10 Supervisor Result Batch Closing Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 10 closes multiple paper-runner outputs produced by the bounded supervisor
using explicit resolution input.

Required rules:

- Read supervisor JSONL and locate per-session runner output paths.
- Use an explicit resolution map keyed by market id or runner output path.
- Reuse the existing result closer logic where possible.
- Record missing runner output or missing resolution as skipped; do not guess.
- Preserve separate signal-only and tradable-signal summaries.
- Do not add automatic settlement crawling, final `p_hat` modeling, long-run database schema, daemon behavior, wallet/signing, or live orders.

Reason:

- Phase 9 can run more than one session, but the results are not yet scored as a batch.
- Explicit resolution input avoids inventing Polymarket settlement rules before a source is confirmed.
- Batch closing is the smallest step that turns bounded paper sessions into comparable PnL output.

## ADR-015 Phase 11 Conservative Automatic Resolution Ingestion Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 11 may derive paper-trading resolution maps from public Gamma closed-market
metadata, but only under strict ambiguity checks.

Source basis:

- Polymarket resolution docs state that after resolution winning tokens redeem for $1 and losing tokens are worth $0.
- Polymarket market-data docs describe Gamma market fetching and closed-market access.
- The Gamma market schema includes fields such as `closed`, `closedTime`, `outcomes`, `outcomePrices`, and `umaResolutionStatus`.

Required rules:

- Fetch or load closed market metadata by market id or slug.
- Accept automatic resolution only when `closed` is true, outcomes and outcomePrices parse cleanly, the market is binary, exactly one outcome is terminal `1`, the other is terminal `0`, and the winning outcome maps to UP or DOWN.
- Save raw source metadata beside the derived resolution map for audit.
- Record skip reasons for unresolved, missing, ambiguous, non-binary, 50/50-like, disputed, or unmapped payloads.
- Output an explicit resolution map compatible with Phase 10.
- Do not use wallet, onchain redemption, UMA proposal/dispute actions, live orders, `p_hat`, long-run database schema, or daemon behavior.

Reason:

- Phase 10 can close results but still needs manual winning-side input.
- A conservative metadata-only resolver moves toward unattended paper scoring without taking settlement risk.
- Skipping ambiguous payloads is safer than turning undocumented or disputed data into hidden strategy behavior.

## ADR-016 Phase 12 Stable Run Artifacts And Local Index Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 12 standardizes local run artifacts so long-running paper simulations can
be inspected and resumed by later phases without adding a database.

Required rules:

- Use local JSON and JSONL files only.
- Define one run directory layout for supervisor output, per-session runner output, resolution maps, raw resolution metadata, result summaries, run manifest, and session index.
- Preserve existing Phase 1-11 record formats; add index/manifest files around them instead of rewriting raw outputs.
- Track each session's market id, session times, runner output path, resolution status/path, result status/path, skip reason, and paper PnL when available.
- Record run-level config, start/end timestamps, final status, aggregate result path, and version/schema label in the manifest.
- Do not add a database, live trading, wallet/signing, `p_hat` modeling, daemon behavior, process supervision, or restart policy.

Reason:

- Phase 9-11 can run, resolve, and score sessions, but the files are not yet organized as one durable run.
- A manifest and index are the smallest useful persistence layer for unattended paper trading.
- Deferring daemon restart logic until after stable artifacts keeps recovery work grounded in actual files.

## ADR-017 Phase 13 Resumable Long-Run Paper Supervisor Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 13 adds process-local long-run reliability for paper trading, using Phase
12 run artifacts as the recovery source of truth.

Required rules:

- Stay paper-only and do not add wallet/signing, credentials, live orders, or `p_hat` modeling.
- Use the Phase 12 run directory, manifest, and session index to decide what has already happened.
- Resume without duplicating sessions already marked closed or skipped.
- Record heartbeat/status updates and recoverable errors in local JSON/JSONL files.
- Add bounded retry/backoff for recoverable discovery, open-price, runner, resolution, or result-closing failures.
- On graceful stop, leave manifest/index readable and mark status as stopped or interrupted.
- Do not add a database, launchd/systemd/crontab, background service installation, machine restart policy, or OS-level process supervision.

Reason:

- Phase 12 made runs inspectable, but the process still needs recovery behavior before it is useful unattended.
- Process-local resume and heartbeat are the smallest reliability step before any deployment-specific service wrapper.
- OS-level supervision should be decided only after the CLI long-run behavior is stable.

## ADR-018 Phase 14 Public-Data End-To-End Dry Run Boundary

- Date: 2026-07-07
- Status: Accepted

Phase 14 validates the full paper-trading loop against public data in a bounded
dry run.

Required rules:

- Run paper trading only; no live orders, wallet/signing, credentials, or order APIs.
- Use existing modules and artifact formats from Phase 1-13.
- Keep the dry run bounded by explicit max sessions, max runtime, or end time.
- Use explicit fixed paper stake and optional caller-supplied `p_hat`; do not estimate or train `p_hat`.
- Produce one inspectable run directory plus a concise dry-run report.
- If public API, WebSocket, market discovery, open-price, or resolution behavior does not match expectations, record the exact blocker and stop instead of silently changing strategy or settlement rules.
- Do not add a database, OS-level service wrapper, launchd/systemd/crontab config, machine restart policy, or new strategy behavior.

Reason:

- The project now has the full paper-run pipeline in isolated pieces.
- A real public-data dry run is the smallest honest test of whether those pieces work together outside fixtures.
- Any remaining stabilization work should come from observed dry-run evidence rather than speculative phases.

## ADR-019 Phase 15 Public BTC 15m Discovery Hardening Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 15 targets the live dry-run blocker from Phase 14: the first public
Gamma events source did not yield a valid current BTC 15m market under existing
validation rules.

Source basis:

- Polymarket market-data docs describe three market-fetching strategies: slug, tags, and events.
- The docs state that both events and markets endpoints are paginated.
- The docs recommend the events endpoint for broad active-market discovery, and document tag filtering plus `related_tags=true`.

Required rules:

- Keep discovery public-data only; no wallet/signing, credentials, order APIs, or live trading.
- Support documented public discovery paths: events endpoint, markets endpoint, slug/source URL, optional tag filtering, and pagination.
- Preserve existing validation rules for BTC/Bitcoin identity, 15-minute duration, active/open status, and clear UP/DOWN token mapping.
- Add diagnostics that record sources tried, source timestamps, page counts, market counts, candidate snapshots, and validation skip reasons.
- Integrate diagnostics into Phase 14 dry-run reporting.
- Do not change signal timing, strategy threshold, marketability/fill, open-price selection, resolution policy, result closer, artifact schema, long-run recovery, `p_hat`, database storage, or OS service behavior.

Reason:

- Phase 14 produced real evidence that the first broad events query is not sufficient for BTC 15m discovery.
- Hardening source coverage and diagnostics is smaller and safer than weakening candidate validation.
- The next dry run should fail only with precise discovery evidence, not a generic `no_valid_candidate`.

## ADR-020 Phase 16 BTC 15m Public Source Calibration Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 16 calibrates the public source path for current BTC 15m Up/Down markets.

Required rules:

- Use public data only; no wallet/signing, credentials, order APIs, or live trading.
- Try documented public source paths first: slug/source URL, tag filters, events endpoint, markets endpoint, and bounded pagination.
- Preserve strict candidate validation for BTC/Bitcoin identity, exact 15-minute duration, active/open status, and clear UP/DOWN token mapping.
- If a stable public tag, slug, or source URL is identified, make it configurable and record it in execution evidence.
- Prove the source through a bounded discovery smoke or Phase 14 dry-run invocation.
- If no valid source is found, record the exact sources, filters, and diagnostics attempted; do not fabricate a fixture success.
- Do not change signal timing, strategy threshold, marketability/fill, open-price selection, resolution policy, result closer, artifact schema, long-run recovery, `p_hat`, database storage, or OS service behavior.

Reason:

- Phase 15 proved the generic public discovery machinery works but still did not locate the BTC 15m source in live data.
- The next smallest useful step is source calibration, not deployment or strategy changes.
- A stable source path is required before unattended public-data operation can be trusted.

## ADR-021 Phase 17 Open-Price Window Alignment Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 17 aligns the public dry-run to a real BTC 15m market open so the existing open-price rule can be tested with live WebSocket data.

Required rules:

- Use the calibrated Phase 16 source path: `--search-query "bitcoin up down 15m"`.
- Prefer `--mode next` for live proof when starting after the current market has already opened.
- If the selected session starts in the future, wait only up to an explicit bounded budget before BTC reference capture.
- Preserve the existing open-price freshness rule; do not accept stale, pre-start, reconstructed, or backfilled prices as the market open.
- Record wait status, BTC capture status, and open-price status in dry-run artifacts.
- If the wait budget, network, or BTC feed prevents capture, return a precise operational blocker.
- Do not change strategy signal, marketability/fill, resolution policy, result closer, artifact schema, long-run recovery, `p_hat`, database storage, live trading, or OS service behavior.

Reason:

- Phase 16 proved public BTC 15m discovery but the dry-run still attempted BTC reference/open-price capture at the wrong time or under a too-short capture window.
- The root strategy depends on a real market-open BTC reference price. Planning should not let execution invent historical reconstruction or loosen freshness just to make the dry-run pass.

## ADR-022 Current Task File Replaces Growing Task-Card Archive

- Date: 2026-07-08
- Status: Accepted

Future planning handoffs use `docs/project_notes/current_task.md` as the only persistent current-task surface.

Required rules:

- Overwrite `current_task.md` when the next execution or acceptance task starts.
- Keep detailed execution cards, acceptance contracts, and acceptance tasks out of `issues.md`.
- Do not append new detailed task cards to `docs/project_notes/polymarket_paper_execution_tasks.md` by default; treat that file as a historical archive.
- Preserve history through concise `issues.md` entries: task ID, intent summary, changed files, evidence summary, blockers, and acceptance outcome.
- `执行区` reads `current_task.md` for the active assignment plus only the listed supporting files.
- `验收区` reads the current Acceptance Contract from `current_task.md`, the latest matching evidence block in `issues.md`, and the current diff.

Reason:

- The task-card archive has grown large enough that pointing zones at it encourages full-file reads and token waste.
- The detailed task card is usually useful only while the task is active.
- The durable record the project needs is what changed and what evidence proved it, not the full prompt used to assign the work.

## ADR-023 Phase 18 Entry-Window Dry-Run Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 18 proves that a calibrated public-data dry run can reach the root strategy's tail entry decision point for one real BTC 15m session.

Required rules:

- Reuse the Phase 16 calibrated source and Phase 17 wait-to-open/open-price capture path.
- After open price capture, wait only to a configured entry remaining-second timestamp within an explicit bounded wait budget.
- Preserve the root signal rule in `polybot.signal`; do not widen exact entry seconds or lower thresholds just to force a signal.
- Existing configurable signal parameters, `entry_remain_seconds` and `move_threshold_pct`, must be wired through orchestration and runner paths when they are already exposed by CLI/config.
- If actual wake time is late beyond a configured tolerance, skip with a precise entry-window blocker.
- A real `NO_SIGNAL` at the tail timestamp is an acceptable proof outcome when BTC movement does not exceed the configured threshold.
- If the signal is UP or DOWN, marketability may still skip because of missing book, missing `p_hat`, non-positive edge, or insufficient ask depth; those are valid paper outcomes when recorded explicitly.
- Do not change marketability/fill semantics, settlement/resolution policy, artifact schema, `p_hat` modeling, storage backend, live orders, wallet/signing, credentials, or OS service behavior.

Reason:

- Phase 17 proved fresh open-price capture but the runner can still execute too early to exercise the root tail signal.
- The clean fix is orchestration timing, not strategy modification.

## ADR-024 Phase 19 Bounded Multi-Session Public Run Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 19 proves that the public-data paper runner can process more than one real BTC 15m session in a single bounded process.

Required rules:

- Reuse Phase 16 source calibration, Phase 17 wait-to-open/open-price capture, and Phase 18 wait-to-entry/signal behavior.
- Honor `max_sessions > 1` for unique chronological sessions.
- Track processed market ids or session keys to prevent duplicate processing inside one run.
- Keep all waits bounded by explicit budgets and stop cleanly with a precise reason when a budget, runtime, or data source prevents progress.
- Write per-session evidence for discovery, open price, entry wait, runner output, and skip reasons.
- Settlement/resolution may remain pending in this phase.
- Do not add live trading, wallet/signing, credentials, final `p_hat` modeling, database storage, launchd/systemd/crontab, service install, or OS restart policy.
- Do not change the root strategy, marketability/fill semantics, open-price freshness, or settlement policy.

Reason:

- Phase 18 proved one real session can reach the tail decision point.
- Unattended operation next needs repeated session processing before deployment or OS supervision decisions are useful.

## ADR-025 Phase 20 Public Resolution And Closing Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 20 wires conservative public resolution and result closing into completed public paper-run sessions.

Required rules:

- Reuse existing Phase 11 conservative resolution ingestion and Phase 10 batch closing behavior.
- Attempt resolution only for sessions with runner outputs.
- Accept automatic resolution only when public market metadata is closed and unambiguous under existing rules.
- Save raw resolution metadata beside derived resolution output when fetched.
- If a session cannot be resolved, keep it pending/skipped with the exact skip reason.
- Do not infer winners from BTC direction, market title, orderbook/trade prices, or partially resolved metadata.
- Do not change paper PnL formulas, marketability/fill semantics, root signal behavior, open-price freshness, discovery validation, artifact schema, storage backend, live trading, wallet/signing, credentials, `p_hat`, or OS service behavior.

Reason:

- Phase 19 proved multi-session runtime, but result status remained `missing_resolution`.
- The project already has conservative resolution and batch-closing modules; the next smallest useful step is wiring them into public-run artifacts, not inventing a new settlement system.

## ADR-026 Phase 21 Public Closed-Loop Soak Boundary

- Date: 2026-07-08
- Status: Accepted

Phase 21 proves that the already wired public paper loop remains inspectable and stable across a longer bounded run plus repeated result-closing attempts.

Required rules:

- Reuse the Phase 16-20 public-data path; do not introduce a second orchestrator.
- Target multiple chronological BTC 15m sessions in one bounded public command.
- Attempt conservative public resolution/result closing for completed sessions.
- Re-run close-existing-run from the same source artifacts to check idempotence and artifact stability.
- Treat `not_closed`, unresolved, ambiguous, disputed, missing prices, source/network failures, and timing budget misses as explicit pending/skipped/blocker states.
- Do not infer winners from BTC direction, title text, orderbook/trade prices, or partially resolved metadata.
- Do not add live trading, wallet/signing, credentials, final `p_hat` modeling, database storage, launchd/systemd/crontab, service install, OS restart policy, or new strategy behavior.

Reason:

- Phase 20 proved closing can work on completed public sessions, but unattended paper trading needs evidence that the loop stays readable after a longer run and repeated close attempts.
- This is the smallest stability step before planning canonical run configuration or OS-level supervision.

## ADR-027 Fixed Remaining Paper-Bot Development Plan

- Date: 2026-07-08
- Status: Accepted

The remaining planned development track is capped at Phase 21 through Phase 23.

Fixed remaining phases:

- Phase 21: public closed-loop soak and repeated close/idempotence proof.
- Phase 22: operator run commands, status, and runbook.
- Phase 23: local process supervision.

Rules:

- Do not add new planned phases for ordinary observation, longer soak duration, or parameter watching.
- Do not build a config wrapper merely to shorten a long terminal command; a copy-paste command plus clear run steps is acceptable.
- Use actual paper operation to accumulate live evidence after the planned track is complete.
- Route failures discovered during operation as bug-driven fixes, not new roadmap phases.
- Add new phases only for explicit new product decisions, such as final `p_hat` modeling, live trading, parameter research, alerts/notifications, UI, or database storage.
- Preserve the root strategy and current paper-only boundary unless the user explicitly changes product scope.

Reason:

- The core paper-trading path is already built through public discovery, open-price capture, entry timing, marketability, paper execution, conservative resolution, and artifacts.
- The remaining work should make the system easier to start, inspect, and keep running, not keep re-proving the same behavior under different observation lengths.
