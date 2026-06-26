#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs

echo "MMN scheduler started at $(date -Is)" | tee -a /app/logs/scheduler.log

while true; do
  current="$(TZ=Asia/Shanghai date '+%u %H:%M')"
  if [[ "$current" == "7 23:00" ]]; then
    echo "weekly founder archive trigger $(date -Is)" | tee -a /app/logs/scheduler.log
    curl -fsS -X POST "http://mmn-app:${MMN_PORT:-8765}/api/founder-archives/run-weekly" \
      -H "Content-Type: application/json" \
      -d '{"edition":"china"}' >> /app/logs/scheduler.log 2>&1 || true
    sleep 70
  fi
  sleep 30
done
