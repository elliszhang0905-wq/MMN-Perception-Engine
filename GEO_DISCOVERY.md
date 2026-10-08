# GEO 仓库诊断（2026-10-08）

授权：Ellis“开工”承接 2026-10-08 GEO 工单；后续确认“先完成离线开发，真实联调暂时阻塞”。本轮仅本地代码与隔离测试，不提交、推送、部署、重启既有运行服务或付费调用。

## 实际架构与基线

- 实际应用：`china-auto-marketing-engine/`，Python `http.server` / `ThreadingHTTPServer`，`server.py:Handler`；原生 `index.html/app.js/style.css`，无需新前端框架。
- 数据：`server.py:DB_PATH` 复用 `MMN_DB_PATH`，默认 `data/commercial_demo.db`。SQLite，既有 `init_db()` 使用新增表与索引迁移。主库只读 `PRAGMA quick_check=ok`。
- 权限：`Handler.require_cloud_auth()`、`current_auth()` 与 `request_org_id()`；本机免登录固定 local/admin，云端沿用签名会话与角色，Cookie 写请求沿用 CSRF 校验。GEO 禁止以客户端 org_id 建立权限。
- 车型：复用 tenant-scoped `vehicle_assets`（org_id / edition / brand_name / model_name / extra_json）；全局 `model_identity_assets` 可作为既有辅助资产，但不创建平行车型主库。GEO 只维护项目内别名与年款配置映射，并在批次冻结。
- 作业：现有公开证据、社媒任务使用持久 SQLite 状态与 thread/external worker 模式。GEO 采用同样进程模式和 DB_PATH，新增模块内可恢复租约与 attempt，不增微服务或队列产品。
- 前端：`showPage()`、`pageNames`、`.page.active` 与 `#nav button[data-page]`。现有一级入口保持顺序，仅按工单授权新增 GEO；驾驶舱增加小型摘要入口。
- 样式：复用 `--bg/--surface/--line/--text/--muted/--blue/--green/--red/--amber`、既有字体、按钮与面板。集成前截图 `output/geo-20261008/mmn-before.png`。
- 配置：2026-10-08 只检查变量是否非空：仓库 `.env` 与执行环境未发现 ARK_API_KEY、GEO_MODEL_ID、GEO_API_MODE 或 GEO 配额。未打印值；普通 API、助手 API、联网真实联调均 blocked。
- 当前工作树：`codex/social-evidence-v2`，既有大量未提交代码、数据、文档；保留全部原差异，只对服务器、导航、页面入口作小型增量接线。原 8765 为受管已安装运行包，开发测试采用独立端口与临时数据库，不把源码修改说成已部署。
- 知识图谱已索引，优先使用 search_graph/get_code_snippet/search_code；部分符号行号滞后于未提交代码，已在准确文件内读取当前片段校验，未依赖旧索引位置编辑。

## 工单映射

`geo/` 包承载数据、提供方、分析、指标、服务和 API；`geo/migrations/001_geo.sql` 新增隔离表；`scripts/run_geo_worker.py` 外部 worker；`geo.js/geo.css` 模块页；`tests/test_geo_*.py` 与前端合同测试。API 使用 `/api/geo`。逻辑 tenant_id 落地为既有 org_id，所有关联和读写含组织隔离。

## 外部契约依据

实施当天核查官方 Responses、联网工具和助手文档：助手使用 Responses 的 `doubao_app` 工具及测试 header，四个 feature 单次只启用一个，助手与 `web_search` 不混用；输出可能包含 `doubao_app_call.blocks`。`search_requested` 与实际事件分开，结构化引用与答案文本 URL 分开。

官方资料：
- https://docs.volcengine.com/docs/ark/create-model-responses-api?lang=en
- https://docs.volcengine.com/docs/ark/web-search?lang=en
- https://docs.volcengine.com/docs/ark/doubao-assistant?lang=zh

模型 ID、价格和账号权限仅由后端配置及真实联调确认。本轮不填写猜测模型、不调用网络采样、不将离线响应当成接入证据。
