const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");

assert.match(app, /classList\.add\("social-risk-trigger"\)/);
assert.match(app, /setAttribute\("aria-expanded","false"\)/);
assert.match(app, /class="social-risk-popover"/);
assert.match(app, /data-social-risk-close/);
assert.match(app, /items\.filter\(x=>x\.sentiment==="negative"\)/);
assert.match(app, /查看原文 ↗/);
assert.match(app, /bindSocialRiskPopover\(\)/);

console.log("social risk popover: ok");
