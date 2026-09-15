# MMN 刷新可靠性 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复周度刷新历史丢失及错过调度分钟后不补跑的问题，保留原始数据和清晰的验收证据。

**Architecture:** 保留现有调度脚本 → 签名 POST → 服务端刷新 → 原子快照/状态文件链路。刷新失败只更新本次结果，不抹掉已有成功时间；调度按当日到期窗口领取一次执行机会，成功与尝试分别记录。

**Tech Stack:** Python 标准库、unittest、Bash、既有 Node 检查。

**后续状态（2026-09-16）：** 用户另行授权提交、部署与启用，双环境已完成，发布标签为 `beta-1.03-20260916-weekly-refresh-1`。本计划下方限制记录隔离开发阶段；当前事实以同日 deployment 计划及《MMN周度刷新_双环境部署与启用回执》为准。

## Global Constraints

- 工单 `MMN-REFRESH-RELIABILITY-20260916-001`；用户“开工”授权隔离实施，不包含推送、部署、启用或业务数据刷新。
- 基于 `c28b116` 的独立工作树；主目录用户修改、8765 受管运行包、生产环境、业务数据库均不修改。
- 不改导航、页面布局、车型和业务口径；不涉及 Sales Credo 或 Essence。
- 当前资源按模块独立版本管理，现行版本契约 17 项测试已通过；不把旧分支失败认定为当前缓存缺陷，不统一改版本号。
- 本地运行包含独立增量，后续发布必须按文件审查增量，禁止整体替换运行目录。
- 调度鉴权保留 HMAC；不增加依赖、付费调用、秘密或不受限重试。

## Task 1：成功记录不丢失

Files: `weekly_market_refresh.py`, `tests/test_weekly_market_refresh.py`。

- [x] RED：固定时钟，成功一次再校验失败，断言 `lastSuccessAt` 仍为首次成功时间，快照字节不变；无成功历史时保持空值，不能用载入基线的时间伪造成功。损坏/非对象状态文件不能导致加载失败。
- [x] GREEN：读取状态时仅接受字典；失败路径继承已记录的 `lastSuccessAt`；加载接口不再把 `publishedAt` 当作刷新成功时间。
- [x] 执行 `python3 -m unittest tests.test_weekly_market_refresh -q`，15 项通过。

## Task 2：到期补跑与有界执行

Files: `scripts/run_scheduler.sh`, `tests/test_weekly_refresh_scheduler.py`；既有 `tests/test_group_dashboard_ui.js` 只运行，不需修改。

- [x] RED：执行真实 Bash 调度控制流，测试夹具仅替换日志根目录、将无限循环限定一轮、注入时钟与 HTTP；覆盖周二 00:01/09:01、周三重启、未到时间、周末、重复运行、HTTP 200 业务失败及传输失败。
- [x] GREEN：到期后补跑最新配置窗口；兼容主抓晚于补抓及相同时间。独立审查发现的晚间配置问题已先观察失败再修复，不同轮重复/并发不能重复领取。
- [x] `.attempted` 原子领取每个窗口，`.done` 只在 `ok=true` 且 `result.status=published` 时写入。失败保留日志，下一配置窗口再试，不在 30 秒轮询中连发；默认每周最多五个窗口。
- [x] 执行 `python3 -m unittest tests.test_weekly_refresh_scheduler -q`（10 项）、`bash -n scripts/run_scheduler.sh` 和 `node tests/test_group_dashboard_ui.js`，通过。

## Task 3：验收与交付

Files: `MMN_CURRENT_STATE.md`, `docs/研发档案/2026-09-16_MMN周度刷新可靠性修复.md`。

- [x] 更新状态包和研发记录，区分隔离候选、已验证、未发布、旧数据未知。
- [x] 定向 30 项测试、语法、看板、状态检查通过；最终完整隔离门禁 876 项 Python / 38 份前端测试 / 98 项浏览器检查通过，所有零漂移检查通过。
- [x] 在隔离端口真实浏览器核验成功刷新及后续校验失败保护；不使用 8765 执行写操作，临时服务已停止。
- [x] 实际 diff 独立复审无未解决项；受影响测试和最终门禁重新执行通过。
- [x] 工单回执存放 `docs/工单/2026-09-16_MMN周度刷新可靠性工单与验收.md`；本地定时器实际安装/生产发布未验证，不声称线上数据已更新。
