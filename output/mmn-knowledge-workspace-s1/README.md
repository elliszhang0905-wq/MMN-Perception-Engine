# MMN 知识工作区 S1｜原型评审包

- 对应工单：MMN-KW-UX-20260908-001。
- 交付日期：2026-09-08；检查时间约 01:14（Asia/Shanghai）。
- 状态：S1 原型已制作并完成开发者自检，待 Ellis 评审；不等于 S1 已验收。
- 授权：本轮“开工”按工单 §7 承接 S1。S2 正式只读界面、S3 候选编辑审核均未授权、未实施。
- 当前预览：http://127.0.0.1:18791/ （仅本机临时静态预览）。

## 1. 交付与使用

本目录包含独立的 `index.html`、`prototype.css`、`prototype.js`、复用的 MMN 标志。只有 6 条虚构样例，没有真实客户、访谈、产品参数或审核员。

建议按以下顺序评审：

1. 选择第一条方法论，阅读正文与右侧证据，打开“查看样例原文”。
2. 切到“关联阅读”，打开支持材料，再“返回上一条”；比较明确关系与关键词相似推荐。
3. 打开“版本与审核”，展开 v1 → v2 差异；此处是演示，不修改版本。
4. 选择续航冲突、来源待补充、过期、原文无法访问四类记录。
5. 搜索“试驾”，清空筛选；底部可模拟加载失败、权限不足。切换样例空间 B 会清空旧详情。
6. 窄屏从目录进入详情，用“返回目录”恢复筛选及选中项；刷新会重置原型，不保存操作状态。

原有策略对话、知识导入和赋能去向以折叠保留区说明，不在本原型重做或调用。所有正式写入、导入、审核、发布操作均不开放。全局导航是静态外壳，只演示既有名称与层级，不进入真实页面，不切换产品版本。

若临时预览服务结束，可从本仓库目录运行：

```sh
python3 -m http.server 18791 --bind 127.0.0.1 --directory output/mmn-knowledge-workspace-s1
```

不要把服务根目录改为仓库根目录，不要绑定公网地址。本原型不是生产服务器。

## 2. 现状与目标交互

| 当前页面 | 原型目标 | 实装约束 |
| --- | --- | --- |
| 品牌/模块气泡，按条数浏览材料 | 分类筛选 + 可选择的知识目录 | 保留既有模块入口；不把启发式归类当成真实实体关系 |
| 材料标题、正文、来源标签、关键词 | 连贯正文、适用条件和使用限制 | 字段缺失就展示未提供，不由前端补事实 |
| 召回 N 条相关依据 | 资产总数、筛选命中、审核记录、实际引用分列 | 原型不执行召回或生成；列表匹配不是实际引用 |
| 片段阅读，没有完整核对面板 | 正文与可定位原文并排阅读 | 来源标签不等于原始文件或可核验摘录 |
| 品牌/关键词下钻 | 明确支持/冲突/反向引用与相似推荐分开 | 明确关系必须有可验证记录，不能从相似度推断 |
| 当前材料展示 | 版本差异、审核记录、事实有效时间 | 原型样例不能充当后台记录或正式审核凭据 |

设计取向：延续 MMN 黑灰导航、浅灰内容区、系统中文字体和现有圆角/颜色 Token；高信息密度、低动效。视觉技能用于层级、键盘可达性、响应式与截图复核，不引入营销落地页风格、第三方字体或另一套品牌。

开发者视觉复核后，补充了“原有流程保留区”、窄屏按钮不拆行、当前导航项在可滚动侧栏中保持可见。桌面以目录—正文—证据协同阅读，窄屏按目录—详情推进，证据置于正文下方。未引入关系图。

## 3. 当前字段能力矩阵（源码核对，不等于接口运行验收）

源码锚点：`index.html` 的 `#strategykb`；`app.js` 的 `loadStrategyKb`、`loadServerAssetLibrary`、`renderKnowledgeMap`、`renderRagResults`；`server.py` 的 `/api/asset-library` 和 `durable_asset_library`；`knowledge_registry.py` 的表合同。

| 界面信息 | 当前可核对来源 | 能力判断与 S2 降级方式 |
| --- | --- | --- |
| ID、标题、正文、类型 | `strategyAssets[].id/title/body/type`，目前从 `asset_json` 返回 | 有现有读取路径；先确认类型映射，未知类型保留未分类 |
| 品牌、模块、关键词 | `metadata`、`keywords/tags`；当前还有标题关键词启发式归类 | 不保证每条齐全；仅使用明确元数据作确定分类 |
| 来源标签 | `strategyAssets[].source` | 可以是导入标识，并非完整 provenance；不得作为“原文已核验”依据 |
| 更新时间 | 表有 `updated_at` 且用于排序；现有函数只解析返回 `asset_json` | 本次统计未见载荷顶层 `updated_at`；`createdAt` 是另一字段，不能冒充更新时间或事实时间 |
| 摘录、定位、来源有效期 | registry 有 sources/source_versions/segments/evidence，包含 quoted_text、locator_json、observed_at、valid_from/to | 数据合同存在不等于 RAG 页面可直接取得；需确认只读投影、身份、真实性与敏感字段过滤。未接通则来源待补充 |
| 知识版本与审核 | registry 有 revisions/reviews，包括 revision_no、status、reviewer、verdict、reviewed_at | 当前资产页面读取未完成这些字段映射；审核可信度相关 A-F01—04 尚不能由 UI 原型消除。缺失则审核记录未提供 |
| 支持、冲突、双向引用 | registry 有 edges；现有页面 knowledgeClusters 是聚类 | 表存在不保证 relation_type、方向、审核状态、权限语义满足前端合同；需逐项确认，不能伪造关联 |
| 检索与生成引用 | 当前 `ragSearch` 输出匹配；registry 有 retrieval_runs/items | retrieval_items 的引用候选不能自动算最终生成实际引用。需独立生成引用记录；无生成则未生成 |
| 租户/版本/项目上下文 | GET 读取 `current_auth().org_id`（另有 local fallback）与 edition；函数按 org/edition 取资产 | 只是源码发现；全局鉴权、local fallback、项目边界和全部投影隔离未做本轮实流验收 |
| 读接口副作用 | `durable_asset_library` 中为 SELECT；`db()` 使用普通读写连接并调用 DATA_DIR.mkdir | 不能仅凭 GET 名称承诺只读隔离。S2 需审计完整中间件、初始化链与缓存；本轮未调用正式 API |

旧客户端 `loadServerAssetLibrary` 会合并浏览器现有缓存并写 localStorage；`saveStrategyKb` 会 POST 并排队项目快照。隔离原型未导入这些函数。S2 不可直接复用它们来证明“无写入、无跨空间残留”。

### 数据量基线

本轮用 `sqlite3 -readonly` 对 `data/commercial_demo.db` 仅做聚合，不导出记录：

- 国内版 `strategy_knowledge_assets` 共 439 行，JSON 有效 439 行；最大载荷 3,592 字符。
- title/body/type 非空字段均存在于 439 行；metadata 349 行；source 标签 411 行；顶层 createdAt 437 行；顶层 updated_at 0 行。
- 以上是国内版数据库全量行数，跨数据库中已有空间，不是当前登录用户或截图模块可见数量；不是知识真实性、已审核数量或去重后的结论数。
- 未请求正式 RAG 页面或接口，故真实列表加载/筛选耗时仍未测量。原型 6 条的速度不用于设置生产性能阈值。S2 须在授权用户范围和真实字段投影上建立耗时基线。

## 4. 验证证据

检查脚本：`../playwright/mmn-kw-s1-checks.js`。使用 Playwright CLI 的 `run-code --filename` 执行，不安装或引入业务测试框架。

2026-09-08 最终运行：**34 项开发者浏览器断言通过**。包括三种宽度无横向溢出、搜索/组合筛选/清空、来源缺失与失效、原文模态框及 Escape 焦点回归、关系语义与返回、版本差异、键盘标签页切换、证据收起、过期/冲突、错误与权限模拟、空间切换清空、手机返回保持筛选、恶意文本转义与长文本、刷新无持久化。

网络采样只有 `127.0.0.1:18791` 下静态 HTML/CSS/JS/PNG 的 GET 请求；无 `/api/`，无生产网络请求，无变更请求。页面 JavaScript error 为 0；CLI console 为 0 errors / 0 warnings。`node --check prototype.js` 通过。

截图：

- `../playwright/mmn-kw-s1-desktop-1440.png`
- `../playwright/mmn-kw-s1-desktop-1280.png`
- `../playwright/mmn-kw-s1-mobile-list.png`
- `../playwright/mmn-kw-s1-mobile-detail.png`
- `../playwright/mmn-kw-s1-missing-source.png`
- `../playwright/mmn-kw-s1-conflict.png`
- `../playwright/mmn-kw-s1-versions.png`
- `../playwright/mmn-kw-s1-empty.png`
- `../playwright/mmn-kw-s1-denied.png`

桌面/窄屏截图已做视觉查看；未声称完成 Safari、真实移动设备、屏幕阅读器或全面安全评估。这里是开发者自检，不是独立工程师审查。模拟权限切换不证明真实多租户隔离；真实引用与原文真实性、B3 门槛、正式模块回归仍未验收。工单 UX-01—14 不因本原型通过而自动变成正式通过。

### 受保护文件核对

开工前与原型完成后的 SHA-256 一致（以下为完整值）：

```text
app.js                  dc0d54199af153f35fe31ae832ebb499c949daa5337abbcda5f88eecac27252a
index.html              c5a3b2712cacff3bd1c53335bc14c332b5e605d8674803edc4f4d5248f210785
style.css               f92d14de8b5e1210b118c30f33372a6ad295ae8e8fbd0d577c97089f3f8e1ff4
server.py               39022845beb51748cdce95834c5725e502e318b62b264a4647013973b770cf8c
data/commercial_demo.db e6a6fc474db15d790fe0084c25853f2d95e93eff0f96f3fbae9d514935fe2adf
```

保护的是本轮列明文件，不代表对仓库所有文件或外部服务进行了零漂移证明。仓库原本已有大量未提交改动，本轮未覆盖它们；未提交、推送、部署或改变生产开关。

## 5. S2 建议范围与估时

建议先做 S2-A：保留原查询/导入流程，只读接入现有材料的目录、搜索、正文和缺失状态。把证据、关系、版本面板作为真实合同就绪后逐项接入的 S2-B，而不是为了填满页面制造数据。

- S2-A 预算：约 **3–5 工程人日**，包含只读/权限与字段合同核对、页面接入、相关回归与实流验收。前提是无新增后端合同或身份问题，且已获 S2 实施授权；这是排期预算，不是本机 Codex 连续运行时长承诺。
- S2-B：只有在明确可用的只读投影、来源和审核可信门槛后才能可靠估时；不能把相关架构修复、证据补齐或真人审批等待算成已经满足的前提。
- S3：候选编辑、审批、发布、回滚另立写入工单；不在 V1 完成声明中。
- 部署、开启新检索路径、备案、公网 HTTPS、A-F01—04 修复均不包含在上述 S2-A 预算与授权内。

Ellis 待确认：目录—正文—证据的布局是否采用；窄屏逐层阅读是否采用；是否先允许“已有字段 + 缺失降级”的只读接入。确认原型与授权 S2 应明确区分。当前仍有 S2 只读实现、S3 写入审核两个后续阶段，S3 可不作为本轮 UI 升级的必做阶段。
