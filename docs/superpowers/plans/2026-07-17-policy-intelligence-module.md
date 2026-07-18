# Policy Intelligence Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变 MMN 现有核心流程的前提下，新增可追溯、需人工审核、能够把政策变化转成车型影响与营销机会的 Policy Intelligence 市场环境变量模块。

**Architecture:** 新增独立 `policy_intelligence.py` 领域模块，负责来源门禁、SQLite 表、政策解析契约、审核、Eval、车型影响和看板聚合；`server.py` 只完成初始化、模型网关与 HTTP 路由接线。前端新增独立 `policy-intelligence.js/css` 页面，同时将已审核政策摘要以只读信号注入机会地图和管理层驾驶舱，不改写原有计算链路。

**Tech Stack:** Python 3 标准库、SQLite、现有 MMN HTTPServer 与模型网关、原生 JavaScript、CSS、Node/Python unittest、Playwright + 本机 Chrome。

## Global Constraints

- 保持现有 MMN 核心流程、导航分组和已有模块不变；仅在用户授权的市场环境分析层新增入口。
- Level 1/2 官方来源是政策事实依据；Level 3 只能辅助验证，不能单独发布政策结论。
- AI 不得创造政策内容；原文、URL、哈希、抓取时间和解析版本必须留存。
- 未经人工审核或来源不明的政策只能标记为“待验证”，不得进入机会地图和驾驶舱。
- Policy Intelligence 输出必须区分事实、规则推断、营销假设和未知，并经过 5×20 分 Eval。
- 不新增第三方运行依赖，不改动或删除用户已有数据。
- 当前工作树已有未提交改动；不执行自动提交，只对本计划文件做差异隔离和逐项验证。

---

### Task 1: Policy 数据契约与来源门禁

**Files:**
- Create: `policy_intelligence.py`
- Create: `tests/test_policy_intelligence.py`

**Interfaces:**
- Produces: `init_policy_schema(conn) -> None`
- Produces: `validate_source_url(url, source_level) -> str`
- Produces: `normalize_policy_json(payload, source) -> dict`
- Produces: `save_policy_document(conn, *, org_id, edition, source, raw_text, metadata) -> dict`

- [ ] **Step 1: Write failing schema and source-gate tests** covering all required fields, Level 3 non-authority, missing source URL, non-public URL, and default `pending_verification` status.
- [ ] **Step 2: Run RED** with `python3 -m unittest tests.test_policy_intelligence.PolicySchemaTest -v`; expect import/function failures.
- [ ] **Step 3: Implement minimal domain constants, six SQLite tables, indexes, URL allowlist/SSRF guard, JSON normalization, and immutable raw-source hash.**
- [ ] **Step 4: Run GREEN** with the same command; expect all schema/source tests to pass.
- [ ] **Step 5: Run `git diff -- policy_intelligence.py tests/test_policy_intelligence.py`** and confirm no unrelated file is touched.

### Task 2: 采集、AI 解析、人工审核与 Eval

**Files:**
- Modify: `policy_intelligence.py`
- Modify: `tests/test_policy_intelligence.py`
- Modify: `server.py`

**Interfaces:**
- Consumes: Task 1 policy document and source contracts.
- Produces: `fetch_policy_source(url, *, source_level, fetcher=None) -> dict`
- Produces: `policy_parse_prompt(raw_text, source) -> list[dict]`
- Produces: `parse_policy_with_gateway(raw_text, source, gateway) -> dict`
- Produces: `review_policy(conn, policy_id, decision, reviewer, note) -> dict`
- Produces: `evaluate_policy_analysis(conn, analysis_id, scores, reviewer, note) -> dict`

- [ ] **Step 1: Write failing tests** for bounded fetches, redirect/domain checks, JSON-only parsing, quote/source preservation, review publication gate, 0–20 score validation, total score, and version history.
- [ ] **Step 2: Run RED** with `python3 -m unittest tests.test_policy_intelligence.PolicyWorkflowTest -v`; expect missing workflow failures.
- [ ] **Step 3: Implement the minimal workflow** using existing MMN model calls through an injected gateway; model failure must retain raw document and return `pending_verification`, never fabricated fallback facts.
- [ ] **Step 4: Add authenticated HTTP routes**: `GET /api/policy-intelligence/dashboard`, `GET /api/policy-intelligence/policies`, `POST /api/policy-intelligence/fetch`, `/parse`, `/review`, `/evaluate`.
- [ ] **Step 5: Run GREEN and API contract tests**; expect invalid inputs to return 400 and unreviewed data to remain unpublished.

### Task 3: 车型影响与 Policy Opportunity Map

**Files:**
- Modify: `policy_intelligence.py`
- Modify: `tests/test_policy_intelligence.py`
- Modify: `opportunity_pipeline.py`
- Modify: `tests/test_opportunity_pipeline.py`

**Interfaces:**
- Produces: `build_vehicle_policy_impact(conn, *, model, region, profile, org_id, edition) -> dict`
- Produces: `build_policy_opportunities(conn, *, model, region, evidence, org_id, edition) -> list[dict]`
- Opportunity item contract: `label`, `type="policy_environment"`, `factIds`, `inference`, `hypothesis`, `action`, `leadingIndicator`, `conversionIndicator`, `stopCondition`, `reviewStatus`, `evalScore`.

- [ ] **Step 1: Write failing tests** showing that national/province/city matching, energy eligibility, active dates and subsidy caps affect the model result, while expired/unreviewed policies do not.
- [ ] **Step 2: Run RED** and verify failures are due to missing policy impact functions.
- [ ] **Step 3: Implement transparent rule calculations** and marketing opportunity templates that reference exact policy IDs; do not infer sales lift.
- [ ] **Step 4: Add optional `policy_signals` input to the opportunity pipeline** without changing existing results when it is absent.
- [ ] **Step 5: Run GREEN plus existing opportunity-map regression tests.**

### Task 4: Policy Intelligence Dashboard

**Files:**
- Create: `policy-intelligence.js`
- Create: `policy-intelligence.css`
- Create: `tests/test_policy_intelligence_ui.js`
- Modify: `index.html`
- Modify: `app.js`

**Interfaces:**
- Consumes: `GET /api/policy-intelligence/dashboard?edition=&model=&region=`.
- Produces: existing-page route `policyintelligence`, city/province selection, 12-month trends, model impact, opportunity/evidence drill-down, review queue.

- [ ] **Step 1: Write failing static UI tests** for navigation placement, page registration, source links, non-news information hierarchy, accessible buttons/selects, loading/error/empty states.
- [ ] **Step 2: Run RED** with `node tests/test_policy_intelligence_ui.js`; expect missing page/script/style failures.
- [ ] **Step 3: Add the page and assets** using existing `--surface`, `--line`, `--ink`, `--muted`, `--green`, `--amber`, `--red`, radius and shadow tokens. Keep all existing navigation items and ordering intact.
- [ ] **Step 4: Implement map matrix, trend SVG, model impact and Policy Opportunity Map** with keyboard-accessible controls and source/effective-date labels.
- [ ] **Step 5: Run GREEN, `node --check policy-intelligence.js`, and existing UI regression tests.**

### Task 5: 管理层驾驶舱只读接入

**Files:**
- Modify: `group_dashboard.py`
- Modify: `group-dashboard.js`
- Modify: `group-dashboard.css`
- Modify: `tests/test_group_dashboard.py`
- Modify: `tests/test_group_dashboard_ui.js`

**Interfaces:**
- Consumes: `build_policy_dashboard_payload(conn, ...)` published summaries only.
- Produces: management view key `policy`, label `政策环境`, and selected-model/region evidence drill-down.

- [ ] **Step 1: Write failing backend/UI tests** proving the new view is additive and existing seven views remain unchanged in name and order.
- [ ] **Step 2: Run RED** and verify the policy view is absent.
- [ ] **Step 3: Extend group dashboard payload and render one new view**; no existing metric or sales-warning calculation may change.
- [ ] **Step 4: Run GREEN plus group-dashboard regression tests.**

### Task 6: Documentation, complete verification, browser acceptance, adversarial review

**Files:**
- Create: `docs/研发档案/2026-07-17_beta-1.02_Policy-Intelligence-MVP.md`
- Modify: `docs/HANDOFF_QWEN_AGENT.md`

**Interfaces:**
- Documents data authority, review gates, API contracts, UI route, test evidence, unresolved source coverage and next phases.

- [ ] **Step 1: Record implementation and source-governance decisions** from the MMN 研发团队 perspective.
- [ ] **Step 2: Run fresh verification:** Python unit tests, Node UI tests, `python3 -m py_compile`, `node --check`, and `pnpm release:gate` where applicable.
- [ ] **Step 3: Start/reload the local app and verify** `http://127.0.0.1:8765/` with independent Chrome at 1440px: navigation, dashboard, city interaction, model impact, source drill-down, review state, network status, console cleanliness, and no page-level overflow.
- [ ] **Step 4: Save desktop screenshots** to `output-policy-after.png` and `output-policy-review.png` and compare against `output-policy-before.png` for navigation and token regression.
- [ ] **Step 5: Run an adversarial diff review** for correctness, architecture, security, performance, accessibility and evidence integrity; fix all Critical/Required findings and rerun affected gates.

## Definition of Done

- [ ] Dashboard answers “政策变化对于汽车品牌营销意味着什么”，not “最近有哪些政策”.
- [ ] Every published fact has a raw source, URL, source level, hash, effective dates and human review record.
- [ ] Unclear or Level 3-only evidence remains “待验证”.
- [ ] Vehicle impact never claims empirical sales causality.
- [ ] Opportunity/cockpit receive only approved and evaluated policy signals.
- [ ] Existing MMN flows and modules pass regression tests unchanged.
- [ ] Real desktop browser evidence and研发档案 are present.
