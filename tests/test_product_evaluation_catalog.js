const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const start = app.indexOf("const productEvaluationCatalog=new Map();");
const end = app.indexOf("function unavailableProductEvaluationDataset", start);
assert.ok(start >= 0 && end > start, "product evaluation catalog helpers should be discoverable");
const catalogSource = app.slice(start, end);

function memoryStorage() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
  };
}

function dataset(model, version, rows = [[model, "本品", "全网", "智能化", "智能座舱"]]) {
  return {
    datasetVersion: version,
    config: {model},
    models: [model],
    rows,
    summaryHeat: {},
    summaryPlatformNsr: {},
    summaryMetrics: {},
    productEvaluationSourceModel: model,
  };
}

function catalogApi(localStorage, {org = "org-a", bundled = null} = {}) {
  const context = {
    localStorage,
    edition: "china",
    importedDataset: bundled,
    state: {config: {model: ""}},
    activeEdition() { return "china"; },
    browserStorageScope() { return {identityKey: `${org}::trial::china`}; },
    storageKey(base, edition) { return `${base}:${org}:${edition}`; },
    JSON,
    String,
    Boolean,
    Object,
    Array,
    Set,
    Map,
  };
  vm.runInNewContext(`${catalogSource}\nthis.catalogApi={prepareProductEvaluationCatalog,registerProductEvaluationDataset,productEvaluationCatalogGet,productEvaluationCatalogHas,loadPersistedProductEvaluationDatasets};`, context);
  return context.catalogApi;
}

const storage = memoryStorage();
const bundledL6 = dataset("智己L6", "xiaomi_su7_6cars_20260608_v1");
const first = catalogApi(storage, {bundled: bundledL6});
first.prepareProductEvaluationCatalog();
assert.equal(first.productEvaluationCatalogGet("智己L6").datasetVersion, bundledL6.datasetVersion, "bundled L6 data should always seed the catalog");
assert.equal(first.loadPersistedProductEvaluationDatasets().length, 0, "bundled data should not consume catalog storage");

const e7x = dataset("奥迪E7X", "product_evaluation_奥迪E7X_2026-04_2026-07-16");
assert.equal(first.registerProductEvaluationDataset(e7x), true);
assert.equal(first.loadPersistedProductEvaluationDatasets().length, 1, "registered product data should persist once");

const afterReload = catalogApi(storage, {bundled: bundledL6});
afterReload.prepareProductEvaluationCatalog();
assert.equal(afterReload.productEvaluationCatalogGet("智己L6").datasetVersion, bundledL6.datasetVersion, "reload should restore bundled L6 data");
assert.equal(afterReload.productEvaluationCatalogGet("奥迪E7X").datasetVersion, e7x.datasetVersion, "reload should restore registered E7X data");

const updatedL6 = dataset("智己L6", "customer_l6_v2", [["智己L6", "本品", "全网", "空间舒适", "空间"]]);
afterReload.registerProductEvaluationDataset(updatedL6);
assert.equal(afterReload.productEvaluationCatalogGet("智己L6").datasetVersion, "customer_l6_v2", "new same-vehicle data should replace the bundled baseline");
assert.equal(afterReload.loadPersistedProductEvaluationDatasets().filter(item => item.productEvaluationSourceModel === "智己L6").length, 1, "same-vehicle persistence should be deduplicated");

const otherOrg = catalogApi(storage, {org: "org-b", bundled: bundledL6});
otherOrg.prepareProductEvaluationCatalog();
assert.equal(otherOrg.productEvaluationCatalogHas("奥迪E7X"), false, "catalog data must not cross organization boundaries");
assert.equal(otherOrg.productEvaluationCatalogHas("智己L6"), true, "bundled data remains available in an isolated organization");

console.log("product evaluation catalog: ok");
