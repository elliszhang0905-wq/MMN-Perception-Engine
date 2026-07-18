const assert = require("assert");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");

assert(html.includes('data-page="policyintelligence"'), "政策环境分析应进入现有决策驾驶舱导航");
assert(html.includes('id="policyintelligence"'), "应提供独立政策智能页面");
assert(html.includes('id="policy-intelligence-root"'), "页面应提供政策看板挂载点");
assert(html.includes("policy-intelligence.css"), "政策看板样式应独立，避免污染现有视觉令牌");
assert(html.includes("policy-intelligence.js"), "政策看板交互应独立加载");
assert(app.includes('policyintelligence:"政策环境分析"'), "页标题应注册政策环境分析");
assert(app.includes('id==="policyintelligence"'), "进入页面时应触发政策看板加载");

const policyJs = path.join(root, "policy-intelligence.js");
assert(fs.existsSync(policyJs), "应实现政策智能前端模块");
const source = fs.readFileSync(policyJs, "utf8");
for (const contract of [
  "/api/policy-intelligence/dashboard",
  "/api/policy-intelligence/analyze",
  "/api/policy-intelligence/review",
  "政策 → 购车门槛 → 车型竞争力 → 营销机会",
  "sourceQuote",
  "causalBoundary",
]) {
  assert(source.includes(contract), `政策看板缺少契约：${contract}`);
}
assert(!source.includes("政策新闻"), "政策智能模块不能退化为政策新闻列表");
assert(source.includes('role: "own"'), "本品候选必须在车型配置中显式标记为上汽集团车型");
assert(source.includes('profile.role === "own"'), "本品选择器只能展示上汽集团重点监测车型");
assert(source.includes("/api/group-dashboard-demo"), "车型对比必须请求销量预警细分市场的动态竞品池");
assert(source.includes("policy_model: model"), "动态竞品池必须随所选本品车型切换");
assert(source.includes("policy_scenario: scenario"), "动态竞品池必须使用请求快照中的购车情景重新测算");
assert(!source.includes('"蔚来ES6": { role: "competitor"'), "政策页不得保留写死的蔚来竞品");
assert(!source.includes('"理想L6": { role: "competitor"'), "政策页不得保留写死的理想竞品");
assert(source.includes("BaaS起售价"), "蔚来BaaS价格口径必须在对比卡片中可见");
assert(source.includes('if (!items.some(item => item.model !== state.model)) return ""'), "没有合格竞品时不得展示伪竞争图表");
assert(source.includes("当前购车方式权益上限"), "顶部权益指标必须随购车方式展示当前车型的条件权益上限");
assert(source.includes("scenarioConditionalBenefit"), "顶部权益指标必须绑定购车方式测算结果，不能继续展示全政策平均值");
assert(source.includes('const regions = ["北京", "天津", "上海", "重庆"'), "区域下拉应覆盖完整省级行政区，而不是仅保留七个重点区域");
for (const region of ["北京", "上海", "重庆", "广东", "内蒙古", "新疆"]) {
  assert(source.includes(`\"${region}\"`) || source.includes(`${region}:`), `区域选择器缺少：${region}`);
}
for (const model of ["Qwen 3.7 Max", "DeepSeek V4 Pro", "Kimi K2.5"]) {
  assert(source.includes(model), `三模型策略区缺少：${model}`);
}
assert(source.includes('select[name="region"]'), "切换区域后应自动触发区域政策和三模型策略刷新");
assert(source.includes("strategyValidation"), "前端应展示后端三模型交叉验证状态");
assert(source.includes('["aligned", "manual_required"].includes(validation?.status)'), "只有一致或明确进入人工裁决的结果才能开放Policy Eval");
assert(source.includes("loadRequest"), "区域快速切换必须使用请求序号阻止旧响应覆盖新选择");
assert(source.includes("MMN模型输出策略"), "区域策略结论必须使用MMN既定输出措辞");
assert(source.includes("engineDisplacementL: 1.5"), "燃油车型必须携带发动机排量，才能校验2.0L门槛");
for (const monitoredModel of ["奥迪E7X", "奥迪E5 Sportback", "智己LS8", "MG4", "荣威i6", "别克至境E7", "ID.ERA 9X", "尚界Z7"]) {
  assert(source.includes(`"${monitoredModel}"`), `政策模块本品列表缺少现有重点监测车型：${monitoredModel}`);
}
assert(!source.includes('state.model = button.dataset.policyModel'), "点击竞品气泡不得改变本品身份");
assert(source.includes("state.focusModel = button.dataset.policyModel"), "点击气泡只应切换对比焦点");

const groupSource = fs.readFileSync(path.join(root, "group-dashboard.js"), "utf8");
assert(groupSource.includes("policy.ownModelOptions"), "管理看板本品选择器必须来自销量预警监测车型清单");
assert(!groupSource.includes("uiState.policyModel=button.dataset.groupPolicyModelBubble"), "管理看板点击竞品不得切换本品");
assert(groupSource.includes("uiState.policyCompareModel=button.dataset.groupPolicyModelBubble"), "管理看板气泡点击只应切换对比焦点");
assert(groupSource.includes('item.role==="top3"'), "政策象限必须标识细分市场销量前三车型");
assert(groupSource.includes('item.role==="median"'), "政策象限必须标识靠近市场中位数车型");
assert(groupSource.includes("salesReference"), "政策象限必须展示销量预警等级和销量参照");
assert(groupSource.includes("policy_model=${encodeURIComponent(uiState.policyModel)}"), "切换本品后必须请求对应细分市场动态竞品池");
assert(groupSource.includes("data-group-policy-region"), "管理看板应提供省／直辖市选择器");
assert(groupSource.includes("policy_region=${encodeURIComponent(uiState.policyRegion)}"), "切换区域后应按省／直辖市重新请求政策测算");
assert(groupSource.includes("省／直辖市"), "区域口径不得继续写成城市");

console.log("policy intelligence UI contract tests passed");
