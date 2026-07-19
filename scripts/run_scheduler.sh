#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/logs

echo "MMN scheduler started at $(date -Is)" | tee -a /app/logs/scheduler.log

post_json() {
  local path="$1"
  local payload="$2"
  python3 - "$path" "$payload" <<'PY'
import os
import sys
import urllib.request

path, payload = sys.argv[1:3]
port = os.environ.get("MMN_PORT", "8765")
url = f"http://mmn-app:{port}{path}"
req = urllib.request.Request(
    url,
    data=payload.encode("utf-8"),
    headers={"Content-Type": "application/json", "X-MMN-Scheduler": "1"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as resp:
    sys.stdout.write(resp.read().decode("utf-8", errors="replace"))
PY
}

while true; do
  current="$(TZ=Asia/Shanghai date '+%u %H:%M')"
  month_mark="$(TZ=Asia/Shanghai date '+%Y-%m')"
  day_time="$(TZ=Asia/Shanghai date '+%d %H:%M')"
	week_mark="$(TZ=Asia/Shanghai date '+%G-W%V')"
	day_mark="$(TZ=Asia/Shanghai date '+%Y-%m-%d')"
	if [[ "$current" == "2 ${MMN_GROUP_WEEKLY_REFRESH_TIME:-00:00}" ]]; then
	  marker="/app/logs/group_dashboard_weekly_${week_mark}.done"
	  if [[ ! -f "$marker" ]]; then
	    echo "weekly group dashboard refresh trigger $(date -Is)" | tee -a /app/logs/scheduler.log
	    post_json "/api/group-dashboard/refresh-weekly" '{}' >> /app/logs/scheduler.log 2>&1 && touch "$marker" || true
	  fi
	  sleep 70
	fi
	# Tuesday-Friday morning catch-up: the official report may not exist at Tuesday 00:00.
	if [[ "$(TZ=Asia/Shanghai date '+%u')" =~ ^(2|3|4|5)$ && "$(TZ=Asia/Shanghai date '+%H:%M')" == "${MMN_GROUP_WEEKLY_RETRY_TIME:-09:00}" ]]; then
	  marker="/app/logs/group_dashboard_weekly_retry_${day_mark}.done"
	  if [[ ! -f "$marker" ]]; then
	    echo "weekly group dashboard publication retry $(date -Is)" | tee -a /app/logs/scheduler.log
	    post_json "/api/group-dashboard/refresh-weekly" '{}' >> /app/logs/scheduler.log 2>&1 && touch "$marker" || true
	  fi
	  sleep 70
	fi
	day_of_month="$(TZ=Asia/Shanghai date '+%d')"
	if [[ "$day_of_month" =~ ^(15|16|17|18)$ && "$(TZ=Asia/Shanghai date '+%H:%M')" == "${MMN_SALES_WARNING_REFRESH_TIME:-09:15}" ]]; then
	  marker="/app/logs/sales_warning_monthly_check_${day_mark}.done"
	  if [[ ! -f "$marker" ]]; then
	    echo "monthly sales warning refresh check $(date -Is)" | tee -a /app/logs/scheduler.log
	    post_json "/api/group-dashboard/refresh-monthly-sales" '{}' >> /app/logs/scheduler.log 2>&1 && touch "$marker" || true
	  fi
	  sleep 70
	fi
	  if [[ "$current" == "7 23:00" ]]; then
	    echo "weekly founder archive trigger $(date -Is)" | tee -a /app/logs/scheduler.log
	    post_json "/api/founder-archives/run-weekly" '{"edition":"china"}' >> /app/logs/scheduler.log 2>&1 || true
	    echo "weekly blogger skill import scan trigger $(date -Is)" | tee -a /app/logs/scheduler.log
	    post_json "/api/blogger-skill/scan-imports" '{"edition":"china"}' >> /app/logs/scheduler.log 2>&1 || true
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
