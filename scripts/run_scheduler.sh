#!/usr/bin/env bash
set -euo pipefail

LOG_ROOT="${MMN_SCHEDULER_LOG_DIR:-/app/logs}"
mkdir -p "$LOG_ROOT"

echo "MMN scheduler started at $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"

post_json() {
  local path="$1"
  local payload="$2"
  python3 - "$path" "$payload" <<'PY'
import os
import sys
import time
import hashlib
import hmac
import json
import urllib.request

path, payload = sys.argv[1:3]
port = os.environ.get("MMN_PORT", "8765")
headers = {"Content-Type": "application/json"}
if os.environ.get("MMN_SCHEDULER_LOCAL_WEEKLY_ONLY") == "true":
    if path != "/api/group-dashboard/refresh-weekly":
        raise RuntimeError("local mode is restricted to weekly refresh")
    # Use the existing same-user loopback API policy. Never send a cloud secret
    # or a privileged scheduler-bypass header to the managed local service.
    origin = f"http://127.0.0.1:{int(port)}"
    url = origin + path
    headers["Origin"] = origin
else:
    url = f"http://mmn-app:{int(port)}{path}"
    secret = os.environ.get("MMN_SCHEDULER_SECRET", "")
    if not secret:
        raise RuntimeError("MMN_SCHEDULER_SECRET is required")
    timestamp = str(int(time.time()))
    message = f"POST\n{path}\n{timestamp}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    headers.update({"X-MMN-Scheduler-Timestamp": timestamp,
                    "X-MMN-Scheduler-Signature": signature})
req = urllib.request.Request(
    url,
    data=payload.encode("utf-8"),
    headers=headers,
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as resp:
    body = resp.read().decode("utf-8", errors="replace")
    print(body, flush=True)
    # HTTP success means the job ran, not that a new snapshot was published.
    if path == "/api/group-dashboard/refresh-weekly":
        response = json.loads(body)
        if response.get("ok") is not True or response.get("result", {}).get("status") != "published":
            sys.exit(1)
PY
}

run_weekly_refresh() {
  local marker="$1"
  # Atomic claim bounds retries across ticks/restarts/concurrent schedulers.
  # A failed/interrupted attempt waits for the next scheduled window.
  if [[ ! -f "$marker" ]] && mkdir "${marker%.done}.attempted" 2>/dev/null; then
    echo "weekly group dashboard refresh attempt $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"
    post_json "/api/group-dashboard/refresh-weekly" '{}' >> "${LOG_ROOT}/scheduler.log" 2>&1 && touch "$marker" || true
  fi
}

while true; do
  current="$(TZ=Asia/Shanghai date '+%u %H:%M')"
  month_mark="$(TZ=Asia/Shanghai date '+%Y-%m')"
  day_time="$(TZ=Asia/Shanghai date '+%d %H:%M')"
	week_mark="$(TZ=Asia/Shanghai date '+%G-W%V')"
	day_mark="$(TZ=Asia/Shanghai date '+%Y-%m-%d')"
	# Run after the due minute too, coalescing to the latest configured window.
	current_day="${current%% *}"
	current_time="${current#* }"
	weekly_time="${MMN_GROUP_WEEKLY_REFRESH_TIME:-00:00}"
	retry_time="${MMN_GROUP_WEEKLY_RETRY_TIME:-09:00}"
	if [[ "$current_day" == "2" && ( "$current" == "2 ${MMN_GROUP_WEEKLY_REFRESH_TIME:-00:00}" || "$current" > "2 ${MMN_GROUP_WEEKLY_REFRESH_TIME:-00:00}" ) && ( "$current_time" < "$retry_time" || "$weekly_time" > "$retry_time" ) ]]; then
	  run_weekly_refresh "${LOG_ROOT}/group_dashboard_weekly_${week_mark}.done"
	elif [[ "$current_day" =~ ^(2|3|4|5)$ && ( "$current_time" == "$retry_time" || "$current_time" > "$retry_time" ) ]]; then
	  run_weekly_refresh "${LOG_ROOT}/group_dashboard_weekly_retry_${day_mark}.done"
	fi
	# launchd invokes this local-only tick periodically; never run other jobs.
	if [[ "${MMN_SCHEDULER_LOCAL_WEEKLY_ONLY:-false}" == "true" ]]; then
	  exit 0
	fi
	day_of_month="$(TZ=Asia/Shanghai date '+%d')"
	if [[ "$day_of_month" =~ ^(15|16|17|18)$ && "$(TZ=Asia/Shanghai date '+%H:%M')" == "${MMN_SALES_WARNING_REFRESH_TIME:-09:15}" ]]; then
	  marker="${LOG_ROOT}/sales_warning_monthly_check_${day_mark}.done"
	  if [[ ! -f "$marker" ]]; then
	    echo "monthly sales warning refresh check $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"
	    post_json "/api/group-dashboard/refresh-monthly-sales" '{}' >> "${LOG_ROOT}/scheduler.log" 2>&1 && touch "$marker" || true
	  fi
	  sleep 70
	fi
	  if [[ "$current" == "7 23:00" ]]; then
	    echo "weekly founder archive trigger $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"
	    post_json "/api/founder-archives/run-weekly" '{"edition":"china"}' >> "${LOG_ROOT}/scheduler.log" 2>&1 || true
	    echo "weekly blogger skill import scan trigger $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"
	    post_json "/api/blogger-skill/scan-imports" '{"edition":"china"}' >> "${LOG_ROOT}/scheduler.log" 2>&1 || true
	    sleep 70
	  fi
  if [[ "$day_time" == "${MMN_VEHICLE_ASSET_SYNC_DAY:-01} ${MMN_VEHICLE_ASSET_SYNC_TIME:-03:10}" ]]; then
    marker="${LOG_ROOT}/vehicle_asset_sync_${month_mark}.done"
    if [[ ! -f "$marker" ]]; then
      echo "monthly MMN vehicle asset sync trigger $(date '+%Y-%m-%dT%H:%M:%S%z')" | tee -a "${LOG_ROOT}/scheduler.log"
      python3 scripts/sync_mmn_vehicle_assets.py >> "${LOG_ROOT}/scheduler.log" 2>&1 && touch "$marker" || true
    fi
    sleep 70
  fi
  sleep 30
done
