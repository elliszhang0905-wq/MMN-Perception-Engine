#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs

echo "MMN scheduler started at $(date -Is)" | tee -a /app/logs/scheduler.log

while true; do
  current="$(TZ=Asia/Shanghai date '+%u %H:%M')"
  month_mark="$(TZ=Asia/Shanghai date '+%Y-%m')"
  day_time="$(TZ=Asia/Shanghai date '+%d %H:%M')"
  if [[ "$current" == "7 23:00" ]]; then
    echo "weekly founder archive trigger $(date -Is)" | tee -a /app/logs/scheduler.log
    curl -fsS -X POST "http://mmn-app:${MMN_PORT:-8765}/api/founder-archives/run-weekly" \
      -H "Content-Type: application/json" \
      -d '{"edition":"china"}' >> /app/logs/scheduler.log 2>&1 || true
    sleep 70
  fi
  if [[ "$day_time" == "${MMN_VEHICLE_ASSET_SYNC_DAY:-01} ${MMN_VEHICLE_ASSET_SYNC_TIME:-03:10}" ]]; then
    marker="/app/logs/vehicle_asset_sync_${month_mark}.done"
    if [[ ! -f "$marker" ]]; then
      echo "monthly MMN vehicle asset sync trigger $(date -Is)" | tee -a /app/logs/scheduler.log
      python3 scripts/sync_mmn_vehicle_assets.py >> /app/logs/scheduler.log 2>&1 && touch "$marker" || true
    fi
    sleep 70
  fi
  sleep 30
done
