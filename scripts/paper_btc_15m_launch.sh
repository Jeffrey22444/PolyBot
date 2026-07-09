#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/jeffrey/Documents/PolyBot"
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PATH
LOG_DIR="$REPO_DIR/runs/paper-btc-15m-logs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_FILE="$LOG_DIR/$STAMP.log"
RESTART_DELAY_SECONDS="${POLYBOT_RESTART_DELAY_SECONDS:-60}"

mkdir -p "$LOG_DIR"
printf '%s\n' "$LOG_FILE" > "$LOG_DIR/latest_log.txt"

cd "$REPO_DIR"
trap 'printf "[%s] [STOP] user interrupted\n" "$(TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M:%S CST")" | tee -a "$LOG_FILE"; exit 130' INT TERM

while true; do
  BEIJING_DAY="$(TZ=Asia/Shanghai date +%Y-%m-%d)"
  RUN_DIR="$REPO_DIR/runs/paper-btc-15m/$BEIJING_DAY"
  mkdir -p "$RUN_DIR"
  ln -sfn "$RUN_DIR" "$REPO_DIR/runs/paper-btc-15m/latest"
  printf '%s\n' "$RUN_DIR" > "$REPO_DIR/runs/paper-btc-15m/latest_run_dir.txt"

  printf "[%s] [START] run_dir=%s log=%s\n" "$(TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M:%S CST")" "$RUN_DIR" "$LOG_FILE" | tee -a "$LOG_FILE"

  set +e
  python3 -m polybot.e2e_dry_run \
    --config "$REPO_DIR/configs/polymarket_paper_btc_15m.yaml" \
    --attempt-public-resolution \
    --run-dir "$RUN_DIR" 2>&1 | awk -v logfile="$LOG_FILE" '
      {
        print >> logfile
        fflush(logfile)
        if ($0 ~ /^\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} CST\] \[(START|RETRY|STOP|WATCH|OPEN|BET|NO_BET|SETTLED|PENDING)\]/) {
          print
          fflush()
        }
      }
    '
  status=${PIPESTATUS[0]}
  set -e

  if [ "$status" -eq 130 ] || [ "$status" -eq 143 ]; then
    printf "[%s] [STOP] exit_status=%s\n" "$(TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M:%S CST")" "$status" | tee -a "$LOG_FILE"
    exit "$status"
  fi

  printf "[%s] [RETRY] exit_status=%s next_try_in=%ss\n" "$(TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M:%S CST")" "$status" "$RESTART_DELAY_SECONDS" | tee -a "$LOG_FILE"
  sleep "$RESTART_DELAY_SECONDS"
done
