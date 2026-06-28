# MMN Perception Engine 发布记录

## 发布日期

2026-06-28

## 发布版本

beta 1.01

## 发布负责人

MMN研发团队

## 发布目标

将本地已完成的车型资产一致性修复、达人蒸馏入库、MMN页面输出能力、打法知识库来源提示和版本信息统一发布到服务器，使本地与服务器均进入 beta 1.01。

## 需求背景

本次发布解决以下问题：

- 车型库品牌和车型归属不稳定。
- 同一车型因空格、中英文、能源写法不同而重复出现。
- 蒸馏后的达人资产需要进入对应平台达人库。
- 功能页需要具备 MMN 分析输出能力。
- 打法知识库需要显示当前车型来源于策略驾驶舱。
- 每次更新必须形成正式文档。

## 本次变更

- 功能新增：人工结论学习页增加品牌 / 车型选择和 MMN 草案生成。
- 功能新增：打法知识库显示当前车型来源、品牌和车型。
- 问题修复：荣威 / 宝马 i5、极狐贝塔 S3、大众途观 L PHEV、ID.ERA 9X、极氪 / ZEEKR 等车型归一。
- 问题修复：垂媒正反向矩阵严格显示当前所选周期。
- 流程优化：蒸馏后的创作者画像进入对应平台达人库。
- 文档更新：新增 beta 1.01 研发档案，更新版本规则和 README。

## 影响范围

- 前端页面：策略驾驶舱、垂媒竞争格局、内容资产中心、打法知识库、人工结论学习、版本架构。
- 后端接口：`/api/health` 返回版本信息。
- 数据库与数据文件：不改变数据库结构；不清空既有数据。
- 定时任务：不改变既有调度逻辑。
- 部署脚本：沿用现有 Docker Compose 发布流程。

## 本地测试结果

- 静态检查：`python3 -m py_compile server.py` 通过。
- 静态检查：`new Function(app.js)` 通过。
- 功能验证：本地服务启动显示 `中国汽车营销引擎 beta 1.01 已启动`。
- 页面访问：首页返回 200。
- 版本验证：本地 `/api/health` 返回 `version: beta 1.01`、`versionCode: beta-1.01`。

## GitHub 版本信息

- 分支：`main`
- Commit：`80ab6e2 release: beta 1.01`
- Tag：`beta-1.01`

## 云端发布结果

- ECS 环境：阿里云 ECS，目录 `/opt/mmn-perception-engine`
- 部署时间：2026-06-29 00:06 左右
- 部署方式：由于服务器连接 GitHub 超时，使用本地 `beta-1.01` Git 归档包同步到服务器，并执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`
- 数据备份：`backups/mmn_backup_20260629_000646.tar.gz`
- 云端工作目录备份：已 stash `server-pre-beta-1.01-20260629-000332`
- 容器状态：`mmn-app` healthy，`mmn-db` healthy，`mmn-scheduler` running，`mmn-web` running
- 健康检查：`http://121.40.60.90/api/health` 返回 `version: beta 1.01`
- 公网测试地址：`http://121.40.60.90`
- 域名状态：`http://mmnsh.com` 当前被阿里云备案拦截，返回 Non-compliance ICP Filing 页面

## 回滚方案

回滚目标版本：

```bash
bash rollback.sh HEAD~1
```

如需恢复服务器发布前数据：

```bash
bash restore.sh backups/mmn_backup_20260629_000646.tar.gz
```

如需查看服务器发布前代码改动：

```bash
git stash show -p stash@{0}
```

## 发布结论

beta 1.01 本地与服务器 IP 版本验证通过。域名访问受备案限制影响，需后续处理备案或域名解析策略。

## 后续计划

- 处理 `mmnsh.com` 备案拦截。
- 建立发布后自动验证：GitHub commit、服务器 health、前端资源版本、容器状态、备份文件。
- 后续每次功能更新继续新增研发档案。
