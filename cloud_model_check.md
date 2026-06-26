# MMN Perception Engine 云端核心模型能力检查

## 检查日期

2026-06-27

## 检查对象

- 云端地址：http://121.40.60.90:8765/
- ECS 项目目录：`/opt/mmn-perception-engine`
- 容器服务：`mmn-web`、`mmn-app`、`mmn-db`、`mmn-scheduler`
- 运行数据库：`/app/data/commercial_demo.db`

## 总体结论

当前云端版本**不是只有网页外壳**。云端已经包含 MMN Perception Engine 的核心策略代码、Qwen/DeepSeek 配置、业务数据库、RAG 训练资料、车型资产、垂媒正反向排名资产、历史项目快照和演示数据，并且已经通过实测完成：

1. RAG 训练包解析。
2. MMN 策略分析生成。
3. Qwen 实际调用。
4. DeepSeek 实际调用。
5. Qwen 与 DeepSeek 双模型融合路径返回成功。
6. 车型身份识别写入数据库。
7. 车型判断写入数据库。
8. 前端首页可访问。

但云端仍存在三项风险：

1. ECS 当前目录还不是 Git 仓库，尚未完全切换为“服务器从 GitHub 拉取代码”的标准发布形态。
2. 当前 RAG 以本地资料包、结构化知识记录和接口召回为主，尚未发现独立向量数据库或 embedding 索引文件。
3. `Positioning` 已在本地最新代码中补入策略模型层，云端需要通过标准发布流程同步后生效。

## 逐项检查

| 检查项 | 状态 | 证据 | 风险与处理 |
| --- | --- | --- | --- |
| 最新 MMN 代码 | 存在风险 | 云端 `server.py`、`app.js`、`docker-compose.yml` 已部署；服务健康。 | ECS 目录当前不是 Git 仓库，不能证明已通过 GitHub 标准发布链路更新。需要重新按 Git clone / pull 方式整理服务器目录。 |
| 前端页面 | 已完成 | `GET /` 返回 HTML，包含 MMN 页面和 `app.js` 入口。 | 需继续做每次发布后的浏览器自动验证。 |
| 后端健康接口 | 已完成 | `/api/health` 返回 `ok=true`，数据库指向 `/app/data/commercial_demo.db`。 | 无重大风险。 |
| NSR | 已完成 | 前端与报告逻辑中已有 NSR 计算与展示，项目快照中含 NSR 相关数据。 | 当前主要基于导入样本计算。 |
| Emotion | 已完成 | 声量数据中包含情绪字段，策略工作流包含用户情绪。 | 需要后续继续细分情绪标签解释与证据链。 |
| Attribute | 已完成 | 声量数据包含产品属性/认知标签，RAG与策略接口可引用。 | 需要继续补充各车型属性词典。 |
| Identity | 已完成 | `model_identity_assets` 已有数据，云端测试新增识别记录成功。 | 品牌/车型归属仍需要持续质检和别名库沉淀。 |
| Positioning | 已完成 | 本地最新代码已将 `Positioning` 显式补入 `MMN_STRATEGY_MODEL.modules`，文档已同步。 | 需要发布到云端后复测。 |
| Gap | 已完成 | 前端认知表、策略工作流与 RAG 策略提示均包含 Gap/认知空位。 | 需要继续区分“认知Gap”和“销量/转化Gap”。 |
| Action | 已完成 | 策略输出要求包含平台、人群、动作、验证指标；行动模块存在。 | 需要继续沉淀为行业动作库。 |
| MMN 策略工作流 | 已完成 | `MMN_STRATEGY_MODEL.workflow` 已包含“本品 → 竞品 → 用户情绪 → 产品属性 → 身份认同 → 认知空位 → 传播动作”。 | `modules` 列表需补入 Positioning。 |
| Qwen API Key 配置 | 已完成 | `/api/ai/status` 显示 Qwen configured=true，实测策略生成使用 `qwen`。 | 不输出 Key 明文；需关注模型名有效性和调用额度。 |
| DeepSeek API Key 配置 | 已完成 | `/api/ai/status` 显示 DeepSeek configured=true，深度策略接口实测使用 `deepseek` 返回内容。 | DeepSeek 响应较慢，演示时建议保留快速策略路径。 |
| OpenAI 配置 | 未完成 | `/api/ai/status` 显示 OpenAI configured=false。 | 当前国内版已按要求隐藏/弱化 OpenAI，不影响国内演示。 |
| 数据库连接 | 已完成 | SQLite `/app/data/commercial_demo.db` 存在，大小约 10MB；`DATABASE_URL` 已配置给 PostgreSQL 预留。 | 当前核心业务仍在 SQLite，PostgreSQL 尚未承载核心业务表。 |
| RAG 知识库数据 | 已完成 | `/app/data/rag_training/v1` 与懂车帝销量 RAG 文件存在；`/api/import-rag-seed` 可解析 83 条训练资料。 | 当前是资料包/结构化知识库形态。 |
| 向量库数据 | 未完成 | 未发现独立向量数据库、embedding 文件或向量检索服务。 | 后续需要接入 embedding、向量索引和相似度召回。 |
| 历史案例数据 | 已完成 | `project_snapshots=56`，`founder_speech_archives` 有记录，`vertical_ai_learnings=2`。 | `learning_cases=0`，人工学习案例还需要继续沉淀。 |
| 演示数据 | 已完成 | `vehicle_assets=557`，`vertical_rank_assets=3760`，`workspace_contexts=4`。 | 数据已上云，但后续要做租户隔离和正式数据版本管理。 |
| 双模型融合稳定性 | 已完成 | 一键脚本复测 `fusion_qwen_deepseek` 通过，Qwen 与 DeepSeek 均返回内容。 | 曾出现过一次 Qwen 分支读取超时，后续仍建议优化并发执行、分支超时隔离和部分结果可用。 |
| 结果写入数据库 | 已完成 | 云端测试后 `model_judgment_assets` 成功写入记录，`model_identity_assets` 记录增加。 | 测试写入会产生测试记录，正式阶段需增加测试数据标识与清理机制。 |
| 前端展示 | 已完成 | 首页可访问，核心 JS 入口存在。 | 需要用浏览器自动化进一步验证真实渲染状态。 |
| 定时任务服务 | 已完成 | `mmn-scheduler` 容器运行健康。 | 周度抓取目前以合规公开源和保底样例为主，数据源仍需继续配置。 |

## 云端数据库现状

检查时云端核心表记录数如下：

| 表 | 记录数 |
| --- | ---: |
| `workspace_contexts` | 4 |
| `project_snapshots` | 56 |
| `vehicle_assets` | 557 |
| `vertical_rank_assets` | 3760 |
| `vertical_ai_learnings` | 2 |
| `model_identity_assets` | 64 |
| `model_judgment_assets` | 1 |
| `founder_speech_archives` | 8 |
| `learning_cases` | 0 |

## 实测结果摘要

已执行以下云端实测：

1. `/api/health`：通过。
2. `/api/ai/status`：Qwen 与 DeepSeek 均已配置。
3. `/api/import-rag-seed`：通过，返回 83 条 RAG 资料。
4. `/api/ai/rag-strategy`：通过，实际使用 Qwen，返回约 1400 字策略内容。
5. `/api/ai/rag-strategy` 深度模式：通过，实际使用 DeepSeek。
6. `/api/ai/fusion-strategy`：通过，Qwen 与 DeepSeek 均返回内容。
7. `/api/ai/model-identities`：通过，车型身份识别返回 4 条并写入资产表。
8. `/api/ai/model-judgment`：通过，车型判断写入数据库。
9. `GET /`：通过，前端页面可访问。

## 一键测试脚本

已新增：

```bash
bash test_mmn_cloud.sh
```

可选参数：

```bash
MMN_CLOUD_URL=http://121.40.60.90:8765 bash test_mmn_cloud.sh
MMN_CLOUD_SSH_CHECK=false bash test_mmn_cloud.sh
```

脚本会测试：

- 健康接口
- 前端首页
- 模型配置
- RAG 种子包解析
- MMN 策略生成
- Qwen + DeepSeek 双模型融合
- 车型身份识别写入
- 车型判断写入
- 数据库关键表记录数

测试结果会写入：

```text
cloud_model_test_result.json
```

最新一键测试结果：

| 测试项 | 结果 |
| --- | --- |
| `health` | 通过 |
| `frontend` | 通过 |
| `ai_status` | 通过 |
| `rag_seed_parse` | 通过 |
| `strategy_fast_generation` | 通过，使用 Qwen，输出 1454 字 |
| `strategy_deep_generation` | 通过，使用 DeepSeek，输出 2495 字 |
| `fusion_qwen_deepseek` | 通过，Qwen 与 DeepSeek 均返回 |
| `model_identity_write` | 通过 |
| `model_judgment_write` | 通过 |

## 最终判断

当前云端版本已经真正接入 MMN 模型能力，**不是只部署了网页外壳**。

更准确地说，当前云端已经具备：

- MMN Strategy Model 代码层
- 本品/竞品/情绪/属性/身份/Gap/Action 策略工作流
- Qwen 主控生成能力
- DeepSeek 策略推理与质检能力
- RAG 资料包解析与策略引用能力
- 业务数据库写入能力
- 演示数据与历史项目快照
- 前端展示入口

但还没有达到“完整商业级模型中台”的最终状态，主要缺口是：

1. 向量库/embedding 检索尚未落地。
2. ECS 目录需要切换为 GitHub 标准发布链路。
3. PostgreSQL 尚未承载核心业务数据。
4. `Positioning` 已补入本地模型层，需随下一次发布同步到云端。
5. 人工学习案例仍为空，需要继续通过日常使用沉淀。
