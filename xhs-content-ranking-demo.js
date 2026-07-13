(function(){
 const state={range:"7d",brand:"all",model:"all",category:"all",selectedId:"",learning:""};
 const demoSamples=[
  {id:"demo-xhs-001",title:"20 万级纯电 SUV 怎么选：把续航、补能和空间放在一张表里",brand:"示例品牌 A",model:"示例 SUV X",author:"汽车决策笔记",category:"购车决策",likes:8420,collects:3160,comments:426,shares:188,ageDays:2,coverLabel:"预算 / 空间",summary:"演示样本：突出购车决策信息的结构化对比。"},
  {id:"demo-xhs-002",title:"高速能耗和补能效率，到底应该怎么看？",brand:"示例品牌 A",model:"示例 SUV X",author:"电车观察室",category:"技术科普",likes:6190,collects:2410,comments:318,shares:126,ageDays:4,coverLabel:"能耗 / 补能",summary:"演示样本：突出技术解释和用户追问。"},
  {id:"demo-xhs-003",title:"带娃通勤一周：车内收纳、后排和补能的真实体验",brand:"示例品牌 B",model:"示例 MPV M",author:"城市用车日记",category:"用车生活",likes:4750,collects:1960,comments:225,shares:82,ageDays:6,coverLabel:"带娃 / 通勤",summary:"演示样本：突出真实用车场景和收藏价值。"},
  {id:"demo-xhs-004",title:"选车前先看这 5 个配置：别只盯着参数表",brand:"示例品牌 B",model:"示例轿车 S",author:"购车清单",category:"购车决策",likes:7020,collects:2890,comments:367,shares:151,ageDays:11,coverLabel:"配置 / 取舍",summary:"演示样本：突出选配清单和决策效率。"},
  {id:"demo-xhs-005",title:"雨天和夜间开车，辅助驾驶到底帮了什么忙？",brand:"示例品牌 C",model:"示例 SUV Z",author:"技术体验派",category:"技术科普",likes:3660,collects:1530,comments:274,shares:71,ageDays:18,coverLabel:"夜间 / 智驾",summary:"演示样本：突出能力边界与安全感受。"},
  {id:"demo-xhs-006",title:"周末露营实测：装载、补能和休息空间怎么安排",brand:"示例品牌 C",model:"示例 SUV Z",author:"周末出行册",category:"用车生活",likes:4380,collects:2070,comments:196,shares:112,ageDays:5,coverLabel:"露营 / 装载",summary:"演示样本：突出生活方式场景和行动清单。"}
 ];
 const esc=value=>String(value??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
 const unique=values=>[...new Set(values.filter(Boolean))];
 const number=value=>{const n=Math.round(+value||0);return n>=10000?`${(n/10000).toFixed(n>=100000?0:1)}万`:n.toLocaleString()};
 function isXhsContent(item){const text=[item?.platform,item?.source,item?.url,item?.sourceUrl].join(" ").toLowerCase();return text.includes("xiaohongshu")||text.includes("小红书")||text.includes("xhslink")}
 function safeUrl(value){try{const url=new URL(String(value||""),window.location.origin);return /^https?:$/.test(url.protocol)?url.href:""}catch{return""}}
 function categoryFor(item){const text=[item?.category,item?.title,item?.tags].flat().join(" ");if(/技术|能耗|续航|补能|智驾|底盘|参数/.test(text))return"技术科普";if(/购车|选车|价格|配置|对比|预算/.test(text))return"购车决策";return"用车生活"}
 function ageDaysFor(item){const raw=item?.publishedAt||item?.publishTime||item?.published_at||item?.date||item?.createdAt;const date=raw?new Date(raw):null;return !date||Number.isNaN(date.getTime())?0:Math.max(0,Math.floor((Date.now()-date.getTime())/86400000))}
 function scoreFor(item){const interactions=(+item.likes||0)+(+item.collects||0)*2+(+item.comments||0)*4+(+item.shares||0)*1.5;return Math.max(0,Math.round(interactions||(+item.engagement||0)))}
 function normalizedItems(items){
  const synced=(items||[]).filter(isXhsContent).map((item,index)=>({id:item.id||item.itemId||`xhs-${index}`,title:item.title||"未命名小红书内容",brand:item.brand||"待识别品牌",model:item.assetModel||item.model||"待识别车型",author:item.author||"待识别账号",category:categoryFor(item),likes:+item.likes||0,collects:+item.collects||0,comments:+item.comments||0,shares:+item.shares||0,ageDays:ageDaysFor(item),summary:item.summary||item.text||item.description||"已同步内容，等待补充正文或评论摘要。",url:safeUrl(item.url||item.sourceUrl),cover:safeUrl(item.cover||item.coverUrl||item.thumbnail||item.poster),coverLabel:item.category||"内容样本",recognition:item.entityRecognition||item.recognition||item.entity_review||null,manualEdited:Boolean(item.manualEdited||item.entityManualEdited)}));
  return synced.length?{items:synced,isDemo:false}:{items:demoSamples,isDemo:true};
 }
 function recognitionFor(item,isDemo){
  const status=item?.recognition?.qa?.dualModel?.status||item?.recognition?.status||item?.recognition?.verificationStatus||"";
  if(item?.manualEdited)return{label:"人工修正",kind:"manual"};
  if(["aligned","confirmed","dual_confirmed"].includes(status))return{label:"双模型确认",kind:"confirmed"};
  if(["manual_required","conflict","pending_review"].includes(status))return{label:"待人工核验",kind:"pending"};
  return{label:isDemo?"演示样本":"待双模型复核",kind:isDemo?"demo":"pending"};
 }
 function learningFor(item){const patterns={"购车决策":{hook:"预算 / 场景切入 → 关键维度降噪",structure:"人群问题 → 3–5 维对比 → 取舍建议",transfer:"把选择焦虑压缩成可执行清单"},"技术科普":{hook:"真实问题切入 → 先讲结论再讲原理",structure:"使用情境 → 指标解释 → 能力边界",transfer:"用可验证的场景解释技术价值"},"用车生活":{hook:"具体生活场景 → 细节感受 → 行动建议",structure:"真实经历 → 高低频细节 → 可复用安排",transfer:"将产品力放进用户的一天"}};return patterns[item?.category]||patterns["用车生活"]}
 function rangeItems(dataset){return dataset.items.filter(item=>item.ageDays<=(state.range==="30d"?30:7))}
 function filteredItems(dataset){return rangeItems(dataset).filter(item=>state.brand==="all"||item.brand===state.brand).filter(item=>state.model==="all"||item.model===state.model).filter(item=>state.category==="all"||item.category===state.category).sort((a,b)=>scoreFor(b)-scoreFor(a))}
 function aggregate(items,key){return Object.values(items.reduce((groups,item)=>{const label=item[key]||"待识别";const group=groups[label]||{label,count:0,total:0,max:0,brand:item.brand};group.count+=1;group.total+=scoreFor(item);group.max=Math.max(group.max,scoreFor(item));groups[label]=group;return groups},{})).sort((a,b)=>b.total-a.total)}
 function toggleButtons(selector,key,value){document.querySelectorAll(selector).forEach(button=>{const active=button.dataset[key]===value;button.classList.toggle("active",active);button.setAttribute("aria-pressed",String(active))})}
 function filterButtons(root,items,key,label,current){if(!root)return;const values=unique(items.map(item=>item[key]));root.innerHTML=["all",...values].map(value=>`<button type="button" class="${value===current?"active":""}" data-xhs-rank-${key}="${esc(value)}" aria-pressed="${value===current}">${value==="all"?`全部${label}`:esc(value)}</button>`).join("")}
 function renderRadarRows(root,groups,type){
  if(!root)return;const max=Math.max(1,...groups.map(group=>group.total));root.innerHTML=groups.length?groups.slice(0,8).map((group,index)=>`<button type="button" class="xhs-radar-row" data-xhs-radar-${type}="${esc(group.label)}"><span>${index+1}</span><div><b>${esc(group.label)}${type==="model"?` <small>${esc(group.brand)}</small>`:""}</b><i><em style="width:${Math.max(8,Math.round(group.total/max*100))}%"></em></i></div><small>入榜 ${group.count} 条 · 最高 ${number(group.max)}</small></button>`).join(""):`<p class="empty">当前范围内没有可聚合的${type==="brand"?"品牌":"车型"}内容。</p>`;
 }
 function renderRadar(dataset){
  const items=rangeItems(dataset),brandGroups=aggregate(items,"brand"),modelGroups=aggregate(items,"model"),status=document.querySelector("#xhs-ranking-radar-status");renderRadarRows(document.querySelector("#xhs-ranking-brand-radar"),brandGroups,"brand");renderRadarRows(document.querySelector("#xhs-ranking-model-radar"),modelGroups,"model");
  if(status){const confirmed=items.filter(item=>recognitionFor(item,dataset.isDemo).kind==="confirmed").length;status.textContent=dataset.isDemo?"演示样本 · 不伪造模型结论":confirmed?`${confirmed} 条双模型确认`:`${items.length} 条待双模型复核`}
 }
 function signalFor(item,rank){
  if(item.collects>=item.likes*.35)return `收藏 ${number(item.collects)}，信息留存信号突出；建议复核标题、封面与收藏动机。`;
  if(item.comments>=Math.max(100,item.likes*.08))return `评论 ${number(item.comments)}，讨论信号突出；建议结合评论确认争议或追问点。`;
  return `综合互动位列当前第 ${rank}；建议结合标题、封面与评论判断走红机制。`;
 }
 function coverMarkup(item){return item.cover?`<img src="${esc(item.cover)}" alt="" loading="lazy">`:`<span>${esc(item.coverLabel||item.category)}</span>`}
 function renderBoard(ranked,dataset){
  const root=document.querySelector("#xhs-ranking-list");if(!root)return;if(!ranked.some(item=>item.id===state.selectedId))state.selectedId=ranked[0]?.id||"";
  root.innerHTML=ranked.length?ranked.map((item,index)=>{const recognition=recognitionFor(item,dataset.isDemo);return `<article class="xhs-ranking-row ${item.id===state.selectedId?"active":""}"><button type="button" class="xhs-row-select" data-xhs-ranking-item="${esc(item.id)}" aria-pressed="${item.id===state.selectedId}" aria-label="查看第 ${index+1} 名：${esc(item.title)}"><span class="xhs-ranking-position">${index+1}</span><span class="xhs-ranking-cover">${coverMarkup(item)}</span><span class="xhs-ranking-copy"><b>${esc(item.title)}</b><small>${esc(item.author)} · ${esc(item.category)}</small><span class="xhs-ranking-metrics">点赞 ${number(item.likes)}　收藏 ${number(item.collects)}　评论 ${number(item.comments)}　分享 ${number(item.shares)}</span><span class="xhs-ranking-tags"><em class="${recognition.kind}">${esc(recognition.label)}</em><em>${esc(item.brand)}</em><em>${esc(item.model)}</em></span></span></button><aside class="xhs-ranking-signal"><b>走红信号</b><p>${esc(signalFor(item,index+1))}</p></aside></article>`}).join(""):`<p class="empty">当前筛选条件下没有内容。切换品牌、车型或时间范围后再查看。</p>`;
 }
 function renderLearning(ranked,selected,dataset){
  const root=document.querySelector("#xhs-ranking-learning-grid"),status=document.querySelector("#xhs-ranking-learning-status"),button=document.querySelector("[data-xhs-ranking-learn]");if(!root||!status||!button)return;const learning=learningFor(selected),counts=ranked.reduce((acc,item)=>{acc[item.category]=(acc[item.category]||0)+1;return acc},{}),category=Object.entries(counts).sort((a,b)=>b[1]-a[1])[0]?.[0]||"—";
  root.innerHTML=selected?`<article class="xhs-learning-card"><span>热榜共性</span><b>${esc(category)}内容在当前筛选下出现最多</b><p>高表现样本优先解决明确场景中的具体问题，而不是罗列卖点。</p></article><article class="xhs-learning-card"><span>开头公式</span><b>${esc(learning.hook)}</b><p>来自当前选中内容类型的可迁移结构，不复制原作者表达。</p></article><article class="xhs-learning-card"><span>可迁移打法</span><b>${esc(learning.transfer)}</b><p>品牌、车型和人设表达必须重新创作；副模型负责证据与边界复核。</p></article>`:`<p class="empty">选择一条内容后，查看可迁移的内容结构与学习边界。</p>`;
  const canLearn=Boolean(selected?.url)&&!dataset.isDemo;button.disabled=!canLearn;button.textContent=state.learning==="正在沉淀…"?"正在沉淀…":canLearn?"学习当前内容":"等待真实内容链接";status.textContent=state.learning||(!selected?"当前没有样本":dataset.isDemo?"演示样本不写入知识库":canLearn?"可沉淀到内容能力库":"缺少公开链接，不能写入知识库");
 }
 function render(items){
  const source=document.querySelector("#xhs-ranking-source");if(!source)return;const dataset=normalizedItems(items),range=rangeItems(dataset);if(!unique(range.map(item=>item.brand)).includes(state.brand))state.brand="all";const byBrand=range.filter(item=>state.brand==="all"||item.brand===state.brand);if(!unique(byBrand.map(item=>item.model)).includes(state.model))state.model="all";
  source.textContent=dataset.isDemo?"演示样本 · 等待同步小红书内容":`已同步小红书内容 · ${dataset.items.length} 条`;filterButtons(document.querySelector("#xhs-ranking-brand-filters"),range,"brand","品牌",state.brand);filterButtons(document.querySelector("#xhs-ranking-model-filters"),byBrand,"model","车型",state.model);toggleButtons("[data-xhs-rank-range]","xhsRankRange",state.range);toggleButtons("[data-xhs-rank-category]","xhsRankCategory",state.category);renderRadar(dataset);const ranked=filteredItems(dataset),selected=ranked.find(item=>item.id===state.selectedId)||ranked[0];renderBoard(ranked,dataset);renderLearning(ranked,selected,dataset);bindDynamicFilters(items);
 }
 function bindDynamicFilters(items){
  document.querySelectorAll("[data-xhs-rank-brand]").forEach(button=>button.onclick=()=>{state.brand=button.dataset.xhsRankBrand;state.model="all";state.selectedId="";state.learning="";render(items)});
  document.querySelectorAll("[data-xhs-rank-model]").forEach(button=>button.onclick=()=>{state.model=button.dataset.xhsRankModel;state.selectedId="";state.learning="";render(items)});
  document.querySelectorAll("[data-xhs-radar-brand]").forEach(button=>button.onclick=()=>{state.brand=button.dataset.xhsRadarBrand;state.model="all";state.selectedId="";state.learning="";render(items)});
  document.querySelectorAll("[data-xhs-radar-model]").forEach(button=>button.onclick=()=>{state.model=button.dataset.xhsRadarModel;state.selectedId="";state.learning="";render(items)});
  document.querySelectorAll("[data-xhs-ranking-item]").forEach(button=>button.onclick=()=>{state.selectedId=button.dataset.xhsRankingItem;state.learning="";render(items)});
 }
 async function learnCurrent(getItems){
  const dataset=normalizedItems(getItems()),selected=filteredItems(dataset).find(item=>item.id===state.selectedId);if(!selected?.url||dataset.isDemo){state.learning="演示样本没有公开链接，未写入内容能力库。";render(getItems());return}if(typeof window.api!=="function"){state.learning="MMN 内容能力库暂不可用，请刷新页面后重试。";render(getItems());return}state.learning="正在沉淀…";render(getItems());
  try{await window.api("/api/content-capability-kb/collect-public",{method:"POST",body:JSON.stringify({edition:window.activeEdition?.()||"china",account:selected.author,platform:"xiaohongshu",source_url:selected.url})});state.learning="已提交内容蒸馏；完成后可在内容能力库查看 RAG 资产。"}catch(error){state.learning=`沉淀失败：${error?.message||String(error)}`}render(getItems());
 }
 function bind(getItems){
  document.querySelectorAll("[data-xhs-rank-range]").forEach(button=>button.onclick=()=>{state.range=button.dataset.xhsRankRange;state.selectedId="";state.learning="";render(getItems())});document.querySelectorAll("[data-xhs-rank-category]").forEach(button=>button.onclick=()=>{state.category=button.dataset.xhsRankCategory;state.selectedId="";state.learning="";render(getItems())});document.querySelector("[data-xhs-ranking-learn]")?.addEventListener("click",()=>learnCurrent(getItems));
 }
 window.MmnXhsContentRanking={render,bind};
})();
