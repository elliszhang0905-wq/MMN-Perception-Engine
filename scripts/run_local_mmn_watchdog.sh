#!/bin/zsh
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

load_local_env() {
  local env_file common_git_dir primary_repo_dir
  local had_tikhub=${+TIKHUB_API_KEY} old_tikhub="${TIKHUB_API_KEY-}"
  local had_dashscope=${+DASHSCOPE_API_KEY} old_dashscope="${DASHSCOPE_API_KEY-}"
  local had_kimi=${+KIMI_API_KEY} old_kimi="${KIMI_API_KEY-}"
  local had_deepseek=${+DEEPSEEK_API_KEY} old_deepseek="${DEEPSEEK_API_KEY-}"
  local had_openai=${+OPENAI_API_KEY} old_openai="${OPENAI_API_KEY-}"
  local had_db_path=${+MMN_DB_PATH} old_db_path="${MMN_DB_PATH-}"
  local had_data_root=${+MMN_DATA_ROOT} old_data_root="${MMN_DATA_ROOT-}"
  local had_data_dir=${+MMN_DATA_DIR} old_data_dir="${MMN_DATA_DIR-}"
  local had_backup_root=${+MMN_BACKUP_ROOT} old_backup_root="${MMN_BACKUP_ROOT-}"
  local had_port=${+MMN_PORT} old_port="${MMN_PORT-}"
  local had_host=${+MMN_HOST} old_host="${MMN_HOST-}"

  env_file="${MMN_ENV_FILE:-}"
  if [[ -z "${env_file}" && -f "${PROJECT_DIR}/.env" ]]; then
    env_file="${PROJECT_DIR}/.env"
  elif [[ -z "${env_file}" ]]; then
    common_git_dir=$(git -C "${PROJECT_DIR}" rev-parse --git-common-dir 2>/dev/null || true)
    if [[ -n "${common_git_dir}" ]]; then
      [[ "${common_git_dir}" == /* ]] || common_git_dir="${PROJECT_DIR}/${common_git_dir}"
      primary_repo_dir="$(cd "$(dirname "${common_git_dir}")" 2>/dev/null && pwd -P || true)"
      [[ -f "${primary_repo_dir}/.env" ]] && env_file="${primary_repo_dir}/.env"
    fi
  fi
  [[ -n "${env_file}" && -f "${env_file}" ]] || return 0

  set +u
  set -a
  source "${env_file}"
  set +a
  set -u

  (( had_tikhub )) && export TIKHUB_API_KEY="${old_tikhub}"
  (( had_dashscope )) && export DASHSCOPE_API_KEY="${old_dashscope}"
  (( had_kimi )) && export KIMI_API_KEY="${old_kimi}"
  (( had_deepseek )) && export DEEPSEEK_API_KEY="${old_deepseek}"
  (( had_openai )) && export OPENAI_API_KEY="${old_openai}"
  (( had_db_path )) && export MMN_DB_PATH="${old_db_path}"
  (( had_data_root )) && export MMN_DATA_ROOT="${old_data_root}"
  (( had_data_dir )) && export MMN_DATA_DIR="${old_data_dir}"
  (( had_backup_root )) && export MMN_BACKUP_ROOT="${old_backup_root}"
  (( had_port )) && export MMN_PORT="${old_port}"
  (( had_host )) && export MMN_HOST="${old_host}"
  return 0
}

load_local_env

LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/local_mmn.log"
PID_FILE="${LOG_DIR}/local_mmn.pid"
WATCHDOG_PID_FILE="${LOG_DIR}/local_mmn_watchdog.pid"
WATCHDOG_LOCK_DIR="${LOG_DIR}/local_mmn_watchdog.lock"
child_pid=""
SOURCE_CHECK_SECONDS="${MMN_LOCAL_SOURCE_CHECK_SECONDS:-2}"
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

if ! mkdir "${WATCHDOG_LOCK_DIR}" 2>/dev/null; then
  lock_owner=$(cat "${WATCHDOG_LOCK_DIR}/pid" 2>/dev/null || true)
  if [[ -n "${lock_owner}" ]] && kill -0 "${lock_owner}" 2>/dev/null; then
    echo "MMN 本地守护进程已运行（PID ${lock_owner}）。" >>"${LOG_FILE}"
    exit 0
  fi
  rm -f "${WATCHDOG_LOCK_DIR}/pid"
  rmdir "${WATCHDOG_LOCK_DIR}" 2>/dev/null || true
  mkdir "${WATCHDOG_LOCK_DIR}"
fi
echo "$$" >"${WATCHDOG_LOCK_DIR}/pid"
echo "$$" >"${WATCHDOG_PID_FILE}"

cleanup() {
  if [[ -n "${child_pid}" ]]; then
    kill "${child_pid}" 2>/dev/null || true
  fi
  if [[ "$(cat "${WATCHDOG_PID_FILE}" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "${WATCHDOG_PID_FILE}"
  fi
  if [[ "$(cat "${WATCHDOG_LOCK_DIR}/pid" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "${WATCHDOG_LOCK_DIR}/pid"
    rmdir "${WATCHDOG_LOCK_DIR}" 2>/dev/null || true
  fi
}

shutdown() {
  cleanup
  trap - EXIT
  exit 0
}

trap shutdown TERM INT HUP
trap cleanup EXIT

backend_code_is_newer() {
  [[ -f "${PID_FILE}" ]] || return 1
  find . -type f -name '*.py' \
    ! -path './tests/*' \
    ! -path './tmp/*' \
    ! -path './output/*' \
    ! -path './.git/*' \
    ! -path './.venv/*' \
    -newer "${PID_FILE}" -print -quit 2>/dev/null | grep -q .
}

active_local_jobs() {
  local health
  health=$(curl -fsS -m 3 "http://127.0.0.1:${MMN_PORT:-8765}/api/health" 2>/dev/null || true)
  [[ -n "${health}" ]] || return 0
  HEALTH_PAYLOAD="${health}" "${PYTHON_BIN}" -c '
import json, os
payload = json.loads(os.environ["HEALTH_PAYLOAD"])
print(int(payload.get("activeLocalJobs", payload.get("activeSocialTrendJobs", 0)) or 0))
' 2>/dev/null || echo 1
}

while true; do
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动 MMN 本地服务" >>"${LOG_FILE}"
  MMN_HOST="${MMN_HOST:-0.0.0.0}" \
  MMN_PORT="${MMN_PORT:-8765}" \
  MMN_CLOUD_LOGIN_REQUIRED="${MMN_CLOUD_LOGIN_REQUIRED:-false}" \
  MMN_AUTO_OPEN_BROWSER="false" \
  "${PYTHON_BIN}" server.py >>"${LOG_FILE}" 2>&1 &
  child_pid=$!
  echo "${child_pid}" >"${PID_FILE}"
  while kill -0 "${child_pid}" 2>/dev/null; do
    sleep "${SOURCE_CHECK_SECONDS}"
    if backend_code_is_newer; then
      running_jobs=$(active_local_jobs)
      if [[ "${running_jobs:-1}" -gt 0 ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到本地代码更新，但有 ${running_jobs} 个任务正在运行，延后重启" >>"${LOG_FILE}"
        continue
      fi
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] 检测到本地后端代码更新，正在自动同步服务" >>"${LOG_FILE}"
      kill "${child_pid}" 2>/dev/null || true
      break
    fi
  done
  exit_code=0
  wait "${child_pid}" || exit_code=$?
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] MMN 本地服务退出（状态 ${exit_code}），2 秒后自动恢复" >>"${LOG_FILE}"
  if [[ "$(cat "${PID_FILE}" 2>/dev/null || true)" == "${child_pid}" ]]; then
    rm -f "${PID_FILE}"
  fi
  child_pid=""
  sleep 2
done
