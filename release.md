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

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-05

## 发布版本

beta 1.01

## 发布负责人

MMN研发团队

## 发布目标

将本地完成的内容能力采集、达人内容学习与蒸馏流水线、达人能力资产系统和研发智能体交接体系同步到 GitHub 与服务器演示环境，保证本地与云端演示版本能力一致。

## 本次变更

- 内容资产中心新增内容能力蒸馏库交互升级。
- 达人蒸馏从内容片段展示升级为达人 DNA 资产包、脚本模板、选题公式、30 天选题库、账号孵化建议和客户 brief 模板。
- 社媒助手导出文件导入规则升级，优先识别账号昵称、内容标题、正文描述和平台字段，避免把账号 ID 当成达人名。
- 新增 MMN 内容采集器桌面版相关研发档案。
- 新增研发智能体交接手册，并明确后续每次更新必须同步交接手册、交接流程和发布记录。

## 本地测试结果

- `python3 -m py_compile server.py` 通过。
- `node --check app.js` 通过。
- 本地 `/api/health` 访问通过。
- 内容能力知识库接口可返回猴哥说车相关样本和达人资产。

## 发布要求

本次同步必须包含代码、研发档案、交接手册和发布记录。服务器仍作为稳定演示环境，后续业务功能仍以本地为主开发与验证。

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-08

## 发布版本

beta 1.01

## 发布负责人

MMN研发团队

## 发布目标

将 MMN PPT Agent 工作流同步到 GitHub 与服务器演示环境，使 MMN 具备可编辑、可复用、可校验的商业咨询型 PPTX 生成基础设施。

## 本次变更

- 新增 `skills/mmn-consulting-pptx/SKILL.md`，沉淀 MMN 专用 PPT Agent 工作规范。
- 新增 `src/ppt-agent/`，以 PptxGenJS 作为可编辑 `.pptx` 主生成引擎。
- 新增 MarkItDown 资料解析脚本、python-pptx 读取检查脚本和一键运行脚本。
- 新增 Marp CLI 结构版演示稿生成能力。
- 新增 Mermaid CLI 流程图、逻辑图生成能力。
- 新增页面结构 JSON、预览图、自动校验报告和示例 PPTX 产物。
- 自动校验覆盖中文溢出、元素重叠、标题层级、图表可读性、品牌配色、页码、目录一致性和 PPTX 页数一致性。
- 更新研发档案和智能体交接手册。
- 优化 Dockerfile 与定时任务脚本，移除云端镜像构建对 apt 安装 curl/nodejs 的依赖，改用 Python 标准库完成健康检查和内部定时 POST 调用，降低服务器构建网络风险。

## 影响范围

- 新增独立 PPT Agent 报告输出基础设施。
- 不替换现有 MMN 首页、策略驾驶舱、内容资产中心和既有策略报告接口。
- 不改变数据库结构，不清空既有数据，不修改云端登录权限。

## 本地测试结果

- `bash scripts/run_mmn_ppt_agent.sh` 通过。
- PPT Agent 校验报告 `ok: true`，`issueCount: 0`。
- `python3 -m py_compile server.py` 通过。
- `node --check src/ppt-agent/generate_deck.mjs` 通过。
- `node --check src/ppt-agent/export_preview.mjs` 通过。
- `node --check src/ppt-agent/validate_deck.mjs` 通过。
- `skills/mmn-consulting-pptx/SKILL.md` 通过 skill 校验。
- `pnpm release:gate` 通过。

## 发布要求

本次同步必须包含代码、依赖锁文件、PPT Agent 示例输入、示例输出产物、研发档案、交接手册和发布记录。服务器发布后需执行云端健康检查并记录结果。

## 云端发布结果

- GitHub Commit：`a7bbfe5 fix: stabilize MMN Docker build`
- 服务器目录：`/opt/mmn-perception-engine`
- 服务器拉取版本：`a7bbfe5`
- 发布前数据备份：`backups/mmn_backup_20260708_163756.tar.gz`
- 容器状态：`mmn-app` healthy，`mmn-db` healthy，`mmn-scheduler` healthy，`mmn-web` running。
- 健康检查：`http://121.40.60.90/api/health` 返回 `ok: true`、`version: beta 1.01`。
- 公网基础检查：`bash scripts/test_mmn_cloud.sh http://121.40.60.90` 通过首页与健康接口检查。
- 服务器 PPT Agent 产物确认：`output/ppt-agent/mmn-strategy-deck.pptx`、`page-structure.generated.json`、`validation-report.json`、预览图、Marp 结构稿和 Mermaid 图均已存在。

## 发布结论

MMN PPT Agent 工作流已同步至 GitHub 与阿里云服务器。服务器当前运行版本健康，PPT Agent 代码、示例输入、示例输出和所有记录已完成同步。
