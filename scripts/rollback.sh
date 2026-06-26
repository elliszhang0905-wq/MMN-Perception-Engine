#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET_REF="${1:-}"

if [[ -z "$TARGET_REF" ]]; then
  echo "请指定要回滚的 Git 版本，例如：bash rollback.sh HEAD~1 或 bash rollback.sh v1.2.0"
  echo "最近版本："
  git --no-pager log --oneline -n 10
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "未找到 .env，无法执行回滚。"
  exit 1
fi

if [[ ! -d .git ]]; then
  echo "当前目录不是 Git 仓库，无法执行代码版本回滚。"
  exit 1
fi

mkdir -p backups logs

ENV_BACKUP="$(mktemp /tmp/mmn-env.XXXXXX)"
cp .env "$ENV_BACKUP"

echo "回滚前备份当前运行数据。"
if docker compose --env-file .env ps --services --filter status=running 2>/dev/null | grep -qx "mmn-app"; then
  bash scripts/backup.sh
fi

echo "切换代码版本：${TARGET_REF}"
git fetch --all --tags
git checkout --detach "$TARGET_REF"

cp "$ENV_BACKUP" .env
rm -f "$ENV_BACKUP"
echo ".env 已保留，不被回滚版本覆盖。"

echo "停止当前容器。"
docker compose --env-file .env down --remove-orphans

echo "构建并启动回滚版本。"
docker compose --env-file .env build
docker compose --env-file .env up -d
docker compose --env-file .env ps

echo "回滚完成。当前代码版本：$(git rev-parse --short HEAD)"
