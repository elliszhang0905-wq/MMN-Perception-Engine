const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");

function sourceBetween(start, end) {
  const from = app.indexOf(start);
  const to = app.indexOf(end, from + start.length);
  assert.ok(from >= 0 && to > from, `${start} should be discoverable`);
  return app.slice(from, to);
}

const escapeHtmlSource = sourceBetween("function escapeHtml(", "function publicMmnProviderLabel(");
const escapeAttrSource = sourceBetween("function escapeAttr(", "function renderPeriodPicker(");
const renderDataBarsSource = sourceBetween("function renderDataBars(", "function emotionMeaning(");
const drillWordCloudSource = sourceBetween("function drillWordCloudHtml(", "function openDataDrill(");
const openDataDrillSource = sourceBetween("function openDataDrill(", "async function generateModelStrategy(");
const drillMiniBarsSource = sourceBetween("function drillMiniBars(", "const semanticLayerLabels=");
const drillKnowhowSource = sourceBetween("function drillKnowhowHtml(", "function drillWordCloudHtml(");

const attack = '<img src=x onerror="globalThis.__xss=1">';
const scriptAttack = "</span><script>globalThis.__xss=2</script>";

const bar = {innerHTML: ""};
const barContext = {
  publicMmnText: value => String(value ?? ""),
  document: {
    querySelector() { return bar; },
    querySelectorAll() { return []; },
  },
  Math,
};
vm.runInNewContext(
  `${escapeHtmlSource}\n${escapeAttrSource}\n${renderDataBarsSource}\nthis.renderDataBars=renderDataBars;`,
  barContext,
);
barContext.renderDataBars("#bars", [{key: attack, count: 1}], "count", "platform");
assert.doesNotMatch(bar.innerHTML, /<img/i);
assert.match(bar.innerHTML, /&lt;img/);

const helperContext = {
  publicMmnText: value => String(value ?? ""),
  wordCloudForRows() { return [{key: attack, count: 1}]; },
  topBreakdown() { return [{key: attack, count: 1}]; },
  score() { return {positive: 1, negative: 0}; },
  knowhowFor() {
    return {why: attack, message: scriptAttack, proof: attack, platform: scriptAttack, kpi: attack};
  },
  latestLearning() {
    return {evidence: attack, platform: scriptAttack, conclusion: attack, recommendation: scriptAttack};
  },
  similarLearnings() { return []; },
  ragSearch() {
    return [{title: attack, body: scriptAttack, reason: attack, score: 1}];
  },
  Math,
};
vm.runInNewContext(
  `${escapeHtmlSource}\n${drillWordCloudSource}\n${drillMiniBarsSource}\n${drillKnowhowSource}\nthis.api={drillWordCloudHtml,drillMiniBars,drillKnowhowHtml};`,
  helperContext,
);
for (const html of [
  helperContext.api.drillWordCloudHtml([]),
  helperContext.api.drillMiniBars([{key: attack, count: 1}]),
  helperContext.api.drillKnowhowHtml("platform", attack, []),
]) {
  assert.doesNotMatch(html, /<img/i);
  assert.doesNotMatch(html, /<script/i);
  assert.match(html, /&lt;/);
}

const body = {innerHTML: ""};
const title = {textContent: ""};
const dialog = {showModal() {}};
const drillContext = {
  publicMmnText: value => String(value ?? ""),
  rowsForDrill() {
    return [{r: [attack, "本品", scriptAttack, attack, scriptAttack, attack, "", "", 1]}];
  },
  drillPlan() {
    return {total: 1, scores: {p: 1, n: 0}, lines: [attack, scriptAttack]};
  },
  qwenContext() { return {}; },
  emotionMeaning() { return attack; },
  topBreakdown() { return []; },
  drillMiniBars() { return "<div>safe</div>"; },
  drillWordCloudHtml() { return "<div>safe</div>"; },
  drillKnowhowHtml() { return "<div>safe</div>"; },
  trafficType() { return scriptAttack; },
  generateModelStrategy() {},
  document: {
    querySelector(selector) {
      if (selector === "#data-drill-dialog") return dialog;
      if (selector === "#data-drill-body") return body;
      if (selector === "#data-drill-title") return title;
      return null;
    },
    querySelectorAll() { return []; },
  },
  Set,
  Math,
};
vm.runInNewContext(
  `${escapeHtmlSource}\n${openDataDrillSource}\nthis.openDataDrill=openDataDrill;`,
  drillContext,
);
drillContext.openDataDrill("platform", attack);
assert.doesNotMatch(body.innerHTML, /<img/i);
assert.doesNotMatch(body.innerHTML, /<script/i);
assert.match(body.innerHTML, /&lt;img/);
assert.equal(title.textContent.includes("<img"), true, "textContent may safely preserve the visible source value");

console.log("data drill xss boundary: ok");
