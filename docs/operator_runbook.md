# PolyBot Operator Runbook

This runbook covers the current paper-only BTC 15m public path. It uses the
existing CLI directly. No config wrapper, background-process installer, or
live-order path is required for Phase 22.

## Start A Paper Run

Recommended run directory convention:

```bash
RUN_DIR="runs/paper-btc-15m/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN_DIR"
```

Recommended copy-paste command:

```bash
python3 -m polybot.e2e_dry_run \
  --max-sessions 96 \
  --max-runtime-seconds 90000 \
  --paper-stake 9 \
  --p-hat 0.55 \
  --capture-seconds 8 \
  --capture-limit 5 \
  --runner-seconds 8 \
  --heartbeat-interval-seconds 30 \
  --retry-limit 1 \
  --retry-backoff-seconds 5 \
  --search-query "bitcoin up down 15m" \
  --mode next \
  --max-pages 10 \
  --limit 100 \
  --lookahead-minutes 90 \
  --max-wait-to-open-seconds 900 \
  --max-wait-to-entry-seconds 900 \
  --entry-window-tolerance-seconds 3 \
  --max-open-price-delay-seconds 5 \
  --attempt-public-resolution \
  --run-dir "$RUN_DIR"
```

Notes:

- `--p-hat` is still caller-supplied. It is not a trained or inferred model.
- `--mode next` plus `--search-query "bitcoin up down 15m"` is the current
  calibrated public BTC 15m path.
- `runs/` is ignored by Git, so local artifacts stay out of commits by default.

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
- `wait_to_entry_budget_exceeded`: the entry window was too far away for the
  configured wait budget.
- `entry_window_missed`: the entry point was missed or reached too late.

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

- `--search-query`: public discovery query; current BTC 15m path uses
  `"bitcoin up down 15m"`.
- `--mode`: session selection mode; use `next` for the current calibrated path.
- `--max-sessions`: upper bound on processed sessions in one run.
- `--max-runtime-seconds`: upper bound on wall-clock runtime for one run.
- `--max-wait-to-open-seconds`: wait budget before market open.
- `--max-wait-to-entry-seconds`: wait budget before entry timing.
- `--entry-window-tolerance-seconds`: lateness tolerance around entry timing.
- `--capture-seconds`: BTC reference capture duration.
- `--capture-limit`: max BTC reference records kept for open-price selection.
- `--runner-seconds`: paper runner duration once entry starts.
- `--heartbeat-interval-seconds`: heartbeat frequency for local status output.
- `--retry-limit`: recoverable retry count for process-local long-run handling.
- `--retry-backoff-seconds`: pause between recoverable retries.
- `--paper-stake`: fixed paper stake.
- `--p-hat`: caller-supplied win probability input for marketability.
- `--entry-remain-seconds`: allowed entry offsets before market end, such as
  `180,240`.
- `--move-threshold-pct`: root signal movement threshold.
- `--attempt-public-resolution`: try conservative public result closing after
  completed sessions.
- `--run-dir`: artifact directory for this run.

CLI reference checks:

```bash
python3 -m polybot.e2e_dry_run --help
python3 -m polybot.long_run --help
```
