#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
PORT="${MMN_PORT:-8765}"
HOST="${MMN_HOST:-0.0.0.0}"
LOCAL_URL="http://127.0.0.1:${PORT}"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/local_mmn.log"
PID_FILE="${LOG_DIR}/local_mmn.pid"
WATCHDOG_PID_FILE="${LOG_DIR}/local_mmn_watchdog.pid"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"

is_healthy() {
  curl -fsS -m 3 "${LOCAL_URL}/api/health" >/dev/null 2>&1
}

has_active_local_jobs() {
  local health
  health=$(curl -fsS -m 3 "${LOCAL_URL}/api/health" 2>/dev/null || true)
  [[ -n "${health}" ]] || return 1
  HEALTH_PAYLOAD="${health}" python3 -c 'import json, os, sys; payload=json.loads(os.environ["HEALTH_PAYLOAD"]); sys.exit(0 if int(payload.get("activeLocalJobs", payload.get("activeSocialTrendJobs", 0)) or 0) > 0 else 1)'
}

server_pid() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true
}

server_cwd() {
  local pid
  pid=$(server_pid)
  [[ -n "${pid}" ]] || return 0
  lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1 || true
}

server_matches_project() {
  [[ "$(server_cwd)" == "${PROJECT_DIR}" ]]
}

watchdog_pid() {
  local pid
  pid=$(cat "${WATCHDOG_PID_FILE}" 2>/dev/null || true)
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    echo "${pid}"
  fi
  return 0
}

stop_foreign_server() {
  local pid cwd foreign_watchdog
  pid=$(server_pid)
  [[ -n "${pid}" ]] || return 0
  cwd=$(server_cwd)
  [[ "${cwd}" != "${PROJECT_DIR}" ]] || return 0

  if has_active_local_jobs; then
    echo "检测到 ${PORT} 端口由其他工作目录提供，且仍有本地任务运行；为保护任务数据，本次不切换服务。"
    return 1
  fi

  echo "检测到 ${PORT} 端口来自其他工作目录：${cwd:-未知}，正在切换到当前发布目录..."
  if [[ -n "${cwd}" && -f "${cwd}/logs/local_mmn_watchdog.pid" ]]; then
    foreign_watchdog=$(cat "${cwd}/logs/local_mmn_watchdog.pid" 2>/dev/null || true)
    if [[ -n "${foreign_watchdog}" ]] && kill -0 "${foreign_watchdog}" 2>/dev/null; then
      kill "${foreign_watchdog}" 2>/dev/null || true
    fi
  fi
  kill "${pid}" 2>/dev/null || true
  for _ in {1..20}; do
    [[ -z "$(server_pid)" ]] && return 0
    sleep 0.2
  done
  kill -9 "${pid}" 2>/dev/null || true
  [[ -z "$(server_pid)" ]]
}

backend_code_is_newer() {
  local pid
  pid=$(server_pid)
  [[ -n "${pid}" && -f "${PID_FILE}" ]] || return 1
  [[ "$(cat "${PID_FILE}" 2>/dev/null || true)" == "${pid}" ]] || return 0
  find . -type f -name '*.py' \
    ! -path './tests/*' \
    ! -path './tmp/*' \
    ! -path './output/*' \
    ! -path './.git/*' \
    ! -path './.venv/*' \
    -newer "${PID_FILE}" -print -quit 2>/dev/null | grep -q .
}

stop_stale_server() {
  local pid
  pid=$(server_pid)
  if [[ -n "${pid}" ]] && backend_code_is_newer; then
    if has_active_local_jobs; then
      echo "检测到本地任务正在运行，延后重启 MMN 本地服务。"
      return
    fi
    echo "检测到后端代码已更新，正在重启 MMN 本地服务..."
    kill "${pid}" 2>/dev/null || true
    for _ in {1..20}; do
      [[ -z "$(server_pid)" ]] && return
      sleep 0.2
    done
    kill -9 "${pid}" 2>/dev/null || true
  fi
  return 0
}

stop_stuck_server() {
  local pids watcher
  pids=$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    echo "检测到 ${PORT} 端口已有服务，正在确认是否为卡住的 MMN 服务..."
    if ! is_healthy; then
      echo "服务无响应，正在重启 MMN 本地服务..."
      watcher=$(watchdog_pid)
      if [[ -n "${watcher}" ]]; then
        kill "${watcher}" 2>/dev/null || true
        rm -f "${WATCHDOG_PID_FILE}"
      fi
      echo "${pids}" | xargs kill 2>/dev/null || true
      sleep 1
      pids=$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)
      if [[ -n "${pids}" ]]; then
        echo "${pids}" | xargs kill -9 2>/dev/null || true
      fi
    fi
  fi
  return 0
}

start_server() {
  stop_foreign_server
  stop_stale_server

  if is_healthy && server_matches_project; then
    echo "MMN 本地服务已可用：${LOCAL_URL}"
    return
  fi

  stop_stuck_server

  if ! is_healthy || ! server_matches_project; then
    if [[ -z "$(watchdog_pid)" ]]; then
      echo "正在启动 MMN 本地服务守护进程..."
      MMN_HOST="${HOST}" \
      MMN_PORT="${PORT}" \
      MMN_CLOUD_LOGIN_REQUIRED="false" \
      MMN_AUTO_OPEN_BROWSER="false" \
      screen -dmS mmn_local_watchdog zsh scripts/run_local_mmn_watchdog.sh
    else
      echo "MMN 守护进程已运行，正在等待服务恢复..."
    fi
  fi

  for _ in {1..30}; do
    if is_healthy && server_matches_project; then
      echo "MMN 本地服务启动成功：${LOCAL_URL}"
      return
    fi
    sleep 1
  done

  echo "MMN 本地服务启动失败，请查看日志：${LOG_FILE}"
  exit 1
}

start_server

if [[ "${MMN_AUTO_OPEN_BROWSER:-true}" == "true" ]]; then
  open "${LOCAL_URL}/"
fi

echo "你现在可以打开：${LOCAL_URL}/"
