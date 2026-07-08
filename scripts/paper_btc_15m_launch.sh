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
  --config "$REPO_DIR/configs/polymarket_paper_btc_15m.yaml" \
  --attempt-public-resolution \
  --run-dir "$RUN_DIR"
