const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const ui = fs.readFileSync(path.join(root, "lead-dashboard.js"), "utf8");
const css = fs.readFileSync(path.join(root, "lead-dashboard.css"), "utf8");

assert.match(html, /id="management-dashboard-panel"[\s\S]*id="lead-dashboard-panel"[\s\S]*class="project-strip"/);
assert.match(ui, /"奥迪E7X"/);
assert.match(ui, /registerModelData/);
assert.match(ui, /normalizeModelData/);
assert.match(ui, /status:"in_progress"/);
assert.match(ui, /phase\.status==="in_progress"/);
assert.doesNotMatch(ui, /item\.name\.includes\("6\.16"\)/);
assert.match(ui, /leadActual:183822[\s\S]*orderActual:9419/);
assert.match(ui, /leadActual:218414[\s\S]*orderActual:6375/);
assert.match(ui, /leadActual:169212[\s\S]*orderActual:1293/);
assert.match(ui, /leadActual:131838[\s\S]*orderActual:837/);
assert.match(ui, /lead-dashboard-overview/);
assert.match(ui, /lead-stage-chart/);
assert.match(ui, /线索与订单阶段达成/);
assert.match(ui, /目标 100%/);
assert.match(ui, /isCurrent\?" current":""/);
assert.match(ui, /当前阶段进度/);
assert.match(ui, /当前周期进行中，不按完整周期直接判定/);
assert.match(ui, /车型总体线索｜暂未分平台/);
assert.match(ui, /不能认定为真实转化率下降/);
assert.match(ui, /Math\.min\(Number\(value\|\|0\),1\.5\)/);
assert.match(ui, /线索超目标，订单未同步增长/);
assert.match(ui, /细分市场容量/);
assert.match(ui, /细分市场销量分析/);
assert.match(ui, /声量分析/);
assert.match(ui, /线索分析/);
assert.match(ui, /订单达成率/);
assert.match(ui, /当前主要断点：线索 → 订单/);
assert.match(ui, /三路独立复核 · 同一证据包/);
assert.match(ui, /三旗舰一致也不构成因果证据/);
assert.match(ui, /\/api\/attribution-reasoning\?model=/);
assert.match(ui, /\/api\/attribution-reasoning\/run/);
assert.match(ui, /typeof authHeaders==="function"\?authHeaders\(\):\{\}/);
assert.match(ui, /if\(!window\.mmnAuthReady\)return/);
assert.match(ui, /mmn:auth-ready/);
assert.match(ui, /mmn:auth-ready"[\s\S]*loadModelData\(activeModel,true\)/);
assert.match(ui, /开始三路复核/);
assert.match(ui, /三路独立复核已完成 · 裁决一致/);
assert.match(ui, /存在分歧或未全部完成，本轮不发布模型最终结论/);
assert.match(ui, /aria-expanded="\$\{attributionBubbleOpen\}"/);
assert.match(ui, /setAttributionBubble/);
assert.match(ui, /event\.key==="Escape"/);
assert.match(ui, /loadGroupDashboardDemo/);
assert.match(ui, /现有T周期、正反向、NSR和策略模块统一读取同一车型上下文/);
assert.match(ui, /mmn:sales-warning-model-selected/);
assert.match(ui, /mmn:vehicle-context-updated/);
assert.match(ui, /已清空上一车型数据，避免跨车型误读/);
assert.match(ui, /clearImportMessage/);
assert.doesNotMatch(ui, /<select/);
assert.match(css, /@media\(max-width:900px\)/);
assert.match(css, /\.lead-dashboard-overview\{grid-template-columns:1fr\}/);
assert.match(css, /\.lead-chart-plot\{grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
assert.match(css, /\.lead-stage-group\.current/);
assert.match(css, /--lead-rate/);
assert.match(css, /\.lead-attribution-trigger/);
assert.match(css, /\.lead-attribution-bubble\[hidden\]\{display:none\}/);
assert.match(css, /\.lead-attribution-run/);
assert.match(css, /\.lead-provider-grid/);
assert.match(css, /\.lead-reasoning-chain\{grid-template-columns:1fr\}/);

const dashboardRoot = {
  innerHTML: "",
  addEventListener() {},
  querySelector() { return null; },
};
const documentStub = {
  querySelector(selector) {
    return selector === "#lead-dashboard-root" ? dashboardRoot : null;
  },
  addEventListener() {},
};
const windowStub = {
  MMNVehicleContext: { getModel: () => "" },
  addEventListener() {},
};
const context = vm.createContext({
  window: windowStub,
  document: documentStub,
  console,
  fetch: async () => ({ ok: true, json: async () => ({ ok: true, run: null }) }),
  setTimeout,
  clearTimeout,
});
vm.runInContext(ui, context, { filename: "lead-dashboard.js" });

const secondModel = windowStub.MMNLeadDashboard.registerModelData("测试车型A", {
  source: { label: "测试车型A线索表", scope: "阶段目标、实际线索与实际订单" },
  warning: { level: "green", label: "正常", sales: 1200, cycle: "销售转化期" },
  phases: [
    { name: "预售", leadTarget: 1000, leadActual: 900, orderTarget: 100, orderActual: 92, status: "completed" },
    { name: "上市首月", leadTarget: 2000, leadActual: 2300, orderTarget: 200, orderActual: 110, status: "completed" },
    { name: "平销首月", leadTarget: 3000, leadActual: 600, orderTarget: 300, orderActual: 45, status: "in_progress" },
  ],
});
assert.equal(secondModel.ok, true);
windowStub.MMNLeadDashboard.renderModel("测试车型A");
assert.match(dashboardRoot.innerHTML, /测试车型A 线索表现/);
assert.match(dashboardRoot.innerHTML, /测试车型A线索表/);
assert.match(dashboardRoot.innerHTML, /上市首月线索达成115\.0%，订单仅55\.0%/);
assert.match(dashboardRoot.innerHTML, /平销首月/);
assert.match(dashboardRoot.innerHTML, /进行中/);
assert.doesNotMatch(dashboardRoot.innerHTML, /奥迪E7X|169,212|117\.7%/);

const invalidModel = windowStub.MMNLeadDashboard.registerModelData("坏数据车型", {
  source: { label: "错误数据", scope: "测试" },
  phases: [{ name: "阶段一", leadTarget: 0, leadActual: 10, orderTarget: 10, orderActual: 2 }],
});
assert.equal(invalidModel.ok, false);
const invalidStatusModel = windowStub.MMNLeadDashboard.registerModelData("状态错误车型", {
  source: { label: "错误状态数据", scope: "测试" },
  phases: [{ name: "阶段一", leadTarget: 10, leadActual: 10, orderTarget: 10, orderActual: 2, status: "未知" }],
});
assert.equal(invalidStatusModel.ok, false);
windowStub.MMNLeadDashboard.renderModel("坏数据车型");
assert.match(dashboardRoot.innerHTML, /坏数据车型线索数据待接入/);
assert.doesNotMatch(dashboardRoot.innerHTML, /测试车型A线索表/);

console.log("lead dashboard UI contract passed");
