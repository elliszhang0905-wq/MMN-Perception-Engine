const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const jsPath = path.join(root, "thailand-social-dashboard.js");
const cssPath = path.join(root, "thailand-social-dashboard.css");
const dataPath = path.join(root, "data", "thailand_social_market_latest.json");

assert.ok(fs.existsSync(jsPath), "Thailand social dashboard script must exist");
assert.ok(fs.existsSync(cssPath), "Thailand social dashboard stylesheet must exist");
assert.ok(fs.existsSync(dataPath), "Thailand social dashboard data contract must exist");

const js = fs.readFileSync(jsPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const server = fs.readFileSync(path.join(root, "server.py"), "utf8");
const deploy = fs.readFileSync(path.join(root, "scripts", "deploy.sh"), "utf8");
const nginx = fs.readFileSync(path.join(root, "deploy", "nginx.conf"), "utf8");

assert.equal(data.market.code, "TH");
assert.equal(data.primary_metric, "monthly_usage_penetration");
assert.equal(data.platforms.length, 10);
assert.ok(data.source_classes.length >= 5);
assert.ok(data.guardrails.some((item) => item.includes("不能相加")));
assert.deepEqual(new Set(data.platforms.map((item) => item.confidence)), new Set(["high", "medium", "medium_low"]));
data.platforms.forEach((item) => {
  assert.ok(item.monthly_usage_pct >= 0 && item.monthly_usage_pct <= 100);
  assert.ok(item.ad_reach_internet_pct === null || (item.ad_reach_internet_pct >= 0 && item.ad_reach_internet_pct <= 100));
  assert.ok(item.source_count >= 1);
});
assert.ok(data.platforms.some((item) => item.ad_reach_internet_pct === null));
assert.ok(data.source_classes.every((item) => /^https:\/\//.test(item.url)));

assert.match(html, /id="thailand-social-dashboard"[^>]+data-global-only/);
assert.match(html, /thailand-social-dashboard\.css/);
assert.match(html, /thailand-social-dashboard\.js/);
assert.match(server, /"thailand-social-dashboard\.css"/);
assert.match(server, /"thailand-social-dashboard\.js"/);
assert.match(server, /"data\/thailand_social_market_latest\.json"/);
assert.match(deploy, /compose cp data\/thailand_social_market_latest\.json mmn-app:\/app\/data\/thailand_social_market_latest\.json/);
assert.match(nginx, /location = \/data\/thailand_social_market_latest\.json/);
assert.match(nginx, /location ~\* \^\/\(\?:data\|backups\|logs/);
assert.match(js, /data\/thailand_social_market_latest\.json/);
assert.match(js, /泰国主流 Social Media 平台份额看板/);
assert.doesNotMatch(js, /泰国不是单平台市场/);
assert.doesNotMatch(js, /主排序使用同口径的月度用户渗透率/);
assert.doesNotMatch(js, /th-social-hero-seal/);
assert.match(js, /月度用户渗透率/);
assert.match(js, /广告可触达率/);
assert.match(js, /未公开/);
assert.match(js, /证据暂不可用/);
assert.match(js, /escapeHtml/);
assert.match(js, /data-th-social-metric/);
assert.match(js, /data-th-social-tier/);
assert.doesNotMatch(js, />\s*(GWI|Meta|Google|DataReportal|StatCounter|YouGov)\s*</i);
assert.match(css, /body\[data-edition="global"\][^{]*#thailand-social-dashboard/);
assert.match(css, /@media\s*\(max-width:\s*560px\)/);
assert.match(css, /prefers-reduced-motion/);

console.log("Thailand social core dashboard contract: ok");
