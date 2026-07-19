const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const ui = fs.readFileSync(path.join(root, "lead-dashboard.js"), "utf8");
const css = fs.readFileSync(path.join(root, "lead-dashboard.css"), "utf8");

assert.match(html, /id="management-dashboard-panel"[\s\S]*id="lead-dashboard-panel"[\s\S]*class="project-strip"/);
assert.match(ui, /"奥迪E7X"/);
assert.match(ui, /leadActual:183822[\s\S]*orderActual:9419/);
assert.match(ui, /leadActual:218414[\s\S]*orderActual:6375/);
assert.match(ui, /leadActual:169212[\s\S]*orderActual:1293/);
assert.match(ui, /leadActual:131838[\s\S]*orderActual:837/);
assert.match(ui, /summaryPhases=\[data\.phases\[0\],data\.phases\[1\],data\.phases\[data\.phases\.length-1\]\]/);
assert.match(ui, /线索超目标，订单未同步增长/);
assert.match(ui, /平台与内容归因待接入/);
assert.match(ui, /不把相关性直接写成内容因果/);
assert.match(ui, /现有T周期、正反向、NSR和策略模块统一读取同一车型上下文/);
assert.match(ui, /mmn:sales-warning-model-selected/);
assert.match(ui, /mmn:vehicle-context-updated/);
assert.match(ui, /已清空上一车型数据，避免跨车型误读/);
assert.doesNotMatch(ui, /<select/);
assert.match(css, /@media\(max-width:900px\)/);
assert.match(css, /\.lead-dashboard-summary,.lead-dashboard-phases,.lead-dashboard-diagnosis\{grid-template-columns:1fr\}/);

console.log("lead dashboard UI contract passed");
