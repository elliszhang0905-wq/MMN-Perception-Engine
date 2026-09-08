# 品牌分层输出：离线评测边界

状态：评测工具已实现；真实 Gold 与负责人审批尚未提供。合成测试仅验证机制，不能代表业务准确率、恢复率或上线许可。

## 数据合同

输入 JSON 为最多 1000 条案例的数组，每条包含：

- `caseId`：唯一案例 ID。
- `sourceKind`：`synthetic` 或 `historical_redacted`；历史来源须由负责人核验，不能把合成记录重命名后计为历史。
- `snapshotId`：与 `packet.scope.snapshotId` 相同。
- `evidenceGroupId`、`declarationId`：负责人在独立清单冻结的稳定同源证据组及声明标识；改写、重新编号不能创建“新来源”。同组只能进入一个集合，同组同声明不能重复凑数。
- `split`：`development` 或 `holdout`；同一快照/完整证据组不能跨集合。
- `packet`：由 `build_layered_packet` 生成的冻结证据包，包含真实隔离范围、时间窗、来源与可定位原文。
- `reviews`：冻结的三路原始结构化输出，保留缺失、失败和反对意见；不重新请求模型。
- `targetClaimId`：本案例目标判断 ID，不以无关品牌内容代替目标。
- `gold`：负责人确认的 `expectedClass`（`publish/source_only/dispute/block`）、布尔 `recoverable`、布尔 `v3Blocked`。

工具重新执行当前纯策略验证与融合，不信任输入中的候选裁决。源于未保存三路原始输出的旧快照，不能伪造历史模型输出来凑满案例数。

## 审批合同

负责人在工具以外审核并冻结独立清单：`datasetHash`、`ruleVersion`、`approvedBy`、`approvedAt`、`thresholdsApproved=true`、与工具 `RUBRIC` 完全相同的 `rubric`，及每条案例的 `caseId/caseHash/sourceKind/sourceRecordId/evidenceGroupId/declarationId`。同一 sourceRecordId 不能归入不同证据组；同一源记录同一声明不能重复计数。一个真实来源可有多个不同声明，但须保持同源分组。哈希使用排序键、紧凑分隔符、UTF-8、非 ASCII 不转义的 JSON SHA-256。

`--trusted-approval-sha256` 必须通过独立可信渠道取得；它绑定已核验清单，不证明任意文件的作者身份。不得由模型、案例文件、公开 API 或自行生成的审批清单代填。工具不生成 Gold 或审批。

```bash
python3 scripts/eval_brand_review_v4.py /absolute/path/cases.json \
  --approval /absolute/path/owner-approved-registry.json \
  --trusted-approval-sha256 OWNER_SUPPLIED_PIN
```

没有审批也可运行机制回放，但结果为 `not_ready`，比例为空。退出码：0 为离线评测通过，1 为质量门禁失败，2 为材料未就绪。任何结果的 `releaseAuthorized` 均为 false。

## 门禁及输出

至少 60 条案例、30 条真实脱敏历史案例、四类各 10 条；开发集与保留集隔离。人工批准的原先被拦截且可恢复案例构成恢复率分母。总恢复率及保留集恢复率均须至少 80%；空分母不能通过。硬阻断命中率和引用完整性须为 100%；出现任何不该发布却发布的目标判断即失败。

输出包含总量、分母、逐案例命中/误拦截/误放行及分类原因、聚合计数、集合分项与数据哈希。误拦截定义为应发布目标未发布，不要求误拦截数为零：本工单已提出的门槛为总量/保留集恢复率至少 80%，该容忍口径也须负责人显式批准；不得隐藏误拦截，也不擅自把它改成 100% 准确率门槛。误放行定义为不应确定发布的目标被发布，必须为零。

模型调用为零，真实成本/时延为 null；该工具不证明真实模型效果、运行耗时或部署安全。发布仍需真实授权运行、独立审查、页面验收、版本一致性、数据零漂移与回滚证据。工具不能凭文本相似度识别所有同源记录，分组和来源归属的真实性须独立人工审核，哈希只能防止批准后被改动。

单元测试里的“历史来源”和“负责人审批”全部为明确标注的测试替身，不能导出后作为验收 Gold。
