const assert = require("node:assert/strict");
const { parseOpportunityCompetitorSources } = require("../opportunity-source-parser.js");

const pasted = [
  "小米YU7 https://www.xiaomiev.com/xiaomi/yu7",
  "特斯拉Model Y https://www.tesla.cn/modely",
  "奥迪Q6 e-tron|https://www.audi.cn/zh/models/q/q6/q6l_e-tron.html",
  "问界M7：https://www.vmall.com/product/cardetail/index.html?prdId=10086434576370",
].join("\n");

const parsed = parseOpportunityCompetitorSources(pasted);
assert.deepEqual(parsed.errors, []);
assert.deepEqual(parsed.items.map(item => item.model), ["小米YU7", "特斯拉Model Y", "奥迪Q6 e-tron", "问界M7"]);
assert.deepEqual(parsed.items.map(item => item.url), [
  "https://www.xiaomiev.com/xiaomi/yu7",
  "https://www.tesla.cn/modely",
  "https://www.audi.cn/zh/models/q/q6/q6l_e-tron.html",
  "https://www.vmall.com/product/cardetail/index.html?prdId=10086434576370",
]);

const invalid = parseOpportunityCompetitorSources("Model Y 官网首页");
assert.equal(invalid.items.length, 0);
assert.deepEqual(invalid.errors, [{ line: 1, text: "Model Y 官网首页", reason: "未识别到HTTP(S)官网地址" }]);

console.log("opportunity source parser: ok");
