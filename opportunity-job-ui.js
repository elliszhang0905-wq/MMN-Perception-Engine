(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) {
    root.OPPORTUNITY_JOB_STAGES = api.OPPORTUNITY_JOB_STAGES;
    root.compactOpportunityDocument = api.compactOpportunityDocument;
    root.competitorProductView = api.competitorProductView;
    root.opportunityJobView = api.opportunityJobView;
    root.opportunityResultView = api.opportunityResultView;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const OPPORTUNITY_JOB_STAGES = [
    {key: "official_sources", label: "官网事实核验"},
    {key: "alignment", label: "统一标签对齐"},
    {key: "primary_model", label: "旗舰模型 A"},
    {key: "review_model", label: "旗舰模型 B"},
    {key: "cross_validation", label: "交叉验证"},
    {key: "saving", label: "地图更新"},
  ];

  function elapsedLabel(seconds) {
    const value = Math.max(0, Number(seconds) || 0);
    if (value < 60) return `已运行 ${Math.round(value)} 秒`;
    const minutes = Math.floor(value / 60);
    const remainder = Math.round(value % 60);
    return `已运行 ${minutes} 分 ${String(remainder).padStart(2, "0")} 秒`;
  }

  function opportunityJobView(job) {
    const current = job || {};
    const status = current.status || "idle";
    const progress = Math.max(0, Math.min(100, Number(current.progress) || 0));
    const activeStage = OPPORTUNITY_JOB_STAGES.findIndex(item => item.key === current.stage);
    if (status === "failed") {
      return {
        statusLabel: "生成失败",
        buttonLabel: "重新生成机会地图",
        detail: current.error || current.message || "机会地图任务未完成，请重试",
        elapsedLabel: elapsedLabel(current.elapsedSeconds),
        activeStage: -1,
        progress,
      };
    }
    if (status === "completed") {
      return {
        statusLabel: "双模型交叉验证完成",
        buttonLabel: "重新生成机会地图",
        detail: current.message || "机会地图和证据链已更新",
        elapsedLabel: elapsedLabel(current.elapsedSeconds),
        activeStage: OPPORTUNITY_JOB_STAGES.length,
        progress: 100,
      };
    }
    if (status === "queued" || status === "running") {
      return {
        statusLabel: "双旗舰模型运行中",
        buttonLabel: `运行中 ${Math.round(progress)}%`,
        detail: current.message || "正在准备产品事实与市场数据",
        elapsedLabel: elapsedLabel(current.elapsedSeconds),
        activeStage,
        progress,
      };
    }
    return {
      statusLabel: "待运行",
      buttonLabel: "生成/更新机会地图",
      detail: "",
      elapsedLabel: "",
      activeStage: -1,
      progress: 0,
    };
  }

  function compactOpportunityDocument(document) {
    if (!document || !document.documentId) return null;
    return {
      documentId: document.documentId,
      filename: document.filename || "",
      brand: document.brand || "",
      model: document.model || "",
      version: document.version || "",
      factCount: document.factCount !== null && document.factCount !== undefined && document.factCount !== "" && Number.isFinite(Number(document.factCount)) ? Number(document.factCount) : (document.facts || []).length,
      manualReviewCount: document.manualReviewCount !== null && document.manualReviewCount !== undefined && document.manualReviewCount !== "" && Number.isFinite(Number(document.manualReviewCount)) ? Number(document.manualReviewCount) : (document.manualReviewItems || []).length,
    };
  }

  function opportunityResultView(result) {
    const current = result || {};
    const verifiedLabelCount = Math.max(0, Number(current.qa?.verifiedLabelCount) || 0);
    if (current.status === "completed") {
      return {
        statusLabel: "双模型交叉验证完成",
        detail: "产品事实、市场认知和传播热度已完成交叉验证。",
        className: "ok",
      };
    }
    if (current.status === "partial_completed") {
      return {
        statusLabel: `已验证 ${verifiedLabelCount} 个标签`,
        detail: "已验证标签已更新能力地图，其余标签仍可继续人工确认。",
        className: "ok",
      };
    }
    return {
      statusLabel: "需人工确认",
      detail: "冲突或证据不足的标签不会进入能力地图。",
      className: "warn",
    };
  }

  function competitorProductView(source) {
    const current = source || {};
    const verified = current.status === "verified";
    const coreProductStrengths = verified
      ? (current.coreProductStrengths || []).filter(item => item?.label && item?.claim)
      : [];
    return {
      model: String(current.model || "竞品"),
      statusLabel: verified ? "官网已核验" : "待补官网证据",
      className: verified ? "verified" : "manual",
      sourceUrl: String(current.finalUrl || current.url || ""),
      coreProductStrengths,
      detail: verified
        ? `已从双模型共同引用的官网事实中提炼 ${coreProductStrengths.length} 个 NSR 属性产品力。`
        : String(current.failureReason || "官网事实尚未达到外显标准。"),
    };
  }

  return {OPPORTUNITY_JOB_STAGES, compactOpportunityDocument, competitorProductView, opportunityJobView, opportunityResultView};
});
