# GEO 数据字典

核对日期：2026-10-08。依据当前 `geo/migrations/001_geo.sql`、`geo/store.py`、`geo/repository.py`、`geo/jobs.py`、`geo/workflows.py`、`geo/service.py`、`geo/api.py`、`geo/config.py`、`geo/worker.py` 与 `scripts/run_geo_worker.py`。这是实现说明，不是部署或真实平台验收证明。

本轮真实联调暂时阻塞；未提交、部署或重启8765，费用为0。隔离18778浏览器演示中的回答是测试文本，不代表真实API/App回答、真实车型事实或优化效果。MMN与Sales Credo的数据、配置和运行环境相互独立。

## 存储与对象投影

GEO使用传入的SQLite数据库路径，表以 `geo_` 为前缀。实例初始化执行幂等迁移；连接启用外键，busy_timeout为15000毫秒，写事务使用 `BEGIN IMMEDIATE`。ID由 `geo_<类型>_<UUID十六进制>` 生成。服务端写入的时间通常是UTC ISO日期时间，预算日按 `Asia/Shanghai` 的自然日计算。

`decoded(row)`先解析 `payload_json`，再合并物理列；同名物理列覆盖JSON字段。随后所有 `*_json` 字段解析为对象并去掉后缀，唯一特例是 `raw_json → raw_response`。`payload_json`本身不在响应中。因此响应中的 `status/id/org_id/actor` 等物理列不能由payload同名值覆盖。JSON序列化排序键、保留中文、禁止NaN；`fingerprint`对该规范JSON计算SHA-256。截图SHA-256直接对二进制内容计算。

常用映射：

| 数据库字段 | 仓库/服务对象字段 | 含义 |
|---|---|---|
| `payload_json` | 展平的业务字段 | 各实体的可变属性或记录内容 |
| `manifest_json` | `manifest` | 批次冻结实验清单 |
| `analysis_json` | `analysis` | 首次自动分析，复核不回写此列 |
| `sample_metadata_json` | `sample_metadata` | App人工采样元数据 |
| `raw_json` | `raw_response` | 提供方原响应或人工导入全文/元数据 |
| `detail_json` | `detail` | 审计事件细节 |
| `cost_micro/reserved_micro/held_micro/spent_micro` | 原整数列；部分对象另有`cost` | 指定币种的百万分之一货币单位，展示时除以1000000 |

分页响应为 `{items,total,limit,offset}`；默认20，limit为1–100，offset为0–1000000。项目聚合/导出另有10000条上限；超限不能忽略后续样本当作全量。

## 表与字段

以下除 `geo_schema_meta` 外，业务表均有 `org_id`；项目内表均有 `project_id`。绝大多数记录有 `id/created_at`。这两个通用字段在表格中省略，不意味着数据库没有它们。

| 表 | 物理列（通用列之外） | payload或JSON内容及关联 |
|---|---|---|
| `geo_schema_meta` | `version`主键、`applied_at` | 当前迁移写入version=1；不是产品发布版本 |
| `geo_project` | `org_id,edition,payload_json,updated_at` | `name,target_key,entities,budget`；edition=`china/global` |
| `geo_question` | `org_id,project_id,active,latest_version` | 问题逻辑ID；active为0/1，版本文本在下一张表 |
| `geo_question_version` | `org_id,project_id,question_id,version,payload_json` | 问题文本与分类/适用性；唯一`(org,question_id,version)` |
| `geo_condition` | `org_id,project_id,condition_hash,payload_json` | 渠道、接口、模型、模式和请求参数；同项目同hash复用 |
| `geo_fact_baseline` | `org_id,project_id,logical_id,version,payload_json` | 产品事实的不可覆盖版本；唯一`(org,logical_id,version)` |
| `geo_batch` | `org_id,project_id,idempotency_key,request_hash,status,paused,manifest_json,budget_day,reserved_micro,held_micro,updated_at` | 冻结清单、定价和成本上界；唯一`(org,project,idempotency_key)` |
| `geo_daily_budget` | `org_id,project_id,day,currency,reserved_micro,spent_micro` | 主键`(org,project,day,currency)`；没有独立id/created_at |
| `geo_observation` | `org_id,project_id,batch_id,question_version_id,condition_id,repeat_index,status,answer,payload_json,raw_json,raw_hash,analysis_json,sample_metadata_json,channel,evidence_origin,lease_owner,lease_expires,next_attempt_at,sampled_at` | 一次固定问题×条件×重复位置；唯一`(org,batch,qversion,condition,repeat)` |
| `geo_attempt` | `org_id,project_id,observation_id,attempt_index,status,payload_json,request_id,raw_json,raw_hash,cost_micro,billing_uncertain,budget_day,reserved_micro,started_at,finished_at` | 一条观测的具体调用尝试，含失败/未知；唯一`(org,observation,attempt_index)` |
| `geo_review` | `org_id,project_id,observation_id,payload_json,actor,reason` | `kind,changes,old,new,entity_key或fact_index`；新增复核记录 |
| `geo_citation` | `org_id,project_id,observation_id,payload_json` | URL、规范URL、source_type、核验状态等；存在URL不证明来源支持结论 |
| `geo_diagnostic_review` | `org_id,project_id,diagnostic_id,source_hash,decision,payload_json,actor,reason` | `snapshot,changes,evidence_hash`；决策=`accepted/modified/rejected` |
| `geo_screenshot` | `org_id,project_id,observation_id,mime,content,sha256` | content为BLOB；只接受≤2MiB的PNG/JPEG严格Base64与魔术头 |
| `geo_action` | `org_id,project_id,payload_json,updated_at` | 动作草稿、批准和执行证据，见后文 |
| `geo_retest` | `org_id,project_id,action_id,baseline_batch_id,batch_id,payload_json` | 基线与新批次关联；JSON存执行时间、初始warnings与非因果声明 |
| `geo_audit` | `org_id,project_id,event,record_id,actor,detail_json` | 项目、版本、批次、尝试、复核、动作、复测、导出事件 |

外键将项目内记录连接至项目，观测连接至批次/问题版本/条件，尝试、引用、复核、截图连接至观测，复测连接至动作和两个批次。主键ID唯一仍不能代替租户条件。

### 实体、问题、条件与事实

`entities`是项目JSON数组，不是独立GEO实体表。每项含 `key,name,aliases,brand,year,trim,market,master_id`。实体key在项目内唯一，1–10项，每项最多20别名；target_key必须属于数组。catalog从已有 `vehicle_assets` 按组织和edition读取，品牌/车型组合生成稳定key并携带master_id；该映射不自动提供已审核年款/配置/市场事实。项目别名可编辑，旧批次实体快照保持原样。

问题版本字段：`text,category,intent,budget,scenario,segment,source,target_entities,competitors,unbranded,recommendation_eligible,ranking_eligible,fact_eligible,year,trim,market`。category为 `category/scenario/comparison/recognition/concern`。逻辑问题ID与版本ID不同：列表以 `id=question_id,version_id=问题版本ID` 返回；批次引用question_version_id，不能用逻辑ID代替。示例问题仅为可编辑示例，不代表真实需求或搜索量。

条件字段：`surface,api_mode,mode,model,temperature,seed,capabilities,provider_config_hash,model_config_version,system_prompt_version,system_prompt,max_output_tokens,timeout_seconds`。surface为 `ark_model_api/ark_assistant_api/doubao_app_manual`；api_mode为 `chat/responses/assistant/manual`且与渠道匹配。API mode为 `non_search/search_enabled`，人工App额外允许 `unknown`。人工搜索状态unknown/on/off分别冻结为unknown/search_enabled/non_search，哈希不同；可见设置不能当作实际搜索事件。model是配置标识，观测actual_model是响应实际标识；服务指标按actual_model或unknown分组，同时保留configured_model。参数支持未验证时不能宣称seed/temperature已固定。

事实版本含 `entity_key,year,trim,market,field,value,unit,cycle,conditions,effective_from,effective_to,source_url,source_excerpt,state,reviewer`。state为 `draft/approved/rejected`，reviewer在approved时来自服务端actor。新版本携带原logical_id，version递增。approved写入要求年款/配置/市场/有效日期/HTTPS公开来源/来源摘录；实际事实核验还要求单位、非空条件及适用条件可核对。仅把事实存成approved不足以保证每条回答可判真，模型知识不能替代基准。取最新版本不等于只取approved；未审核/不完整基准会保留为未核验。

### 冻结清单与观测

`manifest`冻结 `project_id,questions,conditions,repeats,entities,target_key,budget,facts,question_set_hash,entity_set_hash,frozen_at,manual`，并追加 `max_attempts,attempt_reserve_micro,currency,pricing,blocked_reasons,estimated_cost,max_reserved_cost`。清单一次最多50问题/8条件、1000观测；问题/重复数仍受项目配额限制。人工与API条件不能混在同批次。关联重采样/复测保留旧问题与实验快照，但新建批次使用当前项目预算/配额，不能复活旧高预算。

观测payload通常含 `usage,error_class,error,retry_after,search_requested,search_observed,actual_model,capabilities,started_at,finished_at,request_id`；人工导入含sample_time_unknown。sampled_at是证据采样时间，created_at只是系统入库时间。人工缺失采样时间保留null；有值须为带时区ISO日期时间。lease_expires/next_attempt_at是Unix秒用于租约/调度，不能拿来代替采样时间。

`evidence_origin`区分 `provider_api/manual_import/offline_fixture`。测试注入transport完成并标为offline_fixture的观测单独计数；人工测试文本仍是人工导入证据，需在验收说明明确测试性质，不能仅凭manual_import宣称来自真实App。

App元数据为 `new_session`布尔或unknown、`personalization/visible_search`=`on/off/unknown`、`platform_trace_id,paired_observation_id,question_verified,sampled_at,visible_search_is_actual_event=false`；actual_model仅在确实可见时显式记录。缺traceID为null，不伪造平台ID。必须有非空答案与可核对的问题全文才可能valid_answer=true，只有截图或问题不匹配不能进入精确指标。截图无OCR；不支持截图URL下载或本地文件路径。

原分析含 `version,valid_answer,refusal,entities,fact_checks`；实体结果含 `entity_key,mentioned,recommended,rank,evidence,start,end,needs_review,reason`，null为未知；事实含claim/field/value/unit/cycle/year/trim/entity_key/evidence/字符位置/verdict/baseline_id/reason。`apply_reviews`返回副本，将原分析保留为automatic_analysis并叠加有效analysis，只有被修改的条目标reviewed；观测reviewed=true不等于每个条目已复核。人工true须有原答案片段，rank须明确推荐且为正整数；事实supported/contradicted/outdated须有当前组织项目的完整已审核基准和证据。

详情另附冻结 `question,condition,facts,fixed_question_ids,question_set_hash,entity_set_hash,fact_baseline_hash,frozen_target_key,frozen_entity_keys`，以及citations/attempts/reviews/screenshots，均为派生关联投影而非观测物理列。

### 状态与预算

| 对象 | 状态/标志 | 实际意义 |
|---|---|---|
| 批次 | `draft` | 人工采样清单，尚待导入 |
| 批次 | `blocked` | 未满足真实调用配置/权限/成本/预算；不会因创建记录而调用 |
| 批次 | `queued/running` | 任务可派发/已有worker领取；paused独立控制新派发 |
| 批次 | `completed/completed_with_errors` | 全部观测终态，分别全完成/含异常或非答案；不等于优化成功 |
| 批次 | `cancelled` | 取消排队任务，已发请求证据和费用继续保留 |
| 观测 | `draft/queued/running` | 人工待导入/接口待领取/已领取 |
| 观测终态 | `completed/failed/refused/empty/uncertain/cancelled/unanalysable` | 有回答/失败/拒答/空/调用或计费未知/取消/无法分析 |
| 动作 | `draft/approved/executed` | 建议草稿/人工批准/人工声明已执行并提供证据和时间 |
| 诊断复核投影 | `unreviewed/accepted/modified/rejected/stale_review` | 证据变化后原复核失效，须刷新再核 |

批次status有SQL CHECK；观测/尝试status主要由应用控制，不能假定SQL限制了所有枚举。派发使用持久租约和尝试序号；过期running被恢复成uncertain。明确的rate_limit/provider_error且billing_uncertain=false、未达到尝试上限才自动排队重试。人工retry继续失败位置的剩余尝试；resolve_uncertain新建关联批次，不覆盖旧观测。

预算金额不包含汇率换算。配置价格支持CNY/USD，日账本按币种隔离，批次currency冻结；预算数字按该批次币种比较。跨币种不要汇总为一个无币种金额。`planned_calls=问题数×条件数×repeats`，排队前预留 `planned_calls×attempt_reserve_micro×max_attempts`。预览estimated_cost是一次尝试上界乘计划数，max_reserved_cost包含尝试上限，二者不是最终账单。API定价缺失/不完整时估计可为null；人工流程的系统调用估计为0，不证明人工平台服务免费。

每次尝试记录已知cost_micro与billing_uncertain；usage缺失或工具计数/单价不足，测算cost为null。未知余额held_micro保留，同时日reserved保留相应占用；终结批次释放未派发预留，不释放未知已调用费用。超出成本上界会暂停批次并记 `cost_envelope_exceeded`。跨日只迁移未在途预留，在途结算使用尝试原budget_day。

批次响应的cost可能是已知小计，也可能null；必须连同unknown_cost_items解释。指标cost含known_total/unknown_attempt_n/billing_uncertain_attempt_n；零次尝试的known_total=0不能证明已有真实样本免费。未知费用目前没有自动对账解除占用接口。

### 动作、复测与诊断

动作payload为 `title,diagnosis,observation_ids,entity_key,entity_keys,product_point,fact_to_add,content_structure,carrier,owner,status,execution_evidence,executed_at,approved_by,approved_at`。批准身份来自actor；初始draft，executed必须此前approved且有非空执行证据/有效时间。代码记录人工执行声明，不自动发布、不认证外部发布真实性；已执行时间/证据不可覆盖，其他编辑均审计。

复测关联已执行动作、有有效回答的基线和新批次。详情动态返回 `comparable,warnings,comparison,status,baseline_metrics,current_metrics,optimization_completed=false`。两侧独立指标一直保留；问题/条件/实体/事实基准/实际模型/执行前后时间满足比较要求才输出提及和推荐率差值。unknown模型、人工搜索/会话/个性化未知或变化、缺时点、条件变化、未完成都不能生成提升。人工元数据按每个问题版本与条件hash分组比较，同组混用不同状态或有效人工样本范围不一致也会警示不可比。差值为 `(复测rate−基线rate)×100`，字段为 `mention_percentage_point_difference/recommendation_percentage_point_difference`，声明=`observed_difference_not_causal`；不是因果效果。

诊断按有效观测生成，不单独落诊断主表。人工复核表保存诊断快照、source_hash/evidence_hash与变更；证据或复核稿变化，旧hash不能批准新稿。普通角色只查看accepted/modified的当前诊断；驾驶舱仅投影已复核诊断及关联动作，不显示原始未核假设为确认结论。

## 隔离、证据保护与权限

服务端org和actor来自既有认证上下文。GET/POST携带不同org_id/tenant_id会被拒绝；查询、关联检查和外键使用org条件，项目关联再验证project_id。SQL外键能约束同组织父记录，但不能独自证明每个关联都属同一项目，应用层项目校验仍必要。后台worker是有权调度多个组织任务的内部组件，查询全局候选时仍按每条任务的组织结算。

UPDATE触发器保护问题版本、条件、事实版本、观测复核和诊断复核。原观测raw_hash非null后，UPDATE answer/raw_json/raw_hash/analysis_json会失败；复核通过新记录叠加，不覆盖原答案。该保护不是数据库全字段防篡改或DELETE保护；状态/租约等仍可更新，API没有删除/任意SQL接口。保留管理须使用单独授权的方案，不能把hash当作外部可信签名。

GEO复用MMN认证，无独立登录。登录启用时需要有效组织认证；cookie写请求还要求 `X-MMN-CSRF: 1` 与同源Origin/Referer；bearer复用既有认证。既有本地未要求登录模式返回local/admin，这是本地运行边界，不是生产登录保障。所有GEO POST要求admin，普通角色可GET查看/导出；capabilities在模块关闭时仍可读。普通观测响应移除观测和尝试raw_response；admin可看脱敏原响应。配置中的密钥不出现在capabilities响应；provider技术详情仅admin。

截图GET `/api/geo/observations/:observation_id/screenshots/:screenshot_id`需要现有认证并同时匹配org、观测ID、截图ID；同组织普通查看角色也可读取。列表仅含id/mime/sha256，无公开URL或文件路径。数据库本身未在本模块实施加密，需由部署与保留策略管理访问。

导出仅支持 `questions/observations/metrics/audit` CSV，观测导出包含答案/有效分析/引用等白名单，不含raw_response或截图BLOB；GET导出会追加export审计。CSV对公式前缀和控制字符做转义，复杂对象按JSON保存。没有单独raw证据导出或截图打包接口。
