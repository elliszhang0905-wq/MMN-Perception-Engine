#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "未找到 .env。请先复制 .env.example 为 .env 并填写配置。"
  exit 1
fi

mkdir -p data backups logs

set -a
source .env
set +a

docker compose --env-file .env build
docker compose --env-file .env up -d
docker compose --env-file .env ps

echo "部署完成。测试地址：${MMN_PUBLIC_BASE_URL:-http://服务器公网IP:${MMN_HTTP_PORT:-8765}/}"
