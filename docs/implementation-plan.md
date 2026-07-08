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

## Phase 7: Session Config Runner Wiring

Rules:

- Run one discovered/configured session only.
- Consume the Phase 6 session config shape.
- Select the UP or DOWN token only after the root signal direction is known.
- Keep open price explicit unless the task separately defines automatic open-price capture.
- Do not add a long-running daemon yet.

Deliver:

- runner path that accepts a session config JSON
- signal-direction to token-id selection
- JSONL records that include session id, selected side, and selected token id
- skip reasons for no signal, missing open price, missing token mapping, or missing book

Verify:

- UP signal selects UP token id
- DOWN signal selects DOWN token id
- NO_SIGNAL does not capture or fill either side
- missing open price or mapping produces a skip/runtime note
- existing Phase 1-6 self-checks still pass

Gate:

- a discovered session config can drive one paper-runner session without manual token-id selection

## Phase 8: Automatic Open-Price Capture

Rules:

- Capture only the session open reference price.
- Use the existing BTC reference WebSocket source from the market-data layer.
- Define open price as the first valid BTC reference trade at or after the market start time within a configured max delay.
- Skip the session when a valid open price is not captured.
- Do not add continuous supervisor behavior yet.

Deliver:

- open-price capture/enrichment path for one session config
- captured open price, timestamp, source, and max-delay metadata
- runner compatibility so explicit `--open-price` is optional when an enriched session config includes `open_price`
- skip reasons for stale, missing, or invalid open-price data

Verify:

- first valid post-start BTC record becomes open price
- pre-start-only records do not become open price
- stale or missing data produces a skip reason
- enriched session config can drive the Phase 7 runner without manual open-price input
- existing Phase 1-7 self-checks still pass

Gate:

- a discovered session config can be enriched with open price and run once without manual open-price input

## Phase 9: Bounded Continuous Supervisor

Rules:

- Run paper trading only.
- Chain existing discovery, open-price enrichment, session runner, and rotation.
- Stop after a configured session count, end time, or max runtime.
- Write JSONL runtime records for each supervisor step.
- Do not add an unbounded daemon, process supervisor, or restart policy yet.
- Do not add automatic settlement or final `p_hat` modeling.

Deliver:

- bounded supervisor entry point
- config inputs for max sessions, max runtime/end time, lookahead, stake, caller-supplied `p_hat`, output directory or JSONL path
- per-session outputs that include discovery, open-price capture/enrichment, runner output path, skipped reason, and status
- safe handling when discovery/open-price/runner step skips or fails

Verify:

- supervisor can run two sample sessions from local fixtures
- skip in one session does not prevent the next planned session from being evaluated when bounds allow
- supervisor stops at max session count or max runtime/end time
- no live order path exists
- existing Phase 1-8 self-checks still pass

Gate:

- a bounded run can process more than one 15-minute session without manual market id, token id, or open price input

## Phase 10: Supervisor Result Batch Closing

Rules:

- Close paper-runner outputs produced by the bounded supervisor.
- Winning side must come from an explicit resolution map keyed by market id or runner output path.
- Reuse the existing result closer logic where possible.
- Preserve separate signal-only and tradable-signal summaries.
- Do not guess settlement, crawl automatic resolution, estimate `p_hat`, add a database, or add daemon behavior.

Deliver:

- batch closer entry point for supervisor JSONL output
- explicit resolution-map input
- per-session close summaries
- aggregate paper PnL summary
- skipped-session records for missing runner output or missing resolution

Verify:

- a sample supervisor JSONL with two runner outputs can be closed
- one missing resolution is recorded as skipped, not guessed
- per-session and aggregate PnL are written
- existing Phase 1-9 self-checks still pass

Gate:

- a bounded multi-session paper run can be scored after explicit resolutions are supplied

## Phase 11: Conservative Automatic Resolution Ingestion

Rules:

- Use public Gamma closed-market metadata as the first automatic resolution source.
- Treat `outcomes` and `outcomePrices` as accepted only when the market is closed and the values are parseable and unambiguous.
- Derive a winning side only when exactly one binary outcome has terminal value `1` and the other has `0`, and the winning outcome maps to `UP` or `DOWN`.
- Record skip reasons for missing, ambiguous, non-binary, 50/50, disputed, unresolved, or unmapped data.
- Produce an explicit resolution map compatible with Phase 10.
- Do not use wallet, onchain redemption, UMA voting actions, live orders, `p_hat`, a database, or daemon behavior.

Deliver:

- conservative resolution ingestion module/entry point
- input by market id or slug, plus optional sample fixture path
- resolution-map JSON output consumable by Phase 10
- raw source metadata saved beside the derived resolution output
- skip records for unresolved or ambiguous markets

Verify:

- local fixtures cover UP win, DOWN win, missing/ambiguous prices, non-binary outcomes, and 50/50-like prices
- generated resolution map can drive Phase 10 batch closing
- existing Phase 1-10 self-checks still pass

Gate:

- a completed closed market can be converted into explicit resolution-map input without manual winning-side entry when the public payload is unambiguous

## Phase 12: Stable Run Artifacts And Local Index

Rules:

- Keep storage as local files only: JSON and JSONL.
- Define one run directory layout that links supervisor output, session runner outputs, resolution maps, raw resolution metadata, batch results, and aggregate summaries.
- Write a run manifest and session index that can be read after the process exits.
- Preserve existing record formats; add indexing around them instead of rewriting prior phases.
- Do not add a database, daemon behavior, restart policy, live orders, wallet/signing, or `p_hat` modeling.

Deliver:

- run-artifact module/entry point or helper used by existing CLIs
- deterministic run directory layout
- run manifest with config, timestamps, output paths, and final status
- session index with market id, session times, runner path, resolution path/status, result status, skip reason, and PnL when available
- small summary command or self-check that builds an indexed sample run from local fixtures

Verify:

- a sample two-session run produces a readable manifest and session index
- skipped sessions remain visible with skip reasons
- closed sessions link to resolution and result summaries
- existing Phase 1-11 self-checks still pass

Gate:

- a human or later daemon-hardening phase can inspect one run directory and understand what happened without reading every raw JSONL file manually

## Phase 13: Resumable Long-Run Paper Supervisor

Rules:

- Stay paper-only.
- Use Phase 12 run artifacts as the recovery source of truth.
- Add process-local long-run behavior: resume, heartbeat/status updates, recoverable-error records, bounded retry/backoff, and graceful stop.
- Avoid duplicate processing of sessions already marked closed or skipped in the session index.
- Keep OS-level supervision out of scope: no launchd, systemd, crontab, background service install, or machine restart policy.
- Do not add a database, live orders, wallet/signing, or `p_hat` modeling.

Deliver:

- long-run supervisor entry point or a minimal extension around the existing supervisor
- run-dir input and resume behavior
- status/heartbeat records in the run manifest or a small status JSONL
- recoverable error and retry records with configured retry/backoff limits
- graceful stop behavior that leaves the run manifest readable and marked stopped/interrupted
- deterministic self-check using local fixtures and simulated interruption/resume

Verify:

- a sample run can resume from an existing run directory without duplicating completed sessions
- recoverable errors are recorded and retried within bounds
- graceful stop updates manifest/status without corrupting existing artifacts
- existing Phase 1-12 self-checks still pass

Gate:

- a single CLI process can be left running for repeated paper sessions and can be inspected or resumed after interruption

## Phase 14: Public-Data End-To-End Dry Run

Rules:

- Run paper trading only against public data.
- Use existing modules: discovery, open-price capture, runner, marketability/paper fill, resolution ingestion, batch closer, run artifacts, and long-run status.
- Keep the run bounded by explicit max sessions, max runtime, or end time.
- Use explicit paper stake and caller-supplied `p_hat` only; do not estimate `p_hat`.
- Produce a single inspectable run directory and a concise dry-run report.
- Do not add live orders, wallet/signing, database storage, OS service installation, or new strategy rules.

Deliver:

- dry-run command, script, or documented invocation using existing entry points
- sample public-data run artifact directory
- dry-run report with commands, config, session outcomes, skips, PnL when closed, and unresolved items
- issue list for any API/data mismatch discovered during the dry run

Verify:

- dry run creates Phase 12-compatible artifacts and Phase 13 status/heartbeat
- at least one real public session is discovered or a clear public-data skip reason is recorded
- no live-order path exists
- existing Phase 1-13 self-checks still pass

Gate:

- the project can demonstrate a bounded end-to-end paper run on public data, or produce a precise blocker list grounded in live dry-run evidence

## Phase 15: Public BTC 15m Discovery Hardening

Rules:

- Fix only public market/session discovery for BTC 15m paper trading.
- Use documented public Gamma market-data strategies: events endpoint, markets endpoint, slug, tags, and pagination.
- Keep existing candidate validation strict: BTC/Bitcoin identity, 15-minute duration, active/open status, and clear UP/DOWN token mapping.
- Add richer diagnostics for sources tried, page counts, market counts, candidate snapshots, and validation skip reasons.
- Do not change strategy signal, marketability/fill, open-price, resolution, result closing, run artifacts, or long-run behavior.
- Do not add live orders, wallet/signing, database storage, `p_hat` modeling, or OS service behavior.

Deliver:

- public discovery hardening in or around `polybot.market_discovery`
- support for paginated events/markets sources and optional tag/slug/source-url filters
- diagnostics output consumable by Phase 14 dry-run reports
- local fixture self-checks for events payloads, markets payloads, pagination, and ambiguous/no-candidate cases

Verify:

- fixtures can discover a valid BTC 15m UP/DOWN market from both nested events and flat markets payload shapes
- no-candidate public payloads produce useful diagnostics without changing validation rules
- Phase 14 dry run can consume the hardened discovery result or produce a more precise live blocker
- existing Phase 1-14 self-checks still pass

Gate:

- the next public-data dry run can either find a valid BTC 15m session from documented public sources or explain exactly why none was selected

## Phase 16: BTC 15m Public Source Calibration And Dry-Run Proof

Rules:

- Identify the correct public source path for current BTC 15m Up/Down markets: known slug, tag, source URL, or documented filter combination.
- Keep discovery validation strict; do not loosen BTC/Bitcoin identity, exact 15-minute duration, active/open status, or clear UP/DOWN token mapping.
- Prove the source by rerunning bounded public dry run or discovery smoke with recorded evidence.
- If no public source can be found, record a precise blocker and the sources attempted.
- Do not change strategy signal, marketability/fill, open-price, resolution, result closing, artifacts, long-run behavior, `p_hat`, database storage, live trading, or OS service behavior.

Deliver:

- source calibration notes in execution evidence
- optional minimal config/default source support if a stable public tag/slug/source URL is found
- dry-run/discovery smoke output using the calibrated source
- diagnostics showing whether a valid BTC 15m session was selected

Verify:

- calibrated source either produces a valid BTC 15m session or records a precise source blocker
- Phase 14 dry-run path can consume the calibrated source without code edits
- existing Phase 1-15 self-checks still pass

Gate:

- the project has a known public source path for BTC 15m discovery, or a concrete source blocker that Planning can resolve without guessing

## Phase 17: Open-Price Window Alignment For Public Dry Run

Rules:

- Use the calibrated public source path from Phase 16: `--search-query "bitcoin up down 15m"`.
- Target the next BTC 15m session when starting mid-market; do not infer or backfill the opening BTC price for an already-running session.
- Wait only within an explicit bounded budget before capturing BTC reference records by WebSocket.
- Preserve the existing open-price freshness rule; do not accept pre-start or stale BTC records.
- Record exact wait, capture, and open-price outcomes in dry-run artifacts.
- Do not change strategy signal, marketability/fill, result closing, resolution, artifacts schema, `p_hat`, database storage, live trading, or OS service behavior.

Deliver:

- minimal dry-run support for bounded wait-to-open before BTC reference capture
- explicit dry-run evidence for `wait_to_open`, `btc_reference_capture`, and `open_price`
- a real calibrated-source dry-run attempt using `--mode next`
- precise blocker if the run cannot reach open-price capture because of wait budget, network, or missing BTC records

Verify:

- existing self-checks for touched modules still pass
- compile check passes
- public dry run no longer fails merely because it selected an already-running market and tried to capture open price too late
- no historical backfill, fake fixture success, validation loosening, order path, credential path, DB, or OS service was added

Gate:

- public dry-run can either capture a fresh open price for a next session or returns a precise operational blocker that does not require execution to invent policy

## Phase 18: Entry-Window Full-Session Paper Dry-Run Proof

Rules:

- Use the calibrated public source path from Phase 16 and the wait-to-open behavior from Phase 17.
- After open price is captured, wait only within an explicit bounded budget until the next configured entry remaining-second timestamp.
- Preserve `polybot.signal` root logic; do not widen the 180/240 second rule to make the proof easier.
- Wire existing configurable signal parameters through orchestration: `entry_remain_seconds` and `move_threshold_pct`.
- If the process reaches the entry timestamp late beyond the configured tolerance, skip with a precise reason instead of faking a signal.
- A `NO_SIGNAL` at the real tail timestamp is a valid outcome when the move threshold is not met.
- Do not change marketability/fill, result closing, resolution, artifact schema, `p_hat`, database storage, live trading, or OS service behavior.

Deliver:

- minimal dry-run support for bounded wait-to-entry after open price capture
- evidence of selected entry timestamp, wait budget, wake timing, and tolerance result
- public dry-run proof whose runner output contains a real tail-window `signal_record`
- if signal is UP/DOWN, evidence of marketability/paper trade output or a precise market data skip reason

Verify:

- existing self-checks for touched modules still pass
- compile check passes
- public dry run reaches entry-window signal generation or records a precise operational blocker
- no signal-rule widening, historical backfill, fake fixture success, order path, credential path, DB, or OS service was added

Gate:

- public dry-run can prove one real session reaches the strategy's tail decision point, or returns a precise operational blocker that Planning can route without guessing

## Phase 19: Bounded Multi-Session Public Run Proof

Rules:

- Reuse the calibrated source, wait-to-open, open-price capture, wait-to-entry, and runner behavior from Phases 16-18.
- Honor `max_sessions > 1` in the public dry-run path for unique chronological BTC 15m sessions.
- Keep the process bounded by explicit session count, max runtime, and wait budgets.
- Avoid duplicate processing of the same market id/session key in one run.
- Record per-session discovery, wait, open price, entry, runner, and skip evidence.
- Settlement may remain pending; do not block this phase on post-close resolution.
- Do not add a database, daemon/service install, OS restart policy, live trading, wallet/signing, credentials, or final `p_hat` modeling.

Deliver:

- minimal multi-session orchestration in the existing public dry-run path
- run artifacts that include at least two attempted unique sessions, unless a precise operational blocker stops earlier
- per-session runner outputs for sessions that reach the runner
- concise dry-run report showing stop reason and processed/attempted session count

Verify:

- existing self-checks for touched modules still pass
- compile check passes
- bounded public run can process two chronological BTC 15m sessions or records a precise blocker
- no order path, credential path, DB, OS service, or strategy-rule change was added

Gate:

- one process can run repeated paper sessions from public data within explicit bounds, or returns a precise blocker that does not require execution to invent policy

## Phase 20: Public Resolution And Result-Closing Wiring

Rules:

- Reuse existing conservative `resolution_ingestion` and `supervisor_results`/`run_artifacts` behavior.
- Attempt automatic resolution only for sessions that have runner outputs and whose market metadata is closed and unambiguous under the existing Phase 11 rules.
- If a market is not closed, unresolved, ambiguous, disputed, missing outcome prices, or unmapped, keep it pending/skipped with the exact reason.
- Do not guess winners from price movement, orderbook prices, title text, or non-terminal metadata.
- Do not change settlement policy, PnL formulas, marketability/fill semantics, strategy signal, artifact schema, `p_hat`, database storage, live trading, wallet/signing, credentials, or OS service behavior.

Deliver:

- minimal public dry-run wiring that can attempt resolution/closing after runner output exists
- per-session resolution attempt evidence and raw metadata path when fetched
- updated summary/session index showing closed sessions with PnL when conservative resolution succeeds, or explicit pending/skipped reasons when it does not
- bounded public proof using real session outputs

Verify:

- existing self-checks for touched modules still pass
- compile check passes
- at least one public completed session is attempted for resolution/closing, or a precise blocker explains why none can be attempted
- no guessed settlement, order path, credential path, DB, OS service, or strategy-rule change was added

Gate:

- public paper runs can produce conservative result-closing output when resolution data is available, or preserve inspectable pending state when it is not

## Phase 21: Public Closed-Loop Soak And Resume Proof

Rules:

- Reuse the Phase 16-20 public path: calibrated BTC 15m discovery, wait-to-open, fresh WebSocket open price, wait-to-entry, paper runner, conservative public resolution, batch closing, run artifacts, and process-local status.
- Run a longer bounded public proof than the earlier two-session run, targeting multiple chronological BTC 15m sessions in one command.
- After the public run, repeat close-existing-run/result-closing from the same source artifacts and verify it does not duplicate sessions, corrupt artifacts, or change closed/pending semantics unexpectedly.
- Keep waits, session count, and runtime explicitly bounded.
- If public data, network, timing, or resolution state prevents completion, record the precise blocker and stop.
- Do not add live trading, wallet/signing, credentials, final `p_hat` modeling, database storage, launchd/systemd/crontab, service install, OS restart policy, or new strategy behavior.

Deliver:

- one real public closed-loop soak attempt using `--search-query "bitcoin up down 15m"` and `--attempt-public-resolution`
- artifacts proving chronological unique sessions, runner outputs or precise skips, resolution attempts, result summaries, manifest/status/heartbeat readability
- repeated close-existing-run proof from the same source run, with consistent session keys and result statuses
- minimal code fixes only if the proof exposes a real artifact/resume/idempotence bug

Verify:

- existing self-checks for touched modules still pass
- compile check passes
- public proof processes the targeted sessions or records a precise operational blocker
- repeated closing from the same run is stable and does not invent winners or duplicate sessions
- no order path, credential path, DB, OS service, `p_hat` model, or strategy-rule change was added

Gate:

- the public paper loop is inspectably stable across a longer bounded run and repeated result-closing attempts, or it returns a precise stability blocker for planning

## Fixed Remaining Plan

After Phase 21, the remaining planned development is capped at Phases 22-23.

Do not add more planned development phases for longer observation, more soak
runs, parameter watching, or ordinary public-data variance. Those belong to
normal simulated operation. New work after Phase 23 should be bug-driven or an
explicitly new product decision.

Do not build a config wrapper merely to shorten a long terminal command. A
copy-paste command plus clear run steps is sufficient unless execution finds a
real maintainability bug.

## Phase 22: Operator Run Commands, Status, And Runbook

Rules:

- Create one recommended copy-paste paper-run command for unattended public BTC 15m paper trading.
- Reuse the Phase 16-21 public path and current CLI/modules; do not create a wrapper/config layer unless a concrete issue makes the command unreliable.
- Document only the parameters that are operationally required: source query, mode, max sessions/runtime, wait budgets, capture budgets, paper stake, caller-supplied `p_hat`, entry seconds, move threshold, run directory, retry/heartbeat values.
- Provide the smallest status/inspection path needed to read existing artifacts.
- Keep final `p_hat` modeling out of scope; use caller-supplied `p_hat` only.
- Do not add live trading, wallet/signing, credentials, database storage, launchd/systemd/crontab, service install, OS restart policy, or new strategy behavior.

Deliver:

- exact start command and resume/close/status inspection commands
- stable default run directory convention
- short command reference explaining each required parameter and safe default
- operator runbook for starting, stopping, resuming, and diagnosing the paper bot
- optional tiny status command only if existing artifact inspection is too error-prone

Gate:

- a user can start and inspect the paper bot from documented terminal steps without reconstructing long commands by hand

## Phase 23: Local Process Supervision

Rules:

- Add one local unattended-process option for this machine only after Phase 22 defines the canonical command and operator surface.
- Prefer macOS `launchd` if this remains a Mac-local deployment.
- The supervisor starts the existing paper command; it must not change trading logic.
- Logs and run artifacts must remain local and inspectable through the Phase 22 operator path.
- Do not add live trading, wallet/signing, credentials, database storage, `p_hat` modeling, strategy changes, or cloud deployment.

Deliver:

- local supervisor config/template or install instructions
- start/stop/restart/status instructions
- proof that the supervised process can start the canonical paper command and write artifacts/logs to the expected location

Gate:

- the paper bot can be left running unattended locally and inspected/restarted through documented commands

## After Phase 23

The planned development track is complete for the paper bot. Continue with:

- real simulated operation
- bug-driven fixes when actual failures appear
- data review after enough paper sessions have accumulated
- explicit new planning only for a new product decision such as final `p_hat`, live trading, parameter research, notifications, UI, or database storage

## Unresolved Before Later Phases

Do not let execution answer these silently:

- final `p_hat` model
- live trading path
- optimizer or parameter sweep
- pause or stop-trading automation
- multi-entry or richer position management
- OS-level process supervision and machine restart policy
