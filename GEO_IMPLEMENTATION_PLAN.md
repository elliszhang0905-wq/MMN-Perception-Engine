# MMN GEO Implementation Plan

> **For agentic workers:** 使用 subagent-driven-development 的隔离任务与独立审查；步骤采用复选框。当前用户授权只开发和离线测试，所有 commit / deploy 步骤均不执行。

**Goal:** 在现有 MMN 完成问题、采样、证据、诊断、复核、动作、复测、导出的首版闭环。

**Architecture:** 复用主 SQLite、签名组织权限、车型资产、原生导航和样式。GEO 模块自行承载新增业务逻辑，服务器仅接线；worker 与模块开关相互独立。真实联调按用户最新指令保持阻塞。

**Tech Stack:** Python 标准库、SQLite、原生 JavaScript / CSS、unittest、现有 Node 合同测试。

## Global Constraints

- 首版 P0 不削减；真实调用、离线 fixture、人工 App 样本显式区分。
- 不覆盖既有脏改动、不写原业务数据、不新增依赖、不触碰 Credo/Essence。
- 所有业务记录和关联使用 org_id；问题、条件、事实与批次清单不可变。
- 真实采样默认关闭；没有凭证、模型、单价与明确配额时不能排队付费调用。
- 费用属于 attempt，超时未知保留 uncertain，不自动重新计费；原始证据不被复核覆盖。
- 客户界面沿用中文中性能力标签，技术配置仅管理员可见。
- 只增加工单授权 GEO 一级入口和驾驶舱小型摘要，复用当前视觉 Token。
- 先观察失败测试，再实现，再运行测试、浏览器验收与独立审查。
- 验收补充：提及/推荐按问题等权，无法判定单列并显示覆盖率；自动分析缺失、待复核、零可判定问题、重复数不一致均以可手算测试验证，边界未定义保持明确未知。
- P0人工App导入与证据查看必须是可操作页面，不能只交接口契约。
- 客户驾驶舱只投影已经人工复核的诊断、对应证据和改进任务状态；未复核建议只留内部GEO工作台，保留原始证据与审计。

## 冻结接口

`GeoRepository(db_path)`：新增表，所有方法第一个业务参数为 org_id。`GeoService(repo, settings, provider=None)`：权限外的业务编排。`dispatch(handler, parsed, db_path)`：复用 handler.require_cloud_auth() 后组织归属派发，不自行创建认证。

提供方 `ArkProvider(settings).sample(question: dict, condition: dict, cancel_event=None) -> dict`。condition 包含 surface、api_mode、mode、model、max_output_tokens、timeout_seconds、system_prompt_version、system_prompt、temperature、seed、capabilities；返回 status、answer、raw_response、request_id、actual_model、usage、search_requested、search_observed、search_events、citations、capabilities、error_class、retry_after、billing_uncertain、started_at、finished_at。一次 sample 只对应一次网络 attempt。

分析 `analyze_answer(answer, entities, facts=(), observed_at=None, question=None) -> dict`；entities 每项含 key/name/brand/aliases/year/trim；输出 valid_answer/refusal、entities（entity_key/mentioned/recommended/rank/evidence/start/end/needs_review）、fact_checks（claim/verdict/evidence/baseline_id/reason）、version。引用由提供方输出，不由分析补造。`compute_metrics(records, target_key, fixed_entities) -> dict` 输入记录含 question_version_id/question/condition/channel/status/answer/analysis/citations/attempts/reviews。

HTTP 成功 `{ok:true,data:...}`；失败 `{ok:false,error,code}`。列表 data 为 `{items,total,limit,offset}`；详情 data 为单项对象；ID 统一 `id`。路径详见 `output/geo-20261008/ui-contract.md`，该契约由根执行者维护。

## Task 1: 诊断、基线与范围（GEO001）

- [x] 读取工单 MD/DOCX、AGENTS、必读交接与架构文档、图谱。
- [x] 核查当前主库 schema/quick_check 和变量存在性，不输出秘密。
- [x] 记录原 8765 桌面截图与工作树基线。
- [x] 写入 `GEO_DISCOVERY.md` 与本文件；真实联调按用户最新指令 blocked。

## Task 2: 提供方契约（GEO002）

Files: `geo/provider.py`, `tests/test_geo_provider.py`。

- [x] RED：验证 Chat/Responses/助手输入与输出契约，联网未发生不能冒充已搜索；覆盖 JSON/SSE、引用、缺配置、401/403/429/5xx、超时、取消、秘密脱敏。
- [x] 实现单次安全 HTTP 调用，模型来自配置、无历史上下文，搜索工具与助手独立适配，重试由 worker 记账。
- [x] GREEN：`python3 -m unittest tests.test_geo_provider -v`；真实联网样本继续 blocked。

## Task 3: 抽取与指标（GEO006/007）

Files: `geo/analysis.py`, `geo/metrics.py`, `tests/test_geo_analysis.py`, `tests/fixtures/geo_semantic.json`。

- [x] RED：至少30条标注回答；比较/负面/复述不算推荐、短别名歧义复核、明确编号才排序。事实无证据为 unverified，CLTC/WLTC与年款配置分开。
- [x] 实现有片段位置的确定性识别、原子事实核对、拒答与非答案分类。
- [x] 实现按问题等权/回答级显式口径、不同条件与渠道分组、空分母 null、固定问题清单及失败可见。
- [x] GREEN：12次请求10个有效回答4提及3推荐，回答级为40%/30%；不同适用集合独立分母。

## Task 4: 数据、版本、异步与限额（GEO003/004/005）

Files: `geo/migrations/001_geo.sql`, `geo/repository.py`, `geo/service.py`, `geo/worker.py`, `scripts/run_geo_worker.py`, `tests/test_geo_repository.py`, `tests/test_geo_worker.py`。

- [x] RED：版本冻结、跨租户读写、幂等参数冲突、租约竞争、重启未知、重试 attempt、取消与暂停、原子日/批次额度、单价未知、失败费用留存。
- [x] 实现新增表与索引、不可变版本、租户关联、50个明确标识示例问题；不初始化原业务数据。
- [x] 实现 draft/queued/running/completed/completed_with_errors/cancelled/blocked，暂停用独立标志；重试留在同一实验观测，未知不自动重发。
- [x] GREEN：`python3 -m unittest tests.test_geo_repository tests.test_geo_worker -v`，仅临时数据库。

## Task 5: 证据、复核、改进、App与复测（GEO006/009/010）

Files: `geo/service.py`, `geo/api.py`, `tests/test_geo_api.py`, `tests/test_geo_workflow.py`；server.py 最小接线。

- [x] RED：原始证据不可被复核改写、导出隔离与CSV公式安全、截图仅鉴权读取；人工App缺字段为unknown、仅截图不出精确指标。
- [x] 实现项目/问题/条件/事实/批次/观测/复核/动作/复测/指标/审计分页 API。
- [x] 实现诊断证据下钻、动作审核/执行证据、同清单复测和不匹配警示；无执行证据不能标记优化完成。
- [x] GREEN：隔离 HTTP 签名租户A/B，12请求手算样本和一条完整离线闭环。

## Task 6: MMN 页面（GEO008/010）

Files: `geo.js`, `geo.css`, `tests/test_geo_ui.js`；index.html/app.js 最小集成。

- [x] RED：开关、导航、真实API绑定、空态、分页、请求保护、转义、无伪造成绩。
- [x] 实现概览、问题库、采样任务、回答证据、诊断与改进、设置；管理员技术设置只读，提供App导入与事实/别名编辑。
- [x] 驾驶舱摘要下钻当前项目，不替换声量或机会地图。
- [x] GREEN：Node语法/合同与真实浏览器创建项目→问题版本→人工样本→复核→任务→复测，桌面/窄屏截图。

## Task 7: 收口与回归（AT01—AT16）

- [x] 写实际数据字典、指标、运行手册、验收报告、研发档案；更新 MMN_CURRENT_STATE.md。
- [x] 定向及受影响回归、语法/静态检查；此仓库没有应用打包构建，验证原生静态资源与Python可编译，容器发布不在授权范围。
- [x] `npm run check:mmn-state`；本轮独立审查实际新增代码和相对工作树基线的差异，修复 Required/Critical 后重验。
- [x] 保存测试退出码、截图、原业务主库哈希前后、真实联调阻塞与费用0（本轮未调用）证据。
- [x] 报告开发、离线验证、真实联调、试点、发布状态分别列示；不以框架搭建代替工单完成。

## 最终结果

2026-10-08：首版离线开发与可执行验证收口，134项GEO Python、66项MMN回归、54项GEO前端及6个既有脚本通过。桌面/390px实际页面、下载CSV、冻结旧版复测、原库哈希和独立审查见 `GEO_ACCEPTANCE_REPORT.md`。复选框代表已完成本步骤中被授权的离线工作；其中真实普通/助手/联网、真实App配对和试点仍明确BLOCKED/未完成，未提交、部署或启用正式环境。
