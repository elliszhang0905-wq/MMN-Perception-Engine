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

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-10

## 发布版本

beta 1.01

## 发布负责人

MMN研发团队

## 发布目标

修复本机没有全局 Node.js 时发布门禁静默退出的问题，使本地开发环境可以直接完成语法检查、研发档案检查和浏览器检查，并将修复、交接说明与发布记录同步到 GitHub 和服务器。

## 本次变更

- `scripts/release_gate.sh` 不再因 `command -v node` 失败而在 `set -e` 下静默退出。
- Node.js 解析顺序统一为显式 `NODE_BINARY`、系统 `PATH`、本机内置运行时。
- `NODE_BINARY` 同时兼容绝对路径和 PATH 中的命令名。
- 显式配置无效时直接报错，不静默切换到其他 Node.js 版本。
- 新增对应研发档案，并更新研发交接手册。

## 影响范围

- 仅影响本地与服务器代码库中的发布门禁脚本和研发记录。
- 不改变 MMN 页面、后端接口、数据库结构、模型路由、定时任务或登录权限。
- 服务器部署仍沿用现有 Docker Compose 流程；部署前备份运行数据和当前代码归档。

## 本地测试结果

- 自动发现本机内置 Node.js：完整发布门禁 16 项检查通过，`failed: []`、`runtimeErrors: []`。
- `NODE_BINARY=node`：完整发布门禁 16 项检查通过。
- `NODE_BINARY=/path/to/node`：完整发布门禁 16 项检查通过。
- 显式无效 `NODE_BINARY`：退出码 1，并输出明确错误。
- Node.js 完全不可用：退出码 1，并输出明确错误。
- `bash -n scripts/release_gate.sh` 与 `git diff --check` 通过。

## GitHub 与云端发布结果

- GitHub Commit：`fb3dfdf fix: make release gate resolve bundled Node`。
- 服务器目录：`/opt/mmn-perception-engine`。
- 同步方式：GitHub `main` 推送后，使用 `fb3dfdf` 已提交文件归档同步到无 `.git` 的服务器目录，再执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`。
- 部署时间：2026-07-10 04:48（Asia/Shanghai）。
- 发布前数据备份：`backups/mmn_backup_20260710_044802.tar.gz`。
- 发布前代码归档：`backups/code_before_fb3dfdf_20260710_044756.tar.gz`。
- 容器状态：`mmn-app` healthy、`mmn-db` healthy、`mmn-scheduler` healthy、`mmn-web` running。
- 健康检查：`http://121.40.60.90/api/health` 返回 `ok: true`、`version: beta 1.01`。
- 公网基础检查：`bash scripts/test_mmn_cloud.sh http://121.40.60.90` 通过首页与健康接口检查。
- 文件一致性：服务器 `scripts/release_gate.sh` SHA-256 为 `cdc827a8b5e07d5f64d9ae5a0af61c36b6755c44e3003b73cabfb4cc730ac47e`，与本地提交一致。
- 发布后日志：应用、Web 与定时任务近 5 分钟未发现 `traceback`、`exception`、`critical` 或 `error`。

## 回滚方案

如发布后出现异常，恢复本次发布前的服务器代码归档，保留 `.env` 与运行数据，再执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`；如涉及数据问题，使用本次发布前生成的数据备份恢复。

## 发布结论

发布门禁 Node.js 运行时解析修复、研发档案、交接手册与发布记录已同步到 GitHub 和阿里云服务器；公网服务与容器状态健康。

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-10

## 发布版本

beta 1.01｜BF工厂 P0

## 发布目标

发布品牌商业化内容 Brief 生成与训练系统，打通“原始BF上传 → 结构化与溯源 → 历史样本检索 → 自适应BF生成 → 在线校正 → Word导出 → 最终版回流”的 MMN 商业闭环。

## 本次变更

- 新增 BF工厂与BF资产库一级入口，以及新建BF、种子范式快捷入口、人工业务字段校正、证据展示和Word导出。
- 新增 `bf_factory/` 领域模块、A–F六层JSON Schema、项目/客户隔离数据库、文件解析、标签、来源和版本记录。
- 探店、云评/口播、高质感摄影仅作为种子范式；未知和混合需求进入 `CUSTOM` 并动态组合章节。
- 优质自定义终稿可沉淀脱敏范式，并被后续相似需求实际召回；反例只用于风险，禁用样本不进入生成。
- 接入 DeepSeek策略判断、Qwen初稿、DeepSeek风险复核，并保留模型不可用时的可编辑降级结果。
- 默认对外部模型输入脱敏；原始文件按组织、客户和项目隔离。
- Docker增加LibreOffice、中文OCR和Noto CJK字体，支持旧版Office转换、扫描件识别和中文Word导出。
- Docker系统依赖安装切换到阿里云Debian镜像源，并设置超时与重试，避免ECS访问官方源时长时间挂起。
- 同步发布决策驾驶舱指标市场策略表达、平台筛选和对比展示优化。

## 本地测试结果

- BF完整单元与集成测试：28/28通过。
- 系统Python兼容与HTTP端到端测试：4/4通过。
- `bash scripts/release_gate.sh` 通过，`failed: []`、`runtimeErrors: []`。
- `git diff --check` 通过，提交内容未发现密钥或真实客户资料。
- Word样例中文首屏、两页版式和PDF文本层检查通过，无裁切或重叠。

## 发布与回滚要求

- GitHub目标分支：`main`。
- ECS目录：`/opt/mmn-perception-engine`，该目录无 `.git`，需使用提交归档同步。
- 发布前创建服务器代码归档和运行数据备份。
- 同步后执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`，再验证容器、首页、`/api/health`、BF页面与Schema接口。
- 如发布异常，恢复本次发布前代码归档并重新部署；运行数据默认保留，如涉及数据问题再使用发布前备份恢复。

## 云端发布结果

- GitHub功能提交：`e5b21f0 feat: ship adaptive BF factory P0`。
- GitHub构建修复：`7e769d5 fix: stabilize BF image build on ECS`。
- 服务器目录：`/opt/mmn-perception-engine`，使用 `7e769d5` 提交归档同步到无 `.git` 发布目录。
- 部署时间：2026-07-10 19:19（Asia/Shanghai）。
- 发布前代码归档：`backups/code_before_e5b21f0_20260710_191059.tar.gz`。
- 最终部署前运行数据备份：`backups/mmn_backup_20260710_191652.tar.gz`。
- 首次构建访问Debian官方源长时间无进展，旧服务已先恢复；切换阿里云镜像源后，10.1MB索引约2秒完成、218MB依赖下载和安装成功。
- 容器状态：`mmn-app`、`mmn-db`、`mmn-scheduler` healthy，`mmn-web` running。
- 公网检查：`bash scripts/test_mmn_cloud.sh http://121.40.60.90` 通过首页和健康接口；`/api/health` 返回 `ok: true`、`version: beta 1.01`。
- BF前端资源：公网首页包含 `BF FACTORY` 和 `bf-factory.js?v=beta-1.01-bf-p0-1`。
- 生产镜像测试：设置仅作用于测试进程的免登录开关后，BF完整测试28/28通过。
- 生产依赖：LibreOffice `25.2.3.2`、Tesseract `chi_sim/eng/osd`、`Noto Sans CJK SC` 均已验证可用。
- 云端认证验证：管理员登录后 `GET /api/bf/schema` 返回 `schemaVersion: 1.0.0`，A–F六层字段完整。
- 发布后日志：近10分钟未发现 `traceback`、`exception`、`critical` 或 `error`，`RECENT_ERROR_LINES=0`。

## 发布结论

BF工厂 P0、开放式范式学习、资产回流、Word导出、客户项目隔离、默认脱敏、驾驶舱策略表达优化及全部交接记录已同步至 GitHub 和阿里云 ECS。公网服务、生产依赖、容器、BF认证接口和回滚备份均验证通过。

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-10

## 发布版本

beta 1.01｜BF产品规则外显清理

## 修复内容

- 删除BF工厂顶部将内部产品规则直接展示给用户的说明横幅。
- 隐藏BF工厂顶部重复的生成器横向子菜单，减少页面层级和视觉噪音。
- 新增静态实拍、动态实拍、底盘实拍三种BF类型及对应生成章节和执行要求。
- 清理BF快捷入口、生成稿、证据空状态、回流提示和文件状态中的内部机制文案。
- 保留智能识别、自定义内容方向、历史证据、安全开关和终稿回流等业务能力。
- 新增单元测试与浏览器发布门禁，阻止内部规则再次进入BF页面或交付稿。
- BF前端资源版本更新为 `beta-1.01-bf-ui-2`，强制刷新修复后的页面和交互脚本。

## 发布要求

- 本地完整测试和发布门禁通过后推送 GitHub `main`。
- 服务器发布前创建代码归档和运行数据备份。
- 同步到 `/opt/mmn-perception-engine` 后执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`。
- 发布后检查公网首页不包含本次清理短语，并验证健康接口、容器和近期错误日志。

## 云端发布结果

- GitHub功能提交：`0172cca fix: keep BF product rules internal`。
- GitHub缓存刷新提交：`5c9c561 fix: refresh BF factory frontend assets`。
- ECS最终部署时间：2026-07-10 19:43（Asia/Shanghai）。
- 最终部署前代码归档：`backups/code_before_5c9c561_20260710_194257.tar.gz`。
- 最终部署前运行数据备份：`backups/mmn_backup_20260710_194259.tar.gz`。
- 本地完整测试31/31通过；浏览器发布门禁通过，`failed: []`、`runtimeErrors: []`。
- 公网BF工厂已确认不含内部规则横幅，不含生成器横向子菜单，并加载 `beta-1.01-bf-ui-2` 前端资源。
- 公网页面已显示静态实拍、动态实拍、底盘实拍；生产类型库确认三种类型均已初始化。
- 生产容器内完整测试31/31通过；`mmn-app`、`mmn-db`、`mmn-scheduler` healthy，`mmn-web` running。
- `/api/health` 返回 `ok: true`；近10分钟日志 `RECENT_ERROR_LINES=0`。

## 发布结论

BF内部规则外显清理、重复子菜单隐藏、三种实拍BF类型、前端缓存刷新和全部交接记录已同步到 GitHub 与阿里云 ECS，线上验证通过。

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-10

## 发布版本

beta 1.01｜产品评价汇总表导入质量修复

## 修复内容

- 对“数据整理”产品评价汇总表按真实区块解析，禁止把情感字段、车型名或平均值误识别为平台。
- 从 `Read Me` 读取数据周期，并从文件名与车型列表确定本品，避免默认取第一款车型。
- 仅使用源表提供的全网NSR和属性NSR；目标人群、购买意向、标签声量和风险量级缺失时明确展示“不适用”。
- 旧版错误导入结果自动隔离并要求重新导入；缺少必要NSR区块的新文件直接拒绝导入。
- 新增结构化导入单元测试和浏览器发布门禁，覆盖真实字段边界、指标边界和旧数据隔离。

## 验证与发布要求

- 本地完整测试、汇总表专项测试、发布门禁和空白检查通过后推送 GitHub `main`。
- 服务器发布前创建代码归档和运行数据备份；使用提交归档同步到 `/opt/mmn-perception-engine`，再执行 `MMN_SKIP_GIT_PULL=true bash deploy.sh`。
- 发布后验证公网首页、健康接口、前端资源版本、容器状态、生产测试和近期错误日志。

## 云端发布结果

- GitHub提交：`768d7c4 fix: validate product summary workbook imports`。
- ECS部署时间：2026-07-10 22:05（Asia/Shanghai）。
- 发布前代码归档：`backups/code_before_768d7c4_20260710_220429.tar.gz`。
- 发布前运行数据备份：`backups/mmn_backup_20260710_220429.tar.gz`；部署脚本运行数据备份：`backups/mmn_backup_20260710_220444.tar.gz`。
- 本地完整测试33/33通过；专项汇总表测试2/2通过；浏览器发布门禁通过，`failed: []`、`runtimeErrors: []`。
- 公网首页和 `/api/health` 通过，首页已加载 `app.js?v=beta-1.01-summary-import-2`。
- 生产容器内完整测试33/33通过；`mmn-app`、`mmn-db`、`mmn-scheduler` healthy，`mmn-web` running。
- 发布后近10分钟日志未发现 `traceback`、`exception`、`critical` 或 `error`。

## 发布结论

产品评价汇总表导入已从“可被错误字段污染的推断”改为“按已验证区块和数据边界展示”。旧版错误结果会被隔离；同类不完整文件会被拒绝导入，防止再次生成看似正常但不可信的驾驶舱指标。

## 补充修复

- 替换导入现在同步刷新驾驶舱品牌、车型与平台筛选，不会保留上一项目的车型选择状态。
- 驾驶舱车型选择器只列出当前导入数据的车型；前端资源版本更新为 `beta-1.01-summary-import-3`。
- 已用 `AUDI E7X等5车产品评价_0710_v2.xlsx` 走通真实浏览器上传：本品奥迪E7X、全网NSR 75.1%、15个有效标签、数据周期2026.6.1–6.30，且页面无脚本错误。

### 云端补充发布结果

- GitHub提交：`4674cf8 fix: reset dashboard context on summary import`。
- ECS部署时间：2026-07-10 22:19（Asia/Shanghai）；发布前代码归档：`backups/code_before_4674cf8_20260710_221845.tar.gz`；部署脚本运行数据备份：`backups/mmn_backup_20260710_221848.tar.gz`。
- 公网首页已加载 `app.js?v=beta-1.01-summary-import-3`；健康接口正常。
- 本地及生产容器完整测试33/33通过；浏览器发布门禁通过，`failed: []`、`runtimeErrors: []`；近期生产日志无错误记录。

---

# MMN Perception Engine 发布记录补充

## 发布日期

2026-07-11

## 发布版本

beta 1.01｜整体平台NSR与属性NSR拆分

## 发布内容

- 从同一产品评价Excel中独立解析“车型 × 平台整体NSR”，保存为 `summaryPlatformNsr`，不再与产品点属性NSR混用。
- 整体平台NSR支持全网、垂媒车主口碑、抖音、小红书、微博、B站、视频号切换；车型筛选与声量模块同步，本品固定第一且不可移除。
- 点击车型后展示七平台气泡；竞品逐平台与本品对照，本品淡蓝、竞品粉红。
- NSR主图和气泡统一使用-100%至100%零轴，负值向左、正值向右；缺失值不转换为0。
- 全局吸顶样式限定到 `main>header`，修复滚屏后模块标题覆盖主导航的问题。

## 云端发布结果

- GitHub功能提交：`e7f19b1 feat: split overall platform NSR from attribute diagnostics`。
- ECS部署时间：2026-07-11 00:16（Asia/Shanghai）。
- 发布前代码归档：`backups/code_before_e7f19b1_20260711_001551.tar.gz`。
- 发布前运行数据备份：`backups/mmn_backup_20260711_001612.tar.gz`；部署脚本运行数据备份：`backups/mmn_backup_20260711_001632.tar.gz`。
- 公网资源版本：`style.css?v=beta-1.01-platform-nsr-split-1`、`app.js?v=beta-1.01-platform-nsr-split-1`。
- 真实 `AUDI E7X等5车产品评价_0710_v2.xlsx` 已验证5台车型、7个平台、正负值与缺失值均按源表读取；浏览器无横向溢出和控制台错误。
- 本地与生产容器完整测试33/33通过；发布门禁 `failed: []`、`runtimeErrors: []`；公网首页及健康接口通过，近期错误日志为0。
