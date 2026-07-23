const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const server = fs.readFileSync(path.join(__dirname, "..", "server.py"), "utf8");
const weeklyRadar = fs.readFileSync(path.join(__dirname, "..", "demo-brand-weekly-radar.html"), "utf8");

function sourceBetween(start, end) {
  const from = app.indexOf(start);
  const to = app.indexOf(end, from + start.length);
  assert.ok(from >= 0 && to > from, `${start} should be discoverable`);
  return app.slice(from, to);
}

const escapeHtmlSource = sourceBetween("function escapeHtml(", "function publicMmnProviderLabel(");
const renderBarsSource = sourceBetween("function renderVideoBars(", "function renderActions(");
const renderStrategyKbSource = sourceBetween("function renderStrategyKb(", "function renderKnowledgeMap(");
const attack = '<img src=x onerror="globalThis.__globalXss=1">';

const targets = new Map();
const document = {
  querySelector(selector) {
    if (!targets.has(selector)) {
      targets.set(selector, {innerHTML: "", textContent: ""});
    }
    return targets.get(selector);
  },
};
const context = {
  document,
  strategyKb: [{type: attack, body: attack, title: attack}],
  aggregateVideos() { return [{key: attack, count: 1}]; },
  renderKnowledgeMap() {},
  renderRagResults() {},
  Math,
};
vm.runInNewContext(
  `${escapeHtmlSource}\n${renderBarsSource}\n${renderStrategyKbSource}\nthis.api={renderVideoBars,renderStrategyKb};`,
  context,
);
context.api.renderVideoBars("#bars", [{key: attack, count: 1}]);
context.api.renderStrategyKb();
for (const selector of ["#bars", "#strategy-kb-summary"]) {
  assert.doesNotMatch(targets.get(selector).innerHTML, /<img/i, `${selector} must escape imported labels`);
  assert.match(targets.get(selector).innerHTML, /&lt;img/);
}

assert.match(
  server,
  /Content-Security-Policy/,
  "all responses should enforce a content security policy",
);
for (const directive of [
  "script-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "frame-src 'self'",
]) {
  assert.ok(server.includes(directive), `CSP must include ${directive}`);
}
assert.doesNotMatch(
  server,
  /script-src[^;]*'unsafe-inline'/,
  "inline script and event handlers must remain blocked",
);
const weeklyRadarScript = weeklyRadar.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(weeklyRadarScript, "weekly radar inline script should be discoverable");
const weeklyRadarHash = `sha256-${crypto.createHash("sha256").update(weeklyRadarScript).digest("base64")}`;
assert.ok(
  server.includes(weeklyRadarHash),
  "the reviewed weekly radar script hash must stay synchronized with the CSP",
);

console.log("global xss boundaries: ok");
