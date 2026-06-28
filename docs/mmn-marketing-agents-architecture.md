# MMN Marketing Agents Architecture

版本：v0.1
日期：2026-06-28
状态：方案设计，可进入 P0 实施

## 1. 设计目标

MMN Marketing Agents 的目标不是把系统改成一个通用 agent 市场，而是把现有 MMN 多模态营销引擎中已经具备的能力组织成可追踪、可质检、可复盘、可扩展的汽车营销工作流。

核心收益：

- 效率：把 RAG 检索、NSR/Emotion/Attribute/Gap 诊断、竞品监控、创始人蒸馏、周报生成串成自动流程。
- 准确率：每条关键结论绑定证据、来源、时间、平台和置信度。
- 稳定性：引入任务账本、结构化 I/O、QA 闸门、重试与降级策略。
- 可扩展性：后续新增平台、车型、报告类型或模型时，只扩展 agent 合约，不重写业务流程。

## 2. 来源项目可复用部分

基于 Michael Sitarzewski 的 Agency Agents 项目，可复用的是设计模式，不照搬角色和实现。

保留：

- 角色契约：每个 agent 明确职责、输入、输出、边界、成功指标。
- Orchestrator 模式：主控只负责拆解、调度、状态管理和合成，不替代专业 agent。
- Handoff 模板：跨 agent 交接时保留上下文、约束、验收标准和证据要求。
- Generator/Evaluator 闭环：策略生成后必须经过 QA Review。
- 任务级质量闸门：失败反馈可追踪，最多重试 2-3 次，仍失败则降级或人工审核。
- 可观测性：每次 agent 调用带 trace_id、状态、输入摘要、输出摘要、耗时、模型与错误信息。

剔除：

- 与汽车营销无关的通用软件开发、游戏、金融、法律、医疗角色。
- 复杂 mesh agent 协商机制，除非后续有明确的高价值辩论式策略场景。
- 只有人格设定但缺少数据契约和验收标准的角色。
- 会增加流程长度但无法提高营销交付质量的中间 agent。

## 3. 现有 MMN 能力映射

| 现有能力 | 当前承载 | Agent 化后的角色 |
| --- | --- | --- |
| RAG 策略知识库 | `strategyKb`、RAG 导入、`ragSearch` | Evidence Retrieval Agent |
| NSR / IPS / Emotion / Gap / Action | `analysis()`、`score()`、`actionFor()` | Signal Analyst Agent |
| 车型身份与属性判断 | `model_identity_assets`、`model_judgment_assets` | Vehicle Attribute Agent |
| 垂媒/竞品监控 | `vehicle_assets`、`vertical_rank_assets`、`vertical_ai_learnings` | Competitor Monitor Agent |
| 创始人蒸馏 | `founder_speech_archives`、Founder Distill UI | Founder Voice Agent |
| 达人/内容资产 | creator/video/blogger skill 状态与导入 | Creator Content Agent |
| 周报/导出 | `reportPayload()`、PPT/Gamma 导出 | Weekly Report Agent |
| 多模型执行与质检 | Qwen / DeepSeek / local fallback | Strategy Generator + QA Review Council |

## 4. 总体拓扑

默认使用层级式 Orchestrator，而不是 mesh。

```text
MMN Marketing Orchestrator
  |
  +-- Intake Agent
  |     识别任务类型、车型、竞品、平台、时间窗、约束和交付格式
  |
  +-- Evidence Retrieval Agent
  |     召回 RAG、垂媒、竞品、创始人语料、项目学习案例
  |
  +-- Signal Analyst Agent
  |     计算 NSR、Emotion、Attribute、Gap、Action 优先级
  |
  +-- Competitor Monitor Agent
  |     提炼竞品正负榜、对比重点、攻防机会
  |
  +-- Founder Voice Agent
  |     将创始人表达转成品牌口径、话术边界和内容风格
  |
  +-- Creator Content Agent
  |     根据平台和内容资产生成脚本、达人组合、素材方向
  |
  +-- Strategy Generator Agent
  |     合成可执行营销策略、内容计划和指标目标
  |
  +-- Weekly Report Agent
  |     输出周报、简报、PPT/Gamma 结构化素材
  |
  +-- QA Review Council
        +-- Evidence QA
        +-- Logic QA
        +-- Brand/Compliance QA
        +-- Regression QA
```

## 5. 统一任务输入

所有 agent 接收同一个任务对象的子集。Orchestrator 根据权限和职责裁剪字段，避免无关上下文污染。

```json
{
  "trace_id": "uuid",
  "task_id": "uuid",
  "task_type": "strategy | weekly_report | competitor_monitor | founder_distill | content_plan",
  "edition": "china | global",
  "brand": "品牌",
  "model": "车型",
  "competitors": ["竞品A", "竞品B"],
  "platforms": ["懂车帝", "抖音", "小红书", "微博", "B站", "知乎"],
  "time_window": {
    "start": "YYYY-MM-DD",
    "end": "YYYY-MM-DD"
  },
  "constraints": [
    "优先公开来源",
    "高热度/高声量必须说明依据",
    "输出必须绑定车型和平台",
    "不得使用绝对化营销表述"
  ],
  "inputs": {
    "rows": [],
    "strategy_kb": [],
    "vertical_assets": [],
    "model_judgments": [],
    "founder_archives": [],
    "creator_assets": [],
    "learning_cases": [],
    "project_snapshot": {}
  }
}
```

## 6. 统一 agent 输出

```json
{
  "trace_id": "uuid",
  "task_id": "uuid",
  "agent": "EvidenceRetrievalAgent",
  "status": "pass | fail | degraded | needs_review",
  "confidence": 0.82,
  "summary": "一句话结论",
  "findings": [],
  "evidence": [
    {
      "source_type": "rag | public_url | vertical_asset | founder_archive | learning_case",
      "source": "url-or-file-or-record-id",
      "platform": "平台",
      "date": "YYYY-MM-DD",
      "claim": "该证据支持的结论",
      "confidence": 0.8
    }
  ],
  "risks": [],
  "recommendations": [],
  "next_inputs": {},
  "qa_required": true
}
```

## 7. 核心 agent 定义

### 7.1 MMN Marketing Orchestrator

职责：

- 解析任务，决定需要调用哪些 agent。
- 维护 agent run 状态、任务账本、重试次数和最终合成。
- 判断是否进入人工审核。
- 控制上下文预算，只传递必要字段。

输入：

- 用户任务、当前项目配置、工作区快照、时间窗、车型和竞品。

输出：

- `agent_run` 总结、最终策略/周报、QA 结果、降级说明。

边界：

- 不直接生成事实性结论。
- 不绕过 QA 输出高置信度结论。

优先级：P0。

影响：新增服务层，不需要重写现有 RAG、诊断和报告模块。

### 7.2 Intake Agent

职责：

- 将用户意图标准化为 task_type。
- 抽取品牌、车型、竞品、平台、时间窗、交付格式和约束。
- 缺失关键字段时给默认值或标记待确认。

预期收益：

- 降低周报、策略问答、竞品监控之间的入口混乱。

优先级：P0。

影响：可先作为 Orchestrator 内部函数实现。

### 7.3 Evidence Retrieval Agent

职责：

- 从 `strategyKb`、垂媒资产、车型判断、创始人语料、项目学习案例中召回证据。
- 生成 EvidenceBundle。
- 给每条证据标注来源、平台、日期、关联车型和可用范围。

预期收益：

- 提升 RAG 结果可解释性。
- 减少策略生成的无依据判断。

优先级：P0。

影响：复用现有 `ragSearch` 和 RAG 数据结构，增加证据标准化层。

### 7.4 Signal Analyst Agent

职责：

- 复用现有 NSR、IPS、Emotion、Attribute、Gap、Action 计算逻辑。
- 输出诊断列表：机会、风险、资产、行动优先级。
- 对低样本、无竞品、数据缺口进行显式标记。

预期收益：

- 把现有仪表盘指标转成 agent 可消费的结构化诊断。

优先级：P0。

影响：主要封装现有 `analysis()` 输出，不改算法本身。

### 7.5 Competitor Monitor Agent

职责：

- 基于 `vertical_rank_assets`、`vehicle_assets` 和垂媒学习结果，识别竞品正负声量、排名变化、对比重点。
- 输出攻防建议：抢占、避险、借势、澄清。

预期收益：

- 让竞品监控从“列表展示”变成“主动策略输入”。

优先级：P1。

影响：复用已有垂媒导入和资产表。

### 7.6 Vehicle Attribute Agent

职责：

- 归一车型名称、品牌、能源类型、车型家族、关键属性。
- 将 Attribute 结果提供给 RAG 召回和策略生成。

预期收益：

- 降低车型别名、竞品错配、跨平台命名不一致带来的误判。

优先级：P1。

影响：复用 `model_identity_assets` 和 `model_judgment_assets`。

### 7.7 Founder Voice Agent

职责：

- 从创始人语料中提炼品牌叙事、语言风格、技术表达、风险边界。
- 为策略和内容生成提供“品牌本人会怎么说”的口径约束。

预期收益：

- 提升输出内容的品牌一致性。
- 避免通用营销话术稀释品牌差异。

优先级：P1。

影响：复用 `founder_speech_archives`，增加口径注入规则。

### 7.8 Creator Content Agent

职责：

- 基于平台、达人库、垂类学习和策略目标生成内容脚本、达人组合、素材结构。
- 平台原生化输出，不做跨平台复制。

预期收益：

- 提升从策略到内容执行的转化效率。

优先级：P2。

影响：复用现有 creator/video/blogger skill 模块。

### 7.9 Strategy Generator Agent

职责：

- 合成证据、诊断、竞品、创始人口径和内容资产。
- 输出 Action、内容主题、平台打法、KPI、风险提醒。

预期收益：

- 将 MMN 从“诊断工具”推进为“行动建议引擎”。

优先级：P0。

影响：复用现有智能策略按钮和本地兜底策略。

### 7.10 Weekly Report Agent

职责：

- 将本周市场信号、高热度事件、高声量事件、车型/品牌策略、Action 计划组织成周报。
- 每个热度/声量判断必须带平台、日期、来源和依据。

预期收益：

- 周报自动化稳定落地，减少人工整理。

优先级：P1。

影响：复用 `reportPayload()`、PPT/Gamma 导出。

## 8. QA Review Council

### 8.1 Evidence QA

检查：

- 每条关键结论是否有证据。
- 高热度/高声量是否说明平台、日期、量级或公开可检索依据。
- RAG 证据是否与车型、竞品、时间窗匹配。

失败处理：

- 缺来源：退回 Evidence Retrieval Agent。
- 证据弱：降级为“公开信息不足，基于现有样本推断”。

优先级：P0。

### 8.2 Logic QA

检查：

- NSR、Gap、Emotion、Action 是否自洽。
- 是否存在“负面风险高却建议加大曝光”这类逻辑冲突。
- 是否遗漏用户指定车型或竞品。

失败处理：

- 退回 Signal Analyst 或 Strategy Generator。

优先级：P1。

### 8.3 Brand/Compliance QA

检查：

- 是否使用绝对化、夸大、不可证实表述。
- 是否违背创始人口径或品牌风格。
- 是否将平台规则误用到其他平台。

失败处理：

- 退回 Strategy Generator 或 Creator Content Agent。

优先级：P1。

### 8.4 Regression QA

检查：

- 固定样例集的输出结构、关键字段、事实约束是否稳定。
- 新 agent 或模型调整是否导致策略质量下降。

优先级：P2。

## 9. 工作流

### 9.1 智能策略工作流

```text
用户问题
  -> Intake Agent
  -> Evidence Retrieval Agent
  -> Signal Analyst Agent
  -> Competitor Monitor Agent
  -> Founder Voice Agent
  -> Strategy Generator Agent
  -> Evidence QA
  -> Logic QA
  -> Brand/Compliance QA
  -> 输出策略
```

降级路径：

- RAG 无结果：使用本地规则 + 明确提示“缺少项目知识证据”。
- 竞品数据不足：输出“竞品样本不足”，不强行比较。
- 创始人语料不足：不注入创始人口吻，只使用品牌通用口径。
- QA 失败超过 3 次：输出带风险标记的草案，并进入人工审核。

### 9.2 周报工作流

```text
周报任务
  -> Intake Agent
  -> Evidence Retrieval Agent
  -> Competitor Monitor Agent
  -> Signal Analyst Agent
  -> Weekly Report Agent
  -> Evidence QA
  -> Logic QA
  -> 输出 Markdown / PPT / Gamma 素材
```

硬性要求：

- 高热度、高声量事件必须有日期、平台、来源和判断依据。
- 公开信息不足时，必须写成“依据不足”而不是断言。
- 品牌策略必须覆盖任务指定的所有车型。

### 9.3 创始人蒸馏工作流

```text
创始人语料
  -> Evidence Retrieval Agent
  -> Founder Voice Agent
  -> Brand/Compliance QA
  -> 写入 RAG / 口径库
```

硬性要求：

- 只蒸馏可定位来源或本地可信归档。
- 不把创始人的个人表达直接改写成品牌承诺。
- 输出必须包含适用场景和禁用场景。

## 10. 数据表建议

### 10.1 `agent_runs`

```sql
create table if not exists agent_runs (
    id text primary key,
    org_id text,
    user_id text,
    edition text not null default 'china',
    task_type text not null,
    brand text,
    model text,
    competitors_json text not null default '[]',
    platforms_json text not null default '[]',
    time_window_json text not null default '{}',
    status text not null,
    final_output_json text not null default '{}',
    qa_summary_json text not null default '{}',
    created_at text not null,
    updated_at text not null
);
```

### 10.2 `agent_steps`

```sql
create table if not exists agent_steps (
    id text primary key,
    run_id text not null,
    agent_name text not null,
    step_order integer not null,
    status text not null,
    input_summary text,
    output_json text not null default '{}',
    confidence real,
    error text,
    started_at text not null,
    completed_at text
);
```

### 10.3 `agent_reviews`

```sql
create table if not exists agent_reviews (
    id text primary key,
    run_id text not null,
    step_id text,
    reviewer_name text not null,
    verdict text not null,
    severity text,
    findings_json text not null default '[]',
    evidence_json text not null default '[]',
    retry_instruction text,
    created_at text not null
);
```

### 10.4 `evidence_bundles`

```sql
create table if not exists evidence_bundles (
    id text primary key,
    run_id text not null,
    source_type text not null,
    source_ref text not null,
    platform text,
    brand text,
    model text,
    competitor text,
    published_at text,
    claim text not null,
    confidence real,
    payload_json text not null default '{}',
    created_at text not null
);
```

## 11. API 建议

### `POST /api/agents/run`

用途：启动一次 agent 工作流。

请求：

```json
{
  "task_type": "strategy",
  "edition": "china",
  "brand": "品牌",
  "model": "车型",
  "competitors": ["竞品A"],
  "platforms": ["懂车帝", "抖音"],
  "question": "如何提升该车型的新能源智能化认知？",
  "mode": "fast | deep"
}
```

响应：

```json
{
  "ok": true,
  "run_id": "uuid",
  "status": "completed",
  "result": {},
  "qa": {},
  "evidence": []
}
```

### `GET /api/agents/run?id=...`

用途：查看任务步骤、证据、QA 和最终输出。

### `POST /api/agents/review`

用途：人工审核、通过、退回或补充证据。

## 12. 实施优先级

### P0：可追踪与可信策略

改动：

- 新增 agent 任务账本表。
- 新增统一任务输入输出 schema。
- 新增 EvidenceBundle 标准化。
- 将现有 RAG + `analysis()` + 策略生成包装为最小 Orchestrator。
- 增加 Evidence QA。

收益：

- 每次策略生成都有来源、步骤、置信度和 QA 记录。
- 最小改动即可提升准确率和稳定性。

影响：

- 后端新增表和 API。
- 前端可先只展示“引用依据”和“QA 状态”，无需大改 UI。

### P1：竞品、创始人口径、周报编排

改动：

- Competitor Monitor Agent 接入垂媒资产。
- Founder Voice Agent 接入创始人语料。
- Weekly Report Agent 接入报告导出。
- 增加 Logic QA 和 Brand/Compliance QA。

收益：

- 周报和策略从“可生成”变为“可信交付”。
- 竞品和创始人口径进入统一策略链路。

影响：

- 需要定义报告模板和周报验收标准。
- 部分 UI 增加 QA/证据状态。

### P2：规模化与评测

改动：

- Creator Content Agent 输出内容脚本与达人组合。
- Regression QA 样例集。
- 异步任务队列、重试、模型成本统计。

收益：

- 提升长期稳定性。
- 支撑更多平台、车型和客户项目。

影响：

- 需要沉淀 20-50 个高质量汽车营销评测样例。
- 后续可接入调度系统。

## 13. 对现有系统的影响控制

不重写：

- 不重写 RAG 检索。
- 不重写 NSR/Emotion/Gap/Action 算法。
- 不重写创始人蒸馏和垂媒资产导入。
- 不重写现有导出流程。

先封装：

- 现有函数作为 agent 的工具能力。
- 现有数据库作为 agent 的证据和记忆来源。
- 现有前端页面先增加状态展示，不拆页面。

后演进：

- 当 agent run 稳定后，再逐步把按钮式操作升级为工作流入口。

## 14. 最小可行版本

MVP 范围：

- `POST /api/agents/run`
- `agent_runs`、`agent_steps`、`agent_reviews`、`evidence_bundles`
- Intake Agent
- Evidence Retrieval Agent
- Signal Analyst Agent
- Strategy Generator Agent
- Evidence QA
- 本地规则降级输出

MVP 不包含：

- 异步队列。
- 完整 mesh 协商。
- 自动发布。
- 大规模平台爬取。
- 非汽车营销角色。

MVP 成功标准：

- 每次策略输出能看到引用依据。
- 关键结论至少有一条证据或明确“依据不足”。
- 低置信度结果不会伪装成确定结论。
- 现有 RAG 和分析页面功能不受影响。

## 15. 后续实施建议

第一步：在 `server.py` 中新增 agent 数据表和最小 API。

第二步：把现有 RAG 召回和 `analysis()` 输出转换成结构化 `EvidenceBundle` 与 `SignalDiagnosis`。

第三步：在现有智能策略按钮旁增加“Agent 可信策略”入口，展示步骤、证据和 QA 结果。

第四步：将周报导出迁移到同一套 agent run 账本，确保每份周报可追溯。

第五步：沉淀回归样例集，开始做策略质量评测。
