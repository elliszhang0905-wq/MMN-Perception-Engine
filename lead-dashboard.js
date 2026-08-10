(function(){
 const root=document.querySelector("#lead-dashboard-root");
 if(!root)return;

 const leadData=Object.create(null);
 const esc=value=>String(value??"").replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
 const number=value=>Number(value||0).toLocaleString("zh-CN",{maximumFractionDigits:0});
 const percent=value=>`${(Number(value||0)*100).toFixed(1)}%`;
 const compact=value=>Number(value||0)>=10000?`${(Number(value)/10000).toFixed(1)}万`:number(value);
 const rateClass=value=>Number(value)>=.9?"good":Number(value)>=.7?"watch":"risk";
 const chartRate=value=>`${(Math.max(0,Math.min(Number(value||0),1.5))/1.5*100).toFixed(2)}%`;
 let activeModel=window.MMNVehicleContext?.getModel?.()||"";
 let warningContext=null;
 let attributionBubbleOpen=false;
 let attributionRun=null,attributionLoading=false,attributionError="",attributionLoadedModel="";
 let datasetRequestId=0,importLoading=false,importMessage="",importTone="";
 let monthMenuOpen=false;
 const monthStateByModel=new Map();

 function datasetYear(data){
  const sourceYear=Number(data?.source?.year),updatedYear=Number(String(data?.updatedAt||"").slice(0,4));
  return Number.isInteger(sourceYear)&&sourceYear>2000?sourceYear:Number.isInteger(updatedYear)&&updatedYear>2000?updatedYear:new Date().getFullYear();
 }

 function phaseMonthInfo(data,phase){
  const match=String(phase?.name||"").match(/(\d{1,2})\s*[.月\/-]\s*(\d{1,2})\s*日?\s*[—–\-~至]+\s*(?:(\d{1,2})\s*[.月\/-]\s*)?(\d{1,2})/);
  if(!match)return null;
  const month=Number(match[3]||match[1]);
  if(!Number.isInteger(month)||month<1||month>12)return null;
  const year=datasetYear(data),key=`${year}-${String(month).padStart(2,"0")}`;
  return{key,year,month,label:`${year}年${month}月`};
 }

 function monthlyPhasesFor(data){
  return data.phases.map(phase=>({phase,month:phaseMonthInfo(data,phase)})).filter(item=>item.month).sort((a,b)=>a.month.key.localeCompare(b.month.key));
 }

 function ensureMonthState(data,monthly){
  const available=monthly.map(item=>item.month.key),latest=available[available.length-1]||"";
  let state=monthStateByModel.get(data.model);
  if(!state)state={selected:new Set(available),known:new Set(available),focused:latest};
  else{
   let newestAdded="";
   available.forEach(key=>{if(!state.known.has(key)){state.selected.add(key);newestAdded=key}});
   state.selected=new Set([...state.selected].filter(key=>available.includes(key)));
   state.known=new Set(available);
   if(newestAdded)state.focused=newestAdded;
   else if(!available.includes(state.focused))state.focused=[...available].reverse().find(key=>state.selected.has(key))||latest;
  }
  monthStateByModel.set(data.model,state);
  return state;
 }

 function monthProgressNote(data,phase,month){
  if(phase.status!=="in_progress")return "完整月份";
  const raw=String(data?.source?.asOf||"");
  const date=raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if(date&&Number(date[2])===month.month)return `截至${Number(date[2])}月${Number(date[3])}日，数据持续更新`;
  return "本月进行中，数据持续更新";
 }

 function normalizeModelData(model,payload){
  const name=String(model||payload?.model||"").trim();
  if(!name)throw new Error("车型不能为空");
  if(!payload||typeof payload!=="object")throw new Error("线索数据格式无效");
  const source=payload.source&&typeof payload.source==="object"?payload.source:{};
  const sourceLabel=String(source.label||"").trim(),sourceScope=String(source.scope||"").trim();
  if(!sourceLabel||!sourceScope)throw new Error("线索数据来源和口径不能为空");
  if(!Array.isArray(payload.phases)||!payload.phases.length)throw new Error("线索阶段不能为空");
  const names=new Set(),phases=payload.phases.map((item,index)=>{
   const phaseName=String(item?.name||"").trim();
   if(!phaseName)throw new Error(`第${index+1}个阶段名称不能为空`);
   if(names.has(phaseName))throw new Error(`${phaseName}阶段重复`);
   names.add(phaseName);
   const leadTarget=Number(item.leadTarget),leadActual=Number(item.leadActual),orderTarget=Number(item.orderTarget),orderActual=Number(item.orderActual);
   if(!Number.isFinite(leadTarget)||leadTarget<=0)throw new Error(`${phaseName}线索目标无效`);
   if(!Number.isFinite(leadActual)||leadActual<0)throw new Error(`${phaseName}实际线索无效`);
   if(!Number.isFinite(orderTarget)||orderTarget<=0)throw new Error(`${phaseName}订单目标无效`);
   if(!Number.isFinite(orderActual)||orderActual<0)throw new Error(`${phaseName}实际订单无效`);
   if(!["completed","in_progress"].includes(item.status))throw new Error(`${phaseName}阶段状态无效`);
   const status=item.status;
   return{...item,name:phaseName,leadTarget,leadActual,leadRate:leadActual/leadTarget,orderTarget,orderActual,orderRate:orderActual/orderTarget,status};
  });
  if(phases.filter(item=>item.status==="in_progress").length>1)throw new Error("只能有一个进行中阶段");
  return{...payload,model:name,source:{...source,label:sourceLabel,scope:sourceScope},warning:payload.warning&&typeof payload.warning==="object"?{...payload.warning}:{},phases};
 }

 function registerModelData(model,payload,options={}){
  try{
   const normalized=normalizeModelData(model,payload);
   leadData[normalized.model]=normalized;
   if(options.render!==false&&normalized.model===activeModel)render();
   return{ok:true,dataset:normalized};
  }catch(error){
   return{ok:false,error:String(error?.message||error||"线索数据格式无效")};
  }
 }

 registerModelData("奥迪E7X",{
   source:{label:"E7X上市流量表现指标统计表",scope:"阶段目标、实际线索与实际订单",asOf:"表内当前填报周期"},
   warning:{level:"yellow",label:"黄色观察",sales:4017,performanceRate:.265,cycle:"销售转化期"},
   phases:[
    {name:"小订阶段",leadTarget:225000,leadActual:183822,orderTarget:10000,orderActual:9419,status:"completed"},
    {name:"大定阶段",leadTarget:230208,leadActual:218414,orderTarget:6000,orderActual:6375,status:"completed"},
    {name:"平销 6.16—6.30",leadTarget:143758,leadActual:169212,orderTarget:2000,orderActual:1293,status:"completed"},
    {name:"平销 7.1—7.31",leadTarget:457143,leadActual:131838,orderTarget:4000,orderActual:837,status:"in_progress"}
   ]
  },{render:false});

 function currentPhaseFor(data){
  return data.phases.find(item=>item.status==="in_progress")||data.phases[data.phases.length-1];
 }

 function diagnosticPhaseFor(data){
  const candidates=data.phases.filter(item=>item.status!=="in_progress"&&item.leadRate>=1&&item.orderRate<.8);
  return candidates.sort((a,b)=>(b.leadRate-b.orderRate)-(a.leadRate-a.orderRate))[0]||currentPhaseFor(data);
 }

	 function buildReasoning(data,warning){
	  const market=window.MMNAttributionContext?.getWarningEvidence?.(activeModel)||warning||{},voice=window.MMNAttributionContext?.getProductEvidence?.(activeModel),phase=diagnosticPhaseFor(data),hasDivergence=phase.leadRate>=1&&phase.orderRate<.8;
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
	   summaryTitle:marketReady&&voiceReady&&hasDivergence?"当前主要断点：线索 → 订单":"跨域证据仍待补齐",
	   summary:marketReady&&voiceReady&&hasDivergence?`市场有规模、车型销量弱于头部；声量不占优但认知质量较好，${phase.name}线索已达标而订单未同步。`:"需要连接细分市场、车型销量、声量、线索与订单后再判断断点。",
	   conclusion:hasDivergence?"现有证据把问题收敛到线索进入后、订单形成前的承接与交易环节；但尚不能归因到平台、内容、销售跟进、价格金融、库存交付中的任何单一因素。":"当前阶段数据尚未形成“线索达标但订单明显落后”的确定性背离，不发布具体归因结论。",
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

 async function loadModelData(model,force=false){
  const requestedModel=String(model||"").trim();
  if(!requestedModel||!window.mmnAuthReady)return;
  const requestId=++datasetRequestId;
  try{
   const response=await fetch(`/api/lead-dashboard-data?model=${encodeURIComponent(requestedModel)}&edition=china`,{headers:typeof authHeaders==="function"?authHeaders():{}});
   const payload=await response.json();
   if(!response.ok||payload.ok===false)throw new Error(payload.error||"线索数据读取失败");
   if(requestId!==datasetRequestId||requestedModel!==activeModel)return;
   if(payload.dataset)registerModelData(requestedModel,payload.dataset,{render:false});
   else if(requestedModel!=="奥迪E7X")delete leadData[requestedModel];
   if(force||payload.dataset||requestedModel===activeModel)render();
  }catch(error){
   if(requestId!==datasetRequestId||requestedModel!==activeModel)return;
   if(requestedModel!=="奥迪E7X")delete leadData[requestedModel];
   importTone="error";importMessage=String(error?.message||error||"线索数据读取失败");render();
  }
 }

 async function importLeadFile(file){
  if(importLoading||!file)return;
  if(file.size>4*1024*1024){importTone="error";importMessage="文件不能超过4MB";render();return}
  importLoading=true;importTone="";importMessage="正在校验并导入车型线索数据";render();
  try{
   const response=await fetch(`/api/lead-dashboard/import?filename=${encodeURIComponent(file.name)}&edition=china`,{method:"POST",headers:typeof authHeaders==="function"?authHeaders():{},body:await file.arrayBuffer()});
   const payload=await response.json();
   if(!response.ok||payload.ok===false)throw new Error(payload.error||"线索数据导入失败");
   const results=(payload.datasets||[]).map(item=>registerModelData(item.model,item,{render:false}));
   const failed=results.find(item=>!item.ok);
   if(failed)throw new Error(failed.error);
   const models=(payload.datasets||[]).map(item=>item.model);
   importTone="success";
   importMessage=models.includes(activeModel)?`${activeModel}线索数据已更新`:`已导入${models.join("、")}，切换到对应车型后即可查看`;
  }catch(error){
   importTone="error";importMessage=String(error?.message||error||"线索数据导入失败");
  }finally{
   importLoading=false;render();
  }
 }

 function importControl(){
  return `<div class="lead-dashboard-actions"><button class="lead-import-trigger" type="button" ${importLoading?"disabled":""}>${importLoading?"导入处理中…":"导入线索数据"}</button><input class="lead-import-file" type="file" accept=".xlsx,.csv,.json" hidden><small class="${esc(importTone)}" role="status">${esc(importMessage)}</small></div>`;
 }

 function clearImportMessage(){
  importTone="";importMessage="";
 }

 function renderEmpty(model){
  const name=model||"当前车型";
  root.innerHTML=`<section class="lead-dashboard-card empty" aria-labelledby="lead-dashboard-title"><header><div><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(name)} 线索表现</h2><p>车型由上方销量预警统一选择。</p></div>${importControl()}</header><div class="lead-dashboard-empty" role="status"><b>${esc(name)}线索数据待接入</b><p>已清空上一车型数据，避免跨车型误读。导入包含车型、阶段、线索目标、实际线索、订单目标、实际订单和阶段状态的xlsx、csv或json文件后自动生成看板。</p></div><footer><span>当前车型上下文：${esc(name)}</span><small>未取得平台来源、内容ID与内容标签时，不生成内容归因结论。</small></footer></section>`;
 }

	 function render(){
	  const data=leadData[activeModel];
	  if(!data){renderEmpty(activeModel);return}
	  const warning={...data.warning,...(warningContext?.model===activeModel?warningContext:{})};
	  const reasoning=buildReasoning(data,warning);
	  const status=reviewStatus(),finalConclusion=attributionRun?.status==="aligned"?attributionRun?.arbitration?.finalConclusion:null;
	  const monthly=monthlyPhasesFor(data),monthState=ensureMonthState(data,monthly),selectedMonthly=monthly.filter(item=>monthState.selected.has(item.month.key));
	  const focusedMonthly=monthly.find(item=>item.month.key===monthState.focused)||selectedMonthly[selectedMonthly.length-1]||monthly[monthly.length-1];
	  const currentPhase=focusedMonthly?.phase||currentPhaseFor(data),currentMonth=focusedMonthly?.month||null,diagnosticPhase=diagnosticPhaseFor(data),hasDivergence=diagnosticPhase.leadRate>=1&&diagnosticPhase.orderRate<.8;
	  const chartPhases=monthly.length?selectedMonthly.map(item=>({...item.phase,month:item.month})):data.phases;
	  const stageGroups=chartPhases.map((phase,index)=>{
	   const isCurrent=phase.status==="in_progress"||(!data.phases.some(item=>item.status==="in_progress")&&index===data.phases.length-1),isDivergent=phase.leadRate>=1&&phase.orderRate<.8;
	   const month=phase.month,isFocused=month&&month.key===monthState.focused,label=month?.label||phase.name,note=month?monthProgressNote(data,phase,month):(isCurrent?"进行中":isDivergent?"表现背离":"");
	   return `<article class="lead-stage-group${isCurrent?" current":""}${isDivergent?" divergence":""}${isFocused?" focused":""}" ${month?`data-month-key="${esc(month.key)}" tabindex="0" role="button"`:""} aria-label="${esc(label)}：线索达成${percent(phase.leadRate)}，订单达成${percent(phase.orderRate)}"><div class="lead-stage-bars" aria-hidden="true"><span class="lead-stage-bar lead" style="--lead-rate:${chartRate(phase.leadRate)}"><b>${percent(phase.leadRate)}</b></span><span class="lead-stage-bar order" style="--lead-rate:${chartRate(phase.orderRate)}"><b>${percent(phase.orderRate)}</b></span></div><h4>${esc(label)}${isCurrent?' <em>（进行中）</em>':""}</h4><p>线索 ${number(phase.leadActual)} / ${number(phase.leadTarget)}<br>订单 ${number(phase.orderActual)} / ${number(phase.orderTarget)}</p>${note?`<small>${esc(note)}</small>`:""}</article>`;
	  }).join("");
	  const monthOptions=monthly.map(item=>`<label><input type="checkbox" value="${esc(item.month.key)}" ${monthState.selected.has(item.month.key)?"checked":""}><span>${esc(item.month.label)}</span></label>`).join("");
	  const monthPicker=monthly.length?`<div class="lead-month-filter"><button class="lead-month-trigger" type="button" aria-expanded="${monthMenuOpen}" aria-controls="lead-month-menu"><span>月份</span><b>${monthState.selected.size===monthly.length?"全部月份":`已选${monthState.selected.size}个月`}</b><i aria-hidden="true">⌄</i></button><div id="lead-month-menu" class="lead-month-menu" ${monthMenuOpen?"":"hidden"}><header><button type="button" data-month-action="all">全选</button><button type="button" data-month-action="clear">清空</button></header>${monthOptions}</div></div>`:"";
	  const chartEmpty=monthly.length&&!selectedMonthly.length?'<div class="lead-month-empty" role="status"><b>请选择要比较的月份</b><p>可在左上角月份选项中多选历史月份。</p></div>':stageGroups;
	  const evidenceChain=reasoning.evidence.map((item,index)=>`<article class="lead-reasoning-step ${item.state==="待补证据"?"missing":""}"><span>${esc(item.step)}</span><div><small>${esc(item.label)}</small><b>${esc(item.value)}</b><p>${esc(item.detail)}</p></div>${index<reasoning.evidence.length-1?'<i aria-hidden="true">→</i>':""}</article>`).join("");
	  const actionRows=finalConclusion?.nextActions?.length?finalConclusion.nextActions.map(item=>`${item.priority}｜${item.action}｜指标：${item.metric}｜停止：${item.stopCondition}`):reasoning.actions;
	  const actions=actionRows.map(item=>`<li>${esc(item)}</li>`).join("");
	  const providerRows=(attributionRun?.providers||[]).map(item=>`<article class="lead-provider-review ${esc(item.status)}"><span>${esc(item.role)}</span><b>${item.status==="completed"?"已完成":item.status==="failed"?"未完成":"等待中"}</b><p>${esc(item.review?.conclusion||"未形成可发布研判")}</p></article>`).join("");
	  const decisionText=finalConclusion?.conclusion||reasoning.conclusion,decisionLabel=finalConclusion?"交叉裁决结论":"阶段性结论（确定性规则）";
	  const attributionCard=`<article class="lead-attribution-card"><span>跨域归因研判</span><b>${esc(finalConclusion?"裁决结论：线索 → 订单":reasoning.summaryTitle)}</b><p>${esc(finalConclusion?.conclusion||reasoning.summary)}</p><small class="lead-attribution-state ${esc(status.tone)}">${esc(status.label)}</small><button class="lead-attribution-trigger" type="button" aria-expanded="${attributionBubbleOpen}" aria-controls="lead-attribution-bubble" aria-label="${attributionBubbleOpen?"收起":"展开"}完整归因推理论证"><span aria-hidden="true">推理</span></button><aside id="lead-attribution-bubble" class="lead-attribution-bubble" role="dialog" aria-labelledby="lead-attribution-title" ${attributionBubbleOpen?"":"hidden"}><header><div><small>三路独立复核 · 同一证据包</small><h3 id="lead-attribution-title">完整归因研判</h3></div><em class="${esc(status.tone)}">${esc(status.label)}</em></header><div class="lead-attribution-control"><p>${esc(status.detail)}</p><button class="lead-attribution-run" type="button" ${attributionLoading?"disabled":""}>${attributionLoading?"三路复核中…":attributionRun?"重新运行三路复核":"开始三路复核"}</button></div><div class="lead-reasoning-chain" aria-label="细分市场容量到订单达成率的推理路径">${evidenceChain}</div>${providerRows?`<section><h4>三路独立研判</h4><div class="lead-provider-grid">${providerRows}</div></section>`:""}<section><h4>${esc(decisionLabel)}</h4><p>${esc(decisionText)}</p>${attributionRun&&!finalConclusion?`<p class="lead-no-publish">存在分歧或未全部完成，本轮不发布模型最终结论。</p>`:""}</section><section><h4>下一步验证</h4><ol>${actions}</ol></section><footer><b>推理边界</b>${esc(finalConclusion?.causalBoundary||reasoning.boundary)}</footer></aside></article>`;
	  root.innerHTML=`<section class="lead-dashboard-card" aria-labelledby="lead-dashboard-title"><header><div class="lead-dashboard-heading"><span>线索看板 · 跟随销量预警车型</span><h2 id="lead-dashboard-title">${esc(activeModel)} 线索表现</h2><p>车型总体线索｜暂未分平台</p><div class="lead-dashboard-pills" aria-label="当前车型状态"><strong class="${esc(warning.level||"yellow")}">${esc(warning.label||"待复核")} · ${number(warning.sales)}辆</strong><strong>${esc(warning.cycle||"周期待核验")}</strong></div></div><div class="lead-dashboard-header-tools"><em>销量预警 → 线索 → 全局车型分析</em>${importControl()}</div></header><div class="lead-dashboard-overview"><section class="lead-stage-chart" aria-labelledby="lead-stage-chart-title"><header><div class="lead-chart-title-row">${monthPicker}<div><span>${monthly.length?"月度趋势":"阶段表现"}</span><h3 id="lead-stage-chart-title">${monthly.length?"月度线索与订单达成":"线索与订单阶段达成"}</h3></div></div><div class="lead-chart-legend" aria-label="图例"><span class="lead">线索达成率</span><span class="order">订单达成率</span></div></header><div class="lead-chart-scale" aria-hidden="true"><span>150%</span><span>100%</span><span>50%</span><span>0%</span></div><div class="lead-chart-plot" style="--lead-month-count:${Math.max(chartPhases.length,1)}"><div class="lead-target-line" aria-hidden="true"><span>目标 100%</span></div>${chartEmpty}</div></section><aside class="lead-current-progress" aria-labelledby="lead-current-progress-title"><header><span>${monthly.length?"当前查看月份":"当前阶段"}</span><h3 id="lead-current-progress-title">${monthly.length?"月份数据详情":"当前阶段进度"}</h3><small>${esc(currentMonth?.label||currentPhase.name)}${currentPhase.status==="in_progress"?"（进行中）":""}</small></header><article><span>线索</span><p><b>${number(currentPhase.leadActual)}</b><small>/ ${number(currentPhase.leadTarget)} · ${percent(currentPhase.leadRate)}</small></p><progress max="100" value="${Math.min(currentPhase.leadRate*100,100).toFixed(1)}" aria-label="当前查看数据线索达成率 ${percent(currentPhase.leadRate)}">${percent(currentPhase.leadRate)}</progress></article><article class="order"><span>订单</span><p><b>${number(currentPhase.orderActual)}</b><small>/ ${number(currentPhase.orderTarget)} · ${percent(currentPhase.orderRate)}</small></p><progress max="100" value="${Math.min(currentPhase.orderRate*100,100).toFixed(1)}" aria-label="当前查看数据订单达成率 ${percent(currentPhase.orderRate)}">${percent(currentPhase.orderRate)}</progress></article><footer>${currentMonth?monthProgressNote(data,currentPhase,currentMonth):currentPhase.status==="in_progress"?"当前周期进行中，不按完整周期直接判定":"当前阶段已完成，按已导入周期口径判断"}</footer></aside></div><div class="lead-dashboard-diagnosis"><article><span>阶段异常</span><b>${hasDivergence?"线索超目标，订单未同步增长":"暂未发现确定性表现背离"}</b><p>${hasDivergence?`${esc(diagnosticPhase.name)}线索达成${percent(diagnosticPhase.leadRate)}，订单仅${percent(diagnosticPhase.orderRate)}；需要继续核查内容来源与认知阻力。`:"现有阶段尚未同时满足线索达标与订单明显落后条件，不生成具体归因。"}</p></article>${attributionCard}<article><span>全局联动</span><b>驾驶舱分析对象：${esc(activeModel)}</b><p>现有T周期、正反向、NSR和策略模块统一读取同一车型上下文。</p></article></div><footer><span>来源：${esc(data.source.label)} · ${esc(data.source.scope)}</span><small>证据边界：暂未分平台；缺少线索订单关联，不能认定为真实转化率下降</small></footer></section>`;
	 }

	 function setAttributionBubble(open){
	  const trigger=root.querySelector(".lead-attribution-trigger"),bubble=root.querySelector(".lead-attribution-bubble");
	  if(!trigger||!bubble)return;
	  attributionBubbleOpen=Boolean(open);trigger.setAttribute("aria-expanded",String(attributionBubbleOpen));trigger.setAttribute("aria-label",attributionBubbleOpen?"收起完整归因推理论证":"展开完整归因推理论证");bubble.hidden=!attributionBubbleOpen;
	 }

	 function updateMonthSelection(action,value,checked){
	  const data=leadData[activeModel],monthly=data?monthlyPhasesFor(data):[];
	  if(!data||!monthly.length)return;
	  const state=ensureMonthState(data,monthly),available=monthly.map(item=>item.month.key);
	  if(action==="all")state.selected=new Set(available);
	  else if(action==="clear")state.selected=new Set();
	  else if(value){if(checked)state.selected.add(value);else state.selected.delete(value)}
	  if(!state.selected.has(state.focused))state.focused=[...available].reverse().find(key=>state.selected.has(key))||available[available.length-1];
	  render();
	 }

	 function focusMonth(key){
	  const data=leadData[activeModel],monthly=data?monthlyPhasesFor(data):[];
	  if(!data||!monthly.some(item=>item.month.key===key))return;
	  ensureMonthState(data,monthly).focused=key;
	  render();
	 }

	 root.addEventListener("click",event=>{
	  if(event.target.closest?.(".lead-attribution-trigger"))setAttributionBubble(!attributionBubbleOpen);
	  if(event.target.closest?.(".lead-attribution-run"))runAttributionReview();
	  if(event.target.closest?.(".lead-import-trigger"))root.querySelector(".lead-import-file")?.click();
	  if(event.target.closest?.(".lead-month-trigger")){monthMenuOpen=!monthMenuOpen;render();return}
	  const action=event.target.closest?.("[data-month-action]")?.dataset?.monthAction;
	  if(action){updateMonthSelection(action);return}
	  const monthKey=event.target.closest?.("[data-month-key]")?.dataset?.monthKey;
	  if(monthKey)focusMonth(monthKey);
	 });
	 root.addEventListener("change",event=>{
	  if(event.target.matches?.(".lead-import-file")){const file=event.target.files?.[0];event.target.value="";if(file)importLeadFile(file)}
	  if(event.target.matches?.(".lead-month-menu input[type=checkbox]"))updateMonthSelection("toggle",event.target.value,event.target.checked);
	 });
	 root.addEventListener("keydown",event=>{const group=event.target.closest?.("[data-month-key]");if(group&&(event.key==="Enter"||event.key===" ")){event.preventDefault();focusMonth(group.dataset.monthKey)}});
	 document.addEventListener("click",event=>{const attributionCard=root.querySelector(".lead-attribution-card");if(attributionBubbleOpen&&attributionCard&&!attributionCard.contains(event.target))setAttributionBubble(false);if(event.target.closest?.(".lead-month-filter"))return;const monthFilter=root.querySelector(".lead-month-filter");if(monthMenuOpen&&monthFilter&&!monthFilter.contains(event.target)){monthMenuOpen=false;render()}});
	 document.addEventListener("keydown",event=>{if(event.key!=="Escape")return;if(attributionBubbleOpen){setAttributionBubble(false);root.querySelector(".lead-attribution-trigger")?.focus()}if(monthMenuOpen){monthMenuOpen=false;render();root.querySelector(".lead-month-trigger")?.focus()}});
	 window.addEventListener("mmn:auth-ready",()=>{loadModelData(activeModel,true);loadAttributionRun(true)});

 window.addEventListener("mmn:sales-warning-model-selected",event=>{
  const detail=event.detail||{};
  const previousModel=activeModel;
  activeModel=String(detail.model||"").trim();
  if(previousModel!==activeModel)clearImportMessage();
  warningContext=detail;attributionBubbleOpen=false;monthMenuOpen=false;attributionRun=null;attributionLoadedModel="";
  render();loadModelData(activeModel);loadAttributionRun();
 });
 window.addEventListener("mmn:vehicle-context-updated",event=>{
  const detail=event.detail||{};
  if(detail.source!=="sales-warning")return;
  const previousModel=activeModel;activeModel=String(detail.model||activeModel).trim();
  if(previousModel!==activeModel)clearImportMessage();
  attributionBubbleOpen=false;monthMenuOpen=false;attributionRun=null;attributionLoadedModel="";render();loadModelData(activeModel);loadAttributionRun();
 });
	 window.MMNLeadDashboard={getModel:()=>activeModel,getModelData:model=>leadData[String(model||"").trim()]||null,getSelectedMonths:()=>{const data=leadData[activeModel],monthly=data?monthlyPhasesFor(data):[];return data?[...ensureMonthState(data,monthly).selected]:[]},setSelectedMonths:keys=>{const data=leadData[activeModel],monthly=data?monthlyPhasesFor(data):[];if(!data)return;const available=monthly.map(item=>item.month.key),state=ensureMonthState(data,monthly);state.selected=new Set((Array.isArray(keys)?keys:[]).filter(key=>available.includes(key)));if(!state.selected.has(state.focused))state.focused=[...available].reverse().find(key=>state.selected.has(key))||available[available.length-1];render()},focusMonth,normalizeModelData,registerModelData,renderModel:model=>{const nextModel=String(model||"").trim();if(nextModel!==activeModel)clearImportMessage();activeModel=nextModel;warningContext=null;monthMenuOpen=false;render();loadModelData(activeModel)}};
	 render();loadModelData(activeModel);loadAttributionRun();
	 if(leadData[activeModel]&&(!window.MMNAttributionContext?.getWarningEvidence?.(activeModel)||!window.MMNAttributionContext?.getProductEvidence?.(activeModel)))window.loadGroupDashboardDemo?.();
})();
