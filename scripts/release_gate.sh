#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "${PYTHON_BINARY:-}" ]]; then
  PYTHON_BIN="$PYTHON_BINARY"
  if [[ "$PYTHON_BIN" != */* ]]; then
    PYTHON_BIN="$(command -v -- "$PYTHON_BIN" 2>/dev/null || true)"
  fi
else
  bundled_python="${HOME:-}/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12"
  if [[ -x "$bundled_python" ]]; then
    PYTHON_BIN="$bundled_python"
  else
    PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
  fi
fi

if [[ -n "${NODE_BINARY:-}" ]]; then
  NODE_BIN="$NODE_BINARY"
  if [[ "$NODE_BIN" != */* ]]; then
    NODE_BIN="$(command -v -- "$NODE_BIN" 2>/dev/null || true)"
  fi
else
  NODE_BIN="$(command -v node 2>/dev/null || true)"
fi
if [[ -z "$NODE_BIN" && -z "${NODE_BINARY:-}" ]]; then
  bundled_node="${HOME:-}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
  if [[ -x "$bundled_node" ]]; then
    NODE_BIN="$bundled_node"
  fi
fi

SERVER_PID=""
GATE_TMP_DIR=""

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  echo "未找到可执行的 Node.js，请安装 Node.js 或设置 NODE_BINARY。" >&2
  exit 1
fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
  echo "未找到可执行的 Python，请安装 Python 或设置 PYTHON_BINARY。" >&2
  exit 1
fi
if [[ -n "${MMN_URL:-}" ]]; then
  echo "release gate 不接受 MMN_URL：必须启动并验证自己的隔离服务。" >&2
  exit 1
fi
if [[ -n "${MMN_PORT:-}" ]]; then
  PORT="$MMN_PORT"
  if curl -fsS --max-time 1 "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    echo "端口 ${PORT} 已被占用；release gate 不会复用身份不明的服务。" >&2
    exit 1
  fi
else
  PORT="$("$PYTHON_BIN" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"
fi
URL="http://127.0.0.1:${PORT}/"

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ "$GATE_TMP_DIR" == /tmp/mmn-release-gate.* || "$GATE_TMP_DIR" == /private/tmp/mmn-release-gate.* ]]; then
    rm -rf -- "$GATE_TMP_DIR"
  fi
}
trap cleanup EXIT

echo "MMN release gate: prepare isolated data"
GATE_TMP_DIR="$(mktemp -d "/tmp/mmn-release-gate.XXXXXX")"
SOURCE_DATA_ROOT="${MMN_RELEASE_GATE_SOURCE_DATA_ROOT:-${MMN_DATA_ROOT:-$ROOT/data}}"
SOURCE_DB="${MMN_RELEASE_GATE_SOURCE_DB:-${MMN_DB_PATH:-$SOURCE_DATA_ROOT/commercial_demo.db}}"
GATE_SOURCE_DB="$GATE_TMP_DIR/commercial_demo.source.db"
GATE_TEST_DATA_DIR="$GATE_TMP_DIR/test-data"
GATE_BROWSER_DATA_DIR="$GATE_TMP_DIR/browser-data"
GATE_DB="$GATE_BROWSER_DATA_DIR/commercial_demo.db"
GATE_DB_PRE_INIT="$GATE_TMP_DIR/commercial_demo.pre-init.db"
GATE_DB_POST_INIT="$GATE_TMP_DIR/commercial_demo.post-init.db"
GATE_PYCACHE_DIR="$GATE_TMP_DIR/pycache"
GATE_OUTPUT_DIR="$GATE_TMP_DIR/output"
GATE_BACKUP_DIR="$GATE_TMP_DIR/backups"
SERVER_LOG="$GATE_TMP_DIR/server.log"

sqlite_backup_ro() {
  "$PYTHON_BIN" -c 'import sqlite3,sys; from pathlib import Path; uri=Path(sys.argv[1]).resolve().as_uri()+"?mode=ro"; source=sqlite3.connect(uri, uri=True); target=sqlite3.connect(sys.argv[2]); source.backup(target); target.close(); source.close()' "$1" "$2"
}

clone_sqlite() {
  if ! cp -c "$1" "$2" 2>/dev/null; then
    sqlite_backup_ro "$1" "$2"
  fi
}

copy_non_database_data() {
  mkdir -p "$2"
  rsync -a \
    --exclude '*.db' \
    --exclude '*.db-*' \
    --exclude '*.sqlite' \
    --exclude '*.sqlite-*' \
    "$1/" "$2/"
}

snapshot_worktree() {
  git diff --binary HEAD >"$1.tracked"
  : >"$1.untracked"
  while IFS= read -r -d '' untracked_file; do
    shasum -a 256 "$untracked_file" >>"$1.untracked"
  done < <(git -c core.quotePath=false ls-files --others --exclude-standard -z)
}

if [[ ! -d "$SOURCE_DATA_ROOT" ]]; then
  echo "release gate 数据目录源不存在：$SOURCE_DATA_ROOT" >&2
  exit 1
fi
if [[ ! -f "$SOURCE_DB" ]]; then
  echo "release gate 数据库源不存在：$SOURCE_DB" >&2
  exit 1
fi
mkdir -p "$GATE_PYCACHE_DIR" "$GATE_OUTPUT_DIR" "$GATE_BACKUP_DIR"
sqlite_backup_ro "$SOURCE_DB" "$GATE_SOURCE_DB"
copy_non_database_data "$SOURCE_DATA_ROOT" "$GATE_TEST_DATA_DIR"
copy_non_database_data "$SOURCE_DATA_ROOT" "$GATE_BROWSER_DATA_DIR"
clone_sqlite "$GATE_SOURCE_DB" "$GATE_TEST_DATA_DIR/commercial_demo.db"
clone_sqlite "$GATE_SOURCE_DB" "$GATE_DB"
clone_sqlite "$GATE_SOURCE_DB" "$GATE_DB_PRE_INIT"
"$PYTHON_BIN" scripts/compare_sqlite_logical.py "$SOURCE_DB" "$GATE_SOURCE_DB"
snapshot_worktree "$GATE_TMP_DIR/worktree.before"

export MMN_DATA_ROOT="$GATE_TEST_DATA_DIR"
export MMN_DB_PATH="$GATE_TEST_DATA_DIR/commercial_demo.db"
export MMN_BACKUP_ROOT="$GATE_BACKUP_DIR"
export MMN_OUTPUT_ROOT="$GATE_OUTPUT_DIR"
export MMN_AUTO_OPEN_BROWSER=false
export PYTHONPYCACHEPREFIX="$GATE_PYCACHE_DIR"

echo "MMN release gate: runtime"
"$NODE_BIN" --version
"$PYTHON_BIN" --version

echo "MMN release gate: syntax checks"
"$NODE_BIN" --check app.js
"$NODE_BIN" --check legacy-product-evaluation.js
"$NODE_BIN" --check bf-factory.js
"$NODE_BIN" --check group-dashboard.js
"$NODE_BIN" --check lead-dashboard.js
"$NODE_BIN" --check vehicle-decision.js
"$NODE_BIN" --check t-cycle.js
"$NODE_BIN" --check sales-warning-cycle-context.js
"$NODE_BIN" --check scripts/release_gate_all_surfaces.js

while IFS= read -r test_file; do
  "$NODE_BIN" "$test_file"
done < <(find tests -maxdepth 1 \( -name 'test_*.js' -o -name 'test_*.mjs' \) -print | sort)

while IFS= read -r python_file; do
  "$PYTHON_BIN" -m py_compile "$python_file"
done < <(git ls-files '*.py' | sort)

echo "MMN release gate: complete isolated Python suite"
mkdir -p "$GATE_TMP_DIR/python-dbs"
while IFS= read -r test_file; do
  test_module="${test_file%.py}"
  test_module="${test_module//\//.}"
  module_db="$GATE_TMP_DIR/python-dbs/${test_module//./_}.db"
  clone_sqlite "$GATE_SOURCE_DB" "$module_db"
  MMN_DB_PATH="$module_db" "$PYTHON_BIN" -m unittest "$test_module" -q
done < <(find tests -maxdepth 1 -name 'test_*.py' -print | sort)

echo "MMN release gate: current-state contract"
"$NODE_BIN" scripts/check_mmn_state.mjs
"$NODE_BIN" tests/test_check_mmn_state.mjs

echo "MMN release gate:研发档案检查"
if rg -n "AI|ChatGPT|Codex|大模型辅助|AI生成|智能编写" "docs/研发档案"; then
  echo "研发档案包含禁用描述，请修正后再交付。" >&2
  exit 1
fi

changed_files="$({ git -c core.quotePath=false diff --name-only HEAD || true; git -c core.quotePath=false ls-files --others --exclude-standard || true; } | sort -u)"
if echo "$changed_files" | rg -q "^(app\.js|index\.html|server\.py|style\.css|knowhow\.css|scripts/)"; then
  if ! echo "$changed_files" | rg -q "^docs/研发档案/.*\.md$"; then
    echo "本次包含功能或流程变更，但未发现研发档案更新。" >&2
    exit 1
  fi
fi

echo "MMN release gate: start dedicated local service"
MMN_DATA_ROOT="$GATE_BROWSER_DATA_DIR" \
MMN_DB_PATH="$GATE_DB" \
MMN_OUTPUT_ROOT="$GATE_OUTPUT_DIR" \
MMN_AUTO_OPEN_BROWSER=false \
MMN_PORT="$PORT" \
"$PYTHON_BIN" server.py >"$SERVER_LOG" 2>&1 &
SERVER_PID="$!"
for _ in {1..40}; do
  if curl -fsS --max-time 2 "$URL" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    echo "隔离服务启动失败：" >&2
    tail -80 "$SERVER_LOG" >&2
    exit 1
  fi
  sleep 0.5
done
if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
  echo "隔离服务进程已退出，拒绝复用端口上的其他响应。" >&2
  tail -80 "$SERVER_LOG" >&2
  exit 1
fi
if ! curl -fsS --max-time 2 "$URL" >/dev/null 2>&1; then
  echo "隔离服务未在预期端口就绪：$URL" >&2
  tail -80 "$SERVER_LOG" >&2
  exit 1
fi
EXPECTED_VERSION="$("$PYTHON_BIN" -c 'import ast,pathlib; tree=ast.parse(pathlib.Path("server.py").read_text(encoding="utf-8")); print(next(node.value.value for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "APP_VERSION_CODE" for target in node.targets) and isinstance(node.value, ast.Constant)))')"
HEALTH_JSON="$(curl -fsS --max-time 2 "${URL}api/health")"
HEALTH_JSON="$HEALTH_JSON" EXPECTED_VERSION="$EXPECTED_VERSION" "$PYTHON_BIN" -c 'import json,os; payload=json.loads(os.environ["HEALTH_JSON"]); actual=payload.get("versionCode"); expected=os.environ["EXPECTED_VERSION"]; assert actual == expected, f"服务版本不一致：expected={expected}, actual={actual}"'
sqlite_backup_ro "$GATE_DB" "$GATE_DB_POST_INIT"
echo "MMN release gate: startup data zero-drift"
"$PYTHON_BIN" scripts/compare_sqlite_logical.py "$GATE_DB_PRE_INIT" "$GATE_DB_POST_INIT"

echo "MMN release gate: browser checks"
MMN_URL="$URL" "$NODE_BIN" scripts/release_gate_data_first.js
MMN_URL="$URL" "$NODE_BIN" scripts/release_gate_all_surfaces.js

echo "MMN release gate: browser data zero-drift"
"$PYTHON_BIN" -c 'import sqlite3,sys; from pathlib import Path; uri=Path(sys.argv[1]).resolve().as_uri()+"?mode=ro"; conn=sqlite3.connect(uri, uri=True); result=conn.execute("pragma quick_check").fetchone()[0]; conn.close(); print(result); raise SystemExit(0 if result == "ok" else 1)' "$GATE_DB"
"$PYTHON_BIN" scripts/compare_sqlite_logical.py "$GATE_DB_POST_INIT" "$GATE_DB"

echo "MMN release gate: source and worktree zero-drift"
"$PYTHON_BIN" scripts/compare_sqlite_logical.py "$SOURCE_DB" "$GATE_SOURCE_DB"
snapshot_worktree "$GATE_TMP_DIR/worktree.after"
if ! cmp -s "$GATE_TMP_DIR/worktree.before.tracked" "$GATE_TMP_DIR/worktree.after.tracked" || \
   ! cmp -s "$GATE_TMP_DIR/worktree.before.untracked" "$GATE_TMP_DIR/worktree.after.untracked"; then
  echo "release gate 在工作树中产生了文件变化。" >&2
  diff -u "$GATE_TMP_DIR/worktree.before.untracked" "$GATE_TMP_DIR/worktree.after.untracked" >&2 || true
  exit 1
fi

echo "MMN release gate: passed"
