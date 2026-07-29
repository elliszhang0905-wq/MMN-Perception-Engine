const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const script = fs.readFileSync(path.join(root, "douyin-vehicle-radar.js"), "utf8");
const styles = fs.readFileSync(path.join(root, "douyin-vehicle-radar.css"), "utf8");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");

assert.doesNotMatch(
  script,
  />数据联动</,
  "internal product-evaluation dataset versions must not be exposed in the customer UI",
);
assert.match(
  styles,
  /\.dvr-scope\{[^}]*grid-template-columns:minmax\(180px,.75fr\) minmax\(320px,1.5fr\)/,
  "radar scope should close to a two-column product and competitor layout",
);
assert.match(
  html,
  /douyin-vehicle-radar\.(?:css|js)\?v=beta-1\.03-20260729-full-deployment-closure-1/,
  "radar assets should use the cache-busting customer-UI revision",
);
assert.match(script, /待补热度/, "missing view metrics should be isolated from formal rankings");
assert.match(script, /未取得/, "missing play count must never be rendered as zero");
assert.doesNotMatch(script, /互动分/, "internal interaction score should not be customer-facing");
assert.match(styles, /\.dvr-tabs button\{[^}]*flex:0 0 auto[^}]*white-space:nowrap/, "mobile tabs should stay readable and scroll horizontally");

console.log("douyin vehicle radar ui: ok");
