const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); },
    has(key) { return values.has(key); },
  };
}

const browserHelperStart = app.indexOf("function cachedBrowserSession()");
const browserHelperEnd = app.indexOf("let edition=", browserHelperStart);
const browserHelpers = app.slice(browserHelperStart, browserHelperEnd);
const helperStart = app.indexOf("function opportunityCacheContext()");
const helperEnd = app.indexOf("let opportunityEvidenceState=", helperStart);
assert.ok(browserHelperStart >= 0 && browserHelperEnd > browserHelperStart && helperStart >= 0 && helperEnd > helperStart, "browser and opportunity cache helpers should be discoverable");

const localStorage = memoryStorage({
  mmnCommercialSession: JSON.stringify({org_id: "org:a"}),
});
const context = {
  localStorage,
  state: {config: {model: "奥迪E7X"}},
  edition: "china",
  compactOpportunityDocument(document) { return document; },
  encodeURIComponent,
  JSON,
  String,
  Array,
};
vm.runInNewContext(
  `${browserHelpers}\n${app.slice(helperStart, helperEnd)}\nthis.cacheApi={opportunityCacheContext,opportunityDocumentStorageKey,loadOpportunityDocument,saveOpportunityDocument,loadOpportunityJobId,saveOpportunityJobId,loadOpportunitySourceText,saveOpportunitySourceText,loadCockpitDecisionCycleCache,saveCockpitDecisionCycleCache};`,
  context,
);

const cache = context.cacheApi;
assert.equal(cache.opportunityCacheContext().key, "org%3Aa:china:%E5%A5%A5%E8%BF%AAE7X");
cache.saveOpportunityDocument({documentId: "doc-e7x"});
cache.saveOpportunityJobId("job-e7x");
cache.saveOpportunitySourceText("Model Y https://example.com/model-y");
cache.saveCockpitDecisionCycleCache([{id: "cycle-e7x"}]);

context.state.config.model = "Model Y";
assert.equal(cache.loadOpportunityDocument(), null, "a different model must not see the previous document");
assert.equal(cache.loadOpportunityJobId(), "", "a different model must not resume the previous job");
assert.equal(cache.loadOpportunitySourceText(), "", "a different model must not reuse competitor links");
assert.deepEqual(Array.from(cache.loadCockpitDecisionCycleCache()), [], "a different model must not reuse execution cycles");

context.state.config.model = "奥迪E7X";
assert.equal(cache.loadOpportunityDocument().documentId, "doc-e7x");
assert.equal(cache.loadOpportunityJobId(), "job-e7x");
assert.equal(cache.loadCockpitDecisionCycleCache()[0].id, "cycle-e7x");

localStorage.setItem("mmnCommercialSession", JSON.stringify({org_id: "org-b"}));
assert.equal(cache.loadOpportunityDocument(), null, "a different organization must not see the previous document");
assert.equal(cache.loadOpportunityJobId(), "", "a different organization must not resume the previous job");

const localLegacyStorage = memoryStorage({
  "mmnOpportunityDocument:china": JSON.stringify({documentId: "legacy-local"}),
});
const localContext = {
  localStorage: localLegacyStorage,
  state: {config: {model: "奥迪E7X"}},
  edition: "china",
  compactOpportunityDocument(document) { return document; },
  encodeURIComponent,
  JSON,
  String,
  Array,
};
vm.runInNewContext(
  `${browserHelpers}\n${app.slice(helperStart, helperEnd)}\nthis.cacheApi={loadOpportunityDocument,opportunityDocumentStorageKey};`,
  localContext,
);
assert.equal(localContext.cacheApi.loadOpportunityDocument().documentId, "legacy-local");
assert.equal(localLegacyStorage.has("mmnOpportunityDocument:china"), false, "local legacy cache should migrate once");
assert.equal(localLegacyStorage.has(localContext.cacheApi.opportunityDocumentStorageKey()), true);

const storageHelperStart = app.indexOf("function activeEdition()");
const storageHelperEnd = app.indexOf("function importedModelsFromSourceNote", storageHelperStart);
assert.ok(storageHelperStart >= 0 && storageHelperEnd > storageHelperStart, "global storage helpers should be discoverable");
const storageHelpers = `${browserHelpers}\n${app.slice(storageHelperStart, storageHelperEnd)}`;
function globalStorageApi(localStorage, edition = "china") {
  const storageContext = {localStorage, edition, encodeURIComponent, JSON, String, Set};
  vm.runInNewContext(`${storageHelpers}\nthis.storageApi={storageKey,browserStorageScope};`, storageContext);
  return storageContext.storageApi;
}

const adminE7x = JSON.stringify({config: {model: "奥迪E7X"}, rows: [["奥迪E7X"]]});
const adminStorage = memoryStorage({
  mmnCommercialSession: JSON.stringify({org_id: "org-admin", org: "MMN管理空间", role: "admin"}),
  "mmnEngineState:china": adminE7x,
});
const adminStorageApi = globalStorageApi(adminStorage);
const adminStateKey = adminStorageApi.storageKey("mmnEngineState", "china");
assert.equal(adminStateKey, "mmnEngineState:org-admin:china");
assert.equal(JSON.parse(adminStorage.getItem(adminStateKey)).config.model, "奥迪E7X", "admin must retain the existing E7X state");
assert.equal(adminStorage.has("mmnEngineState:china"), false, "authenticated admin migration should consume the legacy key once");

const trialStorage = memoryStorage({
  mmnCommercialSession: JSON.stringify({org_id: "org-trial", org: "MMN试用空间", role: "trial"}),
  "mmnEngineState:china": adminE7x,
});
const trialStorageApi = globalStorageApi(trialStorage);
const trialStateKey = trialStorageApi.storageKey("mmnEngineState", "china");
assert.equal(trialStateKey, "mmnEngineState:org-trial:china");
assert.equal(trialStorage.getItem(trialStateKey), null, "trial must never inherit an unscoped customer state");
assert.equal(trialStorage.has("mmnEngineState:china"), true, "trial access must not consume the admin legacy state");

const twoOrgStorage = memoryStorage({mmnCommercialSession: JSON.stringify({org_id: "org-a", role: "trial"})});
const twoOrgApi = globalStorageApi(twoOrgStorage);
const orgAKey = twoOrgApi.storageKey("mmnVideoState", "china");
twoOrgStorage.setItem(orgAKey, JSON.stringify({owner: "org-a"}));
twoOrgStorage.setItem("mmnCommercialSession", JSON.stringify({org_id: "org-b", role: "trial"}));
const orgBKey = twoOrgApi.storageKey("mmnVideoState", "china");
assert.notEqual(orgAKey, orgBKey);
assert.equal(twoOrgStorage.getItem(orgBKey), null, "a second organization must not read the first organization's domain cache");

assert.match(app, /function startAppDataLoads\(\)\{\s*restoreOpportunityContext\(\)/);
assert.match(app, /function storageKey\([\s\S]*?scope\.canMigrateLegacy/);
assert.match(app, /function saveSession\([\s\S]*?loadEditionData\(\{syncServer:false\}\)[\s\S]*?resetBrowserScopeTransientState\(\)/);
assert.match(app, /function setEdition\([\s\S]*?verticalAssetRestoreTried=false;[\s\S]*?resetOpportunityContextState\(\);[\s\S]*?restoreOpportunityContext\(\)/);
assert.match(app, /function applyModelSelection\([\s\S]*?resetOpportunityContextState\(\);\s*restoreOpportunityContext\(\)/);
assert.match(app, /contextKey!==opportunityCacheContext\(\)\.key/);
assert.match(app, /saveCockpitDecisionCycleCache\(data\.cycles\|\|\[\],contextKey\)/);
assert.doesNotMatch(app, /opportunityJobResumeStarted/);

assert.match(app, /function socialMetric\(value\)\{const number=nullableNumber\(value\);return number===null\?"—"/);
assert.doesNotMatch(app, /function socialMetric\(value\)\{return Number\(value\|\|0\)/);
assert.doesNotMatch(app, /\}pt(?:；|，|。|<|`)/);
assert.doesNotMatch(app, /\}pp(?:；|，|。|<|`)/);
assert.doesNotMatch(app, /Number\.isFinite\(Number\(item\.(?:factStrength|recognition|opportunityScore)\)\)/);

console.log("frontend lifecycle scope: ok");
