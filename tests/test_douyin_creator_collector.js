const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "scripts", "douyin_creator_collector.js"), "utf8");

assert.match(source, /const ranges = \[\s*\{ key: "24h", label: "24小时" \}/, "采集应先切换到24小时，避免首轮重复选择当前7天");
assert.match(source, /\[aria-haspopup="true"\]\[data-popupid\]/, "时间选择器应按语义属性定位");
assert.match(source, /getByRole\("menuitem", \{ name: label, exact: true \}\)/, "下拉项应按菜单语义定位");
assert.match(source, /attempt < 3/, "下拉菜单异步渲染时应重试");
assert.match(source, /current\.label === label/, "当前已选周期应先切到备选周期再抓取");
assert.match(source, /const pivot = ranges\.find\(range => range\.label !== label\)/, "当前周期需要安全切换路径");

console.log("douyin creator collector selector guard: ok");
