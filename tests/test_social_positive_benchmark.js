const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const helperStart = app.indexOf("function socialPositiveHeat(");
const helperEnd = app.indexOf("function renderSocialTrends", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "positive heat helper should be discoverable");

const context = {};
vm.runInNewContext(
  `${app.slice(helperStart, helperEnd)}\nthis.positiveHeatApi={socialPositiveHeat};`,
  context,
);

assert.equal(
  context.positiveHeatApi.socialPositiveHeat([
    {sentiment: "positive", heat: 42.25},
    {sentiment: "negative", heat: 99},
    {sentiment: "positive", heat: "15.5"},
  ]),
  57.75,
  "own-model benchmark must use the same positive-content heat sum as competitors",
);
assert.equal(context.positiveHeatApi.socialPositiveHeat([]), 0);

assert.match(app, /class="social-own-benchmark"/);
assert.match(app, /本品基准/);
assert.match(app, /socialPositiveHeat\(items\)/);
assert.match(app, /Math\.max\(1,ownPositiveHeat,/);

console.log("social positive benchmark: ok");
