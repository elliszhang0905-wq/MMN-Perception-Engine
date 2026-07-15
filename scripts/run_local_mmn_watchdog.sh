#!/bin/zsh
set -u

PROJECT_DIR="/Users/ellis/Documents/MMN汽车营销引擎/china-auto-marketing-engine"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/local_mmn.log"
PID_FILE="${LOG_DIR}/local_mmn.pid"
WATCHDOG_PID_FILE="${LOG_DIR}/local_mmn_watchdog.pid"
child_pid=""
BUNDLED_PYTHON="/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [[ -x "${MMN_PYTHON:-}" ]]; then
  PYTHON_BIN="${MMN_PYTHON}"
elif [[ -x "${BUNDLED_PYTHON}" ]]; then
  PYTHON_BIN="${BUNDLED_PYTHON}"
else
  PYTHON_BIN="$(command -v python3)"
fi

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"
echo "$$" >"${WATCHDOG_PID_FILE}"

cleanup() {
  if [[ -n "${child_pid}" ]]; then
    kill "${child_pid}" 2>/dev/null || true
  fi
  if [[ "$(cat "${WATCHDOG_PID_FILE}" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "${WATCHDOG_PID_FILE}"
  fi
}
trap cleanup TERM INT EXIT

while true; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动 MMN 本地服务" >>"${LOG_FILE}"
  MMN_HOST="${MMN_HOST:-0.0.0.0}" \
  MMN_PORT="${MMN_PORT:-8765}" \
  MMN_CLOUD_LOGIN_REQUIRED="${MMN_CLOUD_LOGIN_REQUIRED:-false}" \
  MMN_AUTO_OPEN_BROWSER="false" \
  "${PYTHON_BIN}" server.py >>"${LOG_FILE}" 2>&1 &
  child_pid=$!
  echo "${child_pid}" >"${PID_FILE}"
  exit_code=0
  wait "${child_pid}" || exit_code=$?
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] MMN 本地服务退出（状态 ${exit_code}），2 秒后自动恢复" >>"${LOG_FILE}"
  if [[ "$(cat "${PID_FILE}" 2>/dev/null || true)" == "${child_pid}" ]]; then
    rm -f "${PID_FILE}"
  fi
  child_pid=""
  sleep 2
done
