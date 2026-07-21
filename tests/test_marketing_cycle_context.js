const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const MmnTCycle = require("../t-cycle.js");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const start = app.indexOf("function localIsoDate()");
const end = app.indexOf("function tCycleTopicStage", start);
assert.ok(start >= 0 && end > start);

function memoryStorage() {
  const values = new Map();
  return {getItem: (key) => values.get(key) ?? null, setItem: (key, value) => values.set(key, String(value))};
}
const localStorage = memoryStorage();
const context = {
  state: {config: {model: "MG4"}},
  localStorage,
  MmnTCycle,
  document: {querySelector: () => null},
  opportunityCacheContext: () => ({orgId: "org-a", edition: "china"}),
  opportunityStorageValue: (_base, key) => localStorage.getItem(`mmnMarketingModelContext:${key}`),
  opportunityScopedStorageKey: (_base, key) => `mmnMarketingModelContext:${key}`,
  encodeURIComponent, JSON, String, Array, Date, Number,
};
vm.runInNewContext(`${app.slice(start, end)}\nthis.api={rawMarketingModelContext,loadMarketingModelContext,saveMarketingModelContext,syncMarketingModelCycleContext,marketingModelPhase};`, context);

const api = context.api;
api.saveMarketingModelContext({firstDate: "2026-04-01", t0Date: "2026-04-02", assessmentDate: "2026-07-17", selectedPhase: "auto", claims: [{id: "claim-mg4"}], competitors: {空间: "车型A"}, productEvidence: {verified: true}}, "MG4");
api.syncMarketingModelCycleContext({model: "MG4", seriesId: "5828", launchDate: "2026-04-24", assessmentDate: "2026-07-17", tLabel: "T+84", phaseKey: "conversion", phaseLabel: "销售转化期", phaseRange: "T+31～T+90", source: "sales-warning-server", status: "verified"}, "MG4");
const mg4 = api.loadMarketingModelContext("MG4");
assert.equal(mg4.t0Date, "2026-04-24");
assert.equal(mg4.assessmentDate, "2026-07-17");
assert.equal(mg4.claims[0].id, "claim-mg4");
assert.equal(mg4.competitors.空间, "车型A");
assert.equal(mg4.productEvidence.verified, true);

api.saveMarketingModelContext({...mg4, t0Date: "2099-01-01", claims: [{id: "claim-updated"}]}, "MG4");
assert.equal(api.loadMarketingModelContext("MG4").t0Date, "2026-04-24", "ordinary save must not overwrite the authoritative T0");
assert.equal(api.loadMarketingModelContext("MG4").claims[0].id, "claim-updated", "non-cycle context remains editable");

api.syncMarketingModelCycleContext({model: "奥迪E7X", seriesId: "25846", launchDate: "2026-05-29", assessmentDate: "2026-07-17", tLabel: "T+49", phaseKey: "conversion", phaseLabel: "销售转化期", phaseRange: "T+31～T+90", source: "sales-warning-server", status: "verified"}, "奥迪E7X");
assert.equal(api.loadMarketingModelContext("奥迪E7X").t0Date, "2026-05-29");
assert.equal(api.loadMarketingModelContext("MG4").t0Date, "2026-04-24", "rapid switching must keep model-scoped dates separate");

console.log("marketing cycle context: ok");
