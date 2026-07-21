const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const css = fs.readFileSync(path.join(__dirname, "..", "style.css"), "utf8");
const server = fs.readFileSync(path.join(__dirname, "..", "server.py"), "utf8");

assert.match(app, /function buildSellingPointEvidencePacket\(/);
assert.match(app, /\/api\/selling-point-advisory\/run/);
assert.match(app, /\/api\/selling-point-advisory\/latest/);
assert.match(app, /sellingPointEvidenceFingerprint/);
assert.match(app, /\/api\/selling-point-advisory\/manual-review/);
assert.match(app, /独立建议一/);
assert.match(app, /独立建议二/);
assert.match(app, /独立建议三/);
assert.match(app, /MMN综合判断/);
assert.match(app, /决策准备度/);
assert.match(app, /aria-live="polite"/);
assert.doesNotMatch(app, /初步营销匹配度/);
assert.doesNotMatch(app, /弱势卖点｜优先修复/);
assert.doesNotMatch(app, /周期数据35、NSR竞品35、战略卖点20、产品证据10/);
assert.match(css, /grid-template-columns:minmax\(0,3fr\) minmax\(360px,2fr\)/);
assert.match(css, /\.selling-point-decision-sidebar/);
assert.match(css, /@media\(max-width:760px\)[\s\S]*\.selling-point-decision-layout\{grid-template-columns:1fr\}/);
assert.match(server, /\/api\/selling-point-advisory\/run/);
assert.match(server, /\/api\/selling-point-advisory\/latest/);
assert.match(server, /\/api\/selling-point-advisory\/manual-review/);

console.log("selling point advisory UI contract passed");
