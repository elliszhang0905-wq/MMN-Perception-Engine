#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_ROOT="${MMN_DATA_ROOT:-${MMN_DATA_DIR:-${ROOT}/data}}"
BACKUP_ROOT="${MMN_BACKUP_ROOT:-${ROOT}/backups}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
DEST="${BACKUP_ROOT}/local_data_${STAMP}.tar.gz"

[[ -d "$DATA_ROOT" ]] || { echo "数据根目录不存在：$DATA_ROOT"; exit 1; }
mkdir -p "$BACKUP_ROOT"
MANIFEST="$(mktemp)"
trap 'rm -f "$MANIFEST"' EXIT
find "$DATA_ROOT" -type f -print0 | sort -z | xargs -0 shasum -a 256 > "$MANIFEST"
tar -czf "$DEST" -C "$DATA_ROOT" .
shasum -a 256 "$DEST" > "${DEST}.sha256"
cp "$MANIFEST" "${DEST}.manifest.sha256"
echo "本地数据备份完成：$DEST"
