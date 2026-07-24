(function(){
 const mount=document.querySelector("#douyin-hot-module-mount");
 if(!mount)return;
 const ranges={"24h":"24小时","7d":"7天","30d":"30天"};
 const RECOGNITION_DELAY_MS=300;
 const state={range:"24h",view:"videos",workspace:"ranking",rankingExpanded:false};
 const rankingState={};
 const rankingRequests={};
 const recognitionState={};
 const manualReviewState={open:false,loading:false,saving:false,items:[],selectedId:"",message:"",error:""};
 const defenseState={jobs:[],loading:false,error:"",pollTimer:0};
 const videoInsightState={jobs:[],loading:false,error:"",pollTimer:0,openItems:new Set()};
 const creationState={plans:[],loading:false,error:"",pollTimer:0,dialog:{open:false,insightJobId:"",saving:false,values:{}},creatorAssets:[],creatorsLoading:false,creatorSelections:{},externalUrl:"",externalSubmitting:false,filters:{query:"",status:"all",favoriteOnly:false},compare:new Set()};
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
  loadContentDefense();loadVideoInsights();
  setTimeout(requestRecognition,RECOGNITION_DELAY_MS);
 }

 async function loadVideoInsights(){
  if(state.workspace==="ranking"&&state.view!=="videos"){videoInsightState.jobs=[];clearTimeout(videoInsightState.pollTimer);return}
  videoInsightState.loading=true;videoInsightState.error="";
  try{
   const response=await api(`/api/douyin-hot/video-insights?edition=${encodeURIComponent(editionKey())}`);
   videoInsightState.jobs=response.result?.jobs||[];scheduleVideoInsightPoll();
  }catch(error){videoInsightState.error=error?.message||String(error)}
  videoInsightState.loading=false;render();
 }
 function videoInsightRunning(){return videoInsightState.jobs.some(job=>["queued","resolving_video","extracting_media","transcribing","building_evidence","analyzing","cross_validating"].includes(job.status))}
 function scheduleVideoInsightPoll(){clearTimeout(videoInsightState.pollTimer);if(videoInsightRunning())videoInsightState.pollTimer=setTimeout(loadVideoInsights,1200)}
 async function startVideoInsight(itemId,force=false,retrySlot=""){
  videoInsightState.error="";
  try{
   const response=await api("/api/douyin-hot/video-insights/jobs",{method:"POST",body:JSON.stringify({edition:editionKey(),view:"videos",range:state.range,itemId,force,retrySlot,generateCoverPrompt:true})});
   videoInsightState.jobs=[response.job,...videoInsightState.jobs.filter(job=>job.jobId!==response.job?.jobId)];
   videoInsightState.openItems.add(String(itemId));render();scheduleVideoInsightPoll();
  }catch(error){videoInsightState.error=error?.message||String(error);render()}
 }
 async function reviewVideoInsight(jobId,slot){
  const note=window.prompt("请记录采用该判断的人工复核依据：","");if(note===null)return;
  try{
   const response=await api(`/api/douyin-hot/video-insights/jobs/${encodeURIComponent(jobId)}/review`,{method:"POST",body:JSON.stringify({action:"confirm",selectedSlot:Number(slot),note})});
   videoInsightState.jobs=[response.job,...videoInsightState.jobs.filter(job=>job.jobId!==response.job?.jobId)];render();
  }catch(error){videoInsightState.error=error?.message||String(error);render()}
 }

 async function loadCreationPlans(){
  creationState.loading=true;creationState.error="";
  try{
   const response=await api(`/api/douyin-hot/creation-plans?edition=${encodeURIComponent(editionKey())}`);
   creationState.plans=response.result?.plans||[];scheduleCreationPoll();
  }catch(error){creationState.error=error?.message||String(error)}
  creationState.loading=false;render();
 }
 function creationRunning(){return creationState.plans.some(plan=>["queued","drafting","reviewing","finalizing"].includes(plan.status))}
 function scheduleCreationPoll(){clearTimeout(creationState.pollTimer);if(creationRunning())creationState.pollTimer=setTimeout(loadCreationPlans,1200)}
 function creationPlansForInsight(jobId){return creationState.plans.filter(plan=>String(plan.insightJobId)===String(jobId))}
 async function loadCreationCreators(){
  if(creationState.creatorsLoading||creationState.creatorAssets.length)return;
  creationState.creatorsLoading=true;
  try{
   const response=await api(`/api/content-capability-kb?edition=${encodeURIComponent(editionKey())}`);
   creationState.creatorAssets=response.creatorAssets||response.result?.creatorAssets||[];
  }catch(error){creationState.error=error?.message||String(error)}
  creationState.creatorsLoading=false;render();
 }
 async function submitExternalVideo(){
  if(creationState.externalSubmitting)return;
  const sourceUrl=mount.querySelector("[data-external-video-url]")?.value?.trim()||"";
  creationState.externalUrl=sourceUrl;
  if(!sourceUrl){creationState.error="请粘贴具体的抖音视频链接。";render();return}
  creationState.externalSubmitting=true;creationState.error="";render();
  try{
   const response=await api("/api/douyin-hot/video-insights/external",{method:"POST",body:JSON.stringify({edition:editionKey(),sourceUrl,generateCoverPrompt:true})});
   videoInsightState.jobs=[response.job,...videoInsightState.jobs.filter(job=>job.jobId!==response.job?.jobId)];
   creationState.externalUrl="";creationState.externalSubmitting=false;render();scheduleVideoInsightPoll();
  }catch(error){creationState.error=error?.message||String(error);creationState.externalSubmitting=false;render()}
 }
 async function retryExternalVideo(jobId){
  creationState.error="";
  try{
   const response=await api(`/api/douyin-hot/video-insights/jobs/${encodeURIComponent(jobId)}/external-retry`,{method:"POST",body:"{}"});
   videoInsightState.jobs=[response.job,...videoInsightState.jobs.filter(job=>job.jobId!==response.job?.jobId)];render();scheduleVideoInsightPoll();
  }catch(error){creationState.error=error?.message||String(error);render()}
 }
 function openCreationDialog(insightJobId){
  creationState.dialog={open:true,insightJobId:String(insightJobId||""),saving:false,values:{}};
  creationState.error="";render();loadCreationCreators();
  requestAnimationFrame(()=>mount.querySelector("[data-creation-brand]")?.focus());
 }
 function closeCreationDialog(){creationState.dialog={open:false,insightJobId:"",saving:false,values:{}};creationState.error="";render()}
 async function submitCreationPlan(){
  if(creationState.dialog.saving)return;
  const values={
   edition:editionKey(),
   insightJobId:creationState.dialog.insightJobId,
   brand:mount.querySelector("[data-creation-brand]")?.value?.trim()||"",
   model:mount.querySelector("[data-creation-model]")?.value?.trim()||"",
   audience:mount.querySelector("[data-creation-audience]")?.value?.trim()||"",
   marketingTask:mount.querySelector("[data-creation-task]")?.value?.trim()||"",
   productBenefit:mount.querySelector("[data-creation-benefit]")?.value?.trim()||"",
   style:mount.querySelector("[data-creation-style]")?.value?.trim()||"真实、克制、可拍摄"
  };
  creationState.dialog.values=values;
  if(Object.entries(values).some(([key,value])=>key!=="edition"&&key!=="style"&&!value)){creationState.error="请完整填写品牌、车型、目标人群、营销任务和产品利益点。";render();return}
  creationState.dialog.saving=true;creationState.error="";render();
  try{
   const response=await api("/api/douyin-hot/creation-plans",{method:"POST",body:JSON.stringify(values)});
   creationState.plans=[response.plan,...creationState.plans.filter(plan=>plan.id!==response.plan?.id)];
   creationState.dialog={open:false,insightJobId:"",saving:false,values:{}};state.workspace="library";render();scheduleCreationPoll();
  }catch(error){creationState.error=error?.message||String(error);creationState.dialog.saving=false;render()}
 }
 async function retryCreationPlan(planId){
  creationState.error="";
  try{
   const response=await api(`/api/douyin-hot/creation-plans/${encodeURIComponent(planId)}/retry`,{method:"POST",body:"{}"});
   creationState.plans=[response.plan,...creationState.plans.filter(plan=>plan.id!==response.plan?.id)];render();scheduleCreationPoll();
  }catch(error){creationState.error=error?.message||String(error);render()}
 }
 async function createScriptFromPlan(planId,directionId){
  const creatorAssetId=mount.querySelector(`[data-creation-creator="${CSS.escape(String(planId))}"]`)?.value||"";
  if(!creatorAssetId){creationState.error="请选择用于生成脚本的达人方法资产。";render();return}
  creationState.error="";
  try{
   const response=await api(`/api/douyin-hot/creation-plans/${encodeURIComponent(planId)}/script`,{method:"POST",body:JSON.stringify({directionId,creatorAssetId,platform:"douyin"})});
   creationState.plans=[response.plan,...creationState.plans.filter(plan=>plan.id!==response.plan?.id)];render();
  }catch(error){creationState.error=error?.message||String(error);render()}
 }
 async function toggleCreationFavorite(planId){
  const plan=creationState.plans.find(row=>row.id===planId);if(!plan)return;
  creationState.error="";
  try{
   const response=await api(`/api/douyin-hot/creation-plans/${encodeURIComponent(planId)}/favorite`,{method:"POST",body:JSON.stringify({favorite:!plan.favorite})});
   creationState.plans=creationState.plans.map(row=>row.id===planId?response.plan:row);render();
  }catch(error){creationState.error=error?.message||String(error);render()}
 }
 function toggleCreationCompare(planId,checked){
  if(checked&&creationState.compare.size>=3){creationState.error="最多同时对比三条拆解资产。";render();return}
  checked?creationState.compare.add(planId):creationState.compare.delete(planId);creationState.error="";render();
 }

 async function loadContentDefense(){
  defenseState.loading=true;defenseState.error="";
  try{
   const response=await api(`/api/douyin-hot/content-defense?edition=${encodeURIComponent(editionKey())}&view=${encodeURIComponent(state.view)}&range=${encodeURIComponent(state.range)}`);
   defenseState.jobs=response.result?.jobs||[];
   scheduleDefensePoll();
  }catch(error){defenseState.error=error?.message||String(error)}
  defenseState.loading=false;render();
 }
 function defenseRunning(){return defenseState.jobs.some(job=>["queued","running"].includes(job.status))}
 function scheduleDefensePoll(){
  clearTimeout(defenseState.pollTimer);
  if(defenseRunning())defenseState.pollTimer=setTimeout(loadContentDefense,1200);
 }
 async function startContentDefense(itemId,force=false){
  defenseState.error="";
  try{
   const response=await api("/api/douyin-hot/content-defense/jobs",{method:"POST",body:JSON.stringify({edition:editionKey(),view:state.view,range:state.range,itemId,model:"奥迪E7X",force})});
   defenseState.jobs=[response.job,...defenseState.jobs.filter(job=>job.jobId!==response.job?.jobId)];render();scheduleDefensePoll();
  }catch(error){defenseState.error=error?.message||String(error);render()}
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
  return `<section class="douyin-manual-review" aria-live="polite"><header><div><span>MANUAL VERIFICATION</span><h3>人工核验工作台</h3><p>人工结论具有最高优先级，点击任一确认按钮后立即更新雷达。</p></div><button type="button" data-manual-review-close>关闭</button></header>${manualReviewState.message?`<p class="douyin-manual-message">${escapeHtml(manualReviewState.message)}</p>`:""}${manualReviewState.error?`<p class="douyin-manual-error">${escapeHtml(manualReviewState.error)}</p>`:""}<div class="douyin-manual-grid"><nav aria-label="榜单内容人工修改">${manualReviewState.items.map((row,index)=>`<button type="button" class="${row.itemId===item.itemId?"active":""}" data-manual-review-item="${escapeHtml(row.itemId)}"><span>${index+1}</span><b>${escapeHtml(row.title)}</b><small>${row.manualStatus==="published"?"已人工确认，可再次修改":row.status==="conflict"?"模型分歧，待人工确认":"可人工修改"}</small></button>`).join("")}</nav><article><span class="douyin-manual-rank">原榜单内容</span><h4>${escapeHtml(item.title)}</h4><div class="douyin-manual-comparison"><p><b>独立识别 A</b>${escapeHtml(mentionsText(item.primaryMentions))}</p><p><b>独立识别 B</b>${escapeHtml(mentionsText(item.reviewerMentions))}</p><p><b>当前归类</b>${escapeHtml(mentionsText(item.mentions))}</p></div><label>确认品牌<input data-manual-brand value="${escapeHtml(seed.brand||"")}" placeholder="例如：零跑"></label><label>确认车型<input data-manual-model value="${escapeHtml(seed.model||"")}" placeholder="品牌明确但车型不明确时可留空"></label><label>核验备注<textarea data-manual-note rows="2" placeholder="可记录判断依据">${escapeHtml(item.note||"")}</textarea></label><div class="douyin-manual-actions"><button type="button" class="primary" data-manual-confirm ${manualReviewState.saving?"disabled":""}>${manualReviewState.saving?"保存中…":"确认并进入雷达"}</button><button type="button" data-manual-exclude ${manualReviewState.saving?"disabled":""}>确认无明确品牌车型</button></div></article></div></section>`;
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

 function workspaceTabs(){return `<nav class="douyin-workspace-tabs" aria-label="抖音内容工作区"><button type="button" class="${state.workspace==="ranking"?"active":""}" data-creation-library="ranking" aria-current="${state.workspace==="ranking"?"page":"false"}">榜单发现</button><button type="button" class="${state.workspace==="library"?"active":""}" data-creation-library="library" aria-current="${state.workspace==="library"?"page":"false"}">爆款内容拆解库</button></nav>`}
 function tabs(){return `${workspaceTabs()}${state.workspace==="library"?"":`<div class="douyin-hot-tabs" role="tablist" aria-label="热点类型">${[["videos","热门视频"],["topics","热门话题"]].map(([key,label])=>`<button type="button" role="tab" aria-selected="${state.view===key}" class="${state.view===key?"active":""}" data-hot-view="${key}">${label}</button>`).join("")}</div><div class="douyin-hot-ranges" role="group" aria-label="时间范围">${Object.entries(ranges).map(([key,label])=>`<button type="button" aria-pressed="${state.range===key}" class="${state.range===key?"active":""}" data-hot-range="${key}">${label}</button>`).join("")}</div>`}`;}

 function summary(){
  const video=rankingState[dataKey("videos")]?.data?.items?.[0];
  const topic=rankingState[dataKey("topics")]?.data?.items?.[0];
  return `<div class="douyin-hot-kpis"><div><span>榜首视频播放</span><b>${video?fmt(video.playCount):"—"}</b><small>${escapeHtml(video?.author||"等待视频榜同步")}</small></div><div><span>榜首话题播放</span><b>${topic?fmt(topic.playCount):"—"}</b><small>${topic?`#${escapeHtml(topic.title)}`:"等待话题榜同步"}</small></div><div><span>话题参与创作者</span><b>${topic?fmt(topic.creatorCount):"—"}</b><small>${ranges[state.range]}真实榜单</small></div></div>`;
 }

 function topicSignal(item){return item.creatorCount?`${fmt(item.creatorCount)} 位创作者参与，观察内容供给与品牌占位`:`播放热度领先，适合下钻相关内容与创作者`}

 function videoCover(item){
  const cover=safeImageUrl(item.coverUrl),source=safeHttpUrl(item.sourceUrl),tag=source?"a":"div",attrs=source?` href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer" aria-label="在新标签页打开${escapeHtml(item.title)}的抖音原视频"`:` aria-hidden="true"`;
  return `<${tag} class="douyin-hot-cover ${cover?"has-image":""}"${attrs}>${cover?`<img src="${escapeHtml(cover)}" alt="${escapeHtml(item.title)}视频封面" referrerpolicy="no-referrer">`:`<b>视频</b>`}<i>▶</i></${tag}>`;
 }

 function manualEditButton(item){return `<button type="button" class="douyin-manual-edit" data-manual-edit="${escapeHtml(item.itemId)}">人工修改</button>`}
 function defenseJobFor(item){return defenseState.jobs.find(job=>String(job.itemId)===String(item.itemId))}
 function defenseAction(item){const job=defenseJobFor(item),running=["queued","running"].includes(job?.status);return `<button type="button" class="douyin-defense-action" data-defense-start="${escapeHtml(item.itemId)}" ${running?"disabled":""}>${running?`${job.progress||0}% · 证据整理中`:job?.status==="completed"?"重新核对内容防线":job?.status==="manual_required"?"补证后重新质检":"生成内容防线"}</button>`}
 function videoInsightJobFor(item){return videoInsightState.jobs.find(job=>String(job.itemId)===String(item.itemId))}
 function videoInsightStatus(job){
  const labels={queued:"待处理",resolving_video:"核对视频",extracting_media:"提取多模态证据",transcribing:"语音转写",building_evidence:"建立证据包",analyzing:"三路独立分析",cross_validating:"交叉校验",completed:"洞察已完成",limited_analysis:"有限分析",manual_required:"待人工复核",incomplete:"分析未完整",failed:"分析失败"};
  return labels[job?.status]||"待分析";
 }
 function customerInsightText(value){
  return String(value??"")
   .replace(/[（(]\s*(?:V:[a-f\d]{8,})(?:\s*[,，、/]\s*V:[a-f\d]{8,})*\s*[)）]/gi,"")
   .replace(/V:[a-f\d]{8,}/gi,"")
   .replace(/\s+([，。；：！？、])/g,"$1")
   .replace(/[（(]\s*[)）]/g,"")
   .replace(/\s{2,}/g," ")
   .trim();
 }
 function customerEvidenceCoverage(value){
  return {full:"完整证据",partial:"部分证据",limited:"有限证据",none:"未取得"}[String(value||"").toLowerCase()]||"未建立";
 }
 function customerEvidenceType(value){
  return {title:"标题",transcript:"字幕",subtitle:"字幕",comment:"评论",shot:"关键镜头",ocr:"画面文字",visual_summary:"画面摘要",visual_structure:"视觉结构"}[value]||"内容证据";
 }
 function customerLimitationText(value){
  const text=String(value||"");
  if(/file size is too large|文件.*过大/i.test(text))return "视频文件超过当前处理上限，暂未取得完整语音转写。";
  if(/非公网媒体地址/.test(text))return "原网页可播放，但后台尚未取得可直接分析的画面文件；视觉与关键镜头证据暂缺。";
  if(/不是 JSON 对象|JSON/.test(text))return "画面文字识别结果不完整，暂未形成可用证据。";
  if(/HTTP\s*400/i.test(text))return "视频证据暂未成功读取，可在处理能力恢复后重试。";
  if(/timeout|timed out|超时/i.test(text))return "证据处理超时，可稍后重试。";
  return customerInsightText(text.replace(/^\d{12,}\s*(?:转写|视觉|OCR)?\s*[:：]\s*/,""));
 }
 function videoRunStatusLabel(row,jobStatus){
  if(jobStatus==="limited_analysis"&&!row.output&&!row.error)return "未启动";
  return row.status==="completed"?"已完成":row.status==="failed"?"失败":"待处理";
 }
 function insightEvidence(packageValue){
  const refs=packageValue?.evidenceRefs||[],counts=refs.reduce((map,row)=>{map[row.type]=(map[row.type]||0)+1;return map},{});
  return `<div class="douyin-video-evidence"><span>${escapeHtml(customerEvidenceCoverage(packageValue?.evidenceCoverage))}</span><span>字幕 ${counts.transcript||counts.subtitle||0}</span><span>镜头 ${counts.shot||0}</span><span>画面文字 ${counts.ocr||0}</span><span>评论 ${counts.comment||0}</span></div>`;
 }
 function insightList(title,rows){return `<section><b>${title}</b>${rows?.length?`<ul>${rows.map(row=>`<li>${escapeHtml(customerInsightText(typeof row==="string"?row:JSON.stringify(row)))}</li>`).join("")}</ul>`:`<p>当前证据未形成该项判断。</p>`}</section>`}
 function coverPromptSection(value){
  if(!value)return "";
  const prompt=value.finalPrompt,status={verified:"已形成统一提示词",limited:"封面证据不足",incomplete:"三路分析未完整",manual_required:"存在分歧，待人工复核"}[value.status]||"暂未形成";
  return `<section class="douyin-cover-prompt"><b>封面图像 Prompt</b><p>${escapeHtml(status)}。${escapeHtml(customerInsightText(value.reason||""))}</p>${prompt?`<dl><dt>正向 Prompt</dt><dd>${escapeHtml(prompt.prompt||"")}</dd><dt>画面文字</dt><dd>${escapeHtml((prompt.ocrText||[]).join(" / ")||"无")}</dd><dt>负向 Prompt</dt><dd>${escapeHtml((prompt.negativePrompt||[]).join("，"))}</dd></dl>`:""}</section>`;
 }
 function videoInsightDetail(item,job){
  if(!job)return "";
  const validation=job.result?.validation||{},insight=validation.finalInsight||{},pkg=job.evidencePackage||{},runs=validation.runs||job.runStatus||[];
  const refs=pkg.evidenceRefs||[],disagreements=validation.disagreements||[];
  const plans=creationPlansForInsight(job.jobId),latest=plans[0],canCreate=job.status==="completed"&&["verified","majority_aligned","human_confirmed"].includes(validation.status);
  const creationCta=canCreate?`<section class="douyin-video-create-cta"><div><b>把洞察转成原创创作任务</b><p>只迁移结构和机制，不复制原视频表达；品牌与车型利益点仍需拍摄补证。</p></div><button type="button" data-creation-plan-open="${escapeHtml(job.jobId)}">${latest?"生成新的创作方向":"按此结构生成创作方向"}</button>${latest?`<button type="button" data-creation-library="library">查看已生成方向</button>`:""}</section>`:`<section class="douyin-video-create-cta disabled"><div><b>创作转化暂不可用</b><p>需要视频证据和关键判断通过MMN校验后才能生成，避免把有限观察包装成可执行方案。</p></div></section>`;
  return `<div class="douyin-video-insight-detail" ${videoInsightState.openItems.has(String(item.itemId))?"":"hidden"}>${insightEvidence(pkg)}<div class="douyin-video-insight-grid"><section><b>视频实际讲了什么</b><p>${escapeHtml(customerInsightText(insight.contentSummary||"当前尚未形成可发布摘要。"))}</p></section><section><b>开场钩子</b><p>${escapeHtml(customerInsightText(insight.openingHook||"证据不足"))}</p></section><section><b>叙事结构</b><p>${escapeHtml(customerInsightText(insight.narrativeStructure||"证据不足"))}</p></section><section><b>评论区反应</b><p>${escapeHtml(customerInsightText(insight.audienceResponse||"尚未取得可追溯评论样本"))}</p></section>${insightList("情绪与心理驱动",insight.emotionDrivers)}${insightList("走红机制",insight.viralMechanisms)}${insightList("品牌与车型角色",insight.brandAndModelRoles)}${insightList("营销启示",insight.marketingImplications)}${insightList("可借鉴方法",insight.reusablePatterns)}${insightList("照搬风险",insight.copyRisks)}</div><section class="douyin-video-quality"><b>MMN三旗舰交叉分析</b><div>${runs.map(row=>`<span class="${row.status}">${escapeHtml(row.label||`独立分析 ${row.slot}`)} · ${videoRunStatusLabel(row,job.status)}</span>`).join("")}</div><p>${escapeHtml(customerInsightText(validation.reason||job.message||""))}</p>${disagreements.length?`<ul>${disagreements.map(row=>`<li>${escapeHtml(customerInsightText(row.field))}：${escapeHtml(customerInsightText((row.opinions||[]).join(" / ")))}</li>`).join("")}`:""}${job.status==="incomplete"?`<div class="douyin-video-review-actions"><b>失败项安全重试</b>${runs.filter(row=>row.status==="failed").map(row=>`<button type="button" data-video-retry-item="${escapeHtml(item.itemId)}" data-video-retry-slot="${Number(row.slot)}">优先重试${escapeHtml(row.label)}</button>`).join("")}</div>`:""}${job.status==="manual_required"?`<div class="douyin-video-review-actions"><b>人工复核入口</b>${runs.filter(row=>row.status==="completed"&&row.output).map(row=>`<button type="button" data-video-review-job="${escapeHtml(job.jobId)}" data-video-review-slot="${Number(row.slot)}">采用${escapeHtml(row.label)}</button>`).join("")}</div>`:job.manualReview?`<p>人工已确认采用 ${escapeHtml(`MMN独立分析 ${job.manualReview.selectedSlot}`)}；原始分歧继续保留。</p>`:""}</section>${creationCta}${coverPromptSection(job.result?.coverPrompt)}<section class="douyin-video-refs"><b>引用证据</b>${refs.length?`<ol>${refs.slice(0,16).map(row=>`<li><span>${escapeHtml(customerEvidenceType(row.type))}</span>${escapeHtml(customerInsightText(row.quote))}${Number.isFinite(row.timestampMs)?` · ${Math.floor(row.timestampMs/1000)}秒`:""}<small>${row.sourceScope==="video_body"?"视频本体":row.sourceScope==="cover"?"封面":"榜单/评论"}</small></li>`).join("")}</ol>`:`<p>尚未取得可引用内容证据。</p>`}</section>${(insight.limitations||pkg.extractionErrors||[]).length?`<section class="douyin-video-limitations"><b>分析边界</b><ul>${[...new Set((insight.limitations||pkg.extractionErrors||[]).map(customerLimitationText).filter(Boolean))].map(row=>`<li>${escapeHtml(row)}</li>`).join("")}</ul></section>`:""}</div>`;
 }
 function videoInsightBlock(item){
  const job=videoInsightJobFor(item),running=job&&["queued","resolving_video","extracting_media","transcribing","building_evidence","analyzing","cross_validating"].includes(job.status),insight=job?.result?.validation?.finalInsight;
  const summary=customerInsightText(!job?"按需分析：点击“生成洞察”后才会提取证据并调用MMN三旗舰。":running?(job.message||"正在分析"):insight?.contentSummary||(job.message||"当前未形成可发布洞察。")),source=safeHttpUrl(item.sourceUrl),open=videoInsightState.openItems.has(String(item.itemId));
  return `<div class="douyin-video-insight ${job?.status||"pending"}"><div class="douyin-video-insight-summary"><div><span>${escapeHtml(videoInsightStatus(job))}${running?` · ${Number(job.progress)||0}%`:""}</span><p>${escapeHtml(summary)}</p></div><div class="douyin-video-insight-actions">${source?`<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">打开原视频</a>`:`<button type="button" disabled title="原视频地址缺失">原视频不可访问</button>`}<button type="button" data-video-insight-start="${escapeHtml(item.itemId)}" ${running?"disabled":""}>${running?"分析中…":job?"重新分析":"生成洞察"}</button>${job?`<button type="button" data-video-insight-toggle="${escapeHtml(item.itemId)}" aria-expanded="${open}">${open?"收起":"查看完整洞察"}</button>`:""}</div></div>${running?`<div class="douyin-video-progress" role="progressbar" aria-label="逐视频洞察进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Number(job.progress)||0}"><i style="width:${Number(job.progress)||0}%"></i></div>`:""}${videoInsightDetail(item,job)}</div>`;
 }
 function videoRows(){return currentItems().map((item,index)=>`<li class="douyin-hot-row"><span class="douyin-hot-rank">${index+1}</span>${videoCover(item)}<div class="douyin-hot-content"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.author)}${item.tags?.length?` · ${item.tags.map(tag=>`<span>#${escapeHtml(tag)}</span>`).join(" ")}`:""}</p><small class="douyin-metrics-label">传播表现</small><div class="douyin-hot-metrics"><span>播放 <b>${fmt(item.playCount)}</b></span><span>点赞 <b>${fmt(item.likeCount)}</b></span><span>评论 <b>${fmt(item.commentCount)}</b></span><span>分享 <b>${fmt(item.shareCount)}</b></span></div><div class="douyin-entity-chips">${entityChips(item)}${manualEditButton(item)}${defenseAction(item)}</div></div>${videoInsightBlock(item)}</li>`).join("")}
 function topicRows(){return currentItems().map((item,index)=>`<li class="douyin-hot-row topic"><span class="douyin-hot-rank">${index+1}</span><div class="douyin-hot-cover" aria-hidden="true"><b>#</b><small>${escapeHtml(item.title)}</small></div><div class="douyin-hot-content"><h3>#${escapeHtml(item.title)}</h3><p>投稿创作者 ${fmt(item.creatorCount)} 人 · 投稿 ${fmt(item.publishCount)} 条</p><div class="douyin-hot-metrics"><span>播放 <b>${fmt(item.playCount)}</b></span><span>点赞 <b>${fmt(item.likeCount)}</b></span><span>评论 <b>${fmt(item.commentCount)}</b></span><span>分享 <b>${fmt(item.shareCount)}</b></span></div><div class="douyin-entity-chips">${entityChips(item)}${manualEditButton(item)}</div></div><p class="douyin-hot-signal"><span>传播含义</span>${escapeHtml(topicSignal(item))}</p></li>`).join("")}

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

 function creationStatusLabel(plan){
  return {queued:"等待生成",drafting:"提炼原创方向",reviewing:"检查事实与照搬风险",finalizing:"形成可拍摄方案",completed:"创作方向已完成",failed:"生成失败"}[plan?.status]||"等待处理";
 }
 function creatorOptions(planId){
  const selected=creationState.creatorSelections[planId]||"";
  if(creationState.creatorsLoading)return `<option value="">正在读取达人方法资产…</option>`;
  if(!creationState.creatorAssets.length)return `<option value="">暂无可用达人方法资产</option>`;
  return `<option value="">选择达人方法资产</option>${creationState.creatorAssets.map(asset=>`<option value="${escapeHtml(asset.id)}" ${String(asset.id)===String(selected)?"selected":""}>${escapeHtml(asset.account_name||"待确认达人")} · ${escapeHtml(asset.platform||"公开平台")} · ${Number(asset.sample_count)||0}条样本</option>`).join("")}`;
 }
 function creationDirectionCard(plan,direction,index){
  const steps=(direction.structureSteps||[]).map(step=>`<li><span>${escapeHtml(step.timing||"")}</span><div><b>${escapeHtml(step.purpose||"")}</b><p>${escapeHtml(step.content||"")}</p></div></li>`).join("");
  const scriptDisabled=!creationState.creatorSelections[plan.id];
  return `<article class="douyin-creation-direction"><header><span>方向 ${index+1}</span><h4>${escapeHtml(direction.title||"待命名方向")}</h4><p>${escapeHtml(direction.coreIdea||"")}</p></header><div class="douyin-creation-hook"><b>开场钩子</b><p>${escapeHtml(direction.openingHook||"")}</p></div><ol class="douyin-creation-timeline">${steps}</ol><div class="douyin-creation-direction-grid"><section><b>产品植入</b><p>${escapeHtml(direction.productIntegration||"")}</p></section><section><b>情绪触发</b><p>${escapeHtml(direction.emotionTrigger||"")}</p></section><section><b>结尾互动</b><p>${escapeHtml(direction.endingInteraction||"")}</p></section><section><b>画面建议</b><ul>${(direction.visualSuggestions||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join("")}</ul></section><section><b>可迁移方法</b><ul>${(direction.transferNotes||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join("")}</ul></section><section><b>照搬风险</b><ul>${(direction.copyRisks||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join("")}</ul></section></div><footer><button type="button" data-creation-script="${escapeHtml(plan.id)}" data-creation-direction="${escapeHtml(direction.id)}" ${scriptDisabled?"disabled":""}>继续生成完整脚本</button></footer></article>`;
 }
 function creationPlanCard(plan){
  const running=["queued","drafting","reviewing","finalizing"].includes(plan.status),source=plan.source||{},request=plan.request||{},directions=plan.result?.directions||[];
  const selected=creationState.compare.has(plan.id);
  return `<article class="douyin-creation-plan ${plan.status||"queued"}"><header><div><span>${escapeHtml(creationStatusLabel(plan))}</span><h3>${escapeHtml(source.title||`${request.brand||""} ${request.model||""}创作方向`)}</h3><p>${escapeHtml(source.author||"来源视频")} · ${escapeHtml(request.brand||"未填写品牌")} / ${escapeHtml(request.model||"未填写车型")}</p></div><div class="douyin-creation-plan-actions"><label><input type="checkbox" data-creation-compare="${escapeHtml(plan.id)}" ${selected?"checked":""}>加入对比</label><button type="button" data-creation-favorite="${escapeHtml(plan.id)}" aria-pressed="${plan.favorite?"true":"false"}">${plan.favorite?"已收藏":"收藏"}</button>${safeHttpUrl(source.sourceUrl)?`<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">打开原视频</a>`:""}</div></header><div class="douyin-creation-source"><b>来源机制</b><p>${escapeHtml(source.primaryMechanism||source.contentSummary||"等待读取来源洞察")}</p><span>${escapeHtml(request.audience||"")}</span><span>${escapeHtml(request.marketingTask||"")}</span></div>${running?`<div class="douyin-creation-progress" role="progressbar" aria-label="创作方向生成进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Number(plan.progress)||0}"><i style="width:${Number(plan.progress)||0}%"></i><span>${Number(plan.progress)||0}% · ${escapeHtml(plan.message||creationStatusLabel(plan))}</span></div>`:""}${plan.status==="failed"?`<div class="douyin-creation-failure"><p>${escapeHtml(plan.error||"当前生成未完成。")}</p><button type="button" data-creation-retry="${escapeHtml(plan.id)}">安全重试</button></div>`:""}${directions.length?`<div class="douyin-creation-script-bridge"><label>完整脚本需要结合达人表达方法<select data-creation-creator="${escapeHtml(plan.id)}">${creatorOptions(plan.id)}</select></label>${plan.scriptJobId?`<p>已进入完整脚本任务：${escapeHtml(plan.scriptJobId)}</p>`:""}</div><div class="douyin-creation-directions">${directions.map((direction,index)=>creationDirectionCard(plan,direction,index)).join("")}</div><p class="douyin-creation-boundary">只迁移结构和机制，不复制原视频文案、镜头组合或人物身份；产品利益点仍需白皮书或拍摄证据支持。</p>`:""}</article>`;
 }
 function filteredCreationPlans(){
  const filters=creationState.filters,query=String(filters.query||"").toLowerCase();
  return creationState.plans.filter(plan=>{
   const running=["queued","drafting","reviewing","finalizing"].includes(plan.status);
   if(filters.status==="completed"&&plan.status!=="completed")return false;
   if(filters.status==="running"&&!running)return false;
   if(filters.status==="failed"&&plan.status!=="failed")return false;
   if(filters.favoriteOnly&&!plan.favorite)return false;
   if(!query)return true;
   const source=plan.source||{},request=plan.request||{},directions=plan.result?.directions||[];
   return JSON.stringify([source.title,source.author,source.primaryMechanism,request.brand,request.model,request.audience,request.marketingTask,...directions.map(row=>row.title)]).toLowerCase().includes(query);
  });
 }
 function creationComparePanel(){
  const plans=creationState.plans.filter(plan=>creationState.compare.has(plan.id));
  if(plans.length<2)return "";
  return `<section class="douyin-creation-compare"><header><div><b>结构对比</b><p>并排检查来源机制、目标人群、营销任务与三条方向，不把热度差异解释成因果。</p></div><button type="button" data-creation-compare-clear>清空对比</button></header><div>${plans.map(plan=>`<article><h4>${escapeHtml(plan.source?.title||plan.request?.model||"创作资产")}</h4><dl><dt>来源机制</dt><dd>${escapeHtml(plan.source?.primaryMechanism||"未形成")}</dd><dt>目标人群</dt><dd>${escapeHtml(plan.request?.audience||"")}</dd><dt>营销任务</dt><dd>${escapeHtml(plan.request?.marketingTask||"")}</dd><dt>创作方向</dt><dd>${escapeHtml((plan.result?.directions||[]).map(row=>row.title).join("；")||"生成中")}</dd></dl></article>`).join("")}</div></section>`;
 }
 function creationFilters(){
  const filters=creationState.filters;
  return `<form class="douyin-creation-filters" data-creation-filter-form><input type="search" data-creation-filter-query value="${escapeHtml(filters.query||"")}" placeholder="搜索品牌、车型、题材或走红机制" aria-label="搜索拆解资产"><select data-creation-filter-status aria-label="创作资产状态"><option value="all" ${filters.status==="all"?"selected":""}>全部状态</option><option value="completed" ${filters.status==="completed"?"selected":""}>已完成</option><option value="running" ${filters.status==="running"?"selected":""}>生成中</option><option value="failed" ${filters.status==="failed"?"selected":""}>失败</option></select><label><input type="checkbox" data-creation-filter-favorite ${filters.favoriteOnly?"checked":""}>仅看收藏</label><button type="submit">筛选</button><button type="button" data-creation-filter-clear>清除</button></form>`;
 }
 function externalInsightCard(job){
  const running=["queued","resolving_video","extracting_media","transcribing","building_evidence","analyzing","cross_validating"].includes(job.status),validation=job.result?.validation||{},pkg=job.evidencePackage||{},canCreate=job.status==="completed"&&["verified","majority_aligned","human_confirmed"].includes(validation.status),plans=creationPlansForInsight(job.jobId),source=safeHttpUrl(pkg.sourceUrl);
  return `<article class="douyin-external-insight ${job.status||"queued"}"><div><span>${escapeHtml(videoInsightStatus(job))}</span><h4>${escapeHtml(pkg.title||`抖音视频 ${job.itemId}`)}</h4><p>${escapeHtml(pkg.author||"等待取得视频作者")} · ${escapeHtml(job.message||"")}</p></div>${running?`<div class="douyin-creation-progress" role="progressbar" aria-label="排行榜外视频分析进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Number(job.progress)||0}"><i style="width:${Number(job.progress)||0}%"></i><span>${Number(job.progress)||0}% · ${escapeHtml(job.message||"正在分析")}</span></div>`:""}<footer>${source?`<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">打开原视频</a>`:""}${canCreate?`<button type="button" data-creation-plan-open="${escapeHtml(job.jobId)}">${plans.length?"生成新的创作方向":"按此结构生成创作方向"}</button>`:""}${job.retryable&&!running?`<button type="button" data-external-video-retry="${escapeHtml(job.jobId)}">安全重试</button>`:""}</footer></article>`;
 }
 function externalInsightPanel(){
  const jobs=videoInsightState.jobs.filter(job=>job.range==="external");
  return `<section class="douyin-external-video"><header><div><b>分析排行榜外的视频</b><p>粘贴具体抖音视频链接，仍按同一证据、降级和人工复核标准处理。</p></div><form data-external-video-form><input type="url" data-external-video-url value="${escapeHtml(creationState.externalUrl||"")}" placeholder="https://www.douyin.com/video/..." aria-label="抖音视频链接"><button type="submit" ${creationState.externalSubmitting?"disabled":""}>${creationState.externalSubmitting?"提交中…":"开始拆解"}</button></form></header>${jobs.length?`<div class="douyin-external-insight-list">${jobs.map(externalInsightCard).join("")}</div>`:""}</section>`;
 }
 function creationLibrary(){
  const plans=filteredCreationPlans(),allPlans=creationState.plans;
  return `<section class="douyin-creation-library" aria-live="polite"><header><div><span>CONTENT BREAKDOWN LIBRARY</span><h2>爆款内容拆解库</h2><p>排行榜负责发现，这里管理已验证的视频结构、原创方向和脚本衔接。</p></div><button type="button" data-creation-library="ranking">返回榜单发现</button></header>${creationState.error?`<p class="douyin-creation-error">${escapeHtml(creationState.error)}</p>`:""}${externalInsightPanel()}${creationFilters()}${creationComparePanel()}${creationState.loading&&!allPlans.length?`<div class="douyin-creation-empty">正在读取创作资产…</div>`:plans.length?`<div class="douyin-creation-plan-list">${plans.map(creationPlanCard).join("")}</div>`:allPlans.length?`<div class="douyin-creation-empty"><b>没有符合当前条件的资产</b><p>调整搜索词、状态或收藏筛选后重试。</p><button type="button" data-creation-filter-clear>清除筛选</button></div>`:`<div class="douyin-creation-empty"><b>还没有创作方向资产</b><p>返回热门视频榜，先完成单视频洞察，再点击“按此结构生成创作方向”。</p><button type="button" data-creation-library="ranking">去排行榜发现视频</button></div>`}</section>`;
 }
 function creationDialog(){
  if(!creationState.dialog.open)return "";
  const values=creationState.dialog.values||{};
  return `<div class="douyin-creation-dialog-backdrop"><section class="douyin-creation-dialog" role="dialog" aria-modal="true" aria-labelledby="douyin-creation-dialog-title"><header><div><span>CREATIVE BRIEF</span><h3 id="douyin-creation-dialog-title">生成原创创作方向</h3><p>来源视频只提供结构与机制参考，产品利益点不自动视为事实。</p></div><button type="button" data-creation-dialog-close aria-label="关闭创作方向表单">关闭</button></header>${creationState.error?`<p class="douyin-creation-error">${escapeHtml(creationState.error)}</p>`:""}<form data-creation-form><div class="douyin-creation-form-grid"><label>品牌<input data-creation-brand autocomplete="organization" placeholder="例如：上汽奥迪" value="${escapeHtml(values.brand||"")}"></label><label>车型<input data-creation-model placeholder="例如：奥迪E7X" value="${escapeHtml(values.model||"")}"></label><label>目标人群<textarea data-creation-audience rows="2" placeholder="描述需要影响的具体用户">${escapeHtml(values.audience||"")}</textarea></label><label>营销任务<textarea data-creation-task rows="2" placeholder="希望改变什么判断或行动">${escapeHtml(values.marketingTask||"")}</textarea></label><label class="wide">核心产品利益点及补证要求<textarea data-creation-benefit rows="3" placeholder="说明想表达的利益点，以及哪些部分需要白皮书、实拍或到店验证">${escapeHtml(values.productBenefit||"")}</textarea></label><label class="wide">内容风格<input data-creation-style value="${escapeHtml(values.style||"真实、克制、可拍摄")}"></label></div><p>系统将输出三条差异化方向：开场钩子、内容时间轴、产品植入、情绪触发、画面建议、结尾互动和照搬风险。</p><footer><button type="button" data-creation-dialog-close>取消</button><button type="submit" class="primary" ${creationState.dialog.saving?"disabled":""}>${creationState.dialog.saving?"提交中…":"生成三条创作方向"}</button></footer></form></section></div>`;
 }

 function evidenceStatus(result){
  const evidence=result?.evidencePackage?.evidence||[],available=type=>evidence.filter(row=>row.type===type&&row.status==="available").length;
  return [["V","视频"],["C","评论"],["N","属性NSR"],["W","白皮书"],["L","线索校验"]].map(([type,label])=>`<span class="${available(type)?"ready":"missing"}">${label} ${available(type)?`${available(type)}项`:"未取得"}</span>`).join("");
 }
 function jointEvidence(job,card){
  const rows=job.result?.evidencePackage?.evidence||[],ids=new Set(card.jointEvidenceIds||[]),labels={V:"视频",C:"评论",W:"白皮书"};
  return ["V","C","W"].map(type=>{
   const matched=rows.filter(row=>row.type===type&&row.status==="available"&&ids.has(row.evidenceId));
   if(!matched.length)return `<li><b>${labels[type]}</b>：未进入三重质检的共同证据，需补证。</li>`;
   return matched.slice(0,3).map(row=>`<li><b>${labels[type]}</b>：${escapeHtml(row.quote||row.subtype||"已取得")}${row.payload?.page?` · 第${Number(row.payload.page)}页`:""}${Number.isFinite(row.timestampMs)?` · ${Math.floor(row.timestampMs/1000)}s`:""}</li>`).join("");
  }).join("");
 }
 function defenseCard(job){
  const validation=job.result?.validation||{},card=validation.card,reasons=validation.reasons||[];
  if(!card)return `<article class="douyin-defense-card pending"><header><div><span>观察 / 待补证</span><h4>${escapeHtml(currentItems().find(item=>String(item.itemId)===String(job.itemId))?.title||job.itemId)}</h4></div><em>${escapeHtml(job.message||"等待分析")}</em></header><div class="douyin-defense-evidence">${evidenceStatus(job.result)}</div>${job.error?`<p class="error">${escapeHtml(job.error)}</p>`:""}${reasons.length?`<ul>${reasons.map(reason=>`<li>${escapeHtml(reason)}</li>`).join("")}</ul>`:`<p>${escapeHtml(job.message||"正在建立证据包")}</p>`}<footer><span>三重交叉质检：${validation.providersComplete?"已完整返回，待共同证据门禁":"未完整通过"}</span><button type="button" data-defense-start="${escapeHtml(job.itemId)}" ${["queued","running"].includes(job.status)?"disabled":""}>${["queued","running"].includes(job.status)?`${job.progress}%`:"重新质检"}</button></footer></article>`;
  const proof=(card.requiredProof||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join(""),challenges=(card.commentChallenges||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join(""),forbidden=(card.forbiddenClaims||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join(""),kpis=(card.kpis||[]).map(row=>`<li>${escapeHtml(row)}</li>`).join("");
  return `<article class="douyin-defense-card published"><header><div><span>${escapeHtml(card.judgementLabel)}</span><h4>${escapeHtml(card.hotClaim)}</h4></div><em>${escapeHtml(card.qualityStatus)}</em></header><div class="douyin-defense-attribute"><b>${escapeHtml(card.attribute)}</b><span>NSR ${Number(card.attributeNsr).toFixed(3)}</span><span>竞品差值 ${Number(card.competitorDelta)>=0?"+":""}${Number(card.competitorDelta).toFixed(3)}</span></div><div class="douyin-defense-evidence">${evidenceStatus(job.result)}</div><div class="douyin-defense-grid"><section><b>内容命题</b><p>${escapeHtml(card.contentProposition)}</p><small>${escapeHtml(card.titleStructure)}</small></section><section><b>视频 / 评论 / 白皮书共同证据</b><ul>${jointEvidence(job,card)}</ul></section><section><b>必须展示的产品证明</b><ul>${proof}</ul></section><section><b>评论区质疑</b><ul>${challenges||"<li>尚未取得可追溯评论样本，需补证。</li>"}</ul></section><section><b>禁用表述</b><ul>${forbidden}</ul></section><section><b>KPI</b><ul>${kpis}</ul></section><section><b>质检与分歧</b><p>${escapeHtml(card.qualityStatus)}；${card.disagreements?.length?escapeHtml(card.disagreements.join("；")):"无共同证据分歧"}</p></section></div><p class="douyin-defense-boundary">${escapeHtml(card.causalBoundary)}</p></article>`;
 }
 function contentDefensePanel(){
  const scoped=defenseState.jobs.filter(job=>currentItems().some(item=>String(item.itemId)===String(job.itemId)));
  return `<section class="douyin-content-defense" aria-live="polite"><header><div><span>MMN MULTIMODAL STRATEGY</span><h3>热点内容攻防 · 内容防线</h3><p>视频洞察按需生成：只分析你手动点击的内容；证据不足只保留观察。</p></div><em>三重交叉质检</em></header>${defenseState.error?`<p class="douyin-defense-error">${escapeHtml(defenseState.error)}</p>`:""}${state.view!=="videos"?`<div class="douyin-defense-empty">话题榜用于发现母题；请切换到热门视频，选择具体内容后生成可追溯防线。</div>`:scoped.length?`<div class="douyin-defense-cards">${scoped.map(defenseCard).join("")}</div>`:`<div class="douyin-defense-empty">展开热门视频榜，点击你需要的单条视频生成洞察；未点击的视频不会调用模型。系统不会把榜单热度直接写成需求、销量或线索因果。</div>`}</section>`;
 }

 function bind(){
  mount.querySelectorAll("[data-creation-library]").forEach(button=>button.addEventListener("click",()=>{state.workspace=button.dataset.creationLibrary;creationState.error="";render();if(state.workspace==="library"){loadCreationPlans();loadCreationCreators();loadVideoInsights()}}));
  mount.querySelectorAll("[data-hot-view]").forEach(button=>button.onclick=()=>{state.view=button.dataset.hotView;state.rankingExpanded=false;manualReviewState.open=false;render();loadContentDefense();loadVideoInsights();setTimeout(requestRecognition,RECOGNITION_DELAY_MS)});
  mount.querySelectorAll("[data-hot-range]").forEach(button=>button.onclick=()=>{state.range=button.dataset.hotRange;state.rankingExpanded=false;manualReviewState.open=false;render();loadRange(state.range)});
  mount.querySelectorAll(".douyin-hot-cover img").forEach(image=>image.onerror=()=>{const cover=image.closest(".douyin-hot-cover");cover?.classList.remove("has-image");if(cover&&!cover.querySelector("b")){const label=document.createElement("b");label.textContent="封面失效";cover.insertBefore(label,cover.querySelector("i"))}image.remove()});
  mount.querySelector("[data-collector-connect]")?.addEventListener("click",connectCollector);
  mount.querySelector("[data-collector-sync]")?.addEventListener("click",()=>startCollectorSync(false));
  mount.querySelector("[data-collector-force]")?.addEventListener("click",()=>startCollectorSync(true));
  mount.querySelector("[data-manual-review-open]")?.addEventListener("click",()=>openManualReview());
  mount.querySelectorAll("[data-manual-edit]").forEach(button=>button.addEventListener("click",()=>openManualReview(button.dataset.manualEdit)));
  mount.querySelectorAll("[data-defense-start]").forEach(button=>button.addEventListener("click",()=>startContentDefense(button.dataset.defenseStart,Boolean(defenseJobFor({itemId:button.dataset.defenseStart})))));
  mount.querySelectorAll("[data-video-insight-start]").forEach(button=>button.addEventListener("click",()=>startVideoInsight(button.dataset.videoInsightStart,Boolean(videoInsightJobFor({itemId:button.dataset.videoInsightStart})))));
  mount.querySelectorAll("[data-video-insight-toggle]").forEach(button=>button.addEventListener("click",()=>{const id=String(button.dataset.videoInsightToggle);videoInsightState.openItems.has(id)?videoInsightState.openItems.delete(id):videoInsightState.openItems.add(id);render()}));
  mount.querySelectorAll("[data-video-review-job]").forEach(button=>button.addEventListener("click",()=>reviewVideoInsight(button.dataset.videoReviewJob,button.dataset.videoReviewSlot)));
  mount.querySelectorAll("[data-video-retry-item]").forEach(button=>button.addEventListener("click",()=>startVideoInsight(button.dataset.videoRetryItem,true,button.dataset.videoRetrySlot)));
  mount.querySelectorAll("[data-creation-plan-open]").forEach(button=>button.addEventListener("click",()=>openCreationDialog(button.dataset.creationPlanOpen)));
  mount.querySelectorAll("[data-creation-dialog-close]").forEach(button=>button.addEventListener("click",closeCreationDialog));
  mount.querySelector("[data-creation-form]")?.addEventListener("submit",event=>{event.preventDefault();submitCreationPlan()});
  mount.querySelectorAll("[data-creation-retry]").forEach(button=>button.addEventListener("click",()=>retryCreationPlan(button.dataset.creationRetry)));
  mount.querySelectorAll("[data-creation-creator]").forEach(select=>select.addEventListener("change",()=>{creationState.creatorSelections[select.dataset.creationCreator]=select.value;render()}));
  mount.querySelectorAll("[data-creation-script]").forEach(button=>button.addEventListener("click",()=>createScriptFromPlan(button.dataset.creationScript,button.dataset.creationDirection)));
  mount.querySelector("[data-external-video-form]")?.addEventListener("submit",event=>{event.preventDefault();submitExternalVideo()});
  mount.querySelectorAll("[data-external-video-retry]").forEach(button=>button.addEventListener("click",()=>retryExternalVideo(button.dataset.externalVideoRetry)));
  mount.querySelectorAll("[data-creation-favorite]").forEach(button=>button.addEventListener("click",()=>toggleCreationFavorite(button.dataset.creationFavorite)));
  mount.querySelectorAll("[data-creation-compare]").forEach(input=>input.addEventListener("change",()=>toggleCreationCompare(input.dataset.creationCompare,input.checked)));
  mount.querySelector("[data-creation-compare-clear]")?.addEventListener("click",()=>{creationState.compare.clear();render()});
  mount.querySelector("[data-creation-filter-form]")?.addEventListener("submit",event=>{event.preventDefault();creationState.filters={query:mount.querySelector("[data-creation-filter-query]")?.value?.trim()||"",status:mount.querySelector("[data-creation-filter-status]")?.value||"all",favoriteOnly:Boolean(mount.querySelector("[data-creation-filter-favorite]")?.checked)};render()});
  mount.querySelectorAll("[data-creation-filter-clear]").forEach(button=>button.addEventListener("click",()=>{creationState.filters={query:"",status:"all",favoriteOnly:false};render()}));
  mount.querySelector("[data-ranking-toggle]")?.addEventListener("click",()=>{state.rankingExpanded=!state.rankingExpanded;render();mount.querySelector("[data-ranking-toggle]")?.focus()});
  mount.querySelector("[data-manual-review-close]")?.addEventListener("click",closeManualReview);
  mount.querySelectorAll("[data-manual-review-item]").forEach(button=>button.addEventListener("click",()=>{manualReviewState.selectedId=button.dataset.manualReviewItem;manualReviewState.error="";manualReviewState.message="";render()}));
  mount.querySelector("[data-manual-confirm]")?.addEventListener("click",()=>submitManualReview("confirm"));
  mount.querySelector("[data-manual-exclude]")?.addEventListener("click",()=>submitManualReview("exclude"));
 }

 function render(){
  const snapshot=currentSnapshot(),source=safeHttpUrl(snapshot?.sourceUrl),capturedDate=snapshot?.capturedAt?new Date(snapshot.capturedAt):null,captured=capturedDate&&!Number.isNaN(capturedDate.getTime())?capturedDate.toLocaleString("zh-CN",{hour12:false}):(snapshot?.capturedAt||"尚未同步");
  const rankingTitle=state.view==="videos"?"热门视频排行榜":"热门话题排行榜";
  const collectorActions=state.workspace==="ranking"?`<div class="douyin-collector-actions"><em class="${collectorState.browserOpen?"connected":""}"><i></i>${collectorState.browserOpen?"采集器窗口已连接":"抖音账号未连接"}</em><button type="button" data-collector-connect>${collectorState.browserOpen?"重新打开登录窗口":"连接抖音账号"}</button><button type="button" class="primary" data-collector-sync ${!collectorState.browserOpen||collectorRunning()||collectorState.freshToday?"disabled":""}>${collectorRunning()?"同步进行中…":collectorState.freshToday?"今日已更新":"更新今日榜单"}</button><button type="button" data-collector-force ${!collectorState.browserOpen||collectorRunning()?"disabled":""}>强制刷新</button></div>`:"";
  const rankingWorkspace=`${collectorProgress()}<div class="douyin-hot-controls">${tabs()}</div>${summary()}${entityRadar()}${manualReviewPanel()}<div class="douyin-hot-layout ${state.rankingExpanded?"is-expanded":"is-collapsed"}"><section class="douyin-hot-list" aria-live="polite"><div class="douyin-hot-list__head"><div><b>${rankingTitle}</b><span>${ranges[state.range]} · 汽车类目 · 按播放热度 · 同步于 ${escapeHtml(captured)}</span></div>${state.rankingExpanded?`<button type="button" class="douyin-ranking-close" data-ranking-toggle aria-expanded="true" aria-controls="douyin-ranking-content" aria-label="收起${rankingTitle}"><span>收起榜单</span><i aria-hidden="true"></i></button>`:""}</div><div id="douyin-ranking-content">${state.rankingExpanded?listBody():rankingPreview()}</div></section>${state.rankingExpanded?insight():""}</div>${contentDefensePanel()}<footer><span>刷新频率：每日一次，同时更新24小时、7天与30天六个榜单；登录不会触发重复抓取。</span>${source?`<a href="${escapeHtml(source)}" target="_blank" rel="noopener noreferrer">查看原始数据源 ↗</a>`:`<span>等待数据源同步</span>`}</footer>`;
  const libraryWorkspace=`<div class="douyin-hot-controls">${tabs()}</div>${creationLibrary()}`;
  mount.innerHTML=`<article class="panel douyin-hot-panel"><header class="douyin-hot-head"><div><span>DOUYIN AUTO PULSE</span><h2 id="douyin-hot-title">${state.workspace==="ranking"?"抖音汽车热点":"抖音内容研究"}</h2><p>${state.workspace==="ranking"?"热门视频与热门话题双榜，帮助客户快速看清近期内容风向。":"把已验证的视频机制沉淀为原创方向，并继续衔接完整脚本。"}</p></div>${collectorActions}</header>${state.workspace==="ranking"?rankingWorkspace:libraryWorkspace}${creationDialog()}</article>`;
  bind();
 }

 function start(){
  render();
  loadRange(state.range);
  loadCreationPlans();
  loadCollectorStatus();
 }
 if(window.mmnAuthReady)start();
 else window.addEventListener("mmn:auth-ready",start,{once:true});
})();
