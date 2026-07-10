#!/bin/zsh
set -euo pipefail

PROJECT_DIR="/Users/ellis/Documents/MMN汽车营销引擎/china-auto-marketing-engine"
PORT="${MMN_PORT:-8765}"
HOST="${MMN_HOST:-0.0.0.0}"
LOCAL_URL="http://127.0.0.1:${PORT}"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/local_mmn.log"
PID_FILE="${LOG_DIR}/local_mmn.pid"

mkdir -p "${LOG_DIR}"
cd "${PROJECT_DIR}"

is_healthy() {
  curl -fsS -m 3 "${LOCAL_URL}/api/health" >/dev/null 2>&1
}

server_pid() {
  lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1
}

backend_code_is_newer() {
  local pid
  pid=$(server_pid)
  [[ -n "${pid}" && -f "${PID_FILE}" ]] || return 1
  [[ "$(cat "${PID_FILE}" 2>/dev/null || true)" == "${pid}" ]] || return 0
  find server.py bf_factory -type f -name '*.py' -newer "${PID_FILE}" -print -quit 2>/dev/null | grep -q .
}

stop_stale_server() {
  local pid
  pid=$(server_pid)
  if [[ -n "${pid}" ]] && backend_code_is_newer; then
    echo "检测到后端代码已更新，正在重启 MMN 本地服务..."
    kill "${pid}" 2>/dev/null || true
    for _ in {1..20}; do
      [[ -z "$(server_pid)" ]] && return
      sleep 0.2
    done
    kill -9 "${pid}" 2>/dev/null || true
  fi
}

stop_stuck_server() {
  local pids
  pids=$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    echo "检测到 ${PORT} 端口已有服务，正在确认是否为卡住的 MMN 服务..."
    if ! is_healthy; then
      echo "服务无响应，正在重启 MMN 本地服务..."
      echo "${pids}" | xargs kill 2>/dev/null || true
      sleep 1
      pids=$(lsof -tiTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)
      if [[ -n "${pids}" ]]; then
        echo "${pids}" | xargs kill -9 2>/dev/null || true
      fi
    fi
  fi
}

start_server() {
  stop_stale_server

  if is_healthy; then
    echo "MMN 本地服务已可用：${LOCAL_URL}"
    return
  fi

  stop_stuck_server

  if ! is_healthy; then
    echo "正在启动 MMN 本地服务..."
    MMN_HOST="${HOST}" \
    MMN_PORT="${PORT}" \
    MMN_CLOUD_LOGIN_REQUIRED="false" \
    MMN_AUTO_OPEN_BROWSER="false" \
    nohup python3 server.py >>"${LOG_FILE}" 2>&1 &
    echo $! >"${PID_FILE}"
  fi

  for _ in {1..30}; do
    if is_healthy; then
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
