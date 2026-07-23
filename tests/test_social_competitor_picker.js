const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");

assert.match(html, /id="social-trend-competitor-brand"/);
assert.match(html, /id="social-trend-competitor-add"/);
assert.match(html, /竞品品牌/);
assert.match(html, /竞品车型/);

const sanitizerStart = app.indexOf("function socialVehicleIdentityKey(");
const sanitizerEnd = app.indexOf("function socialCompetitorCatalog", sanitizerStart);
assert.ok(sanitizerStart >= 0 && sanitizerEnd > sanitizerStart, "social competitor sanitizer should be discoverable");

const sanitizerContext = {};
vm.runInNewContext(
  `${app.slice(sanitizerStart, sanitizerEnd)}\nthis.sanitizerApi={sanitizeSocialCompetitors};`,
  sanitizerContext,
);
assert.deepEqual(
  JSON.parse(JSON.stringify(sanitizerContext.sanitizerApi.sanitizeSocialCompetitors(
    "奥迪 E7X",
    ["奥迪E7X", " 奔驰GLC EV ", "奔驰GLC  EV", "问界M7", "问界M7"],
  ))),
  ["奔驰GLC EV", "问界M7"],
  "competitors should exclude the own model and normalized duplicates",
);

const helperStart = app.indexOf("function socialCompetitorCatalog(");
const helperEnd = app.indexOf("function renderSocialCompetitorPicker", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "competitor catalog helper should be discoverable");

const context = {
  brandModelGroups(models) {
    return [
      {brand: "特斯拉", models: models.filter(model => model.startsWith("Model"))},
      {brand: "小米汽车", models: models.filter(model => model.startsWith("小米"))},
    ].filter(group => group.models.length);
  },
  modelNameUnderBrand(brand, model) {
    return brand === "小米汽车" ? model.replace(/^小米/, "") : model;
  },
};
vm.runInNewContext(
  `${app.slice(helperStart, helperEnd)}\nthis.catalogApi={socialCompetitorCatalog};`,
  context,
);

const groups = context.catalogApi.socialCompetitorCatalog(
  ["小米YU7", "Model Y", "Model 3", "小米SU7"],
  "小米SU7",
  ["Model 3"],
);
assert.deepEqual(
  JSON.parse(JSON.stringify(groups)),
  [
    {brand: "特斯拉", models: [{value: "Model Y", label: "Model Y"}]},
    {brand: "小米汽车", models: [{value: "小米YU7", label: "YU7"}]},
  ],
  "catalog should group the shared vehicle library by brand and exclude own or selected models",
);

assert.match(app, /brandSelect\.disabled=atLimit/);
assert.match(app, /modelSelect\.disabled=atLimit\|\|!activeBrand/);
assert.match(app, /socialTrendState\.competitors\.length<3/);
assert.match(app, /evidenceScope:"all"/);
assert.match(app, /evidencePool:"all"/);
assert.match(app, /socialTrendState\.evidenceScope="all"/);
assert.match(app, /socialTrendState\.evidencePool="all"/);
assert.match(app, /function loadLatestLegacySocialTrendSnapshot\(\)/);
assert.match(app, /function restoreSocialTrendScope\(result\)/);
assert.match(app, /function cancelSocialTrendRestore\(\)/);
assert.match(app, /event\.preventDefault\(\);cancelSocialTrendRestore\(\)/);
assert.match(app, /async function importSocialTrendFile\(file\)\{\n cancelSocialTrendRestore\(\)/);
assert.match(app, /result\?\.snapshot\?\.filters/);
assert.match(app, /socialTrendState\.competitors=restoredCompetitors/);
assert.match(app, /api\(`\/api\/social-trends\/latest\?\$\{query\.toString\(\)\}`\)/);
assert.match(app, /当前车型尚未形成可用快照/);
assert.match(app, /socialTrendState\.loading\|\|socialTrendState\.restoring/);
assert.match(app, /scopeButtons=\[\['all','全部车型'\],\['own','本品'\],\['competitor','竞品'\]\]/);
assert.match(app, /poolButtons=\[\['all','全部相关'\],\['hot','热门内容'\],\['risk','风险内容'\]\]/);
assert.match(app, /relatedEvidence=\(r\.comparisonItems\?\.length\?r\.comparisonItems/);
assert.match(app, /data-social-evidence-pool/);
assert.doesNotMatch(app, /\)\.slice\(0,30\),rankings=/, "all selected vehicle evidence should not be silently capped at 30 rows");
assert.match(app, /pages:0,count:20/, "social trend jobs should request exhaustion rather than a fixed two-page sample");
assert.match(app, /本品 × 竞品统一对比洞察/);
assert.match(app, /disagreement:"存在分歧"/);
assert.match(app, /查询状态/);
assert.match(app, /查询已完成/);
assert.match(app, /抓取候选/);
assert.match(app, /去重后/);
assert.match(app, /有效入池/);
assert.doesNotMatch(app, /已采尽/, "pagination exhaustion must not be presented as platform-wide collection completeness");
assert.match(app, /暂未发现；当前采集或风险分析不完整/);
assert.doesNotMatch(app, /<dt>置信度<\/dt>/, "opaque confidence must not remain in the comparison cards");

console.log("social competitor picker: ok");
