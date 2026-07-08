# Issues

## Current Summary

- Current phase: minimal trade ledger and Polymarket-open execution complete; ready for separate acceptance if requested
- Current recommended next task: review `polybot-paper-minimal-trade-ledger-and-polymarket-open`
- Latest accepted slice: Phase 23 local process supervision
- Open blockers: none for planning; final `p_hat` model and live trading remain explicit future product decisions outside this config/operator UX task
- Last updated: 2026-07-08

## Log

### 2026-07-08 - Main Publish For Current Project State

- Goal: Commit the current full PolyBot workspace state and push it to `origin/main`.
- Changed:
  - Updated `docs/project_notes/issues.md`
- Verified:
  - Local branch is `main`
  - `origin` points to `https://github.com/Jeffrey22444/PolyBot.git`
  - The worktree contains the current project changes requested for full-project publish
- Scope skipped:
  - No additional product or architecture changes were introduced by this maintenance step

### 2026-07-08 - Planning Handoff Prompt Rule Clarified

- Clarified in `docs/project_notes/zone_operating_model.md` that when `规划区`
  gives `执行区` a short prompt pointing at `current_task.md`, it should include
  the paired short `验收区` prompt in the same reply unless the user explicitly
  says to skip acceptance.
- No business code changed by this planning-rule update.

### 2026-07-08 - Minimal Trade Ledger And Polymarket Open Execution

任务ID：
polybot-paper-minimal-trade-ledger-and-polymarket-open

改动文件：
- Added `polybot/trade_ledger.py`
- Updated `polybot/e2e_dry_run.py`
- Updated `polybot/market_discovery.py`
- Updated `polybot/open_price.py`
- Updated `configs/polymarket_paper_btc_15m.yaml`
- Updated `.gitignore`
- Updated `docs/operator_runbook.md`
- Updated `docs/project_notes/issues.md`

实现要点：
- Added a standard-library `sqlite3` local ledger at default path `data/paper_trades.sqlite3`.
- Added one-row-per-`market_id` upsert behavior with minimal fields for market timing, open price/source, observation threshold, decision timing/move, side, stake/ask/shares, result, winning side, paper PnL, cumulative PnL, equity, ROI, and skip reason.
- Added `paper.initial_bankroll: 1000` and `paper.ledger_path: "data/paper_trades.sqlite3"` to the canonical BTC 15m paper config.
- Discovery now carries optional Polymarket public open/reference price fields when present.
- Open-price enrichment prefers Polymarket public metadata/reference/open fields and records `open_price_source=polymarket:<field>`; otherwise it keeps the existing Binance capture fallback and records `open_price_source=binance_btcusdt_fallback`.
- `e2e_dry_run` now writes ledger rows at session start, open-price capture, paper trade/skip, result closing, and `--close-existing-run-dir` closing.
- Operator stdout now uses compact per-market `[TRADE]`, `[SKIP]`, and `[RESULT]` lines while keeping Beijing-time prefixes from the previous slice.
- `p_hat` remains caller-supplied only; no model, training, estimation, or backfill was added.

运行命令：
- `python3 -m polybot.trade_ledger --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.e2e_dry_run --help`
- `python3 -m polybot.long_run --help`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `git diff --check`
- `rg -n "wallet|signing|order placement|order|p_hat model|p_hat training|training|DB schema|SQLite schema|ORM|cloud deployment|root/system|system daemon|LaunchDaemon|machine restart" polybot/trade_ledger.py polybot/e2e_dry_run.py polybot/open_price.py polybot/market_discovery.py configs/polymarket_paper_btc_15m.yaml docs/operator_runbook.md .gitignore`

结果：
- `trade_ledger --self-check` passed; it proved upsert without duplicate rows, `WIN`/`LOSS`/`PENDING`/`SKIPPED`/`NO_TRADE` statuses, win-rate/cumulative-PnL/equity/return stats, and absence of raw orderbook/tick/payload/token-id ledger columns.
- `open_price --self-check` passed; it covers Polymarket-priority open price and Binance fallback source labeling.
- `market_discovery --self-check` passed; it covers the optional Polymarket open price fields.
- `e2e_dry_run --self-check` passed; it covers config overrides, temporary ledger path, two skipped market rows, and existing artifact generation.
- Both CLI help commands passed.
- `compileall` passed.
- `git diff --check` passed.
- Forbidden search had only contextual/negative hits: runbook says no live-order path; runbook says `p_hat` is caller-supplied and not a model/training output; existing discovery parses `acceptingOrders`; ledger self-check asserts no raw/token columns.

手工检查：
- Ledger supplements existing JSON artifacts; artifact semantics and runner output remain in place.
- Terminal output avoids raw payloads, raw BTC ticks, token IDs, and long slugs.
- No wallet, signing, credential, live order placement, cloud deployment, root/system daemon, machine restart policy, ORM, external storage, or new dependency was added.
- Ponytail review: Lean already. Ship.

范围外未做：
- No strategy, signal, observation-window threshold, marketability, fill, resolution policy, PnL semantics, stake sizing, final `p_hat` model, training, backfill, live trading, wallet/signing, DB/ORM service, UI, notification, cloud, or supervisor/service behavior change.

阻塞/待规划决定：
- None.

### 2026-07-08 - Minimal Trade Ledger And Polymarket Open Task Ready

- Goal: Prepare the next execution task after user accepted the Beijing-time operator output slice.
- User-approved behavior:
  - Treat every BTC 15m market as one independent paper-trade record.
  - Store a minimal local backend ledger for later review across however many markets have run.
  - Optimize the ledger for overall win rate, cumulative paper PnL, simulated equity/ROI from a default 1000 initial bankroll, and failure conditions such as remaining time, move percentage, threshold, side, and skip reason.
  - The simulated bankroll is accounting-only and must not change stake sizing or trade decisions.
  - Keep terminal output minimal: one compact trade/skip line and one compact result/pending line per market at most.
  - Align open price with Polymarket public source when possible; clearly mark fallback source otherwise.
- Accepted by user:
  - `polybot-paper-operator-output-beijing-time`
- Active task:
  - `docs/project_notes/current_task.md`
  - `polybot-paper-minimal-trade-ledger-and-polymarket-open`
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Operator Beijing-Time Output Execution

任务ID：
polybot-paper-operator-output-beijing-time

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/operator_runbook.md`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a standard-library Beijing time formatter for human-readable operator stdout only: `timezone(timedelta(hours=8), "CST")`.
- `operator_print` now prefixes every operator brief line with `[YYYY-MM-DD HH:MM:SS CST]`.
- `MARKET_SELECTED` start/end fields now display Beijing time for the human brief.
- Kept JSON artifacts, machine timestamps, WebSocket source timestamps, strategy logic, observation window, threshold, stake, `p_hat` filtering, marketability, fills, resolution, and PnL semantics unchanged.
- Did not add timezone dependencies or a timezone configuration system.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `python3 -m polybot.e2e_dry_run --help`
- `python3 -c "from datetime import datetime, timezone; from polybot.e2e_dry_run import beijing_time_text, operator_time; print(beijing_time_text(datetime(2026,7,8,4,0,tzinfo=timezone.utc))); print(operator_time('2026-07-08T04:15:00+00:00'))"`
- `git diff --check`
- `rg -n "stop-loss|stop loss|take-profit|take profit|reverse|reversal|grid|multi-entry|multiple entries|wallet|signing|credential|real order|live order|account API|database|SQLite|sqlite|ORM|cloud deployment|notification|UI|p_hat model|train|training|backfill" polybot/e2e_dry_run.py docs/operator_runbook.md`

结果：
- `e2e_dry_run --self-check` passed and now asserts:
  - `2026-07-08T04:00:00Z` formats as `2026-07-08 12:00:00 CST`
  - `operator_time("2026-07-08T04:15:00+00:00")` formats as `2026-07-08 12:15:00 CST`
- `compileall` passed.
- `e2e_dry_run --help` passed; no strategy/runtime CLI behavior was changed for this task.
- Direct helper check printed:
  - `2026-07-08 12:00:00 CST`
  - `2026-07-08 12:15:00 CST`
- `git diff --check` passed.
- Forbidden search only found the existing runbook note that `p_hat` is not a trained or inferred model.

手工检查：
- `operator_print` remains guarded by `operator_output.enabled`.
- Only stdout/operator brief formatting changed; artifact writers still use existing JSON/ISO paths.
- `docs/operator_runbook.md` examples now show Beijing-time prefixes and Beijing-time market start/end fields.
- Ponytail review: Lean already. Ship. No new dependency, config layer, or broad refactor.

范围外未做：
- No strategy, observation-window, threshold, paper stake, `p_hat`, discovery, open-price, marketability, fill, resolution, PnL, artifact schema, database, UI, notification, live trading, wallet/signing, cloud, or service behavior change.

阻塞/待规划决定：
- None.

### 2026-07-08 - Operator Beijing-Time Output Task Ready

- Goal: Prepare a narrow execution task to show paper-run operator brief times in Beijing time.
- Active task:
  - `docs/project_notes/current_task.md`
  - `polybot-paper-operator-output-beijing-time`
- Scope:
  - Human-readable stdout/operator brief formatting only.
  - Keep machine artifacts and trading logic unchanged.
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Observation Window Config And Operator Briefs Execution

任务ID：
polybot-paper-observation-window-config-and-operator-briefs

改动文件：
- Added `configs/polymarket_paper_btc_15m.yaml`
- Updated `requirements.txt`
- Updated `polybot/e2e_dry_run.py`
- Updated `polybot/signal.py`
- Updated `polybot/paper_runner.py`
- Updated `polybot/marketability.py`
- Updated `polybot/paper.py`
- Updated `scripts/paper_btc_15m_launch.sh`
- Updated `docs/operator_runbook.md`
- Updated `docs/local_process_supervision.md`
- Updated `docs/project_notes/issues.md`

范围边界：
- Implemented the approved BTC 15m paper behavior: observe continuously during the final configurable window, default `observe_start_remaining_seconds=300`, and attempt at most one paper entry on the first threshold crossing.
- Added YAML config loading for `polybot.e2e_dry_run --config`, with command-line flags overriding YAML values.
- Added config validation for positive stake, non-negative thresholds/timing/capture values, `max_entries_per_market == 1`, and valid `p_hat` when the filter is enabled.
- Added configurable `p_hat` filtering: enabled preserves existing `p_hat=0.55` and positive edge behavior; disabled still requires direction signal, mapped token, and ask depth but does not skip solely for missing/non-positive `p_hat`.
- Added low-frequency operator brief lines for run start, market selection, observation start, trigger/final market check, paper open, skip, and market result.
- Updated launcher to pass `--config configs/polymarket_paper_btc_15m.yaml` plus `--run-dir`, avoiding duplicated long defaults.
- Did not add stop-loss, take-profit, reversal, averaging, grid, multi-entry, live trading, wallet/signing, account API, database, UI, notification system, cloud deployment, service changes, or `p_hat` modeling.

运行命令：
- `python3 -m pip install 'PyYAML>=6,<7'`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.marketability`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `bash -n scripts/paper_btc_15m_launch.sh`
- `python3 -m polybot.signal`
- `python3 -m polybot.e2e_dry_run --help`
- `git diff --check`
- `rg -n "stop-loss|stop loss|take-profit|take profit|reverse|reversal|grid|multi-entry|multiple entries|wallet|signing|credential|real order|live order|account API|database|SQLite|sqlite|ORM|cloud deployment|notification|UI|p_hat model|train|training|backfill" configs docs/product_consensus/polymarket_paper_trader_logic_chain.md docs/operator_runbook.md docs/local_process_supervision.md polybot scripts requirements.txt`
- `rg -n "4 minutes|3 minutes|fixed check|wait_to_entry|wait_to_entry_budget|entry_window_missed|max_wait_to_entry" docs/product_consensus/polymarket_paper_trader_logic_chain.md docs/operator_runbook.md docs/local_process_supervision.md scripts/paper_btc_15m_launch.sh configs/polymarket_paper_btc_15m.yaml polybot/e2e_dry_run.py`

结果：
- Required self-checks passed:
  - `python3 -m polybot.e2e_dry_run --self-check`
  - `python3 -m polybot.paper_runner --session-self-check`
  - `python3 -m polybot.marketability`
  - `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
  - `bash -n scripts/paper_btc_15m_launch.sh`
- Extra signal check passed: `python3 -m polybot.signal`.
- `git diff --check` passed.
- `e2e_dry_run --help` now exposes `--config`, `--observe-start-remaining-seconds`, `--observation-tick-seconds`, `--max-wait-to-observation-seconds`, and `--p-hat-filter-enabled/--no-p-hat-filter-enabled`; old e2e fixed-entry args are no longer exposed.
- `marketability` self-check proves the difference between enabled and disabled `p_hat` filtering with `"p_hat_filter_disabled_filled": true`.
- `paper_runner --session-self-check` covers observation-window triggering and disabled-`p_hat` fill behavior.
- `e2e_dry_run --self-check` covers YAML loading/defaults plus command-line override of YAML values.

手工检查：
- `configs/polymarket_paper_btc_15m.yaml` contains the requested strategy/paper/marketability/discovery/timing/capture/runtime/operator_output sections.
- `run_manifest.json` config snapshot uses the final effective config from YAML plus CLI overrides via `args.config_snapshot`.
- Operator brief output is one line per major event, not per WebSocket tick or full orderbook.
- Launcher now starts the configured CLI and still only creates run/log directories plus local pointers before `exec`.
- Forbidden search hits were documentation-only negative statements such as "not live trading" / "not trained" / "does not include", plus false positives from `reversed(records)`; no implementation path for forbidden behavior was added.
- Old fixed-entry search found no matches in the e2e/operator/config path.

范围外未做：
- No stop-loss, take-profit, reversal, averaging, grid, multi-entry, live trading, wallet/signing/credentials, account API, database/SQLite/ORM/schema, UI, notifications, cloud deployment, new service, or `p_hat` model/training/backfill.
- No change to public data source selection beyond config-driven existing discovery parameters.
- No long public soak.

阻塞/待规划决定：
- None.

### 2026-07-08 - Observation Window And Config Task Ready

- Goal: Convert the user-approved strategy adjustment into an execution-ready task.
- User-approved behavior:
  - No stop-loss concept belongs in this strategy.
  - Entry logic should observe continuously during the final configurable N seconds of a BTC 15m market.
  - The default observation window is the last 300 seconds.
  - The move threshold remains configurable, defaulting to `0.05%`.
  - `p_hat` is a configurable marketability filter, not part of the root signal and not a model.
  - `p_hat` filtering should be switchable on/off.
- Active task:
  - `docs/project_notes/current_task.md`
  - `polybot-paper-observation-window-config-and-operator-briefs`
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Product Consensus Updated For Observation Window

- Goal: Fix product consensus docs so they match the user-approved strategy logic before execution.
- Changed:
  - Updated `docs/product_consensus/polymarket_paper_trader_logic_chain.md`
  - Updated `docs/product_consensus/polymarket_paper_trader_v1.md`
  - Updated `docs/project_notes/current_task.md`
- Current consensus:
  - The active strategy starts continuous observation during the final configurable N seconds of the BTC 15m market.
  - The default observation window starts at 300 seconds remaining.
  - The first threshold crossing may create one paper entry.
  - `p_hat` is an optional marketability filter, not part of the root signal and not a model.
  - No stop-loss concept belongs in this strategy.
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Product Consensus Folder Consolidated

- Goal: Keep `docs/product_consensus/` limited to the latest active strategy logic.
- Changed:
  - Kept `docs/product_consensus/polymarket_paper_trader_logic_chain.md` as the only active product consensus document.
  - Removed the historical `docs/product_consensus/polymarket_paper_trader_v1.md` file.
  - Updated `AGENTS.md` and `docs/project_notes/key_facts.md` so future runs read the active consensus file.
- Scope skipped:
  - No business code changed.
  - Historical task-card archives were not rewritten.

### 2026-07-08 - Main Branch Publish

- Goal: Commit the current full PolyBot workspace state and push it to `origin/main`.
- Changed:
  - Updated `docs/project_notes/issues.md`
- Verified:
  - Local branch is `main` and tracks `origin/main`
  - The current worktree contains tracked and untracked project files that belong to the requested full-project publish scope
  - `origin` points to `https://github.com/Jeffrey22444/PolyBot.git`
- Manual:
  - `gh auth status` currently reports an invalid token, so direct GitHub CLI PR flows are unavailable until re-authenticated
- Scope skipped:
  - No product behavior or architecture changes made by this maintenance step

### 2026-07-08 - Strategy Logic Chain Readability Revision

- Goal: Compare the original v1 consensus with the new logic-chain document and make the logic-chain document easier for humans to read.
- Changed:
  - Rewrote `docs/product_consensus/polymarket_paper_trader_logic_chain.md` as a natural-language strategy flow with a parameter table.
  - Marked `docs/product_consensus/polymarket_paper_trader_v1.md` as the original v1 baseline instead of the current full source of truth.
  - Updated `docs/project_notes/key_facts.md` to distinguish the v1 baseline from the current logic-chain consensus.
- Notes:
  - Removed runbook-style command blocks and artifact inventory from the logic-chain document.
  - Kept the strategy-relevant parameters: 15m market, 240/180 second entry moments, 3 second tolerance, 0.05% move threshold, fixed paper stake 9, caller-supplied `p_hat` 0.55, 8 second capture windows, and 30 second heartbeat.
  - No business code changed.

### 2026-07-08 - Strategy Logic Chain Consensus Added

- Goal: Add a single readable strategy/runtime consensus document for the completed paper-bot path.
- Status note:
  - User reported Phase 23 acceptance completed.
  - Fixed planned paper-bot build track is complete; next work is simulated operation and bug-driven fixes.
- Changed:
  - Added `docs/product_consensus/polymarket_paper_trader_logic_chain.md`
- Notes:
  - Documents the full chain from local launcher through discovery, open-price capture, entry timing, root signal, marketability, paper fill, conservative resolution, PnL, artifacts, and runtime cadence.
  - Records that the current launcher uses `--heartbeat-interval-seconds 30`, `--capture-seconds 8`, and `--runner-seconds 8`.
  - No business code changed.

### 2026-07-08 - Phase 22 Accepted And Phase 23 Ready

- Goal: Record user-confirmed Phase 22 acceptance and prepare the final fixed phase.
- Accepted slice:
  - Phase 22 operator run commands/status/runbook.
  - `docs/operator_runbook.md` documents the canonical paper-run command, status inspection, close-existing-run, run-dir convention, and common state/skip reason handling.
- Planning note:
  - Phase 23 is the last fixed planned phase.
  - Scope is local process supervision for this Mac, reusing the Phase 22 command and artifact path.
  - Do not expand into live trading, wallet/signing, final `p_hat` modeling, database/storage backend, cloud deployment, root/system daemon, or machine restart policy.
  - After Phase 23, continue with actual simulated operation and bug-driven fixes unless the user opens a new product decision.
- Active task:
  - `docs/project_notes/current_task.md`
  - `polybot-paper-phase-23-local-process-supervision`
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Phase 23 Local Process Supervision Execution

任务ID：
polybot-paper-phase-23-local-process-supervision

改动文件：
- Added `docs/local_process_supervision.md`
- Added `docs/launchd/com.polybot.paper-btc-15m.plist`
- Added `scripts/paper_btc_15m_launch.sh`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a Mac-local, user-level supervision path for the existing Phase 22 paper command.
- The launcher only creates the run directory, log directory, latest-run/latest-log pointers, and then `exec`s `python3 -m polybot.e2e_dry_run` with the Phase 22 canonical BTC 15m paper parameters.
- The launchd plist is repo-local documentation/template only; it was not copied into `~/Library/LaunchAgents` and no `launchctl` command was run.
- Did not modify `polybot/`, signal logic, open-price freshness, marketability/fill, PnL, resolution policy, artifact semantics, or runner behavior.

运行命令：
- `chmod +x scripts/paper_btc_15m_launch.sh`
- `bash -n scripts/paper_btc_15m_launch.sh`
- `plutil -lint docs/launchd/com.polybot.paper-btc-15m.plist`
- `python3 -m polybot.e2e_dry_run --help`
- `python3 -m polybot.long_run --help`
- `rg -n "wallet|signing|credential|order placement|place_order|create_order|cancel_order|live order|p_hat.*(model|training)|training.*p_hat|SQLite|sqlite|ORM|database schema|cloud deployment|root/system|LaunchDaemon|systemd|crontab|machine restart policy|order" docs/local_process_supervision.md docs/launchd/com.polybot.paper-btc-15m.plist scripts/paper_btc_15m_launch.sh`

结果：
- `bash -n` passed for the launcher.
- `plutil -lint` returned `docs/launchd/com.polybot.paper-btc-15m.plist: OK`.
- Both CLI help checks passed and confirmed the documented Phase 22 command surface is still available.
- No `polybot/` files were changed, so `compileall` was not required.

supervision proof：
```json
{
  "launcher": "scripts/paper_btc_15m_launch.sh",
  "plist_template": "docs/launchd/com.polybot.paper-btc-15m.plist",
  "auto_installed": false,
  "launchctl_run": false,
  "run_dir_pattern": "runs/paper-btc-15m/<UTC timestamp>/",
  "stdout_stderr_log_pattern": "runs/paper-btc-15m-logs/<UTC timestamp>.log",
  "latest_artifact_pointer": "runs/paper-btc-15m/latest_run_dir.txt",
  "latest_log_pointer": "runs/paper-btc-15m-logs/latest_log.txt",
  "uses_phase22_canonical_command": true,
  "p_hat_modeling": false,
  "business_logic_changed": false
}
```

手工检查：
- `docs/local_process_supervision.md` includes start, stop, restart, status, logs, artifact inspection, disable-supervision, and return-to-Phase-22 foreground instructions.
- The document explicitly states `p_hat` is caller-supplied and not a trained, inferred, smoothed, or backfilled model.
- The document explicitly frames this as Mac-local/user-level supervision, not live trading, cloud deployment, or a root/system service.
- Forbidden search had one expected documentation-only hit: `docs/local_process_supervision.md` says this is not live trading, cloud deployment, or a root/system service. No launcher/plist implementation path contains wallet/signing/order, `p_hat` model/training, DB/schema, cloud deployment implementation, root/system daemon, or machine restart policy behavior.

范围外未做：
- No live trading, wallet/signing/credential/order placement, final `p_hat` model/training/backfill, database/SQLite/ORM/schema, external storage, cloud deployment, remote worker, Docker/Kubernetes, external monitoring, root/system service, machine restart policy, strategy change, or long public soak.
- No automatic LaunchAgent install, no write to `~/Library/LaunchAgents`, and no `launchctl bootstrap/bootout/kickstart`.
- No second trading orchestrator or config system.

阻塞/待规划决定：
- None.

### 2026-07-08 - Planning Verification Defaults Updated

- Goal: Reduce token waste from routine planning-doc verification.
- Changed:
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated local `zone-memory` skill files:
    - `/Users/jeffrey/.codex/skills/zone-memory/SKILL.md`
    - `/Users/jeffrey/.codex/skills/zone-memory/references/agents_section.md`
    - `/Users/jeffrey/.codex/skills/zone-memory/references/zone_operating_model_template.md`
- Rule:
  - Small `规划区` doc-only updates should not run `git diff --check` by default.
  - Prefer `git status --short` or targeted file reads for touched-file confirmation.
  - Use `git diff --check` only for larger Markdown rewrites, complex fenced code blocks, `.gitignore` edits, or concrete whitespace/conflict-marker risk.
  - Do not run full `git diff` as a routine planning check.
- Scope skipped:
  - No business code changed.
  - No execution task handed off.

### 2026-07-08 - Phase 22 Ready

- Goal: Prepare the active execution/acceptance task for operator run commands, status inspection, and runbook.
- Planning note:
  - Phase 22 is deliberately not a config-wrapper task.
  - A copy-paste terminal command is acceptable; the runbook should make it safe and repeatable.
  - Long public soak should not be repeated for this phase because Phase 21 already proved the closed loop.
- Active task:
  - `docs/project_notes/current_task.md`
  - `polybot-paper-phase-22-operator-runbook`
- Scope skipped:
  - No execution work performed by planning.
  - No business code changed by planning.

### 2026-07-08 - Phase 21 Accepted And Remaining Plan Revised

- Goal: Record user-confirmed Phase 21 execution/acceptance pass and remove unnecessary config-wrapper work from the remaining plan.
- Accepted slice:
  - Phase 21 public closed-loop soak and repeated close/idempotence proof.
- Planning revision:
  - Phase 22 is no longer a separate "build a config/entrypoint just to avoid a long command" phase.
  - Since a copy-paste terminal command is acceptable, Phase 22 becomes operator run commands/status/runbook.
  - The remaining fixed development track is now Phase 22 operator run commands/status/runbook, then Phase 23 local process supervision.
- Scope skipped:
  - No execution task handed off.
  - No business code changed by planning.

### 2026-07-08 - Phase 22 Operator Runbook Execution

任务ID：
polybot-paper-phase-22-operator-runbook

改动文件：
- Updated `docs/operator_runbook.md`
- Updated `.gitignore`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a docs-only operator runbook for the existing public paper-run path.
- Reused the current `polybot.e2e_dry_run`, `polybot.long_run`, and run-artifact JSON surface; no new config wrapper, orchestrator, helper, service layer, or status script.
- Added `runs/` to `.gitignore` so workspace-local paper artifacts do not get committed by accident.
- Did not modify signal logic, open-price freshness, marketability/fill, PnL, resolution policy, wallet/signing/order paths, or process supervision behavior.

运行命令：
- `python3 -m polybot.e2e_dry_run --help`
- `python3 -m polybot.long_run --help`
- `rg -n "Phase 22|ADR-027|operator run|runbook|close-existing-run|dry_run_report|heartbeat.jsonl|status.json|run_manifest.json|session_index.json|summary.json|no_valid_candidate|not_closed|non_positive_trade_edge|missing_p_hat|stale_open_price_record|blocked" docs/implementation-plan.md docs/project_notes/decisions.md polybot/e2e_dry_run.py polybot/long_run.py polybot/run_artifacts.py`
- `rg -n "missing_p_hat|non_positive_trade_edge|stale_open_price_record|no_valid_candidate|not_closed|entry_window_missed|wait_to_open_budget_exceeded|wait_to_entry_budget_exceeded|public_discovery_blocked|runner_blocked|public_resolution_blocked" polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|p_hat model|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" docs/operator_runbook.md polybot requirements.txt`

结果：
- `docs/operator_runbook.md` now documents one copy-paste public BTC 15m paper-run command, a `runs/paper-btc-15m/<UTC timestamp>/` convention, status/inspection commands for the existing artifacts, safe stop guidance, close-existing-run usage, and a parameter quick reference.
- Help output matches the documented CLI surface, including `--search-query`, `--mode`, `--max-sessions`, `--max-runtime-seconds`, wait budgets, capture budgets, `--paper-stake`, `--p-hat`, `--entry-remain-seconds`, `--move-threshold-pct`, `--attempt-public-resolution`, and `--run-dir`.
- The runbook explicitly keeps `p_hat` as caller-supplied input and does not promise automatic resume of public discovery runs.
- `runs/` is now ignored in workspace Git state.
- Forbidden-path search found no wallet/signing/order/live-trading, model-training, DB/schema, or OS-service language in the runbook or current code paths touched by this phase.

runbook proof：
```json
{
  "runbook_path": "docs/operator_runbook.md",
  "documented_start_command": true,
  "documented_run_dir_convention": "runs/paper-btc-15m/<UTC timestamp>/",
  "documented_close_existing_run": true,
  "documented_inspection_files": [
    "run_manifest.json",
    "status.json",
    "summary.json",
    "session_index.json",
    "heartbeat.jsonl",
    "dry_run_report.json"
  ],
  "documented_skip_or_status_terms": [
    "running",
    "stopped",
    "blocked",
    "no_valid_candidate",
    "not_closed",
    "non_positive_trade_edge",
    "missing_p_hat",
    "stale_open_price_record"
  ],
  "documents_no_auto_resume_claim": true,
  "docs_only": true
}
```

手工检查：
- Verified from source that `dry_run_report.json` carries `final_status`, `final_stop_reason`, step-level blocker/skip reasons, and resolution counts.
- Verified from source that `run_manifest.json`, `session_index.json`, and `summary.json` are stable artifacts written by `polybot.run_artifacts`.
- Verified from source that `status.json` and `heartbeat.jsonl` are produced by `polybot.long_run`, with `running`, `interrupted`, `stopped`, `resume_skipped`, `recoverable_error`, and `retry_limit_reached` states/events.
- Verified from source that `--close-existing-run-dir` rebuilds artifacts and re-attempts public resolution from an existing run instead of resuming discovery from an interruption point.

范围外未做：
- No live trading, wallet/signing/credential path, final `p_hat` model/training/backfill, database/SQLite/ORM/schema work, launchd/systemd/crontab/service install, OS restart policy, config wrapper, extra orchestrator, or status helper.
- No new public soak or long-running proof.
- No `polybot/` behavior change.

阻塞/待规划决定：
- None for Phase 22 within the assigned scope.
- Phase 23 local process supervision remains a separate next slice if the user wants unattended local restarts/install behavior.

### 2026-07-08 - Phase 21 Public Soak Resume Proof Execution

任务ID：
polybot-paper-phase-21-public-soak-resume-proof

改动文件：
- Updated `docs/project_notes/issues.md`
- No product code changed for Phase 21; existing Phase 20 public close-existing-run path satisfied this proof.

范围边界：
- Ran one real bounded public closed-loop proof using `--search-query "bitcoin up down 15m"`, `--mode next`, `--max-sessions 3`, and `--attempt-public-resolution`.
- Reused existing discovery, fresh open-price capture, wait-to-entry, paper runner, conservative resolution ingestion, batch close, run artifacts, and long-run status/heartbeat.
- Repeated `close-existing-run` twice from the same source run artifacts to prove session/status stability.
- Did not modify strategy, open-price freshness, marketability/fill, PnL, conservative resolution policy, artifact schema, DB/storage, daemon/service, wallet/signing, live order, or p_hat behavior.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.long_run --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|p_hat model|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|guess winner|guessed winner" polybot requirements.txt`
- Public soak: `python3 -m polybot.e2e_dry_run --max-sessions 3 --max-runtime-seconds 5400 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 8 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 10 --limit 100 --lookahead-minutes 90 --max-wait-to-open-seconds 900 --max-wait-to-entry-seconds 900 --entry-window-tolerance-seconds 3 --max-open-price-delay-seconds 5 --attempt-public-resolution --run-dir /private/tmp/polybot_phase21_public_soak`
- Repeated close 1: `python3 -m polybot.e2e_dry_run --close-existing-run-dir /private/tmp/polybot_phase21_public_soak --run-id phase21-close-pass-1 --run-dir /private/tmp/polybot_phase21_close_1 --attempt-public-resolution`
- Repeated close 2: `python3 -m polybot.e2e_dry_run --close-existing-run-dir /private/tmp/polybot_phase21_public_soak --run-id phase21-close-pass-2 --run-dir /private/tmp/polybot_phase21_close_2 --attempt-public-resolution`
- `python3 -m json.tool /private/tmp/polybot_phase21_public_soak/session_index.json`
- `python3 -m json.tool /private/tmp/polybot_phase21_public_soak/summary.json`
- `python3 -m json.tool /private/tmp/polybot_phase21_public_soak/status.json`
- `python3 -m json.tool /private/tmp/polybot_phase21_public_soak/run_manifest.json`
- `tail -n 5 /private/tmp/polybot_phase21_public_soak/heartbeat.jsonl`
- Structural compare across source/close_1/close_2 session indexes.

结果：
- All required touched self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Public soak completed 3 chronological BTC 15m sessions:
  - `2827880`, `btc-updown-15m-1783490400`, `2026-07-08T06:00:00+00:00` -> `2026-07-08T06:15:00+00:00`
  - `2827910`, `btc-updown-15m-1783491300`, `2026-07-08T06:15:00+00:00` -> `2026-07-08T06:30:00+00:00`
  - `2827938`, `btc-updown-15m-1783492200`, `2026-07-08T06:30:00+00:00` -> `2026-07-08T06:45:00+00:00`
- `dry_run_report.json` records `attempted_session_count: 3`, `processed_session_count: 3`, `resolution_attempted_count: 3`, `final_stop_reason: reached_max_sessions`, and no blockers.
- Resolution/closing result: 2 closed, 1 pending/skipped with precise reason `not_closed`.
- Repeated close-existing-run outputs had identical session keys, result statuses, resolution statuses, skip reasons, and paper PnL compared with the source run.

public soak proof：
```json
{"run_dir":"/private/tmp/polybot_phase21_public_soak","attempted_session_count":3,"processed_session_count":3,"resolution_attempted_count":3,"sessions_closed":2,"sessions_pending_or_skipped":1,"final_stop_reason":"reached_max_sessions","blockers":[],"sessions":[{"market_id":"2827880","market_slug":"btc-updown-15m-1783490400","market_start_time":"2026-07-08T06:00:00+00:00","market_end_time":"2026-07-08T06:15:00+00:00","status":"completed"},{"market_id":"2827910","market_slug":"btc-updown-15m-1783491300","market_start_time":"2026-07-08T06:15:00+00:00","market_end_time":"2026-07-08T06:30:00+00:00","status":"completed"},{"market_id":"2827938","market_slug":"btc-updown-15m-1783492200","market_start_time":"2026-07-08T06:30:00+00:00","market_end_time":"2026-07-08T06:45:00+00:00","status":"completed"}]}
```

resolution/result proof：
```json
{"session_index":[{"session_key":"01_2827880","market_id":"2827880","resolution_status":"resolved","result_status":"closed","resolution_path":"sessions/01_2827880/resolution.json","resolution_raw_path":"sessions/01_2827880/resolution_raw.json","result_path":"sessions/01_2827880/result.json","paper_pnl":0.0,"skip_reason":null},{"session_key":"02_2827910","market_id":"2827910","resolution_status":"resolved","result_status":"closed","resolution_path":"sessions/02_2827910/resolution.json","resolution_raw_path":"sessions/02_2827910/resolution_raw.json","result_path":"sessions/02_2827910/result.json","paper_pnl":0.0,"skip_reason":null},{"session_key":"03_2827938","market_id":"2827938","resolution_status":"skipped","result_status":"skipped","resolution_path":"sessions/03_2827938/resolution.json","resolution_raw_path":"sessions/03_2827938/resolution_raw.json","result_path":null,"paper_pnl":null,"skip_reason":"not_closed"}]}
```

aggregate/status proof：
```json
{"summary":{"sessions_seen":3,"sessions_closed":2,"sessions_skipped":1,"skipped_reasons":{"not_closed":1},"aggregate_signal_only_counts":{"UP":0,"DOWN":1,"NO_SIGNAL":1},"aggregate_tradable_paper_pnl":0.0},"status":{"status":"stopped","processed_sessions":0,"last_error":null},"manifest":{"status":"stopped","mode":"public_data_e2e_dry_run","session_index":"session_index.json","summary":"summary.json","status_json":"status.json","heartbeat_jsonl":"heartbeat.jsonl"}}
```

runner proof：
```json
[{"runner":1,"signal":{"signal":"DOWN","remaining_seconds":240,"ret_pct":-0.06106529484479596},"paper_record_type":"skipped_trade_record","skip_reason":"non_positive_trade_edge"},{"runner":2,"signal":{"signal":"NO_SIGNAL","remaining_seconds":240,"ret_pct":0.009579460104821646},"paper_record_type":null,"skip_reason":null},{"runner":3,"signal":{"signal":"DOWN","remaining_seconds":240,"ret_pct":-0.07984347548314641},"paper_record_type":"skipped_trade_record","skip_reason":"non_positive_trade_edge"}]
```

repeated close/idempotence proof：
```json
{"source":[["01_2827880","2827880","resolved","closed",null,0.0],["02_2827910","2827910","resolved","closed",null,0.0],["03_2827938","2827938","skipped","skipped","not_closed",null]],"close_1":[["01_2827880","2827880","resolved","closed",null,0.0],["02_2827910","2827910","resolved","closed",null,0.0],["03_2827938","2827938","skipped","skipped","not_closed",null]],"close_2":[["01_2827880","2827880","resolved","closed",null,0.0],["02_2827910","2827910","resolved","closed",null,0.0],["03_2827938","2827938","skipped","skipped","not_closed",null]],"all_equal":true,"unique_counts":[3,3,3]}
```

artifact/status proof：
```json
{"chronological":true,"unique_keys":true,"keys":["01_2827880","02_2827910","03_2827938"],"starts":["2026-07-08T06:00:00+00:00","2026-07-08T06:15:00+00:00","2026-07-08T06:30:00+00:00"],"readable_files":["dry_run_report.json","run_manifest.json","session_index.json","summary.json","status.json","heartbeat.jsonl","supervisor.jsonl","sessions/01_2827880/result.json","sessions/02_2827910/result.json","sessions/03_2827938/resolution.json"]}
```

手工检查：
- Every attempted session has discovery, wait-to-open, BTC reference capture, open-price, wait-to-entry, paper_runner, and resolution/result status in `dry_run_report.json` and/or `session_index.json`.
- Third session was not guessed closed; it stayed `not_closed` with copied raw/derived resolution metadata and no paper PnL.
- Heartbeat records `resume_skipped` for all three already closed/skipped session keys after artifacts were built, proving process-local resume did not duplicate work.
- Repeated close outputs `/private/tmp/polybot_phase21_close_1` and `/private/tmp/polybot_phase21_close_2` preserved the same session ordering and statuses as `/private/tmp/polybot_phase21_public_soak`.
- No product code changes were required for Phase 21; only `issues.md` was updated with evidence.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, final p_hat model/training/backfill/estimation, database, SQLite, ORM, long-term DB schema, external storage backend, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, strategy change, signal change, open-price freshness change, marketability/fill change, PnL change, conservative resolution policy change, guessed winner, or new trading rule.

阻塞/待规划决定：
- Phase 21 public closed-loop soak and repeated close/idempotence proof is no longer blocked in this run.
- Final `p_hat` modeling, canonical unattended run configuration/operator runbook, OS-level process supervision/service installation, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 20 Accepted And Phase 21 Ready

- Goal: Record user-confirmed completion/acceptance of Phase 20, then prepare a slightly larger stability proof slice.
- Accepted slice:
  - Phase 20 public resolution and result-closing wiring.
  - Completed public sessions can be conservatively resolved/closed from public event child-market metadata when unambiguous.
- Planning note:
  - Phase 21 should bundle a longer public closed-loop run with repeated close/resume/idempotence checks.
  - This is still paper-only and must not turn into database, OS service, live trading, or `p_hat` modeling work.
- Scope skipped:
  - No business code changed by planning.

### 2026-07-08 - Fixed Remaining Plan

- Goal: Stop phase creep and cap the remaining planned paper-bot development.
- Fixed remaining phases:
  - Phase 21: public closed-loop soak and repeated close/idempotence proof.
  - Phase 22: canonical unattended run configuration.
  - Phase 23: operator status and runbook.
  - Phase 24: local process supervision.
- Planning rule:
  - Do not add more planned development phases for longer observation, soak duration, or normal public-data variance.
  - After Phase 24, continue with real simulated operation and bug-driven fixes unless the user explicitly opens a new product decision.
- Scope skipped:
  - No execution task handed off.
  - No business code changed by planning.

### 2026-07-08 - Phase 20 Public Resolution Closing Execution

任务ID：
polybot-paper-phase-20-public-resolution-closing

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `polybot/run_artifacts.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Reused existing `resolution_ingestion.ingest_metadata(...)`, `supervisor_results.batch_close(...)`, and `run_artifacts.build_run_artifacts(...)`.
- Added explicit public resolution attempts only for completed sessions with runner output.
- Public resolution fetch uses completed event metadata by exact session slug, then exact child market id/slug match before conservative ingestion.
- Added `--attempt-public-resolution` for normal dry-run and `--close-existing-run-dir` to close an already completed public run without rerunning signal/open-price/marketability.
- Did not change root signal, open-price freshness, marketability/fill, paper PnL formula, or resolution policy.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|guess winner|guessed winner" polybot requirements.txt`
- Initial public dry-run attempt: `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 120 --paper-stake 9 --p-hat 0.55 --capture-seconds 2 --capture-limit 2 --runner-seconds 2 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 10 --limit 100 --lookahead-minutes 90 --max-wait-to-open-seconds 0 --max-wait-to-entry-seconds 0 --entry-window-tolerance-seconds 3 --max-open-price-delay-seconds 5 --attempt-public-resolution --run-dir /private/tmp/polybot_phase20_public_resolution_proof`
- Completed-session public close proof: `python3 -m polybot.e2e_dry_run --close-existing-run-dir /private/tmp/polybot_phase19_multi_session_public_run --run-id phase20-public-resolution-closing --run-dir /private/tmp/polybot_phase20_public_resolution_closing_events --attempt-public-resolution`
- `python3 -m json.tool /private/tmp/polybot_phase20_public_resolution_closing_events/dry_run_report.json`
- `python3 -m json.tool /private/tmp/polybot_phase20_public_resolution_closing_events/session_index.json`
- `python3 -m json.tool /private/tmp/polybot_phase20_public_resolution_closing_events/summary.json`
- `python3 -m json.tool /private/tmp/polybot_phase20_public_resolution_closing_events/sessions/01_2826343/result.json`
- `python3 -m json.tool /private/tmp/polybot_phase20_public_resolution_closing_events/sessions/02_2827504/result.json`

结果：
- Touched self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Initial live dry-run found no next valid candidate at that moment and recorded `no_valid_candidate`; it was not used as passing completed-session proof.
- Completed-session proof reused Phase 19 public runner outputs and attempted resolution for two completed BTC 15m sessions.
- Both completed sessions resolved conservatively from public event child-market metadata:
  - `2826343` / `btc-updown-15m-1783485900` -> `UP`
  - `2827504` / `btc-updown-15m-1783486800` -> `DOWN`
- `dry_run_report.json` records `resolution_attempted_count: 2`, `sessions_closed: 2`, `sessions_pending_or_skipped: 0`.
- `session_index.json` records resolution path, raw resolution path, result path, and `paper_pnl` for both sessions.

resolution/closing proof：
```json
{"run_dir":"/private/tmp/polybot_phase20_public_resolution_closing_events","resolution_attempted_count":2,"sessions_closed":2,"sessions_pending_or_skipped":0,"resolution_steps":[{"session_index":1,"market_id":"2826343","status":"resolved","resolution_path":"/private/tmp/polybot_phase20_public_resolution_closing_events/_source/resolution_1_2826343.json","raw_resolution_path":"/private/tmp/polybot_phase20_public_resolution_closing_events/_source/resolution_raw_1_2826343.json"},{"session_index":2,"market_id":"2827504","status":"resolved","resolution_path":"/private/tmp/polybot_phase20_public_resolution_closing_events/_source/resolution_2_2827504.json","raw_resolution_path":"/private/tmp/polybot_phase20_public_resolution_closing_events/_source/resolution_raw_2_2827504.json"}]}
```

artifact proof：
```json
{"session_index":[{"market_id":"2826343","resolution_status":"resolved","resolution_path":"sessions/01_2826343/resolution.json","resolution_raw_path":"sessions/01_2826343/resolution_raw.json","result_status":"closed","result_path":"sessions/01_2826343/result.json","paper_pnl":0.0},{"market_id":"2827504","resolution_status":"resolved","resolution_path":"sessions/02_2827504/resolution.json","resolution_raw_path":"sessions/02_2827504/resolution_raw.json","result_status":"closed","result_path":"sessions/02_2827504/result.json","paper_pnl":0.0}]}
```

aggregate summary：
```json
{"sessions_seen":2,"sessions_closed":2,"sessions_skipped":0,"skipped_reasons":{},"aggregate_signal_only_counts":{"UP":1,"DOWN":0,"NO_SIGNAL":1},"aggregate_tradable_paper_pnl":0.0}
```

per-session result proof：
```json
{"market_id":"2826343","winning_side":"UP","signal_only":{"counts":{"UP":0,"DOWN":0,"NO_SIGNAL":1},"winning_side_count":0,"losing_side_count":0,"no_signal_count":1},"tradable_signal":{"filled_count":0,"skipped_reasons":{},"total_paper_pnl":0}}
{"market_id":"2827504","winning_side":"DOWN","signal_only":{"counts":{"UP":1,"DOWN":0,"NO_SIGNAL":0},"winning_side_count":0,"losing_side_count":1,"no_signal_count":0},"tradable_signal":{"filled_count":0,"skipped_reasons":{"non_positive_trade_edge":1},"total_paper_pnl":0}}
```

手工检查：
- `polybot/e2e_dry_run.py` calls existing ingestion and batch closer; it does not derive a winner from BTC direction, title text, orderbook, or trade prices.
- Completed public event metadata had exact child markets with `closed: true`, `umaResolutionStatus: resolved`, binary outcomes, and terminal `outcomePrices`; conservative ingestion produced the winning side.
- `/markets?id` and `/markets?slug` returned empty for these completed 15m sessions; the working public source was `/events?slug=<market_slug>` with exact child-market extraction.
- `polybot.run_artifacts` changes are backward-compatible optional fields for resolution paths/skips.
- `polybot.signal`, `polybot.open_price`, `polybot.marketability`, `polybot.paper`, `polybot.result_closer`, and `polybot.resolution_ingestion` settlement rules were not modified.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, final p_hat model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, strategy change, signal change, open-price freshness change, marketability/fill change, settlement policy change, guessed winner, or new trading rule.

阻塞/待规划决定：
- Phase 20 public resolution/result closing proof is no longer blocked in this run.
- Final `p_hat` modeling, OS-level process supervision/service installation, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 19 Accepted And Phase 20 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 19, then prepare public resolution/result-closing wiring.
- Accepted slice:
  - Phase 19 bounded two-session public run proof, with unique chronological sessions and runner outputs.
- Planning note:
  - Phase 19 left both session results as `missing_resolution` by design.
  - Phase 20 should reuse existing conservative resolution ingestion and batch closing to attempt automatic close for completed public sessions.
  - If public metadata is not closed or not unambiguous, Phase 20 must keep the session pending/skipped with an explicit reason; it must not guess settlement.
- Scope skipped:
  - No business code changed by planning.

### 2026-07-08 - Phase 19 Bounded Multi-Session Public Run Execution

任务ID：
polybot-paper-phase-19-bounded-multi-session-public-run

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added minimal multi-session orchestration inside the existing public dry-run path.
- Reused existing strict discovery, bounded wait-to-open, fresh open-price capture, bounded wait-to-entry, and runner behavior.
- `max_sessions > 1` now attempts unique chronological sessions by advancing the discovery cursor to the previous session start and tracking processed market ids.
- Existing run artifacts are reused; no artifact schema rewrite, DB, daemon, OS service, settlement policy, strategy, open-price freshness, marketability/fill, wallet/signing, or p_hat behavior was changed.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m py_compile polybot/e2e_dry_run.py`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|historical kline|historical price|backfill|reconstruct" polybot requirements.txt`
- Live proof: `python3 -m polybot.e2e_dry_run --max-sessions 2 --max-runtime-seconds 3600 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 8 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 10 --limit 100 --lookahead-minutes 90 --max-wait-to-open-seconds 900 --max-wait-to-entry-seconds 900 --entry-window-tolerance-seconds 3 --max-open-price-delay-seconds 5 --run-dir /private/tmp/polybot_phase19_multi_session_public_run`
- `python3 -m json.tool /private/tmp/polybot_phase19_multi_session_public_run/dry_run_report.json`
- `python3 -m json.tool /private/tmp/polybot_phase19_multi_session_public_run/session_index.json`
- `nl -ba /private/tmp/polybot_phase19_multi_session_public_run/_source/runner_1.jsonl`
- `nl -ba /private/tmp/polybot_phase19_multi_session_public_run/_source/runner_2.jsonl`

结果：
- Touched self-check passed; it now includes a local no-network two-session loop assertion.
- Key existing self-checks passed: market discovery and session runner.
- Compile check passed.
- Forbidden-path search returned no matches.
- Live public proof used the required calibrated source and mode:
  - `--search-query "bitcoin up down 15m"`
  - `--mode next`
  - `--max-sessions 2`
- Live proof attempted two unique chronological BTC 15m sessions:
  - session 1: `2826343`, `btc-updown-15m-1783485900`, `2026-07-08T04:45:00+00:00` -> `2026-07-08T05:00:00+00:00`
  - session 2: `2827504`, `btc-updown-15m-1783486800`, `2026-07-08T05:00:00+00:00` -> `2026-07-08T05:15:00+00:00`
- Both sessions reached runner output.
- Final stop reason was `reached_max_sessions`.
- Resolution/result closing remained pending/missing by design for Phase 19.

multi-session proof：
```json
{"run_dir":"/private/tmp/polybot_phase19_multi_session_public_run","attempted_session_count":2,"processed_session_count":2,"final_stop_reason":"reached_max_sessions","sessions":[{"session":{"market_id":"2826343","market_slug":"btc-updown-15m-1783485900","market_start_time":"2026-07-08T04:45:00+00:00","market_end_time":"2026-07-08T05:00:00+00:00"},"status":"completed","runner_output":"/private/tmp/polybot_phase19_multi_session_public_run/_source/runner_1.jsonl"},{"session":{"market_id":"2827504","market_slug":"btc-updown-15m-1783486800","market_start_time":"2026-07-08T05:00:00+00:00","market_end_time":"2026-07-08T05:15:00+00:00"},"status":"completed","runner_output":"/private/tmp/polybot_phase19_multi_session_public_run/_source/runner_2.jsonl"}]}
```

session status / artifact proof：
```json
{"session_index":[{"session_key":"01_2826343","market_id":"2826343","market_start_time":"2026-07-08T04:45:00+00:00","runner_status":"finished","runner_output":"sessions/01_2826343/runner.jsonl","result_status":"skipped","skip_reason":"missing_resolution"},{"session_key":"02_2827504","market_id":"2827504","market_start_time":"2026-07-08T05:00:00+00:00","runner_status":"finished","runner_output":"sessions/02_2827504/runner.jsonl","result_status":"skipped","skip_reason":"missing_resolution"}]}
```

runner output proof：
```json
{"runner_1_signal":{"market_id":"2826343","now":"2026-07-08T04:56:00+00:00","remaining_seconds":240,"signal":"NO_SIGNAL","ret_pct":-0.03994193914767101}}
{"runner_2_signal":{"market_id":"2827504","now":"2026-07-08T05:11:00+00:00","remaining_seconds":240,"signal":"UP","ret_pct":0.06366241024483264},"runner_2_paper_result":{"record_type":"skipped_trade_record","skip_reason":"non_positive_trade_edge","executable_avg_ask":0.81,"trade_edge":-0.26}}
```

手工检查：
- `polybot/e2e_dry_run.py` still calls existing `discover_session(...)`, `enrich_session_config(...)`, `wait_to_entry(...)`, and `run_session_once(...)`.
- Multi-session cursor advances to the previous session start and processed market ids are tracked to avoid duplicate attempts.
- Per-session waits stay bounded by `--max-wait-to-open-seconds`, `--max-wait-to-entry-seconds`, and remaining `--max-runtime-seconds`.
- `dry_run_report.json` records per-session discovery/open/entry/runner status; `session_index.json` links both runner outputs under stable artifact paths.
- `polybot.signal`, `polybot.open_price`, `polybot.marketability`, `polybot.run_artifacts`, and `polybot.long_run` were not modified.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, final p_hat model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, historical price backfill, REST historical klines, reconstructed open price, validation loosening, signal change, marketability/fill change, open-price freshness change, resolution policy change, artifact schema rewrite, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- Phase 19 bounded two-session public proof is no longer blocked in this run.
- Automatic resolution/closing wiring, final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 18 Accepted And Phase 19 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 18, then prepare the next bounded multi-session public run step.
- Accepted slice:
  - Phase 18 entry-window full-session proof, including fresh open price, wait-to-entry, root `signal_record`, and paper marketability result.
- Planning note:
  - The next smallest useful step toward unattended operation is proving the same process can run more than one real BTC 15m session in sequence.
  - Phase 19 should extend the public dry-run path to honor `max_sessions > 1` with unique chronological sessions, per-session wait/open/entry/runner evidence, and stable artifacts.
  - Settlement may remain pending in Phase 19; automatic post-close resolution/closing can be a later phase if multi-session runtime is stable.
- Scope skipped:
  - No business code changed by planning.

### 2026-07-08 - Phase 18 Entry-Window Session Proof Execution

任务ID：
polybot-paper-phase-18-entry-window-session-proof

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `polybot/paper_runner.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added bounded `wait_to_entry` orchestration after fresh open-price capture.
- Entry timestamps are computed only from configured `entry_remain_seconds` against `market_end_time`; defaults remain `180,240`.
- `--move-threshold-pct` and `--entry-remain-seconds` are passed through to the runner/signal path.
- `polybot.signal` root strategy semantics were not changed.
- No open-price freshness, discovery validation, marketability/fill, result closing, resolution, artifact schema, long-run recovery, trading, wallet/signing, p_hat, DB, or OS service behavior was changed.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.signal`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m py_compile polybot/e2e_dry_run.py polybot/paper_runner.py`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|historical kline|historical price|backfill|reconstruct" polybot requirements.txt`
- Initial bounded dry-run attempt: `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 2400 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 8 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 1 --limit 10 --max-wait-to-open-seconds 1800 --max-wait-to-entry-seconds 900 --entry-window-tolerance-seconds 3 --max-open-price-delay-seconds 5 --run-dir /private/tmp/polybot_phase18_entry_window_dry_run`
- Follow-up nearer-session probe: `python3 -m polybot.market_discovery --search-query "bitcoin up down 15m" --mode next --max-pages 10 --limit 100 --lookahead-minutes 90 --output /private/tmp/polybot_phase18_nearer_discovery_probe.json`
- Successful bounded public proof: `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 1800 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 8 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 10 --limit 100 --lookahead-minutes 90 --max-wait-to-open-seconds 600 --max-wait-to-entry-seconds 900 --entry-window-tolerance-seconds 3 --max-open-price-delay-seconds 5 --run-dir /private/tmp/polybot_phase18_entry_window_nearer_dry_run`
- `python3 -m json.tool /private/tmp/polybot_phase18_entry_window_nearer_dry_run/dry_run_report.json`
- `nl -ba /private/tmp/polybot_phase18_entry_window_nearer_dry_run/_source/runner.jsonl`

结果：
- Touched self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Initial run with `--max-pages 1 --limit 10` could not find a near future session and recorded `session_discovery: skipped` / `no_valid_candidate`.
- A wider calibrated public-search probe found a nearer strict valid BTC 15m UP/DOWN future session:
  - `market_slug: btc-updown-15m-1783483200`
  - `market_start_time: 2026-07-08T04:00:00+00:00`
  - `market_end_time: 2026-07-08T04:15:00+00:00`
- The earlier long run targeting a later session was stopped after the nearer proof run was launched; it is not used as passing evidence.
- Successful proof run reached:
  - `session_discovery: success`
  - `wait_to_open: success`
  - `btc_reference_capture: success`
  - `open_price: captured`
  - `wait_to_entry: success`
  - `paper_runner: completed`

dry-run proof：
```json
{"run_dir":"/private/tmp/polybot_phase18_entry_window_nearer_dry_run","final_status":"stopped","steps":[{"source_timestamp":"Wed, 08 Jul 2026 03:57:59 GMT","status":"success","step":"discovery_fetch"},{"session":{"market_id":"2826127","market_slug":"btc-updown-15m-1783483200","market_start_time":"2026-07-08T04:00:00+00:00","market_end_time":"2026-07-08T04:15:00+00:00"},"status":"success","step":"session_discovery"},{"step":"wait_to_open","status":"success","session_start":"2026-07-08T04:00:00+00:00","local_timestamp":"2026-07-08T03:57:59.106508+00:00","wait_seconds":120.893492,"max_wait_seconds":600.0},{"step":"btc_reference_capture","status":"success","record_count":5},{"step":"open_price","status":"captured","open_price":62767.99,"open_price_timestamp":"2026-07-08T04:00:00.550000+00:00"},{"step":"wait_to_entry","status":"success","selected_entry_timestamp":"2026-07-08T04:11:00+00:00","selected_entry_remain_seconds":240,"candidate_entry_timestamps":["2026-07-08T04:11:00+00:00","2026-07-08T04:12:00+00:00"],"wait_seconds":649.346927,"max_wait_seconds":900.0,"wake_timestamp":"2026-07-08T04:11:00.016550+00:00","lateness_seconds":0.01655,"tolerance_seconds":3.0},{"step":"paper_runner","status":"completed","runner_output":"/private/tmp/polybot_phase18_entry_window_nearer_dry_run/_source/runner.jsonl"},{"step":"resolution_result","status":"pending","reason":"no_explicit_resolution_map_in_phase14_dry_run"}]}
```

runner output 证据：
```json
{"record_type":"signal_record","record":{"now":"2026-07-08T04:11:00+00:00","market_end_time":"2026-07-08T04:15:00+00:00","open_price":62767.99,"current_price":62812.0,"remaining_seconds":240,"ret_pct":0.07011535656949033,"signal":"UP"}}
{"record_type":"skipped_trade_record","record":{"signal":"UP","stake":9.0,"caller_supplied_p_hat":0.55,"executable_avg_ask":0.9,"trade_edge":-0.35,"skip_reason":"non_positive_trade_edge"}}
```

手工检查：
- `polybot/e2e_dry_run.py` waits only to exact configured entry timestamps derived from `market_end_time - entry_remain_seconds`.
- If wait budget is insufficient, it records `wait_to_entry_budget_exceeded`; if wake is late beyond tolerance, it records `entry_window_missed`.
- On success, the runner receives `now=selected_entry_timestamp`, `entry_remain_seconds`, and `move_threshold_pct`.
- The proof signal was `UP`, so the runner selected the UP token and recorded a paper skipped-trade reason after consuming real Polymarket book data.
- The proof used fresh post-start BTC records; no historical price, REST kline, backfill, reconstructed open price, or inferred price path was added.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, p_hat model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, historical price backfill, REST historical klines, reconstructed open price, validation loosening, signal change, marketability/fill change, open-price freshness change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- Phase 18 entry-window proof is no longer blocked in this run.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 17 Accepted And Phase 18 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 17, then prepare the next full-session paper dry-run proof.
- Accepted slice:
  - Phase 17 open-price window alignment, including next-session selection, bounded wait-to-open, and fresh WebSocket BTC open-price capture.
- Planning note:
  - The next blocker is no longer discovery or open price. The dry-run must now wait from open price capture to the configured tail entry timestamp, then run the existing paper runner at the root signal's configured remaining seconds.
  - Phase 18 should preserve `polybot.signal` root logic and make orchestration wait for the configured entry time instead of widening the signal rule.
  - A valid Phase 18 public proof may produce `NO_SIGNAL` if the configured move threshold is not met; that is not a failure. The minimum proof is a real tail-window `signal_record`, and if the signal is UP/DOWN, a real marketability/paper result or a precise market-data skip.
- Scope skipped:
  - No business code changed by planning.

### 2026-07-08 - Phase 17 Next-Session Selection Rework

任务ID：
polybot-paper-phase-17-open-price-window-alignment

改动文件：
- Updated `polybot/market_discovery.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Minimal acceptance rework only: fixed `--mode next` selection to choose the nearest future valid session within the lookahead window.
- `current` mode behavior is unchanged.
- If multiple valid sessions share the same nearest future start time, `ambiguous_candidates` can still protect selection.
- No open-price freshness rule, strategy rule, marketability/fill rule, result closing, resolution policy, artifact schema, long-run behavior, trading path, wallet/signing, p_hat, DB, or OS service behavior was changed.

运行命令：
- `python3 -m polybot.market_discovery --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m py_compile polybot/market_discovery.py`
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 1200 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 1 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 1 --limit 10 --max-wait-to-open-seconds 1200 --max-open-price-delay-seconds 5 --run-dir /private/tmp/polybot_phase17_acceptance_fix_next_dry_run`
- `python3 -m json.tool /private/tmp/polybot_phase17_acceptance_fix_next_dry_run/dry_run_report.json`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.open_price --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|historical kline|historical price|backfill|reconstruct" polybot requirements.txt`

结果：
- `--mode next` no longer returns `ambiguous_candidates` when multiple future BTC 15m sessions are in the lookahead window.
- Discovery self-check now covers the regression: two future valid sessions in `next` mode select the earlier `market-next`.
- The same bounded next-mode dry-run command reached the full Phase 17 success path:
  - `session_discovery: success`
  - `wait_to_open: success`
  - `btc_reference_capture: success`
  - `open_price: captured`
- Captured open price came from a post-start WebSocket BTC record:
  - market start: `2026-07-08T03:00:00+00:00`
  - open price timestamp: `2026-07-08T03:00:01.068000+00:00`
  - max freshness: `5` seconds
  - open price: `62991.83`
- Touched self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.

dry-run proof：
```json
{"run_dir":"/private/tmp/polybot_phase17_acceptance_fix_next_dry_run","final_status":"stopped","steps":[{"source_timestamp":"Wed, 08 Jul 2026 02:57:58 GMT","status":"success","step":"discovery_fetch"},{"session":{"market_id":"2825252","market_slug":"btc-updown-15m-1783479600","market_start_time":"2026-07-08T03:00:00+00:00","market_end_time":"2026-07-08T03:15:00+00:00"},"status":"success","step":"session_discovery"},{"step":"wait_to_open","status":"success","session_start":"2026-07-08T03:00:00+00:00","local_timestamp":"2026-07-08T02:57:58.168621+00:00","wait_seconds":121.831379,"max_wait_seconds":1200.0},{"step":"btc_reference_capture","status":"success","record_count":5},{"step":"open_price","status":"captured","open_price":62991.83,"open_price_timestamp":"2026-07-08T03:00:01.068000+00:00"},{"step":"paper_runner","status":"completed","runner_output":"/private/tmp/polybot_phase17_acceptance_fix_next_dry_run/_source/runner.jsonl"},{"step":"resolution_result","status":"pending","reason":"no_explicit_resolution_map_in_phase14_dry_run"}]}
```

手工检查：
- `polybot/market_discovery.py` still routes all candidates through existing strict `validate_candidate(...)`.
- The next-mode change only narrows future valid candidates to the nearest future start; it does not accept invalid, stale, non-BTC, non-15m, or unclear UP/DOWN markets.
- `polybot/e2e_dry_run.py` wait/open-price behavior from Phase 17 was not weakened.
- No historical BTC price, REST kline, backfill, or reconstructed open price path was added.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, historical price backfill, REST historical klines, reconstructed open price, validation loosening, signal change, marketability/fill change, open-price freshness change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- Phase 17 next-session selection and open-price alignment are no longer blocked in this live proof.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Current Task File Workflow Adopted

- Goal: Reduce token waste from the growing historical task-card archive.
- Decision:
  - `docs/project_notes/current_task.md` is now the active task surface and should be overwritten for each new task.
  - `docs/project_notes/polymarket_paper_execution_tasks.md` is retained as historical reference only and should not receive new detailed task cards by default.
  - `issues.md` keeps concise task summaries, changed-file summaries, evidence, blockers, and acceptance outcomes instead of full prompts.
- Updated docs:
  - `AGENTS.md`
  - `docs/project_notes/zone_operating_model.md`
  - `docs/project_notes/key_facts.md`
  - `docs/project_notes/decisions.md`
  - `docs/project_notes/polymarket_paper_execution_tasks.md`
  - `docs/project_notes/current_task.md`
- Scope skipped:
  - No business code changed.

### 2026-07-08 - Phase 17 Open-Price Window Alignment Execution

任务ID：
polybot-paper-phase-17-open-price-window-alignment

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added bounded wait-to-open behavior only in the dry-run orchestration layer.
- Dry-run now records `wait_to_open`, `btc_reference_capture`, and `open_price` steps after `session_discovery`.
- Wait is bounded by explicit `--max-wait-to-open-seconds`; no unbounded sleep or daemon behavior.
- Existing `open_price.py` freshness semantics were not changed: pre-start, stale, historical, reconstructed, or backfilled prices are still rejected.
- Existing calibrated source `--search-query "bitcoin up down 15m"` and strict BTC 15m discovery validation are preserved.
- Strategy signal, marketability/fill, result closing, resolution, artifact schema, long-run recovery, and trading boundaries were not changed.

运行命令：
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m py_compile polybot/e2e_dry_run.py`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 1200 --paper-stake 9 --p-hat 0.55 --capture-seconds 8 --capture-limit 5 --runner-seconds 1 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --mode next --max-pages 1 --limit 10 --max-wait-to-open-seconds 1200 --max-open-price-delay-seconds 5 --run-dir /private/tmp/polybot_phase17_next_open_dry_run`
- `python3 -m json.tool /private/tmp/polybot_phase17_next_open_dry_run/dry_run_report.json`
- `python3 -m json.tool /private/tmp/polybot_phase17_next_open_dry_run/session_index.json`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.long_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy|historical kline|historical price|backfill|reconstruct" polybot requirements.txt`

结果：
- `polybot.e2e_dry_run` self-check passed and now includes a minimal `wait_to_open_budget_exceeded` assertion.
- `polybot.open_price` self-check passed; no open-price freshness rule was modified.
- Bounded public dry-run used the required calibrated source and next-session mode:
  - `--search-query "bitcoin up down 15m"`
  - `--mode next`
  - `--max-wait-to-open-seconds 1200`
- Dry-run selected the next BTC 15m session:
  - `market_id: 2825296`
  - `market_slug: btc-updown-15m-1783480500`
  - `market_start_time: 2026-07-08T03:15:00+00:00`
  - `market_end_time: 2026-07-08T03:30:00+00:00`
- Operational blocker was precise:
  - selected session required `1599.3807` seconds of waiting
  - configured wait budget was `1200` seconds
  - dry-run recorded `wait_to_open_budget_exceeded`
- Because wait budget was exceeded, BTC WebSocket capture and open-price capture were explicitly skipped; no historical/backfilled price was used.
- Phase 1-16 self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Ponytail review result: Lean already. Ship.

dry-run proof：
```json
{"run_dir":"/private/tmp/polybot_phase17_next_open_dry_run","final_status":"stopped","steps":[{"source_timestamp":"Wed, 08 Jul 2026 02:48:20 GMT","status":"success","step":"discovery_fetch"},{"session":{"market_id":"2825296","market_slug":"btc-updown-15m-1783480500","market_start_time":"2026-07-08T03:15:00+00:00","market_end_time":"2026-07-08T03:30:00+00:00"},"status":"success","step":"session_discovery"},{"step":"wait_to_open","status":"skipped","reason":"wait_to_open_budget_exceeded","session_start":"2026-07-08T03:15:00+00:00","local_timestamp":"2026-07-08T02:48:20.619300+00:00","wait_seconds":1599.3807,"max_wait_seconds":1200.0},{"step":"btc_reference_capture","status":"skipped","reason":"not_reached_after_wait_to_open_budget_exceeded"},{"step":"open_price","status":"skipped","reason":"not_reached_after_wait_to_open_budget_exceeded"}]}
```

session index proof：
```json
{"schema_version":"phase12_run_artifacts_v1","sessions":[{"session_key":"01_2825296","market_id":"2825296","market_slug":"btc-updown-15m-1783480500","market_start_time":"2026-07-08T03:15:00+00:00","market_end_time":"2026-07-08T03:30:00+00:00","runner_status":"skipped","result_status":"skipped","skip_reason":"wait_to_open_budget_exceeded"}]}
```

手工检查：
- `polybot/e2e_dry_run.py` uses `asyncio.sleep(...)` only after discovery selects a future session and only if the required wait is within `--max-wait-to-open-seconds`.
- If wait budget is exceeded, it records `wait_to_open`, `btc_reference_capture`, and `open_price` skip evidence and stops before BTC capture.
- If waiting succeeds or no wait is needed, BTC capture still uses existing `capture_btc_reference(...)`; open price still uses existing `enrich_session_config(...)`.
- No historical BTC price path, REST kline path, backfill path, or inferred open price path was added.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, historical price backfill, REST historical klines, reconstructed open price, validation loosening, signal change, marketability/fill change, open-price freshness change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- This run did not capture open price because the selected next market opened outside the explicit 1200-second wait budget.
- Minimal next operational attempt: rerun the same command closer to the next 15m boundary, or deliberately allow a larger bounded wait budget such as 1800 seconds. Do not use historical/backfilled prices.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 16 Accepted And Phase 17 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 16, then prepare the next targeted dry-run reliability step.
- Accepted slice:
  - Phase 16 BTC 15m public source calibration.
- Planning note:
  - Public discovery is no longer the main blocker. The calibrated source path is `--search-query "bitcoin up down 15m"`.
  - Phase 16 dry-run reached `session_discovery: success`, then hit BTC reference/open-price timing: `btc_reference_capture` timeout and `open_price: no_post_start_record`.
  - Phase 17 should align dry-run execution to the next market open before BTC reference capture. It must not reconstruct open price after the fact, relax open-price freshness, change strategy, or add a deployment service.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-08 - Phase 16 BTC 15m Source Calibration Execution

任务ID：
polybot-paper-phase-16-btc-15m-source-calibration

改动文件：
- Updated `polybot/market_discovery.py`
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Calibrated a public source path for current BTC 15m Up/Down discovery.
- Added minimal `public-search` source support via `--search-query`, because a stable rolling source cannot be expressed by the current-session slug alone.
- Added normalization for `public-search` payloads shaped as `{"events": [...]}`.
- Added `eventStartTime` as the preferred market start timestamp for Gamma BTC 15m payloads; this preserves the strict exact-15-minute validation and avoids using Gamma `startDate`, which is not the market interval start for this source.
- Reused existing strict `validate_candidate(...)`; BTC/Bitcoin identity, exact 15-minute duration, active/open status, UP/DOWN token mapping, and market id checks were not relaxed.
- Phase 14 dry-run CLI can now pass `--search-query` to the same discovery path.

运行命令：
- `python3 -m polybot.market_discovery --source-kind both --max-pages 20 --limit 100 --lookahead-minutes 30 --mode current --output /private/tmp/polybot_phase16_broad_discovery.json`
- `python3 -c '... public-search q="bitcoin up down 15m" ...'`
- `python3 -m polybot.market_discovery --source-kind events --slug btc-updown-15m-1783476900 --max-pages 1 --limit 10 --lookahead-minutes 30 --mode current --output /private/tmp/polybot_phase16_slug_discovery_after_fix.json`
- `python3 -m polybot.market_discovery --search-query "bitcoin up down 15m" --max-pages 1 --limit 10 --lookahead-minutes 30 --mode current --output /private/tmp/polybot_phase16_search_discovery_after_fix.json`
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 20 --paper-stake 9 --p-hat 0.55 --capture-seconds 1 --runner-seconds 1 --heartbeat-interval-seconds 0 --retry-limit 0 --search-query "bitcoin up down 15m" --max-pages 1 --limit 10 --run-dir /private/tmp/polybot_phase16_search_dry_run`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.long_run --self-check`
- `python3 -m polybot.e2e_dry_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" polybot requirements.txt`

结果：
- Broad events/markets pagination still returned `no_valid_candidate`:
  - `events_count: 2000`
  - `markets_count: 2000`
  - `validation_skip_reasons: {"missing_start_or_end_time": 6, "not_15m": 128, "not_btc": 22288}`
- Public source calibration found a stable documented search path:
  - `https://gamma-api.polymarket.com/public-search?q=bitcoin+up+down+15m&events_status=active&limit_per_type=10&page=1&keep_closed_markets=0`
- Search result produced the current BTC 15m slug:
  - `btc-updown-15m-1783476900`
- Strict discovery selected a valid session from the calibrated search source:
  - `market_id: 2825018`
  - `market_slug: btc-updown-15m-1783476900`
  - `market_start_time: 2026-07-08T02:15:00+00:00`
  - `market_end_time: 2026-07-08T02:30:00+00:00`
  - `selected_side_labels: {"UP": "Up", "DOWN": "Down"}`
- Bounded Phase 14 dry-run using `--search-query "bitcoin up down 15m"` reached `session_discovery: success`.
- Dry-run then recorded `btc_reference_capture` timeout and `open_price: no_post_start_record`; that is downstream public-data timing/network evidence, not a discovery failure.
- Phase 1-15 self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Ponytail review result: Lean already. Ship.

source calibration evidence：
```json
{"sources_tried":[{"kind":"search","count":10,"url":"https://gamma-api.polymarket.com/public-search?q=bitcoin+up+down+15m&events_status=active&limit_per_type=10&page=1&keep_closed_markets=0"}],"source_timestamps":["Wed, 08 Jul 2026 02:25:08 GMT"],"selection":{"market_id":"2825018","market_slug":"btc-updown-15m-1783476900","market_start_time":"2026-07-08T02:15:00+00:00","market_end_time":"2026-07-08T02:30:00+00:00","selected_side_labels":{"UP":"Up","DOWN":"Down"}},"validation_skip_reasons":{"valid_but_outside_current_window":9},"top_candidate_snapshots":[{"question":"Bitcoin Up or Down - July 7, 10:15PM-10:30PM ET","market_slug":"btc-updown-15m-1783476900","event_slug":"btc-updown-15m-1783476900","start":"2026-07-08T02:15:00+00:00","end":"2026-07-08T02:30:00+00:00","has_up_down_mapping":true,"reason":"candidate_in_window"}]}
```

dry-run/discovery proof：
```json
{"run_dir":"/private/tmp/polybot_phase16_search_dry_run","final_status":"stopped","blockers":[],"steps":[{"source_timestamp":"Wed, 08 Jul 2026 02:25:20 GMT","status":"success","step":"discovery_fetch"},{"session":{"market_id":"2825018","market_slug":"btc-updown-15m-1783476900","market_start_time":"2026-07-08T02:15:00+00:00","market_end_time":"2026-07-08T02:30:00+00:00"},"status":"success","step":"session_discovery"},{"reason":"TimeoutError: ","status":"blocker","step":"btc_reference_capture"},{"reason":"no_post_start_record","status":"skipped","step":"open_price"}]}
```

手工检查：
- `polybot/market_discovery.py` still routes all candidates through `validate_candidate(...)`.
- The only timestamp compatibility change is preferring `eventStartTime` for market interval start when present; exact `end - start == 15 minutes` remains required.
- `public-search` support uses public GET via Python standard library `urllib`; no SDK, dependency, wallet, signing, credential, or order path was added.
- `polybot/e2e_dry_run.py` only exposes `--search-query` and continues to use existing discovery and dry-run orchestration.
- Official docs checked:
  - Fetching Markets documents slug, tags, events, and pagination.
  - Search API documents `GET /public-search`.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, validation loosening, signal change, marketability/fill change, open-price rule change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- Discovery source calibration is no longer blocked: use `--search-query "bitcoin up down 15m"` as the stable public source path for current BTC 15m sessions.
- Next downstream blocker is BTC reference capture/open-price timing in the bounded dry-run; this is not a Phase 16 source-calibration blocker.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 15 Accepted And Phase 16 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 15, then prepare the next targeted public-discovery step.
- Accepted slice:
  - Phase 15 public BTC 15m discovery hardening.
- Planning note:
  - Phase 15 improved source coverage and diagnostics, but the live smoke still returned `no_valid_candidate` under strict validation after documented events/markets pagination.
  - Phase 16 should identify and prove the correct public source for current BTC 15m Up/Down markets: known slug, tag, source URL, or documented filter combination.
  - Phase 16 must not relax BTC/15m/UP-DOWN validation or invent a market; it should produce either a valid discovered session or a precise source-calibration blocker.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-08 - Phase 15 Discovery Blocker Reporting Rework

任务ID：
polybot-paper-phase-15-public-btc-15m-discovery-hardening

改动文件：
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Minimal acceptance rework only: restored Phase 14 dry-run blocker recording semantics for Phase 15 public discovery failures.
- Public fetch/selection through `discover_session(...)` is now inside the dry-run `try/except` path.
- No discovery validation rule was loosened.
- No signal, marketability/fill, open-price, resolution, artifact, long-run, or trading semantics were changed.

运行命令：
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 20 --paper-stake 9 --p-hat 0.55 --capture-seconds 1 --runner-seconds 1 --heartbeat-interval-seconds 0 --retry-limit 0 --source-kind both --max-pages 2 --limit 50 --run-dir /private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix`
- `python3 -m json.tool /private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix/dry_run_report.json`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" polybot requirements.txt`

结果：
- The exact no-network acceptance scenario no longer raises a traceback.
- The dry run exits 0 and writes:
  - `/private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix/dry_run_report.json`
  - `/private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix/run_manifest.json`
  - `/private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix/session_index.json`
  - `/private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix/summary.json`
- `dry_run_report.json` records `final_status: blocked` and a precise `discovery_fetch` blocker.
- Downstream `open_price`, `signal`, `paper_runner`, and `result_closing` are explicitly skipped; `resolution` is pending.
- `polybot.e2e_dry_run` self-check passed.
- `polybot.market_discovery` self-check passed.
- Compile check passed.
- Forbidden-path search returned no matches.

blocker report 样例：
```json
{"blockers":["public_discovery_blocked=URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>"],"final_status":"blocked","run_dir":"/private/tmp/polybot_phase15_acceptance_dry_run_blocker_fix","steps":[{"reason":"public_discovery_blocked=URLError: <urlopen error [Errno 8] nodename nor servname provided, or not known>","status":"blocker","step":"discovery_fetch"},{"reason":"not_reached_after_discovery_fetch_blocker","status":"skipped","step":"open_price"},{"reason":"not_reached_after_discovery_fetch_blocker","status":"skipped","step":"signal"},{"reason":"not_reached_after_discovery_fetch_blocker","status":"skipped","step":"paper_runner"},{"reason":"not_reached_after_discovery_fetch_blocker","status":"skipped","step":"result_closing"},{"reason":"not_reached_after_discovery_fetch_blocker","status":"pending","step":"resolution"}]}
```

手工检查：
- `polybot/e2e_dry_run.py` now records `discovery_fetch` success only after `discover_session(...)` completes.
- If `discover_session(...)` raises network/API errors, the same blocked-report path writes artifacts and `dry_run_report.json`.
- The existing success/no-candidate diagnostics path remains unchanged.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, validation loosening, signal change, marketability/fill change, open-price rule change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- None for this blocker-reporting rework.

### 2026-07-08 - Phase 15 Public BTC 15m Discovery Hardening Execution

任务ID：
polybot-paper-phase-15-public-btc-15m-discovery-hardening

改动文件：
- Updated `polybot/market_discovery.py`
- Updated `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Hardened public discovery only; no strategy, signal, fill, open-price, resolution, artifact, long-run, or trading semantics were changed.
- `validate_candidate(...)` remains strict for BTC/Bitcoin identity, exact 15-minute duration, active/open status, and clear UP/DOWN token mapping.
- Added public discovery coverage for:
  - events endpoint pagination
  - markets endpoint pagination
  - optional `tag_id` with `related_tags=true`
  - optional `slug`
  - explicit `source_url`
- Added bounded pagination with `--max-pages`; no unbounded fetch loop.
- Added discovery diagnostics and wired Phase 14 dry-run to include those diagnostics in `session_discovery.details`.

运行命令：
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.market_discovery --source-kind both --max-pages 2 --limit 50 --lookahead-minutes 30 --mode current --output /private/tmp/polybot_phase15_discovery_smoke.json`
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 20 --paper-stake 9 --p-hat 0.55 --capture-seconds 1 --runner-seconds 1 --heartbeat-interval-seconds 0 --retry-limit 0 --source-kind both --max-pages 2 --limit 50 --run-dir /private/tmp/polybot_phase15_public_dry_run_smoke`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.long_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" polybot requirements.txt`

结果：
- Phase 15 discovery self-check passed.
- Self-check now covers:
  - valid BTC 15m session from nested events payload
  - valid BTC 15m session from flat markets payload
  - pagination merge within configured bound
  - ambiguous candidates remain `ambiguous_candidates`
  - no-candidate result includes diagnostics with validation skip reasons and candidate snapshots
- Phase 14 dry-run self-check still passed.
- Public discovery smoke reached Polymarket public Gamma endpoints with network approval.
- Public smoke did not find a valid current BTC 15m session under strict validation, but now records precise live diagnostics instead of only `no_valid_candidate`.
- Phase 1-14 self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.

discovery diagnostics 样例：
```json
{"skip_reason":"no_valid_candidate","candidate_count":0,"diagnostics":{"pages_fetched":4,"offsets":[0,50,0,50],"events_count":100,"markets_count":100,"source_timestamps":["Wed, 08 Jul 2026 01:52:28 GMT","Wed, 08 Jul 2026 01:52:28 GMT","Wed, 08 Jul 2026 01:52:29 GMT","Wed, 08 Jul 2026 01:52:29 GMT"],"validation_skip_reasons":{"not_15m":10,"not_btc":1318},"final_skip_reason":"no_valid_candidate","sources_tried":[{"kind":"events","count":50,"url":"https://gamma-api.polymarket.com/events?active=true&closed=false&limit=50&offset=0"},{"kind":"events","count":50,"url":"https://gamma-api.polymarket.com/events?active=true&closed=false&limit=50&offset=50"},{"kind":"markets","count":50,"url":"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&offset=0"},{"kind":"markets","count":50,"url":"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=50&offset=50"}],"top_candidate_snapshots":[{"question":"Kraken IPO in 2025?","market_slug":"kraken-ipo-in-2025","event_slug":"kraken-ipo-in-2025","start":null,"end":null,"has_up_down_mapping":false,"reason":"not_btc"}]}}
```

public dry-run/discovery smoke 摘要：
```json
{"run_dir":"/private/tmp/polybot_phase15_public_dry_run_smoke","final_status":"stopped","blockers":[],"session_discovery":{"status":"skipped","reason":"no_valid_candidate","diagnostics":{"pages_fetched":4,"offsets":[0,50,0,50],"validation_skip_reasons":{"not_15m":10,"not_btc":1318},"final_skip_reason":"no_valid_candidate"}}}
```

手工检查：
- `polybot/market_discovery.py` still has the strict `validate_candidate(...)` checks for BTC/Bitcoin, exact 15 minutes, active/open, UP/DOWN token mapping, and market id.
- Phase 15 source hardening uses public GET only with Python standard library `urllib`; no SDK or dependency was added.
- `polybot/e2e_dry_run.py` now calls `discover_session(...)` for public discovery and records its diagnostics under `session_discovery.details`.
- Official docs checked: Polymarket documents slug, tag, events discovery; `events` and `markets` list endpoints use `limit`/`offset` pagination, and `markets` supports `tag_id` / `related_tags`.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, validation loosening, signal change, marketability/fill change, open-price rule change, resolution policy change, artifact schema change, long-run semantic change, or new strategy rule.

阻塞/待规划决定：
- Current public smoke still returns `no_valid_candidate` under strict validation after 4 pages across documented events and markets sources. Next planning decision, if needed, is whether to provide a known Polymarket BTC tag/slug/source URL or broaden documented source filters further without loosening validation.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-08 - Phase 14 Accepted And Phase 15 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 14, then prepare the targeted fix for the live dry-run blocker.
- Accepted slice:
  - Phase 14 public-data end-to-end dry run.
- Planning note:
  - Phase 14 proved the public dry-run wrapper and artifact path, but the live fetch did not find a valid current BTC 15m market from the first `events?active=true&closed=false&limit=100` source.
  - Phase 15 should harden public discovery by using documented public events/markets endpoints, pagination, optional tag/slug/source-url inputs, and richer diagnostics.
  - Phase 15 must preserve existing validation rules; it should not relax BTC/15m/UP-DOWN/token/open checks just to force a session.
- Source note:
  - Polymarket docs describe three market-fetching strategies: slug, tags, and events; they also document pagination and both events/markets endpoints.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 14 Public Data E2E Dry Run Execution

任务ID：
polybot-paper-phase-14-public-data-e2e-dry-run

改动文件：
- Added `polybot/e2e_dry_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a bounded public-data dry-run wrapper around existing Phase 1-13 modules and artifacts.
- Dry run writes a Phase 12/13-style local run directory with:
  - `run_manifest.json`
  - `session_index.json`
  - `summary.json`
  - `status.json`
  - `heartbeat.jsonl`
  - `supervisor.jsonl`
  - `dry_run_report.json`
- Public discovery uses the Gamma public events endpoint and existing session validation.
- Public BTC capture is attempted only after a valid session is discovered.
- If public data/API/timing prevents a full paper run, the wrapper records explicit skip/blocker evidence instead of changing strategy rules or guessing settlement.
- Existing signal, marketability/fill, result closer, resolution ingestion, run artifact schema, and long-run resume/retry semantics were not changed.

运行命令：
- `python3 -m polybot.e2e_dry_run --self-check`
- `python3 -m polybot.e2e_dry_run --max-sessions 1 --max-runtime-seconds 20 --paper-stake 9 --p-hat 0.55 --capture-seconds 3 --runner-seconds 3 --heartbeat-interval-seconds 0 --retry-limit 0 --run-dir /private/tmp/polybot_phase14_public_dry_run_final`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.long_run --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" polybot requirements.txt`

结果：
- Phase 14 self-check passed.
- Public-data dry-run command actually ran against:
  - `https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100`
- Initial sandboxed public fetch hit DNS/network restriction; rerun with approved network access reached the public endpoint.
- First approved public fetch with plain urllib returned `HTTP 403`; the wrapper now sends a minimal `User-Agent` for this dry-run GET only.
- Re-run after acceptance feedback wrote:
  - `/private/tmp/polybot_phase14_public_dry_run_rerun`
- Public discovery fetch succeeded with source timestamp:
  - `Wed, 08 Jul 2026 01:42:23 GMT`
- No valid current BTC 15m session was discovered from the returned public events payload:
  - `skip_reason: no_valid_candidate`
  - `validation_skip_reasons: {"not_15m": 9, "not_btc": 1219}`
- Because no valid session was discovered, the report now explicitly records downstream `open_price`, `signal`, `paper_runner`, `result_closing`, and `resolution` outcomes as skipped or pending after discovery skip; no winner was guessed.
- Phase 1-13 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`.
- Forbidden-path search returned no matches.

dry-run report 摘要：
```json
{"blockers": [], "config": {"caller_supplied_p_hat": 0.55, "capture_seconds": 3.0, "entry_remain_seconds": "180,240", "lookahead_minutes": 30, "max_runtime_seconds": 20.0, "max_sessions": 1, "move_threshold_pct": 0.05, "paper_stake": 9.0}, "final_status": "stopped", "public_data_source": "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100", "run_dir": "/private/tmp/polybot_phase14_public_dry_run_rerun", "steps": [{"source_timestamp": "Wed, 08 Jul 2026 01:42:23 GMT", "status": "success", "step": "discovery_fetch"}, {"details": {"candidate_count": 0, "local_timestamp": "2026-07-08T01:42:23.716346+00:00", "selection": null, "skip_reason": "no_valid_candidate", "validation_skip_reasons": {"not_15m": 9, "not_btc": 1219}}, "reason": "no_valid_candidate", "status": "skipped", "step": "session_discovery"}, {"reason": "not_reached_after_session_discovery_skip", "status": "skipped", "step": "open_price"}, {"reason": "not_reached_after_session_discovery_skip", "status": "skipped", "step": "signal"}, {"reason": "not_reached_after_session_discovery_skip", "status": "skipped", "step": "paper_runner"}, {"reason": "not_reached_after_session_discovery_skip", "status": "skipped", "step": "result_closing"}, {"reason": "not_reached_after_session_discovery_skip", "status": "pending", "step": "resolution"}]}
```

run directory 样例：
```text
/private/tmp/polybot_phase14_public_dry_run_rerun/run_manifest.json
/private/tmp/polybot_phase14_public_dry_run_rerun/session_index.json
/private/tmp/polybot_phase14_public_dry_run_rerun/status.json
/private/tmp/polybot_phase14_public_dry_run_rerun/heartbeat.jsonl
/private/tmp/polybot_phase14_public_dry_run_rerun/summary.json
/private/tmp/polybot_phase14_public_dry_run_rerun/supervisor.jsonl
/private/tmp/polybot_phase14_public_dry_run_rerun/dry_run_report.json
```

观察到的真实数据/skip/blocker：
```json
{"schema_version": "phase12_run_artifacts_v1", "sessions": [{"market_end_time": null, "market_id": "public-session-discovery", "market_slug": null, "market_start_time": null, "paper_pnl": null, "resolution_path": null, "resolution_raw_path": null, "resolution_status": "missing", "result_path": null, "result_status": "skipped", "runner_output": null, "runner_status": "skipped", "session_key": "01_public-session-discovery", "skip_reason": "no_valid_candidate"}]}
{"processed_sessions": 0, "status": "running", "timestamp": "2026-07-08T01:42:23.719118+00:00"}
{"reason": "already_closed_or_skipped", "session_key": "01_public-session-discovery", "status": "resume_skipped", "timestamp": "2026-07-08T01:42:23.719234+00:00"}
{"last_session": null, "processed_sessions": 0, "status": "stopped", "timestamp": "2026-07-08T01:42:23.719782+00:00"}
```

手工检查：
- `polybot/e2e_dry_run.py` uses public GET discovery, existing `select_session`, existing open-price enrichment, existing paper runner, existing batch closer, existing run artifacts, and existing long-run status helper.
- Dry-run output is JSON/JSONL only.
- No strategy threshold, signal timing, marketability/fill, result closer, resolution policy, artifact schema, or long-run resume/retry semantic was changed.
- The final dry-run outcome is a real public-data skip, not a fixture success and not a silent failure.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, guessed winner, settlement-policy change, or new strategy rule.

阻塞/待规划决定：
- Current public events fetch returned no valid current BTC 15m market under existing validated discovery rules. Later planning can decide whether to adjust public discovery source/filter/tag strategy, but Phase 14 did not change discovery rules to force a pass.
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-07 - Phase 13 Accepted And Phase 14 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 13, then prepare a real public-data end-to-end dry run.
- Accepted slice:
  - Phase 13 resumable long-run paper supervisor.
- Planning note:
  - Phase 14 should run the paper robot end to end against public data for a bounded dry run and produce a readable Phase 12/13 run directory.
  - The dry run should exercise discovery, open-price capture, paper runner, marketability/paper fill or explicit skip, conservative resolution ingestion when available, batch result closing, artifact indexing, heartbeat/status, and resume inspection.
  - Phase 14 must not add live trading, wallet/signing, final `p_hat` modeling, database storage, OS-level service installation, or new strategy rules.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 13 Resumable Long-Run Supervisor Execution

任务ID：
polybot-paper-phase-13-resumable-long-run-supervisor

改动文件：
- Added `polybot/long_run.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a process-local long-run helper around Phase 12 run artifacts.
- Uses `run_manifest.json` and `session_index.json` as recovery state.
- Writes local JSON/JSONL status files:
  - `status.json`
  - `heartbeat.jsonl`
- Supports `--resume`, `--max-sessions`, `--max-runtime-seconds`, `--end-time`, `--continuous`, `--heartbeat-interval-seconds`, `--retry-limit`, `--retry-backoff-seconds`, `--stop-after-sessions`, and local `--session-plan-json`.
- Resume skips sessions already marked `closed` or `skipped`; it does not duplicate them in `session_index.json`.
- Recoverable errors are recorded in heartbeat JSONL and retried up to the configured limit.
- Retry exhaustion records a skipped session with `skip_reason: retry_limit_reached`.
- Graceful test stop marks manifest/status as `interrupted`; normal completion marks them `stopped`.
- Existing Phase 1 signal, Phase 3 marketability/fill, Phase 5 closer, Phase 11 resolution ingestion, and Phase 12 artifact schema semantics were not changed.

运行命令：
- `python3 -m polybot.long_run --self-check`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.run_artifacts --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|launchd|systemd|crontab|service install|OS restart policy|machine restart policy" polybot requirements.txt`

结果：
- Phase 13 self-check passed and wrote sample run directory:
  - `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase13_long_run_0viq2e4t/run`
- Self-check covers:
  - initial run writes heartbeat/status and records two sessions
  - simulated interruption marks run as `interrupted`
  - resume reads the same run directory and records `resume_skipped` for already closed/skipped sessions
  - recoverable error is recorded and succeeds on retry for `03_market-retry`
  - retry exhaustion records `04_market-fail` as skipped with `retry_limit_reached`
  - final manifest/status remain readable and are marked `stopped`
- Existing Phase 1-12 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`.
- Forbidden-path search returned no matches.

heartbeat/status 样例：
```json
{"last_error": "RecoverableRunError: simulated_runner_error", "last_session": "04_market-fail", "processed_sessions": 2, "schema_version": "phase13_long_run_v1", "status": "stopped", "updated_at": "2026-07-07T15:39:23.669057+00:00"}
{"reason": "already_closed_or_skipped", "session_key": "01_market-current", "status": "resume_skipped", "timestamp": "2026-07-07T15:39:23.667753+00:00"}
{"attempt": 1, "error": "RecoverableRunError: simulated_open_price_timeout", "session_key": "03_market-retry", "status": "recoverable_error", "timestamp": "2026-07-07T15:39:23.667939+00:00"}
{"error": "RecoverableRunError: simulated_runner_error", "session_key": "04_market-fail", "status": "retry_limit_reached", "timestamp": "2026-07-07T15:39:23.668690+00:00"}
```

resume/stop 样例：
```json
{"created_at": "2026-07-07T15:39:23.661988+00:00", "heartbeat_jsonl": "heartbeat.jsonl", "last_error": "RecoverableRunError: simulated_runner_error", "last_session": "04_market-fail", "processed_sessions": 2, "schema_version": "phase12_run_artifacts_v1", "status": "stopped", "status_json": "status.json", "updated_at": "2026-07-07T15:39:23.669220+00:00"}
{"schema_version": "phase12_run_artifacts_v1", "sessions": [{"session_key": "01_market-current", "result_status": "closed"}, {"session_key": "02_market-next", "result_status": "skipped"}, {"session_key": "03_market-retry", "result_status": "closed"}, {"session_key": "04_market-fail", "result_status": "skipped", "skip_reason": "retry_limit_reached"}]}
```

手工检查：
- `polybot/long_run.py` only reads/writes Phase 12 artifact files and local status/heartbeat files.
- It does not call live order, wallet, signing, credential, database, service manager, or OS restart paths.
- Retry/backoff is bounded by `retry_limit`; retry exhaustion becomes an explicit skipped session.
- Resume uses `result_status in ("closed", "skipped")` from `session_index.json` to avoid duplicate processing.
- Existing supervisor, result closer, resolution ingestion, signal, marketability, paper fill, and run artifact semantics were not modified.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model/training/backfill, database, SQLite, ORM, long-term DB schema, launchd/systemd/crontab, service install, OS-level process supervision, machine restart policy, or new strategy rule.

阻塞/待规划决定：
- Final `p_hat` modeling, real deployment service manager, OS-level restart policy, and any database/storage backend remain later planning decisions.

### 2026-07-07 - Phase 12 Accepted And Phase 13 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 12, then prepare the long-run reliability slice.
- Accepted slice:
  - Phase 12 stable run artifacts and local index.
- Planning note:
  - Phase 13 should make paper runs resumable and safer for long-running operation using Phase 12 run artifacts.
  - The next slice should add process-local recovery behavior: resume from an existing run directory, heartbeat/status updates, recoverable-error logging, bounded retry/backoff, and graceful stop.
  - Phase 13 must not add live trading, wallet/signing, final `p_hat` modeling, a database, or OS-level process supervision such as launchd/systemd/crontab.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 12 Stable Run Artifacts Execution

任务ID：
polybot-paper-phase-12-stable-run-artifacts

改动文件：
- Added `polybot/run_artifacts.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a local JSON/JSONL run-artifact helper around existing Phase 9-11 outputs.
- Stable run directory layout:
  - `run_manifest.json`
  - `session_index.json`
  - `supervisor.jsonl`
  - `sessions/<session_key>/runner.jsonl`
  - `sessions/<session_key>/resolution.json`
  - `sessions/<session_key>/resolution_raw.json`
  - `sessions/<session_key>/result.json`
  - `summary.json`
- Paths written into manifest, session index, and compact summary are relative to the run directory.
- `summary.json` is compact and readable without scanning raw runner JSONL; per-session detail is linked from `session_index.json`.
- Skipped sessions remain in `session_index.json` with `skip_reason`.
- Existing Phase 9 supervisor, Phase 10 batch closer, and Phase 11 resolution ingestion semantics were not changed.

运行命令：
- `python3 -m polybot.run_artifacts --self-check`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.resolution_ingestion --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|uma_proposal|uma_dispute|uma_vote|uma_redeem|proposal action|dispute action|vote action|redeem action|redeem\\(|p_hat training|sqlite|SQLite|sqlalchemy|ORM|database schema|restart policy|launchd|systemd|crontab|daemon" polybot requirements.txt`

结果：
- Phase 12 self-check passed and wrote sample run directory:
  - `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase12_run_artifacts_ouy32ic8/run`
- Self-check created a two-session sample run:
  - one closed session with runner, resolution, raw resolution metadata, result, and `paper_pnl`
  - one skipped session with `stale_open_price_record`
- `summary.json` can be read directly and includes sessions seen/closed/skipped, skipped reasons, aggregate signal-only counts, and aggregate tradable paper PnL.
- Existing Phase 1-11 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`.
- Forbidden-path search returned no matches.

run manifest 样例：
```json
{"config_snapshot": {"max_sessions": 2}, "created_at": "2026-07-07T15:27:16.381895+00:00", "mode": "self_check", "run_id": "self-check-run", "schema_version": "phase12_run_artifacts_v1", "session_index": "session_index.json", "status": "completed", "summary": "summary.json", "supervisor_jsonl": "supervisor.jsonl", "updated_at": "2026-07-07T15:27:16.381895+00:00"}
```

session index 样例：
```json
{"schema_version": "phase12_run_artifacts_v1", "sessions": [{"market_end_time": "2026-07-06T12:15:00+00:00", "market_id": "market-current", "market_slug": "btc-15m-current", "market_start_time": "2026-07-06T12:00:00+00:00", "paper_pnl": 11.0, "resolution_path": "sessions/01_market-current/resolution.json", "resolution_raw_path": "sessions/01_market-current/resolution_raw.json", "resolution_status": "resolved", "result_path": "sessions/01_market-current/result.json", "result_status": "closed", "runner_output": "sessions/01_market-current/runner.jsonl", "runner_status": "finished", "session_key": "01_market-current", "skip_reason": null}, {"market_end_time": "2026-07-06T12:30:00+00:00", "market_id": "market-next", "market_slug": "btc-15m-next", "market_start_time": "2026-07-06T12:15:00+00:00", "paper_pnl": null, "resolution_path": null, "resolution_raw_path": null, "resolution_status": "missing", "result_path": null, "result_status": "skipped", "runner_output": null, "runner_status": "skipped", "session_key": "02_market-next", "skip_reason": "stale_open_price_record"}]}
```

summary 样例：
```json
{"aggregate_signal_only_counts": {"DOWN": 0, "NO_SIGNAL": 0, "UP": 1}, "aggregate_tradable_paper_pnl": 11.0, "sessions_closed": 1, "sessions_seen": 2, "sessions_skipped": 1, "skipped_reasons": {"stale_open_price_record": 1}, "supervisor_jsonl": "supervisor.jsonl"}
```

手工检查：
- `polybot/run_artifacts.py` only consumes existing supervisor JSONL and Phase 10 batch summary structures.
- Runner JSONL is copied into the run directory without changing raw record shape.
- Closed-session result data is written beside raw runner/resolution artifacts; PnL comes from Phase 10/5 summary output, not a new formula.
- No supervisor orchestration, result closer, resolution ingestion, signal, or paper fill semantics were modified.

范围外未做：
- No database, SQLite, ORM, long-term DB schema, daemon, restart policy, process supervision, launchd/systemd/crontab, live trading, order placement, wallet/signing/credential path, UMA/onchain action, `p_hat` model/training/backfill, or new strategy rule.

阻塞/待规划决定：
- Final `p_hat` modeling, daemon hardening/restart policy, process supervision, and any future database/storage backend remain later planning decisions.

### 2026-07-07 - Phase 11 Accepted And Phase 12 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 11, then prepare the local persistence slice needed for stable long-running paper simulation.
- Accepted slice:
  - Phase 11 conservative automatic resolution ingestion.
- Planning note:
  - Phase 12 should define and implement a small local run-artifact layout and index for bounded or continuous paper runs.
  - The goal is durable JSON/JSONL organization: run manifest, session index, file paths, status, skip reasons, resolution/result paths, and aggregate summary.
  - Phase 12 must not introduce a database, daemon, restart policy, `p_hat` model, live trading, or new strategy behavior.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 11 Conservative Resolution Ingestion Execution

任务ID：
polybot-paper-phase-11-conservative-resolution-ingestion

改动文件：
- Added `polybot/resolution_ingestion.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added conservative resolution ingestion from local fixture JSON or public Gamma market metadata GET inputs.
- Output is Phase 10-compatible JSON: `{"resolutions": {market_id: "UP"|"DOWN"}, "skipped": [...]}`.
- Raw metadata can be saved with `--raw-output` for audit.
- Automatic resolution is accepted only when:
  - `closed` is true
  - `umaResolutionStatus` is absent or an accepted terminal status (`resolved`, `settled`, `finalized`, `complete`, `completed`)
  - `outcomes` parse to exactly two labels
  - `outcomePrices` parse to exactly two numeric prices
  - exactly one price is `1.0` and exactly one price is `0.0`
  - winning outcome maps to `UP` or `DOWN` directly or through `selected_side_labels`
- Disputed or non-terminal UMA resolution statuses are skipped; they are not resolved from `outcomePrices`.
- Any other payload records a skip reason and does not guess.

运行命令：
- `python3 -m polybot.resolution_ingestion --self-check`
- `python3 -m polybot.resolution_ingestion --fixture-json /private/tmp/polybot_phase11_fixture.json --output /private/tmp/polybot_phase11_resolution_cli.json --raw-output /private/tmp/polybot_phase11_resolution_raw.json`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor_results --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|uma_proposal|uma_dispute|uma_vote|uma_redeem|proposal action|dispute action|vote action|redeem action|redeem\\(|p_hat training|database schema|restart policy|launchd|systemd|crontab|daemon" polybot requirements.txt`

结果：
- Phase 11 resolution ingestion self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase11_resolution_ingestion/resolution_map.json`.
- Self-check covers:
  - UP winning fixture -> resolution map `UP`
  - DOWN winning fixture -> resolution map `DOWN`
  - not closed -> `not_closed`
  - missing outcomes -> `missing_outcomes`
  - non-binary outcomes -> `non_binary_market`
  - missing outcome prices -> `missing_outcome_prices`
  - invalid outcome prices -> `invalid_outcome_prices`
  - ambiguous terminal prices -> `ambiguous_terminal_prices`
  - 50/50 terminal prices -> `fifty_fifty_resolution`
  - unmapped winner label -> `unmapped_outcome`
  - disputed UMA status -> `disputed_resolution_status`
  - non-terminal UMA status -> `unresolved_resolution_status`
  - generated map consumed by Phase 10 batch closer, closing one paper result with aggregate paper PnL `11.0`
- CLI fixture command wrote `/private/tmp/polybot_phase11_resolution_cli.json` and `/private/tmp/polybot_phase11_resolution_raw.json`.
- Existing Phase 1-10 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`.
- Forbidden-path search returned no matches.

resolution map 样例：
```json
{"resolutions": {"market-up": "UP"}, "skipped": [], "source_market_id": "market-up"}
```

skip reason 样例：
```json
{"market_id": "market-open", "status": "skipped", "skip_reason": "not_closed"}
{"market_id": "market-missing-outcomes", "status": "skipped", "skip_reason": "missing_outcomes"}
{"market_id": "market-many", "status": "skipped", "skip_reason": "non_binary_market"}
{"market_id": "market-missing-price", "status": "skipped", "skip_reason": "missing_outcome_prices"}
{"market_id": "market-invalid-price", "status": "skipped", "skip_reason": "invalid_outcome_prices"}
{"market_id": "market-ambiguous", "status": "skipped", "skip_reason": "ambiguous_terminal_prices"}
{"market_id": "market-half", "status": "skipped", "skip_reason": "fifty_fifty_resolution"}
{"market_id": "market-unclear", "status": "skipped", "skip_reason": "unmapped_outcome"}
{"market_id": "market-disputed", "status": "skipped", "skip_reason": "disputed_resolution_status"}
{"market_id": "market-proposed", "status": "skipped", "skip_reason": "unresolved_resolution_status"}
```

手工检查：
- `polybot/resolution_ingestion.py` uses public Gamma market metadata shape from Polymarket docs: `closed`, `outcomes`, `outcomePrices`, `closedTime`, `umaResolutionStatus`.
- `derive_resolution(...)` checks `umaResolutionStatus` before outcome-price winner mapping, so disputed payloads skip even if prices are `1/0`.
- It uses GET metadata only through existing `fetch_json`; no order, wallet, credential, signing, onchain, or trading API path was added.
- Phase 5 result closer semantics were not modified.
- Phase 10 batch closer semantics were not modified; it can already consume the `resolutions` object produced by Phase 11.
- Network live smoke test was not run; self-check and CLI fixture are local and deterministic.

范围外未做：
- No wallet, live trading, order placement, signing, credential path, UMA proposal/dispute/vote/redeem action, guessed winner, disputed/ambiguous policy handling beyond skip, `p_hat` model/training/backfill, persistent database schema, daemon, process supervision, restart policy, launchd/systemd/crontab config, or new strategy rule.

阻塞/待规划决定：
- Final `p_hat` modeling, long-run storage shape, daemon hardening, alternate settlement sources, and disputed/ambiguous resolution policy remain later planning decisions.

### 2026-07-07 - Phase 10 Accepted And Phase 11 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 10, then prepare a conservative automatic resolution slice.
- Accepted slice:
  - Phase 10 supervisor result batch closing.
- Planning note:
  - Phase 11 should fetch closed market metadata from the public Gamma market endpoint and derive a resolution map only when the payload is unambiguous.
  - Accepted automatic resolution evidence is limited to closed markets with parseable outcomes/outcomePrices and exactly one winning binary outcome that maps to UP or DOWN.
  - Phase 11 must skip ambiguous, missing, disputed, non-binary, 50/50, or unmapped payloads instead of guessing.
- Source note:
  - Official Polymarket docs say resolved winning tokens redeem for $1 and losing tokens become $0, and Gamma market docs expose closed market fields including `outcomes`, `outcomePrices`, `closed`, `closedTime`, and `umaResolutionStatus`.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 10 Supervisor Result Batch Close Execution

任务ID：
polybot-paper-phase-10-supervisor-result-batch-close

改动文件：
- Added `polybot/supervisor_results.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a batch closer that reads Phase 9 supervisor JSONL and locates `session_runner_finished` runner outputs.
- Resolution input is explicit JSON, keyed by `market_id` or exact `runner_output` path.
- Each closed session is scored by reusing `polybot.result_closer.close_results(...)`; no duplicate PnL formula was added.
- Missing runner output, missing runner file, missing resolution, invalid winning side, and supervisor runner skips become skipped sessions.
- Output remains a single JSON summary; no database or long-term storage schema was added.

运行命令：
- `python3 -m polybot.supervisor_results --self-check`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.supervisor --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement crawler|p_hat training|database schema|restart policy|launchd|systemd|crontab|daemon" polybot requirements.txt`

结果：
- Phase 10 supervisor result batch closer self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase10_supervisor_results/batch_summary.json`.
- Self-check covers:
  - two runner outputs referenced by one sample supervisor JSONL
  - one closed session using explicit `market-current: UP` resolution
  - winning UP filled trade and losing DOWN filled trade through existing Phase 5 close logic
  - one runner output skipped because its resolution is missing
  - aggregate paper PnL equals closed sessions only: `11.0 + -4.0 = 7.0`
  - separate aggregate signal-only counts and tradable-signal PnL
- Existing Phase 1-9 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`.
- Forbidden-path search returned no matches.

batch summary 样例：
```json
{
  "sessions_seen": 2,
  "sessions_closed": 1,
  "sessions_skipped": 1,
  "skipped_reasons": {"missing_resolution": 1},
  "aggregate_signal_only_counts": {"UP": 1, "DOWN": 1, "NO_SIGNAL": 0},
  "aggregate_tradable_paper_pnl": 7.0,
  "per_session": [
    {
      "status": "closed",
      "session": {"market_id": "market-current"},
      "winning_side": "UP",
      "summary": {
        "signal_only": {"counts": {"UP": 1, "DOWN": 1, "NO_SIGNAL": 0}},
        "tradable_signal": {"filled_count": 2, "total_paper_pnl": 7.0}
      }
    },
    {
      "status": "skipped",
      "session": {"market_id": "market-next"},
      "skip_reason": "missing_resolution"
    }
  ]
}
```

手工检查：
- `polybot/supervisor_results.py` imports and calls `close_results`, `load_jsonl`, `parse_winning_side`, and `write_summary` from `polybot.result_closer`.
- Phase 5 result closer semantics were not modified.
- Phase 9 supervisor orchestration was not modified.
- The batch closer only consumes JSONL/JSON files and explicit resolution input; it does not fetch settlement or infer winning side.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic settlement crawler, Polymarket resolution crawling, guessed winning side, `p_hat` model/training/backfill, persistent database schema, unbounded daemon, process supervision, restart policy, launchd/systemd/crontab config, or new strategy rule.

阻塞/待规划决定：
- Automatic resolution source, final `p_hat` modeling, long-run storage shape, daemon hardening, and any production-grade supervision remain later planning decisions.

### 2026-07-07 - Phase 9 Accepted And Phase 10 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 9, then prepare the next paper-simulation accounting slice.
- Accepted slice:
  - Phase 9 bounded continuous supervisor.
- Planning note:
  - The next useful slice is Phase 10 supervisor result batch closing.
  - Phase 10 should read supervisor JSONL, locate per-session runner JSONL outputs, close sessions using an explicit resolution map, and write an aggregate paper result summary.
  - Phase 10 must not guess Polymarket settlement, crawl automatic resolution, add a database, change strategy rules, or add daemon behavior.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 9 Bounded Supervisor Execution

任务ID：
polybot-paper-phase-9-bounded-supervisor

改动文件：
- Added `polybot/supervisor.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a bounded supervisor entry point that orchestrates existing `select_session`, `plan_rotation`, `enrich_session_config`, and `run_session_once`.
- Supervisor writes JSONL records for `supervisor_started`, `session_discovered`, `session_skipped`, `open_price_captured`, `open_price_skipped`, `session_runner_started`, `session_runner_finished`, `session_runner_skipped`, `rotation_planned`, and `supervisor_stopped`.
- Stop reasons implemented: `reached_max_sessions`, `reached_max_runtime`, `reached_end_time`, `no_next_session`, and `unrecoverable_error`; recoverable runner errors are recorded as skipped runner steps.
- Each runner invocation writes to a traceable per-session JSONL path under the configured output directory.
- Self-check uses local fixtures only and injects records into existing module APIs; it does not use network capture.

运行命令：
- `python3 -m polybot.supervisor --self-check`
- `python3 -m polybot.supervisor --sample-fixture --now 2026-07-06T12:05:00+00:00 --max-sessions 1 --lookahead-minutes 20 --output-dir /private/tmp/polybot_phase9_cli --supervisor-jsonl /private/tmp/polybot_phase9_cli/supervisor.jsonl --paper-stake 9 --runner-seconds 0`
- `python3 -m polybot.supervisor --sample-fixture --now 2026-07-06T12:05:00+00:00 --max-sessions 1 --max-runtime-seconds 0 --lookahead-minutes 20 --output-dir /private/tmp/polybot_phase9_runtime_stop --supervisor-jsonl /private/tmp/polybot_phase9_runtime_stop/supervisor.jsonl --paper-stake 9 --runner-seconds 0`
- `python3 -m polybot.supervisor --sample-fixture --now 2026-07-06T12:05:00+00:00 --max-sessions 1 --end-time 2026-07-06T12:00:00+00:00 --lookahead-minutes 20 --output-dir /private/tmp/polybot_phase9_end_stop --supervisor-jsonl /private/tmp/polybot_phase9_end_stop/supervisor.jsonl --paper-stake 9 --runner-seconds 0`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.open_price --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement crawler|p_hat training|restart policy|launchd|systemd|crontab|daemon" polybot requirements.txt`

结果：
- Phase 9 supervisor self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase9_supervisor/supervisor.jsonl`.
- Self-check processed two local fixture sessions:
  - first session captured open price and ran the existing session runner
  - second session recorded recoverable `stale_open_price_record` skip and did not crash
- Self-check recorded `rotation_planned`, per-session runner output path, `supervisor_started`, and `supervisor_stopped`.
- CLI sample fixture command with no BTC records recorded `no_post_start_record` skip and stopped at `reached_max_sessions`.
- Explicit bounds commands verified `reached_max_runtime` and `reached_end_time`.
- Existing Phase 1-8 self-checks passed.
- Compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache`; a plain compileall attempt hit the sandboxed macOS user-cache permission issue.
- Forbidden-path search returned no matches.

supervisor JSONL 样例：
```json
{"record_type": "supervisor_started", "max_sessions": 2}
{"record_type": "session_discovered", "session": {"market_id": "market-current", "market_slug": "btc-15m-current"}, "session_index": 1}
{"record_type": "open_price_captured", "session": {"market_id": "market-current"}, "open_price": 100.0}
{"record_type": "session_runner_finished", "session": {"market_id": "market-current"}, "runner_output": "/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase9_supervisor/session_1_market-current.jsonl"}
{"record_type": "rotation_planned", "from_session": {"market_id": "market-current"}}
{"record_type": "session_discovered", "session": {"market_id": "market-next"}, "session_index": 2}
{"record_type": "open_price_skipped", "session": {"market_id": "market-next"}, "skip_reason": "stale_open_price_record"}
{"record_type": "session_runner_skipped", "session": {"market_id": "market-next"}, "skip_reason": "stale_open_price_record"}
{"record_type": "supervisor_stopped", "processed_sessions": 2, "stop_reason": "reached_max_sessions"}
```

session runner 输出样例：
```json
{"record_type": "runtime_note", "note": "session_runner_started", "session": {"market_id": "market-current", "market_slug": "btc-15m-current"}}
{"record_type": "signal_record", "record": {"signal": "UP", "open_price": 100.0, "current_price": 100.06, "remaining_seconds": 180}}
{"record_type": "runtime_note", "note": "selected_token", "selected_token": {"side": "UP", "token_id": "up-token-current"}}
{"record_type": "runtime_note", "note": "market_data_record", "record": {"source": "polymarket", "event_type": "book"}}
{"record_type": "skipped_trade_record", "record": {"signal": "UP", "skip_reason": "insufficient_ask_depth", "stake": 9.0}}
```

手工检查：
- `polybot/supervisor.py` does not rewrite signal, discovery validation, open-price selection, token selection, marketability, or paper fill logic.
- Supervisor uses JSONL files only and does not introduce a database.
- Network/public API capture remains optional through existing discovery/runner paths; self-check is local and deterministic.
- Runner output path is recorded before and after each runner call.
- Recoverable open-price skip writes both `open_price_skipped` and `session_runner_skipped`.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic settlement/result closing, `p_hat` model, training/backfill, new BTC source, candle aggregation, unbounded daemon, process supervision, restart policy, launchd/systemd/crontab config, persistent database schema, or new trading rule.

阻塞/待规划决定：
- Resolution automation, final `p_hat` modeling, long-run storage shape, daemon hardening, and any production-grade process supervision remain later planning decisions.

### 2026-07-07 - Phase 8 Accepted And Phase 9 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 8, then prepare the first bounded continuous simulation slice.
- Accepted slice:
  - Phase 8 automatic open-price capture.
- Planning note:
  - The next useful slice is Phase 9 bounded continuous supervisor.
  - Phase 9 should chain discovery, open-price enrichment, one-session runner execution, and rotation for a configured session count or time limit.
  - Phase 9 must remain paper-only and bounded; long-running daemon hardening, automatic settlement, final `p_hat` modeling, and long-run storage stay later.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 8 Open-Price Capture Execution

任务ID：
polybot-paper-phase-8-open-price-capture

改动文件：
- Added `polybot/open_price.py`
- Updated `polybot/paper_runner.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a one-session open-price enrichment path that consumes existing `CaptureRecord` BTC reference records.
- Open price selection ignores pre-start records, selects the first valid post-start record within `max_open_price_delay_seconds`, and rejects non-positive or non-numeric prices.
- Enriched session config appends `open_price`, `open_price_timestamp`, `open_price_source`, `open_price_max_delay_seconds`, and `open_price_capture_status`.
- Skip output records `skip_reason` instead of guessing when records are pre-start-only, stale, missing, or invalid.
- Phase 7 runner can now use `session_config.open_price` when CLI `--open-price` is omitted; CLI `--open-price` still overrides config.

运行命令：
- `python3 -m polybot.open_price --self-check`
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -c 'from datetime import datetime, timezone; import json; from polybot.market_discovery import sample_payload, select_session; from polybot.open_price import enrich_session_config, sample_record, parse_datetime; session=select_session(sample_payload(), datetime(2026,7,6,12,5,tzinfo=timezone.utc), 20, "current"); start_ms=int(parse_datetime(session["selection"]["market_start_time"]).timestamp()*1000); print(json.dumps(enrich_session_config(session, [sample_record("99.9", start_ms-1)], 5), sort_keys=True))'`
- `python3 -c 'from datetime import datetime, timezone; import json; from polybot.market_discovery import sample_payload, select_session; from polybot.open_price import enrich_session_config, sample_record, parse_datetime; session=select_session(sample_payload(), datetime(2026,7,6,12,5,tzinfo=timezone.utc), 20, "current"); start_ms=int(parse_datetime(session["selection"]["market_start_time"]).timestamp()*1000); print(json.dumps(enrich_session_config(session, [sample_record("100.01", start_ms+6000)], 5), sort_keys=True))'`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement crawler|p_hat training|daemon supervisor|supervisor|restart policy|new BTC source|candle aggregation|aggregate_candle|candlestick|kline" polybot requirements.txt`

结果：
- Phase 8 open-price self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase8_enriched_session_config.json`.
- Self-check covers:
  - first valid post-start BTC record becomes `open_price`
  - pre-start-only records produce `no_post_start_record`
  - stale post-start records produce `stale_open_price_record`
  - non-positive and non-numeric prices produce `invalid_open_price`
- Runner session self-check still passed and now asserts config `open_price` fallback plus CLI override behavior.
- Existing Phase 1 signal, Phase 2 market-data, Phase 3 marketability, Phase 4 paper-runner, Phase 5 result-closer, Phase 6 market-discovery, and Phase 7 session-runner self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.

enriched session config 样例：
```json
{"selection": {"caller_supplied_p_hat": 0.55, "discovery_source_timestamp": null, "down_token_id": "down-token-current", "event_id": "event-current", "event_slug": "btc-updown-current", "local_timestamp": "2026-07-07T02:35:50.820589+00:00", "market_end_time": "2026-07-06T12:15:00+00:00", "market_id": "market-current", "market_slug": "btc-15m-current", "market_start_time": "2026-07-06T12:00:00+00:00", "open_price": 100.01, "open_price_capture_status": "captured", "open_price_max_delay_seconds": 5, "open_price_source": "binance_btcusdt_trade", "open_price_timestamp": "2026-07-06T12:00:00+00:00", "paper_stake": 9.0, "question": "Bitcoin Up or Down - current", "selected_side_labels": {"DOWN": "Down", "UP": "Up"}, "up_token_id": "up-token-current"}, "skip_reason": null}
```

skip reason 样例：
```json
{"selection": {"market_id": "market-current", "open_price_capture_status": "skipped", "skip_reason": "no_post_start_record"}, "skip_reason": "no_post_start_record"}
{"selection": {"market_id": "market-current", "open_price_capture_status": "skipped", "skip_reason": "stale_open_price_record"}, "skip_reason": "stale_open_price_record"}
```

手工检查：
- `polybot/open_price.py` uses `CaptureRecord` from `polybot.market_data` and the existing BTC reference record shape.
- No new BTC source, candle aggregation, external candle alignment, or polling path was added.
- Root signal logic, Phase 2 WebSocket capture, Phase 3 ask-depth fill, Phase 5 closer, Phase 6 discovery validation, and Phase 7 token selection rules are unchanged.
- Runner compatibility is limited to reading `open_price` from enriched config when CLI `--open-price` is absent.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic settlement/result closing, final `p_hat` model, training/backfill, new BTC source, candle aggregation, long-running daemon, process supervision, restart policy, persistent database schema, or new trading rule.

阻塞/待规划决定：
- Resolution automation, final `p_hat` modeling, bounded continuous supervisor, daemon hardening, long-run storage shape, and any exchange-candle alignment remain later planning items.

### 2026-07-07 - Phase 7 Accepted And Phase 8 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 7, then prepare the next unattended-paper-trading slice.
- Accepted slice:
  - Phase 7 session-config runner wiring.
- Planning note:
  - The next useful slice is Phase 8 automatic open-price capture.
  - Phase 8 should derive the session open price from the existing BTC reference WebSocket records around market start.
  - Phase 8 should still run/enrich one configured session only; bounded continuous supervisor, daemon hardening, automatic settlement, and final `p_hat` modeling stay later.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-07 - Phase 7 Session Config Runner Execution

任务ID：
polybot-paper-phase-7-session-config-runner

改动文件：
- Updated `polybot/paper_runner.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a session-config runner path to `paper_runner.py`; the existing explicit `--polymarket-asset-id` path remains intact.
- Added `--session-config` CLI input plus `--session-self-check`.
- Session-config path keeps `open_price` explicit and uses `paper_stake` / caller-supplied `p_hat` from config unless CLI overrides are supplied.
- Runner generates the root signal first, then selects `up_token_id` for `UP` or `down_token_id` for `DOWN`.
- `NO_SIGNAL` records a runtime note and does not select a token or create a paper fill.
- Missing token mapping records `missing_token_id` as runtime note and skipped trade; it does not guess.
- Existing JSONL record shapes are preserved; session and selected-token metadata are appended beside the existing `record` payload.

运行命令：
- `python3 -m polybot.paper_runner --session-self-check`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.market_discovery --self-check`
- `python3 -m polybot.result_closer --runner-jsonl /private/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase7_session_runner_self_check.jsonl --winning-side UP --output /private/tmp/polybot_phase7_closer_compat.json`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement crawler|p_hat training|daemon supervisor|supervisor|restart policy|open price capture|capture_open|open_price_source" polybot requirements.txt`

结果：
- Phase 7 session-config runner self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase7_session_runner_self_check.jsonl`.
- Self-check covers:
  - `UP` signal selects `up-token-current`
  - `DOWN` signal selects `down-token-current`
  - `NO_SIGNAL` selects no token and creates no paper fill
  - missing `down_token_id` records `missing_token_id`
- Existing Phase 1 signal, Phase 2 market-data, Phase 3 marketability, Phase 4 paper-runner, Phase 5 result-closer, and Phase 6 market-discovery self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Phase 5 result closer consumed the Phase 7 JSONL successfully, proving appended session/token metadata did not break older record consumers.

session runner JSONL 样例：
```json
{"note": "session_runner_started", "record_type": "runtime_note", "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
{"record": {"current_price": 100.06, "market_end_time": "2026-07-06T12:15:00+00:00", "open_price": 100.0, "remaining_seconds": 180, "ret_pct": 0.060000000000002274, "signal": "UP"}, "record_type": "signal_record", "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
{"note": "selected_token", "record_type": "runtime_note", "selected_token": {"label": "Up", "side": "UP", "token_id": "up-token-current"}, "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
{"record": {"caller_supplied_p_hat": 0.55, "executable_avg_ask": 0.45, "kelly_fraction_reference": 0.18181818181818185, "shares": 20.0, "signal": "UP", "stake": 9.0, "trade_edge": 0.10000000000000003}, "record_type": "paper_trade_record", "selected_token": {"label": "Up", "side": "UP", "token_id": "up-token-current"}, "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
{"note": "no_signal_no_token_selected", "record_type": "runtime_note", "selected_token": {"label": null, "side": null, "token_id": null}, "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
{"record": {"signal": "DOWN", "skip_reason": "missing_token_id", "stake": 9.0}, "record_type": "skipped_trade_record", "selected_token": {"label": "Down", "side": "DOWN", "token_id": null}, "session": {"event_id": "event-current", "event_slug": "btc-updown-current", "market_id": "market-current", "market_slug": "btc-15m-current"}}
```

手工检查：
- Signal remains generated by `build_signal_record(...)` from explicit open price, current BTC price, market end time, and now.
- Token selection happens only after the signal is known.
- Marketability and paper fill still use `evaluate_marketability(...)` and ask-depth walk behavior from Phase 3.
- Phase 2 WebSocket capture path is unchanged.
- Phase 5 result closer and Phase 6 discovery validation are unchanged.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic settlement/result closing, final `p_hat` model, training/backfill, automatic open-price capture, long-running daemon, process supervision, restart policy, persistent database schema, or new trading rule.

阻塞/待规划决定：
- Automatic open-price capture, automatic settlement source, final `p_hat` modeling, bounded continuous supervisor, daemon hardening, and any broader multi-session orchestration remain later planning items.

### 2026-07-07 - Phase 6 Accepted And Phase 7 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 6, then prepare the next unattended-paper-trading slice.
- Accepted slice:
  - Phase 6 market discovery and session rotation planner.
- Planning note:
  - The next useful slice is Phase 7 session-config runner wiring.
  - Phase 7 should let the runner consume Phase 6 session config and choose the UP/DOWN token according to the root signal.
  - Phase 7 should still run one configured session only; bounded continuous supervisor, daemon hardening, automatic settlement, and final `p_hat` modeling stay later.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-06 - Zone Memory Resync And Local Rulebook Preference

- Goal: Re-read `zone-memory`, sync any missing workflow rules into local project docs, and make local docs the default source for future runs.
- Changed:
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated `docs/project_notes/key_facts.md`
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - After workflow sync, normal future runs should read local workspace docs first instead of rereading `zone-memory`.
  - `zone-memory` should be reopened only for explicit workflow resyncs or when local docs appear stale or contradictory.
- Scope skipped:
  - No product code, strategy behavior, or phase implementation changed.

### 2026-07-06 - Phase 6 Market Discovery And Rotation Execution

任务ID：
polybot-paper-phase-6-market-discovery-rotation

改动文件：
- Added `polybot/market_discovery.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a public metadata discovery/planning module for BTC 15-minute markets.
- Discovery accepts local/sample JSON or optional public Gamma events URL/filter inputs; it does not touch WebSocket orderbook capture.
- Auto-selection only succeeds when exactly one candidate matches the requested `current` or `next` window.
- Candidate validation checks BTC/Bitcoin identity, 15-minute duration, active/open status, start/end time, and explicit `UP`/`DOWN` token mapping.
- Rotation planning returns the next session config or a skip reason; it does not start a long-running process.
- Session config includes market/event identifiers, title/question, start/end time, UP/DOWN token ids, side labels, discovery timestamps, optional paper stake, and optional caller-supplied `p_hat`.

运行命令：
- `python3 -m polybot.market_discovery --self-check`
- `python3 -c 'from datetime import datetime, timezone; import json; from polybot.market_discovery import sample_payload, select_session; now=datetime(2026,7,6,12,5,tzinfo=timezone.utc); print(json.dumps(select_session(sample_payload()+sample_payload()[:1], now, 20, "current"), sort_keys=True))'`
- `python3 -c 'from datetime import datetime, timezone; import json; from polybot.market_discovery import select_session; payload=[{"id":"event-bad","title":"BTC 15m","active":True,"closed":False,"markets":[{"id":"market-bad","question":"BTC 15m","active":True,"closed":False,"startDate":"2026-07-06T12:00:00+00:00","endDate":"2026-07-06T12:15:00+00:00","outcomes":"[\\"Yes\\", \\"No\\"]","clobTokenIds":"[\\"yes-token\\", \\"no-token\\"]"}]}]; now=datetime(2026,7,6,12,5,tzinfo=timezone.utc); print(json.dumps(select_session(payload, now, 20, "current"), sort_keys=True))'`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.result_closer --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement crawler|p_hat training|daemon supervisor|supervisor|restart policy" polybot requirements.txt`

结果：
- Phase 6 self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase6_session_config.json`.
- Self-check covers exactly one valid current BTC 15m market, exactly one valid next BTC 15m market, rotation to next session, ambiguous candidates skip, and unclear UP/DOWN mapping skip.
- Existing Phase 1 signal, Phase 2 market-data, Phase 3 marketability, Phase 4 paper-runner, and Phase 5 result-closer self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.
- Live public API demo was not run; implementation uses the official public Gamma events shape documented for market discovery and keeps runtime mismatch handling as validation skips.

session config 样例：
```json
{"selection": {"caller_supplied_p_hat": 0.55, "discovery_source_timestamp": null, "down_token_id": "down-token-current", "event_id": "event-current", "event_slug": "btc-updown-current", "local_timestamp": "2026-07-06T14:11:51.976451+00:00", "market_end_time": "2026-07-06T12:15:00+00:00", "market_id": "market-current", "market_slug": "btc-15m-current", "market_start_time": "2026-07-06T12:00:00+00:00", "paper_stake": 9.0, "question": "Bitcoin Up or Down - current", "selected_side_labels": {"DOWN": "Down", "UP": "Up"}, "up_token_id": "up-token-current"}, "skip_reason": null}
```

skip reason 样例：
```json
{"candidate_count": 2, "local_timestamp": "2026-07-06T14:12:30.547403+00:00", "selection": null, "skip_reason": "ambiguous_candidates", "validation_skip_reasons": {}}
{"candidate_count": 0, "local_timestamp": "2026-07-06T14:12:30.546996+00:00", "selection": null, "skip_reason": "no_valid_candidate", "validation_skip_reasons": {"unclear_up_down_mapping": 1}}
```

手工检查：
- `polybot/market_discovery.py` does not import or call signal generation, market capture, marketability, paper runner orchestration, or result closer.
- Price/orderbook capture remains WebSocket-first in `polybot/market_data.py`.
- No Phase 1-5 core-rule files were modified by this task.
- Official docs checked: Polymarket market data is public/no-auth, and Gamma `events` supports active/closed/tag/slug-style discovery.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic settlement/result closing, `p_hat` model, training/backfill, long-running daemon, process supervision, restart policy, persistent database schema, or Phase 1-5 rule change.

阻塞/待规划决定：
- Final `p_hat` modeling, automatic settlement source, live trading path, daemon supervision/restart policy, and any richer runner wiring from UP/DOWN token config remain later planning items.

### 2026-07-06 - Git Publish Completed

- Goal: Finish the initial GitHub publish for the current PolyBot baseline.
- Changed:
  - Updated `docs/project_notes/issues.md`
- Verified:
  - Root commit `1ab2915` was created on local branch `main`
  - Remote `origin` points to `https://github.com/Jeffrey22444/PolyBot.git`
  - `git push -u origin main` succeeded
- Manual:
  - GitHub web UI can now be used for branch/repo visibility checks if desired
- Scope skipped:
  - No product code, strategy behavior, or dependency changes

### 2026-07-06 - Phase 5 Accepted And Phase 6 Ready

- Goal: Record user-confirmed execution and acceptance pass for Phase 5, then prepare the next unattended-paper-trading slice.
- Accepted slice:
  - Phase 5 settlement/result closer.
- Planning note:
  - The next useful slice is Phase 6 market discovery and session rotation planning.
  - Phase 6 should use public market metadata to resolve current/next BTC 15-minute markets and generate runner inputs.
  - Phase 6 must not add live trading, wallet/signing, automatic settlement, final `p_hat` modeling, or long-running daemon hardening.
- Scope skipped:
  - No product code changed by planning.

### 2026-07-06 - Git Publish Baseline

- Goal: Verify the workspace git environment and publish the current baseline to the canonical GitHub repository.
- Changed:
  - Updated `docs/project_notes/issues.md`
- Verified:
  - Local repository exists on branch `main`
  - Working tree has no commits yet and currently contains the full project baseline
  - No `origin` remote was configured before publish setup
  - GitHub CLI is installed locally
- Manual:
  - GitHub authentication may need refresh before first push if the stored token is invalid
- Scope skipped:
  - No product code, strategy behavior, or dependency changes

### 2026-07-06 - Phase 5 Result Closer Execution

任务ID：
polybot-paper-phase-5-result-closer

改动文件：
- Added `polybot/result_closer.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a result closer that consumes Phase 4 runner JSONL records only.
- CLI accepts runner JSONL path, explicit winning side, and output JSON/JSONL path.
- Winning side is validated as `UP` or `DOWN`.
- Filled paper trade PnL uses the Phase 5 rule: win = `shares - stake`, loss = `-stake`.
- Skipped trades are counted by reason and do not affect PnL.
- Signal-only summary remains separate from tradable-signal result summary.

运行命令：
- `python3 -m polybot.result_closer --self-check`
- `python3 -m polybot.result_closer --runner-jsonl /private/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase4_runner_self_check.jsonl --winning-side UP --output /private/tmp/polybot_phase5_result_demo.json`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `python3 -m polybot.paper_runner --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|market discovery|discover|rotation|rotate|p_hat training|train|training|settlement crawler|Polymarket resolution|resolution API" polybot requirements.txt`

结果：
- Phase 5 self-check passed and wrote `/var/folders/wc/vgdsxd757mv2_2mzx_l38xcw0000gn/T/polybot_phase5_result_summary.json`.
- Self-check covers a winning filled trade, losing filled trade, skipped trade, signal-only summary, and total paper PnL.
- CLI demo consumed the Phase 4 self-check JSONL and wrote `/private/tmp/polybot_phase5_result_demo.json`.
- Existing Phase 1 signal, Phase 2 market-data, Phase 3 marketability, and Phase 4 paper-runner self-checks passed.
- Compile check passed.
- Forbidden-path search returned no matches.

result summary 样例：
```json
{"signal_only": {"counts": {"DOWN": 0, "NO_SIGNAL": 0, "UP": 2}, "losing_side_count": 0, "no_signal_count": 0, "winning_side_count": 2}, "tradable_signal": {"filled_count": 1, "paper_pnl": [{"paper_pnl": 11.0, "shares": 20.0, "signal": "UP", "stake": 9.0}], "skipped_reasons": {"missing_p_hat": 1}, "total_paper_pnl": 11.0}, "winning_side": "UP"}
```

手工检查：
- `polybot/result_closer.py` does not import or call Phase 4 runner orchestration, market capture, marketability, or paper fill.
- No wallet, signing, credential, live order, order placement, market discovery, rotation, `p_hat` training, settlement crawler, or resolution API path.
- No Phase 1-4 core-rule files were modified by this task.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic market discovery or rotation, automatic settlement fetch, `p_hat` model, historical backfill, long-term database schema, or Phase 1-4 rule change.

阻塞/待规划决定：
- Automatic market/session discovery, verified resolution-source automation, unattended rotation, and final `p_hat` modeling remain later planning items.

### 2026-07-06 - Zone Memory Rule Refill And Phase 5 Ready

- Goal: Refill missing zone-memory operating rules and prepare Phase 5 settlement/result closer.
- Changed:
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated `docs/project_notes/key_facts.md`
  - Updated `docs/implementation-plan.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - Phase 4 is accepted.
  - Phase 5 should close recorded paper-runner trades from explicit winning-side input or a verified resolution record.
  - Phase 5 must not do market discovery, automatic rotation, live orders, or `p_hat` modeling.
- Scope skipped:
  - No implementation code changed by planning.
  - No new zones, roles, or workflow files added.

### 2026-07-06 - Phase 4 Accepted

- Goal: Record acceptance pass for `polybot-paper-phase-4-single-market-runner`.
- Accepted slice:
  - Phase 4 single-market paper runner.
- Evidence source:
  - `polybot-paper-phase-4-single-market-runner` execution block below.
- Planning note:
  - The next useful slice is Phase 5 settlement/result closer.
  - Market discovery and unattended 15-minute rotation remain future phases.

### 2026-07-06 - Phase 4 Single-Market Paper Runner Execution

任务ID：
polybot-paper-phase-4-single-market-runner

改动文件：
- Added `polybot/paper_runner.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added a single-market runner that orchestrates existing Signal, Market Data, Marketability, and Paper Fill modules.
- Runner accepts explicit CLI inputs for Polymarket asset id, open price, market end time, stake, caller-supplied `p_hat`, run seconds, and output JSONL path.
- Runner writes JSONL record types: `runtime_note`, `signal_record`, `paper_trade_record`, and `skipped_trade_record`.
- Runner does not discover or rotate markets and does not rewrite Phase 1-3 rules.

运行命令：
- `python3 -m polybot.paper_runner --self-check`
- `python3 -m polybot.paper_runner --polymarket-asset-id 43187333641922996188398060383389814287787647811837308994701068387397271207198 --open-price 100.0 --market-end-time 2099-01-01T00:00:00+00:00 --stake 9.0 --p-hat 0.55 --seconds 3 --output /private/tmp/polybot_phase4_live_demo.jsonl`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `python3 -m polybot.marketability`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|settlement|final PnL|PnL|pnl|auto discover|rotate|rotation|optimizer|train|training|historical|history" polybot requirements.txt`

结果：
- `python3 -m polybot.paper_runner --self-check` passed and wrote `polybot_phase4_runner_self_check.jsonl`.
- Self-check JSONL record types:
  `["runtime_note", "runtime_note", "runtime_note", "signal_record", "paper_trade_record", "runtime_note", "runtime_note", "runtime_note", "signal_record", "skipped_trade_record"]`
- Live runner command wrote `/private/tmp/polybot_phase4_live_demo.jsonl`.
- Live runner JSONL record types:
  `["runtime_note", "runtime_note", "runtime_note", "runtime_note", "runtime_note", "runtime_note", "runtime_note", "runtime_note", "runtime_note", "signal_record", "skipped_trade_record"]`
- Existing Phase 1 signal self-check, Phase 2 market-data self-check, and Phase 3 marketability self-check passed.
- Compile check passed.
- Forbidden-path search returned no matches after excluding output paths outside source.
- `polybot/signal.py`, `polybot/market_data.py`, and `polybot/marketability.py` have no diff from this Phase 4 work.

JSONL 输出样例：
```json
{"asset_id": "sample-asset", "local_timestamp": "2026-07-06T13:31:54.260058+00:00", "note": "runner_started", "record_type": "runtime_note"}
{"record": {"current_price": 100.06, "market_end_time": "2026-07-06T12:15:00+00:00", "now": "2026-07-06T12:12:00+00:00", "open_price": 100.0, "remaining_seconds": 180, "ret_pct": 0.060000000000002274, "signal": "UP"}, "record_type": "signal_record"}
{"record": {"caller_supplied_p_hat": 0.55, "executable_avg_ask": 0.45, "kelly_fraction_reference": 0.18181818181818185, "shares": 20.0, "signal": "UP", "stake": 9.0, "trade_edge": 0.10000000000000003}, "record_type": "paper_trade_record"}
{"record": {"caller_supplied_p_hat": null, "executable_avg_ask": 0.45, "signal": "UP", "skip_reason": "missing_p_hat", "stake": 9.0, "trade_edge": null}, "record_type": "skipped_trade_record"}
```

手工检查：
- Runner calls existing `build_signal_record(...)`, `capture_polymarket_market(...)`, `capture_btc_reference(...)`, and `evaluate_marketability(...)`.
- No wallet, signing, credential, live order, order placement, settlement, final PnL, auto market discovery, rotation, optimizer, historical `p_hat`, or training path.
- Runner uses JSONL output only; no database or schema migration.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, automatic 15-minute market discovery or rotation, `p_hat` model, settlement/final PnL, long-term database schema, Phase 1 signal change, Phase 2 capture change, or Phase 3 fill-rule change.

阻塞/待规划决定：
- Automatic current/next 15-minute market discovery, settlement source, winning side, final PnL, and `p_hat` modeling remain future planning items.

### 2026-07-06 - Unattended Paper Trading Path

- Goal: Plan the path from completed Phase 3 primitives to unattended continuous 15-minute BTC paper trading.
- Changed:
  - Updated `docs/implementation-plan.md`
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - Next slice is Phase 4 single-market paper runner.
  - Phase 4 wires existing modules into a short live simulation loop for one explicitly configured market.
  - Settlement/PnL, market discovery, and unattended rotation are later phases.
- Scope skipped:
  - No implementation code changed by planning.
  - No live trading, wallet/signing, auto market discovery, or `p_hat` model added.

### 2026-07-06 - Phase 3 Accepted

- Goal: Record user-confirmed execution and acceptance pass for Phase 3.
- Accepted slice:
  - Phase 3 marketability and paper fill.
- Evidence source:
  - `polybot-paper-phase-3-marketability-paper-fill` execution block below.
- Planning note:
  - The code now has separate Signal, Market Data, Marketability, Paper Fill, and Reporting pieces.
  - The next useful slice is a paper runner that wires these pieces into a short live simulation loop.
  - Final `p_hat` modeling remains out of scope unless planning explicitly defines it.

### 2026-07-06 - Phase 3 Marketability And Paper Fill Execution

任务ID：
polybot-paper-phase-3-marketability-paper-fill

改动文件：
- Added `polybot/marketability.py`
- Updated `polybot/paper.py`
- Updated `docs/project_notes/issues.md`

范围边界：
- Added marketability and paper-fill simulation only.
- `marketability` consumes caller-provided `Signal` plus Phase 2 `CaptureRecord`; it does not create or modify signals.
- Paper fill is simulated from ask-side depth only.
- `p_hat` is caller-supplied only; missing `p_hat` records a skip reason and leaves `trade_edge` unset.
- Reports remain split between `signal_only_report(...)` and `tradable_signal_report(...)`.

运行命令：
- `python3 -m polybot.marketability`
- `python3 -m polybot.signal`
- `python3 -m polybot.market_data --self-check`
- `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
- `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|stop-loss|take-profit|averaging|reverse|multi-entry|optimizer|train|training|historical|history" polybot requirements.txt`
- `rg -n "midpoint|last_trade|last trade|best_ask|best ask" polybot/marketability.py polybot/paper.py`
- `rg -n "from polybot\\.marketability|simulate_ask_depth_fill|evaluate_marketability|PaperTradeRecord|SkippedTradeRecord" polybot/signal.py polybot/market_data.py`

结果：
- `python3 -m polybot.marketability` output:
  `{"fill_executable_avg_ask": 0.45, "insufficient_depth_skip_reason": "insufficient_ask_depth", "missing_p_hat_skip_reason": "missing_p_hat", "missing_p_hat_trade_edge": null, "signal_after_rejection": "UP", "signal_only": {"DOWN": 0, "NO_SIGNAL": 0, "UP": 1}, "tradable_signal": {"filled": 1, "skip_reasons": {"missing_p_hat": 1}}}`
- Phase 1 signal self-check passed.
- Phase 2 market-data self-check passed.
- Compile check passed.
- Forbidden-path searches returned no matches.
- `polybot/signal.py` and `polybot/market_data.py` have no diff from this Phase 3 work.

fill simulation 证据：
- Ask depth `[0.40 x 10, 0.50 x 20]` with stake `9.0` walks both levels.
- Filled cost: `4.0 + 5.0 = 9.0`.
- Filled shares: `10 + 10 = 20`.
- `executable_avg_ask = 9.0 / 20 = 0.45`.

skip reason 证据：
- Stake `20.0` on the same depth returns `insufficient_ask_depth`.
- Missing caller-supplied `p_hat` returns `missing_p_hat` and `trade_edge = null`.
- Non-positive edge returns `non_positive_trade_edge` while preserving signal `UP`.

report separation 证据：
- `signal_only`: `{"DOWN": 0, "NO_SIGNAL": 0, "UP": 1}`
- `tradable_signal`: `{"filled": 1, "skip_reasons": {"missing_p_hat": 1}}`

手工检查：
- No wallet, signing, credential, live order, order placement, optimizer, historical `p_hat`, stop-loss, take-profit, averaging, reverse, or multi-entry path.
- No midpoint, last trade, or best ask shortcut in fill simulation.
- Marketability/paper fill code is not imported by signal or market data.

范围外未做：
- No live trading, order placement, wallet/signing/credential path, `p_hat` model, `p_hat` training/inference, optimizer, stop-loss, take-profit, averaging, reverse, multi-entry, long-term storage schema, Phase 1 signal change, or Phase 2 WebSocket capture change.

阻塞/待规划决定：
- Final `p_hat` estimation method remains out of scope and still requires future planning.

### 2026-07-06 - Phase 2 Accepted And Phase 3 Ready

- Goal: Record that Phase 2 execution and acceptance passed, then prepare the marketability and paper-fill slice.
- Changed:
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/implementation-plan.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - Phase 3 computes `trade_edge` only from caller-supplied `p_hat`.
  - Phase 3 implements ask-depth fill mechanics and separate signal-only/tradable-signal reporting.
  - Final `p_hat` modeling remains out of scope.
- Scope skipped:
  - No implementation code changed by planning.
  - No live trading, wallet signing, order placement, optimizer, or `p_hat` model added to Phase 3.

### 2026-07-06 - Phase 2 Acceptance Refill

- Goal: Address acceptance finding that no real Polymarket record proved `source_timestamp_ms` and `local_receive_timestamp`.
- Changed:
  - Updated `polybot/market_data.py`
  - Updated `docs/project_notes/api_mismatch_notes.md`
  - Updated `docs/project_notes/issues.md`
- Verified:
  - `python3 -m polybot.market_data --polymarket-asset-id 43187333641922996188398060383389814287787647811837308994701068387397271207198 --seconds 10 --limit 2 --output /private/tmp/polybot_phase2_polymarket_refill.jsonl`
  - Captured real Polymarket `book` event with `source_timestamp_ms=1783327698002` and `local_receive_timestamp=2026-07-06T08:48:29.309337+00:00`
  - Captured real Polymarket `new_market` event with `source_timestamp_ms=1783327711200`
  - `python3 -m polybot.market_data --self-check`
  - `python3 -m polybot.signal`
- Scope skipped:
  - No wallet, signing, order placement, marketability, paper fill, PnL, long-term storage schema, or Phase 1 signal rule change.

### 2026-07-06 - Phase 2 Market Capture Execution

- Goal: Implement WebSocket-first market data capture without signal, marketability, paper fill, PnL, wallet, signing, or live-order paths.
- Changed:
  - Added `requirements.txt`
  - Added `polybot/market_data.py`
  - Added `polybot/btc_reference.py`
  - Added `docs/project_notes/api_mismatch_notes.md`
- Verified:
  - `python3 -m pip install -r requirements.txt`
  - `python3 -m polybot.market_data --self-check`
  - `python3 -m polybot.market_data --polymarket-asset-id 21742633143463906290569050155826241533067272736897614950488156847949938836455 --seconds 6 --limit 1`
  - `python3 -m polybot.signal`
  - `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
  - `rg -n "wallet|credential|private|signature|signing|sign\\(|place_order|post_order|create_order|cancel_order|order placement|live order|marketability|paper fill|PnL|pnl|profit|loss|Kelly|kelly|p_hat" polybot requirements.txt`
  - `rg -n "from polybot\\.signal|import polybot\\.signal|generate_signal|Signal" polybot/market_data.py polybot/btc_reference.py`
- Captured data:
  - Binance BTCUSDT `trade` records with source event timestamps and local receive timestamps.
- API mismatch notes:
  - Polymarket market WebSocket connection/subscription did not return an event before timeout with the checked token.
  - CLOB market discovery did not yield an active accepting token in checked pages.
  - Details recorded in `docs/project_notes/api_mismatch_notes.md`.
- Manual:
  - Hand off execution evidence plus current diff to `验收区` for pass/fail review.
- Scope skipped:
  - No live trading, order placement, wallet/signing/credential path, marketability, paper fill, PnL, long-term storage schema, or Phase 1 signal rule change.

### 2026-07-06 - Phase 1 Accepted And Phase 2 Ready

- Goal: Record that Phase 1 execution and acceptance passed, then prepare the next data-capture slice.
- Changed:
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - Phase 2 continues with Python.
  - Phase 2 may add exactly one WebSocket client dependency if the current environment lacks one.
  - Phase 2 captures live market data only; paper fill and PnL stay in Phase 3.
- Scope skipped:
  - No implementation code changed by planning.
  - No live trading, wallet signing, paper fill, or profit calculation added to Phase 2.

### 2026-07-06 - Minimum Required Read Set Rule

- Goal: Reduce token waste from rereading unchanged docs across zones.
- Changed:
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - Task cards should list a minimum required read set.
  - Product, architecture, and implementation docs should be routed as on-demand reads when unchanged.
- Scope skipped:
  - No source code changed.
  - No phase deliverables changed.

### 2026-07-06 - Two-Hop Evidence Flow Rule

- Goal: Remove manual relay of execution evidence between `执行区` and `验收区`.
- Changed:
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decisions:
  - `执行区` writes execution evidence into `issues.md`.
  - `验收区` reads `Current Summary` plus the latest log block for the current task ID instead of requiring manual paste-through.
  - No zone should read all of `issues.md` by default.
- Scope skipped:
  - No source code changed.
  - No phase deliverables changed.

### 2026-07-06 - Phase 1 Signal Core Execution

- Goal: Implement the Phase 1 root signal module and smallest paper skeleton without marketability or execution leakage.
- Changed:
  - Added `polybot/__init__.py`
  - Added `polybot/signal.py`
  - Added `polybot/paper.py`
  - Updated `.gitignore`
- Verified:
  - `python3 -m polybot.signal`
  - `PYTHONPYCACHEPREFIX=/private/tmp/polybot-pycache python3 -m compileall -q polybot`
  - `rg -n "ask|depth|spread|Kelly|kelly|p_hat|balance|orderbook" polybot`
  - `rg -n "socket|requests|urllib|http|os\\.environ|getenv|Polymarket|api" polybot`
  - `rg -n "account|trade_edge" polybot`
- Manual:
  - Hand off execution evidence plus current diff to `验收区` for pass/fail review.
- Scope skipped:
  - No WebSocket, network/API access, live trading, order placement, marketability, Kelly, `p_hat`, optimizer, storage schema, or third-party dependency setup.

### 2026-07-06 - Phase 1 Runtime Decision

- Goal: Unblock `polybot-paper-phase-1-signal-core` after `执行区` correctly stopped on unresolved runtime.
- Changed:
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/key_facts.md`
  - Updated `docs/product_consensus/polymarket_paper_trader_v1.md`
  - Updated `docs/implementation-plan.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
  - Updated `docs/project_notes/issues.md`
- Planning decision:
  - Phase 1 uses Python standard library only, with no third-party dependencies and no network/API access.
- Scope skipped:
  - No source code created in planning.
  - Phase 2 dependency and API decisions remain deferred.

### 2026-07-06 - Polymarket Planning Hardening

- Goal: Tighten the PolyBot planning environment so `执行区` and `验收区` do not fill in unresolved decisions or duplicate each other.
- Changed:
  - Added `docs/product_consensus/polymarket_paper_trader_v1.md`
  - Added `docs/architecture.md`
  - Added `docs/implementation-plan.md`
  - Updated `AGENTS.md`
  - Updated `docs/project_notes/key_facts.md`
  - Updated `docs/project_notes/decisions.md`
  - Updated `docs/project_notes/zone_operating_model.md`
  - Updated `docs/project_notes/polymarket_paper_execution_tasks.md`
- Verified:
  - Planning docs now separate product consensus, architecture boundaries, phase gates, execution evidence, and acceptance input shapes
- Manual:
  - Next planning output should paste the paired execution and acceptance prompts directly from the task doc
- Scope Skipped:
  - No source code or runtime integration changes

### 2026-07-06 - Polymarket Paper Trading Task Plan

- Goal: Create an execution-zone task plan for the Polymarket 15m BTC paper trading simulator.
- Changed:
  - Added `docs/project_notes/polymarket_paper_execution_tasks.md`
- Planning decisions:
  - Keep the root signal logic separate from marketability checks and paper execution.
  - First build paper trading only; no live trading.
  - Use WebSocket-first market data, with REST only for startup/reconnect fallback.
  - Keep the first implementation small: no optimizer, no new signal rules, no multi-entry logic.
- Recommended execution order:
  - Phase 1: strategy core and paper skeleton
  - Phase 2: WebSocket data capture
  - Phase 3: marketability and paper fill
  - Use goal mode for each phase.

### 2026-07-05 - Zone Memory Bootstrap

- Goal: Set up a lean multi-zone collaboration baseline for this empty workspace.
- Changed:
  - Added `AGENTS.md`
  - Added `docs/project_notes/bugs.md`
  - Added `docs/project_notes/decisions.md`
  - Added `docs/project_notes/key_facts.md`
  - Added `docs/project_notes/issues.md`
  - Added `docs/project_notes/zone_operating_model.md`
  - Added `.gitignore`
- Verified:
  - Workspace was empty before bootstrap
  - Root context files and `zone-memory` references were read before writing
  - Git repository initialized on branch `main`
  - Four zone threads were created with opening prompts
- Manual:
  - Open any zone thread and continue from its role-specific prompt
- Scope skipped:
  - No product architecture, code scaffold, or dependency setup yet
