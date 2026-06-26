# MMN Perception Engine 阿里云 ECS 部署说明

本文档用于将 MMN Perception Engine 部署到阿里云 ECS。当前阶段仅用于公网 IP 内部测试，不绑定正式域名，不开放客户访问。

## 1. 当前服务器配置

- 云厂商：阿里云
- 地域：华东 1 杭州
- 实例规格：通用算力型 u1
- CPU：4 核 vCPU
- 内存：8 GiB
- 系统盘：ESSD Entry 40GB
- 系统：Ubuntu 22.04 LTS 64 位

该配置可以支撑当前阶段的单机测试、内部演示和轻量数据导入。正式客户访问前建议升级到正式生产架构。

## 2. 部署架构

Docker Compose 管理以下服务：

- `mmn-web`：Nginx 前端入口，负责公网 HTTP 访问和反向代理
- `mmn-app`：MMN 应用服务，提供前端页面、后端 API、本地数据处理能力
- `mmn-db`：PostgreSQL 数据库服务，为后续商业化迁移预留
- `mmn-scheduler`：定时任务服务，用于周度抓取、归档和后续定时数据任务

当前版本核心业务数据仍保存在 `mmn_data` Docker volume 中的 SQLite 文件，PostgreSQL 已作为后续迁移目标纳入 Compose 管理。

## 3. 阿里云安全组端口

在阿里云控制台进入 ECS 实例安全组，入方向规则建议：

| 端口 | 协议 | 授权对象 | 用途 |
| --- | --- | --- | --- |
| 22 | TCP | 你的办公公网 IP/32 | SSH 管理 |
| 8765 | TCP | 你的办公公网 IP/32 | 当前阶段公网 IP 测试访问 |
| 80 | TCP | 暂不开放，正式域名备案后再开 | 正式 HTTP |
| 443 | TCP | 暂不开放，SSL 接入后再开 | 正式 HTTPS |

当前阶段不要把 `8765` 开放给 `0.0.0.0/0`。如必须临时测试，测试完成后立即收紧为办公 IP。

## 4. 首次初始化服务器

登录 ECS：

```bash
ssh root@YOUR_ECS_PUBLIC_IP
```

上传或拉取项目后，进入项目目录：

```bash
cd /opt/mmn-perception-engine
```

执行初始化：

```bash
sudo bash scripts/init-server.sh
```

该脚本会安装：

- Docker Engine
- Docker Compose Plugin
- Git
- UFW 防火墙
- 基础证书和 curl

## 5. 配置环境变量

复制模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
nano .env
```

必须填写或确认：

```bash
MMN_HTTP_PORT=8765
MMN_PUBLIC_BASE_URL=http://YOUR_ECS_PUBLIC_IP:8765
MMN_ALLOWED_CIDR=你的办公公网IP/32
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD
DATABASE_URL=postgresql://mmn:CHANGE_THIS_STRONG_PASSWORD@mmn-db:5432/mmn
DASHSCOPE_API_KEY=你的阿里云百炼Key
DEEPSEEK_API_KEY=你的DeepSeek Key
OPENAI_API_KEY=
```

注意：

- 不要把 `.env` 提交到 GitHub。
- 当前阶段不绑定正式域名，`MMN_PUBLIC_BASE_URL` 使用公网 IP。
- 如果暂不使用 OpenAI，可保持空值。

## 6. 启动部署

```bash
bash scripts/deploy.sh
```

查看服务：

```bash
docker compose ps
```

测试访问：

```bash
curl http://YOUR_ECS_PUBLIC_IP:8765/api/health
```

浏览器访问：

```text
http://YOUR_ECS_PUBLIC_IP:8765/
```

当前阶段仅内部测试，不对客户开放。

## 7. 标准发布流程

MMN Perception Engine 当前采用以下标准发布流程：

1. 本地 Mac 作为开发与验证环境。
2. 本地完成代码修改、页面检查、数据验证和发布门禁。
3. 确认无误后提交到 GitHub。
4. 阿里云 ECS 只作为运行环境，不直接手工修改业务代码。
5. ECS 通过 `deploy.sh` 从 GitHub 拉取最新代码，重新构建并启动 Docker 服务。
6. 如发布异常，通过 `rollback.sh` 回滚到指定 Git 版本。

### 本地发布前检查

在本地项目目录执行：

```bash
bash scripts/release_gate.sh
git status
```

确认无误后提交：

```bash
git add .
git commit -m "release: vX.X.X"
git push origin main
```

### 云端发布

登录 ECS 后执行：

```bash
cd /opt/mmn-perception-engine
bash deploy.sh
```

`deploy.sh` 会自动完成：

1. 从 GitHub 拉取 `main` 分支最新代码。
2. 保留服务器现有 `.env`，不会被 GitHub 覆盖。
3. 如当前服务正在运行，先备份云端数据。
4. 执行 `docker compose down --remove-orphans`。
5. 重新 `build`。
6. 执行 `docker compose up -d`。
7. 输出服务状态。

### 云端回滚

查看最近版本：

```bash
git log --oneline -n 10
```

回滚到指定版本：

```bash
bash rollback.sh <git_ref>
```

示例：

```bash
bash rollback.sh HEAD~1
```

`rollback.sh` 会保留 `.env`，先备份当前数据，再切换代码版本并重建容器。

### 发布记录

每次正式发布前，复制根目录 `release.md` 模板，填写发布日期、版本号、变更内容、测试结果、GitHub Commit、云端健康检查和回滚方案。

## 8. 停止、重启和更新

停止：

```bash
docker compose down
```

启动：

```bash
docker compose up -d
```

重启应用：

```bash
docker compose restart mmn-app mmn-web
```

拉取新代码并更新：

```bash
bash deploy.sh
```

## 9. 日志查看

查看全部服务日志：

```bash
docker compose logs -f
```

查看应用日志：

```bash
docker compose logs -f mmn-app
```

查看前端入口日志：

```bash
docker compose logs -f mmn-web
```

查看定时任务日志：

```bash
docker compose logs -f mmn-scheduler
```

## 10. 备份

执行：

```bash
bash scripts/backup.sh
```

默认备份到：

```text
backups/mmn_backup_YYYYMMDD_HHMMSS.tar.gz
```

建议：

- 内部测试阶段每天至少备份一次。
- 正式上线后接入 OSS 或企业备份系统。

## 11. 恢复

```bash
bash scripts/restore.sh backups/mmn_backup_YYYYMMDD_HHMMSS.tar.gz
```

恢复完成后应用会自动重启。

## 12. 本地与服务器数据同步

当前阶段采用“本地主数据库兜底、服务器镜像运行”的同步策略：

- 本地 Mac 保留主数据账本。
- 服务器保留同一份运行数据，用于公网 IP 内部测试和后续商业化迁移。
- 服务器中新增的数据会先回流到本地。
- 如果同一条记录本地和服务器同时存在差异，默认保留本地版本。
- 合并完成后，再把本地合并数据镜像到服务器。

执行同步：

```bash
bash sync-local-primary.sh
```

该脚本会自动完成：

1. 备份本地 `data/`。
2. 调用服务器备份脚本备份云端数据。
3. 拉取服务器 `/app/data/`。
4. 将服务器新增 SQLite 记录和新增文件合并回本地。
5. 将本地合并后的 `data/` 推送到服务器 Docker volume。
6. 重启服务器应用和定时任务服务。

默认连接信息可通过环境变量覆盖：

```bash
MMN_ECS_HOST=服务器公网IP
MMN_ECS_USER=root
MMN_ECS_KEY=/path/to/ssh_key
MMN_REMOTE_DIR=/opt/mmn-perception-engine
```

注意：

- 当前同步范围是项目 `data/` 目录和 `commercial_demo.db`，覆盖结构化数据、导入数据、RAG 训练文件和业务资产文件。
- 浏览器临时状态必须先写入项目快照或数据库，才能进入同步链路。
- 正式商业化阶段建议迁移到 RDS PostgreSQL + OSS，并将同步策略升级为实时事件同步和审计日志。

## 13. 定时任务

`mmn-scheduler` 当前预留并运行周度任务：

- 时间：每周日 23:00
- 时区：Asia/Shanghai
- 当前用途：创始人公开表达周度归档接口触发

查看任务日志：

```bash
docker compose logs -f mmn-scheduler
```

后续懂车帝销量、泰国市场数据、RAG资料更新等任务都可以纳入该服务。

## 14. 后续迁移到正式 ECS/RDS/OSS

正式商业化建议按以下顺序升级：

1. ECS 升级为生产实例，并设置快照策略。
2. 将数据库迁移到阿里云 RDS PostgreSQL。
3. 将文件、备份、导入原始数据迁移到 OSS。
4. 将 `.env` 中的 `DATABASE_URL` 指向 RDS。
5. 将备份脚本改为 OSS 上传。
6. 开启应用监控、日志服务和告警。
7. 将测试端口 8765 改为内网服务，由 Nginx 通过 80/443 对外提供正式访问。

## 13. 企业实名认证、域名备案和 SSL

正式对客户开放前，需要完成：

1. 阿里云账号企业实名认证。
2. 购买或接入正式域名。
3. ICP 备案。
4. 公安备案，按业务实际要求执行。
5. 申请 SSL 证书。
6. 将域名解析到 ECS 或负载均衡公网地址。
7. 修改 Nginx 配置，开放 443，并将 HTTP 跳转 HTTPS。
8. `.env` 中设置：

```bash
MMN_PUBLIC_BASE_URL=https://正式域名
```

当前阶段不执行域名绑定和 SSL 接入。

## 16. 安全注意事项

- 不对客户开放当前测试地址。
- 不把 API Key 写入代码。
- 不提交 `.env`。
- 安全组只开放必要端口。
- 22 端口只允许固定办公 IP。
- 测试完成后关闭或限制 8765 端口。
- 定期备份 `mmn_data`。

## 17. 常见问题

### 页面无法访问

检查：

```bash
docker compose ps
docker compose logs -f mmn-web
docker compose logs -f mmn-app
```

确认安全组已开放测试端口。

### 模型不可用

检查 `.env` 中的：

```bash
DASHSCOPE_API_KEY
DEEPSEEK_API_KEY
QWEN_BASE_URL
DEEPSEEK_BASE_URL
```

然后重启：

```bash
docker compose restart mmn-app
```

### 数据丢失

先不要重新部署，立即检查备份：

```bash
ls -lh backups/
```

如需要恢复，执行 `restore.sh`。

### 磁盘空间不足

检查：

```bash
df -h
docker system df
```

谨慎清理旧镜像：

```bash
docker image prune
```
