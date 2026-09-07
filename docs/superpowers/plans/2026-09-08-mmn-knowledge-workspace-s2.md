# MMN 知识工作区 S2 实施计划与接口准入检查

> 状态：2026-09-08 Ellis 回复“同意”，明确批准专用安全只读接口补充范围。Task 2/3 实施与验收已通过；Task 4 Git和双环境发布中。

**Goal:** 将已评审的知识阅读体验接入原 RAG资产库内容区，并在真实本地 8765 与正式服务器验证。

**Architecture:** 保留旧策略查询、导入、导航与数据。独立的只读知识阅读模块通过经过权限验证、无初始化副作用的读取边界获取真实资产；缺失证据、关联、版本、审核记录如实降级。现有接口未通过准入，不能直接接入。

**Tech Stack:** 现有原生 JavaScript、CSS、Python HTTP 服务、SQLite；不新增依赖、数据库或检索引擎。

## Global Constraints

- MMN 与 Essence、Sales Credo 保持独立；不改全局导航名称、顺序、入口或路由语义。
- 只读接入不得初始化、建表、迁移、认领、回填或修改业务库；不得用浏览器缓存代替可信权限边界。
- 原文与元数据都是不可信输入。禁止 HTML 注入、危险链接、内部路径或凭据泄露。
- 不生成假的来源、审核、有效期、引用数量、版本历史或知识关系；关键词相似不等于支持或冲突。
- 保留现有主题与字体，复用 --surface、--bg、--line、--text、--ink、--blue、--radius-lg；不引入营销页模板或新字体。
- 不部署主工作区的无关未提交改动；不覆盖本地受管运行可靠性修复或业务状态。
- 原工单 §3、§6.4 要求接口/schema 变更先确认，发现读取副作用先阻断。本计划不能自我授权修改接口。

## Task 1: 读取链路与运行身份准入

- [x] 从 origin/main 创建隔离分支 codex/mmn-knowledge-workspace-s2-20260908；原脏工作区不动。
- [x] 索引隔离工作区并检查现有 RAG 页面、读取链路、权限与字段。
- [x] 核对本地 8765 使用受管物理 release，不直接使用 Git 工作区。
- [x] 记录真实页面修改前截图：output/playwright/mmn-kw-s2-before-8765.png。
- [x] 发现以下阻塞，停止正式代码修改。

### 实证与边界

1. origin/main 的 server.py:15685 处理 GET /api/asset-library 时调用 current_auth。current_auth:15419 对管理员调用 ensure_legacy_vertical_claim。
2. ensure_legacy_vertical_claim:2064 可以调用 claim_legacy_vertical_scope。后者在历史资料全部属于 local 等条件满足时，对四张垂直资产表执行 UPDATE org_id；并非纯读取。不能因为某次请求恰好没有写入就认定接口只读。
3. durable_asset_library:1876 的 strategyAssets 按 org_id、edition 过滤，但没有项目维度；其中 bloggerProfiles、bloggerSamples、contentChunks、contentSources 统计只按 edition 过滤。不能把它们当作当前客户/项目资产统计。
4. 当前本地物理 release 的 server.py 同样存在管理员认领调用和不含 org_id 的统计查询。不是只在开发分支存在的问题。
5. 没有对生产进行副作用复现，没有证据表明本次发生了跨客户数据泄露或数据改写；以上是代码可达行为与接入合同不相容的发现。
6. 主代理通过 AST 提取原 claim_legacy_vertical_scope 函数、在纯内存 SQLite 中设置四张各一行的测试表，确认该函数造成 4 次 UPDATE；没有导入服务模块或打开真实业务库。
7. server.py:15613-15615 已有统一的 /api/ 云端鉴权门禁。独立审查初稿遗漏该前置门禁，提出的“未登录可直接读取”结论被主代理复核否定，不纳入发现。管理员读时写入和统计口径问题仍成立；不能将此描述为已验证的未登录泄露。

## 已确认的最小范围补充

允许为 S2 增加专用的受认证只读资产读取接口及必要的无副作用认证解析路径；保留旧接口及旧业务行为，不改变数据库 schema、不搬迁/认领数据、不启用 B3、新检索或编辑审核。客户端不得传入任意客户身份取数。

现有资产若只有客户+国内/出海维度，应明确标为“客户级共享知识”，不可伪称项目隔离；具有可验证项目归属的记录才可按其实际授权展示。若需新增项目权限模型或数据回填，另行提请确认。

## Task 2: 只读接口

**Files:** 新建 knowledge_workspace_reader.py、tests/test_knowledge_workspace_reader.py；server.py 只增加必要路由和无副作用认证分支，禁止顺手重构全局认证。

接口决策：`GET /api/knowledge-workspace`，由服务端认证决定 org_id，严格 edition 校验。专用读取必须在旧通用 API 鉴权（会调用 claim）之前进入无副作用认证路径；旧路径默认行为保持。SQLite 使用只读连接并及时关闭。复用 token 校验，若旧 token 需要 scope 解析，其查询亦须使用只读连接，或 fail-closed 要求重新登录，不触发 legacy claim。

返回受控 DTO：`ok, edition, scope: organization, items, total, offset, limit, hasMore`；分页默认 50、上限 100；支持标题/正文 `q` 和真实类型 `type` 筛选，计数与过滤一致。每项 `id,title,body,type,brand,module,createdAt,updatedAt,sourceLabel,sourceUrl`（缺失为 null/空），以及 `reviewStatus: unavailable, validity: unknown`；不返回原始 metadata 或未验证审核/版本字段。前端可用的类型仅“原始材料、知识结论、方法论、案例、未分类”，只映射明确元数据值，不猜测。来源标签不等于原文证据；URL 为安全、无凭据的 http(s) 链接时才输出，仍标记未核验。数据库实际 updated_at 可以显示为记录更新时间，不当成事实有效时间。数据库 ID 仅用于选择，不作为版本。

项目策略：当前接口只呈现组织共享资料；任何显式 project/projectId/project_id 归属（包括 metadata 中）的资料均不混入此共享视图。不接受客户端 org_id 改写；显式 project 查询拒绝或报不支持，不假装实现新项目权限模型。数据字段类型非法/超大/JSON 非法时 fail-closed 明确错误或明确不可展示，禁止偷偷丢弃后仍报完整成功。新接口不得返回 legacyCreators 或跨组织 counts。

筛选补充：支持真实 `brand`、`module` 精确筛选；返回当前已授权共享资产的 `facets.brands` 和 `facets.modules`，用于目录选择，不能只过滤当前页而把结果当作完整命中。元数据 `knowledge_type=case/framework/analysis_method` 可分别明确映射为案例/方法论/方法论；原 `type` 为非资产类型标签时才用此回退，其他不明类型保持未分类。读连接必须关闭，扫描行数、单条/总字节必须有上限并明确失败，不以分页掩盖无限制全量读入。来源 URL 的非法结构/凭据不得原样输出。

- [x] 先写隔离 SQLite 的失败测试：读取前后逻辑数据一致；无表不得创建；未登录拒绝；A/B 租户隔离；国内/出海隔离；未知字段不伪造；未授权项目记录不可见。
- [x] 实际运行测试，确认因目标行为缺失而失败，保留 RED 输出。
- [x] 实现只读连接（mode=ro/query_only）和最少字段投影；不导入会初始化服务的模块；复用可证明无写入的身份校验。
- [x] 返回真实标题、正文和可信元数据；错误不泄露内部路径；不得返回无客户归属的全局统计。
- [x] 运行 `python3 -m unittest discover -s tests -p 'test_knowledge_workspace_reader.py'`、相关认证/租户合同测试及 `python3 -m py_compile server.py knowledge_workspace_reader.py`。
- [x] 独立审查需求、测试、实际 diff；Critical/Required 清零后进入页面接入。

## Task 3: 原 RAG资产库阅读区域

**Files:** 新建 knowledge-workspace.js、knowledge-workspace.css、tests/test_knowledge_workspace.js；最小修改 app.js 的知识地图挂载点、index.html 的原内容区与静态引用、服务端/代理的静态文件白名单。

界面合同：在原 `#strategy-kb-map/#strategy-kb-list` 面板内呈现“知识阅读工作区”，一级导航及 `RAG资产库` 命名不变。目录中有标题/正文搜索、类型筛选、品牌/模块筛选（仅用真实字段）、分页与真实命中计数；中央正文；右侧证据/来源信息。版本/关联/审核没有可信记录时明确显示未提供，不显示假的 0 次审核或版本 v1。可折叠旧分类浏览作为回退，不重复占据默认页面。桌面采用紧凑主从布局，390px 列表→正文→证据逐层切换，提供返回且保留筛选、页码、选中与滚动位置。正文保持纯文本（不执行 HTML），长内容换行；无来源链接不造可点击按钮。

生命周期合同：只在 `window.mmnAuthReady` 且原 `#strategykb` 页面活跃时发出新 GET；退出页、身份变更、国内/出海或项目切换立即清除敏感详情并失效旧响应。旧 `showPage()` 在切换 active class 前先 render，需明确活跃页挂载时机；同组织不同用户登录也必须失效（不能只比较 browserStorageScope 的 org+role）。使用现有认证头，但阅读区自身没有 localStorage 或写接口；所有请求 no-store、可取消并有 generation guard。搜索/翻页前清除旧详情，失败状态与空库分开，提供重试。POST 导入成功后只能使阅读快照失效，不使用旧缓存资产冒充服务端返回。

验证采用纯 Node 的模块行为测试与现有 Playwright CLI 真浏览器（不新增 @playwright/test 框架）；无新第三方依赖。最终版本、缺失能力、真实截图与完整命令结果由主代理记录。

已有设计输入：原工作区 `output/mmn-knowledge-workspace-s1/`（仅可借鉴布局，不复制样例数据到正式模块）；本隔离工作区修改前截图 `output/playwright/mmn-kw-s2-before-8765.png`。该页面属于高密度产品工作区，taste-skill 仅采用审计/可访问性原则，不采用落地页模板、图像生成或默认新技术栈。为保持接口/UI解耦，模块提供可测试的异步读取控制器与独立 DOM 视图，根 app.js 只保留挂载/上下文生命周期钩子。

- [x] 测试先行：字段投影、搜索计数、空结果、缺证据、加载失败、身份/版本/项目快速切换及旧响应不覆盖新上下文。
- [x] 分类/搜索、目录、正文、证据/关联侧栏和版本/审核记录区使用真实数据；无记录用明确的缺失状态。
- [x] 切换身份清除详情及待处理请求；不持久化新阅读缓存，不向旧 strategyKb 数组写回。
- [x] 保留旧查询/导入入口与行为；不替换现有模型或检索来源。
- [x] `node --test tests/test_knowledge_workspace.js`，`node --check app.js` 和新模块；执行相关前端权限、XSS、RAG 合同回归。
- [x] 真实浏览器检查 1440、1280、390px；操作目录、搜索、详情、返回、错误重试；检查焦点、溢出、网络和控制台，保存截图。
- [x] 独立审查实际 diff，复核所有门禁；不以原型截图当作正式验收。

## Task 4: Git 与双运行环境发布

**Files:** docs/研发档案/ 本轮记录、MMN_CURRENT_STATE.md、必要的精确发布清单；现有受管发布脚本默认不修改。

- [x] 记录新鲜定向/回归/构建结果、独立审查结论、缺失能力与风险，运行 `npm run check:mmn-state`。
- [x] 核对精确 diff 后提交并推送授权发布分支；不包含主工作区无关修改。
- [x] 本地基于现用物理 release 制作可回退候选，保留受管启动、配置、状态和数据分离；通过现有发布/安装流程切换。
- [x] ECS 基于核验的正式版本和精确 Git 制品发布，保存回滚点，不在服务器手改代码或覆盖业务库。
- [x] 本地验证 `/`、`/api/ready`、真实业务接口、8765 页面与数据前后对照；ECS 验证正式应用而不是 18792 独立原型。
- [x] 最终报告区分：实现、测试、提交、推送、部署、启用、真实验收；备案不在本轮范围。

## 本轮实际变更

Task 2、Task 3、Task 4均已实施：后端15项、前端11项、完整门禁758项Python/37份前端测试文件/98项既有浏览器检查通过，独立审查Critical/Required清零。代码f7ca19d已推送，受管8765及ECS正式应用已启用同一S2功能版本；实际本地21项、正式服务器14项页面验收通过，本地86/9/7/1表、ECS84/9/7表逻辑变化0。未迁移schema或启用新检索；服务器项目关联知识不混入共享视图。完整回滚资料、真实空态、旧启动POST隔离及此前可能供应商请求的未知次数/费用风险见本轮研发档案和release.md。
