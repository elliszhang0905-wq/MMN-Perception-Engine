const fs=require("fs");
const assert=require("assert");

const html=fs.readFileSync("index.html","utf8");
const app=fs.readFileSync("app.js","utf8");
const css=fs.readFileSync("style.css","utf8");

const dashboardStart=html.indexOf('<section class="page active" id="dashboard">');
const dashboardEnd=html.indexOf('<section class="page" id="policyintelligence">');
const dashboard=html.slice(dashboardStart,dashboardEnd);
const exportIndex=dashboard.indexOf('id="strategy-report-export"');
const judgmentIndex=dashboard.indexOf('class="panel model-judgment-panel compact-judgment"');

assert(dashboardStart>=0&&dashboardEnd>dashboardStart,"决策驾驶舱必须存在");
assert(exportIndex>judgmentIndex,"导出按钮必须位于驾驶舱现有全部内容之后");
assert.strictEqual((html.match(/id="strategy-report-export-run"/g)||[]).length,1,"只能有一个资料包导出按钮");
assert(html.includes("导出策略汇报资料包"),"按钮文案必须准确");
assert(app.includes('api("/api/strategy-report-packages"'),"前端必须调用资料包接口");
assert(app.includes("buildStrategyReportExportInput"),"前端必须冻结当前作用域数据");
assert(app.includes("strategyReportProjectId"),"快照必须携带当前项目ID");
assert(app.includes("evidenceFingerprint.slice"),"界面必须显示可追溯证据指纹");
assert(css.includes(".strategy-report-export"),"导出状态区必须复用轻量页面样式");
assert(/@media \(max-width:860px\)[\s\S]*?\.strategy-report-export\{align-items:stretch;flex-direction:column\}/.test(css),"移动端必须堆叠避免溢出");

console.log("strategy report package UI contract passed");
