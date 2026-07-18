const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const banned = /TikHub|社媒助手|Qwen|DeepSeek|千问|Kimi|OpenAI|ChatGPT/i;
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const visibleHtmlText = html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]*>/g, " ");
const appLines = fs.readFileSync(path.join(root, "app.js"), "utf8").split("\n");

if (banned.test(visibleHtmlText)) {
  throw new Error("index.html 包含对外可见的供应商名称");
}

const internalAllowlist = [
  "analyzeCreatorWithQwen",
  ".replace(/Qwen|千问/",
  ".replace(/DeepSeek/",
  ".replace(/TikHub/",
  ".replace(/社媒助手/",
  ".replace(/Kimi/",
  ".replace(/OpenAI|ChatGPT/",
  "return({qwen:",
  'file.name.includes("社媒助手")',
  "aiStatus=",
  "modelIdentities",
  "qwen_checked",
  "function qwenContext",
  "qwenContext(",
  'id="qwen-',
  'querySelector("#qwen-',
  "const label={qwen:",
  "const endpoint={qwen:",
  "partLabels={qwen:",
  "requiredModels:",
  "if(p.qwen",
  "aiStatus?.",
  "Object.entries(result.parts)",
  "Object.entries(data.parts)",
];
const violations = appLines
  .map((line, index) => ({ line, number: index + 1 }))
  .filter(({ line }) => banned.test(line) && !internalAllowlist.some(token => line.includes(token)));

if (violations.length) {
  throw new Error(`app.js 包含疑似对外供应商名称：${violations.map(x => x.number).join(", ")}`);
}

console.log("public vendor-name guard: ok");
