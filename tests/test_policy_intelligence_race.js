const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const source = fs.readFileSync(path.resolve(__dirname, "..", "policy-intelligence.js"), "utf8");
const root = {
  innerHTML: "",
  querySelector: () => null,
  querySelectorAll: () => [],
};

function dashboard(model, region) {
  return {
    meta: { positioning: "test", asOf: "2026-07-18", dataBoundary: "test", causalBoundary: "test" },
    summary: { activePolicyCount: 0, scenarioConditionalBenefit: 0, purchaseScenario: "置换更新", nevCoverageRate: 0, pendingReviewCount: 0 },
    map: [],
    trend: [],
    vehicleImpact: { model, region, profile: {}, maxVerifiedBenefit: 0, maxConditionalBenefit: 0, policyEffects: [], scenarioLabel: "test", causalBoundary: "test" },
    opportunities: [],
    reviewQueue: [],
  };
}

function response(payload) {
  return { ok: true, json: async () => payload };
}

const context = {
  console,
  URLSearchParams,
  FormData: class {},
  document: { querySelector: selector => selector === "#policy-intelligence-root" ? root : null },
  window: {},
  activeEdition: () => "china",
  authHeaders: () => ({ "Content-Type": "application/json" }),
  fetch: async (url, options = {}) => {
    if (options.method === "POST") return new Promise(() => {});
    const parsed = new URL(url, "http://localhost");
    const model = parsed.searchParams.get("model") || parsed.searchParams.get("policy_model");
    const region = parsed.searchParams.get("region") || parsed.searchParams.get("policy_region");
    await new Promise(resolve => setTimeout(resolve, region === "上海" ? 30 : 1));
    if (parsed.pathname === "/api/group-dashboard-demo") {
      return response({ policyIntelligence: {
        models: [{ role: "own", model, vehicleImpact: dashboard(model, region).vehicleImpact }],
        ownModelOptions: [{ role: "own", model, price: 219800, energyType: "纯电动", bodyType: "轿车" }],
      } });
    }
    return response(dashboard(model, region));
  },
  setTimeout,
  clearTimeout,
};

vm.runInNewContext(source, context, { filename: "policy-intelligence.js" });

(async () => {
  const first = context.window.PolicyIntelligenceModule.load(true);
  const second = context.window.PolicyIntelligenceModule.select("尚界Z7", "广东");
  await Promise.all([first, second]);
  assert(root.innerHTML.includes("尚界Z7在广东"), "较慢的旧请求不得覆盖较新的车型与区域结果");
  console.log("policy intelligence request-race test passed");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
