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
	 const compact=value=>Number(value||0)>=10000?`${(Number(value)/10000).toFixed(1)}万`:number(value);
 const rateClass=value=>Number(value)>=.9?"good":Number(value)>=.7?"watch":"risk";
 let activeModel=window.MMNVehicleContext?.getModel?.()||"";
 let warningContext=null;
	 let attributionBubbleOpen=false;
	 let attributionRun=null,attributionLoading=false,attributionError="",attributionLoadedModel="";

	 function buildReasoning(data,warning){
	  const market=window.MMNAttributionContext?.getWarningEvidence?.(activeModel)||warning||{},voice=window.MMNAttributionContext?.getProductEvidence?.(activeModel),phase=data.phases.find(item=>item.name.includes("6.16"))||data.phases[data.phases.length-1];
	  const marketReady=Number.isFinite(Number(market.marketSales))&&Number(market.marketSales)>0,voiceReady=Boolean(voice&&Number.isFinite(Number(voice.voice))),salesReady=Number.isFinite(Number(market.sales))&&Number(market.sales)>0;
	  const evidence=[
	   {step:"01",label:"细分市场容量",value:marketReady?`${number(market.marketSales)} 辆`:"待接入",state:marketReady?"部分验证":"待补证据",detail:marketReady?`${market.segmentLabel||"当前细分市场"} · ${market.period||"当前月"}实际销量；单月规模不替代容量预测。`:"需要同口径连续周期市场规模或容量预测。"},
	   {step:"02",label:"细分市场销量分析",value:salesReady?`${number(market.sales)} 辆`:"待接入",state:salesReady?"已验证":"待补证据",detail:salesReady?`本品份额 ${percent(market.marketShare)} · 细分榜第 ${market.rank||"—"} · 头部基准达成 ${percent(market.performanceRate)}。`:"需要车型销量、份额、排名与头部竞争基准。"},
	   {step:"03",label:"声量分析",value:voiceReady?compact(voice.voice):"待接入",state:voiceReady?"已验证":"待补证据",detail:voiceReady?`${voice.comparisonCount}车声量第 ${voice.voiceRank} · 全网NSR ${voice.overallNsr===null?"待补":percent(voice.overallNsr)} · ${voice.period||"周期待补"}。`:"需要同周期本竞品声量、互动与认知质量。"},
	   {step:"04",label:"线索分析",value:number(phase.leadActual),state:"已验证",detail:`${phase.name} · 线索目标 ${number(phase.leadTarget)} · 达成 ${percent(phase.leadRate)}。`},
	   {step:"05",label:"订单达成率",value:percent(phase.orderRate),state:"已验证",detail:`实际订单 ${number(phase.orderActual)} / 目标 ${number(phase.orderTarget)}；当前不是同批线索真实转化率。`}
	  ];
	  return{
	   evidence,
	   summaryTitle:marketReady&&voiceReady?"当前主要断点：线索 → 订单":"跨域证据仍待补齐",
	   summary:marketReady&&voiceReady?`市场有规模、车型销量弱于头部；声量不占优但认知质量较好，${phase.name}线索已达标而订单未同步。`:"需要连接细分市场、车型销量、声量、线索与订单后再判断断点。",
	   conclusion:"现有证据把问题收敛到线索进入后、订单形成前的承接与交易环节；但尚不能归因到平台、内容、销售跟进、价格金融、库存交付中的任何单一因素。",
	   actions:["P0｜按同一时间窗打通线索ID—订单ID，并补齐平台、内容、地区与失单原因","P0｜分区域核查首次联系时长、有效线索率、订单归因窗口与销售承接差异","P1｜把价格、金融、库存、交付变化作为替代解释共同检验","P2｜三旗舰基于同一证据包独立输出结论、反证、领先指标与停止条件；分歧进入人工裁决"],
	   boundary:"当前细分市场容量仅以当月同口径实际销量表示；声量不等于需求，订单达成率不等于线索转化率，三旗舰一致也不构成因果证据。"
	  };
	 }

	 const reviewStatus=()=>{
	  if(attributionLoading)return{tone:"running",label:"三路独立复核运行中",detail:"正在基于同一锁定证据包分别研判并等待裁决。"};
	  if(attributionError)return{tone:"failed",label:"本轮复核未完成",detail:attributionError};
	  if(!attributionRun)return{tone:"idle",label:"尚未运行三路独立复核",detail:"展开后可启动真实复核；未运行前不发布模型结论。"};
	  if(attributionRun.status==="aligned")return{tone:"verified",label:"三路独立复核已完成 · 裁决一致",detail:`共同证据 ${attributionRun.arbitration?.commonEvidenceIds?.length||0} 项 · 已持久化`};
	  if(attributionRun.status==="manual_required")return{tone:"review",label:"三路独立复核已完成 · 待人工裁决",detail:(attributionRun.arbitration?.reasons||[]).join("；")||"三路判断存在分歧。"};
	  return{tone:"failed",label:"三路独立复核未全部完成",detail:(attributionRun.arbitration?.reasons||[]).join("；")||"至少一路失败，最终结论未发布。"};
	 };

	 async function loadAttributionRun(force=false){
	  if(!window.mmnAuthReady)return;
	  if(!activeModel||(!force&&attributionLoadedModel===activeModel))return;
	  attributionLoadedModel=activeModel;attributionError="";
	  try{const response=await fetch(`/api/attribution-reasoning?model=${encodeURIComponent(activeModel)}&edition=china`,{headers:typeof authHeaders==="function"?authHeaders():{}}),payload=await response.json();if(!response.ok||payload.ok===false)throw new Error(payload.error||"读取复核记录失败");attributionRun=payload.run||null}
	  catch(error){attributionError=String(error?.message||error||"读取复核记录失败")}
	  render();
	 }

	 async function runAttributionReview(){
	  if(attributionLoading||!activeModel)return;
	  attributionLoading=true;attributionError="";render();
	  try{const response=await fetch("/api/attribution-reasoning/run",{method:"POST",headers:{...(typeof authHeaders==="function"?authHeaders():{}),"Content-Type":"application/json"},body:JSON.stringify({model:activeModel,edition:"china"})}),payload=await response.json();if(!response.ok||payload.ok===false)throw new Error(payload.error||"三路复核未完成");attributionRun=payload.run||null;attributionLoadedModel=activeModel}
	  catch(error){attributionError=String(error?.message||error||"三路复核未完成")}
	  finally{attributionLoading=false;render()}
	 }

 function renderEmpty(model){
  const name=model||"当前车型";
  root.innerHTML=`<section class="lead-dashboard-card empty" aria-labelledby="lead-dashboard-title"><header><div><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(name)} 线索表现</h2><p>车型由上方销量预警统一选择，本看板不设置第二个车型选择器。</p></div><em>数据待接入</em></header><div class="lead-dashboard-empty" role="status"><b>${esc(name)}线索数据待接入</b><p>已清空上一车型数据，避免跨车型误读。接入阶段目标、实际线索与实际订单后自动生成看板。</p></div><footer><span>当前车型上下文：${esc(name)}</span><small>未取得平台来源、内容ID与内容标签时，不生成内容归因结论。</small></footer></section>`;
 }

	 function render(){
	  const data=leadData[activeModel];
	  if(!data){renderEmpty(activeModel);return}
	  const warning={...data.warning,...(warningContext?.model===activeModel?warningContext:{})};
	  const reasoning=buildReasoning(data,warning);
	  const status=reviewStatus(),finalConclusion=attributionRun?.status==="aligned"?attributionRun?.arbitration?.finalConclusion:null;
	  const phases=data.phases.map(phase=>`<article class="lead-phase"><h3>${esc(phase.name)}</h3><div><span><b class="${rateClass(phase.leadRate)}">${number(phase.leadActual)}</b><small>实际线索 / ${percent(phase.leadRate)}</small></span><span><b class="${rateClass(phase.orderRate)}">${number(phase.orderActual)}</b><small>实际订单 / ${percent(phase.orderRate)}</small></span></div><footer>目标：线索 ${number(phase.leadTarget)} · 订单 ${number(phase.orderTarget)}</footer></article>`).join("");
	  const summaryPhases=[data.phases[0],data.phases[1],data.phases[data.phases.length-1]];
	  const evidenceChain=reasoning.evidence.map((item,index)=>`<article class="lead-reasoning-step ${item.state==="待补证据"?"missing":""}"><span>${esc(item.step)}</span><div><small>${esc(item.label)}</small><b>${esc(item.value)}</b><p>${esc(item.detail)}</p></div>${index<reasoning.evidence.length-1?'<i aria-hidden="true">→</i>':""}</article>`).join("");
	  const actionRows=finalConclusion?.nextActions?.length?finalConclusion.nextActions.map(item=>`${item.priority}｜${item.action}｜指标：${item.metric}｜停止：${item.stopCondition}`):reasoning.actions;
	  const actions=actionRows.map(item=>`<li>${esc(item)}</li>`).join("");
	  const providerRows=(attributionRun?.providers||[]).map(item=>`<article class="lead-provider-review ${esc(item.status)}"><span>${esc(item.role)}</span><b>${item.status==="completed"?"已完成":item.status==="failed"?"未完成":"等待中"}</b><p>${esc(item.review?.conclusion||"未形成可发布研判")}</p></article>`).join("");
	  const decisionText=finalConclusion?.conclusion||reasoning.conclusion,decisionLabel=finalConclusion?"交叉裁决结论":"阶段性结论（确定性规则）";
	  const attributionCard=`<article class="lead-attribution-card"><span>跨域归因研判</span><b>${esc(finalConclusion?"裁决结论：线索 → 订单":reasoning.summaryTitle)}</b><p>${esc(finalConclusion?.conclusion||reasoning.summary)}</p><small class="lead-attribution-state ${esc(status.tone)}">${esc(status.label)}</small><button class="lead-attribution-trigger" type="button" aria-expanded="${attributionBubbleOpen}" aria-controls="lead-attribution-bubble" aria-label="${attributionBubbleOpen?"收起":"展开"}完整归因推理论证"><span aria-hidden="true">推理</span></button><aside id="lead-attribution-bubble" class="lead-attribution-bubble" role="dialog" aria-labelledby="lead-attribution-title" ${attributionBubbleOpen?"":"hidden"}><header><div><small>三路独立复核 · 同一证据包</small><h3 id="lead-attribution-title">完整归因研判</h3></div><em class="${esc(status.tone)}">${esc(status.label)}</em></header><div class="lead-attribution-control"><p>${esc(status.detail)}</p><button class="lead-attribution-run" type="button" ${attributionLoading?"disabled":""}>${attributionLoading?"三路复核中…":attributionRun?"重新运行三路复核":"开始三路复核"}</button></div><div class="lead-reasoning-chain" aria-label="细分市场容量到订单达成率的推理路径">${evidenceChain}</div>${providerRows?`<section><h4>三路独立研判</h4><div class="lead-provider-grid">${providerRows}</div></section>`:""}<section><h4>${esc(decisionLabel)}</h4><p>${esc(decisionText)}</p>${attributionRun&&!finalConclusion?`<p class="lead-no-publish">存在分歧或未全部完成，本轮不发布模型最终结论。</p>`:""}</section><section><h4>下一步验证</h4><ol>${actions}</ol></section><footer><b>推理边界</b>${esc(finalConclusion?.causalBoundary||reasoning.boundary)}</footer></aside></article>`;
	  root.innerHTML=`<section class="lead-dashboard-card" aria-labelledby="lead-dashboard-title"><header><div><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(activeModel)} 线索表现</h2><p>车型由上方销量预警统一选择，本看板不设置第二个车型选择器。</p></div><em>销量预警 → 线索 → 全局车型分析</em></header><div class="lead-dashboard-summary"><article><span>当前销量预警</span><strong class="${esc(warning.level||"yellow")}">${esc(warning.label||"待复核")} · ${number(warning.sales)} 辆</strong><small>头部基准达成率 ${percent(warning.performanceRate)} · ${esc(warning.cycle||"周期待核验")}</small></article>${summaryPhases.map((phase,index)=>`<article><span>${index===2?"平销进行中":esc(phase.name)}</span><strong class="${rateClass(phase.leadRate)}">线索 ${percent(phase.leadRate)}</strong><small>订单达成 ${percent(phase.orderRate)}</small></article>`).join("")}</div><div class="lead-dashboard-phases">${phases}</div><div class="lead-dashboard-diagnosis"><article><span>阶段异常</span><b>线索超目标，订单未同步增长</b><p>6月下半月线索达成117.7%，订单仅64.6%；需要继续核查内容来源与认知阻力。</p></article>${attributionCard}<article><span>全局联动</span><b>驾驶舱分析对象：${esc(activeModel)}</b><p>现有T周期、正反向、NSR和策略模块统一读取同一车型上下文。</p></article></div><footer><span>来源：${esc(data.source.label)} · ${esc(data.source.scope)}</span><small>缺失字段：平台来源、内容ID、内容标签、线索订单关联</small></footer></section>`;
	 }

	 function setAttributionBubble(open){
	  const trigger=root.querySelector(".lead-attribution-trigger"),bubble=root.querySelector(".lead-attribution-bubble");
	  if(!trigger||!bubble)return;
	  attributionBubbleOpen=Boolean(open);trigger.setAttribute("aria-expanded",String(attributionBubbleOpen));trigger.setAttribute("aria-label",attributionBubbleOpen?"收起完整归因推理论证":"展开完整归因推理论证");bubble.hidden=!attributionBubbleOpen;
	 }

	 root.addEventListener("click",event=>{if(event.target.closest?.(".lead-attribution-trigger"))setAttributionBubble(!attributionBubbleOpen);if(event.target.closest?.(".lead-attribution-run"))runAttributionReview()});
	 document.addEventListener("click",event=>{if(!attributionBubbleOpen)return;const card=root.querySelector(".lead-attribution-card");if(card&&!card.contains(event.target))setAttributionBubble(false)});
	 document.addEventListener("keydown",event=>{if(event.key==="Escape"&&attributionBubbleOpen){setAttributionBubble(false);root.querySelector(".lead-attribution-trigger")?.focus()}});
	 window.addEventListener("mmn:auth-ready",()=>loadAttributionRun(true));

 window.addEventListener("mmn:sales-warning-model-selected",event=>{
  const detail=event.detail||{};
  activeModel=String(detail.model||"").trim();
  warningContext=detail;attributionBubbleOpen=false;attributionRun=null;attributionLoadedModel="";
  render();loadAttributionRun();
 });
 window.addEventListener("mmn:vehicle-context-updated",event=>{
  const detail=event.detail||{};
  if(detail.source!=="sales-warning")return;
  activeModel=String(detail.model||activeModel).trim();
  attributionBubbleOpen=false;attributionRun=null;attributionLoadedModel="";render();loadAttributionRun();
 });
	 window.MMNLeadDashboard={getModel:()=>activeModel,renderModel:model=>{activeModel=String(model||"").trim();warningContext=null;render()}};
	 render();loadAttributionRun();
	 if(leadData[activeModel]&&(!window.MMNAttributionContext?.getWarningEvidence?.(activeModel)||!window.MMNAttributionContext?.getProductEvidence?.(activeModel)))window.loadGroupDashboardDemo?.();
})();
