#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME="/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies"

export PATH="$RUNTIME/node/bin:$RUNTIME/bin:$PATH"

cd "$ROOT_DIR"
pnpm ppt:build
pnpm ppt:marp
pnpm ppt:mermaid
"$RUNTIME/python/bin/python3" scripts/mmn_ppt_inspect.py output/ppt-agent/mmn-strategy-deck.pptx --out output/ppt-agent/pptx-inspection.json >/dev/null
