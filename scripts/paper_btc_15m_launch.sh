#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/jeffrey/Documents/PolyBot"
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PATH
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="$REPO_DIR/runs/paper-btc-15m/$STAMP"
LOG_DIR="$REPO_DIR/runs/paper-btc-15m-logs"
LOG_FILE="$LOG_DIR/$STAMP.log"

mkdir -p "$RUN_DIR" "$LOG_DIR"
ln -sfn "$RUN_DIR" "$REPO_DIR/runs/paper-btc-15m/latest"
printf '%s\n' "$RUN_DIR" > "$REPO_DIR/runs/paper-btc-15m/latest_run_dir.txt"
printf '%s\n' "$LOG_FILE" > "$LOG_DIR/latest_log.txt"

cd "$REPO_DIR"
exec >>"$LOG_FILE" 2>&1
exec python3 -m polybot.e2e_dry_run \
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
