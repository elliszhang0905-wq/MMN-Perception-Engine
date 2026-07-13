#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "未找到 .env。请先复制 .env.example 为 .env 并填写配置。"
  exit 1
fi

mkdir -p data backups logs

BRANCH="${MMN_DEPLOY_BRANCH:-main}"
SKIP_GIT_PULL="${MMN_SKIP_GIT_PULL:-false}"

if [[ -d .git && "$SKIP_GIT_PULL" != "true" ]]; then
  ENV_BACKUP="$(mktemp /tmp/mmn-env.XXXXXX)"
  cp .env "$ENV_BACKUP"

  echo "从 GitHub 拉取最新代码：${BRANCH}"
  git fetch origin "$BRANCH"
  git pull --ff-only origin "$BRANCH"

  cp "$ENV_BACKUP" .env
  rm -f "$ENV_BACKUP"
  echo ".env 已保留，不被 GitHub 代码覆盖。"
fi

set -a
source .env
set +a

if docker compose --env-file .env ps --services --filter status=running 2>/dev/null | grep -qx "mmn-app"; then
  echo "发布前备份当前运行数据。"
  bash scripts/backup.sh
fi

echo "停止旧版本容器。"
docker compose --env-file .env down --remove-orphans

echo "重新构建镜像。"
docker compose --env-file .env build

echo "启动新版本服务。"
docker compose --env-file .env up -d

echo "同步随版本发布的销量与 RAG 数据资产到持久化卷。"
docker compose --env-file .env exec -T mmn-app mkdir -p /app/data/dongchedi_sales /app/data/rag_training/dongchedi_sales
if [[ -f data/dongchedi_sales/latest_mmn_perception_feed.json ]]; then
  docker compose --env-file .env cp data/dongchedi_sales/latest_mmn_perception_feed.json mmn-app:/app/data/dongchedi_sales/latest_mmn_perception_feed.json
fi
if [[ -f data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl ]]; then
  docker compose --env-file .env cp data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl mmn-app:/app/data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl
fi
docker compose --env-file .env ps

echo "部署完成。测试地址：${MMN_PUBLIC_BASE_URL:-http://服务器公网IP:${MMN_HTTP_PORT:-8765}/}"
