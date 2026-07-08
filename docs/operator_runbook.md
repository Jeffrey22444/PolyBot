# PolyBot Operator Runbook

This runbook covers the current paper-only BTC 15m public path. It uses the
existing CLI directly with a repo-local YAML config. No background-process
installer or live-order path is required.

## Start A Paper Run

Recommended run directory convention:

```bash
RUN_DIR="runs/paper-btc-15m/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR"
```

Recommended copy-paste command:

```bash
python3 -m polybot.e2e_dry_run \
  --config configs/polymarket_paper_btc_15m.yaml \
  --attempt-public-resolution \
  --run-dir "$RUN_DIR"
```

Notes:

- `--p-hat` is still caller-supplied. It is not a trained or inferred model.
- `configs/polymarket_paper_btc_15m.yaml` controls the observation window,
  threshold, stake, `p_hat` filter, discovery, timing, capture, runtime, and
  operator-output defaults.
- The default local ledger is `data/paper_trades.sqlite3`. It is a supplemental
  inspection file; JSON artifacts remain the source for run/session artifacts.
- Command-line flags such as `--paper-stake`, `--move-threshold-pct`, or
  `--no-p-hat-filter-enabled` override the YAML for that run.
- `--mode next` plus `--search-query "bitcoin up down 15m"` is the current
  calibrated public BTC 15m path.
- `runs/` is ignored by Git, so local artifacts stay out of commits by default.

During a run, stdout prints compact operator briefs with Beijing-time prefixes.
Machine artifacts still keep their normal JSON/ISO timestamps.

```text
[2026-07-08 12:00:00 CST] [RUN_START] run_dir=... config=... max_sessions=... stake=... p_hat_filter=...
[2026-07-08 12:10:02 CST] [TRADE] market_id=... side=UP stake=9.0 ask=0.84 shares=10.7143 move=0.0521% rem=242
[2026-07-08 12:10:03 CST] [SKIP] market_id=... reason=non_positive_trade_edge move=0.0521% rem=242
[2026-07-08 12:15:01 CST] [RESULT] market_id=... side=UP winning_side=UP result=WIN pnl=+1.71 equity=1001.71 return=0.1710% win_rate=100.0000% settled=1
```

The terminal and ledger intentionally avoid raw orderbook payloads, raw BTC
ticks, token IDs, and long slugs.

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

Phase 22 does not add process-manager behavior. Do not assume restart, daemon,
or machine boot integration.

## Close An Existing Run

Use this when a previous run already produced artifacts and you want to rebuild
result/resolution artifacts from that run without rerunning discovery, open
price capture, or paper execution.

```bash
SOURCE_RUN="runs/paper-btc-15m/<UTC timestamp>"
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
RUN_DIR="runs/paper-btc-15m/<UTC timestamp>"
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
  final result stays pending/skipped.
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
- `--paper-stake`: fixed paper stake.
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
