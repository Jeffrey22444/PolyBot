# Local Process Supervision

This is a Mac-local, user-level supervision path for the existing Phase 22
paper command. It is not live trading, cloud deployment, or a root/system
service. It does not change signal logic, marketability, fills, PnL,
resolution, artifact semantics, or runner behavior.

`p_hat` is still caller-supplied through `--p-hat 0.55`. It is not a trained,
inferred, smoothed, or backfilled model.

## What Starts

The repo-local launcher is:

```bash
/Users/jeffrey/Documents/PolyBot/scripts/paper_btc_15m_launch.sh
```

It creates:

- artifacts: `runs/paper-btc-15m/<Beijing YYYY-MM-DD>/`
- latest artifact pointer: `runs/paper-btc-15m/latest_run_dir.txt`
- stdout/stderr log files: `runs/paper-btc-15m-logs/<UTC timestamp>.log`
- latest log pointer: `runs/paper-btc-15m-logs/latest_log.txt`

When run in a foreground Terminal, it prints only concise operator lines there
and writes the full stdout/stderr stream to the log file. Then it `exec`s the
configured paper command:

```bash
python3 -m polybot.e2e_dry_run \
  --config "$REPO_DIR/configs/polymarket_paper_btc_15m.yaml" \
  --attempt-public-resolution \
  --run-dir "$RUN_DIR"
```

The YAML controls the final-300-second observation window, `0.15%` threshold,
default `5%` settled-equity paper stake, `p_hat` filter, discovery, timing,
capture, runtime, and operator brief output. The launcher still only starts the
existing CLI and keeps local logs.

Terminal output is limited to startup/retry/stop status plus `[WATCH]`,
`[OPEN]`, `[BET]`, `[NO_BET]`, `[SETTLED]`, and `[PENDING]` lines. The market
window is printed in ET while the timestamp prefix remains local Beijing time.
Full JSON, URLs, candidate snapshots, raw Chainlink payloads, raw debug BTC
captures, diagnostics, and detailed Python output remain in
`runs/paper-btc-15m-logs/<UTC timestamp>.log`.

Signal open and current prices use the Polymarket frontend Chainlink candle
surface and record `open_price_source=polymarket_chainlink` for accepted paper
entries. Binance fallback captures can remain in raw logs for debugging, but a
fallback-only/Binance-only price path is skipped and cannot trigger a signal or
paper entry.

By default, the paper stake is `current settled simulated equity *
paper.stake_fraction`; with initial equity `1000` and `stake_fraction: 0.05`,
the first stake is `50`. `--paper-stake` remains a manual fixed-stake override
if an operator intentionally adds it to a one-off command.

## One-Time Manual Install

The template is repo-local at:

```bash
/Users/jeffrey/Documents/PolyBot/docs/launchd/com.polybot.paper-btc-15m.plist
```

Do not edit system locations from automation. If you choose to install it
manually, copy exactly one file:

```bash
mkdir -p "$HOME/Library/LaunchAgents"
cp /Users/jeffrey/Documents/PolyBot/docs/launchd/com.polybot.paper-btc-15m.plist \
  "$HOME/Library/LaunchAgents/com.polybot.paper-btc-15m.plist"
```

This plist has `RunAtLoad` and `KeepAlive` set to `false`, so loading it does
not immediately start the bot and launchd will not automatically relaunch it
after exit. If those are changed to `true`, the bot can start when the agent is
loaded or restart after it exits; only do that when you want that behavior.

## Start

Start the supervised process:

```bash
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.polybot.paper-btc-15m.plist"
launchctl kickstart -k "gui/$(id -u)/com.polybot.paper-btc-15m"
```

Foreground fallback without launchd:

```bash
/Users/jeffrey/Documents/PolyBot/scripts/paper_btc_15m_launch.sh
```

## Stop

Stop and unload the user agent:

```bash
launchctl bootout "gui/$(id -u)/com.polybot.paper-btc-15m"
```

If it was started in the foreground fallback, stop it with `Ctrl-C`.

## Restart

Restart the already-loaded user agent:

```bash
launchctl kickstart -k "gui/$(id -u)/com.polybot.paper-btc-15m"
```

If the agent is not loaded, run the start commands again.

## Status

Check launchd state:

```bash
launchctl print "gui/$(id -u)/com.polybot.paper-btc-15m"
```

Check the latest artifact status:

```bash
RUN_DIR="$(cat /Users/jeffrey/Documents/PolyBot/runs/paper-btc-15m/latest_run_dir.txt)"
python3 -m json.tool "$RUN_DIR/status.json"
```

## Logs

Show the current stdout/stderr log:

```bash
LOG_FILE="$(cat /Users/jeffrey/Documents/PolyBot/runs/paper-btc-15m-logs/latest_log.txt)"
tail -n 100 "$LOG_FILE"
```

Follow it live:

```bash
tail -f "$LOG_FILE"
```

## Artifact Inspection

Use the same Phase 22 artifact path:

```bash
RUN_DIR="$(cat /Users/jeffrey/Documents/PolyBot/runs/paper-btc-15m/latest_run_dir.txt)"
ls "$RUN_DIR"
python3 -m json.tool "$RUN_DIR/run_manifest.json"
python3 -m json.tool "$RUN_DIR/status.json"
python3 -m json.tool "$RUN_DIR/summary.json"
python3 -m json.tool "$RUN_DIR/session_index.json"
python3 -m json.tool "$RUN_DIR/dry_run_report.json"
tail -n 20 "$RUN_DIR/heartbeat.jsonl"
```

The normal supervised command also retries existing ledger `PENDING` markets at
startup, after each session, and at final/interrupted close. Clear public
resolution metadata updates those rows to `WIN` or `LOSS`; unclear metadata
leaves them `PENDING`.

## Disable Supervision

Unload the user agent:

```bash
launchctl bootout "gui/$(id -u)/com.polybot.paper-btc-15m"
```

Then remove the one copied LaunchAgent file:

```bash
Remove-Item "$HOME/Library/LaunchAgents/com.polybot.paper-btc-15m.plist"
```

On macOS shell, the equivalent single-file delete is:

```bash
rm "$HOME/Library/LaunchAgents/com.polybot.paper-btc-15m.plist"
```

Do not bulk-delete `~/Library/LaunchAgents`.

To return to Phase 22 foreground operation, use the command in
`docs/operator_runbook.md` under "Start A Paper Run".
