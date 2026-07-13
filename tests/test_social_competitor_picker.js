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

console.log("social competitor picker: ok");
