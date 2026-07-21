# Spec: 三路独立归因推理与裁决

## Objective

为销量预警车型提供可审计的跨域研判：以同一锁定证据包串联细分市场容量、细分市场销量、声量、线索和订单达成率，分别调用三路旗舰能力，再做确定性裁决并持久化。客户界面只有在三路全部完成、共同引用同一证据且结论方向一致时显示“已完成”；否则显示待复核或证据不足。

## Tech Stack

- Python 标准库 HTTP 服务与 SQLite
- 现有 `call_provider` 三路模型网关
- 原生 JavaScript / CSS 驾驶舱
- Python `unittest`、Node UI 合约测试、Playwright 业务流验收

## Commands

- 单域测试：`python3 -m unittest tests.test_attribution_reasoning`
- UI 合约：`node tests/test_lead_dashboard_ui.js`
- 全面门禁：`bash scripts/release_gate.sh`
- 本地服务：`MMN_AUTO_OPEN_BROWSER=false zsh scripts/ensure_local_mmn.sh`

## Project Structure

- `attribution_reasoning.py`：证据包、输出规范化、三路裁决、SQLite 持久化
- `server.py`：实际模型调用和 GET/POST API
- `lead-dashboard.js` / `lead-dashboard.css`：摘要、运行状态、展开详情
- `tests/`：领域、API、UI 与发布回归

## Code Style

```python
if common_evidence_ids and verdicts_aligned and all_providers_completed:
    status = "aligned"
else:
    status = "manual_required"
```

事实计算由确定性代码负责；模型只能解释锁定事实、提出替代解释和验证动作。公开响应使用中性角色名，不暴露供应商名称或密钥。

## Testing Strategy

- 单元：证据指纹稳定、缺失证据不调用、三路不完整/证据不相交/方向冲突均禁止发布。
- 集成：真实 API 生成记录，GET 可读最新结果，服务重启后仍可读取。
- UI：未运行、运行中、已完成、待复核、失败五态；桌面与 390px；点击、外部点击与 Escape。
- 发布：本地和服务器分别验证实际业务路径、数据库记录、日志和静态资源版本。

## Boundaries

- Always：三路使用同一证据包和指纹；保留逐路原始结构化输出、耗时、错误与裁决理由；持久化采用新增表；界面保留因果边界。
- Ask first：删除历史记录、改变现有销量预警算法、覆盖原始线索或订单数据。
- Never：用静态文案冒充模型结果；将声量视为需求；将订单达成率称为线索转化率；一条路径失败后仍发布一致结论；在客户界面暴露供应商信息。

## Success Criteria

1. 点击“开始三路复核”触发三路真实独立调用，响应含三路状态和同一证据指纹。
2. 仅三路共同证据、判断方向和主要断点一致且最低置信度不低于 0.6 时发布结论。
3. 结论、替代解释、下一步动作、停止条件、逐路输出与裁决记录写入 SQLite；重启后可读取。
4. 任一路失败、无共同证据或冲突时不发布最终结论，明确进入人工复核。
5. 本地与服务器的真实 E7X 驾驶舱均能完成运行、展开、刷新后回读；无新增控制台错误。

## Rollback

回滚应用文件即可停止新调用；新增表和历史审计记录保留但不影响旧流程。若生产异常，恢复上一个归档版本并验证首页、健康状态及驾驶舱旧流程。

## Open Questions

无阻塞问题。当前实现以奥迪E7X已接入的线索/订单数据为首个可运行对象；其他车型在证据不完整时保持“证据不足”。
