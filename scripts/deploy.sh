#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "未找到 .env。请先复制 .env.example 为 .env 并填写配置。"
  exit 1
fi

mkdir -p data backups logs deploy/nginx-runtime
cp deploy/nginx.conf deploy/nginx-runtime/default.conf

BRANCH="${MMN_DEPLOY_BRANCH:-main}"
SKIP_GIT_PULL="${MMN_SKIP_GIT_PULL:-false}"
DEPLOY_LOCK_DIR="${MMN_DEPLOY_LOCK_DIR:-logs/.deploy.lock}"
MIN_FREE_MB="${MMN_DEPLOY_MIN_FREE_MB:-4096}"
BUILD_TIMEOUT_SECONDS="${MMN_DEPLOY_BUILD_TIMEOUT_SECONDS:-1200}"

release_lock() {
  if [[ -n "${NGINX_BASE_CONFIG:-}" ]] && [[ -f "$NGINX_BASE_CONFIG" ]]; then
    rm -f "$NGINX_BASE_CONFIG"
  fi
  if [[ -f "$DEPLOY_LOCK_DIR/pid" ]] && [[ "$(cat "$DEPLOY_LOCK_DIR/pid" 2>/dev/null || true)" == "$$" ]]; then
    rm -f "$DEPLOY_LOCK_DIR/pid"
    rmdir "$DEPLOY_LOCK_DIR" 2>/dev/null || true
  fi
}

acquire_lock() {
  if mkdir "$DEPLOY_LOCK_DIR" 2>/dev/null; then
    printf '%s\n' "$$" > "$DEPLOY_LOCK_DIR/pid"
    trap release_lock EXIT
    return
  fi

  local holder_pid=""
  holder_pid="$(cat "$DEPLOY_LOCK_DIR/pid" 2>/dev/null || true)"
  if [[ "$holder_pid" =~ ^[0-9]+$ ]] && kill -0 "$holder_pid" 2>/dev/null; then
    echo "已有发布任务运行中（PID ${holder_pid}），本次发布停止。"
    exit 1
  fi

  echo "发现失效的发布锁，安全清理后重试。"
  rm -f "$DEPLOY_LOCK_DIR/pid"
  rmdir "$DEPLOY_LOCK_DIR" 2>/dev/null || true
  mkdir "$DEPLOY_LOCK_DIR"
  printf '%s\n' "$$" > "$DEPLOY_LOCK_DIR/pid"
  trap release_lock EXIT
}

available_disk_mb() {
  df -Pk "$ROOT" | awk 'NR == 2 {printf "%d\n", $4 / 1024}'
}

ensure_build_capacity() {
  local available_mb
  available_mb="$(available_disk_mb)"
  if (( available_mb >= MIN_FREE_MB )); then
    echo "发布磁盘预检通过：可用 ${available_mb}MB，要求至少 ${MIN_FREE_MB}MB。"
    return
  fi

  echo "可用空间 ${available_mb}MB 低于发布下限 ${MIN_FREE_MB}MB，先清理无用构建缓存。"
  docker builder prune --all --force
  available_mb="$(available_disk_mb)"
  if (( available_mb < MIN_FREE_MB )); then
    echo "清理后可用空间仍只有 ${available_mb}MB；旧版本保持在线，本次发布停止。" >&2
    exit 1
  fi
  echo "清理后磁盘预检通过：可用 ${available_mb}MB。"
}

compose() {
  docker compose --env-file .env "$@"
}

wait_for_app_health() {
  local attempts="${1:-60}"
  local app_health=""
  for ((i = 1; i <= attempts; i += 1)); do
    app_health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' mmn-app 2>/dev/null || true)"
    if [[ "$app_health" == "healthy" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_web_health() {
  local attempts="${1:-30}"
  for ((i = 1; i <= attempts; i += 1)); do
    if compose exec -T mmn-web wget -qO- http://127.0.0.1/api/health >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_container_health() {
  local container_name="$1"
  local attempts="${2:-120}"
  local container_health=""
  for ((i = 1; i <= attempts; i += 1)); do
    container_health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_name" 2>/dev/null || true)"
    if [[ "$container_health" == "healthy" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

nginx_worker_pids() {
  local master_pid=""
  master_pid="$(docker inspect --format '{{.State.Pid}}' mmn-web)"
  docker top mmn-web -eo pid,ppid,comm \
    | awk -v master_pid="$master_pid" 'NR > 1 && $2 == master_pid && $3 == "nginx" {print $1}'
}

wait_for_nginx_workers_to_drain() {
  local worker_pids="$1"
  local attempts="${2:-330}"
  local pending=""
  local pid=""
  for ((i = 1; i <= attempts; i += 1)); do
    pending=""
    for pid in $worker_pids; do
      if kill -0 "$pid" 2>/dev/null; then
        pending="${pending} ${pid}"
      fi
    done
    if [[ -z "$pending" ]]; then
      return 0
    fi
    sleep 1
  done
  echo "旧 Nginx 工作进程未在 ${attempts} 秒内完成请求排空：${pending}" >&2
  return 1
}

route_web_to() {
  local upstream_name="$1"
  local previous_worker_pids=""
  local routed_config=""
  previous_worker_pids="$(nginx_worker_pids)"
  routed_config="$(mktemp /tmp/mmn-nginx-route.XXXXXX)"
  sed "s#http://mmn-app:8765#http://${upstream_name}:8765#g" "$NGINX_BASE_CONFIG" > "$routed_config"
  cp "$routed_config" deploy/nginx-runtime/default.conf
  rm -f "$routed_config"
  if ! compose exec -T mmn-web nginx -t || ! compose exec -T mmn-web nginx -s reload; then
    echo "反向代理切换到 ${upstream_name} 失败。" >&2
    return 1
  fi
  if ! compose exec -T mmn-web grep -q "proxy_pass http://${upstream_name}:8765" /etc/nginx/conf.d/default.conf; then
    echo "反向代理配置未指向 ${upstream_name}。" >&2
    return 1
  fi
  if ! compose exec -T mmn-web wget -qO- "http://${upstream_name}:8765/api/health" >/dev/null 2>&1; then
    echo "反向代理目标 ${upstream_name} 健康检查失败。" >&2
    return 1
  fi
  if ! wait_for_nginx_workers_to_drain "$previous_worker_pids" 330; then
    echo "反向代理已指向 ${upstream_name}，但旧请求尚未安全排空。" >&2
    return 1
  fi
}

acquire_lock

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

IMAGE_REPOSITORY="${MMN_IMAGE_REPOSITORY:-mmn-perception-engine}"
DEPLOY_IMAGE_TAG="${MMN_IMAGE_TAG:-latest}"
CANDIDATE_IMAGE_TAG="candidate-$(date '+%Y%m%d%H%M%S')"
ROLLBACK_IMAGE_TAG="rollback"
CANDIDATE_CONTAINER_NAME="mmn-app-candidate"
APP_WAS_RUNNING="false"
NGINX_BASE_CONFIG="$(mktemp /tmp/mmn-nginx-base.XXXXXX)"
cp deploy/nginx.conf "$NGINX_BASE_CONFIG"

if compose ps --services --filter status=running 2>/dev/null | grep -qx "mmn-app"; then
  APP_WAS_RUNNING="true"
  PREVIOUS_IMAGE_ID="$(docker inspect --format '{{.Image}}' mmn-app)"
  docker tag "$PREVIOUS_IMAGE_ID" "${IMAGE_REPOSITORY}:${ROLLBACK_IMAGE_TAG}"
  docker image prune --force
fi

ensure_build_capacity

if [[ "$APP_WAS_RUNNING" == "true" ]]; then
  echo "发布前备份当前运行数据。"
  bash scripts/backup.sh
fi

echo "旧版本继续在线，开始构建候选镜像。"
export MMN_IMAGE_TAG="$CANDIDATE_IMAGE_TAG"
if command -v timeout >/dev/null 2>&1; then
  if ! timeout "$BUILD_TIMEOUT_SECONDS" docker compose --env-file .env build mmn-app; then
    docker builder prune --all --force
    echo "候选镜像构建失败或超时；旧版本保持在线，本次发布停止。" >&2
    exit 1
  fi
else
  if ! compose build mmn-app; then
    docker builder prune --all --force
    echo "候选镜像构建失败；旧版本保持在线，本次发布停止。" >&2
    exit 1
  fi
fi
if ! docker run --rm --entrypoint python "${IMAGE_REPOSITORY}:${CANDIDATE_IMAGE_TAG}" -m py_compile server.py; then
  echo "候选镜像烟雾检查失败；旧版本保持在线，本次发布停止。" >&2
  exit 1
fi
docker tag "${IMAGE_REPOSITORY}:${CANDIDATE_IMAGE_TAG}" "${IMAGE_REPOSITORY}:${DEPLOY_IMAGE_TAG}"

sync_release_assets() {
  echo "同步随版本发布的数据资产到统一持久化根目录。"
  compose exec -T mmn-app mkdir -p /app/data/modules/product_evaluation /app/data/imports/raw/product_evaluation /app/data/dongchedi_sales /app/data/rag_training/dongchedi_sales /app/data/eval
  for eval_fixture in data/eval/mmn_eval_seed_v0.1.jsonl data/eval/mmn_eval_seed_outputs_v0.1.jsonl; do
    if [[ -f "$eval_fixture" ]]; then
      compose cp "$eval_fixture" "mmn-app:/app/$eval_fixture"
    fi
  done
  if [[ -f data/modules/product_evaluation/e7x_product_evaluation_2026-06.json ]]; then
    compose cp data/modules/product_evaluation/e7x_product_evaluation_2026-06.json mmn-app:/app/data/modules/product_evaluation/e7x_product_evaluation_2026-06.json
  fi
  for source_asset in data/imports/raw/product_evaluation/*; do
    [[ -f "$source_asset" ]] || continue
    compose cp "$source_asset" "mmn-app:/app/data/imports/raw/product_evaluation/$(basename "$source_asset")"
  done
  if [[ -f data/sales_warning_demo_2026-06.json ]]; then
    compose cp data/sales_warning_demo_2026-06.json mmn-app:/app/data/sales_warning_demo_2026-06.json
  fi
  if [[ -f data/sales_warning_cycles.json ]]; then
    if compose exec -T mmn-app test -f /app/data/sales_warning_cycles.json; then
      echo "保留服务器已有车型上市日期，不用版本文件覆盖。"
    else
      compose cp data/sales_warning_cycles.json mmn-app:/app/data/sales_warning_cycles.json
    fi
  fi
  for observed_file in data/dongchedi_sales/sales_warning_observed_????-??.json; do
    [[ -f "$observed_file" ]] || continue
    compose cp "$observed_file" "mmn-app:/app/$observed_file"
  done
  if [[ -f data/dongchedi_sales/sales_warning_latest.json ]]; then
    compose cp data/dongchedi_sales/sales_warning_latest.json mmn-app:/app/data/dongchedi_sales/sales_warning_latest.json
  fi
  if [[ -f data/dongchedi_sales/sales_warning_history.json ]]; then
    compose cp data/dongchedi_sales/sales_warning_history.json mmn-app:/app/data/dongchedi_sales/sales_warning_history.json
  fi
  if [[ -f data/dongchedi_sales/latest_mmn_perception_feed.json ]]; then
    compose cp data/dongchedi_sales/latest_mmn_perception_feed.json mmn-app:/app/data/dongchedi_sales/latest_mmn_perception_feed.json
  fi
  if [[ -f data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl ]]; then
    compose cp data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl mmn-app:/app/data/rag_training/dongchedi_sales/latest_dcd_sales_rag.jsonl
  fi
}

remove_candidate_container() {
  docker stop "$CANDIDATE_CONTAINER_NAME" >/dev/null 2>&1 || true
  docker rm "$CANDIDATE_CONTAINER_NAME" >/dev/null 2>&1 || true
}

restore_previous_image() {
  if [[ "$APP_WAS_RUNNING" != "true" ]]; then
    echo "发布前没有可回退的运行版本。" >&2
    return 1
  fi
  echo "新版本未通过健康检查，候选实例继续承接流量并恢复上一运行镜像。" >&2
  docker tag "${IMAGE_REPOSITORY}:${ROLLBACK_IMAGE_TAG}" "${IMAGE_REPOSITORY}:${DEPLOY_IMAGE_TAG}"
  export MMN_IMAGE_TAG="$DEPLOY_IMAGE_TAG"
  compose up -d --no-build --no-deps --force-recreate mmn-app mmn-creator-worker mmn-scheduler
  wait_for_app_health 60
  route_web_to mmn-app
  wait_for_web_health 30
  remove_candidate_container
}

echo "候选镜像构建成功，启动并行候选实例。"
remove_candidate_container
export MMN_IMAGE_TAG="$CANDIDATE_IMAGE_TAG"
compose run -d --no-deps --name "$CANDIDATE_CONTAINER_NAME" mmn-app
if ! wait_for_container_health "$CANDIDATE_CONTAINER_NAME" 120; then
  echo "候选实例未通过健康检查；旧版本保持在线，本次发布停止。" >&2
  remove_candidate_container
  exit 1
fi

sync_release_assets
docker restart "$CANDIDATE_CONTAINER_NAME" >/dev/null
if ! wait_for_container_health "$CANDIDATE_CONTAINER_NAME" 120; then
  echo "候选实例加载版本数据后未恢复健康；旧版本保持在线，本次发布停止。" >&2
  remove_candidate_container
  exit 1
fi

echo "候选实例健康，反向代理切换到候选实例。"
if ! route_web_to "$CANDIDATE_CONTAINER_NAME"; then
  route_web_to mmn-app || true
  remove_candidate_container
  exit 1
fi

echo "候选实例承接流量，后台替换正式应用与任务服务。"
export MMN_IMAGE_TAG="$DEPLOY_IMAGE_TAG"
if ! compose up -d --no-build --no-deps --force-recreate mmn-app mmn-creator-worker mmn-scheduler; then
  restore_previous_image
  exit 1
fi
if ! wait_for_app_health 60; then
  compose ps
  restore_previous_image
  exit 1
fi

echo "正式实例健康，反向代理切回正式实例。"
if ! route_web_to mmn-app || ! wait_for_web_health 30; then
  restore_previous_image
  exit 1
fi
remove_candidate_container

docker image rm "${IMAGE_REPOSITORY}:${CANDIDATE_IMAGE_TAG}" >/dev/null 2>&1 || true
docker builder prune --all --force
compose ps

echo "部署完成。测试地址：${MMN_PUBLIC_BASE_URL:-http://服务器公网IP:${MMN_HTTP_PORT:-8765}/}"
