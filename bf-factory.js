(function(){
 const bfState={projects:[],projectId:"",profile:"AUTO",current:null,libraryView:"raw",documents:[],briefs:[],chunks:[],loading:false};
 const labels={
  currentCommunicationProblem:"当前传播问题",bestAngle:"本品最适合打什么",avoidLeadingWith:"不建议主打",competitorPressure:"竞品压力",
  creatorRole:"达人内容角色",finalDirection:"本轮最终指向",riskAvoidance:"需要规避的风险",executionMusts:"执行清单必进项"
 };
 const libraryTitles={raw:"原始BF文件",structured:"结构化BF样本",quality:"优质BF样本",negative:"反例/禁用样本",claim:"甲方口径库",shooting:"拍摄规范库",vehicle:"车务执行规范库",risk:"表达红线库",material:"素材链接库"};
 const assetTypes={claim:"CLIENT_CLAIM",shooting:"SHOOTING_STANDARD",vehicle:"VEHICLE_LOGISTICS",risk:"EXPRESSION_RED_LINE",material:"MATERIAL_LINK"};
 const esc=value=>typeof escapeHtml==="function"?escapeHtml(String(value??"")):String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
 const split=value=>String(value||"").split(/[、,，/|｜;；]+/).map(x=>x.trim()).filter(Boolean);
 const splitLines=value=>String(value||"").split(/[\n、,，/|｜;；]+/).map(x=>x.trim()).filter(Boolean);
 const scope=()=>({
  orgId:session?.org_id||"mmn-local",
  userId:session?.user_id||session?.username||"local",
  clientKey:document.querySelector("#bf-client-key")?.value.trim()||`client-${state.config.brand||"mmn"}`.replace(/\s+/g,"-")
 });

 async function bfFetch(path,options={}){
  const headers=authHeaders(options.body instanceof ArrayBuffer?{}:{"Content-Type":"application/json",...(options.headers||{})});
  const response=await fetch(path,{...options,headers});
  const raw=await response.text();
  let json;
  try{json=raw?JSON.parse(raw):{}}catch{throw new Error(`BF接口返回非JSON：HTTP ${response.status}`)}
  if(!response.ok||!json.ok){const error=json.error;throw new Error(error?.message||error||`BF请求失败：HTTP ${response.status}`)}
  return json.data;
 }

 function projectOptions(){
  return bfState.projects.map(item=>`<option value="${esc(item.id)}" ${item.id===bfState.projectId?"selected":""}>${esc(item.name)}｜${esc(item.brand||"品牌待确认")} ${esc(item.model||"")}</option>`).join("");
 }

 function syncProjectSelects(){
  ["#bf-project","#bf-library-project"].forEach(selector=>{const el=document.querySelector(selector);if(el){el.innerHTML=projectOptions();el.value=bfState.projectId}});
  const current=bfState.projects.find(item=>item.id===bfState.projectId);
  if(current){document.querySelector("#bf-client-key").value=current.client_key;document.querySelector("#bf-brand").value=current.brand||state.config.brand||"";document.querySelector("#bf-model").value=current.model||state.config.model||""}
 }

 async function loadProjects(){
  const s=scope();
  bfState.projects=await bfFetch(`/api/bf/projects?orgId=${encodeURIComponent(s.orgId)}`);
  if(!bfState.projects.length){
   const name=state.config.project||`${state.config.brand||"MMN"}${state.config.model||"车型"} BF项目`;
   const project=await bfFetch("/api/bf/projects",{method:"POST",body:JSON.stringify({orgId:s.orgId,userId:s.userId,edition:activeEdition(),clientKey:s.clientKey,name,brand:state.config.brand||"",model:state.config.model||""})});
   bfState.projects=[project];
  }
  if(!bfState.projectId||!bfState.projects.some(item=>item.id===bfState.projectId))bfState.projectId=bfState.projects[0].id;
  syncProjectSelects();
  return bfState.projects;
 }

 async function ensureReady(){
  try{await loadProjects();await loadLibrary()}catch(error){toast(`BF工厂初始化失败：${error.message}`)}
 }

 function chooseProfile(profile){
  bfState.profile=profile;
  document.querySelectorAll("[data-bf-profile]").forEach(button=>button.classList.toggle("active",button.dataset.bfProfile===profile));
  const textarea=document.querySelector("#bf-content-directions");
  const presets={STORE_VISIT:"探店静态体验、用户第一视角、必须露出信息、到店CTA和拍摄注意事项",CLOUD_REVIEW:"围绕核心论点、数据事实、话题矩阵、达人分工和口播逻辑展开",HIGH_END_PHOTOGRAPHY:"围绕视觉调性、产品点分发、场景、镜头语言、车务流程和素材回传展开",STATIC_SHOOT:"完成外观、内饰、空间、座椅、车机和产品细节的静态实拍，明确场景、机位、必拍镜头和素材规格",DYNAMIC_SHOOT:"完成合规道路上的路跑、跟车、车身姿态和动态性能实拍，明确驾驶安全、机位、车速和素材回传要求",CHASSIS_SHOOT:"完成举升机环境下的底盘全貌、悬架、护板、制动和关键结构实拍，明确车务安全、讲解口径和特写镜头"};
  if(profile!=="AUTO"&&!textarea.value.trim())textarea.value=presets[profile]||"";
 }

 function activateFactoryTab(tab){
  document.querySelectorAll("#bffactory [data-bf-tab]").forEach(button=>button.classList.toggle("active",button.dataset.bfTab===tab));
  const mapping={store:["STORE_VISIT",""],cloud:["CLOUD_REVIEW",""],photo:["HIGH_END_PHOTOGRAPHY",""],creator:["AUTO","请根据达人类型和内容任务动态组织达人分工、表达方式与交付要求"],script:["AUTO","请重点输出可执行脚本框架，同时保留策略判断、证据和风险边界"],checklist:["AUTO","请重点生成拍摄执行清单、车务检查、素材回传和补拍规则"]};
  if(mapping[tab]){chooseProfile(mapping[tab][0]);if(mapping[tab][1])document.querySelector("#bf-content-directions").value=mapping[tab][1]}
  if(tab==="export")document.querySelector(".bf-editor-panel")?.scrollIntoView({behavior:"smooth",block:"start"});
 }

 async function submitGeneration(event){
  event.preventDefault();
  if(bfState.loading)return;
  if(!bfState.projectId)await loadProjects();
  const form=new FormData(event.currentTarget),s=scope();
  const body={
   projectId:bfState.projectId,orgId:s.orgId,clientKey:s.clientKey,userId:s.userId,
   brand:form.get("brand"),model:form.get("model"),competitors:split(form.get("competitors")),projectStage:form.get("projectStage"),
   communicationGoals:split(form.get("communicationGoals")),bfType:bfState.profile,platform:form.get("platform"),creatorTypes:split(form.get("creatorTypes")),
   contentForms:split(form.get("contentForms")),contentDirections:split(form.get("contentDirections")),budget:form.get("budget"),publishingSchedule:form.get("publishingSchedule"),
   specialRequirements:form.get("specialRequirements"),isPriceAllowed:form.has("isPriceAllowed"),isAdasAllowed:form.has("isAdasAllowed"),
   isDynamicDrivingAllowed:form.has("isDynamicDrivingAllowed"),needsStoreCta:form.has("needsStoreCta"),needsExecutionChecklist:form.has("needsExecutionChecklist"),needsMaterialLinks:form.has("needsMaterialLinks"),redactBeforeExternal:form.has("redactBeforeExternal")
  };
  bfState.loading=true;document.querySelector("#bf-generation-status").textContent="MMN正在检索、判断与复核";toast("MMN正在生成商业化内容BF…");
  try{
   const result=await bfFetch("/api/bf/generations",{method:"POST",body:JSON.stringify(body)});
   bfState.current={...result,versionNo:result.brief.current_version_no||1};
   renderGeneration(result);await loadLibrary();toast(result.status==="EDITABLE"?"BF已完成MMN质量复核":"BF已生成，模型复核不可用时已标记人工审核");
  }catch(error){toast(`BF生成失败：${error.message}`);document.querySelector("#bf-generation-status").textContent="生成失败"}
  finally{bfState.loading=false}
 }

 function renderGeneration(result){
  document.querySelector("#bf-generation-status").textContent=result.status==="EDITABLE"?"MMN质量复核通过":"可编辑 · 需人工复核";
  document.querySelector("#bf-editor-version").textContent=`V${result.brief.current_version_no||1} · ${result.payload.classification.bfTypeLabel||result.brief.bf_type}`;
  document.querySelector("#bf-editor").value=result.markdown||"";
  renderCorrectionFields(result.payload);
  document.querySelector("#bf-section-plan").innerHTML=(result.sectionPlan||[]).filter(item=>item.visibility!=="INTERNAL").map(item=>`<span>${esc(item.title)}</span>`).join("");
  document.querySelector("#bf-internal-strategy").className="bf-strategy-grid";
  document.querySelector("#bf-internal-strategy").innerHTML=Object.entries(labels).map(([key,label])=>`<div><b>${esc(label)}</b><span>${esc(Array.isArray(result.internalStrategy?.[key])?result.internalStrategy[key].join("、"):result.internalStrategy?.[key]||"待确认")}</span></div>`).join("");
  const evidence=[...(result.retrieval?.positive||[]).map(item=>({...item,kind:"优质/普通样本"})),...(result.retrieval?.risk||[]).map(item=>({...item,kind:"反例风险"}))];
  document.querySelector("#bf-evidence-list").innerHTML=evidence.length?evidence.map(item=>`<article class="bf-evidence-card"><b>${esc(item.title)}</b><span>${esc(item.kind)} · ${esc(item.sample_grade)} · ${esc(item.bf_type)}</span></article>`).join(""):`<p class="empty">当前项目暂无可引用的历史BF。</p>`;
 }

 function renderCorrectionFields(payload){
  const values={
   "#bf-correct-type":payload?.classification?.bfTypeLabel||payload?.classification?.bfType||"",
   "#bf-correct-summary":payload?.summary||"",
   "#bf-correct-strategy":payload?.strategy?.coreStrategyJudgment||"",
   "#bf-correct-content":payload?.content?.contentDirections?.join("、")||"",
   "#bf-correct-risk":[...(payload?.risk?.prohibitedExpressions||[]),...(payload?.risk?.expressionRedLines||[]),...(payload?.risk?.riskChecklist||[])].filter((value,index,all)=>value&&all.indexOf(value)===index).join("、"),
   "#bf-correct-tags":Object.entries(payload?.tags||{}).filter(([key])=>key!=="sampleGrade").flatMap(([,value])=>Array.isArray(value)?value:[]).filter((value,index,all)=>value&&all.indexOf(value)===index).join("、")
  };
  Object.entries(values).forEach(([selector,value])=>{const element=document.querySelector(selector);if(element)element.value=value});
 }

 function syncCorrectionsToPayload(){
  if(!bfState.current?.payload)return;
  const payload=bfState.current.payload,now=new Date().toISOString(),userId=scope().userId;
  const record=(path,value)=>{payload.provenance=payload.provenance||{};payload.provenance[path]=[...(payload.provenance[path]||[]),{originType:"MANUAL",sourceDocumentId:"",sourceSegmentId:"",sourceLocator:"在线编辑器",sourceFieldPath:path,excerpt:String(Array.isArray(value)?value.join("、"):value||"").slice(0,240),confidence:1,isManual:true,modifiedAt:now,modifiedBy:userId}]};
  const typeLabel=document.querySelector("#bf-correct-type").value.trim(),summary=document.querySelector("#bf-correct-summary").value.trim(),strategy=document.querySelector("#bf-correct-strategy").value.trim();
  const content=splitLines(document.querySelector("#bf-correct-content").value),risk=splitLines(document.querySelector("#bf-correct-risk").value),tags=splitLines(document.querySelector("#bf-correct-tags").value);
  const knownTypes={"探店BF":"STORE_VISIT","探店":"STORE_VISIT","云评/口播BF":"CLOUD_REVIEW","云评BF":"CLOUD_REVIEW","口播BF":"CLOUD_REVIEW","高质感摄影BF":"HIGH_END_PHOTOGRAPHY","摄影BF":"HIGH_END_PHOTOGRAPHY","静态实拍":"STATIC_SHOOT","静态实拍BF":"STATIC_SHOOT","动态实拍":"DYNAMIC_SHOOT","动态实拍BF":"DYNAMIC_SHOOT","底盘实拍":"CHASSIS_SHOOT","底盘实拍BF":"CHASSIS_SHOOT","产品解读BF":"PRODUCT_INTERPRETATION","竞品攻防BF":"COMPETITOR_ATTACK_DEFENSE","执行规范BF":"EXECUTION_GUIDE"};
  if(typeLabel){payload.classification.bfType=knownTypes[typeLabel]||"CUSTOM";payload.classification.bfTypeLabel=typeLabel}payload.strategy.bfType=payload.classification.bfType;record("/classification/bfTypeLabel",payload.classification.bfTypeLabel);
  payload.summary=summary;record("/summary",summary);payload.strategy.coreStrategyJudgment=strategy;record("/strategy/coreStrategyJudgment",strategy);
  payload.content.contentDirections=content;record("/content/contentDirections",content);payload.risk.riskChecklist=risk;record("/risk/riskChecklist",risk);
  payload.tags.manualTags=tags;payload.tags.sampleGrade=document.querySelector("#bf-sample-grade").value;record("/tags/manualTags",tags);
 }

 async function saveDraft({silent=false}={}){
  if(!bfState.current){toast("请先生成或选择一份BF");return false}
  try{
   syncCorrectionsToPayload();
   const s=scope(),version=await bfFetch(`/api/bf/briefs/${encodeURIComponent(bfState.current.brief.id)}/versions`,{method:"POST",body:JSON.stringify({projectId:bfState.projectId,orgId:s.orgId,userId:s.userId,baseVersionNo:bfState.current.versionNo,payload:bfState.current.payload,markdown:document.querySelector("#bf-editor").value})});
   bfState.current.versionNo=version.version_no;document.querySelector("#bf-editor-version").textContent=`V${version.version_no} · 人工修改版`;if(!silent)toast("BF草稿已保存为新版本");return true;
  }catch(error){toast(`保存失败：${error.message}`);return false}
 }

 async function finalizeBrief(){
  if(!bfState.current)return toast("请先生成或选择一份BF");
  try{
   syncCorrectionsToPayload();
   const s=scope(),sampleGrade=document.querySelector("#bf-sample-grade").value;
   const result=await bfFetch(`/api/bf/briefs/${encodeURIComponent(bfState.current.brief.id)}/finalizations`,{method:"POST",body:JSON.stringify({projectId:bfState.projectId,orgId:s.orgId,userId:s.userId,baseVersionNo:bfState.current.versionNo,payload:bfState.current.payload,markdown:document.querySelector("#bf-editor").value,sampleGrade,outcome:{isCustomerAdopted:false,isCommercialUsed:false,needsReshoot:false,passedReview:true},learnedProfileName:bfState.current.payload.classification.bfTypeLabel})});
   bfState.current.versionNo=result.version.version_no;document.querySelector("#bf-editor-version").textContent=`V${result.version.version_no} · 最终版 · ${sampleGrade}`;await loadLibrary();toast(result.learnedProfile?"最终版已回流，并保存为可复用BF样本":"最终版已回流BF资产库");
  }catch(error){toast(`最终版回流失败：${error.message}`)}
 }

 async function exportWord(){
  if(!bfState.current)return toast("请先生成或选择一份BF");
  try{
   if(!await saveDraft({silent:true}))return;
   const s=scope(),response=await fetch(`/api/bf/briefs/${encodeURIComponent(bfState.current.brief.id)}/exports`,{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({projectId:bfState.projectId,orgId:s.orgId,format:"DOCX",includeInternal:false})});
   if(!response.ok){const json=await response.json().catch(()=>({}));throw new Error(json.error?.message||"Word导出失败")}
   const blob=await response.blob(),anchor=document.createElement("a");anchor.href=URL.createObjectURL(blob);anchor.download=`${bfState.current.payload.strategy.bfName||"MMN-BF"}.docx`;anchor.click();URL.revokeObjectURL(anchor.href);toast("BF Word已导出");
  }catch(error){toast(`Word导出失败：${error.message}`)}
 }

 async function uploadDocument(file){
  if(!file)return;if(!bfState.projectId)await loadProjects();
  const s=scope(),project=bfState.projects.find(item=>item.id===bfState.projectId);document.querySelector("#bf-upload-status").textContent="正在解析文件、识别BF类型并抽取字段…";
  try{
   const query=new URLSearchParams({projectId:bfState.projectId,orgId:s.orgId,clientKey:project?.client_key||s.clientKey,userId:s.userId,filename:file.name});
   const response=await fetch(`/api/bf/documents?${query}`,{method:"POST",headers:authHeaders({"Content-Type":file.type||"application/octet-stream"}),body:await file.arrayBuffer()});
   const json=await response.json().catch(()=>({}));if(!response.ok||!json.ok)throw new Error(json.error?.message||"上传解析失败");
   document.querySelector("#bf-upload-status").textContent=`已解析 ${file.name}：${json.data.payload.classification.bfTypeLabel}，可进入结构化样本校正。`;await loadLibrary();toast("原始BF已解析并进入资产库");
  }catch(error){document.querySelector("#bf-upload-status").textContent=`解析失败：${error.message}`;toast(`BF上传失败：${error.message}`)}
 }

 async function loadLibrary(){
  if(!bfState.projectId)return;
  const s=scope(),view=bfState.libraryView;document.querySelector("#bf-library-title").textContent=libraryTitles[view]||"BF资产";
  try{
   if(view==="raw"){
    bfState.documents=await bfFetch(`/api/bf/documents?projectId=${encodeURIComponent(bfState.projectId)}&orgId=${encodeURIComponent(s.orgId)}`);renderLibrary(bfState.documents,"document");
   }else if(assetTypes[view]){
    bfState.chunks=await bfFetch(`/api/bf/knowledge-chunks?projectId=${encodeURIComponent(bfState.projectId)}&orgId=${encodeURIComponent(s.orgId)}&assetType=${encodeURIComponent(assetTypes[view])}`);renderLibrary(bfState.chunks,"chunk");
   }else{
    const grades=view==="quality"?["QUALITY"]:view==="negative"?["NEGATIVE","DISABLED"]:[];let rows=[];
    if(grades.length){for(const grade of grades)rows.push(...await bfFetch(`/api/bf/briefs?projectId=${encodeURIComponent(bfState.projectId)}&orgId=${encodeURIComponent(s.orgId)}&sampleGrade=${grade}`))}
    else rows=await bfFetch(`/api/bf/briefs?projectId=${encodeURIComponent(bfState.projectId)}&orgId=${encodeURIComponent(s.orgId)}`);
    bfState.briefs=rows;renderLibrary(rows,"brief");
   }
  }catch(error){document.querySelector("#bf-library-list").innerHTML=`<p class="empty">${esc(error.message)}</p>`}
 }

 function renderLibrary(items,kind){
  const search=(document.querySelector("#bf-library-search")?.value||"").trim().toLowerCase();
  const rows=(items||[]).filter(item=>!search||JSON.stringify(item).toLowerCase().includes(search));document.querySelector("#bf-library-count").textContent=`${rows.length}项`;
  document.querySelector("#bf-library-list").innerHTML=rows.length?rows.map(item=>{
   if(kind==="document")return`<article class="bf-library-item"><div><small>${esc((item.uploaded_at||"").slice(0,19).replace("T"," "))}</small><h3>${esc(item.filename)}</h3><p>${esc(item.extension)} · ${esc(item.page_count||"页数待识别")} · 已归入当前项目</p></div><span class="bf-grade">${esc(item.parse_status)}</span></article>`;
   if(kind==="chunk")return`<article class="bf-library-item"><div><small>${esc(item.asset_type)} · ${esc(item.scope)}</small><h3>${esc((item.redacted_text||"结构化资产").slice(0,70))}</h3><p>来源BF：${esc(item.brief_id||"—")} · 仅在允许范围内召回</p></div><span class="bf-grade ${esc(item.sample_grade)}">${esc(item.sample_grade)}</span></article>`;
   return`<button type="button" class="bf-library-item" data-bf-brief-id="${esc(item.id)}"><div><small>${esc((item.updated_at||"").slice(0,19).replace("T"," "))}</small><h3>${esc(item.title)}</h3><p>${esc(item.bf_type)} · ${esc(item.summary||"等待补充摘要")}</p></div><span class="bf-grade ${esc(item.sample_grade)}">${esc(item.sample_grade)}</span></button>`;
  }).join(""):`<p class="empty">当前筛选下暂无BF资产。</p>`;
  document.querySelectorAll("[data-bf-brief-id]").forEach(button=>button.onclick=()=>openBrief(button.dataset.bfBriefId));
 }

 async function openBrief(briefId){
  try{
   const s=scope(),brief=await bfFetch(`/api/bf/briefs/${encodeURIComponent(briefId)}?projectId=${encodeURIComponent(bfState.projectId)}&orgId=${encodeURIComponent(s.orgId)}`),version=brief.currentVersion;
   bfState.current={brief,payload:version.structured,markdown:version.rendered_markdown||`# ${brief.title}\n\n${version.structured.summary||""}`,versionNo:version.version_no,internalStrategy:{},sectionPlan:[],retrieval:{positive:[],risk:[]}};
   document.querySelector("#bf-editor").value=bfState.current.markdown;renderCorrectionFields(bfState.current.payload);document.querySelector("#bf-editor-version").textContent=`V${version.version_no} · ${brief.sample_grade}`;document.querySelector("#bf-sample-grade").value=brief.sample_grade||"NORMAL";showPage("bffactory");document.querySelector("#page-title").textContent="BF工厂";toast("已打开BF，可继续编辑、导出或回流")
  }catch(error){toast(`打开BF失败：${error.message}`)}
 }

 function openFactory(tab="new"){showPage("bffactory");document.querySelector("#page-title").textContent="BF工厂";activateFactoryTab(tab);ensureReady()}
 function openLibrary(){showPage("bflibrary");document.querySelector("#page-title").textContent="BF资产库";ensureReady()}

 pageNames.bffactory="BF工厂";pageNames.bflibrary="BF资产库";
 document.querySelector("#bf-brand").value=state.config.brand||"";document.querySelector("#bf-model").value=state.config.model||"";
 document.querySelectorAll('#nav [data-page="bffactory"]').forEach(button=>button.onclick=()=>openFactory(button.dataset.bfTab||"new"));
 document.querySelectorAll('#nav [data-page="bflibrary"]').forEach(button=>button.onclick=openLibrary);
 document.querySelectorAll("#bffactory [data-bf-tab]").forEach(button=>button.onclick=()=>activateFactoryTab(button.dataset.bfTab));
 document.querySelectorAll("[data-bf-profile]").forEach(button=>button.onclick=()=>chooseProfile(button.dataset.bfProfile));
 document.querySelector("#bf-generation-form").onsubmit=submitGeneration;
 document.querySelector("#bf-refresh-projects").onclick=ensureReady;
 document.querySelector("#bf-project").onchange=event=>{bfState.projectId=event.target.value;syncProjectSelects();loadLibrary()};
 document.querySelector("#bf-library-project").onchange=event=>{bfState.projectId=event.target.value;syncProjectSelects();loadLibrary()};
 document.querySelector("#bf-save-draft").onclick=()=>saveDraft();document.querySelector("#bf-finalize").onclick=finalizeBrief;document.querySelector("#bf-export-word").onclick=exportWord;
 document.querySelector("#bf-document-file").onchange=event=>{const file=event.target.files[0];uploadDocument(file);event.target.value=""};
 document.querySelectorAll("[data-bf-library-view]").forEach(button=>button.onclick=()=>{bfState.libraryView=button.dataset.bfLibraryView;document.querySelectorAll("[data-bf-library-view]").forEach(item=>item.classList.toggle("active",item===button));loadLibrary()});
 document.querySelector("#bf-library-search").oninput=()=>loadLibrary();document.querySelector("#bf-library-grade").onchange=event=>{bfState.libraryView=event.target.value?event.target.value.toLowerCase():"structured";loadLibrary()};
 const dropzone=document.querySelector("#bf-dropzone");["dragenter","dragover"].forEach(name=>dropzone.addEventListener(name,event=>{event.preventDefault();dropzone.classList.add("drag")}));["dragleave","drop"].forEach(name=>dropzone.addEventListener(name,event=>{event.preventDefault();dropzone.classList.remove("drag")}));dropzone.addEventListener("drop",event=>uploadDocument(event.dataTransfer.files[0]));
})();
