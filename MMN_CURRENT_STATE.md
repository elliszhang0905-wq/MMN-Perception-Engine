# MMN 当前系统状态包

## 状态基线

- 状态包版本：`v2.3`
- 最后核验时间：`2026-07-22 00:37:43 +0800`（Asia/Shanghai）
- Git commit：短 hash `72ecb1c`；完整 hash `72ecb1cc5edd7951f5b2ae2e4816cd0ca572b56f`
- 当前分支：`main`
- 生成时工作树状态：`dirty`
- 基线说明：`72ecb1c` 已推送到 GitHub `main` 并部署至 ECS `/opt/mmn-perception-engine`；当前只更新本状态包以记录生产验收证据，业务代码与数据不再变更。
- 未提交修改路径（按 `git status --short`，未展开未跟踪目录内的文件内容）：
  - `MMN_CURRENT_STATE.md`
  - `output/mmn-eval-seed-report.json`（发布门禁生成的临时评测产物，不进入提交）
- 维护要求：以后每次更新本状态包时，必须同步刷新状态包版本、最后核验时间、短/完整 commit hash、当前分支、工作树状态和未提交修改路径。

> 应用版本常量：`beta 1.03`
> 内容规则：本文件只记录已在当前代码中核验到的状态；静态 UI、模拟数据、降级结果和待建设能力必须明确标记，不得写成真实上线能力。禁止写入密钥、Token、连接串、客户数据或账号密码。

## 1. 系统定位与不可擅自改变的产品边界

- MMN 是面向车企品牌、市场部门、代理公司与汽车垂直 MCN 的汽车营销决策操作系统，核心闭环是“证据 → Insight → 判断/行动 → 结果 → Learning → Know-how”。定位依据：`README.md`、`docs/mmn-auto-consulting-os.md`、`docs/mmn-strategy-model.md`。
- MMN 与 Sales Credo 是两条独立产品线；不得把经销商门店接待、销售顾问即时攻防等 Credo 场景混入 MMN。规则依据：`README.md`、`AGENTS.md`。
- 必须保留现有左侧核心模块、导航分组、入口归属、路由语义和整体 UI 结构；未经用户明确授权，不得新增、删除、迁移、合并、拆分或重命名一级/二级模块。实现与规则依据：`index.html`、`app.js`、`style.css`、`AGENTS.md`。
- “决策驾驶舱”是 MMN 唯一对外显性的核心产品模块；其他现有左侧模块作为驾驶舱的证据、策略、内容资产、知识沉淀和系统治理能力继续保留，不得据此删除现有导航。
- 不得擅自新增“线索 → 到店 → 成交”归因链路，也不得把平台曝光、互动、情绪或热度直接表述为销售转化。
- 用户侧不得暴露底层模型、插件、数据服务商或技术供应商名称；统一使用中性的 MMN 能力名称。底层路由可替换，但事实结论必须保留证据和人工复核边界。规则依据：`README.md`、`AGENTS.md`、`mmn_model_governance.py`。
- 不得删除、覆盖用户数据、原始导入文件、数据库或研发档案；采集只处理公开可访问、用户导入或合法授权的数据，不绕过登录、验证码、风控或付费墙。规则依据：`README.md`、`AGENTS.md`。

## 2. 当前技术栈、启动与部署

### 2.1 技术栈

| 层 | 当前真实实现 | 关键路径 |
| --- | --- | --- |
| 前端 | 原生 HTML、CSS、JavaScript 单页界面；按 `data-page` 切换 `<section class="page">`，部分模块拆分独立 JS/CSS | `index.html`、`app.js`、`style.css`、`group-dashboard.js`、`lead-dashboard.js`、`policy-intelligence.js`、`bf-factory.js` |
| 后端 | Python 3 标准库 `http.server`/`socketserver` 单体服务，路由集中在 `server.py` | `server.py` |
| 本地业务存储 | 以 SQLite 与 JSON/JSONL/导入文件为主；浏览器还保存按组织与版本隔离的本地状态 | `server.py`、`mmn_data.py`、`data/`、`app.js` |
| 异步任务 | 进程内线程任务；达人蒸馏在 Redis 可用时可由 Celery worker 执行，本地可回退为本地队列 | `server.py`、`creator_distillation/tasks.py`、`docker-compose.yml` |
| 文档/报告 | Python 文档解析与导出；Node/PptxGenJS、Marp、Mermaid 负责 PPT 生成/校验链路 | `bf_factory/`、`creator_script_generation.py`、`src/ppt-agent/`、`package.json` |
| 销量预警—T周期适配 | 将已核验的销量预警正式上市日、考核日、T+X与阶段原子同步到驾驶舱T周期；服务端优先、本地仅作可靠缓存 | `sales-warning-cycle-context.js`、`group-dashboard.js`、`app.js`、`t-cycle.js` |
| 测试与验收 | Python `unittest`、Node 脚本测试、Playwright 全表面发布门禁 | `tests/`、`scripts/release_gate.sh`、`scripts/release_gate_all_surfaces.js` |

### 2.2 启动方式

- 本地直接启动：`python3 server.py`，默认访问 `http://127.0.0.1:8765/`。入口：`server.py`、`README.md`。
- 本地守护启动：`bash scripts/ensure_local_mmn.sh`；桌面启动器调用该脚本并在健康检查后打开浏览器。说明：`README_DEPLOY.md`。
- 基础发布门禁：`npm run release:gate`，实际执行 `scripts/release_gate.sh`。
- 状态包门禁：`npm run check:mmn-state`；指定基线可用 `npm run check:mmn-state -- --base <git-ref>` 或环境变量 `MMN_STATE_BASE_REF`。实现：`scripts/check_mmn_state.mjs`。

### 2.3 部署方式

- Docker 镜像基于 Python 3.11，同时包含服务器端 Node.js、Chromium 与受限浏览器取证运行时，启动命令为 `python server.py`。配置：`Dockerfile`。
- Docker Compose 当前定义 Nginx 前置入口、MMN 应用、PostgreSQL/pgvector、Redis、达人 worker 和 scheduler。配置：`docker-compose.yml`、`deploy/nginx.conf`。
- 当前核心业务运行数据仍以挂载到 `/app/data` 的 SQLite/文件资产为主；PostgreSQL 已进入 Compose，并有达人资产迁移 schema，但不是全系统唯一主存储。依据：`Dockerfile`、`docker-compose.yml`、`migrations/creator_distillation/`、`README_DEPLOY.md`。
- 标准部署脚本：`scripts/deploy.sh`；备份/恢复/回滚：`scripts/backup.sh`、`scripts/restore.sh`、`scripts/rollback.sh`。云端部署说明：`README_DEPLOY.md`。
- 当前仓库未发现 GitHub Actions、GitLab CI、Jenkins 或 Azure Pipelines 配置；`check:mmn-state` 目前仅为本地门禁，**待接入 CI**。

## 3. 左侧导航、页面路径、用途与完成度

当前页面不是传统多 URL 路由；根路径 `/` 内由 `app.js` 的 `showPage(id)` 根据导航按钮 `data-page` 切换页面 section。导航来源：`index.html`；名称和隐藏逻辑：`app.js` 的 `pageNames`、`hiddenPages`。

| 导航分组 | 页面 ID / 访问语义 | 用途 | 当前完成度与数据状态 |
| --- | --- | --- | --- |
| 核心工作流 / 决策驾驶舱 | `dashboard` | 汇总 T 周期、数据导入、诊断、证据、策略与行动复盘 | 已实现交互；混合真实导入、数据库快照、接口结果与明确演示/降级状态。`index.html`、`app.js`、`lead-dashboard.js`、`group-dashboard.js` |
| 决策驾驶舱子项 | `brandpenetration` | 品牌传播穿透与周度策略视图 | 已实现页面/API；读取社媒快照、周度市场与销量预警数据，缺源时存在降级/演示口径。`app.js`、`server.py`、`group_dashboard.py` |
| 决策驾驶舱子项 | `socialtrends` | 社媒热度、竞品与证据明细 | 已实现任务、导入与快照；可接真实服务或用户导入，服务不可用时不得视作实时事实。`social-trends.js`、`social_trends.py`、`server.py` |
| 决策驾驶舱子项 | `policyintelligence` | 政策来源、车型影响、策略交叉验证与人工复核 | MVP 已实现；只有证据完整且通过规则的结果可发布，否则为 `manual_required`/待验证。`policy-intelligence.js`、`policy_intelligence.py`、`server.py` |
| MMN 策略输出 | `contentstrategy` | 将证据与诊断转为内容/传播策略 | 已实现 UI 与策略接口；模型不可用时可能返回规则/缓存降级，不等于真实模型完成。`app.js`、`server.py`、`consulting_output.py` |
| MMN 策略输出 | `bffactory` | 品牌商业化内容 Brief 的导入、结构化、生成、编辑与导出 | P0 全链路已实现；真实文件/SQLite 持久化，模型步骤允许明确降级。`bf-factory.js`、`bf_factory/`、`server.py` |
| 核心工作流 | `videos` | 内容资产、达人/博主相关工作台的承载页 | 已实现；不同子视图复用此页面。`index.html`、`app.js` |
| 诊断分析 | `data` | 声量/评价数据导入、清洗与表格查看 | 已实现 XLSX 导入和浏览器/服务端状态；数据真实性取决于导入源。`index.html`、`app.js`、`server.py` |
| 诊断分析 | `cognition` | NSR、情绪、属性、身份与认知诊断 | 已实现计算与交互；既有样例/模拟行必须与真实导入结果区分。`app.js`、`nsr-map.js` |
| 诊断分析 | `vertical` | 竞品格局、垂媒评价与排名学习 | 已实现导入、诊断与学习接口；外部数据缺失时不代表无风险/无机会。`app.js`、`server.py` |
| 诊断分析 | `actions` | 行动预算 | 代码与数据字段保留，但导航和页面当前隐藏，直接访问会回到 `dashboard`。`index.html`、`app.js`、`style.css` |
| 资产沉淀 / 达人资产 | `bloggerskill` | 博主导入、蒸馏、孵化与任务进度 | 已实现文件/URL 导入、扫描和任务状态；真实下游验收必须继续到内容能力资产与脚本导出。`app.js`、`server.py`、`creator_distillation/` |
| 资产沉淀 | `strategykb` | RAG 资产导入、查看与策略召回 | 已实现导入和读取接口；数据来自本地知识文件/数据库。`app.js`、`server.py`、`data/rag_training/` |
| 资产沉淀 | `bflibrary` | BF 历史资产库 | 页面由 BF 工厂代码管理；真实 SQLite/文件资产。`bf-factory.js`、`bf_factory/` |
| 资产沉淀 | `knowhow` | 方法论和可复用打法沉淀 | 已实现 UI 与本地状态；部分初始内容属于内置种子。`knowhow.css`、`app.js` |
| 资产沉淀 | `learning` | 人工结论、反馈与学习记录 | 已实现 API 与 SQLite 持久化。`app.js`、`server.py` |
| 系统治理 | `workspace` | 组织空间、知识范围与模型路由上下文 | 已实现基础组织/角色隔离与工作区读写。`app.js`、`server.py` |
| 系统治理 | `config` | 项目、车型、阈值与平台权重 | 已实现浏览器侧配置保存；部分配置也进入项目快照。`app.js`、`server.py` |
| 系统治理 | `eval` | 离线结果评测、报告与人工复核 | v0.1 已实现；当前是离线最终输出发布门禁，不应声称为所有请求实时调用。`mmn_eval/`、`server.py`、`app.js` |
| 系统治理 | `architecture` | 当前版本与架构说明 | 说明型静态 UI，内容来自前端内置状态。`index.html`、`app.js` |

补充：`creatorassets`（达人资产诊断）存在页面逻辑和 API，但不是当前左侧独立按钮；`founder` 等兼容入口会映射到 `videos` 子视图。依据：`app.js`。

## 4. 功能模块真实性分层

| 类型 | 当前模块 | 状态说明 |
| --- | --- | --- |
| 已实现并可持久化 | 项目快照、Learning、Workspace、BF 工厂、社媒快照、抖音热点实体复核、按需视频洞察与内容防线、达人蒸馏、内容能力资产、政策记录与复核、Eval 人工复核 | 持久化在 SQLite、JSON/JSONL 或资产文件中；具体表和路径见下节。 |
| 已实现但依赖外部/用户数据 | 社媒趋势采集、销量/垂媒导入、政策抓取、产品白皮书、达人 URL 导入、模型策略分析 | “接口成功”不自动等于来源真实有效；必须核对来源状态、证据和下游资产。 |
| 静态 UI / 内置种子 | 全球版部分能力路线图、版本架构说明、部分默认驾驶舱样例和知识库初始项 | 用于说明和演示，不得写成已接入海外真实数据或完整商业化能力。主要在 `app.js`、`index.html`。 |
| 模拟/演示数据 | `group-dashboard-demo`、部分销售预警 demo/baseline、前端 `defaultState` | 必须在 UI/报告中保留 demo、baseline、待验证或降级语义。`group_dashboard.py`、`data/`、`app.js`。 |
| 明确待建设 | 全系统 PostgreSQL 主存储迁移、正式多租户 SaaS、完整海外跨语言 RAG/合规引擎、CI 状态门禁 | 当前配置或占位不等于完成。`README.md`、`README_DEPLOY.md`、`app.js`。 |

## 5. 数据链路、核心字段与计算规则

### 5.1 数据根与分层

- `mmn_data.py` 统一解析 `MMN_DATA_ROOT`/`MMN_DATA_DIR`；默认根目录为 `data/`。代码按模块组织目录，并兼容部分旧路径读取；新写入应走规范模块路径。
- 主 SQLite 默认是 `data/commercial_demo.db`，可由运行环境覆盖路径；达人蒸馏本地库默认是 `data/creator_distillation.db`。只记录路径规则，不在本文记录实际连接信息。
- 前端本地状态通过 `app.js` 的 `storageKey()` 按组织 ID 与国内/全球版本隔离；浏览器状态不会自动成为服务器持久数据，需经项目快照/API 才进入同步链路。

### 5.2 主要链路

| 链路 | 来源 → 接口/处理 → 存储/输出 | 核心字段/规则 | 关键路径 |
| --- | --- | --- | --- |
| 声量与认知 | 用户 XLSX → `/api/import-vertical-xlsx` → 前端行数据/项目快照 → NSR 与认知看板 | 车型、平台、赛道、认知标签、情绪、用户身份、购买意向、有效评论、Impact/Growth/Competition；导入校验失败不得沿用错误旧结果 | `server.py`、`app.js`、`nsr-map.js` |
| 社媒趋势 | 外部公开数据服务或用户文件 → `/api/social-trends/jobs`、`/import` → `social_trend_snapshots` | `org_id`、`edition`、`keyword`、过滤条件、来源模式、结果 JSON、时间；热度/互动是传播证据，不是成交证明 | `social_trends.py`、`server.py`、`social-trends.js` |
| 抖音热点实体 | 榜单/采集器 → 规则与模型识别 → 人工复核 → 排名快照 | 车型实体、关系、证据类型、fingerprint、双路审计、复核状态；不完整识别进入人工队列 | `douyin_hot_entities.py`、`douyin-hot-demo.js`、`server.py` |
| 抖音逐视频洞察/内容防线 | 用户单条点击 → 原页验证与多模态证据包 → 三路独立分析 → MMN 交叉校验 → 持久化洞察/降级/人工复核 | 仅用户手动点击触发；跨24小时/7天/30天按内容指纹幂等复用；播放量变化不触发重分析；无可读视频时明确 `limited_analysis`/失败，不声称已读完整视频 | `douyin_video_insights.py`、`douyin_browser_evidence.py`、`content_defense.py`、`creator_distillation/media_processing.py`、`server.py`、`douyin-hot-demo.js` |
| 销量预警 | 懂车帝销量文件、CPCA/已导入市场数据 → 月度历史与预警计算 → 驾驶舱 | 细分市场、车型、上市时间、月销量、市场容量、阈值与观察周期；当前规则和数据源以 `group_dashboard.py`、`sales_warning_*` 文件为准 | `group_dashboard.py`、`data/dongchedi_sales/`、`server.py` |
| 销量预警—T周期联动 | `/api/group-dashboard-demo.salesWarningCycles` 已核验记录 → 周期上下文适配 → 车型选择事件 → 下方T周期/卖点决策/传播阶段 | 依次使用服务端已核验记录、本地已核验缓存、具有完整日期证据的数据库记录；仅有阶段文字不生成日期；权威T0禁止在下方覆盖 | `sales-warning-cycle-context.js`、`group-dashboard.js`、`app.js`、`t-cycle.js` |
| 决策执行周期 | 驾驶舱输入/策略 → `/api/cockpit/execution-cycles` → 项目周期与监测状态 | T0、阶段、建议、状态、监测窗口；用于策略执行与复盘，不扩展为线索/到店/成交归因 | `cockpit_decision_loop.py`、`server.py`、`app.js`、`t-cycle.js` |
| 政策情报 | 官方/公开政策来源 → 抽取与多路交叉验证 → SQLite 记录/人工复核 | 来源、地区、适用车型、价格/场景、共同证据 ID、评估状态；证据不足必须 `manual_required` | `policy_intelligence.py`、`policy-intelligence.js`、`server.py` |
| BF 工厂 | Word/PPT/PDF/图片/表格/文本 → 解析分段 → A–F 结构/策略/复核 → 编辑/Word 导出 | 项目/客户隔离、来源页码/段落、样本状态、章节意图、人工修订、风险复核；模型不可用时只生成明确降级稿 | `bf_factory/`、`bf-factory.js`、`server.py` |
| 达人蒸馏 | URL/文件/公开数据 → 任务与媒体处理 → 创作者、资产、证据、方法论 | 任务阶段/进度、creator/profile、asset、provenance、evidence、performance、人工纠正；HTTP 200 不等于上游业务成功 | `creator_distillation/`、`migrations/creator_distillation/`、`server.py` |
| 内容能力与脚本 | 博主/内容能力导入 → `/api/content-capability-kb` → creatorAssets → script-jobs → DOCX | 完整验收链为任务完成、资产可查、脚本成功、导出文件可读；中间任务卡完成不等于下游可用 | `server.py`、`creator_script_generation.py`、`app.js` |
| Learning/Know-how | 人工结论与策略反馈 → `/api/learnings`/本地知识状态 → 可复用资产 | 保留组织、用户、版本、车型、标签、结论、建议、证据、阶段与时间；人工结论优先于自动推断 | `server.py`、`app.js`、`knowhow.css` |
| Eval | 固定样例/最终咨询输出 → 离线 runner/scorer → 报告与人工复核 | 事实/推断/假设/未知、证据引用、评分、阈值、人工裁决；当前不保证请求时实时执行 | `mmn_eval/`、`scripts/run_mmn_eval.py`、`server.py` |

## 6. API、数据库与权限机制

### 6.1 API

- HTTP API 由 `server.py` 的请求处理器统一提供，当前代码知识图谱识别到 78 个路由。主要分组包括：
  - 系统与权限：`/api/health`、`/api/auth/config`、`/api/login`、`/api/workspace`、`/api/project-state`；
  - 数据与资产：`/api/import-vertical-xlsx`、`/api/import-video-xlsx`、`/api/import-rag-*`、`/api/asset-library`、`/api/vertical-assets`；
  - 策略与分析：`/api/ai/*`、`/api/semantic/*`、`/api/opportunity-map/*`、`/api/topic-planning/run`、`/api/product-whitepaper/*`；
  - 驾驶舱与情报：`/api/group-dashboard*`、`/api/cockpit/execution-cycles*`、`/api/social-trends/*`、`/api/policy-intelligence/*`、`/api/douyin-hot/*`；
  - 内容生产：`/api/bf/*`（动态分派）、`/api/blogger-skill/*`、`/api/creator-distillation/*`、`/api/content-capability-kb/*`；
  - 治理：`/api/eval/*`、`/api/learnings`、`/api/agents/run`。
- 精确方法、参数和响应契约以 `server.py` 与对应测试为准；状态包不复制敏感运行配置。

### 6.2 数据库/文件

- `commercial_demo.db` 主要表包含组织、用户、Learning、Workspace、项目快照、策略/资产和各模块扩展表；schema 由 `server.py` 及模块 `init_schema` 增量创建。
- BF 表覆盖 project、document、segment、brief、revision、sample、audit/feedback 等结构，定义于 `bf_factory/repository.py`。
- 社媒与热点表定义于 `social_trends.py`、`douyin_hot_entities.py`；政策表定义于 `policy_intelligence.py`。
- 达人本地兼容表定义于 `creator_distillation/repository.py`；PostgreSQL/pgvector 目标 schema 在 `migrations/creator_distillation/*.sql`。
- 文件资产位于 `data/` 的模块目录，包括导入原件、RAG JSONL、销量历史、状态 JSON、机会地图文档和 BF 资产；部署时映射到持久卷。目录定义：`mmn_data.py`、`docker-compose.yml`。

### 6.3 权限

- 本地默认 `MMN_CLOUD_LOGIN_REQUIRED=false`，用于单机开发；云端 Compose 默认要求登录。实现：`server.py`、`docker-compose.yml`。
- 登录成功后服务端签发带 HMAC 校验和有效期的会话；Cookie/角色校验逻辑位于 `server.py`，本文不记录任何密钥或账号值。
- 角色至少区分 `admin` 与 `trial`。管理员可写入、导入、清理和管理；试用角色仅允许白名单 POST 能力，其他写操作由 `TRIAL_POST_ALLOWED_PATHS` 与路由权限规则限制。实现：`server.py`；说明：`README_DEPLOY.md`。
- 数据读取/写入按 `org_id`、`user_id` 与 `edition` 进行作用域约束；部分明确的公共演示快照存在受控回退，但不得泛化为跨租户访问。实现：`server.py`、`app.js`、各 repository。

## 7. 已知问题与 TODO

- 尚无仓库 CI 配置，`npm run check:mmn-state` 只能本地执行；待建立 CI 后使用 `--base` 对 PR 基线检查。
- `server.py` 是超大单体路由/业务入口，模块边界虽已部分拆出，但修改时回归面较大；本机制不进行业务重构。
- 当前存储是 SQLite、JSON/文件、浏览器状态与 PostgreSQL 目标结构并存；全系统 PostgreSQL/RDS 迁移尚未完成。
- 多个页面混合真实导入、缓存、内置种子、演示和降级结果；对外输出必须继续显示状态语义，不能把缺失/超时变成业务结论。
- Eval 当前按离线最终输出发布门禁记录；除非有新鲜调用链证据，不得描述为在线请求时强制执行。
- 全球版跨语言数据、RAG 和区域合规能力存在规划/占位项，尚不能表述为完整真实数据能力。
- 外部数据、异步任务和内容生产必须验收实际下游资产；任务进度 100% 或 HTTP 200 不是最终成功证明。
- 抖音原页取证受平台登录、风控、网络与媒体大小限制；服务器无头浏览器只访问公开原页，不绕过验证。失败时保留可追溯原因并降级，不用标题或互动率模板补齐。

## 8. 最近改动

- 2026-07-20：建立长期系统状态包机制：在 `AGENTS.md` 增加永久维护规则，创建本文件，新增 `scripts/check_mmn_state.mjs`，并在 `package.json` 增加 `npm run check:mmn-state`。
- 2026-07-21：大版本升级为 `beta 1.03`，在现有抖音六榜与品牌车型雷达后增加手动逐条视频洞察和热点内容防线；建立证据包、三路独立分析、交叉校验、分歧/降级、缓存幂等、刷新恢复与服务器端公开原页浏览器取证链路。
- 2026-07-21：修复管理层销量预警与下方T周期的上下文断链；八台重点车型从已核验周期记录继承T0、考核日、T+X、阶段与七段日期，服务端记录优先且本地仅作失败缓存，移除E7X硬编码默认日期，并保护权威T0不被下方普通保存覆盖；代码提交 `37058d6` 已部署至 GitHub `main` 与 ECS `/opt/mmn-perception-engine`。
- 2026-07-22：修复竞争趋势详情在稀疏周期下只有点、没有线以及横轴标签重叠的问题；跨无记录周期使用带图例说明的虚线，横轴最多显示 6 个关键刻度，完整周期仍保留在明细表。功能提交 `030c76e` 与发布状态提交 `72ecb1c` 已推送到 GitHub `main` 并部署至 ECS。

## 9. 验证状态

- 状态包事实来源：本轮已审查 `README.md`、`README_DEPLOY.md`、`AGENTS.md`、`package.json`、`Dockerfile`、`docker-compose.yml`、`index.html`、`app.js`、`server.py`、`mmn_data.py`、模块 repository/schema、路由知识图谱与目录结构。
- 状态检查命令：`npm run check:mmn-state`。检查业务源码、页面/组件、接口、schema、依赖与部署配置；测试、普通文档、锁文件及 `data/`、`output/`、`tmp/`、`backups/`、`logs/` 运行数据/产物不触发状态同步要求。
- 2026-07-21 beta 1.03 新鲜验证：完整 Python 回归 `467/467` 通过，逐视频洞察与媒体专项 `48/48` 通过，内容防线、启动器和状态包脚本测试通过；本地与生产健康接口均返回 `beta-1.03-20260721-douyin-content-defense-1`。生产全表面桌面/390px 检查无失败、运行时错误或失败响应；真实点击视频任务 `afecda8b179142a19cd96638f8717818` 形成 full 证据、三路独立完成并达到 `verified`，刷新后两端均显示“洞察已完成”，无页面溢出、控制台错误、失败请求、内部错误文案或证据哈希串。服务器另对第二条 117.5 秒视频取得 6 个时间点关键帧，证明取证不依赖固定样本。
- 2026-07-21 销量预警—T周期联动发布验证：集成主线后 Python 全量 `477/477` 通过，新增/相关 Node 周期、适配、持久化与UI契约通过；生产真实浏览器在 1440px 与 390px 验证 MG4 `T+84`、奥迪E7X `T+49`、红色预警奥迪E5 Sportback `T+304`，三车均为上下同车、同考核日、七张真实日期卡和自动当前阶段，刷新后仍保持最后选择车型；生产全页面门禁失败项、运行时错误与失败网络响应均为 0。部署前后八台已核验周期记录数量与 SHA-256 完全一致。`scripts/release_gate.sh` 的本工单语法/周期专项/150项后端子集均通过，但全门禁仍被既有 NSR 地图标签重叠检查拦截（530px 图面检测到 7 处重叠，`runtimeErrors=[]`），未在本工单越界修改。
- 2026-07-22 竞争趋势图本地发布验证：Python 全量 `477/477`、专项 Node 契约、前端语法、状态包门禁及 `scripts/release_gate.sh` 的 150 项后端子集均通过；桌面/390px 全表面门禁覆盖 19 个客户页面和 8 个管理视图，失败项、运行时错误和失败响应均为 0。真实业务路径选择“汽车之家 → 奥迪E7X → 奔驰GLC EV”后，弹窗呈现 4 段跨缺失周期虚线、6 个横轴关键刻度且标签重叠为 0，控制台错误为 0。全门禁仍只被既有 NSR 地图的 3 项断言拦截（竞品数量、单气泡语义、530px 下 7 处标签重叠），`runtimeErrors=[]`，与本轮竞争趋势图改动无关并未越界修改。
- 2026-07-22 竞争趋势图生产发布验证：部署前分别完成代码、配置和完整 `/app/data` 备份并生成 SHA-256；部署后版本为 `beta-1.03-20260722-trend-legibility-1`，发布文件与 Git 提交指纹一致，6 个服务均运行且健康日志错误计数为 0。部署前备份与部署后数据库逐表逐行逻辑对比覆盖 61 张表，变化表为 0；配置与 `sales_warning_cycles.json` 指纹不变。经生产 SSH 隧道完成桌面/390px 全表面真实登录验收，失败项、运行时错误和失败响应均为 0；“汽车之家 → 奥迪E7X → 奔驰GLC新能源”线上弹窗呈现 2 段跨缺失周期虚线、6 个横轴关键刻度、标签重叠 0，控制台错误与失败响应均为 0。公网域名 `mmnsh.com` 当前被阿里云 ICP 合规页返回 403，属于域名入口外部阻断，不影响本次容器内发布与隧道验收，仍待备案/入口侧处理后补做公网直连验收。
- 仓库没有独立 lint 命令；前端/Python 语法检查已由 `scripts/release_gate.sh` 执行。PPT 生成命令会生成交付产物，不属于本次状态机制影响面，未额外执行。

## 10. 后续每次任务的固定汇报格式

1. 已实现内容；
2. 修改文件；
3. `MMN_CURRENT_STATE.md`：已更新，具体更新了什么；
4. `npm run check:mmn-state`：通过 / 未通过及原因；
5. 验证结果；
6. 已知风险或待办。
