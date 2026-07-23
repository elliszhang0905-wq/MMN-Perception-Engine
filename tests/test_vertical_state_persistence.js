const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const helperStart = app.indexOf("function emptyVerticalState()");
const helperEnd = app.indexOf("function loadStrategyKb()", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "vertical persistence helpers should be discoverable");
const helpers = app.slice(helperStart, helperEnd);

function memoryStorage(initial = {}, {failWrites = false} = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) {
      if (failWrites) throw new DOMException("quota exceeded", "QuotaExceededError");
      values.set(key, String(value));
    },
  };
}

function verticalApi(localStorage) {
  const context = {
    localStorage,
    storageKey() { return "mmnVerticalState:local:china"; },
    queueWorkspaceSnapshot() {},
    console: {warn() {}},
    JSON,
    Array,
    DOMException,
  };
  vm.runInNewContext(
    `let verticalLegacyCachePresent=false,verticalServerHydrated=false,verticalState;\n${helpers}\nverticalState=loadVerticalState();\nthis.verticalApi={getState:()=>verticalState,compactVerticalState,saveVerticalState,setHydrated:()=>{verticalServerHydrated=true;verticalLegacyCachePresent=false}};`,
    context,
  );
  return context.verticalApi;
}

const key = "mmnVerticalState:local:china";
const legacy = {
  sources: [{source: "legacy.xlsx"}],
  items: Array.from({length: 2500}, (_, index) => ({ownModel: "本品", competitor: `竞品${index}`})),
  assetSummary: {relationCount: 2500},
  selectedPlatform: "汽车之家",
  selectedModel: "本品",
  selectedCompetitor: "竞品1",
  selectedPeriod: "2026.07.16",
};
const storage = memoryStorage({[key]: JSON.stringify(legacy)});
const api = verticalApi(storage);

assert.equal(api.getState().items.length, 2500, "legacy rows remain available until the server confirms recovery");
assert.equal(api.saveVerticalState(), false, "legacy rows must not be discarded before server hydration");
assert.equal(JSON.parse(storage.getItem(key)).items.length, 2500);

api.setHydrated();
assert.equal(api.saveVerticalState(), true);
const compact = JSON.parse(storage.getItem(key));
assert.deepEqual(
  Object.keys(compact).sort(),
  ["schemaVersion", "selectedCompetitor", "selectedModel", "selectedPeriod", "selectedPlatform", "selectedSource"].sort(),
  "browser persistence must contain view preferences only",
);
assert.equal(compact.selectedModel, "本品");
assert.ok(storage.getItem(key).length < 500, "compact vertical state should remain far below browser quota");

const failingApi = verticalApi(memoryStorage({}, {failWrites: true}));
failingApi.setHydrated();
assert.equal(failingApi.saveVerticalState(), false, "preference quota failures should be non-fatal");

assert.match(app, /verticalState:compactVerticalState\(\)/, "project snapshots must not duplicate full vertical datasets");
assert.match(app, /function startAppDataLoads\(\)\{\s*restoreOpportunityContext\(\);\s*restoreVerticalAssetsFromServer\(\);/);
assert.match(app, /if\(!allItems\.length&&!verticalServerHydrated\)\{[\s\S]*?return;/, "empty pre-hydration renders must not erase saved selectors");
assert.match(app, /const restored=await restoreVerticalAssetsFromServer\(\{force:true,silent:true\}\)/);
assert.doesNotMatch(
  app,
  /#vertical-xlsx-file"\)\.onchange=[\s\S]*?saveVerticalState\(\);[\s\S]*?垂媒数据导入失败/,
  "a browser cache write must not turn a server-side import success into an import failure",
);

console.log("vertical state persistence: ok");
