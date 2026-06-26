#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" || ! -f "$BACKUP_FILE" ]]; then
  echo "用法：bash scripts/restore.sh backups/mmn_backup_YYYYMMDD_HHMMSS.tar.gz"
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "未找到 .env，无法确认当前部署配置。"
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

tar -xzf "$BACKUP_FILE" -C "$TMP_DIR"
RESTORE_DATA="$(find "$TMP_DIR" -maxdepth 2 -type d -name data | head -n 1)"
if [[ -z "$RESTORE_DATA" ]]; then
  echo "备份文件中未找到 data 目录。"
  exit 1
fi

docker compose --env-file .env up -d mmn-app
docker compose --env-file .env exec -T mmn-app sh -lc 'rm -rf /app/data/*'
docker compose --env-file .env cp "$RESTORE_DATA/." mmn-app:/app/data
docker compose --env-file .env restart mmn-app

echo "恢复完成，应用已重启。"
