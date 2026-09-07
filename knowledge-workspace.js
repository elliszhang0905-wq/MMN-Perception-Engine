(function(root,factory){
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.MmnKnowledgeWorkspace=api;
})(typeof window!=="undefined"?window:globalThis,function(){
  "use strict";
  const TYPES=["","原始材料","知识结论","方法论","案例","未分类"];
  const clean=value=>typeof value==="string"?value:null;
  function safeHttpUrl(value){if(typeof value!=="string")return null;try{const url=new URL(value);return url.protocol==="http:"||url.protocol==="https:"?value:null}catch(_){return null}}
  function projectKnowledgeItem(source={}){
    return{id:clean(source.id)||"",title:clean(source.title)||"",body:clean(source.body)||"",type:clean(source.type)||"未分类",brand:clean(source.brand),module:clean(source.module),sourceLabel:clean(source.sourceLabel),sourceUrl:safeHttpUrl(source.sourceUrl),createdAt:clean(source.createdAt),updatedAt:clean(source.updatedAt),reviewStatus:source.reviewStatus==="unavailable"?"unavailable":"unavailable",validity:source.validity==="unknown"?"unknown":"unknown"};
  }
  function buildKnowledgeWorkspaceUrl(filters={}){
    const params=new URLSearchParams();
    params.set("edition",filters.edition==="global"?"global":"china");
    for(const key of ["q","type","brand","module"]){if(filters[key])params.set(key,String(filters[key]))}
    params.set("offset",String(Math.max(0,Number(filters.offset)||0)));
    params.set("limit",String(Math.min(100,Math.max(1,Number(filters.limit)||50))));
    return `/api/knowledge-workspace?${params}`;
  }
  function contextKey(context={}){return [context.orgId,context.userId,context.edition,context.project].map(value=>String(value||"")).join("\u001f")}
  function createKnowledgeWorkspaceController({fetchJson,getHeaders=()=>({}),onChange=()=>{}}={}){
    let generation=0,abort=null,context={},lastRequest=null;
    let state={status:"idle",items:[],total:0,offset:0,limit:50,hasMore:false,facets:{brands:[],modules:[]},filters:{q:"",type:"",brand:"",module:""},selectedId:"",error:""};
    const publish=()=>onChange({...state,items:[...state.items],filters:{...state.filters},facets:{...state.facets}});
    const clear=(resetFilters=false)=>{state={...state,status:"idle",items:[],total:0,offset:0,hasMore:false,facets:{brands:[],modules:[]},filters:resetFilters?{q:"",type:"",brand:"",module:""}:state.filters,selectedId:"",error:""};publish()};
    function setContext(next={}){
      const changed=contextKey(next)!==contextKey(context)||Boolean(next.active)!==Boolean(context.active)||Boolean(next.authReady)!==Boolean(context.authReady);
      context={...next};
      if(changed){generation++;if(abort)abort.abort();abort=null;clear(true)}
      return changed;
    }
    async function load(overrides={}){
      if(!context.active||!context.authReady)return;
      const filters={...state.filters,...overrides,edition:context.edition,offset:overrides.offset??state.offset,limit:state.limit};
      state={...state,filters:{q:filters.q||"",type:filters.type||"",brand:filters.brand||"",module:filters.module||""},items:[],total:0,hasMore:false,offset:filters.offset,selectedId:"",status:"loading",error:""};publish();
      const own=++generation; if(abort)abort.abort(); abort=new AbortController();
      lastRequest={...state.filters,offset:state.offset};
      try{
        const data=await fetchJson(buildKnowledgeWorkspaceUrl(filters),{method:"GET",cache:"no-store",credentials:"same-origin",headers:getHeaders(),signal:abort.signal});
        if(own!==generation)return;
        const items=Array.isArray(data.items)?data.items.map(projectKnowledgeItem):[];
        state={...state,status:items.length?"ready":"empty",items,total:Number(data.total)||0,offset:Number(data.offset)||0,limit:Number(data.limit)||state.limit,hasMore:Boolean(data.hasMore),facets:{brands:Array.isArray(data.facets?.brands)?data.facets.brands:[],modules:Array.isArray(data.facets?.modules)?data.facets.modules:[]},error:""};publish();
      }catch(error){if(own!==generation||error?.name==="AbortError")return;state={...state,status:"error",items:[],total:0,selectedId:"",error:error?.message||"知识库读取失败"};publish()}
    }
    return{setContext,load,search(filters){return load({...filters,offset:0})},retry(){return load(lastRequest||{})},invalidate(){generation++;if(abort)abort.abort();abort=null;clear(true)},select(id){if(state.status!=="ready")return;state={...state,selectedId:String(id||"")};publish()},getState(){return state}};
  }
  function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node}
  function option(select,value,label){const node=el("option","",label);node.value=value;select.append(node)}
  function createKnowledgeWorkspaceView(rootNode,{fetchJson,getHeaders,getContext}){
    let state=null,listScroll=0,mobilePane="list",viewContext="";
    const controller=createKnowledgeWorkspaceController({fetchJson,getHeaders,onChange:next=>{state=next;render()}});
    rootNode.className="knowledge-workspace";
    const toolbar=el("form","knowledge-workspace-toolbar"); toolbar.setAttribute("role","search");
    const search=el("input");search.type="search";search.placeholder="搜索标题或正文";search.setAttribute("aria-label","搜索知识标题或正文");
    const type=el("select");type.setAttribute("aria-label","按知识类型筛选");TYPES.forEach(value=>option(type,value,value||"全部类型"));
    const brand=el("select");brand.setAttribute("aria-label","按品牌筛选");
    const moduleSelect=el("select");moduleSelect.setAttribute("aria-label","按模块筛选");
    const submit=el("button","primary","查询");submit.type="submit";toolbar.append(search,type,brand,moduleSelect,submit);
    const status=el("div","knowledge-workspace-status");status.setAttribute("aria-live","polite");
    const grid=el("div","knowledge-workspace-grid");
    const list=el("section","knowledge-workspace-list");list.setAttribute("aria-label","知识目录");
    const body=el("article","knowledge-workspace-body");body.setAttribute("aria-label","知识正文");
    const evidence=el("aside","knowledge-workspace-evidence");evidence.setAttribute("aria-label","证据与记录");grid.append(list,body,evidence);rootNode.append(toolbar,status,grid);
    function focusAfterRender(selector){requestAnimationFrame(()=>rootNode.querySelector(selector)?.focus())}
    function backButton(label,pane){const button=el("button","knowledge-workspace-back",label);button.type="button";button.onclick=()=>{mobilePane=pane;render();focusAfterRender(pane==="list"?`[data-id="${CSS.escape(state.selectedId)}"]`:".knowledge-workspace-body h3")};return button}
    function syncSelect(select,label,values,current){select.replaceChildren();option(select,"",label);values.forEach(value=>option(select,value,value));select.value=current||""}
    function render(){
      if(!state)return;listScroll=list.scrollTop;
      syncSelect(brand,"全部品牌",state.facets.brands,state.filters.brand);syncSelect(moduleSelect,"全部模块",state.facets.modules,state.filters.module);type.value=state.filters.type;search.value=state.filters.q;
      rootNode.dataset.mobilePane=mobilePane;
      if(state.status==="loading")status.textContent="正在读取当前组织知识…";
      else if(state.status==="error")status.replaceChildren(document.createTextNode(`${state.error}，`),Object.assign(el("button","ghost","重试"),{type:"button",onclick:()=>controller.retry()}));
      else if(state.status==="empty")status.textContent="当前筛选下没有可读取的知识。";
      else status.textContent=`真实命中 ${state.total} 条·第 ${Math.floor(state.offset/state.limit)+1} 页`;
      list.replaceChildren();
      state.items.forEach(item=>{const button=el("button",`knowledge-workspace-item${item.id===state.selectedId?" active":""}`);button.type="button";button.dataset.id=item.id;button.setAttribute("aria-pressed",String(item.id===state.selectedId));button.append(el("span","",[item.type,item.brand,item.module].filter(Boolean).join(" · ")||"未分类"),el("b","",item.title||"未提供标题"));button.onclick=()=>{listScroll=list.scrollTop;mobilePane="body";controller.select(item.id);focusAfterRender(".knowledge-workspace-body h3")};list.append(button)});
      if(state.items.length){const pager=el("div","knowledge-workspace-pager");const prev=el("button","ghost","上一页"),next=el("button","ghost","下一页");prev.type=next.type="button";prev.disabled=state.offset===0;next.disabled=!state.hasMore;prev.onclick=()=>controller.load({offset:Math.max(0,state.offset-state.limit)});next.onclick=()=>controller.load({offset:state.offset+state.limit});pager.append(prev,next);list.append(pager)}
      list.scrollTop=listScroll;
      const selected=state.items.find(item=>item.id===state.selectedId);
      body.replaceChildren();evidence.replaceChildren();
      if(!selected){body.append(el("p","empty",state.status==="loading"?"更新目录时已清除上一条详情。":"从左侧目录选择一条知识。"));evidence.append(el("p","empty","选择知识后查看来源与缺失记录。"));return}
      const bodyTitle=el("h3","",selected.title||"未提供标题");bodyTitle.tabIndex=-1;
      body.append(backButton("返回目录","list"),el("span","knowledge-workspace-kicker",selected.type),bodyTitle,el("div","knowledge-workspace-copy",selected.body||"未提供正文"));
      const evidenceButton=el("button","ghost knowledge-workspace-evidence-open","查看证据与记录");evidenceButton.type="button";evidenceButton.onclick=()=>{mobilePane="evidence";render();focusAfterRender(".knowledge-workspace-evidence h3")};body.append(evidenceButton);
      const evidenceTitle=el("h3","","证据与记录");evidenceTitle.tabIndex=-1;evidence.append(backButton("返回正文","body"),evidenceTitle);
      const dl=el("dl");[["来源（未核验）",selected.sourceLabel||"未提供"],["品牌",selected.brand||"未提供"],["模块",selected.module||"未提供"],["版本记录","未提供"],["关联记录","未提供"],["审核记录","未提供"],["有效性","未提供"]].forEach(([key,value])=>{dl.append(el("dt","",key),el("dd","",value))});evidence.append(dl);
      if(selected.sourceUrl){const link=el("a","knowledge-workspace-source-link","打开未核验来源");link.href=selected.sourceUrl;link.target="_blank";link.rel="noopener noreferrer";evidence.append(link)}
    }
    toolbar.onsubmit=event=>{event.preventDefault();listScroll=0;mobilePane="list";controller.search({q:search.value.trim(),type:type.value,brand:brand.value,module:moduleSelect.value})};
    function applyViewContext(context){const next=[contextKey(context),Boolean(context.active),Boolean(context.authReady)].join("|");if(next!==viewContext){viewContext=next;mobilePane="list";listScroll=0}return controller.setContext(context)}
    function activate(){const context=getContext(),changed=applyViewContext(context);if(context.active&&context.authReady&&(changed||controller.getState().status==="idle"))controller.load()}
    return{activate,setContext(){applyViewContext(getContext())},invalidate(){viewContext="";mobilePane="list";listScroll=0;controller.invalidate()},controller};
  }
  return{projectKnowledgeItem,buildKnowledgeWorkspaceUrl,createKnowledgeWorkspaceController,createKnowledgeWorkspaceView};
});
