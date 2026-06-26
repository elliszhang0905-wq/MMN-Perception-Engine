#!/usr/bin/env bash
set -euo pipefail
export COPYFILE_DISABLE=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ECS_HOST="${MMN_ECS_HOST:-121.40.60.90}"
ECS_USER="${MMN_ECS_USER:-root}"
ECS_KEY="${MMN_ECS_KEY:-/Users/ellis/.ssh/mmn_ecs_hangzhou_v1}"
REMOTE_DIR="${MMN_REMOTE_DIR:-/opt/mmn-perception-engine}"
DATA_DIR="${MMN_DATA_DIR:-data}"
DB_FILE="${MMN_DB_FILE:-commercial_demo.db}"
DB_PATH="${DATA_DIR}/${DB_FILE}"
STAMP="$(date '+%Y%m%d_%H%M%S')"
WORK_DIR="$(mktemp -d "/tmp/mmn-sync-${STAMP}.XXXXXX")"
LOCAL_BACKUP_DIR="${ROOT}/backups/sync_${STAMP}"
REMOTE_TAR="/tmp/mmn_server_data_${STAMP}.tar.gz"
LOCAL_TAR="${WORK_DIR}/mmn_local_primary_data_${STAMP}.tar.gz"
REMOTE_LOCAL_TAR="/tmp/mmn_local_primary_data_${STAMP}.tar.gz"

cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

if [[ ! -d "$DATA_DIR" ]]; then
  echo "未找到本地数据目录：$DATA_DIR"
  exit 1
fi

if [[ ! -f "$ECS_KEY" ]]; then
  echo "未找到 ECS SSH 密钥：$ECS_KEY"
  exit 1
fi

mkdir -p "$LOCAL_BACKUP_DIR"
tar -czf "${LOCAL_BACKUP_DIR}/local_data_before_sync.tar.gz" -C "$DATA_DIR" .
echo "本地同步前备份完成：${LOCAL_BACKUP_DIR}/local_data_before_sync.tar.gz"

ssh -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}" \
  "cd '${REMOTE_DIR}' && mkdir -p backups && bash scripts/backup.sh >/tmp/mmn_backup_${STAMP}.log && cat /tmp/mmn_backup_${STAMP}.log"

ssh -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}" \
  "rm -rf /tmp/mmn_sync_server_data_${STAMP} && mkdir -p /tmp/mmn_sync_server_data_${STAMP} && docker cp mmn-app:/app/data/. /tmp/mmn_sync_server_data_${STAMP}/ && tar -czf '${REMOTE_TAR}' -C /tmp/mmn_sync_server_data_${STAMP} ."

scp -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}:${REMOTE_TAR}" "${WORK_DIR}/server_data.tar.gz" >/dev/null
mkdir -p "${WORK_DIR}/server_data"
tar -xzf "${WORK_DIR}/server_data.tar.gz" -C "${WORK_DIR}/server_data"

python3 - "$ROOT" "$DATA_DIR" "$DB_FILE" "${WORK_DIR}/server_data" <<'PY'
import os
import shutil
import sqlite3
import sys

root, data_dir, db_file, server_data = sys.argv[1:5]
local_data = os.path.join(root, data_dir)
local_db = os.path.join(local_data, db_file)
server_db = os.path.join(server_data, db_file)

def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in conn.execute(
            "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
        )
    ]

def table_columns(conn: sqlite3.Connection, table: str) -> list[dict]:
    rows = conn.execute(f"pragma table_info({quote_ident(table)})").fetchall()
    return [
        {"name": row[1], "pk": row[5]}
        for row in rows
    ]

def pk_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cols = table_columns(conn, table)
    return [col["name"] for col in sorted([c for c in cols if c["pk"]], key=lambda x: x["pk"])]

def copy_server_only_files() -> int:
    copied = 0
    for dirpath, _, filenames in os.walk(server_data):
        for filename in filenames:
            rel = os.path.relpath(os.path.join(dirpath, filename), server_data)
            if rel == db_file:
                continue
            dst = os.path.join(local_data, rel)
            if os.path.exists(dst):
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(server_data, rel), dst)
            copied += 1
    return copied

if not os.path.exists(server_db):
    print("服务器数据库不存在，仅同步服务器端新增文件。")
    copied_files = copy_server_only_files()
    print(f"服务器端新增文件回流：{copied_files} 个")
    raise SystemExit(0)

if not os.path.exists(local_db):
    os.makedirs(os.path.dirname(local_db), exist_ok=True)
    shutil.copy2(server_db, local_db)
    copied_files = copy_server_only_files()
    print("本地数据库不存在，已用服务器数据库初始化本地。")
    print(f"服务器端新增文件回流：{copied_files} 个")
    raise SystemExit(0)

local = sqlite3.connect(local_db)
server = sqlite3.connect(server_db)
local.row_factory = sqlite3.Row
server.row_factory = sqlite3.Row

inserted_total = 0
skipped_conflicts = 0
created_tables = 0

for table in table_names(server):
    server_create = server.execute(
        "select sql from sqlite_master where type='table' and name=?", (table,)
    ).fetchone()
    local_table_exists = local.execute(
        "select 1 from sqlite_master where type='table' and name=?", (table,)
    ).fetchone()

    if not local_table_exists:
        if server_create and server_create[0]:
            local.execute(server_create[0])
            created_tables += 1
        else:
            continue

    local_cols = [col["name"] for col in table_columns(local, table)]
    server_cols = [col["name"] for col in table_columns(server, table)]
    common_cols = [col for col in server_cols if col in local_cols]
    if not common_cols:
        continue

    keys = [col for col in pk_columns(local, table) if col in common_cols]
    if not keys:
        keys = common_cols

    select_sql = f"select {', '.join(quote_ident(col) for col in common_cols)} from {quote_ident(table)}"
    rows = server.execute(select_sql).fetchall()

    for row in rows:
        where = " and ".join(f"{quote_ident(col)} = ?" for col in keys)
        key_values = [row[col] for col in keys]
        existing = local.execute(
            f"select 1 from {quote_ident(table)} where {where} limit 1",
            key_values,
        ).fetchone()
        if existing:
            skipped_conflicts += 1
            continue

        placeholders = ", ".join("?" for _ in common_cols)
        insert_sql = (
            f"insert into {quote_ident(table)} "
            f"({', '.join(quote_ident(col) for col in common_cols)}) "
            f"values ({placeholders})"
        )
        local.execute(insert_sql, [row[col] for col in common_cols])
        inserted_total += 1

local.commit()
local.close()
server.close()

copied_files = copy_server_only_files()
print(f"服务器新增表回流：{created_tables} 张")
print(f"服务器新增记录回流：{inserted_total} 条")
print(f"本地优先保留冲突记录：{skipped_conflicts} 条")
print(f"服务器端新增文件回流：{copied_files} 个")
PY

tar -czf "$LOCAL_TAR" -C "$DATA_DIR" .
scp -i "$ECS_KEY" -o StrictHostKeyChecking=no "$LOCAL_TAR" "${ECS_USER}@${ECS_HOST}:${REMOTE_LOCAL_TAR}" >/dev/null

ssh -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}" "cd '${REMOTE_DIR}' && \
  DATA_VOLUME=\$(docker volume ls --format '{{.Name}}' | grep '_mmn_data$' | head -n 1) && \
  APP_IMAGE=\$(docker compose --env-file .env images -q mmn-app | head -n 1) && \
  if [ -z \"\$DATA_VOLUME\" ]; then echo '未找到 mmn_data Docker volume'; exit 1; fi && \
  if [ -z \"\$APP_IMAGE\" ]; then echo '未找到 mmn-app 镜像'; exit 1; fi && \
  docker compose --env-file .env stop mmn-scheduler mmn-app >/dev/null && \
  docker run --rm -v \"\$DATA_VOLUME:/app/data\" -v /tmp:/host_tmp \"\$APP_IMAGE\" sh -lc \"find /app/data -mindepth 1 -maxdepth 1 -exec rm -rf {} + && tar -xzf /host_tmp/$(basename "$REMOTE_LOCAL_TAR") -C /app/data\" && \
  docker compose --env-file .env up -d mmn-app mmn-scheduler >/dev/null && \
  docker compose --env-file .env ps"

ssh -i "$ECS_KEY" -o StrictHostKeyChecking=no "${ECS_USER}@${ECS_HOST}" "rm -f '${REMOTE_TAR}' '${REMOTE_LOCAL_TAR}'"

echo "本地主数据库同步完成。当前策略：服务器新增回流本地；冲突记录本地优先；合并后再镜像到服务器。"
