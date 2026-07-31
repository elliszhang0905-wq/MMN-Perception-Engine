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
assert(
  source.includes('authHeaders({ "Content-Type": "application/json" })'),
  "政策分析 POST 请求应明确声明 JSON 内容类型"
);
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
assert(source.includes('role: "own"'), "动态车型档案必须显式标记本品身份");
assert(source.includes('profile.role === "own"'), "本品选择器只能展示上汽集团重点监测车型");
assert(source.includes("syncProfiles(group?.policyIntelligence?.ownModelOptions || [])"), "独立政策页必须从销量预警权威车型目录同步本品，不得依赖手写名单");
assert(source.indexOf("jsonFetch(comparisonUrl(selection.model") < source.indexOf("jsonFetch(dashboardUrl(selection.model"), "政策页必须先核验销量预警车型并取得政策输入，再计算独立页面");
assert(source.includes('value !== undefined && value !== null && value !== ""'), "缺失的车型可选字段不得以undefined字符串传入政策接口");
assert(source.includes('if (!profile) throw new Error("所选车型缺少销量预警政策输入，暂不能测算。")'), "缺少权威车型输入时必须失败关闭，不能借用E7X默认值");
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
  assert(!source.includes(model), `客户界面不应暴露内部模型名称：${model}`);
}
assert(source.includes('select[name="region"]'), "切换区域后应自动触发区域政策和三模型策略刷新");
assert(source.includes('select[name="model"]'), "切换车型后应自动触发车型政策审核");
assert(source.includes('select[name="scenario"]'), "切换购车情景后应自动触发政策审核");
assert(source.includes("syncProfiles"), "车型档案必须从当前销量预警车型清单动态同步");
assert(!source.includes('profiles[model] || profiles["奥迪E7X"]'), "缺少车型档案时不得回退成其他车型");
assert(source.includes("strategyValidation"), "前端应展示后端三模型交叉验证状态");
assert(source.includes("persist: force"), "自动预览不得保存政策分析，只有人工重新运行才允许持久化");
assert(!source.includes("void startEvaluation();"), "打开政策看板不得自动写入分析记录");
assert(source.includes('["aligned", "manual_required"].includes(validation?.status)'), "只有一致或明确进入人工裁决的结果才能开放Policy Eval");
assert(source.includes("loadRequest"), "区域快速切换必须使用请求序号阻止旧响应覆盖新选择");
assert(source.includes("MMN交叉验证结论"), "区域策略结论必须使用中立的MMN输出措辞");
assert(source.includes("const profiles = {};"), "本品清单必须来自服务端当前监测车型，不得在前端固化");
assert(source.includes('model: ""'), "政策页首次进入时必须由当前企业空间自动选择可审核车型");
assert(!source.includes('model: "奥迪E7X"'), "政策页不得以历史车型作为全局默认值");
assert(source.includes("交叉复核暂未完成，可安全重试。"), "交叉复核服务异常时必须展示可执行的中文安全提示");
assert(!source.includes('state.model = button.dataset.policyModel'), "点击竞品气泡不得改变本品身份");
assert(source.includes("state.focusModel = button.dataset.policyModel"), "点击气泡只应切换对比焦点");
assert(source.includes('target.dataset.submitting === "true" || target.dataset.submitted === "true"'), "Policy Eval必须阻止请求中和已成功评分的重复提交");
assert(source.includes('button.textContent = "评分提交中…"'), "Policy Eval点击后必须立即提供提交中反馈");
assert(source.includes("评分已保存但未通过"), "未通过的Policy Eval必须明确说明保存结果与知识版本状态");
assert(source.includes("当前结果未进入可用知识版本"), "Policy Eval未通过时不得让用户误以为已发布结论");
assert(source.includes('"variant_required"'), "部分动力版本适用时必须进入车型版本待选择状态");
assert(source.includes("需选择具体动力版本"), "车型版本待选择状态必须提供明确中文提示");
assert(source.includes("unresolvedPolicyImpact"), "前端必须统一拦截档案缺失和动力版本未确定状态");
assert(source.includes('value !== null && value !== undefined && value !== ""'), "空权益值不得格式化成¥0");
assert(app.includes("async function ensureModelIdentities(models=[],{persistToServer=false}={})"), "车型标准化必须显式区分只读浏览与导入持久化");
assert(app.includes("ensureModelIdentities(state.models||[],{persistToServer:true})"), "数据导入后才允许把车型标准化结果写入服务端");

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
assert(groupSource.includes("/api/policy-intelligence/analyze"), "管理看板选择车型后必须自动发起政策交叉审核");
assert(groupSource.includes("persist:false"), "管理看板自动审核只能预览，不得写入分析记录");
assert(groupSource.includes("strategyValidation"), "管理看板结论卡必须消费交叉验证结果");
assert(groupSource.includes("MMN交叉验证结论"), "管理看板不得把规则草案冒充最终策略结论");
assert(groupSource.includes('uiState.policyModel=""'), "管理看板首次进入时必须由服务端选择当前可审核车型");

console.log("policy intelligence UI contract tests passed");
