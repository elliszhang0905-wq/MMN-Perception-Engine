# MMN Eval v0.1

## 定位

MMN Eval 评测的不是底层模型“聪不聪明”，而是一次输出是否达到 **MMN模型输出策略** 的交付标准。它优先保护事实、证据和产品边界，再评价策略质量。

v0.1 的评分器保持离线、确定性运行；同时已在现有 MMN 中加入可视化页面和薄 API，用于读取报告、运行种子评测和保存人工判断。它不修改现有数据库和模型调度，不需要模型 Key，适合本地开发、案例标注和后续 CI 门禁。

## 当前能力

- 严格校验评测案例与候选输出 JSONL。
- 执行不可被总分抵消的硬门禁。
- 对五个 MMN 质量维度计算 100 分制得分。
- 缺失评分维度保持 `null`，不会伪装成 0。
- 输出通过、人工复核、失败三种判断。
- 对比 baseline 与 candidate，识别新硬失败、状态降级和显著分数下降。
- 生成 JSON 报告和 Markdown 人工复核清单。
- 在「系统设置 → Eval评测」展示发布判断、五维得分、案例明细和人工复核进度。
- 通过真实 API 运行种子评测、导出报告，并按组织保存人工判断。

## 可视化页面

本地启动 MMN 后，在左侧导航打开「系统设置 → Eval评测」。页面数据只来自当前 Eval 报告，不构造演示基线；只有存在真实 baseline/candidate 对比时才显示版本变化，否则明确显示“尚无可对比基线”。

页面提供：

- 当前发布判断、综合分、通过/复核/失败数量。
- 五维质量表现和案例状态筛选。
- 失败项详情与人工复核弹窗。
- “运行 Eval”入口和 JSON 报告导出。

当前种子集是机制验证夹具，页面会持续显示边界提示：它只证明评测机制可工作，不代表 MMN 真实业务能力成绩。

浏览器验收截图：

- `output/playwright/mmn-eval-dashboard.png`
- `output/playwright/mmn-eval-human-review.png`

## HTTP API 与复核记录

- `GET /api/eval/report`：读取当前报告、案例上下文和当前组织的人工复核进度。
- `POST /api/eval/run`：重新运行内置种子评测并返回最新报告。
- `POST /api/eval/human-review`：保存待复核案例的人工结论；驳回必须填写理由。

人工结论默认写入 `data/eval/mmn_eval_human_reviews.json`，按 `orgId` 隔离。只有报告中 verdict 为 `human_review` 的案例可以保存人工结论；它不会覆盖或绕过硬门禁失败。

## Rubric v0.1

| 维度 | 权重 | 判断重点 |
| --- | ---: | --- |
| 证据真实性与可追溯性 | 30 | 证据 ID、来源、版本、时间、适用边界 |
| 洞察与证据一致性 | 25 | 推理链、替代解释、是否把相关性写成因果 |
| 策略可执行性 | 20 | 选择、取舍、动作、指标、窗口、停止条件 |
| 品牌车型与场景适配 | 15 | 人群、预算、车型版本、竞品、购车阶段和场景 |
| 不确定性与边界表达 | 10 | 事实、推断、假设、未知及补证计划 |

暂定阈值：

- `80–100`：通过。
- `65–79.99`：进入人工复核。
- `<65`：失败。
- 任一硬门禁失败：无论总分多高，直接失败。
- 任一评分维度缺失：保持已知维度的归一化得分，但必须进入人工复核。

## 硬门禁

1. 编造事实或事实声明没有证据。
2. 引用不存在的证据 ID。
3. 把缺失或未知写成 0。
4. MMN 规定的多模型复核未完成或没有共同证据。
5. 车型配置未完成 Qwen、DeepSeek、Kimi 三模型复核与共同证据确认。
6. 仅凭平台曝光、互动、情绪或热度推导购买需求、转化或成交。
7. 可执行机会缺少规定数量的独立来源；转载或同源二次引用不算独立。
8. 策略没有区分事实、推断、假设和未知。

## 文件格式

### 案例 JSONL

每行一个对象：

```json
{
  "id": "strategy-001",
  "taskType": "strategy",
  "input": {
    "question": "需要做出的汽车营销决策",
    "evidence": [
      {"id": "official-1", "sourceGroup": "official", "sourceType": "product"},
      {"id": "owner-1", "sourceGroup": "owner-study", "sourceType": "experience"}
    ]
  },
  "expected": {
    "requiredProviders": ["qwen", "deepseek"],
    "requiredStatementTypes": ["fact", "inference", "hypothesis", "unknown"],
    "minimumIndependentSources": 2
  },
  "tags": ["strategy", "happy_path"]
}
```

`taskType` 当前允许：`strategy`、`opportunity_map`、`social_evidence`、`content_strategy`、`brief`、`vehicle_configuration`。

### 候选输出 JSONL

```json
{
  "caseId": "strategy-001",
  "claims": [
    {"statementType": "fact", "text": "事实文本", "evidenceIds": ["official-1"]},
    {"statementType": "unknown", "text": "当前未知项", "evidenceIds": []}
  ],
  "dimensions": {
    "evidence": 0.9,
    "reasoning": 0.8,
    "actionability": 0.8,
    "fit": 0.8,
    "uncertainty": 0.9
  },
  "modelValidation": {
    "completedProviders": ["qwen", "deepseek"],
    "commonEvidenceIds": ["official-1"]
  },
  "flags": {},
  "metadata": {"promptVersion": "strategy-v1", "gradingSource": "independent_judge"}
}
```

维度分使用 `0–1`；没有可靠评分时写 `null`，不得填 0。维度分必须来自人工标注或独立 Judge，禁止把候选模型的自评分直接作为 Eval 分数。只要存在维度分，`metadata.gradingSource` 就必须是 `human`、`independent_judge` 或 `synthetic_fixture`。`flags` 是确定性检查或人工标注结果，目前支持 `fabricatedFact`、`missingAsZero`、`platformSignalOverreach`。

## 运行方式

单版本：

```bash
python3 scripts/run_mmn_eval.py \
  --cases data/eval/mmn_eval_seed_v0.1.jsonl \
  --outputs data/eval/mmn_eval_seed_outputs_v0.1.jsonl \
  --out output/mmn-eval-report.json \
  --markdown output/mmn-eval-report.md
```

版本对比：

```bash
python3 scripts/run_mmn_eval.py \
  --cases path/to/cases.jsonl \
  --baseline path/to/baseline.jsonl \
  --outputs path/to/candidate.jsonl \
  --out output/mmn-eval-comparison.json \
  --markdown output/mmn-eval-comparison.md
```

退出码：

- `0`：通过，或仅存在待人工复核项。
- `1`：存在失败、缺失案例或版本回归。

种子输出文件故意包含错误样本，因此整套种子运行应返回退出码 `1`；它用于证明门禁能够拦截错误，不代表程序故障。

## 人工标注流程

MMN 负责人是最终裁决人。工程侧先完成去标识化、预标注和冲突归类，只在以下时点请求人工：

1. 两种合理 Rubric 解释会改变案例通过或失败状态。
2. 确定性检查和匿名双评之后仍存在争议。
3. 首批真实案例已经跑完，需要冻结 Rubric 版本和阈值。

每个真实案例建议记录：

- `humanVerdict`：`pass`、`human_review` 或 `fail`。
- 五个维度分及一句理由。
- 硬门禁及对应证据。
- 人工最终文本或修改摘要。
- `rubricVersion`、标注时间和案例版本。

首批真实金标准建议 20–50 条，覆盖核心模块和已知失败；稳定后扩展到 120–150 条。争议案例不要删除，应单独保留为边界集。

## 当前边界与下一步

v0.1 尚未完成：

- 全部模型调用的统一 Trace 接入。
- Langfuse 数据集同步和在线 Judge。
- 从历史运行中脱敏抽取 120–150 条真实案例。
- 将 Eval 接入正式发布门禁。

当前可视化页面已完成机制闭环，但真实历史 Gold Set 的扩充仍是后续数据任务；首批 20–50 条案例需要 MMN 负责人逐条裁决。

在人工冻结阈值前，v0.1 报告用于内部校准，不作为生产发布的唯一依据。
