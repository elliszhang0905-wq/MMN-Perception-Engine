#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

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
PORT="${MMN_PORT:-18765}"
URL="${MMN_URL:-http://localhost:${PORT}/}"
SERVER_PID=""

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  echo "未找到可执行的 Node.js，请安装 Node.js 或设置 NODE_BINARY。" >&2
  exit 1
fi

echo "MMN release gate: syntax checks"
"$NODE_BIN" --check app.js
"$NODE_BIN" --check bf-factory.js
"$NODE_BIN" tests/test_nsr_map.js
"$NODE_BIN" tests/test_data_first_cockpit_ui.js
"$NODE_BIN" tests/test_social_competitor_picker.js
"$NODE_BIN" tests/test_social_positive_benchmark.js
"$NODE_BIN" tests/test_social_risk_popover.js
"$NODE_BIN" tests/test_vertical_trend_label_layout.js
"$NODE_BIN" tests/test_douyin_creator_collector.js
"$NODE_BIN" tests/test_xhs_content_ranking_demo.js
"$NODE_BIN" tests/test_ensure_local_mmn.js
python3 -m py_compile server.py bf_factory/*.py
python3 -m unittest \
  tests.test_product_summary_import \
  tests.test_brand_penetration_module \
  tests.test_dongchedi_sales_freshness \
  tests.test_douyin_hot_entities \
  tests.test_social_trend_jobs \
  tests.test_social_trends -v

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

if ! curl -fsS "$URL" >/dev/null 2>&1; then
  echo "MMN release gate: 启动临时本地服务"
  MMN_PORT="$PORT" python3 server.py >/tmp/mmn-release-gate-server.log 2>&1 &
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
MMN_URL="$URL" "$NODE_BIN" scripts/release_gate_data_first.js

echo "MMN release gate: passed"
