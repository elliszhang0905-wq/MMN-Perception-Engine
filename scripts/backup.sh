#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "未找到 .env，无法确认当前部署配置。"
  exit 1
fi

set -a
source .env
set +a

BACKUP_DIR="${BACKUP_DIR:-backups}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
OUT="${BACKUP_DIR}/mmn_backup_${STAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

docker compose --env-file .env exec -T mmn-app sh -lc 'mkdir -p /tmp/mmn-backup && cp -a /app/data /tmp/mmn-backup/data'
docker compose --env-file .env cp mmn-app:/tmp/mmn-backup/data "${BACKUP_DIR}/data_${STAMP}"
tar -czf "$OUT" -C "$BACKUP_DIR" "data_${STAMP}"
rm -rf "${BACKUP_DIR}/data_${STAMP}"

echo "备份完成：$OUT"
