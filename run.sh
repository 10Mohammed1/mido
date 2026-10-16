#!/usr/bin/env bash
# ── Mido keep-alive supervisor ─────────────────────────────────────────────
# Restarts the userbot automatically if it ever dies.  Run detached:
#     setsid nohup ./run.sh >/dev/null 2>&1 &
cd /home/medo/Downloads/zz/ZThon || exit 1
export PYTHONUNBUFFERED=1
export TZ="Africa/Cairo"
LOG="${ZTHON_LOG:-/tmp/opencode/zthon_run3.log}"

: > "$LOG"
while true; do
    echo "===== $(date '+%F %T') :: starting zira =====" >> "$LOG"
    python3 -u -m zira >> "$LOG" 2>&1
    code=$?
    echo "===== $(date '+%F %T') :: zira exited (code=$code), restarting in 20s =====" >> "$LOG"
    sleep 20
done
