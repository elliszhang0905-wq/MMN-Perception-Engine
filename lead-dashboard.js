(function(){
 const root=document.querySelector("#lead-dashboard-root");
 if(!root)return;

 const leadData={
  "奥迪E7X":{
   source:{label:"E7X上市流量表现指标统计表",scope:"阶段目标、实际线索与实际订单",asOf:"表内当前填报周期"},
   warning:{level:"yellow",label:"黄色观察",sales:4017,performanceRate:.265,cycle:"销售转化期"},
   phases:[
    {name:"小订阶段",leadTarget:225000,leadActual:183822,leadRate:.817,orderTarget:10000,orderActual:9419,orderRate:.942},
    {name:"大定阶段",leadTarget:230208,leadActual:218414,leadRate:.949,orderTarget:6000,orderActual:6375,orderRate:1.062},
    {name:"平销 6.16—6.30",leadTarget:143758,leadActual:169212,leadRate:1.177,orderTarget:2000,orderActual:1293,orderRate:.646},
    {name:"平销 7.1—7.31 · 进行中",leadTarget:457143,leadActual:131838,leadRate:.288,orderTarget:4000,orderActual:837,orderRate:.209}
   ]
  }
 };
 const esc=value=>String(value??"").replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
 const number=value=>Number(value||0).toLocaleString("zh-CN");
 const percent=value=>`${(Number(value||0)*100).toFixed(1)}%`;
 const rateClass=value=>Number(value)>=.9?"good":Number(value)>=.7?"watch":"risk";
 let activeModel=window.MMNVehicleContext?.getModel?.()||"";
 let warningContext=null;

 function renderEmpty(model){
  const name=model||"当前车型";
  root.innerHTML=`<section class="lead-dashboard-card empty" aria-labelledby="lead-dashboard-title"><header><div><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(name)} 线索表现</h2><p>车型由上方销量预警统一选择，本看板不设置第二个车型选择器。</p></div><em>数据待接入</em></header><div class="lead-dashboard-empty" role="status"><b>${esc(name)}线索数据待接入</b><p>已清空上一车型数据，避免跨车型误读。接入阶段目标、实际线索与实际订单后自动生成看板。</p></div><footer><span>当前车型上下文：${esc(name)}</span><small>未取得平台来源、内容ID与内容标签时，不生成内容归因结论。</small></footer></section>`;
 }

 function render(){
  const data=leadData[activeModel];
  if(!data){renderEmpty(activeModel);return}
  const warning={...data.warning,...(warningContext?.model===activeModel?warningContext:{})};
  const phases=data.phases.map(phase=>`<article class="lead-phase"><h3>${esc(phase.name)}</h3><div><span><b class="${rateClass(phase.leadRate)}">${number(phase.leadActual)}</b><small>实际线索 / ${percent(phase.leadRate)}</small></span><span><b class="${rateClass(phase.orderRate)}">${number(phase.orderActual)}</b><small>实际订单 / ${percent(phase.orderRate)}</small></span></div><footer>目标：线索 ${number(phase.leadTarget)} · 订单 ${number(phase.orderTarget)}</footer></article>`).join("");
  const summaryPhases=[data.phases[0],data.phases[1],data.phases[data.phases.length-1]];
  root.innerHTML=`<section class="lead-dashboard-card" aria-labelledby="lead-dashboard-title"><header><div><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(activeModel)} 线索表现</h2><p>车型由上方销量预警统一选择，本看板不设置第二个车型选择器。</p></div><em>销量预警 → 线索 → 全局车型分析</em></header><div class="lead-dashboard-summary"><article><span>当前销量预警</span><strong class="${esc(warning.level||"yellow")}">${esc(warning.label||"待复核")} · ${number(warning.sales)} 辆</strong><small>头部基准达成率 ${percent(warning.performanceRate)} · ${esc(warning.cycle||"周期待核验")}</small></article>${summaryPhases.map((phase,index)=>`<article><span>${index===2?"平销进行中":esc(phase.name)}</span><strong class="${rateClass(phase.leadRate)}">线索 ${percent(phase.leadRate)}</strong><small>订单达成 ${percent(phase.orderRate)}</small></article>`).join("")}</div><div class="lead-dashboard-phases">${phases}</div><div class="lead-dashboard-diagnosis"><article><span>阶段异常</span><b>线索超目标，订单未同步增长</b><p>6月下半月线索达成117.7%，订单仅64.6%；需要继续核查内容来源与认知阻力。</p></article><article><span>归因边界</span><b>平台与内容归因待接入</b><p>当前只判断线索与订单背离，不把相关性直接写成内容因果。</p></article><article><span>全局联动</span><b>驾驶舱分析对象：${esc(activeModel)}</b><p>现有T周期、正反向、NSR和策略模块统一读取同一车型上下文。</p></article></div><footer><span>来源：${esc(data.source.label)} · ${esc(data.source.scope)}</span><small>缺失字段：平台来源、内容ID、内容标签</small></footer></section>`;
 }

 window.addEventListener("mmn:sales-warning-model-selected",event=>{
  const detail=event.detail||{};
  activeModel=String(detail.model||"").trim();
  warningContext=detail;
  render();
 });
 window.addEventListener("mmn:vehicle-context-updated",event=>{
  const detail=event.detail||{};
  if(detail.source!=="sales-warning")return;
  activeModel=String(detail.model||activeModel).trim();
  render();
 });
 window.MMNLeadDashboard={getModel:()=>activeModel,renderModel:model=>{activeModel=String(model||"").trim();warningContext=null;render()}};
 render();
})();
