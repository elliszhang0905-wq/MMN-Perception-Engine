# MMN Eval Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将已确认的 MMN Eval Demo 接入现有 MMN，在「系统设置」中提供连接真实 Eval 报告、运行入口和人工复核记录的可视化页面。

**Architecture:** 保留现有 `index.html + app.js + style.css + server.py` 单页架构。新增聚焦的 `mmn_eval/dashboard.py` 负责报告加载、种子评测运行与按组织隔离的人工复核记录；`server.py` 只增加三个薄 API 路由；前端只在现有导航和渲染循环中增加 `eval` 页面状态与组件。页面只展示真实报告字段；没有 baseline 时明确显示“尚无对比基线”，不构造回归数据。

**Tech Stack:** Python 3 标准库、现有 `http.server` API、原生 JavaScript、HTML/CSS、`unittest`、Node.js 静态 UI 契约测试、Playwright 浏览器验收。

## Global Constraints

- 保留 MMN 现有信息架构、左侧导航、模块名称和视觉变量，不重构主应用。
- Eval 页面位于「系统设置 → Eval评测」。
- 数据读取自 `data/eval/` 与 `output/mmn-eval-seed-report.json`；页面不得把演示数值冒充真实结果。
- 人工结论必须包含 `orgId`、`caseId`、`decision`、`note`、`reviewer`、`decidedAt`，并按组织过滤返回。
- 只有当前报告中 verdict 为 `human_review` 的案例可提交人工结论；驳回必须填写理由。
- 不修改 MMN 与 Sales Credo 的任何边界、配置或凭据。

---

### Task 1: Eval Dashboard 数据服务

**Files:**
- Create: `mmn_eval/dashboard.py`
- Create: `tests/test_mmn_eval_dashboard.py`
- Modify: `mmn_eval/__init__.py`

**Interfaces:**
- Consumes: `mmn_eval.runner.load_jsonl(path)` 与 `evaluate_dataset(cases, outputs, run_name)`。
- Produces: `load_dashboard_payload(...) -> dict`、`run_seed_dashboard(...) -> dict`、`save_human_review(...) -> dict`。

- [x] **Step 1: 写报告加载失败测试**

```python
def test_dashboard_payload_exposes_real_summary_and_pending_reviews(self):
    payload = load_dashboard_payload(self.report_path, self.cases_path, self.reviews_path, org_id="org-a")
    self.assertEqual(payload["report"]["summary"]["evaluated"], 2)
    self.assertEqual(payload["reviewProgress"], {"total": 1, "resolved": 0, "pending": 1})
```

- [x] **Step 2: 运行测试并确认因模块缺失失败**

Run: `python3 -m unittest tests.test_mmn_eval_dashboard -v`
Expected: FAIL with `ModuleNotFoundError: mmn_eval.dashboard`.

- [x] **Step 3: 实现最小报告加载与组织隔离复核存储**

```python
def load_dashboard_payload(report_path, cases_path, reviews_path, *, org_id="local"):
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    cases = {item["id"]: item for item in load_jsonl(cases_path)}
    reviews = [item for item in _load_reviews(reviews_path) if item["orgId"] == org_id]
    return _dashboard_payload(report, cases, reviews)
```

- [x] **Step 4: 增加运行、合法人工结论、驳回理由、非复核案例拒绝测试并实现**

```python
saved = save_human_review(
    "review-case", "rejected", "证据不足", report_path, reviews_path,
    org_id="org-a", reviewer="ellis@example.com",
)
self.assertEqual(saved["decision"], "rejected")
```

- [x] **Step 5: 运行专项测试**

Run: `python3 -m unittest tests.test_mmn_eval_dashboard -v`
Expected: all dashboard service tests PASS.

### Task 2: Eval HTTP API

**Files:**
- Modify: `server.py`
- Create: `tests/test_mmn_eval_api_contract.py`

**Interfaces:**
- Consumes: Task 1 的三个公开函数。
- Produces: `GET /api/eval/report`、`POST /api/eval/run`、`POST /api/eval/human-review`。

- [x] **Step 1: 写 API 路由契约失败测试**

```python
self.assertIn('parsed.path == "/api/eval/report"', server_source)
self.assertIn('parsed.path == "/api/eval/run"', server_source)
self.assertIn('parsed.path == "/api/eval/human-review"', server_source)
```

- [x] **Step 2: 运行测试并确认三个路由均缺失**

Run: `python3 -m unittest tests.test_mmn_eval_api_contract -v`
Expected: FAIL because `/api/eval/report` is absent.

- [x] **Step 3: 添加经过现有认证层的薄路由**

```python
if parsed.path == "/api/eval/report":
    auth = self.current_auth() or {}
    self.send_json({"ok": True, **load_mmn_eval_dashboard(org_id=auth.get("org_id", "local"))})
    return
```

- [x] **Step 4: 运行数据服务与 API 契约测试**

Run: `python3 -m unittest tests.test_mmn_eval_dashboard tests.test_mmn_eval_api_contract -v`
Expected: all tests PASS.

### Task 3: 系统设置 Eval 页面

**Files:**
- Modify: `index.html`
- Modify: `app.js`
- Modify: `style.css`
- Create: `tests/test_mmn_eval_ui.py`

**Interfaces:**
- Consumes: Task 2 三个 API。
- Produces: `loadMmnEvalDashboard()`、`runMmnEval()`、`renderMmnEval()`、`openMmnEvalReview(caseId)`、`saveMmnEvalReview(decision)`。

- [x] **Step 1: 写导航、页面 DOM、真实 API 与人工复核控件失败测试**

```python
self.assertIn('data-page="eval">Eval评测</button>', html)
self.assertIn('class="page" id="eval"', html)
self.assertIn('function renderMmnEval()', app)
self.assertIn('/api/eval/human-review', app)
```

- [x] **Step 2: 运行测试并确认页面缺失**

Run: `python3 -m unittest tests.test_mmn_eval_ui -v`
Expected: FAIL because the Eval navigation item is absent.

- [x] **Step 3: 添加最小可读页面与加载状态**

```javascript
let mmnEvalState={loading:false,running:false,data:null,error:"",filter:"all",activeCaseId:""};
async function loadMmnEvalDashboard(){
  mmnEvalState.loading=true; renderMmnEval();
  try{mmnEvalState.data=await api("/api/eval/report")}finally{mmnEvalState.loading=false;renderMmnEval()}
}
```

- [x] **Step 4: 添加总览、五维得分、真实 baseline 空状态、案例筛选和人工复核抽屉**

```javascript
const comparison=data.comparison;
const comparisonCopy=comparison?renderComparison(comparison):"尚无对比基线；保存首个稳定版本后再显示回归。";
```

- [x] **Step 5: 运行 UI 与后端专项测试**

Run: `python3 -m unittest tests.test_mmn_eval_ui tests.test_mmn_eval_dashboard tests.test_mmn_eval_api_contract -v`
Expected: all tests PASS.

### Task 4: 端到端验收与文档

**Files:**
- Modify: `docs/mmn-eval.md`
- Modify: `docs/HANDOFF_QWEN_AGENT.md`
- Create: `docs/研发档案/2026-07-17_beta-1.02_MMN-Eval可视化页面.md`

**Interfaces:**
- Consumes: 完成后的真实页面与 API。
- Produces: 可复现的验收记录和人工确认入口。

- [x] **Step 1: 运行专项与全量 Python 测试**

Run: `python3 -m unittest tests.test_mmn_eval_contracts tests.test_mmn_eval_scorer tests.test_mmn_eval_runner tests.test_mmn_eval_dashboard tests.test_mmn_eval_api_contract tests.test_mmn_eval_ui -v`
Expected: all Eval tests PASS.

Run: `python3 -m unittest discover -s tests -p 'test_*.py'`
Expected: full Python suite PASS.

- [x] **Step 2: 运行语法、差异和发布门禁**

Run: `python3 -m py_compile mmn_eval/*.py server.py && git diff --check && bash scripts/release_gate.sh`
Expected: exit code 0 and release gate PASS.

- [x] **Step 3: 启动真实 MMN 并用 Playwright 验收**

Run: `MMN_AUTO_OPEN_BROWSER=false python3 server.py`
Expected: local MMN serves successfully; Eval navigation opens the page, real report loads, filters work, review drawer accepts a decision, console errors are empty.

- [x] **Step 4: 更新文档并记录边界**

Document exact API routes, report source, review storage, test counts, screenshot path, and the fact that real historical Gold Set expansion remains a subsequent data task.

## Self-Review

- Spec coverage: Demo 中的总览、五维评分、案例筛选、人工复核与运行入口均有对应任务；生产页面将版本对比改为真实数据或明确空状态。
- Placeholder scan: 无 `TBD`、`TODO` 或未定义接口。
- Type consistency: 三个数据服务函数在 Task 1 定义，Task 2 原样消费；五个前端函数只消费 Task 2 的三个固定路由。
