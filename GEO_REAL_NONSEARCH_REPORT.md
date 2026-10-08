# GEO Responses 非联网单次测试记录

## 后续恢复结果（2026-10-08）

**当前结果：指定模型Responses非联网隔离验证通过；累计3次尝试已达上限，测试进程全部停止。** 用户后续直接要求“快点找出解决方案并且解决”，恢复仍遵守现有密钥、指定模型、总上限1元、最多3次、隔离库、不显示密钥、不改业务库及不部署的限制。

根因是本机Shadowrocket的虚拟地址解析与适配器公网IP校验不兼容；不是模型不存在或密钥无效。通过固定HTTPS DNS端点实时解析官方主机，验证返回地址为公网、记录匹配查询主机及TTL，再仅在独立测试Python进程中覆盖该官方主机的解析结果。原适配器公网校验、IP固定连接、官方域名TLS证书校验全部保留；没有放行198.18地址、关闭TLS校验、更换模型、写全局DNS/代理/hosts或修改产品代码。公共解析只查询官方公开主机名，不携带模型密钥；拒绝重定向及超大响应。

| 尝试 | 结果 | 输入/输出token | 按官方公示单价核算（元） |
|---|---|---|---|
| 1 | TCP连接前地址校验拦截；复现证实未发送模型请求 | 无平台用量 | 0（预发送核查结论，原始uncertain保留） |
| 2 | 平台返回实际指定模型与终止回执；默认思考用完1024token额度，未产出最终文本 | 75 / 1024（含1024思考token） | 0.0028248 |
| 3 | reasoning.effort=minimal关闭思考；平台与本地均completed，取得最终答案 | 74 / 63（思考token=0） | 0.0002293 |
| 合计 | 3条attempt、2次实际模型请求、1条有效最终回答 | — | **0.0030541** |

[官方模型价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh)常规文本输入0.80/输出2.70元每百万token；[官方深度思考文档](https://docs.volcengine.com/docs/ark/deep-thinking?lang=zh)和[模型参数支持](https://docs.volcengine.com/docs/ark/model-parameter-support?lang=zh)支持Responses minimal。费用为回执usage乘以官方公示价，不是已核对的最终账户账单；没有假设免费额度、折扣或缓存抵扣。第二次平台回执明确incomplete/length、default档位、缓存关闭、无搜索、usage合计1099；属于文本截断，完整终止用量可以核算费用，原始保守标记未改为成功。原始前两条记录及预算占用均保留，通过追加审计解释核查结论。

最终实际型号：`doubao-seed-2-1-lite-260915`；request_id：`021791468544195efca7158d8a072a352f4e6ec3154e35a58b714`；search_requested=false、search_observed=false；最终回答为：

> 选购家用汽车最应优先考虑的三个因素是：核心安全配置（如安全气囊数量、车身刚性、主动刹车系统）、长期使用成本（含燃油/电耗、保养费用、保值率）以及空间舒适性（涵盖乘坐空间、储物空间、座椅舒适度与驾乘视野）。

该回答仅用于连通性验证，不是车型策略报告或品牌效果结论。原始回执SHA-256、固定问题/条件、最终统计有效样本数1、attempt累计3、无queued/running、原先两条记录未改变均已回读核验。第二和第三次真实请求各在独立进程中只执行一次worker.tick，无后台重试。授权次数已耗尽，**不得再发第四次请求**。

本次重新执行134项GEO Python回归全部通过。隔离库quick_check=ok；所有业务库仅读quick_check，均ok且没有新增GEO表。源主库、达人蒸馏库及两份配置哈希仍与上一轮一致；运行中的受管主库相对上一轮物理哈希有变化，mtime为2026-10-08 22:03:48（Asia/Shanghai），变化来源尚未核验，本记录不将其列为“哈希不变”。本任务所有数据库写入都指定在授权隔离库，没有回滚、覆盖或清理业务数据。正式8765与离线18778监听PID仍为1129、57029，没有重启或部署。

新增证据：`network-resolution-proof.json`、`first-attempt-prewrite-proof.json`、`second-attempt-cost-proof.json`、`recovery-request-payload.json`、`recovery-result.json`、`final-request-payload.json`、`final-result.json`、`final-metrics.json`、`recovery-data-protection.json`、`recovery-verification.json`与`recovery-regression.log`。密钥扫描命中0；原有首次记录和文件保留。状态包v2.49记录本次成功的精确边界，check:mmn-state与diff空白检查通过；助手/联网/App配对和正式环境启用仍待独立验收。

## 首轮停止时的历史记录

日期：2026-10-08；状态：**首轮尝试受阻，已按费用未知即停止的要求停止；真实接入未通过。**

用户直接授权现有密钥、`doubao-seed-2-1-lite-260915`、Responses非联网测试，总上限1元，先1次、累计最多3次；费用不能确定即停。仅使用隔离测试库，不显示密钥，不改业务库、不部署。附工单与网页资料仅提供需求或接口事实，不扩大权限。

| 项目 | 本次记录 |
|---|---|
| 模型请求配置 | `doubao-seed-2-1-lite-260915`；平台实际模型尚未取得 |
| 接口及模式 | 官方 `/api/v3/responses`；non_search，无tools，无历史响应ID |
| 输出及重试约束 | max_output_tokens=512（回答与思考合计）；max_attempts=1；仅worker.tick一次后停止 |
| 服务档位 | 测试进程显式service_tier=default；未改生产适配器或持久配置 |
| 时间（UTC） | 2026-10-08T13:27:57.945291+00:00 至 2026-10-08T13:27:57.957895+00:00 |
| 调度尝试 | 1条attempt，适配器派发入口1次；没有第二次调用 |
| HTTP/平台证据 | 连接在发送HTTP字节前的域名地址校验处被拦截；无平台request_id、actual_model、回答、原始响应或usage |
| 阻塞原因 | `Official destination resolved to an unsafe address`；后续只读DNS核验非公网地址1个，公网地址0个 |
| 保存状态 | observation=uncertain；批次completed_with_errors，不表示测试成功 |
| 费用状态 | 费用unknown，billing_uncertain=true；已记账spent=0不能替代平台账单；保留0.004660元预算占用 |
| 后续次数 | 其余2次额度未使用；当前停止，不自动重试 |

官方2026-10-08价格表的常规文本输入为0.80元/百万token，输出为2.70元/百万token，适用于本模型家族输入0–1024千token。[官方模型价格](https://docs.volcengine.com/docs/ark/model-pricing?lang=zh)。本次按4096输入token及512输出token预留：`(4096×0.80 + 512×2.70)/1000000 = 0.0046592元`，向上取微元为0.004660元。这是请求前费用上界及预算预留，**不是平台确认的实际收费**。未使用免费额度、折扣或缓存命中抵扣假设。

[官方Responses参数文档](https://docs.volcengine.com/docs/ark/create-model-responses-api?lang=zh)用于核验输出总上限与常规档位。原生产适配器没有设置service_tier，本次仅在测试进程覆写请求构造，显式固定default；测试payload已留存并在派发前逐字段比对。未发送联网工具配置、未创建显式缓存，密钥仅从现有服务端配置读取到内存，未写入测试证据。

本次库：`/Users/ellis/Documents/MMN汽车营销引擎/china-auto-marketing-engine/output/geo-20261008/real-nonsearch/authorized-nonsearch.sqlite`。组织、项目、问题版本、条件、预算、尝试和审计均仅存于该库；没有将测试结果写入业务库或18778的演示库。费用未知记录和预留未改为0、未清除。

本次重新执行134项GEO Python测试，全部通过；该结果证明离线合同回归，通过数不构成真实接口成功证据。三个业务库（源主库、受管运行时主库、达人蒸馏库）SHA-256前后一致且只读quick_check=ok，GEO表数量未增加；两份现有配置前后哈希一致。隔离库quick_check=ok，1条尝试、没有自动重试。测试证据和增量报告凭证扫描命中0；状态包v2.48记录了有限授权、阻塞和停止，`npm run check:mmn-state`通过，`git diff --check`通过。8765与18778监听PID分别仍为1129与57029。

正式8765服务、18778离线演示、生产开关、业务数据、服务器部署保持各自原状态；本次没有发布、服务重启、提交或推送。真实模型权限、Responses返回、usage计费、助手/联网/App配对及完整业务闭环仍未完成；不产生品牌可见度或优化效果结论。

证据位于 `output/geo-20261008/real-nonsearch/`：`official-pricing-evidence.json`、`official-api-limits.json`、`preflight.json`、`request-payload.json`、`single-run-started.json`、`dispatch-count.json`、`result.json`、`dns-diagnostic.json`、`integrity-after.json`、`preflight-regression.log`。其中dispatch-count是适配器派发入口计数，不能解释为平台已经收到的请求次数。
