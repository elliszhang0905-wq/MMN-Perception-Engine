#!/bin/zsh
set -euo pipefail

PROJECT_DIR="${MMN_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
CRAWLER_DIR="${MMN_DCD_CRAWLER_DIR:-$PROJECT_DIR/../mmn-dcd-sales-crawler}"

if [ ! -f "$CRAWLER_DIR/scripts/install_monthly_schedule.py" ]; then
  echo "未找到 MMN 懂车帝采集器：$CRAWLER_DIR" >&2
  exit 1
fi

select_python() {
  local candidates=()
  [ -n "${PYTHON_BIN:-}" ] && candidates+=("$PYTHON_BIN")
  candidates+=(
    "$CRAWLER_DIR/.venv/bin/python3"
    "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  )
  local system_python
  system_python="$(command -v python3 2>/dev/null || true)"
  [ -n "$system_python" ] && candidates+=("$system_python")

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -x "$candidate" ] && "$candidate" -c 'import pydantic' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! PYTHON_BIN="$(select_python)"; then
  echo "未找到包含懂车帝采集依赖的 Python；请先在采集器中安装 requirements.txt" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$CRAWLER_DIR/scripts/install_monthly_schedule.py"
