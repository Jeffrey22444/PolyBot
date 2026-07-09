# PolyBot Operator Runbook

This runbook covers the current paper-only BTC 15m public path. It uses the
existing CLI directly with a repo-local YAML config. No background-process
installer or live-order path is required.

## Start A Paper Run

Recommended run directory convention:

```bash
RUN_DIR="runs/paper-btc-15m/$(TZ=Asia/Shanghai date +%Y-%m-%d)"
mkdir -p "$RUN_DIR"
```

Recommended copy-paste command:

```bash
./scripts/paper_btc_15m_launch.sh
```

Notes:

- The launcher is the normal daily command. It writes artifacts under the
  Beijing-date run directory, writes full logs, prints compact status lines in
  the Terminal, and retries after short normal exits.
- `--p-hat` is still caller-supplied. It is not a trained or inferred model.
- `configs/polymarket_paper_btc_15m.yaml` controls the observation window,
  threshold, stake fraction, `p_hat` filter, discovery, timing, capture,
  runtime, and operator-output defaults.
- Normal operation rolls by Beijing calendar day. `runtime.max_sessions` is a
  safety cap, not the normal run boundary.
- The default local ledger is `data/paper_trades.sqlite3`. It is a supplemental
  inspection file; JSON artifacts remain the source for run/session artifacts.
- Command-line flags such as `--paper-stake`, `--move-threshold-pct`, or
  `--no-p-hat-filter-enabled` override the YAML for that run.
- By default, stake is `current settled simulated equity * paper.stake_fraction`.
  With `initial_bankroll: 1000` and `stake_fraction: 0.05`, the first stake is
  `50`. `--paper-stake` pins a fixed manual override for that run.
- `--mode next` plus `--search-query "bitcoin up down 15m"` is the current
  calibrated public BTC 15m path.
- `runs/` is ignored by Git, so local artifacts stay out of commits by default.

During a run, Terminal stdout prints concise operator briefs with Beijing-time
prefixes. Full CLI output, including machine JSON and diagnostics, is still
kept in `runs/paper-btc-15m-logs/`.

```text
[2026-07-09 17:55:00 CST] [RUN] stake=equity*0.05 p_hat_filter=False
[2026-07-09 17:55:02 CST] [WATCH] 2026-07-09 18:00-18:15 CST
[2026-07-09 18:10:02 CST] [BET] DOWN stake=50.00 avg=0.82 shares=60.98 move=-0.31%
[2026-07-09 18:15:01 CST] [SETTLED] DOWN WIN pnl=+10.98 equity=1010.98
[2026-07-09 18:30:01 CST] [PENDING] awaiting_public_resolution
[2026-07-09 18:45:01 CST] [NO_BET] no_signal move=0.08%
```

Terminal output intentionally avoids `market_id`, raw orderbook payloads, raw
BTC ticks, token IDs, long slugs, full JSON, URLs, candidate snapshots, and raw
diagnostics.

## Safe Stop

If the process is running in the foreground, stop it with `Ctrl-C`.

After stopping, inspect the same `RUN_DIR`. Existing artifacts stay on disk,
including:

- `run_manifest.json`
- `status.json`
- `summary.json`
- `session_index.json`
- `heartbeat.jsonl`
- `dry_run_report.json`

The repo launcher retries after short normal exits. It is still not a daemon or
machine boot integration unless you explicitly use the launchd path.

## Close An Existing Run

Use this when a previous run already produced artifacts and you want to rebuild
result/resolution artifacts from that run without rerunning discovery, open
price capture, or paper execution.

```bash
SOURCE_RUN="runs/paper-btc-15m/<Beijing YYYY-MM-DD>"
CLOSE_RUN="runs/paper-btc-15m/$(date -u +%Y%m%dT%H%M%SZ)-close"

python3 -m polybot.e2e_dry_run \
  --close-existing-run-dir "$SOURCE_RUN" \
  --run-id phase22-close \
  --attempt-public-resolution \
  --run-dir "$CLOSE_RUN"
```

This is not automatic resume of interrupted public discovery. It only reuses an
existing run directory as the source for closing/inspection work.

## Inspect Status And Results

Set the run directory once:

```bash
RUN_DIR="runs/paper-btc-15m/<Beijing YYYY-MM-DD>"
```

Check manifest and current status:

```bash
python3 -m json.tool "$RUN_DIR/run_manifest.json"
python3 -m json.tool "$RUN_DIR/status.json"
```

Check aggregate outcome and per-session index:

```bash
python3 -m json.tool "$RUN_DIR/summary.json"
python3 -m json.tool "$RUN_DIR/session_index.json"
```

Check the local trade ledger:

```bash
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect("data/paper_trades.sqlite3")
conn.row_factory = sqlite3.Row
for row in conn.execute(
    "select market_id, market_start_time, open_price_source, side, result, paper_pnl, cumulative_pnl, equity_after, skip_reason from paper_trades order by market_start_time"
):
    print(dict(row))
PY
```

Ledger notes:

- One row is kept per `market_id` using upsert semantics.
- `result` is one of `WIN`, `LOSS`, `PENDING`, `SKIPPED`, or `NO_TRADE`.
- `initial_bankroll` defaults to `1000` in
  `configs/polymarket_paper_btc_15m.yaml`.
- `stake_fraction` defaults to `0.05`; only settled `WIN` and `LOSS` PnL
  changes simulated equity for the next default stake. `PENDING`, `SKIPPED`,
  and `NO_TRADE` rows do not change equity.
- If Polymarket public metadata provides an open/reference price, the ledger
  records `open_price_source=polymarket:<field>`. Otherwise the existing BTC
  capture path is used and recorded as
  `open_price_source=binance_btcusdt_fallback`.
- `p_hat` remains caller-supplied. It is not a model, training output, or
  inferred estimate.

Check the end-to-end report and recent heartbeat lines:

```bash
python3 -m json.tool "$RUN_DIR/dry_run_report.json"
tail -n 20 "$RUN_DIR/heartbeat.jsonl"
```

Quick file-presence check:

```bash
ls "$RUN_DIR"
```

What each file is for:

- `run_manifest.json`: top-level run metadata and artifact paths.
- `status.json`: latest process-local run status written by `polybot.long_run`.
- `summary.json`: aggregate closed/skipped counts, skipped reasons, and PnL.
- `session_index.json`: per-session status, skip reason, result path, and paper
  PnL.
- `heartbeat.jsonl`: ordered runtime heartbeat and resume/retry events.
- `dry_run_report.json`: full end-to-end report with config snapshot, stop
  reason, blockers, and step-by-step outcomes.

## How To Read Common States

Use `status.json`, `dry_run_report.json`, `summary.json`, and
`session_index.json` together.

### Running

- `status.json` shows `"status": "running"`.
- `heartbeat.jsonl` continues to grow with fresh timestamps.

### Stopped

- `status.json` shows `"status": "stopped"` or `"status": "interrupted"`.
- `run_manifest.json` typically ends at `"status": "stopped"` or
  `"status": "interrupted"`.
- `dry_run_report.json` keeps the final report for inspection.

### Blocked

Check `dry_run_report.json` first.

- A non-empty `blockers` list means the dry run hit a blocking error.
- Step reasons such as `public_discovery_blocked=...`,
  `runner_blocked=...`, or `public_resolution_blocked=...` point to the stage
  that failed.
- `status.json` may still end as `stopped`, so rely on `dry_run_report.json`
  for the actual blocking reason.

### Common Skip Reasons

- `no_valid_candidate`: discovery did not find one valid next session.
- `not_closed`: public resolution found the market but it is not closed yet, so
  final result stays pending.
- `non_positive_trade_edge`: a signal existed, but paper marketability rejected
  the trade edge.
- `missing_p_hat`: caller did not supply `--p-hat`, so marketability could not
  evaluate trade edge.
- `stale_open_price_record`: BTC open-price capture did not produce a fresh
  post-open reference price.
- `wait_to_open_budget_exceeded`: the session start was too far away for the
  configured wait budget.
- `wait_to_observation_budget_exceeded`: the observation window was too far away for the
  configured wait budget.
- `observation_window_missed`: the observation window was already over.
- `observation_window_no_signal`: no movement crossed the configured threshold
  before the market ended.

Helpful spot checks:

```bash
rg -n '"skip_reason"|final_stop_reason|blockers|status' "$RUN_DIR"/dry_run_report.json "$RUN_DIR"/summary.json "$RUN_DIR"/session_index.json "$RUN_DIR"/status.json
```

## What To Check First When Something Looks Wrong

1. `python3 -m json.tool "$RUN_DIR/dry_run_report.json"`
2. `python3 -m json.tool "$RUN_DIR/status.json"`
3. `python3 -m json.tool "$RUN_DIR/session_index.json"`
4. `tail -n 20 "$RUN_DIR/heartbeat.jsonl"`

Use that order because:

- `dry_run_report.json` shows the stage and the final stop reason.
- `status.json` shows the latest long-run state and last error.
- `session_index.json` shows whether each session closed, skipped, or stayed
  pending.
- `heartbeat.jsonl` shows timing, retries, and resume-skipped events.

## Resume / Continue Boundary

Current supported operator actions:

- inspect an existing run directory
- stop a foreground process and inspect its artifacts
- run `--close-existing-run-dir` against an existing run directory
- let the next normal run retry existing ledger `PENDING` markets from public
  metadata by `market_id`

Current Phase 22 boundary:

- do not claim automatic resume of interrupted public discovery/execution from
  the exact interruption point
- do not claim daemon/service restart behavior
- do not claim OS-level supervision

Those belong, if needed, to Phase 23 local process supervision rather than this
runbook.

## Parameter Quick Reference

- `--config`: YAML config path. Default operator config is
  `configs/polymarket_paper_btc_15m.yaml`.
- `--search-query`, `--mode`, `--max-pages`, `--limit`,
  `--lookahead-minutes`: discovery controls.
- `--max-sessions`, `--max-runtime-seconds`, `--retry-limit`,
  `--retry-backoff-seconds`, `--heartbeat-interval-seconds`: runtime controls.
- `--max-wait-to-open-seconds`, `--max-wait-to-observation-seconds`,
  `--max-open-price-delay-seconds`: timing controls.
- `--capture-seconds`, `--capture-limit`, `--observation-tick-seconds`,
  `--runner-seconds`: BTC/open-price and orderbook capture controls.
- `--paper-stake`: fixed manual paper stake override for a run.
- `--stake-fraction`: default stake fraction of current settled simulated
  equity when `--paper-stake` is not set. The YAML default is `0.05`.
- `--initial-bankroll`: local ledger bankroll baseline.
- `--ledger-path`: local SQLite ledger path. Defaults to
  `data/paper_trades.sqlite3`.
- `--p-hat`: caller-supplied win probability input for marketability.
- `--p-hat-filter-enabled` / `--no-p-hat-filter-enabled`: enable or disable
  the `p_hat` edge filter while keeping ask-depth tradability checks.
- `--observe-start-remaining-seconds`: start observing this many seconds before
  market end.
- `--move-threshold-pct`: root signal movement threshold.
- `--attempt-public-resolution`: try conservative public result closing after
  completed sessions.
- `--run-dir`: artifact directory for this run.

CLI reference checks:

```bash
python3 -m polybot.e2e_dry_run --help
python3 -m polybot.long_run --help
```
