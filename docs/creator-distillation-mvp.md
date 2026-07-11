# MMN 达人账号蒸馏 MVP

## 定位与状态

达人账号蒸馏位于「资产沉淀 → 达人资产库」，产物供策略项目、内容策划和达人匹配复用。当前交付状态为：**功能开发完成，待生产数据验证**。在真实 TikHub Key、抖音/小红书各 10 个脱敏账号和每平台至少 3 个端到端任务验收完成前，不得标记“可部署”。

## 架构

- `DouyinAdapter` 与 `XiaohongshuAdapter` 分别负责链接、接口版本、请求和平台差异；endpoint 可由环境变量 JSON 覆盖。
- 上层 Canonical Asset Schema 使用 provenance 描述 `platform/source_endpoint/fetch_time/availability/confidence`。接口未返回必须写 `not_returned + null`，不能写 0。
- PostgreSQL 迁移覆盖 Creator、CreatorProfile、Video（兼容视频/图文笔记）、TranscriptSegment、Shot、OCRSegment、CommentInsight、ContentTag、Evidence、StyleProfile、ScriptTemplate、DistillationTask，并建立 GIN、时间、综合分和 pgvector HNSW 索引。
- Redis/Celery 队列名为 `creator-distillation`；前台只轮询任务状态，不执行媒体处理。
- 原始平台响应写入 `raw_api_responses`，用于接口版本变化后的回放排错。
- Langfuse 记录提示词版本、脱敏证据 ID、模型、耗时、成本、输出和人工修正；不上传完整评论个人信息。

## 配置

必需：`DATABASE_URL`、`POSTGRES_PASSWORD`、`REDIS_URL`、`TIKHUB_API_KEY`。平台版本使用 `TIKHUB_DOUYIN_VERSION`、`TIKHUB_XIAOHONGSHU_VERSION`；接口表使用 `TIKHUB_*_ENDPOINTS`。媒体处理使用 `MMN_MEDIA_ROOT`、`SENSEVOICE_MODEL_PATH`、`WHISPER_FALLBACK_ENABLED`。yt-dlp 仅在 `MMN_YTDLP_FALLBACK_ENABLED=true` 时作为故障兜底。Langfuse 使用 `LANGFUSE_PUBLIC_KEY/SECRET_KEY/HOST`。

## 部署

1. 安装 FFmpeg、SenseVoice 模型和 PaddleOCR 运行依赖。
2. 启动 pgvector PostgreSQL 和 Redis，执行 `migrations/creator_distillation/001_creator_assets.sql`。
3. 启动 `mmn-app` 与 `mmn-creator-worker`，检查 `/api/creator-distillation/health`。
4. worker 必须能写媒体目录和原始响应归档；平台 Key 只配置在后端。
5. 配置 Langfuse 后核对一次模型调用 trace 的输入证据、版本、耗时与输出。

## 用户测试路径

打开 MMN → 资产沉淀 → 达人资产库 → 达人蒸馏，粘贴抖音或小红书公开主页，选择 90/180/全量和样本数，发起任务。任务页检查阶段、进度、失败原因、降级原因、暂停/重试；完成后进入达人档案，查看 DNA、代表作、表现分布和证据；进入视频/笔记拆解查看字幕、镜头、OCR、评论和回跳证据；方法论库只显示带来源达人、作品和 evidence ID 的条目。

## 降级与边界

- 图文笔记不执行音频和镜头分析；保留标题、正文、图片组、OCR、评论与互动。
- 视频媒体地址不可用时保留元数据、正文、图片/OCR与评论，并显示降级原因；不生成虚假字幕或镜头。
- 429/5xx/超时按指数退避重试；认证错误不盲重试；接口版本错误可切换版本后重放原始响应。
- SenseVoice 低置信度片段才允许 Whisper 兜底；FFmpeg/PaddleOCR/PySceneDetect 缺失时任务显式降级。
- 商业合作、疑似投流、热点和异常数据参与降权，不能主导 DNA；默认综合分与题材覆盖共同选择 50 条，支持 20–100 条。
- DNA 至少需要 20 条有效样本；人工修正形成新版本，不覆盖旧版本。
- 原创生成不得逐句改写、复刻固定表达或模仿特定真人身份。

## 真实验收

将经授权的脱敏账号集复制为 `tests/fixtures/creator_acceptance_accounts.private.json`（不提交真实账号），运行：

`TIKHUB_API_KEY=... python3 scripts/run_creator_acceptance.py tests/fixtures/creator_acceptance_accounts.private.json`

报告必须补齐每平台 10 个账号、每平台 3 个端到端任务、故障注入、成功率、失败原因、缺失字段、平均耗时、单账号成本和人工介入点。当前仓库没有真实 Key 和账号集结果，因此无生产验收结论。

## 下一阶段（不在当前实现）

当资产规模和并发量有实际数据后，再评估分区表、冷热媒体存储、Qdrant 或 Temporal；当前阶段不引入。
