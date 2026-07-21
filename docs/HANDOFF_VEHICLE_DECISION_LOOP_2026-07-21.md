# 车型全驾驶舱综合决策闭环本地 Handoff

## 交付状态

闭环工程能力完成，等待真实行动结果验证。当前代码与数据库迁移已完成本地发布候选验证，纳入 `beta-1.03-20260722-decision-closure-1`；生产发布证据以总 handoff 与 `release.md` 的最终闭环记录为准。

## 变更入口

- 领域契约与迁移：`vehicle_decision.py`
- HTTP 适配与路由：`server.py`
- 前端：`vehicle-decision.js`、`vehicle-decision.css`
- 页面加载：`index.html`
- 测试：`tests/test_vehicle_decision.py`、`tests/test_vehicle_decision_server.py`、`tests/test_vehicle_decision_ui.js`
- 研发记录：`docs/研发档案/2026-07-21_beta-1.03_车型全驾驶舱综合决策闭环报告.md`

## 架构和数据契约

上游八类看板继续拥有各自事实与分析。本功能只读适配已持久化结果，冻结为带数据指纹的车型快照，再生成不可变报告版本。报告必须人工发布后才能建立 Action；Result 按版本追加；Learning 和 Know-how 只能由候选经过门禁与人工裁决进入正式状态。所有业务实体按组织隔离。

## 上线前步骤

1. 在目标环境备份 `commercial_demo.db` 并记录哈希与逐表行数。
2. 在维护窗口启动新版本，让增量 schema 初始化执行；再次比对旧表行数。
3. 使用真实账号验证组织隔离、E7X 八表面快照、版本报告与导出。
4. 执行 `483` 项 Python 回归、相关 Node UI 契约和全表面 1440/390 发布门禁。
5. 由 Ellis 审核真实项目的发布门禁、Learning/Know-how 口径后再批准上线。

## 客户侧待提供

- Action 负责人、预算、平台/区域/人群与执行资源。
- 执行前基线、目标、实际执行范围及逐期结果数据。
- 同期价格、金融、渠道、库存、交付和竞品动作等外部变量。
- 客户项目负责人确认与 Ellis 最终业务裁决。

## 残余风险

- 当前八表面不是所有车型都具备完整数据，缺失会被保留为未知，不会自动补齐。
- 本地隔离验收中的结果仅用于验证工程链路，不构成业务有效性证据。
- 单体 `server.py` 的回归面较大，后续路由或权限调整必须重跑全量测试。
- 未经至少两个已批准 Learning 的重复验证，Know-how 默认不会生成；Ellis 显式豁免也仍需人工复核。
