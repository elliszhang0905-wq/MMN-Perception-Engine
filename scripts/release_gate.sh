#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

NODE_BIN="${NODE_BINARY:-/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node}"
PORT="${MMN_PORT:-8765}"
URL="${MMN_URL:-http://127.0.0.1:${PORT}/}"
SERVER_PID=""

echo "MMN release gate: syntax checks"
"$NODE_BIN" --check app.js
python3 -m py_compile server.py

echo "MMN release gate:研发档案检查"
if rg -n "AI|ChatGPT|Codex|大模型辅助|AI生成|智能编写" "docs/研发档案"; then
  echo "研发档案包含禁用描述，请修正后再交付。" >&2
  exit 1
fi

changed_files="$(git diff --name-only HEAD || true)"
if echo "$changed_files" | rg -q "^(app\.js|index\.html|server\.py|style\.css|knowhow\.css|scripts/)"; then
  if ! echo "$changed_files" | rg -q "^docs/研发档案/.*\.md$"; then
    echo "本次包含功能或流程变更，但未发现研发档案更新。" >&2
    exit 1
  fi
fi

if ! curl -fsS "$URL" >/dev/null 2>&1; then
  echo "MMN release gate: 启动临时本地服务"
  python3 server.py >/tmp/mmn-release-gate-server.log 2>&1 &
  SERVER_PID="$!"
  for _ in {1..20}; do
    if curl -fsS "$URL" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "MMN release gate: browser checks"
MMN_URL="$URL" "$NODE_BIN" scripts/release_gate.js

echo "MMN release gate: passed"
