# MMN 品牌穿透分歧治理与双环境部署 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 独立审查遵循 AGENTS.md，不以实施者自审替代；本文件不授予执行或发布权限。

**Goal:** 将品牌穿透的整行一致性拦截改为有证据约束的声明级分层输出，并完成本地、MMN服务器部署与验收。

**Architecture:** 保留三路盲审和当前页面结构。新增本模块政策与版本存储层，服务端生成脱敏投影，旧 v3 路径默认不变；按 legacy/shadow/enabled 分阶段验收，发布不搬运业务数据。

**Tech Stack:** 既有 Python 服务、SQLite、原生 JavaScript/HTML、unittest、Node/Playwright、本地受管运行器、Docker Compose；不引入新模型或前端框架。

## Global Constraints

- 本计划唯一产品合同：`docs/工单/2026-09-08_MMN品牌穿透分歧治理与分层输出_本地及服务器部署工单.md`，编号 `MMN-BRAND-REVIEW-20260908-001`。
- 2026-09-08 用户“开工”已授权隔离实施与验证；当前形成候选代码，尚未提交、推送、本地或服务器部署、启用。
- 保存至 `docs/工单/` 的主工单为产品与部署验收依据；本计划为研发拆解，不替代权限检查。
- 仅品牌级与本品逐竞品结论在范围内；不改其他模块、导航、视觉 Token、既有业务数据。
- 本机源工作区：`/Users/ellis/Documents/MMN汽车营销引擎/china-auto-marketing-engine`；下文路径均相对此仓库。实施时先建立经核验基线的隔离工作树，隔离数据根。
- 下述复选项为原始计划；实际阶段记录见末尾“实施记录”，不能仅凭计划清单当作当前可调用能力。
- 未获得发布授权前，仅形成候选与隔离验收证据；严禁直接执行后述部署命令。

---

## 实施记录（隔离候选，非发布回执）

- 工作树 `.worktrees/mmn-brand-review-v4-20260908`，分支 `codex/mmn-brand-review-v4-20260908`，基线 `3c8987b56f17552cdcd0240c0ff8bc329eba212e`。与受管本地运行包存在 38 项跟踪文件差异；正式发布前必须逐项对齐，不能整包覆盖。
- W0：已只读定位与截图状态一致的历史快照；三路原始输出未留存。合成复现和独立审查通过；不声称恢复了真实原答。
- W1：新增纯策略与 28 项测试，旧 v3 文件未修改；独立复审通过。三项早期问题已完成失败复现与修复。
- W2：版本库、运行器及服务端适配已实现，独立复审通过；取消及运行中撤销开关补充独立复审通过。后端合并 87 项定向测试通过，未迁移正式数据、未调用真实模型。已派发远程请求不能保证即时中止，但取消先成功时不再发布复核版本。
- W3：完成分层展示、复核对话框、刷新与取消接入，27 项前端测试通过；合成专用实例的真实开始/取消/采纳/修改/否决/刷新、1440/1280/390、手机键盘和最终独立复审通过。精确 CSP 保持匹配，沙箱权限未放宽。
- W4：离线评测工具与 13 项机制测试及独立复审通过；同源组、逐声明误判和独立保留集门禁已加入。真实 Gold/独立负责人批准未就绪，真实合成回放为 not_ready，禁止报告业务改善率。
- W5：仅代码模式与既有部署合同 17 项测试及最终独立复审通过；候选健康、路由和标签提升失败有明确保留/回退路径。执行测试使用替身 Docker，没有执行部署。
- W6：未执行；隔离工程验收已完成，仍待真实案例质量验收、运行基线对齐及明确发布授权。

最终隔离门禁：清洁环境完整执行通过，863 项 Python（97 模块）、38 份前端测试文件、98 项既有浏览器检查；86 张表启动/浏览器/源备份逻辑变化为零，工作树零漂移。门禁后仅同步验收文档，并再次执行状态、研发档案及差异格式检查。业务源码未再变更。验收回执：`docs/工单/2026-09-08_MMN品牌分层复核_隔离验收回执.md`。本单不因工程机制通过而关闭：真实 Gold、运行基线对齐、本地与服务器发布及启用仍未完成。

实现能力限制：当前自动解释只覆盖可确定核验的来源提及和双品牌样本提及；候选动作仅限完整条件的人工观察。人工确认只允许同一可核验命题的中性软差异；任意营销判断、实质反对及任意改写不自动发布。这是安全的首版发布矩阵，不等同于完成通用语义理解。最终全量门禁与页面结果见本轮验收回执，不以中途通过替代最终结果。

---

## Task 1：冻结基线、复现与声明合同（W0）

**Files:** Read `brand_penetration_analysis.py`、`server.py::run_brand_penetration_conclusions`、`demo-brand-weekly-radar.html::renderBrandDecision`、`tests/test_brand_penetration_analysis.py`、`tests/test_brand_penetration_module.py`；Create `tests/fixtures/brand_review_v4_cases.json`、`tests/test_brand_review_policy.py`。

**Interfaces:** 输入为同一冻结证据包与三路原始输出；输出为脱敏测试夹具及逐声明 expected 状态，不修改生产快照。夹具外层固定 `caseId, sourceKind, packet, reviews, expected`；sourceKind 只能为 synthetic 或 historical_redacted。

- [ ] 记录 Git、工作树、本地运行包、服务器已知记录的差异；无法确认部署基线时标注待核验，绝不覆盖原工作树。
- [ ] 只读查找截图同轮 snapshot/evidenceFingerprint/reviews；未保存原始输出则记录证据缺口，并创建合成复现，不声称已恢复真实原答。
- [ ] 先在隔离根运行旧定向测试，保留完整日志及退出码：

```bash
python3 -m unittest tests.test_brand_penetration_analysis tests.test_brand_penetration_module -v
```

- [ ] 增加复现断言：只改 actionDirection 时，旧 v3 为 manual_required；旧选文策略能选出枚举相同但文本无依据的行。预期旧行为被明确复现，不修改旧测试去制造通过。
- [ ] 冻结主工单第8节 Gold 标签、开发/留出划分和规则词典正反例；真实记录不足是启用阻塞，不是伪造样本的理由。

## Task 2：最小发布矩阵及字段级策略（W1）

**Files:** Create `brand_review_policy.py`、`tests/test_brand_review_policy.py`；Modify `brand_penetration_analysis.py`。

**Interfaces:** 新增纯函数 `layer_status(kind, hard_failures, completed, supports, conflicts)`；新增 `fuse_layered_reviews(provider_outputs, packet, validation_records)` 生成 v4；现有 `fuse_reviews` 保持 v3 默认行为。validation_records 只能由可信服务端核验过程生成，不能来自公共请求体。

下面为最小状态矩阵的可执行规格，不能把它当成完整语义核验器：

```python
def layer_status(kind, hard_failures, completed, supports, conflicts):
    if hard_failures:
        return "blocked"
    if conflicts:
        return "disputed"
    if kind == "source_fact":
        return "source_only"
    if completed != 3:
        return "review_incomplete"
    if supports != 3:
        return "manual_required"
    return "supported" if kind == "inference" else "candidate"
```

`supports` 表示同一原子声明的有依据支持，不是三张卡片的分类标签一致；只有无语义歧义的确定性规范化可计入支持。source_fact 仅限已通过来源/锚点/范围门禁的可核对来源信息，不能传入任意模型改写。模型新增的解释声明无法对齐到同一命题时保持 manual_required，不自动补足支持数。

- [ ] 写入以下失败测试并观察因生产函数不存在而失败；不能接受语法/依赖错误作为 RED：

```python
import unittest
from brand_review_policy import layer_status

class LayerStatusTest(unittest.TestCase):
    def test_source_information_survives_action_disagreement(self):
        self.assertEqual(layer_status("source_fact", [], 2, 0, []), "source_only")

    def test_fact_conflict_blocks_dependent_claim(self):
        self.assertEqual(layer_status("inference", ["source_conflict"], 3, 3, []), "blocked")

    def test_majority_does_not_erase_opposition(self):
        self.assertEqual(layer_status("inference", [], 3, 2, ["opposed"]), "disputed")

    def test_complete_supported_inference_is_available(self):
        self.assertEqual(layer_status("inference", [], 3, 3, []), "supported")

    def test_missing_review_is_not_consensus(self):
        self.assertEqual(layer_status("inference", [], 2, 2, []), "review_incomplete")
```

- [ ] 实现上面最小矩阵，再按工单合同实现 packet 身份/日期/锚点核验、声明规范化、依赖阻断和 v4 投影。新增声明依赖有环时返回 blocked，不能递归无界。
- [ ] 单独为 evidenceId 存在但引文不支持、标签同义化误判、相反趋势、转载去重、逐竞品缺一方、主体/时间错配建立 RED→GREEN。
- [ ] 不以 confidence 选文；用通过的声明构建固定中文模板。不能直接选一路整段建议再加“部分可用”标签。
- [ ] 执行并保留本组与 v3 回归：

```bash
python3 -m unittest tests.test_brand_review_policy tests.test_brand_penetration_analysis -v
```

该任务仅分层判断，不写库、不调模型、不负责客户按钮。清晰的源信息保留与逐声明审核替代“整个品牌三字段全一致”；不是把原门禁原样换个名字。

## Task 3：版本、权限与限次运行（W2）

**Files:** Create `brand_review_repository.py`、`tests/test_brand_review_repository.py`、`tests/test_brand_review_runtime.py`；Modify `server.py`、`.env.example`。

**Interfaces:** `save_review_version(connection, scope, payload, expected_version, idempotency_key)` 追加版本；`append_review_decision(connection, scope, actor, request)` 追加人工裁决；`get_review_projection(connection, scope, review_id)` 返回脱敏投影。scope 来自服务端鉴权，不接受客户端租户覆盖。

- [ ] 为越租户、无写权限、旧版本、重复请求、同键异文、旧快照修改各写失败测试；同键异文与旧版本期望冲突，无写权限期望403，跨租户不得返回对象数据。
- [ ] 在显式迁移阶段创建工单规定的两张新增表与唯一约束；事务内比对 expectedVersion 并追加，不更新旧版本正文。
- [ ] 建立服务端 v4 模式/allowlist 分支。legacy 请求完整 JSON 与旧逻辑逐字段一致，新库不创建、新调用数为0。
- [ ] 给三路首轮/结构修复增加共用截止时间、取消与预算计数。用注入 provider_runner 精确断言最多6次、首次盲审同包、成功行不被修复覆盖、401/403不重试、超时不再执行后续修复。
- [ ] 给无凭据 GET/越租户/试用写入增加 API 测试；保持已有分析入口，人工裁决新增薄路由必须复用认证，origin/CSRF 策略按现有框架落实。
- [ ] 模型原始输出、校验记录、人工决定存内部版本；公共 JSON 只经固定字段投影，敏感错误仅返回中文类别。
- [ ] 执行：

```bash
python3 -m unittest tests.test_brand_review_repository tests.test_brand_review_runtime -v
```

## Task 4：原位展示与人工处理闭环（W3）

**Files:** Modify `demo-brand-weekly-radar.html`、`app.js`；Create `tests/test_brand_review_ui.js`、`scripts/verify_brand_review_ui.js`；仅必要时修改 `style.css`。

**Interfaces:** iframe 继续接受现有 snapshot/mart 消息，v4 内容读取统一投影；人工裁决由父页面认证请求提交，iframe 消息必须核验 origin、source、当前项目和请求版本，不从消息信任 actor/scope。

- [ ] 按 AGENTS.md 读取 frontend-design、项目 ui-ux-pro-max、taste-skill；拍摄原1440/1280/390基线，记录现有导航与 Token。
- [ ] 先写 v4 仅事实卡、分歧卡、完整卡、复核未完成卡与 v3 历史卡的渲染失败测试；未知 schema 不能假装正常。
- [ ] 原位增加分层内容和中性状态；保留品牌定位证据行为，独立复核按钮不能嵌套在现有 button 内；取消把整体 aligned 作为唯一显示开关。
- [ ] 接通采纳/修改/否决及理由保存，409时提示重新读取，403时禁止保存；刷新后从服务端恢复，不以 localStorage 替代保存。
- [ ] 用真实服务、隔离数据完成开始分析、证据下钻、修改、否决、刷新、切换项目；合成与真实模型场景分别保存证据。
- [ ] 执行并记录屏幕与控制台：

```bash
node --check app.js
node tests/test_brand_review_ui.js
node scripts/verify_brand_review_ui.js
```

新浏览器脚本默认只对隔离测试实例运行；要求显式指定测试数据根和 URL，拒绝默认向8765或公网写入。

## Task 5：质量评估与仅代码发布能力（W4—W5）

**Files:** Create `scripts/eval_brand_review_v4.py`、`tests/test_brand_review_eval.py`、`tests/test_brand_review_deploy.py`；Modify `scripts/deploy.sh`、`README_DEPLOY.md`；需要对接通用 Eval 时 Create `mmn_eval/brand_review.py`。

**Interfaces:** 评测输出冻结 datasetHash/ruleVersion、逐声明命中/误拦截/误放行、分母和结论。部署仅代码模式输入 `MMN_DEPLOY_CODE_ONLY=true`，保留原默认资产同步合同。

- [ ] 为零分母、合成冒充真实、相同快照泄漏到留出集、少数关键反例误放、伪造验收记录写失败测试；不允许仅凭数量满足质量门禁。
- [ ] 实现工单第8.2节指标，低于真实样本门槛则返回 not_ready，不把工具运行成功作为业务通过。
- [ ] 为 deploy.sh 建立 mock docker 命令记录：仅代码模式不可 cp 业务data、不可down -v、构建失败不可停旧服务，默认模式仍保留既有合法资产同步。
- [ ] 将预构建放在旧服务切换前，按服务最小影响切换；对无.git归档发布和保留旧镜像回退分别加入测试。
- [ ] 禁止在生产库直接运行测试；执行定向回归、完整测试与发布门禁：

```bash
python3 -m unittest tests.test_brand_review_eval tests.test_brand_review_deploy -v
python3 -m unittest discover -s tests -v
npm run release:gate
git diff --check
```

- [ ] 对实际 diff 做独立审查，修复 Critical/Required 后重新跑受影响测试和真实页面。已有无关失败必须定位并说明，不得删测试或宣称全通过。

## Task 6：获得发布授权后的本地交付（W6-L）

**Files:** Update `MMN_CURRENT_STATE.md`、`release.md`、`docs/HANDOFF_QWEN_AGENT.md`；Create 本工单研发档案与 `output/brand-review-v4/local-acceptance.json`。

- [ ] 核对用户发布授权、精确候选清单及功能基线；仅暂存审查过的本单路径，按授权提交/推送，不运行整仓暂存。
- [ ] 按主工单第9节完成一致性备份、恢复演练、活动任务/监听者检查及数据基线。
- [ ] 发布命令使用操作员已经核验的非空绝对候选路径变量 `MMN_BRAND_RELEASE_SOURCE`；变量未设时必须拒绝执行：

```bash
python3 scripts/managed_local_runtime.py publish --source "${MMN_BRAND_RELEASE_SOURCE:?verified candidate path required}"
python3 scripts/managed_local_runtime.py agent install --timeout 30
python3 scripts/managed_local_runtime.py agent verify --timeout 30
```

- [ ] legacy、shadow、enabled allowlist依次验收；实际发布回执记录路径/哈希，不在计划里预填新版本。
- [ ] 完成主工单第10节真实业务流及数据差异检查；预算未授权不触发真实模型调用，不把隔离 fixture 写成真实业务验收。
- [ ] 回退演练使用本次安装返回、已核验的备份路径；不得固定使用旧UI备份：

```bash
python3 scripts/managed_local_runtime.py agent rollback --backup "${MMN_BRAND_ROLLBACK_BACKUP:?verified backup path required}" --timeout 30
```

- [ ] 保存演练后最终目标版本与开关证据，避免回退后却报告新版本已启用。

## Task 7：获得服务器发布授权后的源站交付（W6-S）

**Files:** 使用同一已审查发布候选；Create `output/brand-review-v4/server-acceptance.json`；Update 双环境发布/交接/状态记录。

- [ ] 只读核验实际 MMN 服务器、目录、挂载、镜像和入口，严禁误操作同机其他产品。历史路径和域名不可当实时证明。
- [ ] 校验已推送 commit 归档或镜像 digest；备份代码/配置/一致性状态，预构建成功后才允许维护窗口切换。
- [ ] 以下是新增模式测试通过后的执行形态，当前脚本尚未具备此模式，不能提前调用：

```bash
MMN_SKIP_GIT_PULL=true MMN_DEPLOY_CODE_ONLY=true bash scripts/deploy.sh
```

命令必须在服务器上核验过的 MMN 候选发布目录执行，且已完成归档哈希检查；不内嵌主机IP、密钥、账号或Token。

- [ ] 按主工单第11节逐项验证：legacy历史兼容→allowlist启用→真实鉴权分析/裁决/刷新→跨租户负向→资源哈希→15分钟观察→数据允许差异。
- [ ] 源站与公网入口分别记录；公网被备案/TLS阻断时不扩大修复范围、不用明文公网传凭据。
- [ ] 无.git服务器使用预留旧镜像/代码归档做代码回退，不能调用要求.git的旧回滚脚本；持久化卷保持原样。
- [ ] 核对本地/服务器规则与核心文件哈希，更新 `MMN_CURRENT_STATE.md` 为真实分项状态并执行：

```bash
npm run check:mmn-state
```

- [ ] 对照主工单第13节关闭清单交付。无真实业务验收、Gold未通过、服务器未部署或未启用，只能报告相应阶段状态，不能关单。

## 文档自审记录

- 覆盖：分层输出、声明级证据、逐竞品、运行失败、人工反馈、旧版兼容、成本边界、双环境部署、数据保护与双级回滚均有任务承接。
- 权限：当前全部执行复选框保持未勾选，不包含已执行声明。
- 技术边界：最小状态函数不是语义验证替代物；有证据的反对意见不被投票覆盖。
- 发布边界：仅代码模式是新增交付项，已有默认数据资产同步不能被删除；实际服务器身份、版本和公网状态需发布前核验。
