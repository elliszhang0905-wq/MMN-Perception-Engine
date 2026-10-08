# GEO 指标与证据口径

定义版本：`geo-metrics-1`；确定性抽取版本：`geo-rules-1`。实现为 `geo/metrics.py`、`geo/analysis.py`、`geo/service.py`；界面和CSV均消费同一后端结果。当前仅完成离线验证，真实平台指标尚无验收证据。

## 固定范围和未知值

每条观测绑定冻结的问题版本清单、实体集合、事实基准、条件及重复序号。分组使用渠道、接口surface、联网模式、实际模型、condition_hash、question_set_hash、entity_set_hash、fact_baseline_hash；当前项目的实体编辑不会改写历史范围。请求配置模型与实际返回模型分别记录；实际模型缺失显示unknown。

默认提及/推荐率按问题等权：先在每个问题的可判定回答中计算比率，再平均所有有可判定回答的问题。重复数不一致不会增加某题权重。另列回答级比率、命中、分母和参与平均的问题数。失败或全未知问题不当作0分：列入缺失/零可判定问题，并显示完整适用问题数和判定覆盖率。

示例：题A三次都提及、题B一次不提及，等权提及率为50%，回答级为75%。12次请求中10条有效且可判定、4条提及、3条推荐，另2次失败，回答级为40%/30%，运行总数仍是12。只有一个问题时等权值与回答级相同。

完整、非空、非拒答且属于可分析答案才进入有效回答集合。失败、空答案、拒答、仅工具事件、未完成流、解析失败、截图无全文分别计数。完整答案但自动分析失败不记“未提及/未推荐”，进入该字段的未判定候选。提及已确定而推荐待复核时，提及仍有效；不同字段各自保留未知。

`judgment_coverage.mention/recommendation`包括judged_n、candidate_n、unresolved_n、rate。覆盖率=已判定候选/候选；有候选但全部未知时覆盖率0，候选0时null。`judgment_unresolved_causes`区分analysis_missing、indeterminate和重叠的needs_review。`eligible_question_n`、`equal_weight_judged_question_n`、`zero_judgment_question_ids`必须与正向比率一并阅读。完全缺失且没有适用标记的问题ID进入`eligibility_unknown_question_ids`，不会猜测推荐适用性。

## 指标定义

| 指标 | 每题分子 / 分母 | 边界 |
|---|---|---|
| 提及率 | 目标mentioned=true / 目标提及可判定有效回答 | 有品牌提示与无品牌问题分别统计；短别名歧义为null |
| 推荐率 | 目标recommended=true / recommendation_eligible题中的推荐可判定有效回答 | 比较列名、负面描述、复述问题不算推荐；中性否为有效分母 |
| 第一推荐率 | 目标明确推荐且rank=1 / ranking_eligible题中可判定有效回答 | 普通先后顺序不产生排名；无明确排序计未第一，并列no_explicit_ranking_n |
| 推荐份额 | 目标推荐次数 / 同固定实体集合所有推荐次数 | 一条回答可推荐多车；存在未判定实体时该回答不进入份额分母，列share_unresolved_n；不是市场份额 |
| 事实错误率 | contradicted+outdated / supported+contradicted+outdated原子断言 | unverified、conflicting_sources、subjective、not_applicable另列；空分母null；默认先每题再等权 |
| 域名引用率 | 实际出现指定域名引用的回答 / 有效回答 | structured与text_link分开；同答案域名去重；等权及回答级分别保留 |

实体结果包含原回答Unicode字符位置（从0开始，end不含末位），片段必须等于`answer[start:end]`。未出现实体的否定结果没有凭空的正向片段。明确优先词或推荐编号列表才形成rank；自动输出为有限规则匹配，非普遍语义准确率。现有标注fixture覆盖35个语义样本，另有事实、否定、版本与类型边界测试。无法覆盖的语言表达进入人工复核，不能用模型常识替代来源。

## 事实基准与引用

原子字段范围包括动力形式、纯电/综合续航、尺寸、价格、有限配置项、补能电压/方法及主观体验。CLTC/WLTC、年款、配置、市场、日期、单位、选装和适用条件严格区分。数值型表单字符串按字段转换；年份仅做年份规范化，枚举与布尔值不互转。否定断言保留否定词、polarity和完整位置，不能拿肯定基准直接证明支持。

只有审核通过且范围一致、有效期内、具有来源URL/摘录/审核人的基准可用于核验。无基准或范围缺失为unverified，适用性不一致为not_applicable，过时基准为outdated，多来源有效值冲突为conflicting_sources。未核验数量、核验覆盖率和复核状态另列，不能由无证据推导准确率。

search_requested、search_observed与citation_available独立记录。请求工具不等于工具已执行；人工App的可见联网设置不是实际工具事件。结构化引用来自响应，文本URL只标text_link；本版不抓取网页正文，verification=not_fetched。引用出现不证明来源支持断言，未返回引用不自动补造。引用能力覆盖率使用冻结capabilities，与引用命中率分开。

## 成本、复核与复测

费用归属于attempt，失败与重试产生的已知成本也计入。未知费用和billing_uncertain单列并保留预算占用。无调用的离线人工流程为0次提供方尝试；known_total=0不表示真实采样免费。价格、币种、模型、时间与来源版本化保存在清单；排队需输入token和工具成本的可执行上界。当前联网批量采样在未验证工具次数与费用上限前保持blocked。

首版项目与后端额度明确以CNY计价。其他币种价格可显示但排队被阻塞，不能把同一个预算数静默改解释成美元或换算金额；多币种预算尚未实现。

人工修订新增old/new、操作者、时间、原因，原答案、原始响应hash与自动分析不变。指标使用当前有效结果，并显示reviewed与needs_review。诊断另有accepted/modified/rejected审批及证据快照hash；车型结果复核不能代替诊断审批，旧审批在证据变化后退出驾驶舱。离线fixture和人工导入保持来源标识。

复测必须绑定已执行动作的时间和证据、同问题版本与冻结范围。实际模型、条件、有效样本时间或人工App会话/个性化/可见联网字段未知、变化或混用时，不生成可比提升；仍可查看前后独立指标。可比差值为`(后比率-前比率)*100`个百分点，标为observed_difference_not_causal。仅创建动作不是优化完成；本轮没有真实App/API配对或真实内容干预实验。

## 下钻与规模

每组提供observation_ids、evidence_filters和evidence_scope_hash。下钻在相同组织/项目与原batch/channel筛选下重算并核对token，再对该组准确ID分页；token过期返回409并要求刷新。不能扩大为同渠道/条件下其他模型或版本的回答。后端聚合上限10000条，超过时要求按批次缩小范围；列表每页1–100条。首版未验证大规模运行性能或统计区间。
