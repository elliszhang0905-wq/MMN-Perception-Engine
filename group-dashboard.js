(function(){
 const root=document.querySelector("#group-dashboard-root");
 if(!root)return;
 let loading=false,loadedEdition="";
 const esc=value=>String(value??"").replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
 const num=value=>Number(value||0).toLocaleString("zh-CN");
 const compact=value=>Number(value||0)>=10000?`${(Number(value)/10000).toFixed(1)}万`:num(value);
 const pct=value=>value===null||value===undefined?"暂无":`${(Number(value)*100).toFixed(1)}%`;
 const rate=value=>value===null||value===undefined?"暂无环比":`${value>=0?"+":""}${(value*100).toFixed(1)}%`;
 const rateClass=value=>value===null||value===undefined?"flat":value>=0?"up":"down";
 const starPoints=(cx,cy,outer,inner)=>Array.from({length:10},(_,index)=>{const radius=index%2?inner:outer,angle=-Math.PI/2+index*Math.PI/5;return`${cx+Math.cos(angle)*radius},${cy+Math.sin(angle)*radius}`}).join(" ");

 function skeleton(){
  root.innerHTML=`<div class="group-dashboard-loading" role="status" aria-live="polite"><b>正在聚合集团看板数据</b><span></span><span></span><span></span></div>`;
 }

 function renderDimensionPlot(dimension,index,focusKeys){
  const items=dimension.items||[],width=920,height=300,baseline=132,maxAbs=Math.max(.2,...items.map(item=>Math.abs(item.changeRate||0))),maxSales=Math.max(1,...items.map(item=>item.top10Sales||0));
  const points=items.map((item,pointIndex)=>{const missing=item.status!=="available",focused=focusKeys.includes(item.key),x=85+pointIndex*((width-170)/Math.max(1,items.length-1)),change=item.changeRate||0,y=missing?baseline:baseline-change/maxAbs*78,r=missing?13:10+Math.sqrt((item.top10Sales||0)/maxSales)*12,saic=item.saicTop10.map(row=>`${row.model} #${row.rank}`).join(" / ")||"本期未进入",delta=missing?"待接入":rate(item.changeRate),sales=missing?"独立榜暂无":num(item.top10Sales);return`<g class="group-star-point ${missing?"missing":rateClass(item.changeRate)} ${focused?"focus":""}" tabindex="0" role="img" aria-label="${esc(item.label)}，${focused?"奥迪E7X所在赛道，":""}${missing?"独立榜待接入":`环比${rate(item.changeRate)}，Top10合计${num(item.top10Sales)}`}"><line x1="${x}" y1="${baseline}" x2="${x}" y2="${y}"/><circle class="halo" cx="${x}" cy="${y}" r="${r+7}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/>${focused?`<circle class="focus-ring" cx="${x}" cy="${y}" r="${r+12}"/><text class="focus-tag" x="${x}" y="216" text-anchor="middle">E7X 所在赛道</text>`:""}<text class="delta" x="${x}" y="${y-r-10}" text-anchor="middle">${esc(delta)}</text><text class="segment" x="${x}" y="236" text-anchor="middle">${esc(item.label)}</text><text class="sales" x="${x}" y="254" text-anchor="middle">${esc(sales)}</text><text class="saic" x="${x}" y="276" text-anchor="middle">${missing?"不从总体榜倒推":esc(saic.length>18?`${saic.slice(0,18)}…`:saic)}</text></g>`}).join("");
  return `<div class="group-market-panel ${index===0?"active":""}" data-market-panel="${esc(dimension.key)}" ${index===0?"":"hidden"}><div class="group-chart-axis"><span>赛道扩张</span><span>0%</span><span>赛道收缩</span></div><svg class="group-segment-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(dimension.label)}趋势星点图"><line class="zero-line" x1="45" y1="${baseline}" x2="875" y2="${baseline}"/>${points}</svg></div>`;
 }

 function renderSegments(dimensions,positioning){
  const focusKeys=[positioning?.energyRankKey,positioning?.bodyRankKey].filter(Boolean);
  const tabs=dimensions.map((dimension,index)=>`<button type="button" class="${index===0?"active":""}" data-market-dimension="${esc(dimension.key)}" aria-pressed="${index===0}"><b>${esc(dimension.label)}</b><small>${esc(dimension.note)}</small></button>`).join("");
  return `<section class="group-board-section" aria-labelledby="group-segment-title"><header><div><span>01 · MARKET CONTEXT</span><h2 id="group-segment-title">E7X 所在赛道环境</h2><p>默认聚焦${esc(positioning?.energy||"纯电")}与${esc(positioning?.bodyClass||"中大型 SUV")}；百分比仅表示懂车帝细分榜 Top10 销量合计环比。</p></div><em>懂车帝细分榜 Top10 · 非市场份额</em></header><nav class="group-market-tabs" aria-label="市场结构维度">${tabs}</nav><div class="group-chart-frame">${dimensions.map((dimension,index)=>renderDimensionPlot(dimension,index,focusKeys)).join("")}<div class="group-chart-legend"><span><i class="up"></i>Top10合计环比扩张</span><span><i class="down"></i>Top10合计环比收缩</span><span><i class="size"></i>点越大，榜单规模越大</span><span><i class="focus"></i>E7X 所在赛道</span></div></div></section>`;
 }

 function renderCompetitive(evaluation){
  const items=evaluation.models||[],width=920,height=390,left=88,right=870,top=40,bottom=305,maxVoice=Math.max(1,...items.map(item=>item.voice||0)),maxEngagement=Math.max(1,...items.map(item=>item.engagement||0));
  const points=items.map((item,index)=>{const x=left+Math.sqrt((item.voice||0)/maxVoice)*(right-left),y=bottom-(item.overallNsr||0)*(bottom-top),r=11+Math.sqrt((item.engagement||0)/maxEngagement)*11,own=item.isOwn,below=item.model==="问界M7",dx=own?-14:12,anchor=own?"end":"start",labelY=below?y+r+17:y-r-9,metricY=below?labelY+13:labelY+13;return`<g class="group-competitive-point ${own?"own":"competitor"}" tabindex="0" role="img" aria-label="${esc(item.model)}，声量${num(item.voice)}，互动量${num(item.engagement)}，全网NSR${pct(item.overallNsr)}">${own?`<circle class="halo" cx="${x}" cy="${y}" r="${r+12}"/><polygon class="star" points="${starPoints(x,y,r+5,r*.48)}"/>`:`<circle class="halo" cx="${x}" cy="${y}" r="${r+7}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/>`}<text class="model" x="${x+dx}" y="${labelY}" text-anchor="${anchor}">${esc(item.model)}</text><text class="metric" x="${x+dx}" y="${metricY}" text-anchor="${anchor}">${compact(item.voice)} · NSR ${pct(item.overallNsr)}</text></g>`}).join("");
  const own=items.find(item=>item.isOwn)||{};
  return `<section class="group-board-section" aria-labelledby="group-competitive-title"><header><div><span>02 · COMPETITIVE MOMENTUM</span><h2 id="group-competitive-title">E7X 五车传播势能星图</h2><p>横向为声量相对位置，纵向为全网NSR，点越大代表互动量越高。</p></div><em>${esc(evaluation.source?.period||"")} · 五车同口径</em></header><div class="group-chart-frame group-competitive-frame"><svg class="group-competitive-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X与四款竞品传播势能比较"><rect class="quality-zone" x="${left}" y="${top}" width="${right-left}" height="${(bottom-top)*.5}"/><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="axis" x1="${left}" y1="${top}" x2="${left}" y2="${bottom}"/><line class="midline" x1="${left}" y1="${bottom-(bottom-top)*.5}" x2="${right}" y2="${bottom-(bottom-top)*.5}"/><text class="zone-label" x="${right-10}" y="${top+18}" text-anchor="end">高口碑区</text><text class="axis-label" x="${(left+right)/2}" y="360" text-anchor="middle">声量 →</text><text class="axis-label" transform="translate(27 173) rotate(-90)" text-anchor="middle">全网 NSR →</text>${points}</svg><div class="group-chart-legend"><span><i class="e7x-star"></i>E7X 本品</span><span><i class="voc-dot"></i>竞品</span><span>本品声量第${own.voiceRank||"—"} · 互动第${own.engagementRank||"—"} · NSR第${own.overallNsrRank||"—"}</span></div></div></section>`;
 }

 function renderPlatforms(evaluation){
  const items=(evaluation.platforms||[]).filter(item=>item.platform!=="全网"),overall=(evaluation.platforms||[]).find(item=>item.platform==="全网")?.nsr||0,width=920,height=315,left=76,right=860,top=38,bottom=225,maxEngagement=Math.max(1,...items.map(item=>item.engagement||0)),baselineY=bottom-overall*(bottom-top);
  const points=items.map((item,index)=>{const x=left+index*((right-left)/Math.max(1,items.length-1)),y=bottom-item.nsr*(bottom-top),r=9+Math.sqrt((item.engagement||0)/maxEngagement)*12,status=item.nsr>=overall?"above":"below";return`<g class="group-platform-point ${status}" tabindex="0" role="img" aria-label="${esc(item.platform)}，NSR${pct(item.nsr)}，声量${num(item.voice)}，互动量${num(item.engagement)}"><line x1="${x}" y1="${baselineY}" x2="${x}" y2="${y}"/><circle class="halo" cx="${x}" cy="${y}" r="${r+6}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/><text class="value" x="${x}" y="${y-r-9}" text-anchor="middle">${pct(item.nsr)}</text><text class="platform" x="${x}" y="256" text-anchor="middle">${esc(item.platform)}</text><text class="volume" x="${x}" y="272" text-anchor="middle">${compact(item.engagement)}互动</text></g>`}).join("");
  return `<section class="group-board-section" aria-labelledby="group-platform-title"><header><div><span>03 · CHANNEL PERFORMANCE</span><h2 id="group-platform-title">E7X 平台阵地点阵</h2><p>点位高低代表平台NSR，点越大代表互动量越高；虚线为E7X全网NSR。</p></div><em>全网 NSR ${pct(overall)}</em></header><div class="group-chart-frame group-platform-frame"><svg class="group-platform-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X分平台口碑与互动点阵"><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="benchmark" x1="${left}" y1="${baselineY}" x2="${right}" y2="${baselineY}"/><text class="benchmark-label" x="${right}" y="${baselineY-7}" text-anchor="end">全网 ${pct(overall)}</text>${points}</svg><div class="group-chart-legend"><span><i class="up"></i>高于全网NSR</span><span><i class="down"></i>低于全网NSR</span><span>点大小＝互动量</span></div></div></section>`;
 }

 function renderAttributes(evaluation){
  const items=evaluation.attributes||[],width=920,height=400,left=92,right=870,top=42,bottom=310,minX=.25,maxX=1,minY=-.15,maxY=.38,zeroY=bottom-(0-minY)/(maxY-minY)*(bottom-top),thresholdX=left+(.65-minX)/(maxX-minX)*(right-left),offsets=[[-10,-12,"end"],[10,-10,"start"],[-10,-10,"end"],[10,18,"start"],[-10,18,"end"],[10,-10,"start"],[-10,-10,"end"],[10,18,"start"],[-10,18,"end"],[10,-10,"start"],[10,18,"start"],[-10,-10,"end"],[-10,-10,"end"],[10,18,"start"],[10,-10,"start"]];
  const points=items.map((item,index)=>{const x=left+(item.ownNsr-minX)/(maxX-minX)*(right-left),y=bottom-(item.deltaVsAverage-minY)/(maxY-minY)*(bottom-top),status=item.deltaVsAverage<0?"risk":item.ownNsr>=.75?"asset":item.ownNsr<.6?"fragile":"watch",[dx,dy,anchor]=offsets[index]||[10,-10,"start"],label=item.attribute==="动力与操控"?"动力操控":item.attribute;return`<g class="group-attribute-point ${status}" tabindex="0" role="img" aria-label="${esc(item.attribute)}，E7X NSR${pct(item.ownNsr)}，相对五车平均${item.deltaVsAverage>=0?"高":"低"}${pct(Math.abs(item.deltaVsAverage))}"><circle class="halo" cx="${x}" cy="${y}" r="15"/><circle class="dot" cx="${x}" cy="${y}" r="9"/><text x="${x+dx}" y="${y+dy}" text-anchor="${anchor}">${esc(label)}</text></g>`}).join("");
  return `<section class="group-board-section" aria-labelledby="group-attribute-title"><header><div><span>04 · PRODUCT VOC</span><h2 id="group-attribute-title">E7X 产品认知星图</h2><p>横轴是E7X属性NSR，纵轴是相对五车平均的领先程度；点大小不代表样本量。</p></div><em>15项产品属性 · 全网口径</em></header><div class="group-chart-frame group-attribute-frame"><svg class="group-attribute-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X十五项产品属性认知分布"><rect class="asset-zone" x="${thresholdX}" y="${top}" width="${right-thresholdX}" height="${zeroY-top}"/><rect class="risk-zone" x="${left}" y="${zeroY}" width="${thresholdX-left}" height="${bottom-zeroY}"/><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="axis" x1="${left}" y1="${top}" x2="${left}" y2="${bottom}"/><line class="midline" x1="${left}" y1="${zeroY}" x2="${right}" y2="${zeroY}"/><line class="midline" x1="${thresholdX}" y1="${top}" x2="${thresholdX}" y2="${bottom}"/><text class="zone-label asset" x="${right-12}" y="${top+18}" text-anchor="end">高认可 · 相对领先</text><text class="zone-label risk" x="${left+12}" y="${bottom-14}">低认可 · 相对落后</text><text class="axis-label" x="${(left+right)/2}" y="365" text-anchor="middle">E7X 属性 NSR →</text><text class="axis-label" transform="translate(27 176) rotate(-90)" text-anchor="middle">相对五车平均领先 →</text>${points}</svg><div class="group-chart-legend"><span><i class="attribute-asset"></i>优势资产</span><span><i class="attribute-watch"></i>相对领先但仍需建设</span><span><i class="attribute-risk"></i>低于五车平均</span></div></div></section>`;
 }

 function render(data){
  const evaluation=data.productEvaluation||{},own=(evaluation.models||[]).find(item=>item.isOwn)||{},source=evaluation.source||{};
  const views=[
   {key:"market",label:"赛道环境",content:renderSegments(data.marketDimensions||[],evaluation.positioning||{})},
   {key:"competitive",label:"传播势能",content:renderCompetitive(evaluation)},
   {key:"platform",label:"平台阵地",content:renderPlatforms(evaluation)},
   {key:"attribute",label:"产品 VOC",content:renderAttributes(evaluation)}
  ];
  root.innerHTML=`<div class="group-dashboard-shell group-dashboard-onepage"><section class="group-dashboard-hero group-e7x-hero"><div><p>SAIC GROUP · MANAGEMENT VIEW</p><h2>集团营销经营驾驶舱 <span>E7X DEMO</span></h2><small>本品：奥迪E7X · ${esc(evaluation.positioning?.energy||"纯电")} · ${esc(evaluation.positioning?.bodyClass||"中大型 SUV")} · ${esc(source.period||"")}</small></div><div class="group-dashboard-actions"><span><i></i>${esc(data.meta?.dataMode||"Beta")}</span><button type="button" id="group-dashboard-refresh">刷新</button></div></section><section class="group-kpi-strip" aria-label="奥迪E7X核心传播指标"><article><span>本品声量</span><strong>${compact(own.voice)}</strong><small>五车第 ${own.voiceRank||"—"}</small></article><article><span>本品互动量</span><strong>${compact(own.engagement)}</strong><small>五车第 ${own.engagementRank||"—"}</small></article><article><span>全网 NSR</span><strong>${pct(own.overallNsr)}</strong><small>五车第 ${own.overallNsrRank||"—"}</small></article><article><span>垂媒车主口碑 NSR</span><strong>${pct(own.verticalNsr)}</strong><small>有效样本第 ${own.verticalNsrRank||"—"}/${evaluation.validVerticalModels||"—"}</small></article></section><aside class="group-source-strip"><div><span>数据来源</span><b>${esc(source.fileName||"产品评价工作簿")}</b></div><p>声量、互动量、NSR沿用源表定义；社媒证据不等于市场需求或销量。</p></aside><nav class="group-view-tabs" role="tablist" aria-label="管理层看板视图">${views.map((view,index)=>`<button type="button" id="group-view-tab-${view.key}" role="tab" data-group-view="${view.key}" aria-controls="group-view-panel-${view.key}" aria-selected="${index===0}" class="${index===0?"active":""}"><span>0${index+1}</span>${view.label}</button>`).join("")}</nav><div class="group-view-deck" tabindex="0" aria-label="可左右滑动切换看板">${views.map((view,index)=>`<div id="group-view-panel-${view.key}" class="group-view-panel ${index===0?"active":""}" role="tabpanel" data-group-panel="${view.key}" aria-labelledby="group-view-tab-${view.key}" ${index===0?"":"hidden"}>${view.content}</div>`).join("")}</div><footer class="group-view-footer"><button type="button" class="group-view-arrow" data-group-view-prev aria-label="上一视图">←</button><span data-group-view-progress>1 / ${views.length}</span><small>点击按钮或左右滑动</small><button type="button" class="group-view-arrow" data-group-view-next aria-label="下一视图">→</button></footer></div>`;
  root.querySelector("#group-dashboard-refresh")?.addEventListener("click",()=>load(true));
  root.querySelectorAll("[data-page-jump]").forEach(button=>button.addEventListener("click",()=>window.showPage?.(button.dataset.pageJump)));
  root.querySelectorAll("[data-market-dimension]").forEach(button=>button.addEventListener("click",()=>{const key=button.dataset.marketDimension;root.querySelectorAll("[data-market-dimension]").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active))});root.querySelectorAll("[data-market-panel]").forEach(panel=>{const active=panel.dataset.marketPanel===key;panel.hidden=!active;panel.classList.toggle("active",active)})}));
  const viewKeys=views.map(view=>view.key),deck=root.querySelector(".group-view-deck"),progress=root.querySelector("[data-group-view-progress]");
  let activeView=0,pointerStartX=null;
  const activateView=(next,focus=false)=>{activeView=(next+viewKeys.length)%viewKeys.length;const key=viewKeys[activeView];root.querySelectorAll("[data-group-view]").forEach(button=>{const active=button.dataset.groupView===key;button.classList.toggle("active",active);button.setAttribute("aria-selected",String(active));if(active&&focus)button.focus()});root.querySelectorAll("[data-group-panel]").forEach(panel=>{const active=panel.dataset.groupPanel===key;panel.hidden=!active;panel.classList.toggle("active",active)});if(progress)progress.textContent=`${activeView+1} / ${viewKeys.length}`};
  root.querySelectorAll("[data-group-view]").forEach((button,index)=>button.addEventListener("click",()=>activateView(index)));
  root.querySelector("[data-group-view-prev]")?.addEventListener("click",()=>activateView(activeView-1));
  root.querySelector("[data-group-view-next]")?.addEventListener("click",()=>activateView(activeView+1));
  deck?.addEventListener("keydown",event=>{if(event.key==="ArrowLeft"||event.key==="ArrowRight"){event.preventDefault();activateView(activeView+(event.key==="ArrowLeft"?-1:1),true)}});
  deck?.addEventListener("pointerdown",event=>{if(event.isPrimary!==false)pointerStartX=event.clientX});
  deck?.addEventListener("pointerup",event=>{if(pointerStartX===null)return;const delta=event.clientX-pointerStartX;pointerStartX=null;if(Math.abs(delta)>=48)activateView(activeView+(delta<0?1:-1))});
 }

 function renderError(error){
  root.innerHTML=`<div class="group-dashboard-error" role="alert"><span>集团看板暂未加载</span><b>${esc(error?.message||"数据接口不可用")}</b><button type="button" id="group-dashboard-retry">重新连接</button></div>`;
  root.querySelector("#group-dashboard-retry")?.addEventListener("click",()=>load(true));
 }

 async function load(force=false){
  const currentEdition=document.querySelector("[data-edition].active")?.dataset.edition||"china";
  if(currentEdition!=="china"){
   loadedEdition=currentEdition;
   root.innerHTML='<div class="group-dashboard-error" role="status"><span>国内版专属看板</span><b>上汽集团营销看板 Demo 仅使用国内版数据，已与出海版数据隔离。</b></div>';
   return;
  }
  if(loading||(!force&&loadedEdition===currentEdition))return;
  loading=true;skeleton();
  try{
   const response=await fetch(`/api/group-dashboard-demo?edition=${encodeURIComponent(currentEdition)}`,{credentials:"same-origin"});
   const data=await response.json();
   if(!response.ok||!data.ok)throw new Error(data.error||`HTTP ${response.status}`);
   loadedEdition=currentEdition;render(data);
  }catch(error){renderError(error)}finally{loading=false}
 }

 window.loadGroupDashboardDemo=load;
})();
