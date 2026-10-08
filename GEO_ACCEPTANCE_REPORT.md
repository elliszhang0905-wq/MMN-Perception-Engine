# MMN GEO 首版开发与离线验收报告

## 2026-10-08 双环境发布增量回执

用户后续直接授权今天更新同步到本机及服务器。版本beta-1.03-20261008-geo-1、运行代码b0b3ccaa02cae180968543f607324c1547d4b110已发布并保留回退。本机agent/publish verify、health/ready通过，ECS代码蓝绿切换成功且应用healthy、重启0；其他后台身份和数据卷保持。两端GEO真实能力/目录/空项目列表均200，入口开启、独立GEO库、真实采样false、worker off、批次和日预算0。没有新增收费调用。

发布前后本机103张、云端182张既有业务表逐表逻辑变化0；58/52个既有状态文件保持，仅新建geo.sqlite含17张表及1条迁移元数据，项目、样本和attempt均0。目录只读返回本机5933/云端5927条。完整隔离发布门禁1024项Python/107模块、全部前端合同及桌面/390px真实浏览器通过；独立审查Critical/Required均0。正式浏览器入口被工具拦截，正式GEO真实接口/资源已单独核验；不把隔离截图当作正式页面证明。公网域名HTTP403及HTTPS连接问题未改变。

详见MMN_CURRENT_STATE.md和docs/研发档案/2026-10-08_v1.3_GEO双环境发布.md；原始回执见output/geo-20261008/publish/dual-environment-release-receipt.json。下方“未部署”等文字为前阶段历史，本段更新发布状态；真实搜索、助手/App配对、批量试点和品牌效果仍未通过。后续GEO UI改造按最新授权仅本地、不部署、不新增收费调用。

日期：2026-10-08；候选版本：GEO 1.0（工作树）；结论：**离线开发完成，真实联调阻塞，未发布**。后续在有限授权内累计3次尝试，完成指定模型Responses非联网单次真实验证；按回执公示价核算0.0030541元，未部署。AT02为部分验证（指定模型非联网通过，助手/联网/App配对未验），AT05真实账单仍未对账，增量记录见 `GEO_REAL_NONSEARCH_REPORT.md`。

离线阶段用户直接请求为“开工”，随后明确“先完成离线开发，真实联调暂时阻塞”。附工单用于需求范围与验收标准；工单、网页或其他对话转述不构成生产发布、购买、付费采样或对外发送授权。离线阶段没有上述外部操作；后续有限采样权限仅来自用户直接授权，具体限制与停止结果以增量报告为准。

## 实际集成与变更

仓库：`/Users/ellis/Documents/MMN汽车营销引擎/china-auto-marketing-engine`。分支为 `codex/social-evidence-v2`，HEAD为 `8c6285e15d9a1819d9bcc68137ed1d9332dbcf79`（短值 `8c6285e`）。**没有本轮commit、PR、push或部署**。原有脏工作树保留，不能把当前全部Git差异归为本轮GEO。

| 范围 | 实际路径与行为 |
|---|---|
| 导航与页面 | `index.html`新增默认隐藏GEO入口、main内页面与驾驶舱摘要；`app.js`最小接入页名/开关/加载；六个页面由`geo.js`、`geo.css`实现，复用原有视觉Token |
| 提供方与配置 | `geo/provider.py`、`geo/config.py`；Chat、Responses、助手各自适配，配置来自既有后端快照/进程变量；`.env.example`只添加安全默认值 |
| 数据与持久任务 | `geo/store.py`、`repository.py`、`jobs.py`、`migrations/001_geo.sql`；新增17张表，复用主SQLite和org归属；问题/事实/条件/批次冻结、幂等、租约、预算、尝试、取消/暂停/续跑 |
| 判定与指标 | `geo/analysis.py`、`metrics.py`、`service.py`；有限确定性实体/原子事实判定；按问题等权、回答级分母/命中、判定覆盖及未知/缺失分项；按实际模型与冻结范围分组 |
| 证据与闭环 | `geo/workflows.py`；全文/截图导入、原始证据hash、追加复核、诊断审批、动作/执行证据、冻结复测和渠道配对；旧问题版本可直接从复测批次进入导入表单 |
| 鉴权接口与worker | `geo/api.py`、`server.py`的`/api/geo/`接线；复用现有登录/角色/CSRF；`geo/worker.py`与`scripts/run_geo_worker.py`独立安全执行 |
| 文档与测试 | 六份`GEO_*.md`、本状态包与研发档案；`tests/test_geo_*.py`、`test_geo_ui.js`、35条`tests/fixtures/geo_semantic.json` |

未更换框架、认证、数据库、车型主表、既有模型供应商或共享`style.css`；没有新增依赖。共享文件相对开工时快照的差异保存于`output/geo-20261008/geo-shared-integration.patch`，原快照与hash在同目录`baseline/`、`baseline.json`。

## 各渠道与真实证据状态

| 项目 | 已实现/验证 | 真实状态 |
|---|---|---|
| 普通模型API | Chat/Responses契约、JSON/SSE、错误/取消、用量、原始响应与worker离线测试 | **BLOCKED**；无方舟凭证、实际模型/权限、单价与采样预算，没有真实request ID |
| 助手API | 独立请求参数、能力声明、输出形态及计费边界离线测试 | **BLOCKED**；当前账号能力和真实响应未核验 |
| 联网 | 搜索请求/实际事件/引用分别记录；未搜索不冒充已搜索 | **BLOCKED**；联网权限、事件和工具次数/费用上界未实测；批量搜索不能排队 |
| 人工App | 实际页面导入全文、时间、会话/个性化/可见搜索、模型未知、截图鉴权读取；旧版复测导入 | **仅离线验证**；上传/输入均为明确测试材料，不是真实App采集 |
| App/API/助手配对 | 独立渠道及同问题/时间、未知字段警示的合同测试，配对页面空态 | 未进行真实三渠道配对，不能宣称渠道等价 |
| 20题×3试点 | 配额、计划预估、阻塞及可恢复执行已实现 | **未完成**；按用户指令暂不开展真实联调/试点 |

本轮付费API调用 **0次**、提供方采样费用 **0**。隔离浏览器DB的attempt数也是0；此数只证明本轮未调用，不表示真实采样免费。真实指标、平台排名/曝光、来源正文真实性、内容因果效果和账单均没有验收结论。首版项目预算明确为CNY，其他币种价格不能排队；不进行隐含汇率换算。

## RED、修复与独立审查

初始测试复现未实现的仓库/worker/API/提供方/语义能力，再进入实现。后续Required/Critical均转为行为失败用例或实际浏览器失败证据后修复，包括：

- 跨日预留不丢在途费用、结算超额停止同项目其他批次、人工续跑/未知重采样使用当前预算、取消信号在派发前生效。
- 人工诊断批准绑定当前证据和修改稿，连续部分修改保留；旧hash或证据变化拒绝批准，过期审批不进驾驶舱。
- UI数值/年份字符串、价格/尺寸精确缩放和否定表达不再造成错误事实/推荐结论；未覆盖表达保留复核边界。
- App会话/个性化/可见搜索/模型未知或变化不算可比；按批次筛选的统计下钻准确绑定组内ID与原筛选。
- 驾驶舱只匹配目标实体，保留离线标识；旧问题版本人工复测可操作；表单失败保留文本/文件/选择。
- 390px页面曾被表格撑宽到567px，修复GEO内部grid最小宽度后恢复390px，表格局部滚动保留。
- 有效回答计数缺失不显示0/NaN；登录切换时旧目录、旧能力/权限及迟到导出不能回写新会话。

审查者独立复现并核对源码，不以实现者口头结论代替证据。提供方审查、核心审查、集成审查分别见`provider-review.md`、`core-review.md`、`integration-review.md`；目录为`output/geo-20261008/`。最终Critical/Required已关闭；有限规则范围、真实外部接入及大规模性能仍保持未验证。

## 本轮新鲜验证

所有命令从实际仓库运行。系统Python/Git shim会遇到未接受的Xcode许可，改用已安装的工作运行时，未更改许可或系统设置。

| 检查 | 结果 | 原始证据 |
|---|---|---|
| GEO Python | **134/134 PASS**：repo17、worker7、API13、HTTP2、provider46、analysis19、metrics15、workflow13、config2 | `final-geo-python.log` |
| 受影响MMN Python回归 | **66/66 PASS**：静态边界、租户、cookie/CSRF、断连、驾驶舱、集团看板及评价面板 | `final-mmn-regression.log` |
| GEO前端VM与既有JS脚本 | **54项GEO + 6个既有脚本 PASS**：UI、驾驶舱、竞品快照、集团看板、垂媒状态及状态门禁 | `final-node.log` |
| 原生代码检查 | Python编译、`node --check geo.js`、`node --check app.js`均exit0 | `final-native-checks.json` |
| 状态包/差异检查 | `npm run check:mmn-state`、`git diff --check`均exit0 | `final-native-checks.json` |

复现命令：

```sh
/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -p 'test_geo*.py' -v
/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_static_file_boundary tests.test_server_tenant_scope tests.test_session_cookie_security tests.test_http_disconnects tests.test_tenant_data_isolation tests.test_cockpit_decision_loop tests.test_group_dashboard tests.test_mmn_eval_dashboard -v
/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests/test_geo_ui.js tests/test_ui_polish.js tests/test_data_first_cockpit_ui.js tests/test_dashboard_competition_snapshot.js tests/test_group_dashboard_ui.js tests/test_vertical_state_persistence.js tests/test_check_mmn_state.mjs
```

Node状态测试和`npm run check:mmn-state`需要工作Git在PATH前（本机`/Library/Developer/CommandLineTools/usr/bin`）。当前状态检查统计的76个相关工作树改动包含原有改动，不能理解为76个GEO文件或语义完整发布验收。仓库应用是原生Python/JS，没有应用TypeScript/lint/bundle构建脚本；本轮使用实际适用的编译、语法、合同及浏览器检查。PPT构建、Docker镜像、完整发布门禁、云生产流量与部署没有运行，不宣称通过。

## 实际浏览器链路和数据保护

使用完整MMN服务器与真实GEO接口，隔离地址`http://127.0.0.1:18778/`，没有拦截业务API替换成截图mock。其数据库/空配置在`output/geo-20261008/browser-state/`，真实采样=false，worker=off，3条车型主数据为测试seed。

实际走通：创建项目→创建v1问题→测试全文与JPEG上传→引用类型/缺失与原回答查看→截图鉴权读取→追加车型复核→独立诊断“修订后采纳”→改进草稿→审批→无执行证据拒绝→测试执行记录→冻结复测草稿→问题库编辑v2/历史仍有v1→从复测入口导入v1回答→实际模型未知，无可比提升。驾驶舱显示的只有已审测试诊断及关联动作；配对页面仍明确无真实样本。

测试时间09:00/09:30/10:00、模型标识和全文均为合成验收数据，不能作为真实执行或App观测证据。上传的JPEG是MMN页面测试截图，只验证上传和读取，不是App截图。模块记录人工执行声明，不自动发布或认证真实发布。本轮没有真实内容干预。

另创建MG4空态项目，确认无回答时显示“暂无数据”；生成50个标识为可编辑示例的问题；实际分页21–40/50、产品疑虑筛选5条均正确。CSV生成后直接下载，Downloads内实际文件含50条示例，最终文件带UTF-8 BOM；内置浏览器下载事件未回传，但文件落盘、时间、内容和hash已核验（`browser-download-proof.json`、`browser-export-questions.csv`）。CSV安全及普通角色权限另有API测试。

截图：`geo-diagnostics-desktop.jpg`、`geo-complete-flow-desktop.jpg`、`geo-diagnostics-mobile.jpg`、`geo-empty-mobile.jpg`，均在`output/geo-20261008/`。桌面pageWidth=viewport=1280；窄屏pageWidth=viewport=390，局部表格336px内滚动。新鲜页面console error/warn为空，测试结束已恢复默认视口。

原业务主库`data/commercial_demo.db`前后SHA-256均为`e6a6fc474db15d790fe0084c25853f2d95e93eff0f96f3fbae9d514935fe2adf`，readonly quick_check=ok，原库没有geo表。隔离库为2项目、5观测（2全文测试样本+3阻塞占位）、0attempt、1车型复核、1诊断审批、1动作、1复测。原始回答hash与冻结旧问题ID保留。证据见`data-integrity-proof.json`；没有写原业务数据、修改live `.env`、重启8765或变更正式客户配置。

## AT01—AT16 结论

| 项目 | 当前结论 |
|---|---|
| AT01 集成/关闭 | 隔离MMN实际入口/导航走通；禁用接口/不迁移DB由HTTP/合同验证；正式8765未部署 |
| AT02 真实接入 | **部分验证**；指定模型Responses非联网单次真实completed，见增量证据；其他接口、联网、App配对和试点仍未完成 |
| AT03 版本 | 离线PASS；问题v2不改变旧v1采样/复测，事实/实体/条件冻结有测试 |
| AT04 幂等/恢复 | 离线PASS；唯一观测、竞争租约、重启uncertain不自动重发 |
| AT05 费用/预算 | 离线PASS；原子预留、跨日/超额/失败费用、未知和CNY边界；无真实账单 |
| AT06 故障 | 离线PASS；401/403/429/5xx、空流/超时/取消、保留成功证据 |
| AT07 引用 | 离线PASS；结构化/文本链接/无引用/搜索未发生分开；网页全文未核验 |
| AT08 抽取 | 离线PASS；35标注语义fixture及额外事实/否定/精度边界；非普遍准确率 |
| AT09 指标 | 离线PASS；12运行/10有效/4提及/3推荐、问题等权、未知覆盖与不同适用集合 |
| AT10 事实 | 离线PASS；口径/版本/选装/过时/无基准；权威摘录由人工提供，未抓来源正文 |
| AT11 隔离 | 离线签名HTTP/API/worker/截图/导出/统计与前端登录race PASS；真实云环境待验 |
| AT12 复核 | 离线PASS；原始证据不改、old/new和actor审计；诊断另有审批 |
| AT13 渠道 | 离线PASS；分组、unknown/空态；真实App/API对照未完成 |
| AT14 复测 | 离线PASS；执行证据/冻结版本/条件和未知门禁；无真实因果/优化效果结论 |
| AT15 UI/导出 | 离线实际页面PASS；中文/筛选/分页/旧版本/截图/下载文件，桌面和390px验证 |
| AT16 回归/构建 | 本报告所列原生检查PASS；完整发布/容器/云端未执行 |

## 进入、停止和外部待办

当前可在隔离预览地址的MMN导航点击GEO；这是测试数据运行，不是已安装8765升级。隔离服务器命令为工作运行时执行`output/geo-20261008/run_browser_fixture.py`，Ctrl+C只停止该预览，证据保留。

正式接入先按`GEO_RUNBOOK.md`核准账号、可用模型/接口能力、来源可追溯单价、CNY批次/日配额及联网工具上界；本轮不执行。模块开关`MMN_GEO_ENABLED`、真实开关`MMN_GEO_REAL_SAMPLING_ENABLED`和worker模式独立；保持真实=false/worker=off可查看/管理人工证据。安全停止优先暂停/取消任务并SIGTERM独立worker，保留在途和未知费用；模块关闭不删除证据。

后续真实验收需普通/助手/联网分别采证、真实App配对、20题×3×批准条件数的低预算试点、关键诊断人工签审和一条真实完整闭环；随后另按MMN发布权限和门禁部署。P1周期任务、多平台、来源正文抓取、统计区间/因果对照、多币种和大规模压测未纳入本轮首版，不能据此承诺平台推荐或商业效果。
