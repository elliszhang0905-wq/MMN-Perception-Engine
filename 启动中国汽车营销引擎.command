#!/bin/zsh
cd "$(dirname "$0")"
if [ -x "/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]; then
  "/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" server.py
else
  python3 server.py
fi
