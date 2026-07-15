(function(){
 const mount=document.querySelector("#douyin-hot-module-mount");
 if(!mount)return;
 const ranges={"24h":"24小时","7d":"7天","30d":"30天"};
 const RECOGNITION_DELAY_MS=300;
 const state={range:"24h",view:"videos",rankingExpanded:false};
 const rankingState={};
 const rankingRequests={};
 const recognitionState={};
 const manualReviewState={open:false,loading:false,saving:false,items:[],selectedId:"",message:"",error:""};
 const collectorState={browserOpen:false,loginState:"disconnected",progress:0,message:"尚未连接抖音采集器",job:null,error:""};
 let collectorPollTimer=0;
 const escapeHtml=value=>String(value??"").replace(/[&<>\"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
 const safeHttpUrl=value=>/^https?:\/\//i.test(String(value||"").trim())?String(value).trim():"";
 const safeImageUrl=value=>/^(https?:\/\/|\/api\/)/i.test(String(value||"").trim())?String(value).trim():"";
 const fmt=value=>{const n=Number(value)||0;if(n>=1e8)return `${(n/1e8).toFixed(1)}亿`;if(n>=1e4)return `${(n/1e4).toFixed(1)}万`;return Math.round(n).toLocaleString("zh-CN")};
 const editionKey=()=>typeof activeEdition==="function"?activeEdition():"china";
 const dataKey=(view=state.view,range=state.range)=>`${editionKey()}:${view}:${range}`;
 const currentSnapshot=()=>rankingState[dataKey()]?.data||null;
 const currentItems=()=>currentSnapshot()?.items||[];
 const recognitionKey=()=>dataKey();
 const recognitionSignature=()=>currentItems().map(item=>JSON.stringify([item.itemId,item.title,item.author,item.tags,item.transcript,item.rank,item.playCount])).join("|");
 const currentRecognition=()=>{const value=recognitionState[recognitionKey()],signature=recognitionSignature();return value?.signature===signature?value:{signature,loading:false,data:null,error:""}};

 async function loadRanking(view,range){
  const key=dataKey(view,range);
  if(rankingRequests[key])return rankingRequests[key];
  rankingState[key]={loading:true,data:rankingState[key]?.data||null,error:""};
  rankingRequests[key]=(async()=>{
   try{
    const edition=editionKey();
    const response=await api(`/api/douyin-hot/rankings?edition=${encodeURIComponent(edition)}&view=${encodeURIComponent(view)}&range=${encodeURIComponent(range)}`);
    rankingState[key]={loading:false,data:response.result,error:""};
   }catch(error){rankingState[key]={loading:false,data:null,error:error?.message||String(error)}}
   finally{delete rankingRequests[key]}
  })();
  return rankingRequests[key];
 }

 async function loadRange(range){
  await Promise.all([loadRanking("videos",range),loadRanking("topics",range)]);
  render();
  setTimeout(requestRecognition,RECOGNITION_DELAY_MS);
 }

 function collectorRunning(){return ["queued","running"].includes(collectorState.job?.status)}
 async function loadCollectorStatus(){
  try{
   const response=await api(`/api/douyin-hot/collector/status?edition=${encodeURIComponent(editionKey())}`);
   Object.assign(collectorState,response.collector||{}, {error:""});
   render();
   if(collectorRunning())scheduleCollectorPoll();
  }catch(error){collectorState.error=error?.message||String(error);render()}
 }
 async function connectCollector(){
  collectorState.message="正在打开采集器专用浏览器…";collectorState.error="";render();
  try{
   const response=await api("/api/douyin-hot/collector/connect",{method:"POST",body:JSON.stringify({edition:editionKey()})});
   Object.assign(collectorState,response.collector||{}, {error:""});
  }catch(error){collectorState.error=error?.message||String(error)}
  render();
 }
 async function startCollectorSync(force=false){
  collectorState.message="正在提交六榜同步任务…";collectorState.error="";render();
  try{
   const response=await api("/api/douyin-hot/collector/sync",{method:"POST",body:JSON.stringify({edition:editionKey(),force})});
   collectorState.job=response.job;collectorState.progress=response.job?.progress||0;collectorState.message=response.job?.message||"同步任务已提交";
   scheduleCollectorPoll(100);
  }catch(error){collectorState.error=error?.message||String(error);render()}
 }
 function scheduleCollectorPoll(delay=1200){
  clearTimeout(collectorPollTimer);
  collectorPollTimer=setTimeout(pollCollectorJob,delay);
 }
 async function pollCollectorJob(){
  const jobId=collectorState.job?.jobId;if(!jobId)return;
  try{
   const response=await api(`/api/douyin-hot/collector/jobs/${encodeURIComponent(jobId)}`);
   collectorState.job=response.job;collectorState.progress=response.job?.progress||0;collectorState.message=response.job?.message||"";collectorState.error=response.job?.error||"";
   render();
   if(collectorRunning())scheduleCollectorPoll();
   else if(response.job?.status==="completed"){
    Object.keys(rankingState).forEach(key=>delete rankingState[key]);
    await loadRange(state.range);
   }
  }catch(error){collectorState.error=error?.message||String(error);render()}
 }

 function collectorProgress(){
  const job=collectorState.job||{},progress=Math.max(0,Math.min(100,Number(job.progress??collectorState.progress)||0));
  const stage=job.stage||(collectorState.browserOpen?"login":"disconnected");
  const order={disconnected:-1,queued:0,login:0,login_verified:1,collecting:1,storage:1,analysis:2,delivery:3,completed:4,failed:-1};
  const current=order[stage]??-1;
  const loginVerified=["login_verified","collecting","storage","analysis","delivery","completed"].includes(stage);
  const steps=[[loginVerified?"登录成功":"等待登录","连接并验证账号"],["抓取排行榜","同步视频/话题六榜"],["双模型分析","识别品牌与车型"],["交付","刷新正式看板"]];
  return `<section class="douyin-collector-progress" aria-live="polite"><div class="douyin-collector-progress__top"><div><b>榜单交付进度</b><span>${escapeHtml(collectorState.error||job.error||collectorState.message||"等待连接")}</span></div><strong>${progress}%</strong></div><div class="douyin-collector-progress__bar" role="progressbar" aria-label="抖音榜单交付进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><i style="width:${progress}%"></i></div><ol>${steps.map(([label,detail],index)=>`<li class="${current>index||stage==="completed"?"done":current===index?"active":""}"><i>${current>index||stage==="completed"?"✓":index+1}</i><div><b>${label}</b><span>${detail}</span></div></li>`).join("")}</ol></section>`;
 }

 async function loadManualReviewQueue(){
  manualReviewState.loading=true;manualReviewState.error="";render();
  try{
   const response=await api(`/api/douyin-hot/manual-reviews?edition=${encodeURIComponent(editionKey())}&view=${encodeURIComponent(state.view)}&range=${encodeURIComponent(state.range)}`);
   manualReviewState.items=response.result?.items||[];
   if(!manualReviewState.items.some(item=>item.itemId===manualReviewState.selectedId))manualReviewState.selectedId=(manualReviewState.items.find(item=>item.status==="conflict")||manualReviewState.items[0])?.itemId||"";
  }catch(error){manualReviewState.error=error?.message||String(error)}
  manualReviewState.loading=false;render();requestAnimationFrame(()=>mount.querySelector(".douyin-manual-review")?.scrollIntoView({behavior:"smooth",block:"start"}));
 }
 function openManualReview(itemId=""){manualReviewState.open=true;manualReviewState.selectedId=itemId||manualReviewState.selectedId;manualReviewState.message="";manualReviewState.error="";render();loadManualReviewQueue()}
 function closeManualReview(){manualReviewState.open=false;manualReviewState.message="";manualReviewState.error="";render()}
 function selectedManualReview(){return manualReviewState.items.find(item=>item.itemId===manualReviewState.selectedId)||manualReviewState.items[0]||null}
 async function submitManualReview(action){
  const item=selectedManualReview();if(!item||manualReviewState.saving)return;
  const brand=mount.querySelector("[data-manual-brand]")?.value?.trim()||"",model=mount.querySelector("[data-manual-model]")?.value?.trim()||"",note=mount.querySelector("[data-manual-note]")?.value?.trim()||"";
  if(action==="confirm"&&!brand){manualReviewState.error="请填写确认后的品牌。";render();return}
  manualReviewState.saving=true;manualReviewState.error="";manualReviewState.message="正在保存人工确认并更新品牌车型雷达…";render();
  try{
   const response=await api("/api/douyin-hot/manual-reviews/submit",{method:"POST",body:JSON.stringify({edition:editionKey(),itemId:item.itemId,fingerprint:item.fingerprint,action,brand,model,note})});
   manualReviewState.message=response.result?.message||"审核已完成";
   delete recognitionState[recognitionKey()];
   await requestRecognition();
   await loadManualReviewQueue();
  }catch(error){manualReviewState.error=error?.message||String(error)}
  manualReviewState.saving=false;render();
 }

 function recognitionFor(item){return currentRecognition().data?.items?.find(row=>String(row.itemId)===String(item.itemId))}
 function entityChips(item){
  const result=recognitionFor(item),mentions=result?.mentions||[],candidates=item.candidateMentions||[];
  if(!mentions.length){
   if(result?.status==="manual_verified")return `<span class="douyin-entity-status manual_verified">${escapeHtml(result.recognitionLabel||"人工确认：无明确品牌车型")}</span>`;
   if(currentRecognition().loading&&candidates.length)return `${candidates.map(row=>`<span class="douyin-entity-status pending">标题候选 · 待双模型确认</span><span class="douyin-entity-chip pending"><b>${escapeHtml(row.brand||"品牌待核")}</b>${row.model?`<i>${escapeHtml(row.model)}</i>`:""}</span>`).join("")}`;
   if(result?.status==="conflict")return `<span class="douyin-entity-status conflict">双模型存在分歧</span>${candidates.map(row=>`<span class="douyin-entity-chip pending"><b>${escapeHtml(row.brand||"品牌待核")}</b>${row.model?`<i>${escapeHtml(row.model)}</i>`:""}<small>标题明确·待复核</small></span>`).join("")||`<span class="douyin-entity-empty">暂不计入确认榜</span>`}`;
   return `<span class="douyin-entity-empty">${currentRecognition().loading?"双模型识别中…":"未识别到明确品牌车型"}</span>`;
  }
  return `<span class="douyin-entity-status ${result.status}">${escapeHtml(result.recognitionLabel)}</span>${mentions.map(row=>`<span class="douyin-entity-chip"><b>${escapeHtml(row.brand||"品牌待核")}</b>${row.model?`<i>${escapeHtml(row.model)}</i>`:""}<small>${escapeHtml(row.relation||"提及")}</small></span>`).join("")}`;
 }

 function candidateRadar(){
  const brands=new Map(),models=new Map();
  currentItems().forEach(item=>(item.candidateMentions||[]).forEach(row=>{
   if(row.brand){const value=brands.get(row.brand)||{name:row.brand,appearances:0,totalPlay:0,bestRank:999};value.appearances++;value.totalPlay+=Number(item.playCount)||0;value.bestRank=Math.min(value.bestRank,Number(item.rank)||999);brands.set(row.brand,value)}
   if(row.model){const key=`${row.brand}|${row.model}`,value=models.get(key)||{name:row.model,brand:row.brand,appearances:0,totalPlay:0,bestRank:999};value.appearances++;value.totalPlay+=Number(item.playCount)||0;value.bestRank=Math.min(value.bestRank,Number(item.rank)||999);models.set(key,value)}
  }));
  const sort=rows=>[...rows.values()].sort((a,b)=>b.appearances-a.appearances||b.totalPlay-a.totalPlay||a.bestRank-b.bestRank);
  return {brands:sort(brands),models:sort(models)};
 }

 function radarList(rows,type,pending=false){
  if(!rows?.length)return `<p class="douyin-radar-empty">本期双模型尚未确认明确${type}。</p>`;
  const max=Math.max(...rows.map(row=>Number(row.totalPlay)||0),1);
  return `<ol>${rows.slice(0,8).map((row,index)=>`<li><span>${index+1}</span><div><b>${escapeHtml(row.name)}</b>${row.brand?`<small>${escapeHtml(row.brand)}</small>`:""}<i style="--entity-heat:${Math.max(10,Math.round((Number(row.totalPlay)||0)/max*100))}%"></i></div><em>${pending?"标题候选 · 待确认":`上榜 ${row.appearances} 次 · 最高 #${row.bestRank}`}</em></li>`).join("")}</ol>`;
 }

 function entityRadar(){
  const recognition=currentRecognition(),pending=recognition.loading,candidates=candidateRadar(),radar=pending?candidates:(recognition.data?.radar||{});
  const candidateCount=candidates.brands.length+candidates.models.length;
  const status=recognition.error?"识别异常":pending?`双模型识别中 · ${candidateCount}个标题候选`:recognition.data?.dualModelReady?"MMN识别已更新":"等待模型识别";
  const cls=recognition.error?"error":recognition.data?.dualModelReady?"ready":"";
  const reviewModels=(radar.candidateModels||[]).map(row=>`${row.brand?`${row.brand} `:""}${row.name}`).join("、"),reviewBrands=(radar.candidateBrands||[]).map(row=>row.name).join("、");
  const reviewCount=recognition.data?.statusCounts?.conflict||0;
  const reviewSummary=reviewBrands||reviewModels?`${reviewBrands?`品牌 ${escapeHtml(reviewBrands)}`:""}${reviewBrands&&reviewModels?"；":""}${reviewModels?`车型 ${escapeHtml(reviewModels)}`:""}`:`${reviewCount} 条内容`;
  return `<section class="douyin-entity-radar"><header><div><span>BRAND & MODEL RADAR</span><h3>品牌车型上榜雷达</h3><p>基于当前${ranges[state.range]}真实榜单识别；人工修改优先于模型结果。</p></div><em class="${cls}"><i></i>${status}</em></header>${recognition.error?`<p class="douyin-radar-error">${escapeHtml(recognition.error)}</p>`:`<div class="douyin-radar-grid"><article><div><b>${pending?"品牌标题候选":"品牌上榜"}</b><span>${pending?"等待模型识别":"出现次数 × 播放热度"}</span></div>${radarList(radar.brands,"品牌",pending)}</article><article><div><b>${pending?"车型标题候选":"车型上榜"}</b><span>模型一致或人工确认后计入</span></div>${radarList(radar.models,"车型",pending)}</article></div>${!pending&&reviewCount?`<div class="douyin-radar-review-alert"><p>待人工复核：${reviewSummary}。人工确认后将立即进入雷达，不受模型分歧阻断。</p><button type="button" data-manual-review-open>进入人工核验（${reviewCount}）</button></div>`:""}`}
  <footer>${pending?"标题候选只用于避免识别过程中的空白误导，最终仍以双模型一致结果为准。":`本轮新识别 ${recognition.data?.freshCount||0} 条，复用 ${recognition.data?.reusedCount||0} 条，分歧待复核 ${recognition.data?.statusCounts?.conflict||0} 条`}</footer></section>`;
 }

 function mentionsText(rows){return rows?.length?rows.map(row=>`${row.brand||"未识别品牌"}${row.model?` ${row.model}`:""}`).join("、"):"未识别到明确实体"}
 function manualReviewPanel(){
  if(!manualReviewState.open)return "";
  const item=selectedManualReview();
  if(manualReviewState.loading&&!item)return `<section class="douyin-manual-review"><header><div><span>MANUAL VERIFICATION</span><h3>人工核验工作台</h3></div><button type="button" data-manual-review-close>关闭</button></header><p class="douyin-manual-empty">正在读取当前榜单待核验内容…</p></section>`;
  if(!item)return `<section class="douyin-manual-review"><header><div><span>MANUAL VERIFICATION</span><h3>人工核验工作台</h3></div><button type="button" data-manual-review-close>关闭</button></header>${manualReviewState.message?`<p class="douyin-manual-message">${escapeHtml(manualReviewState.message)}</p>`:""}<p class="douyin-manual-empty">当前${ranges[state.range]}${state.view==="videos"?"视频":"话题"}榜没有待人工核验内容。</p></section>`;
  const seed=item.decision?.action==="exclude"?{}:item.decision?.brand?item.decision:(item.mentions?.[0]||item.candidateMentions?.[0]||item.primaryMentions?.[0]||item.reviewerMentions?.[0]||{});
  return `<section class="douyin-manual-review" aria-live="polite"><header><div><span>MANUAL VERIFICATION</span><h3>人工核验工作台</h3><p>人工结论具有最高优先级，点击任一确认按钮后立即更新雷达。</p></div><button type="button" data-manual-review-close>关闭</button></header>${manualReviewState.message?`<p class="douyin-manual-message">${escapeHtml(manualReviewState.message)}</p>`:""}${manualReviewState.error?`<p class="douyin-manual-error">${escapeHtml(manualReviewState.error)}</p>`:""}<div class="douyin-manual-grid"><nav aria-label="榜单内容人工修改">${manualReviewState.items.map((row,index)=>`<button type="button" class="${row.itemId===item.itemId?"active":""}" data-manual-review-item="${escapeHtml(row.itemId)}"><span>${index+1}</span><b>${escapeHtml(row.title)}</b><small>${row.manualStatus==="published"?"已人工确认，可再次修改":row.status==="conflict"?"模型分歧，待人工确认":"可人工修改"}</small></button>`).join("")}</nav><article><span class="douyin-manual-rank">原榜单内容</span><h4>${escapeHtml(item.title)}</h4><div class="douyin-manual-comparison"><p><b>Qwen 识别</b>${escapeHtml(mentionsText(item.primaryMentions))}</p><p><b>DeepSeek 识别</b>${escapeHtml(mentionsText(item.reviewerMentions))}</p><p><b>当前归类</b>${escapeHtml(mentionsText(item.mentions))}</p></div><label>确认品牌<input data-manual-brand value="${escapeHtml(seed.brand||"")}" placeholder="例如：零跑"></label><label>确认车型<input data-manual-model value="${escapeHtml(seed.model||"")}" placeholder="品牌明确但车型不明确时可留空"></label><label>核验备注<textarea data-manual-note rows="2" placeholder="可记录判断依据">${escapeHtml(item.note||"")}</textarea></label><div class="douyin-manual-actions"><button type="button" class="primary" data-manual-confirm ${manualReviewState.saving?"disabled":""}>${manualReviewState.saving?"保存中…":"确认并进入雷达"}</button><button type="button" data-manual-exclude ${manualReviewState.saving?"disabled":""}>确认无明确品牌车型</button></div></article></div></section>`;
 }

 async function requestRecognition(){
  const items=currentItems();
  if(!items.length)return;
  const key=recognitionKey(),signature=recognitionSignature(),current=recognitionState[key];
  if(current?.signature===signature&&(current.loading||current.data))return;
  recognitionState[key]={signature,loading:true,data:null,error:""};render();
  try{
   const response=await api("/api/douyin-hot/recognize",{method:"POST",body:JSON.stringify({edition:editionKey(),range:state.range,view:state.view,items})});
   if(recognitionState[key]?.signature!==signature)return;
   recognitionState[key]={signature,loading:false,data:response.result,error:""};
  }catch(error){if(recognitionState[key]?.signature!==signature)return;recognitionState[key]={signature,loading:false,data:null,error:error?.message||String(error)}}
  render();
 }

 function tabs(){return `<div class="douyin-hot-tabs" role="tablist" aria-label="热点类型">${[["videos","热门视频"],["topics","热门话题"]].map(([key,label])=>`<button type="button" role="tab" aria-selected="${state.view===key}" class="${state.view===key?"active":""}" data-hot-view="${key}">${label}</button>`).join("")}</div><div class="douyin-hot-ranges" role="group" aria-label="时间范围">${Object.entries(ranges).map(([key,label])=>`<button type="button" aria-pressed="${state.range===key}" class="${state.range===key?"active":""}" data-hot-range="${key}">${label}</button>`).join("")}</div>`}

 function summary(){
  const video=rankingState[dataKey("videos")]?.data?.items?.[0];
  const topic=rankingState[dataKey("topics")]?.data?.items?.[0];
  return `<div class="douyin-hot-kpis"><div><span>榜首视频播放</span><b>${video?fmt(video.playCount):"—"}</b><small>${escapeHtml(video?.author||"等待视频榜同步")}</small></div><div><span>榜首话题播放</span><b>${topic?fmt(topic.playCount):"—"}</b><small>${topic?`#${escapeHtml(topic.title)}`:"等待话题榜同步"}</small></div><div><span>话题参与创作者</span><b>${topic?fmt(topic.creatorCount):"—"}</b><small>${ranges[state.range]}真实榜单</small></div></div>`;
 }

 function signal(item){
  const play=Number(item.playCount)||0,interactions=(Number(item.likeCount)||0)+(Number(item.commentCount)||0)+(Number(item.shareCount)||0);
  if(item.sourceType==="topic")return item.creatorCount?`${fmt(item.creatorCount)} 位创作者参与，观察内容供给与品牌占位`:`播放热度领先，适合下钻相关内容与创作者`;
  const rate=play?interactions/play*100:0;
  return rate>=3?`互动率约 ${rate.toFixed(1)}%，互动效率突出`:`播放进入榜单，建议结合标题、封面与评论判断走红机制`;
 }

 function videoCover(item){
  const cover=safeImageUrl(item.coverUrl),source=safeHttpUrl(item.sourceUrl),tag=source?"a":"div",attrs=source?` href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer" aria-label="在新标签页打开${escapeHtml(item.title)}的抖音原视频"`:` aria-hidden="true"`;
  return `<${tag} class="douyin-hot-cover ${cover?"has-image":""}"${attrs}>${cover?`<img src="${escapeHtml(cover)}" alt="${escapeHtml(item.title)}视频封面" referrerpolicy="no-referrer">`:`<b>视频</b>`}<i>▶</i></${tag}>`;
 }

 function manualEditButton(item){return `<button type="button" class="douyin-manual-edit" data-manual-edit="${escapeHtml(item.itemId)}">人工修改</button>`}
 function videoRows(){return currentItems().map((item,index)=>`<li class="douyin-hot-row"><span class="douyin-hot-rank">${index+1}</span>${videoCover(item)}<div class="douyin-hot-content"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.author)}${item.tags?.length?` · ${item.tags.map(tag=>`<span>#${escapeHtml(tag)}</span>`).join(" ")}`:""}</p><div class="douyin-hot-metrics"><span>播放 <b>${fmt(item.playCount)}</b></span><span>点赞 <b>${fmt(item.likeCount)}</b></span><span>评论 <b>${fmt(item.commentCount)}</b></span><span>分享 <b>${fmt(item.shareCount)}</b></span></div><div class="douyin-entity-chips">${entityChips(item)}${manualEditButton(item)}</div></div><p class="douyin-hot-signal"><span>走红信号</span>${escapeHtml(signal(item))}</p></li>`).join("")}
 function topicRows(){return currentItems().map((item,index)=>`<li class="douyin-hot-row topic"><span class="douyin-hot-rank">${index+1}</span><div class="douyin-hot-cover" aria-hidden="true"><b>#</b><small>${escapeHtml(item.title)}</small></div><div class="douyin-hot-content"><h3>#${escapeHtml(item.title)}</h3><p>投稿创作者 ${fmt(item.creatorCount)} 人 · 投稿 ${fmt(item.publishCount)} 条</p><div class="douyin-hot-metrics"><span>播放 <b>${fmt(item.playCount)}</b></span><span>点赞 <b>${fmt(item.likeCount)}</b></span><span>评论 <b>${fmt(item.commentCount)}</b></span><span>分享 <b>${fmt(item.shareCount)}</b></span></div><div class="douyin-entity-chips">${entityChips(item)}${manualEditButton(item)}</div></div><p class="douyin-hot-signal"><span>传播含义</span>${escapeHtml(signal(item))}</p></li>`).join("")}

 function rankingPreview(){
  const items=currentItems().slice(0,3),total=currentItems().length;
  const preview=items.length?items.map((item,index)=>`<span><b>${index+1}</b><em>${state.view==="topics"?"#":""}${escapeHtml(item.title)}</em></span>`).join(""):`<span class="empty"><em>榜单数据同步后可在这里快速预览前三名</em></span>`;
  return `<button type="button" class="douyin-ranking-preview" data-ranking-toggle aria-expanded="false" aria-controls="douyin-ranking-content"><span class="douyin-ranking-preview__items"><small>TOP 3 快览</small>${preview}</span><span class="douyin-ranking-preview__action"><em>${total?`共 ${total} 条`:`查看榜单`}</em><strong>展开完整榜单<i aria-hidden="true"></i></strong></span></button>`;
 }

 function insight(){const copy={"24h":["用于捕捉突发爆款和快速升温的话题。","结合24小时排名变化，判断内容是否仍在加速。","优先下钻高互动视频的封面、标题和评论。"],"7d":["用于判断内容结构是否持续，而非只看单条爆发。","对比品牌车型的上榜次数与最高排名。","把稳定高热主题与现有NSR机会交叉验证。"],"30d":["用于识别稳定母题、创作者供给和长期品牌占位。","与7天榜对比，区分长期热门与近期异动。","月度热度属于传播证据，不直接代表购车需求或销量。"]};return `<aside class="douyin-hot-insight"><span class="douyin-hot-insight__eyebrow">MMN 传播信号</span><h3>${ranges[state.range]}热点怎么用</h3><ol>${copy[state.range].map(text=>`<li>${escapeHtml(text)}</li>`).join("")}</ol><div><b>策略边界</b><p>榜单说明“有人在看、在聊、在参与”，不直接等于市场需求、购车意向或销量。</p></div></aside>`}

 function listBody(){
  const scope=rankingState[dataKey()]||{};
  if(scope.loading&&!scope.data)return `<div class="douyin-hot-empty"><b>正在读取${ranges[state.range]}真实榜单…</b><span>榜单返回后将自动触发品牌车型识别。</span></div>`;
  if(scope.error)return `<div class="douyin-hot-empty error"><b>榜单读取失败</b><span>${escapeHtml(scope.error)}</span></div>`;
  if(!scope.data?.available)return `<div class="douyin-hot-empty"><b>该时间维度尚未同步真实榜单</b><span>请先在已登录的抖音创作者中心同步“汽车”类目数据；系统不会用其他时间维度或样例数据代替。</span></div>`;
  return `<ol>${state.view==="videos"?videoRows():topicRows()}</ol>`;
 }

 function bind(){
  mount.querySelectorAll("[data-hot-view]").forEach(button=>button.onclick=()=>{state.view=button.dataset.hotView;state.rankingExpanded=false;manualReviewState.open=false;render();setTimeout(requestRecognition,RECOGNITION_DELAY_MS)});
  mount.querySelectorAll("[data-hot-range]").forEach(button=>button.onclick=()=>{state.range=button.dataset.hotRange;state.rankingExpanded=false;manualReviewState.open=false;render();loadRange(state.range)});
  mount.querySelectorAll(".douyin-hot-cover img").forEach(image=>image.onerror=()=>{const cover=image.closest(".douyin-hot-cover");cover?.classList.remove("has-image");if(cover&&!cover.querySelector("b")){const label=document.createElement("b");label.textContent="封面失效";cover.insertBefore(label,cover.querySelector("i"))}image.remove()});
  mount.querySelector("[data-collector-connect]")?.addEventListener("click",connectCollector);
  mount.querySelector("[data-collector-sync]")?.addEventListener("click",()=>startCollectorSync(false));
  mount.querySelector("[data-collector-force]")?.addEventListener("click",()=>startCollectorSync(true));
  mount.querySelector("[data-manual-review-open]")?.addEventListener("click",()=>openManualReview());
  mount.querySelectorAll("[data-manual-edit]").forEach(button=>button.addEventListener("click",()=>openManualReview(button.dataset.manualEdit)));
  mount.querySelector("[data-ranking-toggle]")?.addEventListener("click",()=>{state.rankingExpanded=!state.rankingExpanded;render();mount.querySelector("[data-ranking-toggle]")?.focus()});
  mount.querySelector("[data-manual-review-close]")?.addEventListener("click",closeManualReview);
  mount.querySelectorAll("[data-manual-review-item]").forEach(button=>button.addEventListener("click",()=>{manualReviewState.selectedId=button.dataset.manualReviewItem;manualReviewState.error="";manualReviewState.message="";render()}));
  mount.querySelector("[data-manual-confirm]")?.addEventListener("click",()=>submitManualReview("confirm"));
  mount.querySelector("[data-manual-exclude]")?.addEventListener("click",()=>submitManualReview("exclude"));
 }

 function render(){
  const snapshot=currentSnapshot(),source=safeHttpUrl(snapshot?.sourceUrl),capturedDate=snapshot?.capturedAt?new Date(snapshot.capturedAt):null,captured=capturedDate&&!Number.isNaN(capturedDate.getTime())?capturedDate.toLocaleString("zh-CN",{hour12:false}):(snapshot?.capturedAt||"尚未同步");
  const rankingTitle=state.view==="videos"?"热门视频排行榜":"热门话题排行榜";
  mount.innerHTML=`<article class="panel douyin-hot-panel"><header class="douyin-hot-head"><div><span>DOUYIN AUTO PULSE</span><h2 id="douyin-hot-title">抖音汽车热点</h2><p>热门视频与热门话题双榜，帮助客户快速看清近期内容风向。</p></div><div class="douyin-collector-actions"><em class="${collectorState.browserOpen?"connected":""}"><i></i>${collectorState.browserOpen?"采集器窗口已连接":"抖音账号未连接"}</em><button type="button" data-collector-connect>${collectorState.browserOpen?"重新打开登录窗口":"连接抖音账号"}</button><button type="button" class="primary" data-collector-sync ${!collectorState.browserOpen||collectorRunning()||collectorState.freshToday?"disabled":""}>${collectorRunning()?"同步进行中…":collectorState.freshToday?"今日已更新":"更新今日榜单"}</button><button type="button" data-collector-force ${!collectorState.browserOpen||collectorRunning()?"disabled":""}>强制刷新</button></div></header>${collectorProgress()}<div class="douyin-hot-controls">${tabs()}</div>${summary()}${entityRadar()}${manualReviewPanel()}<div class="douyin-hot-layout ${state.rankingExpanded?"is-expanded":"is-collapsed"}"><section class="douyin-hot-list" aria-live="polite"><div class="douyin-hot-list__head"><div><b>${rankingTitle}</b><span>${ranges[state.range]} · 汽车类目 · 按播放热度 · 同步于 ${escapeHtml(captured)}</span></div>${state.rankingExpanded?`<button type="button" class="douyin-ranking-close" data-ranking-toggle aria-expanded="true" aria-controls="douyin-ranking-content" aria-label="收起${rankingTitle}"><span>收起榜单</span><i aria-hidden="true"></i></button>`:""}</div><div id="douyin-ranking-content">${state.rankingExpanded?listBody():rankingPreview()}</div></section>${state.rankingExpanded?insight():""}</div><footer><span>刷新频率：每日一次，同时更新24小时、7天与30天六个榜单；登录不会触发重复抓取。</span>${source?`<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">查看原始数据源 ↗</a>`:`<span>等待数据源同步</span>`}</footer></article>`;
  bind();
 }

 render();
 loadRange(state.range);
 loadCollectorStatus();
})();
