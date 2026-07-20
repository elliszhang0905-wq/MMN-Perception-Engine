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

echo "同步随版本发布的数据资产到统一持久化根目录。"
docker compose --env-file .env exec -T mmn-app mkdir -p /app/data/modules/product_evaluation /app/data/imports/raw/product_evaluation /app/data/dongchedi_sales /app/data/rag_training/dongchedi_sales /app/data/eval
for eval_fixture in data/eval/mmn_eval_seed_v0.1.jsonl data/eval/mmn_eval_seed_outputs_v0.1.jsonl; do
  if [[ -f "$eval_fixture" ]]; then
    docker compose --env-file .env cp "$eval_fixture" "mmn-app:/app/$eval_fixture"
  fi
done
if [[ -f data/modules/product_evaluation/e7x_product_evaluation_2026-06.json ]]; then
  docker compose --env-file .env cp data/modules/product_evaluation/e7x_product_evaluation_2026-06.json mmn-app:/app/data/modules/product_evaluation/e7x_product_evaluation_2026-06.json
fi
for source_asset in data/imports/raw/product_evaluation/*; do
  [[ -f "$source_asset" ]] || continue
  docker compose --env-file .env cp "$source_asset" "mmn-app:/app/data/imports/raw/product_evaluation/$(basename "$source_asset")"
done
if [[ -f data/sales_warning_demo_2026-06.json ]]; then
  docker compose --env-file .env cp data/sales_warning_demo_2026-06.json mmn-app:/app/data/sales_warning_demo_2026-06.json
fi
if [[ -f data/sales_warning_cycles.json ]]; then
  if docker compose --env-file .env exec -T mmn-app test -f /app/data/sales_warning_cycles.json; then
    echo "保留服务器已有车型上市日期，不用版本文件覆盖。"
  else
    docker compose --env-file .env cp data/sales_warning_cycles.json mmn-app:/app/data/sales_warning_cycles.json
  fi
fi
for observed_file in data/dongchedi_sales/sales_warning_observed_????-??.json; do
  [[ -f "$observed_file" ]] || continue
  docker compose --env-file .env cp "$observed_file" "mmn-app:/app/$observed_file"
done
if [[ -f data/dongchedi_sales/sales_warning_latest.json ]]; then
  docker compose --env-file .env cp data/dongchedi_sales/sales_warning_latest.json mmn-app:/app/data/dongchedi_sales/sales_warning_latest.json
fi
if [[ -f data/dongchedi_sales/sales_warning_history.json ]]; then
  docker compose --env-file .env cp data/dongchedi_sales/sales_warning_history.json mmn-app:/app/data/dongchedi_sales/sales_warning_history.json
fi
if [[ -f data/dongchedi_sales/latest_mmn_perception_feed.json ]]; then
  docker compose --env-file .env cp data/dongchedi_sales/latest_mmn_perception_feed.json mmn-app:/app/data/dongchedi_sales/latest_mmn_perception_feed.json
fi
if [[ -f data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl ]]; then
  docker compose --env-file .env cp data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl mmn-app:/app/data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl
fi

echo "版本数据资产同步完成，重启数据读取服务以重新解析规范路径。"
docker compose --env-file .env restart mmn-app mmn-scheduler
for _ in {1..30}; do
  APP_HEALTH="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' mmn-app 2>/dev/null || true)"
  if [[ "$APP_HEALTH" == "healthy" ]]; then
    break
  fi
  sleep 1
done
if [[ "${APP_HEALTH:-}" != "healthy" ]]; then
  echo "数据资产同步后 mmn-app 未恢复健康，停止发布。" >&2
  docker compose --env-file .env ps
  exit 1
fi
docker compose --env-file .env ps

echo "部署完成。测试地址：${MMN_PUBLIC_BASE_URL:-http://服务器公网IP:${MMN_HTTP_PORT:-8765}/}"
