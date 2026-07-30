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
  /douyin-vehicle-radar\.(?:css|js)\?v=beta-1\.03-20260730-douyin-video-evidence-chain-1/,
  "radar assets should use the cache-busting customer-UI revision",
);
assert.match(script, /待补热度/, "missing view metrics should be isolated from formal rankings");
assert.match(script, /未取得/, "missing play count must never be rendered as zero");
assert.doesNotMatch(script, /互动分/, "internal interaction score should not be customer-facing");
assert.match(styles, /\.dvr-tabs button\{[^}]*flex:0 0 auto[^}]*white-space:nowrap/, "mobile tabs should stay readable and scroll horizontally");
assert.match(
  html,
  /id="dashboard-competitor-intelligence"[\s\S]*id="dashboard-douyin-vehicle-radar"[\s\S]*id="selling-point-decision-workbench"/,
  "vehicle heat evidence must sit inside competitor cognition before selling-point decisions",
);
assert.match(script, /data-dvr-model/, "single-model ranking should expose a vehicle-name input");
assert.match(script, /data-dvr-topn/, "single-model ranking should expose a Top N control");
assert.match(script, /查看完整榜单/, "cockpit should keep a compact Top 5 summary with an explicit full-list action");
assert.match(script, /collection\?\.stopReason|collection\.stopReason/, "coverage stop reason must be rendered");
assert.match(script, /视频内容未读取完整/, "limited evidence must not look like a generic model failure");
assert.match(script, /三路分析尚未启动/, "the UI must distinguish evidence acquisition from model analysis");
assert.match(script, /补取视频证据并分析/, "limited evidence must expose the correct recovery action");
assert.match(script, /data-dvr-retry-slot/, "an incomplete review must expose the failed slot only");
assert.match(script, /retrySlot/, "the radar retry request must preserve successful review runs");
assert.match(styles, /\.dvr-insight small\{[^}]*display:block/, "evidence limitations must remain readable");
assert.doesNotMatch(
  script,
  /visibleItems\.map\(resultRow\)|items\.map\(resultRow\)/,
  "Array.map's third argument must not be mistaken for the pending-review flag",
);

console.log("douyin vehicle radar ui: ok");
