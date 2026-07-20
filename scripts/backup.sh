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

docker compose --env-file .env exec -T mmn-app sh -lc 'rm -rf /tmp/mmn-backup && mkdir -p /tmp/mmn-backup && cp -a /app/data /tmp/mmn-backup/data && find /tmp/mmn-backup/data -type f -exec sha256sum {} \; | sort > /tmp/mmn-backup/manifest.sha256'
docker compose --env-file .env cp mmn-app:/tmp/mmn-backup/data "${BACKUP_DIR}/data_${STAMP}"
docker compose --env-file .env cp mmn-app:/tmp/mmn-backup/manifest.sha256 "${BACKUP_DIR}/manifest_${STAMP}.sha256"
tar -czf "$OUT" -C "$BACKUP_DIR" "data_${STAMP}" "manifest_${STAMP}.sha256"
rm -rf "${BACKUP_DIR}/data_${STAMP}"
shasum -a 256 "$OUT" > "${OUT}.sha256"
docker compose --env-file .env cp "$OUT" "mmn-app:/app/backups/$(basename "$OUT")"
docker compose --env-file .env cp "${OUT}.sha256" "mmn-app:/app/backups/$(basename "$OUT").sha256"
docker compose --env-file .env cp "${BACKUP_DIR}/manifest_${STAMP}.sha256" "mmn-app:/app/backups/manifest_${STAMP}.sha256"

echo "备份完成：$OUT（含文件清单与 SHA-256，副本已写入 /app/backups）"
