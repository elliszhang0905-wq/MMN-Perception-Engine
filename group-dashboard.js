(function(){
 const root=document.querySelector("#group-dashboard-root");
 if(!root)return;
 let loading=false,loadedEdition="";
 const uiState={viewKey:"brief",brand:"",vehicleId:"",marketDimension:""};
 const esc=value=>String(value??"").replace(/[&<>'"]/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
 const safeHighlight=(text,highlights=[])=>{
  const source=String(text??""),ranges=[];
  (Array.isArray(highlights)?highlights:[]).slice(0,4).forEach((item,index)=>{
   const quote=String(typeof item==="string"?item:item?.quote||"").trim(),level=typeof item==="object"&&item?.level==="secondary"?"secondary":index===0?"primary":"secondary",start=source.indexOf(quote);
   if(!quote||start<0||ranges.some(range=>start<range.end&&start+quote.length>range.start))return;
   ranges.push({start,end:start+quote.length,level});
  });
  ranges.sort((a,b)=>a.start-b.start);
  let cursor=0;
  return ranges.map(range=>{const before=esc(source.slice(cursor,range.start)),marked=`<mark class="mmn-highlight ${range.level}">${esc(source.slice(range.start,range.end))}</mark>`;cursor=range.end;return before+marked}).join("")+esc(source.slice(cursor));
 };
 const num=value=>Number(value||0).toLocaleString("zh-CN");
 const compact=value=>Number(value||0)>=10000?`${(Number(value)/10000).toFixed(1)}万`:num(value);
 const pct=value=>value===null||value===undefined?"暂无":`${(Number(value)*100).toFixed(1)}%`;
 const rate=value=>value===null||value===undefined?"暂无环比":`${value>=0?"+":""}${(value*100).toFixed(1)}%`;
 const rateClass=value=>value===null||value===undefined?"flat":value>=0?"up":"down";
 const starPoints=(cx,cy,outer,inner)=>Array.from({length:10},(_,index)=>{const radius=index%2?inner:outer,angle=-Math.PI/2+index*Math.PI/5;return`${cx+Math.cos(angle)*radius},${cy+Math.sin(angle)*radius}`}).join(" ");

 function skeleton(){
  root.innerHTML=`<div class="group-dashboard-loading" role="status" aria-live="polite"><b>正在聚合集团看板数据</b><span></span><span></span><span></span></div>`;
 }

 const executivePulse={
  period:"2026年7月1—12日",
  sourceUrl:"https://www.cpcaauto.com/newslist.php?types=csjd&id=4272",
  sourceLabel:"乘联会《周度分析｜车市扫描（20260706—0712）》",
  retail:"44.3万",retailYoy:"-15%",nevRetail:"28.0万",nevPenetration:"63.1%"
 };

 const groupBrandImplications=[
  {brand:"智己",category:"高端新能源",title:"智己",summary:"智己承担集团高端新能源心智突破任务。在新能源渗透率维持高位、行业总量承压的环境下，不应继续只讲参数领先，而要把技术优势转译成用户愿意换购的豪华体验、补能便利与智能场景价值。",action:"围绕核心车型建立“人群—场景—产品证据”内容链，集中解释底盘、智驾、座舱与补能体验；对高意向人群强化试驾、换购政策和真实车主证言，减少技术名词的自我表达。",signal:"持续观察品牌搜索、试驾线索、优势属性提及率、换购人群占比与高意向评论变化。",status:"机会｜优先建立确定性认知",tone:"opportunity"},
  {brand:"MG",category:"全球与年轻化品牌",title:"MG",summary:"MG需要同时管理国内年轻化价值与全球业务交付。国内不能只依赖性价比和运动标签，海外也不能只报告出口总量，必须把重点区域的真实需求、库存、运力、价格和交付节奏放在同一张经营图里。",action:"国内按年轻用户的通勤、旅行和个性表达组织内容；海外按区域市场拆分车型、渠道与交付信息，传播排期必须与现车、上市节点和经销商承接能力同步。",signal:"持续观察国内品牌搜索与年轻人群互动，海外重点追踪区域订单、库存周转、交付周期、运价及终端价格稳定性。",status:"任务｜国内价值建设与海外交付并行",tone:"watch"},
  {brand:"荣威",category:"主流乘用车",title:"荣威",summary:"荣威应承担集团主流家庭换购与大众新能源需求的承接任务。当前最重要的不是继续放大优惠，而是重新说明空间、舒适、可靠、能耗与长期使用成本，建立家庭用户可理解、可比较的购买确定性。",action:"以家庭通勤、亲子出行和跨城使用为主场景，形成与同价位竞品的证据化对比；优惠信息只作为成交辅助，不再替代产品价值、品质保障和售后服务表达。",signal:"持续观察家庭人群内容渗透、核心产品点NSR、到店试驾、换购线索、价格敏感评论与成交转化变化。",status:"任务｜强化产品价值而非价格刺激",tone:"watch"},
  {brand:"大众",category:"合资主流品牌",title:"上汽大众",summary:"上汽大众需要一边稳住燃油车规模与存量用户，一边加快新能源产品的认知转换。管理层应避免把两类业务混成同一套销量或传播逻辑：燃油车强调可靠与保有体验，新能源重点回答智能化和本土场景适配。",action:"燃油产品围绕品质、保值、服务网络和换购权益稳定基本盘；新能源产品强化智能座舱、辅助驾驶、补能与空间体验，用真实对比消除用户对合资新能源“智能不足”的惯性判断。",signal:"持续观察燃油换购留存率、新能源搜索占比、智能化属性NSR、试驾线索以及燃油与新能源用户的相互迁移。",status:"任务｜稳定基本盘并推进新能源转化",tone:"watch"},
  {brand:"AUDI",category:"豪华新能源",title:"上汽奥迪",summary:"上汽奥迪需要借E7X等新能源产品建立新的豪华购买理由。传统品牌认知可以提供信任，但不能自动转化为新能源选择，必须让用户清楚看到设计、驾控、智能、舒适与场景体验相对新势力的具体差异。",action:"围绕E7X建立“总体声量—平台NSR—产品属性VOC—竞品差距”的传播闭环；优先放大已经领先的产品资产，对认知偏弱的平台和属性单独设计内容语言、达人类型与试驾证据。",signal:"持续观察E7X总体声量、全网与分平台NSR、核心属性提及率、竞品共同比较率、试驾预约和豪华新能源人群渗透。",status:"机会｜放大新能源差异化资产",tone:"opportunity"},
  {brand:"别克",category:"合资主流品牌",title:"上汽通用别克",summary:"别克需要在家庭出行优势与新能源转型之间重新建立价值连接。长期促销容易让用户只记住价格变化，管理层应把舒适、空间、品质、服务和新能源使用体验重新组织成清晰的家庭购买理由。",action:"针对家庭用户分别设计燃油、插混和纯电产品的场景化证据，明确不同能源形式的适用人群与使用成本；减少泛化优惠传播，增加车主口碑、长期用车和服务保障内容。",signal:"持续观察家庭人群好感、能源形式认知、价格负面评论、核心属性NSR、到店试驾与置换成交的变化。",status:"任务｜重建家庭用户购买确定性",tone:"watch"},
  {brand:"凯迪拉克",category:"豪华品牌",title:"上汽通用凯迪拉克",summary:"凯迪拉克的核心风险是价格信息持续压过豪华价值，进而影响品牌认知、保值预期与老用户信心。新能源转型期更需要同步解释技术、体验和服务，而不是仅用折扣降低决策门槛。",action:"控制价格信息在传播中的占比，强化设计、驾控、舒适、静谧和服务体验；新能源产品应增加真实场景试驾与技术证据，形成与同级豪华品牌和新势力的差异化理由。",signal:"持续观察价格相关声量占比、豪华属性NSR、保值焦虑评论、老用户情绪、试驾线索与新能源产品的品牌迁移率。",status:"风险｜避免价格叙事侵蚀豪华价值",tone:"risk"},
  {brand:"大通",category:"商用、皮卡与出海",title:"上汽大通",summary:"上汽大通需要把商用、皮卡和海外增长转化为可执行的区域与车型机会。出口总量只能说明规模，不能替代对订单质量、运力、区域库存、渠道能力和利润波动的经营判断。",action:"按重点国家和区域建立车型机会清单，传播内容与当地行业、使用场景和经销商能力对应；同时把滚装运力、交付周期、库存和终端价格纳入周度监测。",signal:"持续观察区域订单、车型结构、交付周期、运价、库存周转、终端价格与重点市场的内容反馈。",status:"机会｜建立海外市场优先级",tone:"opportunity"},
  {brand:"五菱",category:"国民品牌与新能源普及",title:"上汽通用五菱",summary:"五菱已经具备广泛的国民认知与新能源规模基础，下一步重点是从“卖得多、价格亲民”升级为“产品值得长期信任”。传播需要同步强化品质、安全、空间、能耗和家庭场景价值。",action:"围绕代步、接送、家庭短途和县域出行建立真实用户内容，突出低使用成本之外的品质与安全证据；对主力新能源车型持续沉淀车主口碑，避免新品之间相互稀释认知。",signal:"持续观察新能源规模、品质与安全NSR、真实车主口碑、县域人群覆盖、复购换购和主力车型认知集中度。",status:"机会｜从规模领先转向价值巩固",tone:"opportunity"}
 ];

 const groupBrandHighlights={
  "智己":{summary:[{quote:"用户愿意换购",level:"primary"},{quote:"不应继续只讲参数领先",level:"secondary"},{quote:"技术优势转译",level:"secondary"}],action:[{quote:"人群—场景—产品证据",level:"primary"}],signal:[{quote:"试驾线索",level:"primary"},{quote:"换购人群占比",level:"secondary"}]},
  "MG":{summary:[{quote:"真实需求、库存、运力、价格和交付节奏",level:"primary"}],action:[{quote:"与现车、上市节点和经销商承接能力同步",level:"primary"}],signal:[{quote:"区域订单、库存周转、交付周期",level:"primary"}]},
  "荣威":{summary:[{quote:"家庭用户可理解、可比较的购买确定性",level:"primary"}],action:[{quote:"产品价值、品质保障和售后服务表达",level:"primary"}],signal:[{quote:"核心产品点NSR",level:"primary"}]},
  "大众":{summary:[{quote:"燃油车强调可靠与保有体验",level:"primary"}],action:[{quote:"新能源产品强化智能座舱、辅助驾驶、补能与空间体验",level:"primary"}],signal:[{quote:"新能源搜索占比",level:"primary"}]},
  "AUDI":{summary:[{quote:"新的豪华购买理由",level:"primary"}],action:[{quote:"放大已经领先的产品资产",level:"primary"}],signal:[{quote:"核心属性提及率",level:"primary"}]},
  "别克":{summary:[{quote:"清晰的家庭购买理由",level:"primary"}],action:[{quote:"增加车主口碑、长期用车和服务保障内容",level:"primary"}],signal:[{quote:"核心属性NSR",level:"primary"}]},
  "凯迪拉克":{summary:[{quote:"价格信息持续压过豪华价值",level:"primary"}],action:[{quote:"控制价格信息在传播中的占比",level:"primary"}],signal:[{quote:"保值焦虑评论",level:"primary"}]},
  "大通":{summary:[{quote:"可执行的区域与车型机会",level:"primary"}],action:[{quote:"建立车型机会清单",level:"primary"}],signal:[{quote:"区域订单",level:"primary"}]},
  "五菱":{summary:[{quote:"产品值得长期信任",level:"primary"}],action:[{quote:"品质与安全证据",level:"primary"}],signal:[{quote:"真实车主口碑",level:"primary"}]}
 };

 const decisionStateCopy={
  opportunity:{summary:"机会放大｜优势势能正在形成",action:"机会放大｜优先加码有效表达",signal:"正向验证｜持续放大有效信号"},
  watch:{summary:"重点补强｜关键认知仍需加强",action:"重点补强｜传播任务需要加速",signal:"重点监测｜关键指标需加密追踪"},
  risk:{summary:"紧急行动｜重大认知风险需立即干预",action:"紧急行动｜立即启动传播修复",signal:"风险监测｜进入高频复盘机制"}
 };
 const renderDecisionState=(item,section)=>{
  const state=item.states?.[section]||{},tone=state.tone||item.tone||"watch",label=state.label||decisionStateCopy[tone]?.[section]||decisionStateCopy.watch[section];
  return `<small class="decision-state ${esc(tone)}"><i aria-hidden="true"></i>${esc(label)}</small>`;
 };

function renderExecutiveFactChart(fact){
  const current=Number(fact?.value||0),prior=Number(fact?.priorValue||0),max=Math.max(1,current,prior),currentHeight=28+current/max*82,priorHeight=28+prior/max*82,baseline=137,yoy=Number(fact?.yoy||0),direction=yoy>=0?"增长":"下降",tone=yoy>=0?"positive":"negative";
  return `<article class="executive-yoy-card ${tone}" role="img" aria-label="${esc(fact?.label)}，2026年7月1至12日${current.toFixed(1)}万辆，2025年同期反算${prior.toFixed(1)}万辆，同比${direction}${Math.abs(yoy*100).toFixed(0)}%"><span>${esc(fact?.label)}</span><strong>同比${direction} ${Math.abs(yoy*100).toFixed(0)}%</strong><svg viewBox="0 0 220 175" aria-hidden="true"><line class="bar-baseline" x1="20" y1="${baseline}" x2="200" y2="${baseline}"/><rect class="current-bar vertical-bar" x="45" y="${baseline-currentHeight}" width="48" height="${currentHeight}" rx="4"/><text class="bar-value" x="69" y="${baseline-currentHeight-7}" text-anchor="middle">${current.toFixed(1)}</text><rect class="prior-bar vertical-bar" x="127" y="${baseline-priorHeight}" width="48" height="${priorHeight}" rx="4"/><text class="bar-value" x="151" y="${baseline-priorHeight-7}" text-anchor="middle">${prior.toFixed(1)}</text><text class="bar-label" x="69" y="158" text-anchor="middle">2026年7月</text><text class="bar-label" x="151" y="158" text-anchor="middle">2025年7月</text></svg><small>单位：万辆 · 均为1—12日同期口径 · 2025年按同比反算</small></article>`;
}

function renderExecutiveOverview(brief){
  const facts=brief?.facts||[],source=brief?.source||{period:executivePulse.period,url:executivePulse.sourceUrl,label:executivePulse.sourceLabel},verified=brief?.status==="verified",summary=verified?esc(brief.summary).replace("63.1%","<b>63.1%</b>"):"双旗舰模型交叉验证尚未完成，本周摘要暂不发布。",inferences=verified?(brief?.inferences||[]):[],pressure=inferences.filter(item=>item.id!=="penetration_buffer"),buffer=inferences.find(item=>item.id==="penetration_buffer");
  const inferenceContent=verified?`<ol class="executive-causal-chain">${pressure.map(item=>`<li><b>${esc(item.title)}</b><small>${esc(item.detail)}</small></li>`).join("")}</ol>${buffer?`<div class="executive-buffer"><span>${esc(buffer.title)}</span><b>${esc(buffer.detail)}</b></div>`:""}`:`<div class="executive-inference-pending">双旗舰模型交叉验证完成前，MMN模型推论暂不发布。</div>`;
  return `<section class="group-board-section group-executive-section" aria-labelledby="group-executive-title"><header><div><span>01 · EXECUTIVE BRIEF</span><h2 id="group-executive-title">市场在降温，但新能源仍在扩大结构性优势</h2><p>事实数字锁定后，由双旗舰模型独立验证；只有两路交叉验证一致通过才发布摘要。</p></div><em>${esc(source.period||executivePulse.period)} · 周度快照</em></header><div class="executive-brief-grid"><article class="executive-thesis ${verified?"verified":"pending"}"><div class="executive-proof-row"><span class="executive-proof-tag">本周一句话</span><span class="executive-review-status ${verified?"verified":"pending"}">${verified?"✓ ":"◷ "}${esc(brief?.statusLabel||"双旗舰模型交叉验证中 · 暂不发布")}</span></div><h3>${summary}</h3><div class="executive-fact-charts">${facts.filter(fact=>fact.id!=="nev_penetration").map(renderExecutiveFactChart).join("")}</div></article><aside class="executive-causal-card"><div class="executive-card-heading"><span>市场结构推论</span><small class="executive-inference-status ${verified?"verified":"pending"}">${verified?"MMN模型推论 · 已通过双旗舰模型交叉验证":"MMN模型推论 · 交叉验证中"}</small></div>${inferenceContent}</aside></div><footer class="executive-source-line"><span>事实来源</span><a href="${esc(source.url||executivePulse.sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(source.label||executivePulse.sourceLabel)}</a><small>${verified?"双旗舰模型已引用同一事实包":"未通过前不展示策略摘要与MMN模型推论"} · 同期值按同比反算</small></footer></section>`;
}

 function renderGroupImplications(){
  const selectedBrand=groupBrandImplications.some(item=>item.brand===uiState.brand)?uiState.brand:groupBrandImplications[0]?.brand||"";
  uiState.brand=selectedBrand;
  const options=groupBrandImplications.map(item=>`<option value="${esc(item.brand)}" ${item.brand===selectedBrand?"selected":""}>${esc(item.brand)}</option>`).join(""),panels=groupBrandImplications.map(item=>{const highlights=groupBrandHighlights[item.brand]||{};return`<article class="executive-brand-panel" data-brand-panel="${esc(item.brand)}" ${item.brand===selectedBrand?"":"hidden"}><span>${esc(item.category)}</span><h3>${esc(item.title)}</h3><div class="executive-brand-narrative"><article class="executive-brand-narrative-card"><b>集团判断</b><p>${safeHighlight(item.summary,highlights.summary)}</p>${renderDecisionState(item,"summary")}</article><article class="executive-brand-narrative-card"><b>传播动作</b><p>${safeHighlight(item.action,highlights.action)}</p>${renderDecisionState(item,"action")}</article><article class="executive-brand-narrative-card"><b>复盘信号</b><p>${safeHighlight(item.signal,highlights.signal)}</p>${renderDecisionState(item,"signal")}</article></div></article>`}).join("");
  return `<section class="group-board-section group-executive-section" aria-labelledby="group-implication-title"><header><div><span>02 · GROUP IMPLICATIONS</span><h2 id="group-implication-title">把行业变化翻译成上汽的品牌判断</h2><p>选择集团品牌，查看对应的集团判断、传播动作与复盘信号。</p></div><em>MMN Demo 判断 · 待集团经营数据校准</em></header><div class="executive-impact-layout"><div class="executive-brand-switcher"><label for="group-brand-select"><span>选择品牌</span><select id="group-brand-select" aria-label="选择集团品牌">${options}</select></label><div class="executive-brand-stage" aria-live="polite">${panels}</div></div></div></section>`;
 }

 function renderExecutiveActions(brief){
  const verified=brief?.status==="verified",actions=brief?.actions||[],vehicleActions=brief?.vehicleActions||[],byId=Object.fromEntries(actions.map(item=>[item.id,item])),p1=byId.p1||{},p3=byId.p3||{},selected=vehicleActions.find(item=>item.id===uiState.vehicleId)||vehicleActions.find(item=>item.selected)||vehicleActions[0]||{};
  if(!verified)return `<section class="group-board-section group-executive-section" aria-labelledby="group-action-title"><header><div><span>03 · THIS WEEK'S MOVES</span><h2 id="group-action-title">本周只推动三件事</h2><p>P1—P3必须由双旗舰模型对同一事实包交叉验证通过后才发布。</p></div><em>双旗舰模型交叉验证中</em></header><div class="executive-inference-pending">交叉验证完成前，本周动作与MMN推导结论暂不发布。</div></section>`;
  const actionCard=(action,priority)=>`<article class="${priority===1?"priority-one":""}"><div class="executive-action-top"><span class="executive-action-no">P${priority}</span><span class="executive-action-verification">✓ 双旗舰模型交叉验证已通过</span></div><div><small>${esc(action.scope)}</small><h3>${esc(action.title)}</h3><b class="executive-action-conclusion">MMN推导结论</b><p>${esc(action.conclusion)}</p></div><footer><b>复盘信号</b><span>${esc(action.reviewSignal)}</span></footer></article>`;
  uiState.vehicleId=selected.id||"";
  const options=vehicleActions.map(item=>`<option value="${esc(item.id)}" ${item.id===selected.id?"selected":""}>${esc(item.brand)} · ${esc(item.model)}</option>`).join("");
  const panels=vehicleActions.map(item=>`<div class="executive-vehicle-action" data-action-vehicle-panel="${esc(item.id)}" ${item.id===selected.id?"":"hidden"}><small>${esc(item.brand)} · ${esc(item.stage)} · ${esc(item.dataStatus)}</small><h3>${esc(item.title)}</h3><b class="executive-action-conclusion">MMN推导结论</b><p>${esc(item.conclusion)}</p><footer><b>复盘信号</b><span>${esc(item.reviewSignal)}</span></footer></div>`).join("");
  return `<section class="group-board-section group-executive-section" aria-labelledby="group-action-title"><header><div><span>03 · THIS WEEK'S MOVES</span><h2 id="group-action-title">本周只推动三件事</h2><p>P1—P3与全部同期重点车型结论均引用同一锁定事实包，并由双旗舰模型独立交叉验证。</p></div><em>✓ 双旗舰模型交叉验证已通过</em></header><div class="executive-action-grid">${actionCard(p1,1)}<article class="executive-action-vehicle-card"><div class="executive-action-top"><span class="executive-action-no">P2</span><label class="executive-vehicle-select"><span>同期上市重点车型</span><select id="executive-vehicle-action-select" aria-label="选择同期上市重点车型">${options}</select></label></div><span class="executive-action-verification">✓ 双旗舰模型交叉验证已通过</span><div class="executive-vehicle-action-stage">${panels}</div></article>${actionCard(p3,3)}</div><div class="executive-evidence-note"><b>证据边界</b><span>乘联会数据用于行业态势；社媒与 VOC 仅用于传播认知判断，不作为市场需求证明。车型动作只使用已接入的同口径声量、NSR与VOC；标记“专项数据待接入”的车型只发布证据建设任务。</span></div></section>`;
 }

 function renderDimensionPlot(dimension,selectedKey,focusKeys){
  const items=dimension.items||[],width=920,height=190,baseline=56;
  const maxAbs=Math.max(.2,...items.map(item=>Math.abs(item.changeRate||0)));
  const maxSales=Math.max(1,...items.filter(item=>item.dataBasis!=="cpca_ice_retail_market").map(item=>item.top10Sales||0));
  const points=items.map((item,pointIndex)=>{
   const missing=item.status!=="available",derived=item.dataBasis==="overall_top10_minus_new_energy",cpca=item.dataBasis==="cpca_ice_retail_market",basisChanged=item.comparisonBasisChanged===true,focused=focusKeys.includes(item.key);
   const x=85+pointIndex*((width-170)/Math.max(1,items.length-1)),change=item.changeRate||0,y=missing?baseline:baseline-change/maxAbs*36,r=missing?13:cpca?19:10+Math.sqrt((item.top10Sales||0)/maxSales)*12,deltaY=Math.max(14,y-r-10);
   const saic=(item.saicTop10||[]).map(row=>`${row.model} #${row.rank}`).join(" / ")||"本期未进入",marketPeriod=item.latestPeriod||"月份待确认",saicPeriod=item.saicRankPeriod||"月份待确认",stale=item.sourceStale===true,rankMissing=cpca&&item.saicRankBasis==="missing";
   const delta=missing?"待接入":cpca?`${rate(item.changeRate)}${stale?" · 缓存":""}`:basisChanged?(derived?"总榜推导 · 口径切换":"口径切换"):derived?"总榜推导":rate(item.changeRate);
   const sales=missing?"独立榜暂无":cpca?`乘联会 ${compact(item.marketSales)} · ${marketPeriod}`:num(item.top10Sales);
   const saicHeading=rankMissing?"懂车帝车型榜待接入":cpca?(item.saicRankBasis==="dongchedi_fuel_top10"?"懂车帝燃油榜中的上汽车型":"全国总榜中的上汽车型"):"上汽集团 Top10 车型";
   const saicWithPeriod=rankMissing?"暂无可核对车型名次":cpca?`${saic} · ${saicPeriod}`:saic;
   const saicLabel=missing?"本期未进入":saicWithPeriod.length>22?`${saicWithPeriod.slice(0,22)}…`:saicWithPeriod;
   const metricLabel=cpca?`乘联会 ICE 零售${marketPeriod}环比${rate(item.changeRate)}，销量${num(item.marketSales)}，份额${pct(item.marketShare)}${stale?"，当前使用24小时内成功缓存":""}；${rankMissing?"懂车帝车型榜待接入，暂无可核对上汽车型名次":`${saicHeading}${saic}，榜单月份${saicPeriod}`}`:basisChanged?`前后期口径切换，不计算环比，Top10合计${num(item.top10Sales)}`:derived?`全国总榜Top10内燃油车型合计${num(item.top10Sales)}`:`环比${rate(item.changeRate)}，Top10合计${num(item.top10Sales)}`;
   return`<g class="group-star-point ${missing?"missing":rateClass(item.changeRate)} ${cpca?"cpca-market":""} ${focused?"focus":""}" tabindex="0" role="img" aria-label="${esc(item.label)}，${focused?"奥迪E7X所在赛道，":""}${missing?"独立榜待接入":metricLabel}\"><line x1="${x}" y1="${baseline}" x2="${x}" y2="${y}"/><circle class="halo" cx="${x}" cy="${y}" r="${r+7}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/>${focused?`<circle class="focus-ring" cx="${x}" cy="${y}" r="${r+12}"/><text class="focus-tag" x="${x}" y="108" text-anchor="middle">E7X 所在赛道</text>`:""}<text class="delta" x="${x}" y="${deltaY}" text-anchor="middle">${esc(delta)}</text><text class="segment" x="${x}" y="126" text-anchor="middle">${esc(item.label)}</text><text class="sales" x="${x}" y="146" text-anchor="middle">${esc(sales)}</text><text class="saic-heading" x="${x}" y="165" text-anchor="middle">${esc(saicHeading)}</text><text class="saic" x="${x}" y="184" text-anchor="middle">${esc(saicLabel)}</text></g>`;
  }).join("");
  return `<div class="group-market-panel ${dimension.key===selectedKey?"active":""}" data-market-panel="${esc(dimension.key)}" ${dimension.key===selectedKey?"":"hidden"}><div class="group-chart-axis"><span>销量环比扩张</span><span>0%</span><span>销量环比收缩</span></div><svg class="group-segment-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(dimension.label)}销量趋势星点图"><line class="zero-line" x1="45" y1="${baseline}" x2="875" y2="${baseline}"/>${points}</svg></div>`;
 }

 function renderSegments(dimensions,positioning){
  const focusKeys=[positioning?.energyRankKey,positioning?.bodyRankKey].filter(Boolean),selectedKey=dimensions.some(item=>item.key===uiState.marketDimension)?uiState.marketDimension:dimensions[0]?.key||"";
  uiState.marketDimension=selectedKey;
  const tabs=dimensions.map(dimension=>`<button type="button" class="${dimension.key===selectedKey?"active":""}" data-market-dimension="${esc(dimension.key)}" aria-pressed="${dimension.key===selectedKey}"><b>${esc(dimension.label)}</b><small>${esc(dimension.note)}</small></button>`).join("");
  return `<section class="group-board-section" aria-labelledby="group-segment-title"><header><div><span>04 · MARKET CONTEXT</span><h2 id="group-segment-title">E7X 所在销量赛道环境</h2><p>纯电、插混与增程采用懂车帝 Top10；燃油采用乘联会 ICE 零售整体市场。纵向只比较各自同口径环比方向，不对不同来源的绝对规模做横向比较；默认聚焦${esc(positioning?.energy||"纯电")}与${esc(positioning?.bodyClass||"中大型 SUV")}。</p></div><em>双源销量口径 · 懂车帝 + 乘联会</em></header><nav class="group-market-tabs" aria-label="销量赛道维度">${tabs}</nav><div class="group-chart-frame"><div class="group-chart-legend group-chart-legend-explicit"><span><i class="up"></i><b>绿色</b>＝销量环比扩张</span><span><i class="down"></i><b>红色</b>＝销量环比收缩</span><span><i class="missing"></i><b>金色虚线</b>＝数据待接入</span><span><i class="size"></i>点大小＝懂车帝Top10规模；燃油为固定标记</span><span><i class="focus"></i>E7X 所在赛道</span></div>${dimensions.map(dimension=>renderDimensionPlot(dimension,selectedKey,focusKeys)).join("")}</div></section>`;
 }

 function renderCompetitive(evaluation){
  const items=evaluation.models||[],width=920,height=205,left=88,right=870,top=14,bottom=140,maxVoice=Math.max(1,...items.map(item=>item.voice||0)),maxEngagement=Math.max(1,...items.map(item=>item.engagement||0));
  const points=items.map((item,index)=>{const x=left+Math.sqrt((item.voice||0)/maxVoice)*(right-left),y=bottom-(item.overallNsr||0)*(bottom-top),r=11+Math.sqrt((item.engagement||0)/maxEngagement)*11,own=item.isOwn,below=item.model==="问界M7",rightEdge=x>right-120,dx=own||rightEdge?-14:12,anchor=own||rightEdge?"end":"start",labelY=(below?y+r+17:y-r-9)+(rightEdge?-22:0),metricY=labelY+17;return`<g class="group-competitive-point ${own?"own":"competitor"}" tabindex="0" role="img" aria-label="${esc(item.model)}，声量${num(item.voice)}，互动量${num(item.engagement)}，全网NSR${pct(item.overallNsr)}">${own?`<circle class="halo" cx="${x}" cy="${y}" r="${r+12}"/><polygon class="star" points="${starPoints(x,y,r+5,r*.48)}"/>`:`<circle class="halo" cx="${x}" cy="${y}" r="${r+7}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/>`}<text class="model" x="${x+dx}" y="${labelY}" text-anchor="${anchor}">${esc(item.model)}</text><text class="metric" x="${x+dx}" y="${metricY}" text-anchor="${anchor}">${compact(item.voice)} · NSR ${pct(item.overallNsr)}</text></g>`}).join("");
  const own=items.find(item=>item.isOwn)||{};
  return `<section class="group-board-section" aria-labelledby="group-competitive-title"><header><div><span>05 · COMPETITIVE MOMENTUM</span><h2 id="group-competitive-title">E7X 五车传播势能：先声量，后 NSR</h2><p>先用总体声量判断传播规模，再用全网NSR判断这份规模形成正向资产还是负向风险；互动量仅补充活跃度。</p></div><em>${esc(evaluation.source?.period||"")} · 五车同口径</em></header><div class="group-chart-frame group-competitive-frame"><div class="group-decision-order" aria-label="传播势能判断顺序"><span><b>① 总体声量</b> 有没有形成传播规模</span><span><b>② 全网 NSR</b> 规模对应正向还是负向认知</span><span><b>③ 互动量</b> 仅由点大小补充活跃度</span></div><svg class="group-competitive-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X与四款竞品传播势能比较"><rect class="quality-zone" x="${left}" y="${top}" width="${right-left}" height="${(bottom-top)*.5}"/><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="axis" x1="${left}" y1="${top}" x2="${left}" y2="${bottom}"/><line class="midline" x1="${left}" y1="${bottom-(bottom-top)*.5}" x2="${right}" y2="${bottom-(bottom-top)*.5}"/><text class="zone-label" x="${right-10}" y="${top+15}" text-anchor="end">高口碑区</text><text class="axis-label" x="${(left+right)/2}" y="190" text-anchor="middle">第一判断：总体声量 →</text><text class="axis-label" transform="translate(26 78) rotate(-90)" text-anchor="middle">第二判断：全网 NSR →</text>${points}</svg><div class="group-chart-legend"><span><i class="e7x-star"></i>E7X 本品</span><span><i class="voc-dot"></i>竞品</span><span>本品声量第${own.voiceRank||"—"} · 互动第${own.engagementRank||"—"} · NSR第${own.overallNsrRank||"—"}</span></div></div></section>`;
 }

 function renderPlatforms(evaluation){
  const items=(evaluation.platforms||[]).filter(item=>item.platform!=="全网"),overall=(evaluation.platforms||[]).find(item=>item.platform==="全网")?.nsr||0,width=920,height=315,left=76,right=860,top=38,bottom=225,maxEngagement=Math.max(1,...items.map(item=>item.engagement||0)),baselineY=bottom-overall*(bottom-top);
  const points=items.map((item,index)=>{const x=left+index*((right-left)/Math.max(1,items.length-1)),y=bottom-item.nsr*(bottom-top),r=9+Math.sqrt((item.engagement||0)/maxEngagement)*12,status=item.nsr>=overall?"above":"below",direction=item.nsr>=overall?"↑":"↓";return`<g class="group-platform-point ${status}" tabindex="0" role="img" aria-label="${esc(item.platform)}，NSR${pct(item.nsr)}，${item.nsr>=overall?"高于":"低于"}E7X全网NSR，声量${num(item.voice)}，互动量${num(item.engagement)}"><line x1="${x}" y1="${baselineY}" x2="${x}" y2="${y}"/><circle class="halo" cx="${x}" cy="${y}" r="${r+6}"/><circle class="dot" cx="${x}" cy="${y}" r="${r}"/><text class="value" x="${x}" y="${y-r-9}" text-anchor="middle">${direction} ${pct(item.nsr)}</text><text class="platform" x="${x}" y="256" text-anchor="middle">${esc(item.platform)}</text><text class="volume" x="${x}" y="272" text-anchor="middle">${compact(item.engagement)}互动</text></g>`}).join("");
  return `<section class="group-board-section" aria-labelledby="group-platform-title"><header><div><span>06 · CHANNEL PERFORMANCE</span><h2 id="group-platform-title">E7X 平台阵地点阵</h2><p>点位高低＝平台NSR，点大小＝互动量；虚线＝E7X全网NSR基准。</p></div><em>全网 NSR ${pct(overall)}</em></header><div class="group-chart-frame group-platform-frame"><div class="group-chart-legend group-chart-legend-explicit"><span><i class="up"></i><b>绿色 / ↑</b>＝高于E7X全网NSR</span><span><i class="down"></i><b>红色 / ↓</b>＝低于E7X全网NSR</span><span><i class="size"></i>点越大＝互动量越高</span></div><svg class="group-platform-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X分平台口碑与互动点阵"><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="benchmark" x1="${left}" y1="${baselineY}" x2="${right}" y2="${baselineY}"/><text class="benchmark-label" x="${right}" y="${baselineY-7}" text-anchor="end">全网基准 ${pct(overall)}</text>${points}</svg></div></section>`;
 }

 function renderAttributes(evaluation){
  const items=evaluation.attributes||[],viewportWidth=window.innerWidth||1440,viewportHeight=window.innerHeight||900,width=Math.max(920,viewportWidth-320),height=Math.max(300,Math.min(360,viewportHeight-570)),left=22,right=width-22,top=15,bottom=height-45,minX=.25,maxX=1,minY=-.15,maxY=.38,zeroY=bottom-(0-minY)/(maxY-minY)*(bottom-top),thresholdX=left+(.65-minX)/(maxX-minX)*(right-left),middle=(left+right)/2;
  const positioned=items.map((item,index)=>({item,index,x:left+(item.ownNsr-minX)/(maxX-minX)*(right-left),y:bottom-(item.deltaVsAverage-minY)/(maxY-minY)*(bottom-top)}));
  const labelPositions=new Map();
  const layoutLabels=(side)=>{const sideItems=positioned.filter(point=>side==="left"?point.x<=middle:point.x>middle).sort((a,b)=>a.y-b.y),minLabelY=top+16,maxLabelY=bottom-4,minGap=22;let cursor=minLabelY;sideItems.forEach(point=>{const labelY=Math.max(cursor,Math.min(maxLabelY,point.y));labelPositions.set(point.index,{x:side==="left"?left+12:right-12,y:labelY,anchor:side==="left"?"start":"end"});cursor=labelY+minGap});if(sideItems.length&&cursor-minGap>maxLabelY){const shift=cursor-minGap-maxLabelY;sideItems.forEach(point=>{const current=labelPositions.get(point.index);current.y-=shift})}};
  layoutLabels("left");layoutLabels("right");
  const points=positioned.map(({item,index,x,y})=>{const status=item.deltaVsAverage<0?"risk":item.ownNsr>=.75?"asset":item.ownNsr<.6?"fragile":"watch",label=item.attribute==="动力与操控"?"动力操控":item.attribute,labelPosition=labelPositions.get(index),lineEndX=labelPosition.anchor==="start"?labelPosition.x-4:labelPosition.x+4;return`<g class="group-attribute-point ${status}" tabindex="0" role="img" aria-label="${esc(item.attribute)}，E7X NSR${pct(item.ownNsr)}，相对五车平均${item.deltaVsAverage>=0?"高":"低"}${pct(Math.abs(item.deltaVsAverage))}"><path class="label-leader" d="M ${x} ${y} L ${lineEndX} ${labelPosition.y-3}"/><circle class="halo" cx="${x}" cy="${y}" r="15"/><circle class="dot" cx="${x}" cy="${y}" r="9"/><text x="${labelPosition.x}" y="${labelPosition.y}" text-anchor="${labelPosition.anchor}">${esc(label)}</text></g>`}).join("");
  return `<section class="group-board-section" aria-labelledby="group-attribute-title"><header><div><span>07 · PRODUCT VOC</span><h2 id="group-attribute-title">E7X 产品认知星图</h2><p>每个点＝一个产品属性；点大小不代表样本量。</p></div><em>15项产品属性 · 全网口径</em></header><div class="group-chart-frame group-attribute-frame"><div class="group-axis-guide" aria-label="产品认知四象限坐标说明"><span><b>X轴｜本品认知</b> E7X属性NSR，越右消费者评价越正面</span><span><b>Y轴｜相对竞争力</b> E7X相对五车平均，越上领先越多</span></div><div class="group-chart-legend group-chart-legend-explicit"><span><i class="attribute-asset"></i>领先优势＝重点放大</span><span><i class="attribute-watch"></i>认知待建立＝先建设</span><span><i class="attribute-risk"></i>双重风险＝优先修复</span><span><i class="attribute-short"></i>对标短板＝重点追赶</span></div><svg class="group-attribute-plot" viewBox="0 0 ${width} ${height}" role="img" aria-label="奥迪E7X十五项产品属性认知分布"><rect class="quadrant-zone awareness-zone" x="${left}" y="${top}" width="${thresholdX-left}" height="${zeroY-top}"/><rect class="quadrant-zone asset-zone" x="${thresholdX}" y="${top}" width="${right-thresholdX}" height="${zeroY-top}"/><rect class="quadrant-zone risk-zone" x="${left}" y="${zeroY}" width="${thresholdX-left}" height="${bottom-zeroY}"/><rect class="quadrant-zone short-zone" x="${thresholdX}" y="${zeroY}" width="${right-thresholdX}" height="${bottom-zeroY}"/><line class="axis" x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}"/><line class="axis" x1="${left}" y1="${top}" x2="${left}" y2="${bottom}"/><line class="midline" x1="${left}" y1="${zeroY}" x2="${right}" y2="${zeroY}"/><line class="midline" x1="${thresholdX}" y1="${top}" x2="${thresholdX}" y2="${bottom}"/><text class="zone-label awareness" x="${(left+thresholdX)/2}" y="${top+18}" text-anchor="middle">认知待建立｜先建设</text><text class="zone-label asset" x="${(thresholdX+right)/2}" y="${top+18}" text-anchor="middle">领先优势｜重点放大</text><text class="zone-label risk" x="${(left+thresholdX)/2}" y="${bottom-10}" text-anchor="middle">双重风险｜优先修复</text><text class="zone-label short" x="${(thresholdX+right)/2}" y="${bottom-10}" text-anchor="middle">对标短板｜重点追赶</text><text class="axis-label" x="${(left+right)/2}" y="${height-9}" text-anchor="middle">X轴：本品属性 NSR（越右越正面）→</text><text class="axis-label" transform="translate(10 ${height/2}) rotate(-90)" text-anchor="middle">Y轴：相对五车平均（越上越领先）→</text>${points}</svg></div></section>`;
 }

 function render(data){
  const evaluation=data.productEvaluation||{},own=(evaluation.models||[]).find(item=>item.isOwn)||{},source=evaluation.source||{};
  const views=[
   {key:"brief",label:"高管摘要",content:renderExecutiveOverview(data.executiveBrief||{})},
   {key:"implication",label:"集团影响",content:renderGroupImplications()},
   {key:"actions",label:"本周动作",content:renderExecutiveActions(data.executiveBrief||{})},
   {key:"market",label:"赛道环境",content:renderSegments(data.marketDimensions||[],evaluation.positioning||{})},
   {key:"competitive",label:"传播势能",content:renderCompetitive(evaluation)},
   {key:"platform",label:"平台阵地",content:renderPlatforms(evaluation)},
   {key:"attribute",label:"产品 VOC",content:renderAttributes(evaluation)}
  ];
  const initialView=Math.max(0,views.findIndex(view=>view.key===uiState.viewKey));
  uiState.viewKey=views[initialView].key;
  root.innerHTML=`<div class="group-dashboard-shell group-dashboard-onepage"><section class="group-dashboard-hero group-executive-hero"><div><h2>集团市场决策简报</h2><small>${executivePulse.period} · 行业态势 → 集团影响 → 本周动作 → 证据下钻</small></div><div class="group-dashboard-actions"><button type="button" id="group-dashboard-refresh">刷新</button></div></section><section class="group-kpi-strip group-market-kpis" aria-label="全国乘用车市场周度核心指标"><article><span>乘用车零售</span><strong>${executivePulse.retail}</strong><small>${executivePulse.period}</small></article><article class="is-negative"><span>零售同比</span><strong>${executivePulse.retailYoy}</strong><small>终端需求偏弱</small></article><article><span>新能源零售</span><strong>${executivePulse.nevRetail}</strong><small>同比 -8%</small></article><article class="is-positive"><span>新能源渗透率</span><strong>${executivePulse.nevPenetration}</strong><small>结构韧性仍在</small></article></section><nav class="group-view-tabs" role="tablist" aria-label="管理层看板视图">${views.map((view,index)=>`<button type="button" id="group-view-tab-${view.key}" role="tab" data-group-view="${view.key}" aria-controls="group-view-panel-${view.key}" aria-selected="${index===initialView}" class="${index===initialView?"active":""}"><span>0${index+1}</span>${view.label}</button>`).join("")}</nav><div class="group-view-deck" tabindex="0" aria-label="可左右滑动切换看板">${views.map((view,index)=>`<div id="group-view-panel-${view.key}" class="group-view-panel ${index===initialView?"active":""}" role="tabpanel" data-group-panel="${view.key}" aria-labelledby="group-view-tab-${view.key}" ${index===initialView?"":"hidden"}>${view.content}</div>`).join("")}</div><footer class="group-view-footer"><button type="button" class="group-view-arrow" data-group-view-prev aria-label="上一视图">←</button><span data-group-view-progress>${initialView+1} / ${views.length}</span><small>同一页面 · 点击页签、键盘方向键或左右滑动</small><button type="button" class="group-view-arrow" data-group-view-next aria-label="下一视图">→</button></footer></div>`;
  root.querySelector("#group-dashboard-refresh")?.addEventListener("click",()=>load(true));
  root.querySelector("#group-brand-select")?.addEventListener("change",event=>{const brand=event.target.value;uiState.brand=brand;root.querySelectorAll("[data-brand-panel]").forEach(panel=>{panel.hidden=panel.dataset.brandPanel!==brand})});
  root.querySelector("#executive-vehicle-action-select")?.addEventListener("change",event=>{const vehicleId=event.target.value;uiState.vehicleId=vehicleId;root.querySelectorAll("[data-action-vehicle-panel]").forEach(panel=>{panel.hidden=panel.dataset.actionVehiclePanel!==vehicleId})});
  root.querySelectorAll("[data-page-jump]").forEach(button=>button.addEventListener("click",()=>window.showPage?.(button.dataset.pageJump)));
  root.querySelectorAll("[data-market-dimension]").forEach(button=>button.addEventListener("click",()=>{const key=button.dataset.marketDimension;uiState.marketDimension=key;root.querySelectorAll("[data-market-dimension]").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active))});root.querySelectorAll("[data-market-panel]").forEach(panel=>{const active=panel.dataset.marketPanel===key;panel.hidden=!active;panel.classList.toggle("active",active)})}));
  const viewKeys=views.map(view=>view.key),deck=root.querySelector(".group-view-deck"),progress=root.querySelector("[data-group-view-progress]");
  let activeView=initialView,pointerStartX=null;
  const activateView=(next,focus=false)=>{activeView=(next+viewKeys.length)%viewKeys.length;const key=viewKeys[activeView];uiState.viewKey=key;root.querySelectorAll("[data-group-view]").forEach(button=>{const active=button.dataset.groupView===key;button.classList.toggle("active",active);button.setAttribute("aria-selected",String(active));if(active&&focus)button.focus()});root.querySelectorAll("[data-group-panel]").forEach(panel=>{const active=panel.dataset.groupPanel===key;panel.hidden=!active;panel.classList.toggle("active",active)});if(progress)progress.textContent=`${activeView+1} / ${viewKeys.length}`};
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
   const response=await fetch(`/api/group-dashboard-demo?edition=${encodeURIComponent(currentEdition)}&refresh_review=${force?"1":"0"}`,{credentials:"same-origin",headers:typeof authHeaders==="function"?authHeaders():{}});
   const data=await response.json();
   if(!response.ok||!data.ok)throw new Error(data.error||`HTTP ${response.status}`);
   loadedEdition=currentEdition;render(data);
  }catch(error){renderError(error)}finally{loading=false}
 }

 window.loadGroupDashboardDemo=load;
})();
