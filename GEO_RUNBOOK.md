# GEO 运维手册

核对日期：2026-10-08。离线开发后有限授权的指定模型Responses非联网隔离验证已取得completed最终答案。累计3条attempt、2次实际模型请求，按官方公示价与usage核算0.0030541元，未对账最终账户账单；已耗尽3次授权，全部测试进程停止。正式8765、18778离线演示、产品代码、后端配置及全局网络未改变，详见 `GEO_REAL_NONSEARCH_REPORT.md`。以下常驻启动与正式启用均未执行。

### 本次解析恢复与输出验证

遇到本机网络工具将官方主机返回为198.18虚拟地址时，先用不带凭证的HTTPS DNS读取实时A记录，校验查询名、DNS状态、记录类型、公网属性、TTL、响应大小和无重定向，再验证以官方域名为server_hostname的TLS。只有这些检查通过，才允许在一次独立测试进程中对该固定官方主机替换解析；其他主机继续原解析，TTL到期即停止。不放行虚拟/私网IP，不关闭TLS或地址校验，不改全机DNS、代理、hosts或业务进程。恢复后的原提供方仍对公网地址固定连接，并核验官方域名证书。

指定模型默认启用深度思考，短输出上限可能全耗于思考。仅进行本次简单非联网连通测试时，在请求中明确固定service_tier=default及Responses reasoning.effort=minimal，保存实际payload与配置版本；不能用增大输出额度代替判断原因。无tools、store=false、无previous_response_id；seed/temperature未固定。此为隔离测试进程参数，尚未扩展产品配置接口。

每次模型请求前检查隔离DB路径、累计attempt数、冻结清单、版本化单价及最坏费用、max_attempts=1和独占启动记录。执行一次worker.tick后立即停止，原始回执逐字段回读并扫描凭证。第一次预发送拦截和第二次终止于length的费用通过独立证据核查，原记录不覆盖、不释放原保守预算占用；无回执或无法计价仍须停。**本次已累计3次，不可再试第4次。** 新的采样必须由用户另行明确安排。

## 配置与启用边界

| 环境变量 | 默认值 | 约束/用途 |
|---|---|---|
| `MMN_GEO_DB_PATH` | 空 | 后端GEO库路径；开启后必须显式配置独立geo.sqlite，缺路径/主库路径/同文件拒绝访问，车型目录只读主库 |
| `MMN_GEO_ENABLED` | `false` | 模块/API开启；开启本身不授权真实调用 |
| `MMN_GEO_REAL_SAMPLING_ENABLED` | `false` | 真实采样开关；保持off即可使用人工流程或blocked计划 |
| `MMN_GEO_WORKER_MODE` | `off` | `off/thread/external`；无效值归off并记录配置错误 |
| `ARK_API_KEY` | 空 | 服务端凭证，不能放前端、报告或日志 |
| `ARK_BASE_URL` | `https://ark.cn-beijing.volces.com/api/v3` | 适配器验证HTTPS固定官方主机，不能当任意代理URL使用 |
| `GEO_MODEL_ID` | 空 | 后台核准实际可用模型/接入点标识；本手册不猜型号 |
| `GEO_API_MODE` | `responses` | API条件须与后台配置匹配；普通接口chat/responses，assistant渠道有自身约束 |
| `GEO_MODEL_CONFIG_VERSION` | `unverified` | 能力/模型配置版本，改配置后创建新条件 |
| `GEO_SUPPORTS_TEMPERATURE` | `false` | 只有已核验支持才启用该请求参数 |
| `GEO_SUPPORTS_SEED` | `false` | 同上；不支持时不能宣称已固定seed |
| `GEO_MAX_QUESTIONS` | `50` | 1–50，后端配额上限 |
| `GEO_MAX_REPEATS` | `5` | 1–10，实验重复次数上限，区别于失败尝试 |
| `GEO_MAX_CONCURRENCY` | `1` | 1–4，worker线程数及执行时并发限制 |
| `GEO_MAX_OUTPUT_TOKENS` | `2048` | 1–8192，输出上界 |
| `GEO_MAX_ATTEMPTS` | `3` | 1–3，单观测调用尝试上限 |
| `MMN_GEO_BATCH_BUDGET` | `0` | 非负货币金额，创建/调整项目不能超过后台上限 |
| `MMN_GEO_DAY_BUDGET` | `0` | 非负货币金额，含已知开销和未释放占用 |
| `GEO_PRICE_CONFIG_JSON` | 空 | 版本化单价与输入成本上界；不完整则真实排队阻塞 |

布尔开关仅识别 `1/true/yes/on`（忽略大小写和外侧空白），其他值为false。数字错误进入configuration_errors并回落默认/0，不是批准忽略错误。GEO当前 `load_settings()`复用 `runtime_config.env_value` 的后端文件快照，并先检查显式进程环境变量：进程变量优先，包括显式空字符串。快照来源依次为显式初始化路径、`MMN_ENV_FILE`、仓库根目录 `.env`；相对路径按仓库根目录解析。文件内容在同一进程首次初始化后保持不变，修改文件需要在后续明确授权的环境中重启相应服务/worker才加载新快照，不能假定编辑后即时生效。本轮不修改live.env、不重启8765。凭证、模型、价格只保存在后端配置。

项目预算按后台上限初始化；改变后台上限不等于已调整所有项目预算。项目预算可用admin POST `/api/geo/projects/:id/budget` 调整。金额按定价币种解释，无自动汇率换算；同一项目跨CNY/USD时分别核账，不混合总额。

## 当前安全操作与后续真实启动

当前可做代码/测试文档核对与隔离测试；不修改业务库、不启用真实开关、不重启8765。后续操作者先核对授权范围、数据路径、凭证权限、实际模型能力、版本化定价和预算，再从登录的admin界面查看capabilities、创建新条件并预览一个明确清单。不得用测试文本、mock的model/request_id/usage或capabilities configured=true替代真实平台证据。

预览 POST `/api/geo/projects/:id/batches/preview` 返回planned_calls、估计/最大预留、币种、unknown_cost_items和blocked_reasons。创建同样清单需独立idempotency_key；关闭真实开关仍可保存blocked批次。人工App条件生成draft。blocked不能resume直接执行，修复后建立新的批次以保留原阻塞清单。

联网工具次数/费用上界当前尚未真实核验，`search_enabled`的批量API采样在policy中保持阻塞，即使配置了search_per_call也不会解除此门。单次真实核验是后续独立授权任务。本轮不执行、不声称已验证。

### 独立worker

`external`将GEOworker与既有Web进程分离；此模式Web不会自行启动worker。独立脚本必须同时满足模块on、真实采样on、worker_mode=external、无配置错误、凭证和model非空，才创建仓库和尝试领取。未满足时退出码2，脚本说明未创建数据库或调用。`--db`必填，必须与目标MMN数据库路径完全一致；脚本不会自动读取MMN_DB_PATH替代参数。

后续已批准的命令形式如下；GEO_PYTHON与GEO_APPROVED_DB_PATH由操作者填入与服务一致的已核准值（独立部署对应MMN_GEO_DB_PATH），不能把隔离测试库与业务库混用：

```sh
"$GEO_PYTHON" scripts/run_geo_worker.py --db "$GEO_APPROVED_DB_PATH" --once
"$GEO_PYTHON" scripts/run_geo_worker.py --db "$GEO_APPROVED_DB_PATH"
```

`--once`最多处理一个已经排队的观测；它不是只读测试命令，条件满足会调用真实提供方。常驻模式启动GEO_MAX_CONCURRENCY条线程。多实例共享SQLite持久领取/租约；需要核对数据库路径相同，不能仅凭进程存活认定业务可运行。

独立worker停止用其准确PID发送SIGTERM或SIGINT（前台Ctrl-C）；脚本设置stop事件、停止新派发，并等待线程退出，单线程join上限125秒。停止期间已发调用可能已有费用，也可能无法确认；不删除running/attempt、不归零预算。恢复worker后租约回收会将过期调用转uncertain，需人工核对。

`thread`模式由启用后的GEO请求启动Web进程内线程，按数据库路径缓存worker及初始settings。独立脚本不支持此模式。改外部环境/文件不能保证已存在worker重新加载；暂停/取消批次可阻止后续派发，进程级停用须由既有发布运维流程处理。当前没有GEO专用全局停止HTTP接口，本轮不会以重启8765代替停止流程。

### 暂停与取消

admin POST `/api/geo/batches/:id/control`：pause设置paused；resume只允许非终态且非blocked；cancel取消queued/draft并保留已发任务的证据及费用。worker在请求前和请求期间检测停止/派发权限，但无法撤销已经发生的外部计费。完成后检查batch/observations/attempts/audit，不用HTTP 200或worker输出一句完成作为账单确认。

## 定价维护和预算核账

首版项目/后端预算币种为CNY，界面明确标注。USD价格可保存为配置但不能排队真实任务，避免同一个数值预算被重新解释或跨币种分账绕过日限额；多币种换算未实现。

GEO_PRICE_CONFIG_JSON必须来自实际模型当前官方资料与操作者核验，字段为 `version,currency,model,priced_at,source_url,input_per_million,output_per_million,input_token_ceiling`；currency仅CNY/USD，model须与GEO_MODEL_ID一致。适用助手模式还需assistant_per_call；已知联网实测核账需要search_per_call和有效工具次数，批量联网门仍保持阻塞。本文不提供未核实官方价格或model。

服务代码仅验证来源/计价日期等字符串非空，不能替运营核验资料真实性、时效和可用模型权限。input_token_ceiling应能保守覆盖问题、提示和协议开销；输入上界太小会阻塞。token单价按每百万token、工具单价按每次计价；单次reserve取条件成本上界的最大值，批次总reserve还乘最大尝试数。

更新单价时保留旧记录的来源、日期和version；经批准更新进程配置，检查新预览后新建批次。旧manifest定价不可当作实时价自动替换；有价差时用旧冻结单价解释测算并和实际账单分开报告。不通过修改旧manifest把新价格回填成旧证据。

日预算按北京时间自然日/币种计。巡检将known cost、预留、未知held分开；cost=null、unknown_cost_items>0或billing_uncertain=true不能写成0。usage缺失、工具次数无效、费用超上界均需核对；`cost_envelope_exceeded`会暂停。跨日只迁移未在途预留，在途按attempt原budget_day结算。当前没有确认账单后自动释放held的公开接口，需后续授权的对账功能/操作方案，不直接SQL清零。

## 失败、重试与uncertain

| 情况 | 操作与约束 |
|---|---|
| 未发请求、配置或认证权限/额度失败 | 查error_class/blocked_reasons与审计；修复后台配置，不循环盲重试。配置hash变化需新建条件/批次 |
| 明确失败的rate_limit/provider_error且计费确定 | worker在尝试上限内自动重试；检查next_attempt_at及attempt_index，重复次数保持原实验位置 |
| 人工续跑failed | control `{command:'retry', observation_id可选, reason}`；需真实policy允许、剩余尝试与当前批次/日预算；原attempt保留，追加新attempt |
| 达到尝试上限 | retry拒绝；建立明确关联的新试验/复测，不增加原重复数掩盖尝试 |
| timeout、租约过期、已发请求但响应/账单未知 | 保持uncertain和billing_uncertain；先人工核对请求ID、证据、提供方用量/账单，不推断未计费 |
| 人工确认需要重采未知项 | control `{command:'resolve_uncertain',observation_id,reason}`；逐条处理，要求policy允许，新建关联批次返回其ID；旧观测和费用不覆盖 |
| cancelled | 原批次不续跑，保留历史；后续另建授权清单 |

未知项关联重采样保留问题/条件/实体/事实清单，repeat=1，manifest含linked_observation_id/resample_reason。幂等键由旧观测ID和原因生成；重复相同操作复用同批次，改变原因可能产生另一笔调用。它是新采样，不是确认旧调用免费，也不是同一实验增加一次隐藏重复。

## 人工App、事实与诊断审核

人工App采样使用POST `/api/geo/projects/:id/app-imports`，填写真实问题版本与问题全文、原答案、实际采样时间、会话/个性化/可见搜索状态、可见traceID和模型标识；不知则unknown/null。不补造时间或模型。只有截图可存证但不能做精确分析；截图PNG/JPEG≤2MiB，严格Base64上传，不提交URL或本地文件路径。新导入自动建立独立1×1×1人工批次；复测选择batch_id/repeat_index及必要condition_id，不能覆盖已填证据。

人工App的visible_search是可见设置，actual search仍未知；搜索状态unknown有独立条件hash，复测不可因此认定与off同条件。可配对同组织/项目、相同question_version_id、不同channel的API观测；配对显示差异、时间距离、未知个性化/会话，不能证明全量渠道等价。

事实维护通过POST `/api/geo/projects/:id/facts`，修订携带logical_id创建新版本。approved前核对年款/配置/市场、值/单位/测试口径、条件、有效日期、HTTPS来源和摘录。审核身份来自登录actor。原批次事实快照不随新事实自动替换。证据不足保留unverified；禁止以模型常识补真值。

观测复核POST `/api/geo/observations/:id/reviews`，kind为entity/fact、changes只允许对应字段，理由必填。确认实体true须原答案片段；recommended=true必须mentioned=true；rank为正整数且确实推荐。事实支持/矛盾/过时判断必须对应完整已审核基准和原答案证据。复核新增记录并保存old/new，不修改原答案/自动分析/raw_hash。查看有效analysis和automatic_analysis的区别，不把观测reviewed=true当所有条目已核验。

诊断由有效回答和有效analysis生成，admin能查看未审稿，普通角色只看当前accepted/modified。审核POST `/api/geo/projects/:id/diagnostics/reviews`提交diagnostic_id、当前source_hash、decision、reason，modified另有实际changes。证据或上一份复核稿变化后source_hash失效；遇stale_review刷新并重新核，不重用旧hash批准新稿。驾驶舱只展示已核诊断与关联动作，区分observation/hypothesis，不把假设当事实。

## 动作和复测

动作POST `/api/geo/projects/:id/actions`初始draft；记录diagnosis、证据观测、产品点、事实补充、内容结构、载体、负责人。POST `/api/geo/actions/:id`人工approved，approved_by由登录身份生成；人工执行后再提交executed、execution_evidence和带时区executed_at。模块不自动发布，只记录人工执行声明；建立任务不代表完成优化。已执行时间/证据不可覆盖，新的执行应建新动作。

复测POST `/api/geo/actions/:id/retest`需要baseline_batch_id和新的idempotency_key。动作须executed且有证据，基线有有效回答，采样不得晚于动作执行。新批次保留旧问题版本、实体/事实、条件、重复数，并使用当前预算限制；选择新condition_ids会记录不匹配。API按policy blocked/queued，人工保持draft再按冻结位置导入。

诊断页人工复测行可点“导入人工复测回答”，绑定批次冻结的问题全文/版本和条件；当前问题库编辑后的新版本不会替换它，重复序号从1开始。

GET项目retests动态展示两侧独立指标；只有问题/条件/实体/事实/实际模型与执行时间条件满足才给差值。unknown搜索/会话/个性化/模型/时间、逐问题条件下会话或个性化变化/混用、不在执行后的样本、未完成或条件变化没有提升结论。明确匹配的人工比较须记录同样的new_session、personalization和visible_search，不能把unknown当off或新会话。有效差值仍是observed_difference_not_causal，不能把观测变化宣传为动作因果效果。未完成任务的optimization_completed仍为false。

## 导出、保留与权限

普通角色只GET查看/导出，全部POST为admin；登录org与关联项目必须匹配。cookie写操作复用MMN同源CSRF校验，bearer复用现有认证。未要求登录的本地模式为local/admin，不应作为生产权限证明。不要在客户端配置org权限或把密钥写入GEO字段。

GET `/api/geo/projects/:id/export?kind=questions|observations|metrics|audit`返回CSV下载内容，记录export审计。导出观测含答案与有效分析的白名单，不带raw_response或截图BLOB；admin可在鉴权详情查看脱敏原响应，截图通过同时匹配组织/观测/截图ID的鉴权GET读取，同组织查看角色可访问。没有raw整包或截图压缩包导出接口。CSV虽做公式转义，下载文件仍可能含客户答案，交接按组织权限管理。

页面先生成认证范围内的CSV，再点击“下载 CSV”；输出带UTF-8 BOM。登录变化或更换项目清除此前下载内容，迟到响应不能归入新会话。

当前没有自动TTL、定期清理、删除API、专用备份恢复CLI或本模块数据库加密。保留期限与删除需单独明确授权和实现，不随worker停止或批次取消删证据。备份由既有数据库运维流程建立一致SQLite快照，保留组织、版本清单、原证据/哈希、截图和审计；恢复应先在隔离环境核验schema、外键、完整性与抽样关联，再经既有发布流程接入。此文档没有执行备份/恢复。

## 巡检与验收记录

每次受影响发布后或运行异常时，按组织/项目核对：

1. capabilities的模块/真实开关/worker_mode、缺配置、价格版本/币种及配额；不是仅看health。
2. 批次manifest、paused、status、总/完成数、error_summary和uncertain IDs；将blocked/待采样与有效结果分开。
3. worker准确PID/参数/数据库路径，running租约是否持续异常；不要把每次失败都重发为新费用。
4. attempts中request_id、actual_model、usage、搜索实际事件/引用类型、error_class、billing_uncertain；凭证脱敏且不上传客户全文到第三方telemetry。
5. 费用已知小计、未知条数、预留/held和币种/日期，核对cost_envelope_exceeded、provider_access_blocked、inflight_became_uncertain审计。
6. 原答案/hash、截图鉴权、版本关联、复核old/new、诊断source_hash是否过期；未知和待核条目保留可见标记。
7. 分组指标的固定问题清单、实体/事实快照、分母与失败数；offline_fixture或测试文本不得混作live验收。复测不匹配时显示两侧数据与原因，不展示虚构提升。
8. 实际受影响用户路径、普通/admin权限与跨组织拒绝、CSV导出、动作证据门、同条件复测；记录完成范围、修复与剩余风险。

这是一份人工巡检流程，未安装自动定时监控。本轮验收记录仅为隔离测试证据和文档核对；真实非联网/联网API调用、真实App截图/时间/模型、实际usage/账单、正式发布与业务库状态仍须后续授权验证。
