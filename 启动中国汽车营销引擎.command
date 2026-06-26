#!/bin/zsh
cd "$(dirname "$0")"
export MMN_HOST="${MMN_HOST:-localhost}"
export MMN_PORT="${MMN_PORT:-8765}"
export MMN_AUTO_OPEN_BROWSER="${MMN_AUTO_OPEN_BROWSER:-true}"
python3 server.py
