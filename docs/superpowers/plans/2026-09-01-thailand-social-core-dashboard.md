# MMN 泰国 Social Media 核心看板实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 MMN 出海版决策驾驶舱首屏增加一个可审计的泰国 Social Media 核心看板，以月度用户渗透率为主口径，分开展示广告可触达率、交叉验证区间、平台角色和数据边界。

**Architecture:** 使用独立 JSON 文件保存平台指标、来源类别、时间与可信度；独立 JavaScript 负责 fail-closed 加载、指标切换、分层筛选和安全渲染；独立 CSS 只在 `body[data-edition="global"]` 下展示，不修改国内版数据与管理层看板。页面仅在现有 `index.html` 接入一个容器和两个静态资源。

**Tech Stack:** 原生 JavaScript、HTML、CSS、JSON、Node.js 静态契约测试。

## Global Constraints

- 主指标名称必须为“月度用户渗透率”，不得写成相互排他的“市场份额”。
- 月度使用率、广告可触达率、月活、新闻使用率和外部引流份额不得相加或混排行。
- 数据缺失必须显示“未公开／不可比”，不得以 0 填充。
- 客户界面使用中性来源类别，不展示底层数据服务或技术供应商名称。
- 只修改本地代码；不提交、不推送、不部署、不写业务数据库。

---

### Task 1: 固化可审计数据合同

**Files:**
- Create: `data/thailand_social_market_latest.json`
- Test: `tests/test_thailand_social_dashboard_ui.js`

**Interfaces:**
- Produces: `market`, `as_of`, `primary_metric`, `platforms[]`, `source_classes[]`, `decision_layers[]`, `guardrails[]`。
- `platforms[].monthly_usage_pct` 必须为 0–100；`ad_reach_internet_pct` 可为 `null`；`confidence` 只允许 `high`、`medium`、`medium_low`。

- [ ] **Step 1: 写失败测试**，断言数据合同、十个平台、缺失值、来源链接和客户界面中性标签。
- [ ] **Step 2: 运行 `node tests/test_thailand_social_dashboard_ui.js`**，预期因 JSON、JS、CSS、HTML 容器缺失而失败。
- [ ] **Step 3: 创建 JSON 数据合同**，录入已核验数字、交叉区间、来源数量、角色和证据时间。
- [ ] **Step 4: 重跑测试**，预期数据合同部分通过，界面资产仍失败。

### Task 2: 实现核心看板和交互

**Files:**
- Create: `thailand-social-dashboard.js`
- Create: `thailand-social-dashboard.css`
- Modify: `index.html`
- Test: `tests/test_thailand_social_dashboard_ui.js`

**Interfaces:**
- Consumes: `data/thailand_social_market_latest.json`。
- Produces: `window.MMNThailandSocialDashboard`，包含 `load()`、`render()`；DOM 控件 `data-th-social-metric` 与 `data-th-social-tier`。

- [ ] **Step 1: 在出海版驾驶舱增加 `#thailand-social-dashboard` 容器**，并接入独立 CSS/JS。
- [ ] **Step 2: 实现 fail-closed 加载**；请求失败时只显示证据不可用与下一步，不渲染零值。
- [ ] **Step 3: 实现月度渗透率／广告可触达率切换**；缺失广告数据明确显示“未公开”。
- [ ] **Step 4: 实现核心／补充分层筛选、交叉区间、决策层和来源审计卡**。
- [ ] **Step 5: 实现 1440px 与 390px 响应式、键盘焦点和 reduced-motion**。
- [ ] **Step 6: 运行 `node tests/test_thailand_social_dashboard_ui.js && node --check thailand-social-dashboard.js`**，预期全部通过。

### Task 3: 回归与真实浏览器验收

**Files:**
- Test: `tests/test_thailand_social_dashboard_ui.js`
- Test: `tests/test_global_foundation_ui.js`
- Test: `tests/test_data_first_cockpit_ui.js`

**Interfaces:**
- Produces: 出海版真实页面、网络、控制台、桌面和移动端可用性证据。

- [ ] **Step 1: 运行静态回归**：`node tests/test_thailand_social_dashboard_ui.js && node tests/test_global_foundation_ui.js && node tests/test_data_first_cockpit_ui.js && git diff --check`。
- [ ] **Step 2: 使用独立临时数据库和空闲端口启动服务**，不影响 8765 和业务数据库。
- [ ] **Step 3: 浏览器切换“出海版”并进入决策驾驶舱**，验证面板显示、两种指标切换、筛选、来源链接、无失败请求和控制台错误。
- [ ] **Step 4: 在 1440px 与 390px 检查无裁切、横向溢出、不可点击区域或小字号失真。
- [ ] **Step 5: 切回国内版**，确认泰国看板不可见且国内驾驶舱未改变。
