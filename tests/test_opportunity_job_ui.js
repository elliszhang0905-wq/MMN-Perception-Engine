const assert = require("node:assert/strict");
const {
  OPPORTUNITY_JOB_STAGES,
  compactOpportunityDocument,
  competitorProductView,
  opportunityJobView,
  opportunityResultView,
} = require("../opportunity-job-ui.js");

assert.deepEqual(
  OPPORTUNITY_JOB_STAGES.map(item => item.key),
  ["official_sources", "alignment", "primary_model", "review_model", "cross_validation", "saving"]
);

const running = opportunityJobView({
  status: "running",
  stage: "primary_model",
  progress: 52,
  message: "MMN旗舰模型 A 正在独立分析",
  elapsedSeconds: 18,
});
assert.equal(running.statusLabel, "双旗舰模型运行中");
assert.equal(running.buttonLabel, "运行中 52%");
assert.equal(running.activeStage, 2);
assert.match(running.detail, /旗舰模型 A/);
assert.match(running.elapsedLabel, /18 秒/);

const completed = opportunityJobView({status: "completed", stage: "completed", progress: 100});
assert.equal(completed.statusLabel, "双模型交叉验证完成");
assert.equal(completed.buttonLabel, "重新生成机会地图");

assert.deepEqual(
  opportunityResultView({status: "partial_completed", qa: {verifiedLabelCount: 2}}),
  {
    statusLabel: "已验证 2 个标签",
    detail: "已验证标签已更新能力地图，其余标签仍可继续人工确认。",
    className: "ok",
  },
);

assert.deepEqual(
  competitorProductView({
    model: "竞品A",
    status: "verified",
    finalUrl: "https://example.com/a",
    coreProductStrengths: [{label: "空间", claim: "轴距 3000mm", factStrength: 0.91}],
  }),
  {
    model: "竞品A",
    statusLabel: "官网已核验",
    className: "verified",
    sourceUrl: "https://example.com/a",
    coreProductStrengths: [{label: "空间", claim: "轴距 3000mm", factStrength: 0.91}],
    detail: "已从双模型共同引用的官网事实中提炼 1 个 NSR 属性产品力。",
  },
);

assert.deepEqual(
  competitorProductView({model: "竞品B", status: "manual_required", failureReason: "官网限制访问"}),
  {
    model: "竞品B",
    statusLabel: "待补官网证据",
    className: "manual",
    sourceUrl: "",
    coreProductStrengths: [],
    detail: "官网限制访问",
  },
);

const failed = opportunityJobView({status: "failed", stage: "failed", error: "网络连接中断"});
assert.equal(failed.statusLabel, "生成失败");
assert.match(failed.detail, /网络连接中断/);

assert.deepEqual(compactOpportunityDocument({
  documentId: "doc-1",
  filename: "产品白皮书.pdf",
  brand: "奥迪",
  model: "奥迪E7X",
  version: "V260410",
  facts: new Array(1424).fill({}),
  manualReviewItems: new Array(81).fill({}),
}), {
  documentId: "doc-1",
  filename: "产品白皮书.pdf",
  brand: "奥迪",
  model: "奥迪E7X",
  version: "V260410",
  factCount: 1424,
  manualReviewCount: 81,
});

console.log("opportunity job ui: ok");
