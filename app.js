const APP_VERSION="beta 1.03";
const emotions={兴奋:[1,0],惊喜:[.9,0],期待:[.75,.1],信任:[1,0],认可:[.85,0],自豪:[.95,0],怀疑:[-.4,.5],焦虑:[-.55,.7],失望:[-.75,.85],愤怒:[-1,1],后悔:[-.95,1],嘲讽:[-.7,.9]};
const identityWeights={目标核心人群:1.35,增量人群:1.2,高影响力车主:1.3,家庭用户:1.15,科技用户:1.15,性能用户:1.1,价格敏感用户:1,未知:.85};
const intentWeights={高意向:1.5,中意向:1.15,低意向:.8,无:.5};
const rawImportedDataset=typeof window!=="undefined"?window.importedDataset20260608:null;
const importedDataset=typeof MmnLegacyProductEvaluation!=="undefined"?MmnLegacyProductEvaluation.normalizeLegacyAttributeNsrDataset(rawImportedDataset):rawImportedDataset;
const defaultState={
 datasetVersion:importedDataset?.datasetVersion||importedDataset?.version||"demo_v1",
 sourceNote:importedDataset?.sourceNote||importedDataset?.note||"演示数据",
 config:importedDataset?.config||{project:"智己LS8上市期认知战役（演示）",brand:"智己",model:"智己LS8",competitor:"理想L8",targetIdentity:"目标核心人群",budget:800,priorityThreshold:60,riskThreshold:500},
 platforms:importedDataset?.platforms||{抖音:1.25,小红书:1.15,微博:1.1,懂车帝:1.2,汽车之家:1.15,微信:1.05,B站:1.1,线下活动:1.3},
 rows:importedDataset?.rows||[
["智己LS8","本品","抖音","底盘操控","底盘滤震","兴奋","目标核心人群","高意向",820,4,1.25,2],
["智己LS8","本品","懂车帝","智能化","智能驾驶","认可","科技用户","中意向",620,5,1.35,4],
["智己LS8","本品","小红书","空间舒适","二排舒适","认可","家庭用户","中意向",430,4,1.15,3],
["智己LS8","本品","微博","价格权益","价格","焦虑","价格敏感用户","高意向",520,5,1.4,4],
["智己LS8","本品","汽车之家","品牌信任","品牌信任","怀疑","增量人群","中意向",390,5,1.25,3],
["智己LS8","本品","抖音","用户证词","真实口碑","期待","高影响力车主","中意向",510,4,1.3,2],
["智己LS8","本品","B站","底盘操控","操控稳定","信任","性能用户","高意向",360,4,1.2,3],
["智己LS8","本品","小红书","能耗补能","城市能耗","失望","目标核心人群","中意向",280,4,1.1,3],
["智己LS8","本品","线下活动","安全质量","被动安全","信任","家庭用户","高意向",680,5,1.3,3],
["理想L8","竞品","抖音","家庭场景","家庭场景","信任","家庭用户","高意向",1100,5,1.1,4],
["理想L8","竞品","小红书","空间舒适","二排舒适","兴奋","家庭用户","高意向",760,5,1.05,4],
["理想L8","竞品","汽车之家","品牌信任","品牌信任","认可","目标核心人群","中意向",650,5,1.05,5],
["理想L8","竞品","懂车帝","底盘操控","底盘滤震","怀疑","性能用户","中意向",420,4,1.05,4],
["理想L8","竞品","微博","价格权益","价格","失望","价格敏感用户","高意向",690,5,1.15,5],
["理想L8","竞品","抖音","智能化","智能驾驶","认可","科技用户","中意向",830,4,1.2,5],
["理想L8","竞品","小红书","用户证词","真实口碑","信任","高影响力车主","高意向",590,5,1.05,4]
 ],
 models:importedDataset?.models,
 summaryHeat:importedDataset?.summaryHeat,
 summaryPlatformNsr:importedDataset?.summaryPlatformNsr,
 summaryMetrics:importedDataset?.summaryMetrics,
 summaryAttributeBenchmark:importedDataset?.summaryAttributeBenchmark,
 importQuality:importedDataset?.importQuality,
 sourceRowCount:importedDataset?.sourceRowCount,
 aggregatedRowCount:importedDataset?.aggregatedRowCount,
 replace:importedDataset?.replace,
 productEvaluationSourceModel:importedDataset?.productEvaluationSourceModel,
 productEvaluationBoundModel:importedDataset?.productEvaluationBoundModel
};
const defaultGlobalState={
 datasetVersion:"global_demo_v1",
 sourceNote:"出海版演示数据，与国内版完全隔离",
 config:{project:"Thailand EV Launch Perception Pilot",brand:"BYD",model:"BYD Atto 3",competitor:"Toyota Yaris / Tesla Model Y",targetIdentity:"东南亚新能源意向人群",budget:600,priorityThreshold:60,riskThreshold:400},
 platforms:{TikTok:1.25,YouTube:1.15,Instagram:1.1,Reddit:1.05,GoogleTrends:1.1,ThailandMarket:1.3,DLT:1.2,ASEANMedia:1.1},
 rows:[
["BYD Atto 3","本品","TikTok","EV Adoption","Price / Incentive","期待","东南亚新能源意向人群","高意向",520,4,1.2,3],
["BYD Atto 3","本品","ThailandMarket","Market Sales","BEV penetration","认可","东南亚新能源意向人群","中意向",410,5,1.15,2],
["BYD Atto 3","本品","DLT","Registration","BEV registration","信任","家庭用户","中意向",360,4,1.1,2],
["Toyota Yaris","竞品","ASEANMedia","ICE Reliability","Brand trust","信任","家庭用户","高意向",680,5,1.05,4],
["Tesla Model Y","竞品","YouTube","Tech Image","Smart cockpit","兴奋","科技用户","中意向",590,5,1.25,5],
["BYD Atto 3","本品","Instagram","Lifestyle","Design acceptance","期待","增量人群","中意向",330,3,1.1,3]
 ]};
function cachedBrowserSession(){try{return JSON.parse(localStorage.getItem("mmnCommercialSession")||"null")}catch(_){return null}}
function browserStorageScope(ed="china"){
 const cached=cachedBrowserSession(),orgId=String(cached?.org_id||cached?.org||"local").trim()||"local",role=String(cached?.role||"").trim().toLowerCase(),editionName=ed==="global"?"global":"china";
 return{orgId,orgName:String(cached?.org||"").trim(),role,edition:editionName,isLocal:!cached||orgId==="local",canMigrateLegacy:!cached||orgId==="local"||role==="admin",identityKey:[orgId,role,editionName].join("::")};
}
let edition=loadEdition();
let managementDashboardVisible=false,managementWarningContextReady=false;
let state=load();
let nsrMapSelectedModels=[],nsrMapSelectionInitialized=false,nsrMapActiveItemKey="";
let summaryAttributeActiveLabel="",summaryAttributeActiveCategory="全部",summaryAttributeEvidenceExpanded=false;
const summaryAttributeCollapsedQuadrants=new Set(),summaryAttributeExpandedQuadrants=new Set();
function opportunityCacheContext(){
 const scope=browserStorageScope(edition),model=String(state?.config?.model||"unselected").trim()||"unselected";
 return{orgId:scope.orgId,edition:scope.edition,model,key:[scope.orgId,scope.edition,model].map(value=>encodeURIComponent(value)).join(":")};
}
function opportunityScopedStorageKey(base,contextKey=opportunityCacheContext().key){return `${base}:${contextKey}`}
function opportunityLegacyStorageValue(base){
 const context=opportunityCacheContext();
 if(context.orgId!=="local")return null;
 try{
  const legacyKey=`${base}:${context.edition}`,value=localStorage.getItem(legacyKey);
  if(value!==null){localStorage.setItem(opportunityScopedStorageKey(base,context.key),value);localStorage.removeItem(legacyKey)}
  return value;
 }catch(_){return null}
}
function opportunityStorageValue(base,contextKey=opportunityCacheContext().key){try{const value=localStorage.getItem(opportunityScopedStorageKey(base,contextKey));return value===null&&contextKey===opportunityCacheContext().key?opportunityLegacyStorageValue(base):value}catch(_){return null}}
function opportunitySourceStorageKey(contextKey=opportunityCacheContext().key){return opportunityScopedStorageKey("mmnOpportunityCompetitorSources",contextKey)}
function loadOpportunitySourceText(contextKey=opportunityCacheContext().key){return opportunityStorageValue("mmnOpportunityCompetitorSources",contextKey)||""}
function saveOpportunitySourceText(value,contextKey=opportunityCacheContext().key){try{localStorage.setItem(opportunitySourceStorageKey(contextKey),String(value||""))}catch(_){}return String(value||"")}
function opportunityJobStorageKey(contextKey=opportunityCacheContext().key){return opportunityScopedStorageKey("mmnOpportunityMapJob",contextKey)}
function loadOpportunityJobId(contextKey=opportunityCacheContext().key){return opportunityStorageValue("mmnOpportunityMapJob",contextKey)||""}
function saveOpportunityJobId(value,contextKey=opportunityCacheContext().key){try{value?localStorage.setItem(opportunityJobStorageKey(contextKey),value):localStorage.removeItem(opportunityJobStorageKey(contextKey))}catch(_){}return value||""}
function opportunityDocumentStorageKey(contextKey=opportunityCacheContext().key){return opportunityScopedStorageKey("mmnOpportunityDocument",contextKey)}
function loadOpportunityDocument(contextKey=opportunityCacheContext().key){try{return JSON.parse(opportunityStorageValue("mmnOpportunityDocument",contextKey)||"null")}catch(_){return null}}
function saveOpportunityDocument(document,contextKey=opportunityCacheContext().key){const compact=typeof compactOpportunityDocument==="function"?compactOpportunityDocument(document):document;try{compact?localStorage.setItem(opportunityDocumentStorageKey(contextKey),JSON.stringify(compact)):localStorage.removeItem(opportunityDocumentStorageKey(contextKey))}catch(_){}return compact}
function cockpitCycleStorageKey(contextKey=opportunityCacheContext().key){return opportunityScopedStorageKey("mmnCockpitDecisionCycles",contextKey)}
function loadCockpitDecisionCycleCache(contextKey=opportunityCacheContext().key){try{const cycles=JSON.parse(localStorage.getItem(cockpitCycleStorageKey(contextKey))||"[]");return Array.isArray(cycles)?cycles:[]}catch(_){return[]}}
function saveCockpitDecisionCycleCache(cycles,contextKey=opportunityCacheContext().key){const items=Array.isArray(cycles)?cycles:[];try{localStorage.setItem(cockpitCycleStorageKey(contextKey),JSON.stringify(items))}catch(_){}return items}
let opportunityEvidenceState={document:loadOpportunityDocument(),result:null,job:null,jobId:loadOpportunityJobId(),loading:false,error:"",competitorSourceText:loadOpportunitySourceText()};
let cockpitDecisionState={cycles:loadCockpitDecisionCycleCache(),loading:false,error:""};
const OPPORTUNITY_REVIEW_LABELS=["用车场景","动力与操控","空间","舒适性","内饰","配置","外观","智能座舱","品牌口碑","辅助/自动驾驶","价格","质量","用户服务","用车成本","安全"];
let opportunityReviewState={loading:false,saving:false,queue:null,selectedId:"",selectedIds:new Set(),filter:"pending",search:"",message:"",error:"",drafts:new Map()};
let opportunityReviewTrigger=null,opportunityReviewDialogBound=false;
let opportunityCompetitorPopoverModel="";
let dataModelFilter="all",dataTrafficFilter="all",dataSearch="";
let dataBrandFilter="all";
let dashBrandOpen="";
let dashboardPlatformFilter="all";
let summaryDashboardModels=[];
let summaryNsrPlatform="全网";
let summaryAttributePlatform="全网";
let sellingPointActiveLabel="";
let productWhitepaperUploadState={loading:false,error:""};
let productWhitepaperRestoreKeys=new Set();
let sellingPointActiveCompetitor="";
let sellingPointAdvisoryState={key:"",loading:false,result:null,error:"",restoredKeys:new Set()};
let summaryPlatformPopoverCleanup=null;
let summaryPlatformPopoverTrigger=null;
let dashModelMenuOpen=false;
let learningBrandOpen="";
let cognitionBrandOpen="";
let contentAssetView="assets",creatorFilter="all",creatorSearch="";
let contentStrategyState={loading:false,result:null,error:""};
let contentPptState={loading:false,result:null,error:""};
let cognitionStrategyState={loading:false,result:null,error:""};
let socialPluginStatus=null;
let currentDrillContext=null;
let semanticState={result:null,schema:null};
let aiStatus={qwen:{configured:false,model:"qwen-plus",baseUrl:"https://dashscope.aliyuncs.com/compatible-mode/v1"},deepseek:{configured:false,model:"deepseek-chat",baseUrl:"https://api.deepseek.com"},openai:{configured:false,model:"gpt-5.5",baseUrl:"https://api.openai.com/v1"},rules:{configured:true,model:"MMN规则引擎"}};
let videoState=loadVideoState(),creatorState=loadCreatorState(),videoSearch="";
let verticalState=loadVerticalState(),verticalSearch="",verticalPeriodPickerOpen=false,verticalAssetRestoreTried=false;
let strategyKb=loadStrategyKb();
let modelJudgments=loadModelJudgments();
let modelIdentities=loadModelIdentities(),modelIdentitySyncing=false;
let founderState=loadFounderState(),founderSearch="",founderFilters={brand:"all",person:"all",topic:"all"};
let bloggerSkillState={stats:{sources:0,samples:0,profiles:0,ragChunks:0},sources:[],samples:[],profiles:[],knowledgeItems:[],creatorWorkbenches:[],importJob:null},bloggerSkillPersonFilter="",bloggerTaskPollToken=0,bloggerImportPollToken=0,bloggerImportPollingJobId="";
let contentCapabilityState={stats:{sources:0,chunks:0,matched:0},chunks:[],tagOptions:{},knowledgeItems:[]},contentCapabilitySearch="",contentCapabilitySelectedTags=[];
let creatorScriptWorkspaceAsset=null,creatorScriptCurrentJob=null,creatorScriptPollToken=0;
let selectedKnowledgeCluster="";
let ragResultsExpanded=false;
let dashboardTopicPlanState={loading:false,result:null,error:""};
let strategyReportExportState={loading:false,result:null,error:""};
let workspaceState=defaultWorkspaceState(),workspaceSyncTimer=null;
let salesMarquee={edition:"china",status:"loading",items:[{text:"正在连接懂车帝销量榜..."}],note:""};
const editions={
 china:{
  label:"国内版",
  title:"MMN汽车营销引擎｜国内版",
  eyebrow:"MMN PERCEPTION ENGINE · CHINA AUTO",
  sideTitle:"国内版运行",
  sideDesc:"MMN多模态 / 本土化RAG / 本土规则优先",
  logo:"assets/mmn-logo-cn-line-cropped.png",
  routerTitle:"MMN多模型策略路由（国内版）",
  routerRole:"MMN根据任务类型自动调度底层AI发动机：复杂策略分析走深度推理，中文营销表达走内容生成，数据归纳走稳定摘要，失败时自动切换备用模型并由本地规则兜底。",
  scopeSuffix:"国内版：集团-品牌-车型-项目隔离",
  knowledge:[
   {tier:"MMN母知识库",scope:"中国汽车营销方法论、垂媒/抖音/小红书打法、可复用策略框架",items:13,storage:"平台只读"},
   {tier:"客户私有知识库",scope:"集团/品牌/车型项目私有资料，按企业空间隔离",items:0,storage:"企业隔离"},
   {tier:"项目学习库",scope:"本地导入数据、人工结论、RAG巡检、复盘学习",items:0,storage:"项目隔离"}
  ],
  architecture:{
   eyebrow:"DOMESTIC FOUNDATION",
   title:"国内版数据源与策略智能架构",
   button:"国内版优先优化",
   mode:"国内版",
   headline:"从国内声量数据到 MMN 策略闭环",
   desc:"优先打通抖音、小红书、垂媒、人工结论、RAG知识库和MMN多模型策略路由，让系统围绕MMN方法论完成执行、推理、质检和兜底，本地系统先具备稳定可演示、可私有化、可持续学习的能力。",
   status:[["当前版本",APP_VERSION],["策略路由","MMN自动调度"],["部署形态","本地 / 私有云"],["数据原则","客户隔离"]],
   flow:["国内声量数据","清洗与标签拆解","本土化RAG召回","MMN策略模型分析","MMN策略质检","行动计划与学习"],
   data:[
    ["抖音 / 小红书","短视频与种草内容，区分商业化声量和自然声量，按车型/竞品/平台拆解。","已接入导入面板"],
    ["汽车之家 / 懂车帝","正反向排名、竞品格局、周期趋势和标签钻取。","已接入 Excel 导入"],
    ["人工结论 / 客户复盘","把客户判断、项目经验、市场反馈沉淀为项目学习库。","已接入学习表单"],
    ["企业私有资料","品牌手册、产品资料、FAQ、媒介策略、历史战役复盘。","下一步接入RAG文件库"]
   ],
   ai:[
    ["MMN策略按钮","前台只露出 MMN策略，不暴露底层模型品牌。","已完成"],
    ["MMN主控执行引擎","负责RAG检索、知识库调用、结构化输出和常规营销方案生成。","主控"],
    ["MMN策略推理质检引擎","负责竞品拆解、观点压力测试、逻辑校验和数据分析。","质检"],
    ["本土化RAG巡检","策略生成前召回MMN母库、客户私库、项目学习库，输出可追溯依据。","已接入原型"],
    ["本土规则兜底","无模型或模型失败时，仍可用本土规则生成保守策略建议。","已运行"]
   ],
   roadmap:[
    ["01","稳定多模型路由","底层模型由MMN自动调度，前台统一只显示MMN策略。"],
    ["02","RAG文件库","支持 PDF/Word/Markdown/Excel 策略资料导入，形成客户私有知识库。"],
    ["03","数据版本管理","每次导入形成数据版本，支持项目复盘、回滚、对比。"],
    ["04","权限隔离","集团、品牌、车型、项目四级权限和知识库隔离。"],
    ["05","国内SaaS地基","把本地SQLite升级为可多租户部署的数据服务。"]
   ]
  }
 },
 global:{
  label:"出海版",
  title:"MMN汽车营销引擎｜出海版",
  eyebrow:"MMN PERCEPTION ENGINE · GLOBAL AUTO",
  sideTitle:"出海版预览",
  sideDesc:"海外平台 / 海外模型网关 / 全球素材预留",
  logo:"assets/mmn-logo-reverse-cropped.png",
  ticker:[
   {text:"SEA EV Watch｜泰国/印尼/马来西亚新能源关注：注册量、TikTok声量、区域意向线索待接入"},
   {text:"Europe Pulse｜英国/德国/法国市场：Google Trends、YouTube评测、媒体试驾热度预留"},
   {text:"Middle East Signal｜中东区域：豪华SUV/新能源SUV竞品动向、KOC素材表现预留"},
   {text:"TikTok Creative｜海外短视频素材：完播率、互动率、创作者转化榜待接入"},
   {text:"Global RAG｜多语言资料库：英文/东南亚/中东/欧洲市场材料进入跨语言RAG"},
   {text:"Compliance｜出海版按区域隔离数据源，保留原文引用与本地法规标签"}
  ],
  routerTitle:"MMN策略路由（出海版）",
  routerRole:"面向海外市场接入海外模型网关、海外社媒数据、跨语言RAG和区域化合规规则。",
  scopeSuffix:"出海版：区域-国家-品牌-车型项目隔离",
  knowledge:[
   {tier:"MMN Global Playbook",scope:"海外上市、社媒种草、创作者营销、区域定位方法论",items:0,storage:"平台只读"},
   {tier:"客户海外私有库",scope:"国家/区域市场资料、区域渠道材料、海外媒体和消费者洞察",items:0,storage:"企业隔离"},
   {tier:"Campaign Learning",scope:"海外项目复盘、素材表现、跨语言策略学习",items:0,storage:"项目隔离"}
  ],
  architecture:{
   eyebrow:"GLOBAL FOUNDATION",
   title:"出海版数据源与策略智能架构",
   button:"出海版同步开发",
   mode:"出海版",
   headline:"从海外平台声量到区域化增长策略",
   desc:"出海版保留独立架构位，面向海外社媒、跨语言RAG、海外模型网关和区域市场隔离，后续与国内版共享MMN方法论底座。",
   status:[["当前版本",APP_VERSION],["模型路由","海外模型网关"],["部署形态","SaaS / 专属云"],["数据原则","区域隔离"]],
   flow:["海外社媒数据","翻译与本地化标签","多语言RAG","全球模型路由","区域策略计划","Campaign Learning"],
   data:[
    ["TikTok / YouTube","海外短视频内容、创作者素材、互动表现和话题趋势。","预留"],
    ["Instagram / Reddit","生活方式种草、社区口碑、真实用户问题和竞品讨论。","预留"],
    ["海外媒体 / 区域市场反馈","海外垂媒、PR报道、区域市场反馈和本地消费者资料。","预留"],
    ["多语言资料库","英文、东南亚、中东、欧洲市场材料统一进入跨语言RAG。","预留"]
   ],
   ai:[
    ["MMN策略按钮","出海版同样只暴露MMN策略，背后路由不同区域模型与知识库。","已占位"],
    ["MMN海外模型网关","额度和网络可用后接入海外模型或客户可控模型网关。","已接入SDK"],
    ["跨语言RAG","召回海外资料并保留原文引用、中文解释和区域化建议。","待建设"],
    ["合规规则引擎","区域广告合规、数据合规、素材禁区和风险提示。","待建设"]
   ],
   roadmap:[
    ["01","海外市场模板","建立国家/区域/品牌/车型项目结构。"],
    ["02","平台数据字段","定义TikTok、YouTube、Instagram、Reddit导入模板。"],
    ["03","跨语言RAG","支持原文、翻译、摘要、策略引用四层输出。"],
    ["04","海外模型网关","支持海外模型、客户网关和无模型规则兜底。"],
    ["05","全球战役复盘","沉淀Campaign Learning并反哺MMN Global Playbook。"]
   ]
  }
 }
};
const headers=["车型","类型","平台","一级赛道","认知标签","情绪","用户身份","购买意向","有效评论","Impact","Growth","Competition"];
const pageNames={dashboard:"决策驾驶舱",brandpenetration:"品牌穿透中心",socialtrends:"社媒趋势中心",policyintelligence:"政策环境分析",data:"声量数据",cognition:"认知诊断",vertical:"竞品格局",videos:"内容资产",creatorassets:"达人资产诊断",bloggerskill:"博主蒸馏孵化",contentstrategy:"MMN策略输出",actions:"行动预算",knowhow:"打法知识库",strategykb:"RAG资产库",learning:"人工结论",architecture:"版本架构",workspace:"空间权限",config:"项目权重",eval:"Eval评测"};
const hiddenPages=new Set(["actions"]);
const creatorAssetState={tab:"distill",tasks:[],creators:[],methods:[],selectedCreator:null,selectedAsset:null,processingAssetId:"",loading:false,error:""};
const socialTrendState={loading:false,restoring:false,restoreKey:"",result:null,mart:null,queryPlan:null,error:"",stage:"idle",stageTimer:null,progressTimer:null,progress:0,startedAt:0,runToken:0,jobId:"",competitors:[],visibleModels:[],evidencePlatform:"all",evidenceScope:"all"};
let socialEvidenceCapabilities={enabled:false,workerMode:"off",supportedCenters:[],schemaVersion:""};
let mmnEvalState={loading:false,running:false,data:null,error:"",filter:"all",activeCaseId:""};
function activeEdition(){try{return typeof edition==="string"?edition:loadEdition()}catch{return"china"}}
function defaultStateForEdition(ed=activeEdition()){return structuredClone(ed==="global"?defaultGlobalState:defaultState)}
function legacyStorageKeys(base,ed,scope){
 const keys=[`${base}:${ed}`];
 if(base==="mmnEngineState"&&ed==="china")keys.push("mmnChinaState");
 if(scope?.role==="admin"&&scope.orgName&&scope.orgName!==scope.orgId)keys.push(`${base}:${encodeURIComponent(scope.orgName)}:${ed}`);
 return [...new Set(keys)];
}
function storageKey(base,ed=activeEdition()){
 const scope=browserStorageScope(ed),key=`${base}:${encodeURIComponent(scope.orgId)}:${scope.edition}`;
 try{
  if(localStorage.getItem(key)===null&&scope.canMigrateLegacy){
   const legacyKeys=legacyStorageKeys(base,scope.edition,scope),sourceKey=legacyKeys.find(candidate=>localStorage.getItem(candidate)!==null);
   if(sourceKey){localStorage.setItem(key,localStorage.getItem(sourceKey));if(scope.role==="admin")legacyKeys.forEach(candidate=>localStorage.removeItem(candidate))}
  }
 }catch(_){}
 return key;
}
function importedModelsFromSourceNote(note){
 const m=String(note||"").match(/识别车型[:：]\s*([^；。]+)/);
 return m?m[1].split(/[、,，/]/).map(x=>x.trim()).filter(Boolean):[];
}
function normalizeLoadedEngineState(saved){
 if(!saved||!Array.isArray(saved.rows))return saved;
 if(typeof MmnLegacyProductEvaluation!=="undefined")saved=MmnLegacyProductEvaluation.normalizeLegacyAttributeNsrDataset(saved);
 if(/^summary_xlsx_/i.test(String(saved.datasetVersion||""))&&(!saved.importQuality||!saved.summaryHeat)){
  return {...saved,rows:[],models:[],summaryMetrics:{},summaryHeat:{},importQuality:{kind:"INVALID_LEGACY_SUMMARY_IMPORT",message:"已阻止旧版产品评价汇总表结果：该版本缺少车型热度字段或可能错误识别平台和标签。请使用“导入数据”重新替换导入原始文件。"}};
 }
 const imported=importedModelsFromSourceNote(saved.sourceNote);
 const primary=imported.find(m=>saved.rows.some(r=>r[0]===m));
 if(primary&&(!saved.config?.model||!saved.rows.some(r=>r[0]===saved.config.model))){
  const allModels=[...new Set(saved.rows.map(r=>r[0]).filter(Boolean))];
  saved.config={...(saved.config||{}),model:primary,brand:brandForModel(primary),project:`${primary}认知诊断｜原始声量导入`,competitor:allModels.filter(m=>m!==primary).join(" / ")};
 }
 return saved;
}
function load(){try{const ed=activeEdition(),saved=JSON.parse(localStorage.getItem(storageKey("mmnEngineState",ed))||"null");return saved&&Array.isArray(saved.rows)?normalizeLoadedEngineState(saved):defaultStateForEdition(ed)}catch{return defaultStateForEdition()}}
function save(){localStorage.setItem(storageKey("mmnEngineState"),JSON.stringify(state));queueWorkspaceSnapshot()}
function loadEdition(){try{return localStorage.getItem("mmnEngineEdition")==="global"?"global":"china"}catch{return"china"}}
function loadEditionData({syncServer=true}={}){state=load();reconcileProductEvaluationBinding();videoState=loadVideoState();creatorState=loadCreatorState();verticalState=loadVerticalState();strategyKb=loadStrategyKb();modelJudgments=loadModelJudgments();modelIdentities=loadModelIdentities();founderState=loadFounderState();serverLearnings=[];ragResultsExpanded=false;selectedKnowledgeCluster="";if(syncServer){loadServerLearnings();loadWorkspace()}}
function setEdition(next){
 edition=next==="global"?"global":"china";
 managementDashboardVisible=false;
 localStorage.setItem("mmnEngineEdition",edition);
 nsrMapSelectedModels=[];
 nsrMapSelectionInitialized=false;
 verticalAssetRestoreTried=false;
 loadEditionData();
 resetOpportunityContextState();
 render();
 restoreOpportunityContext();
 restoreVerticalAssetsFromServer();
 loadSalesMarquee();
 toast(`已切换为${editions[edition].label}，数据域已隔离`);
}
function setDomesticMode(next){
 if(edition!=="china"||next!=="management")return;
 managementDashboardVisible=!managementDashboardVisible;
 managementWarningContextReady=false;
 if(managementDashboardVisible){showPage("dashboard");window.loadGroupDashboardDemo?.()}
 renderEditionChrome();
 renderModelSwitcher();
 toast(managementDashboardVisible?"管理层看板已展开":"管理层看板已收起");
}
function currentEdition(){return editions[edition]||editions.china}
const assetSlots=[{key:"own",label:"本品",field:"ownModel"},{key:"comp1",label:"竞品 1",field:"competitor1"},{key:"comp2",label:"竞品 2",field:"competitor2"},{key:"comp3",label:"竞品 3",field:"competitor3"}];
const assetPlatforms=[{key:"douyin",name:"抖音"},{key:"xiaohongshu",name:"小红书"}];
function defaultCreatorLibraries(){
 return{
  douyin:[
   {id:"dy_001",name:"车研社阿森",type:"review",city:"上海",fans:1820000,avgViews:420000,engagementRate:5.8,costLevel:"高",categories:["智能驾驶","底盘操控","新能源技术"],strengths:["深度评测","技术解释","横评拆解"],fitStages:["上市预热","技术破圈"],risk:"观点强，需要提前对齐技术边界"},
   {id:"dy_002",name:"周末试驾计划",type:"lifestyle",city:"杭州",fans:760000,avgViews:210000,engagementRate:7.1,costLevel:"中",categories:["家庭场景","空间舒适","长途出行"],strengths:["家庭叙事","场景体验","女性用户触达"],fitStages:["种草扩散","试驾转化"],risk:"专业参数表达较弱"},
   {id:"dy_003",name:"新能源老车主李想想",type:"owner",city:"成都",fans:320000,avgViews:98000,engagementRate:8.4,costLevel:"中低",categories:["车主证言","能耗补能","真实口碑"],strengths:["真实体验","评论互动","疑虑回应"],fitStages:["口碑修复","线索承接"],risk:"内容产能需要排期"},
   {id:"dy_004",name:"性能车观察室",type:"review",city:"北京",fans:940000,avgViews:260000,engagementRate:5.2,costLevel:"中高",categories:["性能操控","底盘操控","安全质量"],strengths:["动态体验","赛道表达","男性用户触达"],fitStages:["卖点证明","竞品对抗"],risk:"适合硬核内容，不适合泛生活种草"}
  ],
  xiaohongshu:[
   {id:"xhs_001",name:"一只会开车的妈妈",type:"lifestyle",city:"苏州",fans:410000,avgViews:68000,engagementRate:9.3,costLevel:"中",categories:["家庭场景","空间舒适","儿童安全"],strengths:["家庭决策","图文种草","女性用户信任"],fitStages:["种草扩散","试驾转化"],risk:"需要真实体验素材支撑"},
   {id:"xhs_002",name:"城市通勤EV日记",type:"owner",city:"深圳",fans:180000,avgViews:42000,engagementRate:11.2,costLevel:"中低",categories:["能耗补能","城市通勤","用车成本"],strengths:["真实账本","评论答疑","长期追踪"],fitStages:["口碑修复","长尾转化"],risk:"覆盖面小但信任度高"},
   {id:"xhs_003",name:"设计感车生活",type:"lifestyle",city:"广州",fans:520000,avgViews:73000,engagementRate:8.1,costLevel:"中",categories:["外观设计","座舱体验","生活方式"],strengths:["高质感图片","审美表达","收藏率高"],fitStages:["品牌调性","上市预热"],risk:"不适合承担硬核技术解释"},
   {id:"xhs_004",name:"懂车的Jane",type:"review",city:"上海",fans:690000,avgViews:88000,engagementRate:7.6,costLevel:"中高",categories:["智能驾驶","安全质量","价格权益"],strengths:["理性评测","女性视角","购买建议"],fitStages:["疑虑澄清","购买决策"],risk:"需要完整FAQ和价格权益口径"}
  ]
 }
}
function defaultAssetConfig(){
 const comps=(state?.config?.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
 return{ownModel:state?.config?.model||"本品车型",competitor1:comps[0]||"",competitor2:comps[1]||"",competitor3:comps[2]||""};
}
function emptyAssetFiles(){return{douyin:{},xiaohongshu:{}}}
function loadVideoState(){try{return normalizeVideoState(JSON.parse(localStorage.getItem(storageKey("mmnVideoState"))))}catch{return normalizeVideoState(null)}}
function normalizeVideoState(raw){
 const base={config:defaultAssetConfig(),files:emptyAssetFiles(),legacyItems:[]};
 if(!raw)return base;
 if(raw.config)base.config={...base.config,...raw.config};
 if(raw.files)base.files=cleanAssetFiles(raw.files);
 if(Array.isArray(raw.items)&&!raw.files)base.legacyItems=raw.items;
 if(Array.isArray(raw.legacyItems))base.legacyItems=raw.legacyItems;
 return base;
}
function cleanAssetFiles(files={}){
 const cleaned=emptyAssetFiles();
 assetPlatforms.forEach(p=>assetSlots.forEach(s=>{
  const file=files?.[p.key]?.[s.key];
  if(!file)return;
  cleaned[p.key][s.key]=file;
 }));
 return cleaned;
}
function saveVideoState(){localStorage.setItem(storageKey("mmnVideoState"),JSON.stringify(videoState));queueWorkspaceSnapshot()}
function loadCreatorState(){try{return normalizeCreatorState(JSON.parse(localStorage.getItem(storageKey("mmnCreatorState"))))}catch{return normalizeCreatorState(null)}}
function normalizeCreatorState(raw){
 const base={creators:defaultCreatorLibraries(),creatorNotes:{}};
 let legacy=null;
 try{legacy=JSON.parse(localStorage.getItem(storageKey("mmnVideoState")))}catch{}
 if(legacy?.creators)base.creators={...base.creators,...legacy.creators};
 if(raw?.creators)base.creators={...base.creators,...raw.creators};
 base.creatorNotes=raw?.creatorNotes||legacy?.creatorNotes||{};
 return base;
}
function saveCreatorState(){localStorage.setItem(storageKey("mmnCreatorState"),JSON.stringify(creatorState));queueWorkspaceSnapshot()}
function loadVerticalState(){const base={sources:[],items:[],assetSummary:null,selectedPlatform:"all",selectedSource:"all",selectedModel:"",selectedCompetitor:"",selectedPeriod:"latest"};try{return{...base,...(JSON.parse(localStorage.getItem(storageKey("mmnVerticalState")))||{})}}catch{return base}}
function saveVerticalState(){localStorage.setItem(storageKey("mmnVerticalState"),JSON.stringify(verticalState));queueWorkspaceSnapshot()}
async function restoreVerticalAssetsFromServer(){
 if(verticalAssetRestoreTried||(verticalState.items||[]).length)return;
 verticalAssetRestoreTried=true;
 try{
  const data=await api(`/api/vertical-assets?platform=all&limit=5000&edition=${encodeURIComponent(activeEdition())}`);
  const items=data.items||[];
  if(!items.length)return;
  verticalState.items=items;
  verticalState.sources=data.sources||[{source:"vertical_rank_assets",platform:"车型资产库",count:items.length,importedAt:new Date().toISOString(),remembered:{assetSource:"vertical_rank_assets"}}];
  verticalState.assetSummary=data.assetSummary||verticalState.assetSummary;
  if(!verticalState.selectedModel)verticalState.selectedModel=items.find(x=>x.ownModel)?.ownModel||"";
  saveVerticalState();
  renderVertical();
  toast(`已从垂媒车型资产库恢复 ${items.length.toLocaleString()} 条正反向关系`);
 }catch(err){
  console.warn("垂媒车型资产库恢复失败", err);
 }
}
function loadStrategyKb(){try{return JSON.parse(localStorage.getItem(storageKey("mmnStrategyKnowledgeBase")))||[]}catch{return[]}}
function saveStrategyKb(){
 localStorage.setItem(storageKey("mmnStrategyKnowledgeBase"),JSON.stringify(strategyKb));
 api("/api/asset-library",{method:"POST",body:JSON.stringify({edition:activeEdition(),org_id:session?.org_id||"local",strategyAssets:strategyKb})}).catch(e=>console.warn("资产库持久化失败",e));
 queueWorkspaceSnapshot();
}
async function loadServerAssetLibrary(){
 try{
  const data=await api(`/api/asset-library?edition=${encodeURIComponent(activeEdition())}`);
  const existing=new Map(strategyKb.map(x=>[x.id,x]));
  (data.strategyAssets||[]).forEach(item=>{if(item?.id&&!existing.has(item.id))existing.set(item.id,item)});
  strategyKb=[...existing.values()];
  localStorage.setItem(storageKey("mmnStrategyKnowledgeBase"),JSON.stringify(strategyKb));
  render();
 }catch(e){console.warn("服务端资产库读取失败",e)}
}
function mergeStrategyKnowledge(items=[]){
 const existing=new Map(strategyKb.map(x=>[x.id,x]));
 items.forEach(item=>{if(item?.id)existing.set(item.id,{...item,source:item.source||"rag_import"})});
 strategyKb=[...existing.values()];
 saveStrategyKb();
 return items.length;
}
function defaultFounderArchive(){
 return [
  {id:"li-xiang-2026-01",brand:"理想",person:"李想",role:"创始人/CEO",platform:"微博",date:"2026-06-24",topic:"产品定义",type:"技术表达",content:"用家庭用户真实场景解释产品取舍，把配置、空间、能耗和智能化放回日常用车任务里讲。",sourceUrl:"公开互联网待接入",tags:["家庭场景","产品定义","用户价值"]},
  {id:"he-xiaopeng-2026-01",brand:"小鹏",person:"何小鹏",role:"董事长/CEO",platform:"发布会",date:"2026-06-20",topic:"智能驾驶",type:"技术叙事",content:"强调技术路线、长期投入和体验边界，把智能驾驶从参数竞争转成可验证的用户体验。",sourceUrl:"公开互联网待接入",tags:["智驾","技术路线","长期主义"]},
  {id:"lei-jun-2026-01",brand:"小米汽车",person:"雷军",role:"创始人/董事长",platform:"短视频",date:"2026-06-18",topic:"用户沟通",type:"高管IP",content:"用通俗语言降低技术理解门槛，通过个人信誉、工程细节和用户反馈建立品牌亲近感。",sourceUrl:"公开互联网待接入",tags:["用户沟通","工程细节","亲和表达"]},
  {id:"li-bin-2026-01",brand:"蔚来",person:"李斌",role:"创始人/CEO",platform:"用户沟通会",date:"2026-06-15",topic:"服务体系",type:"品牌叙事",content:"围绕用户社区、补能体系和长期陪伴讲品牌，强调信任关系和服务确定性。",sourceUrl:"公开互联网待接入",tags:["用户社区","服务体系","长期信任"]}
 ];
}
function loadFounderState(){try{return JSON.parse(localStorage.getItem(storageKey("mmnFounderDistill")))||{archive:defaultFounderArchive(),selectedPerson:"李想",lastOutput:""}}catch{return{archive:defaultFounderArchive(),selectedPerson:"李想",lastOutput:""}}}
function saveFounderState(){localStorage.setItem(storageKey("mmnFounderDistill"),JSON.stringify(founderState));queueWorkspaceSnapshot()}
const founderNavNoiseTerms=["导航","车型","报价","图片","视频","新闻","排行","排行榜","热搜","请选择品牌","请选择车系","紧凑型","中型","中大型","大型","小型","微型","SUV","MPV","两厢","三厢","旅行车","新浪汽车","腾讯汽车","网易汽车"];
const founderSpeechMarkers=["表示","称","说","认为","提到","强调","回应","解释","透露","发布","接受采访","公开信","微博","直播","发布会","发文","谈到","指出","宣布","“","”","\"", "："];
function isValidFounderArchiveItem(x={}){
 const source=String(x.sourceUrl||x.source_url||"");
 if(source.startsWith("local://"))return true;
 const text=String(x.originalSummary||x.original_summary||x.content||"").replace(/\s+/g," ").trim();
 if(text.length<36)return false;
 if(x.person&&!text.includes(x.person))return false;
 const noise=founderNavNoiseTerms.filter(t=>text.includes(t)).length;
 const markers=founderSpeechMarkers.filter(t=>text.includes(t)).length;
 if(noise>=8)return false;
 if(markers<=0)return false;
 if(noise>=4&&markers<2)return false;
 return true;
}
async function loadFounderArchives(){
 try{
  const data=await api(`/api/founder-archives?edition=${encodeURIComponent(activeEdition())}`);
  if(data.items?.length)founderState.archive=data.items.map(x=>({
   id:x.id,brand:x.brand,person:x.person,role:x.role,published_at:x.published_at,date:x.published_at,
   platform:x.platform,sourceName:x.source_name,sourceUrl:x.source_url,event_type:x.event_type,topic:x.event_type,type:x.event_type,
   content:x.original_summary,originalSummary:x.original_summary,coreViewpoint:x.core_viewpoint,
   languageStyleTags:x.language_style_tags||[],tags:x.language_style_tags||[],distillableTalk:x.distillable_talk,
   promptTemplate:x.prompt_template,riskNote:x.risk_note,capturedAt:x.captured_at
  })).filter(isValidFounderArchiveItem);
  founderState.scheduler=data.scheduler;
  founderState.sources=data.sources||[];
  founderState.modelRoles=data.modelRoles||{};
  saveFounderState();
  renderFounderDistill();
 }catch(e){renderFounderDistill()}
}
function founderRows(){
 const q=founderSearch.trim().toLowerCase();
 return (founderState.archive||[]).filter(x=>isValidFounderArchiveItem(x)&&
  (founderFilters.brand==="all"||x.brand===founderFilters.brand)&&
  (founderFilters.person==="all"||x.person===founderFilters.person)&&
  (founderFilters.topic==="all"||x.type===founderFilters.topic||x.topic===founderFilters.topic)&&
  (!q||[x.brand,x.person,x.role,x.platform,x.topic,x.type,x.content,(x.tags||[]).join(" ")].join(" ").toLowerCase().includes(q))
 ).sort((a,b)=>String(b.date||"").localeCompare(String(a.date||"")));
}
function founderProfile(person=founderState.selectedPerson){
 const rows=(founderState.archive||[]).filter(x=>x.person===person&&isValidFounderArchiveItem(x));
 const personRows=rows.length?rows:founderRows();
 const tags=[...new Set(personRows.flatMap(x=>x.tags||[]))].slice(0,8);
 const topics=[...new Set(personRows.map(x=>x.topic).filter(Boolean))].slice(0,6);
 const brand=personRows[0]?.brand||"待选择品牌";
 return {
  brand,person:person||personRows[0]?.person||"待选择人物",role:personRows[0]?.role||"高管",
  style:tags.length?`基于已验证公开表达，围绕${tags.slice(0,4).join("、")}沉淀语言风格；输出必须具体、克制、可追溯。`:"有效公开表达样本不足，暂不生成语言风格结论。",
  narrative:topics.length?`品牌叙事主线：${topics.join(" / ")}。`:"有效样本不足，品牌叙事框架待补充。",
  tech:personRows.length?"技术表达要把参数翻译成用户可感知场景，并明确边界、证据和可验证动作。":"待补充具体发布会、采访或社媒原文后再做技术表达蒸馏。",
  user:personRows.length?"用户沟通要先承认真实疑虑，再用产品证据、服务承诺和后续动作建立信任。":"待补充用户沟通类公开表达后再归纳。",
  defense:personRows.length?"舆论攻防不硬怼，优先拆清事实、口径、证据和下一步解决机制。":"待补充争议回应或公开说明后再判断。",
  prompt:personRows.length?`请参考${brand}${person||"高管"}已验证公开表达风格，输出面向汽车用户的高管IP表达。要求：表达通俗、证据明确、少空话；先讲用户问题，再讲技术/产品逻辑，最后给出行动承诺。`:"有效公开表达样本不足，暂不生成高管IP Prompt。"
 };
}
function founderKnowledgeItem(profile, output){
 return {id:`founder_${Date.now()}`,type:"创始人蒸馏",title:`${profile.brand}${profile.person}｜高管IP表达模板`,body:output||profile.prompt,keywords:[profile.brand,profile.person,"高管IP","创始人蒸馏"],tags:[profile.brand,profile.person,"高管IP","创始人蒸馏"],targets:["创始人蒸馏","RAG知识库管理","MMN策略"],source:"founder_distillation",metadata:{brand:profile.brand,person:profile.person,domain:"高管IP表达"}};
}
function loadModelJudgments(){try{return JSON.parse(localStorage.getItem(storageKey("mmnModelJudgments")))||[]}catch{return[]}}
function saveModelJudgments(){localStorage.setItem(storageKey("mmnModelJudgments"),JSON.stringify(modelJudgments));queueWorkspaceSnapshot()}
function upsertModelJudgment(item){
 if(!item?.id)return;
 const idx=modelJudgments.findIndex(x=>x.id===item.id);
 if(idx>=0)modelJudgments[idx]={...modelJudgments[idx],...item};
 else modelJudgments.unshift(item);
 modelJudgments=modelJudgments.slice(0,120);
 saveModelJudgments();
}
function modelJudgmentsFor(model=state.config.model){
 return (modelJudgments||[]).filter(x=>!model||x.model_name===model||x.model===model).sort((a,b)=>(b.created_at||b.createdAt||"").localeCompare(a.created_at||a.createdAt||""));
}
function renderModelHighlight(text,item,field){
 const source=String(text??""),raw=item?.highlight_status==="model_verified"&&Array.isArray(item?.highlights)?item.highlights.filter(x=>x?.field===field):[],ranges=[];
 raw.slice(0,3).forEach((candidate,index)=>{const quote=String(candidate?.quote||"").trim(),start=source.indexOf(quote);if(!quote||start<0||ranges.some(range=>start<range.end&&start+quote.length>range.start))return;ranges.push({start,end:start+quote.length,level:candidate?.level==="primary"||index===0?"primary":"secondary"})});
 ranges.sort((a,b)=>a.start-b.start);
 let cursor=0;
 return ranges.map(range=>{const before=escapeHtml(source.slice(cursor,range.start)),marked=`<mark class="model-highlight ${range.level}">${escapeHtml(source.slice(range.start,range.end))}</mark>`;cursor=range.end;return before+marked}).join("")+escapeHtml(source.slice(cursor));
}
function loadModelIdentities(){try{return JSON.parse(localStorage.getItem(storageKey("mmnModelIdentities")))||{items:{},updatedAt:""}}catch{return{items:{},updatedAt:""}}}
function saveModelIdentities(){localStorage.setItem(storageKey("mmnModelIdentities"),JSON.stringify(modelIdentities))}
function modelIdentityFor(model){return modelIdentities.items?.[model]||null}
const knownBrandNames=["沃尔沃","阿维塔","广汽埃安","埃安","奇瑞","别克","奥迪","宝马","奔驰","本田","东风本田","广汽本田","荣威","智己","启境","小米汽车","特斯拉","蔚来","乐道","极氪","理想","问界","比亚迪","吉利","吉利银河","领克","零跑","小鹏","广汽传祺","腾势","深蓝","长安","长安启源","五菱","宝骏","丰田","广汽丰田","一汽丰田","大众","日产","MG","smart","firefly","北京越野","奔腾","标致","MINI","雪铁龙","上汽大通","埃尚","极狐","东风纳米","待人工确认"];
function cleanModelText(model){return String(model||"").trim().replace(/\s+/g," ")}
function nullableNumber(value){
 if(value===null||value===undefined)return null;
 const text=String(value).trim();
 if(!text||["-","—","/","n/a","na","null","none"].includes(text.toLowerCase()))return null;
 const percent=text.endsWith("%"),number=Number(text.replace(/,/g,"").replace(/%$/, ""));
 return Number.isFinite(number)?(percent?number/100:number):null;
}
function meanNumbers(values){const valid=(values||[]).map(nullableNumber).filter(value=>value!==null);return valid.length?valid.reduce((sum,value)=>sum+value,0)/valid.length:null}
function attributeSourceScores(rows,model,label){
 const grouped=new Map();
 (rows||[]).forEach(row=>{if(row[0]!==model||row[4]!==label||!row[2])return;const score=nullableNumber(row[14]);if(score===null)return;const values=grouped.get(row[2])||[];values.push(score);grouped.set(row[2],values)});
 return [...grouped.entries()].map(([source,values])=>({source,score:meanNumbers(values)}));
}
function localStandardIdentity(model){
 const raw=cleanModelText(model),compact=raw.replace(/\s+/g,"");
 const token=compact.replace(/[.\-_·]/g,"").toUpperCase();
 const vwIdEra=token.match(/^(?:大众|VOLKSWAGEN)?IDERA(8X|9X)$/i);
 if(vwIdEra){const family=`大众ID.ERA ${vwIdEra[1].toUpperCase()}`;return{brand_name:"大众",normalized_name:family,model_family:family,energy_type:"UNKNOWN",variant_name:"",canonical_key:`大众|${family}|UNKNOWN|`}}
 const tiguan=compact.match(/^(?:大众|VOLKSWAGEN)?途观L(PHEV|插电混动|插混|新能源)?(.*)$/i);
 if(tiguan){const energy=tiguan[1]?"PHEV":"UNKNOWN";const family="大众途观L";const normalized=energy==="PHEV"?`${family} PHEV`:family;return{brand_name:"大众",normalized_name:normalized,model_family:family,energy_type:energy,variant_name:"",canonical_key:`大众|${family}|${energy}|`}}
 const zeekr=raw.match(/^(?:ZEEKR|Zeekr|Zeeker|ZEEKER|极氪)\s*([0-9]{3}|[0-9]X|MIX|X)(.*)$/i)||raw.match(/^(001|007|009)(.*)$/i);
 if(zeekr){
  const code=String(zeekr[1]||"").toUpperCase();
  let suffix=cleanModelText(zeekr[2]||"");
  suffix=/^(GT|GT版|ME版|WE版|YOU版)$/i.test(suffix)?"":suffix;
  const family=`极氪${code}`;
  const energy=/PHEV|插混/i.test(raw)?"PHEV":/增程|EREV/i.test(raw)?"EREV":/HEV|混动/i.test(raw)?"HEV":/燃油|ICE/i.test(raw)?"ICE":"UNKNOWN";
  return{brand_name:"极氪",normalized_name:suffix?`${family} ${suffix}`:family,model_family:family,energy_type:energy,variant_name:suffix,canonical_key:`极氪|${family}|${energy}|${suffix}`};
 }
 const roewe=compact.match(/^荣威(i5|i6|D7|D5X|RX5|RX9|IMAX8)(.*)$/i);
 if(roewe){const code=/^i[56]$/i.test(roewe[1])?String(roewe[1]).toLowerCase():String(roewe[1]).toUpperCase();const family=`荣威${code}`;const energy=/EV|纯电|BEV/i.test(raw)?"BEV":/DMH|插混|PHEV/i.test(raw)?"PHEV":"UNKNOWN";return{brand_name:"荣威",normalized_name:family+(roewe[2]?` ${roewe[2]}`:""),model_family:family,energy_type:energy,variant_name:roewe[2]||"",canonical_key:`荣威|${family}|${energy}|${roewe[2]||""}`}}
 const bmw=raw.match(/^(?:宝马|BMW)\s*(i3|i5|iX1|iX3|X1|X3|3系|5系)(.*)$/i);
 if(bmw){const code=String(bmw[1]).toUpperCase().replace(/^IX/,"iX").replace(/^I([0-9])/,"i$1");const family=`宝马${code}`;return{brand_name:"宝马",normalized_name:family+(cleanModelText(bmw[2]||"")?` ${cleanModelText(bmw[2]||"")}`:""),model_family:family,energy_type:/^i/i.test(code)?"BEV":"UNKNOWN",variant_name:cleanModelText(bmw[2]||""),canonical_key:`宝马|${family}|${/^i/i.test(code)?"BEV":"UNKNOWN"}|${cleanModelText(bmw[2]||"")}`}}
 const arcfox=compact.match(/^极狐(?:(阿尔法|α|Alpha|贝塔|β|Beta))?([ST]\d|考拉|森林版|V9)(.*)$/i);
 if(arcfox){const series=/^(贝塔|β|Beta)$/i.test(arcfox[1]||"")?"贝塔":arcfox[1]?"阿尔法":"";const code=String(arcfox[2]).toUpperCase();const family=`极狐${series}${code}`;return{brand_name:"极狐",normalized_name:family+(arcfox[3]?` ${arcfox[3]}`:""),model_family:family,energy_type:"BEV",variant_name:arcfox[3]||"",canonical_key:`极狐|${family}|BEV|${arcfox[3]||""}`}}
 const avatr=compact.match(/^阿维塔(06|07|11|12|15)(.*)$/);
 if(avatr){const family=`阿维塔${avatr[1]}`;return{brand_name:"阿维塔",normalized_name:family+(avatr[2]?` ${avatr[2]}`:""),model_family:family,energy_type:"UNKNOWN",variant_name:avatr[2]||"",canonical_key:`阿维塔|${family}|UNKNOWN|${avatr[2]||""}`}}
 const volvo=raw.match(/^(?:Volvo|沃尔沃)\s*(EX90|EX30|XC60|XC90|S90)(.*)$/i);
 if(volvo){const family=`沃尔沃${String(volvo[1]).toUpperCase()}`;return{brand_name:"沃尔沃",normalized_name:family,model_family:family,energy_type:/EX/i.test(volvo[1])?"BEV":"UNKNOWN",variant_name:cleanModelText(volvo[2]||""),canonical_key:`沃尔沃|${family}|${/EX/i.test(volvo[1])?"BEV":"UNKNOWN"}|${cleanModelText(volvo[2]||"")}`}}
 const im=compact.match(/^智己(L6|LS6|LS7|LS8|LS9)(.*)$/i);
 if(im){const family=`智己${String(im[1]).toUpperCase()}`;return{brand_name:"智己",normalized_name:family+(im[2]?` ${im[2]}`:""),model_family:family,energy_type:"UNKNOWN",variant_name:im[2]||"",canonical_key:`智己|${family}|UNKNOWN|${im[2]||""}`}}
 const qijing=compact.match(/^(?:启境|QIJING)(GT7)(.*)$/i);
 if(qijing){const family=`启境${String(qijing[1]).toUpperCase()}`;return{brand_name:"启境",normalized_name:family+(qijing[2]?` ${qijing[2]}`:""),model_family:family,energy_type:"UNKNOWN",variant_name:qijing[2]||"",canonical_key:`启境|${family}|UNKNOWN|${qijing[2]||""}`}}
 const onvo=compact.match(/^(?:乐道|ONVO)(L60)(.*)$/i);
 if(onvo){const family=`乐道${String(onvo[1]).toUpperCase()}`;return{brand_name:"乐道",normalized_name:family+(onvo[2]?` ${onvo[2]}`:""),model_family:family,energy_type:"BEV",variant_name:onvo[2]||"",canonical_key:`乐道|${family}|BEV|${onvo[2]||""}`}}
 const galaxy=compact.match(/^(?:吉利银河|银河)(L6|L7|L8|E5|E8)(.*)$/i);
 if(galaxy){const family=`银河${String(galaxy[1]).toUpperCase()}`;return{brand_name:"吉利银河",normalized_name:family+(galaxy[2]?` ${galaxy[2]}`:""),model_family:family,energy_type:/^E/i.test(galaxy[1])?"BEV":"UNKNOWN",variant_name:galaxy[2]||"",canonical_key:`吉利银河|${family}|${/^E/i.test(galaxy[1])?"BEV":"UNKNOWN"}|${galaxy[2]||""}`}}
 return null;
}
function standardIdentityFor(model){
 const local=localStandardIdentity(model),id=modelIdentityFor(model)||{};
 const rawBrand=id.brand_name||id.brandName||"";
 const brand=local?.brand_name||(!isBadBrandName(rawBrand,model)?rawBrand:brandForModel(model));
 const family=local?.model_family||id.model_family||id.modelFamily||id.normalized_name||id.normalizedName||cleanModelText(model);
 const normalized=local?.normalized_name||id.normalized_name||id.normalizedName||family;
 const energy=local?.energy_type||id.energy_type||id.energyType||"UNKNOWN";
 const variant=local?.variant_name||id.variant_name||id.variantName||"";
 const canonical=local?.canonical_key||id.canonical_key||id.canonicalKey||`${brand}|${family}|${energy}|${variant}`;
 return{brand_name:brand,normalized_name:normalized,model_family:family,energy_type:energy,variant_name:variant,canonical_key:canonical,display_model_name:local?.normalized_name||id.display_model_name||id.displayModelName||normalized};
}
function isBadBrandName(brand,model){
 const b=String(brand||"").trim(),m=String(model||"").trim();
 if(!b)return true;
 if(!knownBrandNames.includes(b))return true;
 if(b===m||m.startsWith(b)&&/\\d|PLUS|PRO|MAX|L|S|T|GT|EV|PHEV|DM|e-tron/i.test(m.slice(b.length)))return true;
 if(/[0-9]|\\b(PLUS|PRO|MAX|GT|EV|PHEV|HEV|DM-i|DM-p|e-tron|Sportback|Hyper)\\b/i.test(b))return true;
 if(b.length>8)return true;
 return false;
}
function brandForDisplay(model){
 return standardIdentityFor(model).brand_name;
}
function canonicalModelLabel(model){
 const id=standardIdentityFor(model);
 const energy=id.energy_type||"";
 const family=id.model_family||id.normalized_name||model;
 return energy&&energy!=="UNKNOWN"?`${family} · ${energy}`:family;
}
async function ensureModelIdentities(models=[]){
 let localChanged=false;
 models.filter(Boolean).forEach(m=>{const local=localStandardIdentity(m);if(local&&!modelIdentityFor(m)){modelIdentities.items[m]={raw_name:m,...local,confidence:"local-standard",qwen_checked:0,qwen_reason:"MMN本地车型资产规则"};localChanged=true}});
 if(localChanged){modelIdentities.updatedAt=new Date().toISOString();saveModelIdentities()}
 const missing=[...new Set(models.filter(Boolean))].filter(m=>!modelIdentityFor(m)||isBadBrandName(modelIdentityFor(m)?.brand_name||modelIdentityFor(m)?.brandName,m)||((modelIdentityFor(m)?.brand_name||modelIdentityFor(m)?.brandName)==="待确认品牌"&&!modelIdentityFor(m)?.qwen_checked&&!modelIdentityFor(m)?.qwenChecked));
 if(!missing.length||modelIdentitySyncing)return;
 modelIdentitySyncing=true;
 try{
  const data=await api("/api/ai/model-identities",{method:"POST",body:JSON.stringify({edition:activeEdition(),models:missing.slice(0,80)})});
  (data.items||[]).forEach(item=>{modelIdentities.items[item.raw_name||item.rawName||item.normalized_name]=item});
  modelIdentities.updatedAt=new Date().toISOString();
  saveModelIdentities();
  if(document.querySelector("#data.active"))renderData();
 }catch(err){
  missing.forEach(m=>{const brand=brandForModel(m);modelIdentities.items[m]={raw_name:m,normalized_name:m,brand_name:brand,model_family:m,energy_type:"UNKNOWN",canonical_key:`${brand}|${m}|UNKNOWN|`,confidence:"local",qwen_checked:0,qwen_reason:err.message}});
  saveModelIdentities();
 }finally{
  modelIdentitySyncing=false;
 }
}
function defaultWorkspaceState(){
 return{hierarchy:{group:"未登录客户空间",brands:[],activeScope:"本机临时模式"},knowledge:[
  {tier:"MMN母知识库",scope:"平台方法论与汽车营销框架",items:13,storage:"平台只读"},
  {tier:"客户私有知识库",scope:"登录后按企业空间隔离",items:0,storage:"企业隔离"},
  {tier:"项目学习库",scope:"人工结论、项目复盘、数据版本",items:0,storage:"项目隔离"}
 ],modelRouter:[
  {provider:"无模型规则引擎",role:"本地评分、排名、分类、权限判断",status:"已运行"},
  {provider:"MMN海外模型网关",role:"复杂策略推理与报告生成",status:"可插拔"},
  {provider:"MMN多模态能力层",role:"国内网络可用的多模态策略、摘要和RAG问答能力",status:"预留"},
  {provider:"客户私有模型",role:"私有化或专属云部署",status:"预留"}
 ],snapshots:[],updatedAt:""};
}
function assetModel(slot){return (videoState.config?.[assetSlots.find(s=>s.key===slot)?.field]||"").trim()}
function assetPlatformName(key){return assetPlatforms.find(p=>p.key===key)?.name||key}
function compactModelName(v){return String(v||"").toLowerCase().replace(/[\s·.\-_/｜|]+/g,"")}
function contentAuthorName(item){
 const candidates=[item?.authorName,item?.nickname,item?.nickName,item?.userName,item?.accountName,item?.accountNickname,item?.source_account_name,item?.author].map(x=>String(x||"").trim()).filter(Boolean);
 const good=candidates.find(x=>!/^[a-f0-9]{16,}$/i.test(x)&&!/^\d{8,}$/.test(x)&&!/^user[_-]?\d+/i.test(x));
 return good||"";
}
function itemMatchesAssetModel(item,model){
 const m=compactModelName(model);
 if(!m)return true;
 const explicit=compactModelName(item?.model||item?.assetModel||"");
 if(explicit&&explicit===m)return true;
 const text=compactModelName([item?.title,item?.searchText,item?.topicText,item?.tags,item?.desc,item?.description,item?.url].filter(Boolean).join(" "));
 return text.includes(m);
}
function cleanAssetItemsForSlot(items,platformKey,slot,model,role,source="MMN自动抓取"){
 return (items||[])
  .filter(x=>itemMatchesAssetModel(x,model))
  .map(x=>({...x,author:contentAuthorName(x),platform:assetPlatformName(platformKey),assetPlatform:platformKey,assetSlot:slot,assetRole:model||role,assetModel:model,model:model,source}));
}
function storedAssetItems(platformKey,slot){
 const file=videoState.files?.[platformKey]?.[slot],model=assetModel(slot);
 if(!file?.items?.length)return [];
 return file.items.filter(x=>itemMatchesAssetModel(x,model)).map(x=>({...x,author:contentAuthorName(x),assetRole:x.assetModel||model||x.assetRole}));
}
function allVideoItems(){
 const items=[...(videoState.legacyItems||[])];
 assetPlatforms.forEach(p=>assetSlots.forEach(s=>{
  items.push(...storedAssetItems(p.key,s.key));
 }));
 return items.map(enrichContentItem);
}
const contentCategoryRules=[
 ["价格权益",/价格|售价|权益|优惠|补贴|定金|金融|贷款|置换|保值|性价比|贵不贵|值不值|落地|购车|订单|锁单/i],
 ["购买阻塞点",/劝退|不买|缺点|槽点|问题|故障|投诉|异响|召回|翻车|后悔|失望|焦虑|担心|质疑|避坑|智商税|不值/i],
 ["竞品关系",/对比|横评|PK|pk|VS|vs|大战|打得过|不输|吊打|平替|竞品|理想|问界|蔚来|极氪|小米|特斯拉|小鹏|腾势|比亚迪|宝马|奔驰|奥迪/i],
 ["上市发布",/上市|发布|首发|发布会|预售|盲订|开启交付|交付|亮相|新车|官宣|申报|谍照|成都车展|上海车展|广州车展/i],
 ["智驾科技",/智驾|智能驾驶|自动驾驶|辅助驾驶|NOA|城区|城市NOA|高速NOA|端到端|激光雷达|泊车|座舱|车机|语音|OTA|芯片|算力/i],
 ["动力操控",/动力|加速|零百|操控|底盘|悬架|空悬|CDC|转向|刹车|麋鹿|赛道|驾驶感|运动|性能|扭矩|马力/i],
 ["空间舒适",/空间|后排|二排|三排|座椅|舒适|家用|家庭|亲子|后备箱|露营|NVH|静谧|隔音|按摩|通风|冰箱|彩电|沙发/i],
 ["续航补能",/续航|电耗|能耗|充电|补能|快充|电池|亏电|长途|高速续航|CLTC|WLTC|油耗|馈电|增程|纯电/i],
 ["安全质量",/安全|碰撞|质量|品控|耐久|自燃|刹不住|AEB|气囊|车身|高强钢|电池安全|中保研|五星安全/i],
 ["身份表达",/面子|豪华|格调|审美|设计感|精英|年轻人|家庭用户|奶爸|宝妈|女性|商务|老板|高级|质感|颜值/i],
 ["用户口碑",/车主|真实体验|提车|用车|试驾|测评|长测|口碑|满意|吐槽|实测|体验|开起来|坐起来/i],
 ["流量热点",/爆了|热搜|刷屏|出圈|争议|大事件|热点|全网|破圈|雷军|余承东|李想|何小鹏|李斌/i]
];
function contentText(item){
 return [item?.title,item?.author,item?.category,item?.searchText,item?.topicText,item?.tags,item?.desc,item?.description,item?.url,item?.assetModel,item?.model].filter(Boolean).join(" ");
}
function mmnContentCategory(item){
 const text=contentText(item);
 for(const [name,pattern] of contentCategoryRules){
  if(pattern.test(text))return name;
 }
 if(/汽车|新能源|SUV|MPV|轿车|车系|车型|试驾|评测|体验|懂车|车主|权益|线索|销量/i.test(text))return"综合评测";
 return item?.category&&item.category!=="其他内容"?item.category:"综合评测";
}
function contentMarketingLabels(item){
 const text=contentText(item),category=mmnContentCategory(item);
 const blockers=[["价格门槛",/贵|价格|售价|落地|预算|权益|优惠/],["质量信任",/质量|故障|异响|投诉|召回|品控/],["安全顾虑",/安全|碰撞|刹不住|自燃|AEB/],["续航补能",/续航|充电|补能|电耗|油耗|亏电/],["品牌信任",/品牌|保值|售后|服务|交付/]].filter(([,p])=>p.test(text)).map(([x])=>x);
 const actions=[["证据化解释",/故障|投诉|安全|质量|续航|智驾|底盘|操控/],["场景化种草",/家庭|亲子|露营|通勤|长途|女性|宝妈|奶爸/],["竞品反打",/对比|横评|PK|vs|竞品|理想|问界|蔚来|极氪|小米|特斯拉/],["权益转化",/价格|权益|优惠|补贴|金融|订单/]].filter(([,p])=>p.test(text)).map(([x])=>x);
 return{category,blockers:blockers.slice(0,3),actions:actions.slice(0,3),confidence:category==="综合评测"?"medium":"high"};
}
function enrichContentItem(item){
 const labels=contentMarketingLabels(item||{});
 return{...item,author:contentAuthorName(item),assetRole:item?.assetModel||item?.model||item?.assetRole||"",originalCategory:item?.originalCategory||item?.category||"",category:labels.category,mmnLabels:labels};
}
let session=loadSession(),serverLearnings=[];
function loadSession(){try{return JSON.parse(localStorage.getItem("mmnCommercialSession"))||null}catch{return null}}
function resetBrowserScopeTransientState(){
 nsrMapSelectedModels=[];nsrMapSelectionInitialized=false;nsrMapActiveItemKey="";
 dashBrandOpen=brandForDisplay(state.config?.model);dashboardPlatformFilter="all";summaryDashboardModels=[...(state.models||[])];summaryNsrPlatform="全网";summaryAttributePlatform="全网";
 dataModelFilter="all";dataTrafficFilter="all";dataSearch="";dataBrandFilter="all";learningBrandOpen="";cognitionBrandOpen="";
 videoSearch="";verticalSearch="";verticalPeriodPickerOpen=false;verticalAssetRestoreTried=false;currentDrillContext=null;semanticState={result:null,schema:null};
 contentStrategyState={loading:false,result:null,error:""};contentPptState={loading:false,result:null,error:""};cognitionStrategyState={loading:false,result:null,error:""};dashboardTopicPlanState={loading:false,result:null,error:""};
 if(socialTrendState.stageTimer)clearInterval(socialTrendState.stageTimer);if(socialTrendState.progressTimer)clearInterval(socialTrendState.progressTimer);
 Object.assign(socialTrendState,{loading:false,restoring:false,restoreKey:"",result:null,mart:null,queryPlan:null,error:"",stage:"idle",stageTimer:null,progressTimer:null,progress:0,startedAt:0,runToken:socialTrendState.runToken+1,jobId:"",competitors:[],visibleModels:[],evidencePlatform:"all",evidenceScope:"all"});
 Object.assign(creatorAssetState,{tab:"distill",tasks:[],creators:[],methods:[],selectedCreator:null,selectedAsset:null,processingAssetId:"",loading:false,error:""});
 bloggerSkillState={stats:{sources:0,samples:0,profiles:0,ragChunks:0},sources:[],samples:[],profiles:[],knowledgeItems:[],creatorWorkbenches:[],importJob:null};bloggerSkillPersonFilter="";bloggerTaskPollToken++;bloggerImportPollToken++;bloggerImportPollingJobId="";
 contentCapabilityState={stats:{sources:0,chunks:0,matched:0},chunks:[],tagOptions:{},knowledgeItems:[]};contentCapabilitySearch="";contentCapabilitySelectedTags=[];
 creatorScriptWorkspaceAsset=null;creatorScriptCurrentJob=null;creatorScriptPollToken++;
 workspaceState=defaultWorkspaceState();
}
function saveSession(s){
 const previousScope=browserStorageScope(activeEdition()).identityKey;
 session=s;
 localStorage.setItem("mmnCommercialSession",JSON.stringify(s));
 if(previousScope!==browserStorageScope(activeEdition()).identityKey){loadEditionData({syncServer:false});resetBrowserScopeTransientState();resetOpportunityContextState();render()}
 renderAccount();
}
function authHeaders(extra={}){return session?.token?{"Authorization":`Bearer ${session.token}`,...extra}:extra}
const MMN_PUBLIC_API_ORIGIN="http://121.40.60.90";
function shouldRetryPublicApi(path,res,raw){
 return path.startsWith("/api/")&&location.hostname!=="121.40.60.90"&&location.hostname!=="localhost"&&location.hostname!=="127.0.0.1"&&(res.status===404||res.status===403||/<!doctype|<html/i.test(raw||""));
}
async function api(path,options={}){
 const request=target=>fetch(target,{headers:authHeaders({"Content-Type":"application/json",...(options.headers||{})}),...options});
 let res=await request(path);
 const raw=await res.text();
 if(shouldRetryPublicApi(path,res,raw)){
  res=await request(MMN_PUBLIC_API_ORIGIN+path);
  return parseApiResponse(res,await res.text());
 }
 return parseApiResponse(res,raw);
}
function parseApiResponse(res,raw){
 let data=null;
 try{data=raw?JSON.parse(raw):{}}catch{
  if(res.status===401||res.status===403)throw new Error("登录状态已失效，请刷新页面后重新登录。");
  throw new Error("当前页面没有命中MMN后端接口。请从 http://121.40.60.90/ 打开MMN，并重新登录后再试。");
 }
 if(!res.ok||!data.ok)throw new Error(data.error||`请求失败：HTTP ${res.status}`);
 return data;
}
function opportunityJobRunning(job){return job?.status==="queued"||job?.status==="running"}
function opportunityPause(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
function resetOpportunityContextState(){
 const contextKey=opportunityCacheContext().key;
 opportunityEvidenceState={document:loadOpportunityDocument(contextKey),result:null,job:null,jobId:loadOpportunityJobId(contextKey),loading:false,error:"",competitorSourceText:loadOpportunitySourceText(contextKey)};
 cockpitDecisionState={cycles:loadCockpitDecisionCycleCache(contextKey),loading:false,error:""};
 opportunityReviewState={loading:false,saving:false,queue:null,selectedId:"",selectedIds:new Set(),filter:"pending",search:"",message:"",error:"",drafts:new Map()};
 opportunityCompetitorPopoverModel="";
}
async function restoreOpportunityContext(){
 const contextKey=opportunityCacheContext().key;
 const results=await Promise.allSettled([restoreLatestOpportunityDocument(contextKey),loadCockpitDecisionCycles(contextKey),resumeOpportunityMapJob(contextKey)]);
 return results;
}
async function waitForOpportunityMapJob(jobId,contextKey=opportunityCacheContext().key){
 const deadline=Date.now()+12*60*1000;
 while(Date.now()<deadline){
  if(contextKey!==opportunityCacheContext().key)return null;
  const data=await api(`/api/opportunity-map/jobs/${encodeURIComponent(jobId)}`);
  if(contextKey!==opportunityCacheContext().key)return null;
  opportunityEvidenceState.job=data.job;
  opportunityEvidenceState.loading=opportunityJobRunning(data.job);
  renderOpportunityEvidence();
  if(data.job.status==="completed"){
   opportunityEvidenceState.result=data.job.result;
   if(data.job.result?.document){opportunityEvidenceState.document=data.job.result.document;saveOpportunityDocument(data.job.result.document,contextKey)}
   opportunityEvidenceState.jobId="";
   saveOpportunityJobId("",contextKey);
   return data.job.result;
  }
  if(data.job.status==="failed")throw new Error(data.job.error||data.job.message||"机会地图生成失败");
  await opportunityPause(1000);
 }
 throw new Error("机会地图运行超过12分钟，请检查网络后重试；已填写的官网地址不会丢失");
}
const opportunityJobResumeContexts=new Set();
async function restoreLatestOpportunityDocument(contextKey=opportunityCacheContext().key){
 const cached=loadOpportunityDocument(contextKey),context=opportunityCacheContext(),model=context.model==="unselected"?"":context.model,ed=context.edition;
 if(!model)return cached;
 try{
  const data=await api(`/api/opportunity-map/own-document/latest?edition=${encodeURIComponent(ed)}&model=${encodeURIComponent(model)}`);
  saveOpportunityDocument(data.document||null,contextKey);
  if(contextKey!==opportunityCacheContext().key)return null;
  opportunityEvidenceState.document=data.document||null;
  renderOpportunityEvidence();
  return data.document||null;
 }catch(_){return cached}
}
async function resumeOpportunityMapJob(contextKey=opportunityCacheContext().key){
 const jobId=contextKey===opportunityCacheContext().key?(opportunityEvidenceState.jobId||loadOpportunityJobId(contextKey)):loadOpportunityJobId(contextKey);
 if(!jobId||opportunityJobResumeContexts.has(contextKey))return null;
 opportunityJobResumeContexts.add(contextKey);
 if(contextKey!==opportunityCacheContext().key){opportunityJobResumeContexts.delete(contextKey);return null}
 opportunityEvidenceState.loading=true;
 opportunityEvidenceState.job={jobId,status:"queued",stage:"alignment",progress:1,message:"正在恢复上次机会地图任务",elapsedSeconds:0};
 renderOpportunityEvidence();
 try{
  const result=await waitForOpportunityMapJob(jobId,contextKey);
  if(result&&contextKey===opportunityCacheContext().key)toast("机会地图后台任务已完成");
  return result;
  }catch(err){
  if(contextKey===opportunityCacheContext().key){opportunityEvidenceState.error=err.message;opportunityEvidenceState.jobId=""}
  saveOpportunityJobId("",contextKey);
  return null;
 }finally{
  opportunityJobResumeContexts.delete(contextKey);
  if(contextKey===opportunityCacheContext().key){opportunityEvidenceState.loading=false;render()}
 }
}
async function loadCockpitDecisionCycles(contextKey=opportunityCacheContext().key){
 const context=opportunityCacheContext(),model=context.model==="unselected"?"":context.model,ed=context.edition;
 if(!model){cockpitDecisionState={cycles:[],loading:false,error:""};saveCockpitDecisionCycleCache([],contextKey);return []}
 if(contextKey!==context.key)return [];
 cockpitDecisionState={...cockpitDecisionState,loading:true,error:""};
 try{
  const data=await api(`/api/cockpit/execution-cycles?edition=${encodeURIComponent(ed)}&model=${encodeURIComponent(model)}`);
  saveCockpitDecisionCycleCache(data.cycles||[],contextKey);
  if(contextKey!==opportunityCacheContext().key)return [];
  cockpitDecisionState={cycles:data.cycles||[],loading:false,error:""};
  renderCockpitEvidenceChain();
  renderCockpitDecisionLoop();
  return cockpitDecisionState.cycles;
 }catch(err){
  if(contextKey!==opportunityCacheContext().key)return [];
  cockpitDecisionState={...cockpitDecisionState,loading:false,error:err.message};
  renderCockpitEvidenceChain();
  renderCockpitDecisionLoop();
  return [];
 }
}
async function initCloudLoginGate(){
 const screen=document.querySelector("#cloud-login-screen"),form=document.querySelector("#cloud-login-form"),msg=document.querySelector("#cloud-login-message");
 if(!screen||!form)return true;
 try{
  const res=await fetch("/api/auth/config",{headers:authHeaders()});
  const data=await res.json();
  if(!data.loginRequired){screen.hidden=true;return true}
  document.body.classList.add("cloud-auth-required");
  if(session?.token&&data.user){screen.hidden=true;return true}
  if(session?.token&&!data.user){
   localStorage.removeItem("mmnCommercialSession");
   session=null;
   loadEditionData({syncServer:false});
   resetBrowserScopeTransientState();
   resetOpportunityContextState();
  }
  screen.hidden=false;
  form.onsubmit=async e=>{
   e.preventDefault();
   const old=msg.textContent;
   msg.textContent="正在验证账号权限…";
   form.querySelector("button").disabled=true;
   try{
    const fd=new FormData(form);
    const data=await api("/api/login",{method:"POST",body:JSON.stringify({username:fd.get("username"),password:fd.get("password")})});
    saveSession(data.session);
    screen.hidden=true;
    startAppDataLoads();
    signalAppAuthReady();
    toast(`${data.session.name} 已进入云端演示环境`);
   }catch(err){
    msg.textContent=err.message||"登录失败，请检查账号密码。";
   }finally{
    form.querySelector("button").disabled=false;
   if(msg.textContent==="正在验证账号权限…")msg.textContent=old;
   }
  };
  return false;
 }catch(err){
  screen.hidden=false;
  msg.textContent="云端登录状态检查失败，请稍后刷新。";
  return false;
 }
}
async function loadServerLearnings(){if(!session)return;try{const data=await api(`/api/learnings?org_id=${encodeURIComponent(session.org_id)}&edition=${encodeURIComponent(activeEdition())}`);serverLearnings=data.items.map(x=>({...x,savedAt:x.saved_at,userId:x.user_id,orgId:x.org_id}));render()}catch(e){toast(`学习库同步失败：${e.message}`)}}
async function loadWorkspace(){
 if(!session){workspaceState=defaultWorkspaceState();renderWorkspace();return}
 try{const data=await api(`/api/workspace?org_id=${encodeURIComponent(session.org_id)}&edition=${encodeURIComponent(activeEdition())}`);workspaceState={...defaultWorkspaceState(),...data.workspace};renderWorkspace()}
 catch(e){toast(`空间配置读取失败：${e.message}`)}
}
async function loadAiStatus(){
 try{const data=await api("/api/ai/status");aiStatus=data;renderWorkspace()}
 catch{aiStatus={qwen:{configured:false,model:"qwen-plus",baseUrl:"https://dashscope.aliyuncs.com/compatible-mode/v1"},deepseek:{configured:false,model:"deepseek-chat",baseUrl:"https://api.deepseek.com"},openai:{configured:false,model:"gpt-5.5",baseUrl:"https://api.openai.com/v1"},rules:{configured:true,model:"MMN规则引擎"}}}
}
function projectSnapshotPayload(){return{edition:activeEdition(),state,videoState,creatorState,verticalState,strategyKb,learnings:learnings().filter(x=>x.model===state.config.model),savedAt:new Date().toISOString()}}
async function syncProjectSnapshot(silent=false){
 if(!session){if(!silent)toast("请先进入客户空间，再保存项目快照");return}
 try{
  const data=await api("/api/project-state",{method:"POST",body:JSON.stringify({org_id:session.org_id,user_id:session.user_id,edition:activeEdition(),payload:projectSnapshotPayload()})});
  workspaceState.snapshots=[{id:data.id,brand:state.config.brand,model:state.config.model,project:state.config.project,data_version:state.datasetVersion,created_at:data.createdAt},...(workspaceState.snapshots||[])].slice(0,8);
  renderWorkspace();
  if(!silent)toast("项目快照已保存到本地数据库");
 }catch(e){if(!silent)toast(`快照保存失败：${e.message}`)}
}
function queueWorkspaceSnapshot(){if(!session)return;clearTimeout(workspaceSyncTimer);workspaceSyncTimer=setTimeout(()=>syncProjectSnapshot(true),1800)}
function learnings(){if(session)return serverLearnings;try{return JSON.parse(localStorage.getItem(storageKey("mmnStrategyLearnings")))||[]}catch{return[]}}
function saveLearnings(items){localStorage.setItem(storageKey("mmnStrategyLearnings"),JSON.stringify(items))}
function similarLearnings(label,limit=3){return learnings().filter(x=>x.label===label||x.model===state.config.model).sort((a,b)=>(b.savedAt||"").localeCompare(a.savedAt||"")).slice(0,limit)}
function latestLearning(label){return learnings().filter(x=>x.model===state.config.model&&x.label===label).sort((a,b)=>(b.savedAt||"").localeCompare(a.savedAt||""))[0]}
function isRedundantModelOption(model){
 const compact=String(model||"").replace(/\s+/g,"");
 return /^(?:上汽)?奥迪E5$/i.test(compact);
}
function modelOptions(){
 const models=new Set([state.config.model]);
 state.rows.forEach(r=>{if(r[0])models.add(r[0])});
 (verticalState.items||[]).forEach(x=>{if(x.ownModel)models.add(x.ownModel);if(x.competitor)models.add(x.competitor)});
 (modelJudgments||[]).forEach(x=>{if(x.model_name||x.model)models.add(x.model_name||x.model)});
 return [...models].filter(x=>x&&!isRedundantModelOption(x)).sort((a,b)=>String(a).localeCompare(String(b),"zh-CN",{numeric:true}));
}
function dashboardModelOptions(){
 const models=new Set([state.config.model]);
 state.rows.forEach(r=>{if(r[0])models.add(r[0])});
 return [...models].filter(x=>x&&!isRedundantModelOption(x)).sort((a,b)=>String(a).localeCompare(String(b),"zh-CN",{numeric:true}));
}
function learningModelOptions(){
 const models=new Set(modelOptions());
 Object.keys(modelIdentities.items||{}).forEach(x=>x&&models.add(x));
 learnings().forEach(x=>{if(x.model)models.add(x.model)});
 return [...models].filter(x=>x&&!isRedundantModelOption(x)).sort((a,b)=>String(a).localeCompare(String(b),"zh-CN",{numeric:true}));
}
function dataModelOptions(){
 return [...new Set(state.rows.map(r=>r[0]).filter(x=>x&&!isRedundantModelOption(x)))].sort((a,b)=>String(a).localeCompare(String(b),"zh-CN",{numeric:true}));
}
function brandForModel(model){
 const text=String(model||"").trim();
 const rules=[
  ["firefly","firefly"],["萤火虫","firefly"],
  ["艾力绅","东风本田"],["奥德赛","广汽本田"],["本田","本田"],
  ["宝骏悦也","宝骏"],["宝骏","宝骏"],["缤果","五菱"],["宏光","五菱"],
  ["北京越野","北京越野"],["BJ30","北京越野"],
  ["奔腾小马","奔腾"],["奔腾","奔腾"],
  ["标致","标致"],
  ["铂智","广汽丰田"],["锋兰达","广汽丰田"],["广汽丰田","广汽丰田"],["格瑞维亚","一汽丰田"],["丰田 bZ","丰田"],["丰田bZ","丰田"],
  ["宝来","大众"],["T-ROC","大众"],["探歌","大众"],["途观","大众"],["途昂","大众"],["朗逸","大众"],["速腾","大众"],
  ["MINI","MINI"],["ACEMAN","MINI"],["COOPER","MINI"],
  ["凡尔赛","雪铁龙"],["C5 X","雪铁龙"],
  ["大通","上汽大通"],["G50","上汽大通"],
  ["埃尚","埃尚"],["极狐","极狐"],
  ["MG","MG"],
  ["QQ冰淇淋","奇瑞"],["QQ3","奇瑞"],["QQ","奇瑞"],
  ["RAV4","丰田"],
  ["T-ROC","大众"],["探歌","大众"],
  ["smart","smart"],["精灵","smart"],
  ["沃尔沃","沃尔沃"],["Volvo","沃尔沃"],["EX90","沃尔沃"],["XC60","沃尔沃"],["XC90","沃尔沃"],["S90","沃尔沃"],
  ["阿维塔","阿维塔"],["埃安","广汽埃安"],["AION","广汽埃安"],["艾瑞泽","奇瑞"],["瑞虎","奇瑞"],["风云","奇瑞"],
  ["昂科威","别克"],["别克","别克"],["奥迪","奥迪"],["E5 Sportback","奥迪"],["E5","奥迪"],["荣威","荣威"],["宝马","宝马"],["奔驰","奔驰"],["本田","本田"],
  ["启境GT7","启境"],["启境","启境"],["Qijing GT7","启境"],["Qijing","启境"],["QIJING","启境"],
  ["智己LS9","智己"],["智己LS8","智己"],["智己LS7","智己"],["智己LS6","智己"],["智己L6","智己"],["智己","智己"],["小米","小米汽车"],["SU7","小米汽车"],["Model","特斯拉"],["乐道","乐道"],["ONVO","乐道"],["蔚来","蔚来"],["ET","蔚来"],
  ["ZEEKR","极氪"],["Zeekr","极氪"],["ZEEKER","极氪"],["Zeeker","极氪"],["极氪","极氪"],["007","极氪"],["001","极氪"],["理想","理想"],["问界","问界"],["比亚迪","比亚迪"],
  ["秦","比亚迪"],["宋","比亚迪"],["唐","比亚迪"],["海鸥","比亚迪"],["海豚","比亚迪"],["海狮","比亚迪"],
  ["银河","吉利银河"],["星愿","吉利"],["星瑞","吉利"],["领克","领克"],["零跑","零跑"],["小鹏","小鹏"],
  ["传祺","广汽传祺"],["腾势","腾势"],["深蓝","深蓝"],["长安","长安"],["五菱","五菱"]
 ];
 const hit=rules.find(([k])=>text.toLowerCase().includes(k.toLowerCase()));
 if(hit)return hit[1];
 const cleaned=text.replace(/[A-Z0-9\\s].*$/,"").replace(/[\\-_/].*$/,"").trim();
 return cleaned&&knownBrandNames.includes(cleaned)?cleaned:"待人工确认";
}
function modelNameUnderBrand(brand,model){
 const id=standardIdentityFor(model);
 const b=String(brand||"").trim(),m=String(model||"").trim();
  const aliases={
  沃尔沃:["沃尔沃","Volvo"],
  智己:["智己"],
  奥迪:["奥迪","Audi"],
  宝马:["宝马","BMW"],
  奔驰:["奔驰","Mercedes-Benz","Mercedes"],
  荣威:["荣威","Roewe","ROEWE"],
  启境:["启境","Qijing","QIJING"],
  蔚来:["蔚来","NIO"],
  小鹏:["小鹏"],
  理想:["理想"],
  问界:["问界"],
  特斯拉:["特斯拉","Tesla"],
  小米汽车:["小米"],
  极氪:["极氪","ZEEKR","Zeekr","Zeeker"],
  阿维塔:["阿维塔"],
  奇瑞:["奇瑞"],
  MG:["MG"],
  宝骏:["宝骏"],
  北京越野:["北京越野","BJ"],
  奔腾:["奔腾"],
  标致:["标致"],
  MINI:["MINI","电动 MINI"],
  雪铁龙:["雪铁龙"],
  上汽大通:["上汽大通","大通"],
  东风本田:["东风本田","本田"],
  广汽本田:["广汽本田","本田"],
  埃尚:["埃尚"],
  极狐:["极狐"],
  丰田:["丰田","Toyota"],
  广汽丰田:["广汽丰田","丰田"],
  一汽丰田:["一汽丰田","丰田"],
  大众:["大众","Volkswagen"],
  smart:["smart"],
  firefly:["firefly","萤火虫"],
  待人工确认:[],
  比亚迪:["比亚迪"],
  广汽埃安:["广汽埃安","埃安","AION"],
  广汽传祺:["广汽传祺","传祺"],
  吉利银河:["吉利银河","银河"]
 };
 const names=aliases[b]||[b];
 let out=String(id?.display_model_name||id?.displayModelName||id?.normalized_name||m).trim();
 names.filter(Boolean).forEach(alias=>{out=out.replace(new RegExp(`^${alias}\\s*`,"i"),"")});
 return out.trim()||m;
}
function brandModelGroups(models){
 const groups={};
 models.forEach(model=>{
  const brand=brandForDisplay(model),id=standardIdentityFor(model);
  if(brand==="待确认品牌"||brand==="待人工确认")return;
  const energy=id?.energy_type||id?.energyType||"UNKNOWN";
  const key=[brand,id?.model_family||id?.modelFamily||id?.normalized_name||model,energy].join("|");
  const list=(groups[brand]||(groups[brand]=new Map()));
  const current=list.get(key);
  if(!current||canonicalModelLabel(model).length>=canonicalModelLabel(current).length)list.set(key,model);
 });
 return Object.entries(groups).sort((a,b)=>a[0].localeCompare(b[0],"zh-CN",{numeric:true})).map(([brand,map])=>({brand,models:[...map.values()].sort((a,b)=>a.localeCompare(b,"zh-CN",{numeric:true}))}));
}
function cognitionModelOptions(){
 const models=new Set([state.config.model]);
 state.rows.forEach(r=>{if(r[0])models.add(r[0])});
 (verticalState.items||[]).forEach(x=>{if(x.ownModel)models.add(x.ownModel);if(x.competitor)models.add(x.competitor)});
 (modelJudgments||[]).forEach(x=>{if(x.model_name||x.model)models.add(x.model_name||x.model)});
 return [...models].filter(Boolean).sort((a,b)=>String(a).localeCompare(String(b),"zh-CN",{numeric:true}));
}
function cognitionBrandModelGroups(models){
 const groups={};
 models.forEach(model=>{
  const brand=brandForDisplay(model)||brandForModel(model)||"待确认品牌";
  const id=standardIdentityFor(model);
  const energy=id?.energy_type||id?.energyType||"UNKNOWN";
  const key=[brand,id?.model_family||id?.modelFamily||id?.normalized_name||model,energy].join("|");
  const list=(groups[brand]||(groups[brand]=new Map()));
  const current=list.get(key);
  if(!current||canonicalModelLabel(model).length>=canonicalModelLabel(current).length)list.set(key,model);
 });
 return Object.entries(groups).sort((a,b)=>a[0].localeCompare(b[0],"zh-CN",{numeric:true})).map(([brand,map])=>({brand,models:[...map.values()].sort((a,b)=>a.localeCompare(b,"zh-CN",{numeric:true}))}));
}
function dcdTopPositiveCompetitors(model){
 const items=(verticalState.items||[]).filter(x=>x.ownModel===model&&x.platform==="懂车帝"&&x.competitor&&Number(x.positiveRank)>0);
 if(!items.length)return[];
 const periods=uniquePeriods(items),latest=periods[periods.length-1];
 const picked=new Map();
 items.filter(x=>x.period===latest).sort((a,b)=>(a.positiveRank||999)-(b.positiveRank||999)).forEach(x=>{
  if((+x.positiveRank||999)<=3&&!picked.has(x.competitor))picked.set(x.competitor,x);
 });
 return [...picked.values()].sort((a,b)=>(a.positiveRank||999)-(b.positiveRank||999)).slice(0,3).map(x=>x.competitor);
}
function syncDashboardCompetitors(){
 if(isBlockedImport())return String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
 if(isSummaryImport()){
  const comps=(state.models||[]).filter(model=>model!==state.config.model);
  const next=comps.join(" / ");
  if(state.config.competitor!==next)state.config.competitor=next;
  return comps;
 }
 const comps=dcdTopPositiveCompetitors(state.config.model),next=comps.join(" / ");
 if(state.config.competitor!==next)state.config.competitor=next;
 return comps;
}
const productEvaluationCatalog=new Map();
const PRODUCT_EVALUATION_CATALOG_STORAGE_BASE="mmnProductEvaluationCatalog";
const PRODUCT_EVALUATION_CATALOG_LIMIT=8;
const productEvaluationCatalogHydratedScopes=new Set();
const productEvaluationServerSyncAttempts=new Set();
function productEvaluationCatalogKey(model){return`${browserStorageScope(edition).identityKey}::${String(model||"").trim()}`}
function productEvaluationCatalogGet(model){return productEvaluationCatalog.get(productEvaluationCatalogKey(model))}
function productEvaluationCatalogHas(model){return productEvaluationCatalog.has(productEvaluationCatalogKey(model))}
const productEvaluationDatasetKeys=["datasetVersion","sourceNote","platforms","rows","models","summaryHeat","summaryPlatformNsr","summaryMetrics","summaryAttributeBenchmark","importQuality","sourceRowCount","aggregatedRowCount","replace","productEvaluationSourceModel"];
function productEvaluationSupportedModels(dataset={}){
 return[...new Set([...(dataset.models||[]),...Object.keys(dataset.summaryHeat||{}),...Object.keys(dataset.summaryPlatformNsr||{}),...(dataset.rows||[]).map(row=>row?.[0])].map(model=>String(model||"").trim()).filter(Boolean))];
}
function productEvaluationHasData(dataset={}){
 return Boolean((dataset.rows||[]).length||Object.keys(dataset.summaryHeat||{}).length||Object.keys(dataset.summaryPlatformNsr||{}).length||Object.keys(dataset.summaryMetrics||{}).length);
}
function productEvaluationDatasetSnapshot(dataset=state){
 if(!productEvaluationHasData(dataset)||dataset.importQuality?.kind==="PRODUCT_EVALUATION_UNAVAILABLE")return null;
 const snapshot={config:{...(dataset.config||{})}};
 productEvaluationDatasetKeys.forEach(key=>{if(dataset[key]!==undefined)snapshot[key]=dataset[key]});
 snapshot.models=productEvaluationSupportedModels(snapshot);
 const ownRows=[...new Set((snapshot.rows||[]).filter(row=>row?.[1]==="本品"&&row?.[0]).map(row=>row[0]))];
 snapshot.productEvaluationSourceModel=snapshot.productEvaluationSourceModel||(ownRows.length===1?ownRows[0]:snapshot.models.includes(snapshot.config.model)?snapshot.config.model:"");
 return snapshot.models.length?snapshot:null;
}
function productEvaluationCatalogStorageKey(){return storageKey(PRODUCT_EVALUATION_CATALOG_STORAGE_BASE,activeEdition())}
function productEvaluationPersistenceId(dataset={}){return String(dataset.productEvaluationSourceModel||dataset.config?.model||dataset.datasetVersion||"").trim()}
function loadPersistedProductEvaluationDatasets(){
 try{const value=JSON.parse(localStorage.getItem(productEvaluationCatalogStorageKey())||"[]");return Array.isArray(value)?value:[]}
 catch(_){return[]}
}
function persistProductEvaluationDataset(dataset){
 const snapshot=productEvaluationDatasetSnapshot(dataset),id=productEvaluationPersistenceId(snapshot||{});if(!snapshot||!id)return false;
 const retained=loadPersistedProductEvaluationDatasets().filter(item=>productEvaluationPersistenceId(item)!==id);
 try{localStorage.setItem(productEvaluationCatalogStorageKey(),JSON.stringify([snapshot,...retained].slice(0,PRODUCT_EVALUATION_CATALOG_LIMIT)));return true}catch(_){return false}
}
function registerProductEvaluationDataset(dataset,{replaceSource=true,persist=true}={}){
 const snapshot=productEvaluationDatasetSnapshot(dataset);if(!snapshot)return false;
 snapshot.models.forEach(model=>{const key=productEvaluationCatalogKey(model);if(!productEvaluationCatalog.has(key)||(replaceSource&&model===snapshot.productEvaluationSourceModel))productEvaluationCatalog.set(key,snapshot)});
 if(persist)persistProductEvaluationDataset(snapshot);
 return true;
}
function hydrateProductEvaluationCatalog(){
 const scope=browserStorageScope(activeEdition()).identityKey;if(productEvaluationCatalogHydratedScopes.has(scope))return;
 productEvaluationCatalogHydratedScopes.add(scope);
 loadPersistedProductEvaluationDatasets().forEach(dataset=>registerProductEvaluationDataset(dataset,{persist:false}));
}
function seedBundledProductEvaluationDatasets(){
 if(activeEdition()==="china"&&importedDataset)registerProductEvaluationDataset(importedDataset,{replaceSource:false,persist:false});
}
function prepareProductEvaluationCatalog(){hydrateProductEvaluationCatalog();seedBundledProductEvaluationDatasets()}
function rememberCurrentProductEvaluationDataset(){return registerProductEvaluationDataset(state)}
function productEvaluationServerContextKey(){return`${browserStorageScope(activeEdition()).identityKey}::${activeEdition()}`}
async function syncProductEvaluationDatasetToServer(dataset){
 const snapshot=productEvaluationDatasetSnapshot(dataset);if(!snapshot)return false;
 const attemptKey=`${productEvaluationServerContextKey()}::${productEvaluationDatasetSignature(snapshot)}`;if(productEvaluationServerSyncAttempts.has(attemptKey))return true;
 productEvaluationServerSyncAttempts.add(attemptKey);
 try{await api("/api/product-evaluation-catalog",{method:"POST",body:JSON.stringify({edition:activeEdition(),dataset:snapshot})});return true}
 catch(_){return false}
}
async function restoreProductEvaluationCatalogFromServer(){
 const contextKey=productEvaluationServerContextKey(),localCandidate=productEvaluationDatasetSnapshot(state);
 try{
  const data=await api(`/api/product-evaluation-catalog?edition=${encodeURIComponent(activeEdition())}`);if(contextKey!==productEvaluationServerContextKey())return false;
  const items=Array.isArray(data.datasets)?data.datasets:[],serverSources=new Set();
  items.forEach(item=>{if(!item?.dataset)return;serverSources.add(String(item.sourceModel||item.dataset.productEvaluationSourceModel||""));registerProductEvaluationDataset(item.dataset,{persist:true})});
  const model=state.config?.model,registered=productEvaluationCatalogGet(model);
  if(registered&&productEvaluationDatasetNeedsUpgrade(registered,model)){installProductEvaluationDataset(registered,model);save();render()}
  const localSource=productEvaluationPersistenceId(localCandidate||{});if(localCandidate&&localSource&&!serverSources.has(localSource))syncProductEvaluationDatasetToServer(localCandidate);
  return true;
 }catch(_){return false}
}
function unavailableProductEvaluationDataset(model){
 return{datasetVersion:`product_evaluation_unavailable_${model}`,sourceNote:`${model} 暂无已绑定的产品评价数据；当前已清除上一车型数据，等待导入该车型数据。`,config:{model,brand:brandForModel(model),project:`${model}认知诊断`,competitor:""},platforms:{...state.platforms},rows:[],models:[model],summaryHeat:{},summaryPlatformNsr:{},summaryMetrics:{},summaryAttributeBenchmark:{},importQuality:{kind:"PRODUCT_EVALUATION_UNAVAILABLE",timeRange:"",metricCoverage:{nsr:false,ips:false,intent:false,risk:false},attributeVolumeAvailable:false,platformVolumeAvailable:false,platformNsrAvailable:false,platformNsrSources:[],attributeNsrSources:[],message:`${model} 暂无产品评价数据，未沿用其他车型数据。`},sourceRowCount:0,aggregatedRowCount:0,replace:true,productEvaluationSourceModel:""};
}
function reconcileProductEvaluationBinding(){
 const model=state.config?.model;if(!model)return false;
 prepareProductEvaluationCatalog();
 rememberCurrentProductEvaluationDataset();
 const registered=productEvaluationCatalogGet(model);
 if(registered&&!productEvaluationDatasetNeedsUpgrade(registered,model))return true;
 installProductEvaluationDataset(registered||unavailableProductEvaluationDataset(model),model);
 return true;
}
function productEvaluationAttributeCategory(label){
 const text=String(label||"");
 if(/价格|权益/.test(text))return"价格权益";
 if(/动力|操控/.test(text))return"动力与操控";
 if(/外观|内饰|设计/.test(text))return"设计体验";
 if(/安全|质量/.test(text))return"安全质量";
 if(/智能|辅助|驾驶|座舱/.test(text))return"智能化";
 if(/空间|舒适/.test(text))return"空间舒适";
 if(/品牌|口碑/.test(text))return"品牌信任";
 return"其他赛道";
}
function productEvaluationSummaryDataset(evaluation){
 if(!evaluation||evaluation.status!=="available"||!evaluation.ownModel)return null;
 if(evaluation.dataset?.config?.model===evaluation.ownModel){
  const dataset={...evaluation.dataset,config:{...evaluation.dataset.config},productEvaluationSourceModel:evaluation.ownModel};
  dataset.sourceNote=`${dataset.sourceNote||"已载入产品评价数据"}；原始文件已登记校验：${evaluation.sourceAsset?.sha256?.slice(0,12)||"待登记"}。`;
  return dataset;
 }
 const ownModel=String(evaluation.ownModel),models=(evaluation.models||[]).map(item=>String(item.model||"").trim()).filter(Boolean);
 if(!models.includes(ownModel)||models.length<2)return null;
 const competitors=models.filter(model=>model!==ownModel),source=evaluation.source||{},attributes=(evaluation.attributes||[]).filter(item=>item.attribute&&nullableNumber(item.ownNsr)!==null),summaryHeat={},summaryPlatformNsr={},summaryMetrics={};
 (evaluation.models||[]).forEach(item=>{const model=String(item.model||"").trim();if(!model)return;summaryHeat[model]={volume:Number(item.voice||0),interaction:Number(item.engagement||0),platformVolume:{}};summaryPlatformNsr[model]={"全网":nullableNumber(item.overallNsr),"垂媒车主口碑":nullableNumber(item.verticalNsr),"抖音":nullableNumber(item.douyinNsr)};summaryMetrics[model]={overallNsr:nullableNumber(item.overallNsr)}});
 const rows=attributes.map(item=>{const nsr=nullableNumber(item.ownNsr),label=String(item.attribute);return[ownModel,"本品","全网",productEvaluationAttributeCategory(label),label,nsr>=.6?"信任":nsr>=.25?"认可":nsr>=0?"期待":"怀疑","目标核心人群","无",100,3,1,4,"汇总NSR评分",`数据整理｜全网｜${label}`,nsr]});
 const benchmark={"全网":Object.fromEntries(attributes.map(item=>[String(item.attribute),nullableNumber(item.averageNsr)]).filter(([,value])=>value!==null))};
 return{
  datasetVersion:`product_evaluation_${ownModel}_${source.period||"current"}`.replace(/\s+/g,"_"),
  sourceNote:`已载入《${source.fileName||`${ownModel}产品评价汇总`}》；数据周期：${source.period||"当前周期"}；识别车型：${models.join("、")}；属性竞品口径：${competitors.length}车均值。`,
  config:{project:`${ownModel}认知诊断｜${competitors.length}车核心竞品`,brand:brandForModel(ownModel),model:ownModel,competitor:competitors.join(" / ")},
  platforms:{"全网":1,"垂媒车主口碑":1.15,"抖音":1.35},rows,models,summaryHeat,summaryPlatformNsr,summaryMetrics,summaryAttributeBenchmark:benchmark,
  importQuality:{kind:"PRODUCT_EVALUATION_SUMMARY",timeRange:source.period||"当前周期",metricCoverage:{nsr:true,ips:false,intent:false,risk:false},attributeVolumeAvailable:false,platformVolumeAvailable:false,platformNsrAvailable:true,platformNsrSources:["全网","垂媒车主口碑","抖音"],attributeNsrSources:["全网"],attributeBenchmarkLabel:`${competitors.length}车竞品均值`,attributeBenchmarkModels:competitors,message:`源表提供${models.length}车总体声量、互动量、整体/垂媒/抖音NSR，以及${ownModel}属性NSR与${competitors.length}车均值；未提供逐竞品属性NSR，不作推断。`},
  sourceRowCount:models.length,aggregatedRowCount:rows.length,replace:true,productEvaluationSourceModel:ownModel
 };
}
function productEvaluationDatasetMatches(model){return state.productEvaluationBoundModel===model&&productEvaluationSupportedModels(state).includes(model)}
function productEvaluationDatasetSignature(dataset={}){
 const platformVolumeCount=Object.values(dataset.summaryHeat||{}).reduce((count,item)=>count+Object.keys(item?.platformVolume||{}).length,0);
 const platformNsrCount=Object.values(dataset.summaryPlatformNsr||{}).reduce((count,item)=>count+Object.keys(item||{}).length,0);
 return JSON.stringify({
  datasetVersion:String(dataset.datasetVersion||""),
  sourceModel:String(dataset.productEvaluationSourceModel||dataset.config?.model||""),
  models:productEvaluationSupportedModels(dataset).sort(),
  rowCount:(dataset.rows||[]).length,
  rowModels:[...new Set((dataset.rows||[]).map(row=>String(row?.[0]||"")).filter(Boolean))].sort(),
  attributeSources:[...new Set((dataset.rows||[]).map(row=>String(row?.[2]||"")).filter(Boolean))].sort(),
  platformVolumeCount,
  platformNsrCount,
 });
}
function productEvaluationDatasetNeedsUpgrade(dataset,model){
 return!productEvaluationDatasetMatches(model)||productEvaluationDatasetSignature(state)!==productEvaluationDatasetSignature(dataset);
}
function installProductEvaluationDataset(dataset,model){
 if(!dataset||!productEvaluationSupportedModels(dataset).includes(model))return false;
 const previousConfig=state.config||{};
 const sourceModel=dataset.productEvaluationSourceModel||dataset.config?.model||"",hasTargetAttributes=(dataset.rows||[]).some(row=>row?.[0]===model&&row?.[4]),sourceNote=model!==sourceModel&&!hasTargetAttributes?`${dataset.sourceNote||"已载入产品评价数据"}；${model} 当前只有总体指标，暂无该车型属性数据。`:dataset.sourceNote;
 state={...state,...dataset,sourceNote,summaryAttributeBenchmark:model===sourceModel?(dataset.summaryAttributeBenchmark||{}):{},productEvaluationBoundModel:model,config:{...previousConfig,...dataset.config,model,brand:brandForModel(model)}};
 summaryDashboardModels=[model,...productEvaluationSupportedModels(dataset).filter(item=>item!==model).slice(0,4)];
 summaryAttributeActiveLabel="";summaryAttributeActiveCategory="全部";summaryAttributeEvidenceExpanded=false;resetSummaryQuadrantCollapse();
 sellingPointInputModel=model;sellingPointActiveLabel="";sellingPointActiveCompetitor="";
 return true;
}
function registerProductEvaluation(evaluation,{activateCurrent=true}={}){
 const dataset=productEvaluationSummaryDataset(evaluation);if(!dataset)return false;
 registerProductEvaluationDataset(dataset);
 syncProductEvaluationDatasetToServer(dataset);
 const currentModel=state.config.model,registered=productEvaluationCatalogGet(currentModel);
 if(activateCurrent&&registered&&productEvaluationDatasetNeedsUpgrade(registered,currentModel)){
  installProductEvaluationDataset(registered,currentModel);save();queueMicrotask(()=>render());
 }
 return true;
}
function applyModelSelection(model){
 prepareProductEvaluationCatalog();
 const models=modelOptions();
 if(!models.includes(model)&&!productEvaluationCatalogHas(model))return;
 const changed=state.config.model!==model;
 rememberCurrentProductEvaluationDataset();
 const registered=productEvaluationCatalogGet(model);
 if(!productEvaluationDatasetMatches(model))installProductEvaluationDataset(registered||unavailableProductEvaluationDataset(model),model);
 state.config.model=model;
 state.config.brand=brandForModel(model);
 const datasetCompetitors=productEvaluationDatasetMatches(model)?(state.models||[]).filter(item=>item!==model):[];
 const comps=datasetCompetitors.length?datasetCompetitors:dcdTopPositiveCompetitors(model);
 state.config.competitor=comps.join(" / ");
 state.config.project=`${model}认知诊断${comps.length?`｜${comps.length}车核心竞品`:""}`;
 sellingPointInputModel=model;
 if(changed){
  videoState.config={...videoState.config,ownModel:model,competitor1:comps[0]||"",competitor2:comps[1]||"",competitor3:comps[2]||""};
  contentStrategyState={loading:false,result:null,error:""};
  resetContentPptPlan();
  saveVideoState();
  resetOpportunityContextState();
  restoreOpportunityContext();
 }
}
function selectDashboardVehicleContext(model,{source="dashboard",notify=true,cycleContext=null}={}){
 const models=modelOptions();
 if(!models.includes(model)&&!productEvaluationCatalogHas(model))return false;
 if(source==="sales-warning"&&!managementDashboardVisible)return false;
 if(managementDashboardVisible&&source!=="sales-warning"){
  if(notify)toast("管理层看板开启时，分析车型由销量预警统一控制");
  queueMicrotask(()=>render());
  return false;
 }
 if(source==="sales-warning")managementWarningContextReady=true;
 const changed=state.config.model!==model;
 applyModelSelection(model);
 if(cycleContext)syncMarketingModelCycleContext(cycleContext,model);
 dashBrandOpen=brandForDisplay(model);
 dashboardTopicPlanState={loading:false,result:null,error:""};
 save();
 render();
 window.dispatchEvent(new CustomEvent("mmn:vehicle-context-updated",{detail:{model,source,changed}}));
 if(changed&&notify)toast(source==="sales-warning"?`驾驶舱已跟随销量预警切换为 ${model}`:`已切换为 ${model}`);
 return true;
}
window.MMNVehicleContext={
 getModel:()=>state.config.model,
 select:(model,options={})=>selectDashboardVehicleContext(model,options),
 registerProductEvaluation:(evaluation,options={})=>registerProductEvaluation(evaluation,options)
};
window.addEventListener("mmn:sales-warning-model-selected",event=>{
 const cycleContext=event.detail?.cycleContext,model=event.detail?.model;
 if(!cycleContext||!model)return;
 syncMarketingModelCycleContext(cycleContext,model);
 if(model===state.config.model){renderTCyclePanel();renderSellingPointDecisionWorkbench()}
});
window.addEventListener("mmn:sales-warning-cycle-refresh-failed",()=>{
 const model=state.config.model,current=rawMarketingModelContext(model),cycleContext=current.salesWarningCycle;
 if(!cycleContext||cycleContext.status!=="verified")return;
 syncMarketingModelCycleContext({...cycleContext,refreshStatus:"stale"},model);
 renderTCyclePanel();renderSellingPointDecisionWorkbench();
});
function isSummaryImport(){return state.importQuality?.kind==="PRODUCT_EVALUATION_SUMMARY"}
function isUnavailableProductEvaluation(){return state.importQuality?.kind==="PRODUCT_EVALUATION_UNAVAILABLE"}
function isBlockedImport(){return state.importQuality?.kind==="INVALID_LEGACY_SUMMARY_IMPORT"}
function summaryMetric(model=state.config.model){return state.summaryMetrics?.[model]||{}}
function metricDisplay(a){
 const coverage=state.importQuality?.metricCoverage||{};
 if(isUnavailableProductEvaluation())return{nsr:"—",nsrNote:"暂无产品评价数据",ips:"—",ipsNote:"暂无产品评价数据",intent:"—",intentNote:"暂无产品评价数据",risk:"—"};
 if(isBlockedImport())return{nsr:"请重新导入",nsrNote:state.importQuality.message,ips:"请重新导入",ipsNote:"旧版结果已隔离",intent:"请重新导入",intentNote:"旧版结果已隔离",risk:"请重新导入"};
 if(isSummaryImport())return{
  nsr:typeof summaryMetric().overallNsr==="number"?`${(summaryMetric().overallNsr*100).toFixed(1)}%`:"—",
  nsrNote:"源表全网NSR",
  ips:coverage.ips?`${(a.ips*100).toFixed(1)}%`:"不适用",
  ipsNote:coverage.ips?"目标身份有效评论占比":"源表未提供目标人群字段",
  intent:coverage.intent?a.intent.toFixed(2):"不适用",
  intentNote:coverage.intent?"越高代表声量越接近购买":"源表未提供购买意向字段",
  risk:coverage.risk?Math.round(a.neg).toLocaleString():"不适用"
 };
 return{nsr:`${(a.nsr*100).toFixed(1)}%`,nsrNote:a.nsr>=.7?"口碑健康":"需要优先处理购买阻力",ips:`${(a.ips*100).toFixed(1)}%`,ipsNote:"目标身份有效评论占比",intent:a.intent.toFixed(2),intentNote:"越高代表声量越接近购买",risk:Math.round(a.neg).toLocaleString()};
}
function metricValues(a){
 if(isSummaryImport())return{nsr:summaryMetric().overallNsr??null,ips:null,intent:null,risk:null,coverage:state.importQuality?.metricCoverage||{}};
 return{nsr:+(a.nsr||0).toFixed(3),ips:+(a.ips||0).toFixed(3),intent:+(a.intent||0).toFixed(3),risk:Math.round(a.neg||0),coverage:{nsr:true,ips:true,intent:true,risk:true}};
}
function score(r){
 const [sat,risk]=emotions[r[5]]||[0,0],iw=identityWeights[r[6]]||.85,pw=state.platforms[r[2]]||1,intw=intentWeights[r[7]]||.5,n=+r[8]||0,impact=+r[9]||3,summaryNsr=Number(r[14]);
 if(isSummaryImport()&&Number.isFinite(summaryNsr))return{positive:summaryNsr>0?n*summaryNsr*iw*pw:0,negative:summaryNsr<0?n*Math.abs(summaryNsr)*impact*pw:0};
 return{positive:sat>0?n*sat*iw*pw*intw:0,negative:risk>0?n*risk*impact*pw*intw:0}
}
function analysis(){
 const modelRows=state.rows.filter(r=>r[0]===state.config.model);
 const own=modelRows;
 const configuredComps=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
 const comp=own.length
  ?state.rows.filter(r=>r[0]!==state.config.model&&(!configuredComps.length||configuredComps.includes(r[0])||r[1]==="竞品"))
  :[];
 const total=(arr,i)=>arr.reduce((s,r)=>s+(+r[i]||0),0), ownComments=total(own,8),compComments=total(comp,8);
 let pos=0,neg=0,intent=0,target=0;own.forEach(r=>{const s=score(r);pos+=s.positive;neg+=s.negative;intent+=(+r[8]||0)*(intentWeights[r[7]]||.5);if(r[6]===state.config.targetIdentity)target+=+r[8]||0});
 const scopedRows=own.length?[...own,...comp]:[];
 const labels=[...new Set(scopedRows.map(r=>r[4]).filter(Boolean))].map(label=>{
  const o=own.filter(r=>r[4]===label),c=comp.filter(r=>r[4]===label),sumScore=a=>a.reduce((z,r)=>{const s=score(r);z.p+=s.positive;z.n+=s.negative;return z},{p:0,n:0});
  const os=sumScore(o),cs=sumScore(c),oShare=ownComments?total(o,8)/ownComments:0,cShare=compComments?total(c,8)/compComments:0,gap=cShare-oShare;
  const impact=o.length?total(o,9)/o.length:3,growth=o.length?total(o,10)/o.length:1,competition=o.length?total(o,11)/o.length:3,white=Math.max(gap,0)*impact*growth/Math.max(competition,.1)*100;
  let diagnosis=os.n>=state.config.riskThreshold?"优先修复":white>=1?"抢占空位":os.p>os.n?"持续放大":"补充样本";
  let priority=diagnosis==="优先修复"?os.n/100:white*4*3.8;
  return{label,category:(o[0]||c[0]||[])[3]||"",op:os.p,on:os.n,cp:cs.p,cn:cs.n,oShare,cShare,gap,impact,growth,competition,white,diagnosis,priority}
 }).sort((a,b)=>b.priority-a.priority);
 return{own,comp,pos,neg,nsr:pos+neg?pos/(pos+neg):0,ips:ownComments?target/ownComments:0,intent:ownComments?intent/ownComments:0,ownComments,labels};
}
function actionFor(x){
 const type=x.diagnosis==="优先修复"?"风险修复":x.diagnosis==="抢占空位"?"认知抢位":x.diagnosis==="持续放大"?"资产放大":"数据补充";
 const proposition=type==="风险修复"?`消除用户对“${x.label}”的购买疑虑`:type==="认知抢位"?`建立“${x.label}是本品差异化优势”的认知`:type==="资产放大"?`把“${x.label}”从口碑变成可复述卖点`:`补充“${x.label}”有效样本`;
 const evidence=type==="风险修复"?"官方证据 + 第三方实测 + 车主答疑":type==="认知抢位"?"竞品对比 + 场景实验 + KOC矩阵":"技术解析 + 真实车主证词";
 const platform=["价格","品牌信任"].includes(x.label)?"微博 + 汽车之家":["智能驾驶","底盘滤震","操控稳定"].includes(x.label)?"抖音 + 懂车帝":"小红书 + 抖音";
 return{type,proposition,evidence,platform};
}
const knowhowLibrary={
  价格:{why:"价格争议本质不是贵不贵，而是用户还没有把配置、权益、保值、使用成本合并成一笔账。",crowd:"价格敏感用户 / 高意向犹豫人群",message:"把价格从单点数字改写成“总拥有成本 + 权益确定性 + 同价位配置差”。",proof:"权益清单、同级配置对比、金融方案、车主真实用车成本",creator:"官方产品经理定规则，垂媒做横评，真实车主讲账本",risk:"避免硬怼用户嫌贵，先承认门槛，再证明值。"},
  用车成本:{why:"用车成本会直接影响家庭决策和长周期持有信心。",crowd:"家庭用户 / 价格敏感用户",message:"把能耗、补能、保养、保险拆成真实场景账。",proof:"城市通勤能耗、长途补能记录、保养保险账单",creator:"车主日记 + 垂媒长测 + 产品专家答疑",risk:"不要只给官方 CLTC，用真实路线和极端天气补证据。"},
  安全:{why:"安全负面是高影响、低容忍问题，一旦进入购车决策，会压过外观和智能化好感。",crowd:"家庭用户 / 目标核心人群",message:"从“我说安全”切到“看得见、测得出、有人背书的安全”。",proof:"碰撞结构、主动安全触发、极端工况测试、第三方评价",creator:"工程师解释底层逻辑，第三方做实测，家庭用户讲安心感",risk:"不要空喊安全，必须有可验证画面和测试条件。"},
  质量:{why:"质量怀疑会放大新品牌或新车型的不确定感，影响下订和推荐。",crowd:"目标核心人群 / 增量人群",message:"把抽象质量变成制造标准、品控流程、长期耐久和售后承诺。",proof:"工厂品控、耐久测试、交付质检、售后响应 SLA",creator:"工厂探访 + 长测车主 + 售后负责人",risk:"不要只解释个案，要给系统性机制和改进闭环。"},
  "动力与操控":{why:"动力操控是情绪资产，也容易被竞品用参数或圈速抢走话语权。",crowd:"性能用户 / 科技用户",message:"把参数翻译成日常可感知的稳、准、快、舒服。",proof:"麋鹿测试、制动距离、山路/高架/雨天场景、竞品同场对比",creator:"专业测评人拉开差距，车主补充日常体感",risk:"避免只拼极限成绩，要回到用户每天开车的价值。"},
  "辅助/自动驾驶":{why:"智驾是高关注赛道，但用户更关心可用边界和接管焦虑。",crowd:"科技用户 / 高意向人群",message:"少讲概念，多讲“哪些路能用、什么时候好用、边界在哪里”。",proof:"城区/高速实录、接管次数、复杂路口通过率、OTA计划",creator:"工程师说明边界，KOC做连续通勤实测",risk:"不要过度承诺无人驾驶，边界透明反而增加信任。"},
  智能座舱:{why:"座舱好感通常来自第一眼体验，但需要持续内容把新鲜感变成使用黏性。",crowd:"科技用户 / 增量人群",message:"用高频任务展示座舱效率：导航、语音、娱乐、家庭协作。",proof:"功能录屏、任务挑战、用户场景脚本",creator:"数码博主 + 家庭用户 + 品牌体验官",risk:"避免堆功能名，必须用“一个场景解决一个麻烦”。"},
  外观:{why:"外观是破圈入口，但只靠审美容易短热，必须连接身份和场景。",crowd:"增量人群 / 年轻用户",message:"把设计语言转成身份标签、城市生活方式和社交表达。",proof:"设计师解读、街拍、改色案例、真实用户照片",creator:"设计师 + 生活方式达人 + 摄影师",risk:"不要自嗨式审美，要让用户参与二创。"},
  内饰:{why:"内饰决定坐进去的高级感，也是静态体验转化的重要触点。",crowd:"家庭用户 / 增量人群",message:"把材质、收纳、交互和舒适打包成“每天坐进去都舒服”。",proof:"材质细节、夜间氛围、亲子/通勤场景、竞品静态对比",creator:"女性/家庭 KOC + 场景体验短视频",risk:"避免只拍豪华感，要拍耐脏、易用、顺手。"},
  空间:{why:"空间不是尺寸竞赛，用户在意的是乘坐、储物、亲子、露营等具体任务。",crowd:"家庭用户",message:"用真实物品和真实乘员证明空间效率。",proof:"儿童座椅、后备箱装载、二排腿部/头部、长途乘坐",creator:"家庭车主 + 亲子达人 + 场景体验演示",risk:"不要只报轴距，要展示“能不能装、坐得累不累”。"},
  舒适性:{why:"舒适性连接家庭购买和高级感，是试驾最容易感知的转化点。",crowd:"家庭用户 / 目标核心人群",message:"把滤震、静谧、座椅、空调变成可比较的乘坐体验。",proof:"NVH测试、烂路滤震、水杯实验、长途乘坐反馈",creator:"车主长测 + 专业测评 + 家庭乘客视角",risk:"不要只讲配置，要把体感做成可看见的实验。"},
  用户服务:{why:"服务影响下订后的确定感，尤其对新势力和新车型会放大信任问题。",crowd:"目标核心人群 / 高意向人群",message:"把服务承诺从口号变成流程、时效、责任人和案例。",proof:"交付流程、售后响应时效、用户案例、服务网点覆盖",creator:"交付专家 + 真实车主 + 区域体验活动",risk:"不要只晒好评，要展示问题如何被解决。"},
  总体口碑:{why:"总体口碑是所有具体问题叠加后的信任温度，会影响搜索、搜索和推荐。",crowd:"目标核心人群 / 高意向人群",message:"先处理高风险负面，再用真实车主和第三方评价重建信任。",proof:"口碑样本复盘、车主证词、第三方横评、问题闭环",creator:"品牌负责人定调，车主和媒体补信任",risk:"不要用一条大广告解决口碑，要用连续证据修复。"}
};
function knowhowFor(x){
 const base=knowhowLibrary[x.label]||{why:`“${x.label}”正在影响用户对车型价值的判断。`,crowd:"目标核心人群 / 高意向人群",message:`把“${x.label}”从产品参数翻译成用户可感知的购买理由。`,proof:"场景实测、竞品对比、真实车主证词",creator:"产品专家 + KOC + 垂媒测评",risk:"避免只讲参数，必须给场景和证据。"};
 const ac=actionFor(x);
 const mode=x.diagnosis==="优先修复"?"先止血：先承认疑虑，再用证据拆解风险":x.diagnosis==="抢占空位"?"抢心智：在竞品更强的赛道里找到本品可占据的具体场景":x.diagnosis==="持续放大"?"做资产：把已有好评包装成用户能复述的卖点":"补样本：先拿到更多有效评价，再决定放大还是修复";
 const kpi=x.diagnosis==="优先修复"?"负面评论占比下降、搜索联想改善、试驾转化恢复":x.diagnosis==="抢占空位"?"目标标签声量提升、竞品领先 Gap 收窄、收藏/询价提升":"正向内容复述率、自然转发、KOC 二创数量";
 return{...base,...ac,mode,kpi};
}
function platformAdvice(platform){
 const map={
  抖音:"用强画面和强对比抓第一认知：实测、挑战、场景短剧、车主反应。",
  微博:"处理争议和公共议题：口径统一、信息澄清、负责人回应、热搜话题承接。",
  B站:"适合深度解释：长测、拆解、工程逻辑、横评复盘，建立理性信任。",
  微信视频号:"适合熟人传播和私域转化：直播答疑、车主故事、本地试驾邀请。",
  垂媒车主口碑:"适合影响高意向人群：真实车主口碑、车型论坛答疑、垂媒横评。",
  今日头条:"适合扩大泛人群覆盖：标题清晰、利益点明确、争议点快速解释。",
  其他:"承接长尾搜索和补充曝光：把核心证据沉淀成可检索内容。",
  小红书:"适合生活方式和家庭场景：真实体验、女性/家庭视角、图文收藏。",
  懂车帝:"适合参数和横评：榜单、测试、配置解释、购车决策对比。",
  汽车之家:"适合口碑与决策：车主评价、配置表、价格权益、意向线索。"
 };
 return map[platform]||"根据平台用户心智选择内容形态：短视频抓注意，长内容建信任，社区内容做转化。";
}
function money(n){return `${n.toFixed(1)} 万`}
function render(){
 const dashCompetitors=syncDashboardCompetitors();
 const a=analysis();
 const metrics=metricDisplay(a);
 renderEditionChrome();
 renderAccount();
 document.querySelector("#dash-project").textContent=state.config.project;renderModelSwitcher();document.querySelector("#dash-competitor").textContent=dashCompetitors.join(" / ");document.querySelector("#dash-samples").textContent=isBlockedImport()?"旧版结果已隔离":(isSummaryImport()?`${(state.models||[]).length} 车汇总对标`:`${a.ownComments.toLocaleString()} 条`);
 document.querySelector("#kpi-nsr").textContent=metrics.nsr;document.querySelector("#kpi-nsr-note").textContent=metrics.nsrNote;document.querySelector("#kpi-ips").textContent=metrics.ips;document.querySelector("#kpi-ips-note").textContent=metrics.ipsNote;document.querySelector("#kpi-intent").textContent=metrics.intent;document.querySelector("#kpi-intent-note").textContent=metrics.intentNote;document.querySelector("#kpi-risk").textContent=metrics.risk;document.querySelector("#kpi-risk-note").textContent=isSummaryImport()?"源表未提供风险量级":`阈值 ${state.config.riskThreshold.toLocaleString()}`;
 renderDashboard(a);renderSocialTrends();renderData();renderCognition(a);renderVertical();renderVideos();renderActions(a);renderKnowhow(a);renderFounderDistill();renderBloggerSkill();renderStrategyKb();renderLearning(a);renderArchitecture();renderWorkspace();renderMmnEval();renderConfig();
}

function socialMetric(value){const number=nullableNumber(value);return number===null?"—":number.toLocaleString("zh-CN",{maximumFractionDigits:1})}
function socialPercent(value){const number=nullableNumber(value);return number===null?"—":`${number.toLocaleString("zh-CN",{maximumFractionDigits:1})}%`}
function socialPlatformBadge(platform,label){const icon=platform==="douyin"?"♪":platform==="xiaohongshu"?"RED":"◉";return `<span class="social-platform-badge ${escapeAttr(platform)}"><i>${icon}</i>${escapeHtml(label||platform)}</span>`}
const socialTrendStages=[{id:"collecting",label:"正在采集"},{id:"validating",label:"正在三路独立审阅"},{id:"delivering",label:"等待交付"},{id:"success",label:"交付成功"}];
function renderSocialTrendProgress(){
 const el=document.querySelector("#social-trend-status");if(!el)return;
 if(socialTrendState.stage==="idle"){el.hidden=true;el.innerHTML="";return}
 el.hidden=false;const active=Math.max(0,socialTrendStages.findIndex(x=>x.id===socialTrendState.stage));
 const elapsed=socialTrendState.startedAt?Math.max(0,Math.floor((Date.now()-socialTrendState.startedAt)/1000)):0,progress=socialTrendState.stage==="success"?100:Math.max(1,Math.min(99,Math.round(socialTrendState.progress||0)));
 el.innerHTML=`<div class="social-progress-summary"><div><b>${socialTrendState.stage==="success"?"分析完成":socialTrendStages[active]?.label||"处理中"}</b><span>${socialTrendState.stage==="success"?"结果已交付，可查看下方看板":`任务持续运行中 · 已用时 ${elapsed} 秒`}</span></div><strong>${progress}%</strong></div><ol>${socialTrendStages.map((x,i)=>`<li class="${i<active||socialTrendState.stage==="success"?"done":i===active?"active":"pending"}" ${i===active?'aria-current="step"':""}><i>${i<active||socialTrendState.stage==="success"?"✓":i+1}</i><span>${x.label}</span></li>`).join("")}</ol><div class="social-progress-track" role="progressbar" aria-label="社媒趋势分析进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}"><i style="width:${progress}%"></i></div>`;
}
function bindSocialTrendSegments(){
 const platformButtons=[...document.querySelectorAll("[data-social-platform]")],checks=[...document.querySelectorAll('[name="social-platform"]')];
 platformButtons.forEach(button=>button.onclick=()=>{const value=button.dataset.socialPlatform;if(value==="all"){const turnOn=!checks.every(x=>x.checked);checks.forEach(x=>x.checked=turnOn)}else{const input=checks.find(x=>x.value===value);if(input)input.checked=!input.checked;if(!checks.some(x=>x.checked))input.checked=true}platformButtons.forEach(x=>x.classList.toggle("active",x.dataset.socialPlatform==="all"?checks.every(c=>c.checked):checks.find(c=>c.value===x.dataset.socialPlatform)?.checked))});
 document.querySelectorAll("[data-social-time]").forEach(button=>button.onclick=()=>{document.querySelectorAll("[data-social-time]").forEach(x=>x.classList.toggle("active",x===button));document.querySelector("#social-trend-time").value=button.dataset.socialTime;document.querySelector("#social-custom-dates").hidden=button.dataset.socialTime!=="custom"});
}
function bindSocialResultModels(){
 document.querySelectorAll("[data-social-result-model]").forEach(button=>button.onclick=()=>{const model=button.dataset.socialResultModel,own=model===socialTrendState.result?.keyword;if(own)return;socialTrendState.visibleModels=socialTrendState.visibleModels.includes(model)?socialTrendState.visibleModels.filter(x=>x!==model):[...socialTrendState.visibleModels,model];renderSocialTrends()});
}
function bindSocialEvidenceFilters(){
 document.querySelectorAll("[data-social-evidence-platform]").forEach(button=>button.onclick=()=>{socialTrendState.evidencePlatform=button.dataset.socialEvidencePlatform;renderSocialTrends()});
 document.querySelectorAll("[data-social-evidence-scope]").forEach(button=>button.onclick=()=>{socialTrendState.evidenceScope=button.dataset.socialEvidenceScope;renderSocialTrends()});
}
function socialTrendRequestWindow(){
 const timeRange=document.querySelector("#social-trend-time")?.value||"30d",startDate=document.querySelector("#social-start-date")?.value||"",endDate=document.querySelector("#social-end-date")?.value||"";
 if(timeRange!=="custom")return{timeRange,startDate:"",endDate:""};
 if(!startDate||!endDate)throw new Error("请选择自定义开始和结束日期");
 if(startDate>endDate)throw new Error("结束日期不能早于开始日期");
 return{timeRange,startDate,endDate};
}
function socialTrendUiStage(job){
 if(job?.status==="completed")return"success";
 if(job?.stage==="validation")return"validating";
 if(["storage","comparison"].includes(job?.stage))return"delivering";
 return"collecting";
}
async function waitForSocialTrendJob(jobId,runToken,initialJob=null){
 const deadline=Date.now()+15*60*1000;
 let job=initialJob;
 while(Date.now()<deadline){
  if(runToken!==socialTrendState.runToken)return null;
  if(!job)job=(await api(`/api/social-trends/jobs/${encodeURIComponent(jobId)}`)).job;
  if(!job)throw new Error("采集任务状态不可用，请重新发起分析");
  socialTrendState.stage=socialTrendUiStage(job);socialTrendState.progress=Number(job.progress||0);renderSocialTrendProgress();
  if(job.status==="completed")return job.result;
  if(job.status==="failed")throw new Error(job.error||job.message||"社媒采集任务失败");
  await opportunityPause(700);
  job=null;
 }
 throw new Error("采集分析超过15分钟，请检查数据源后重试");
}
function socialVehicleIdentityKey(value){
 return String(value||"").normalize("NFKC").replace(/\s+/g,"").toLocaleLowerCase();
}
function sanitizeSocialCompetitors(own,competitors,limit=3){
 const ownKey=socialVehicleIdentityKey(own),seen=new Set(),sanitized=[];
 for(const value of competitors||[]){const label=String(value||"").normalize("NFKC").trim().replace(/\s+/g," "),identity=socialVehicleIdentityKey(label);if(!identity||identity===ownKey||seen.has(identity))continue;seen.add(identity);sanitized.push(label);if(sanitized.length>=limit)break}
 return sanitized;
}
function socialCompetitorCatalog(models,own,selected){
 const identity=value=>String(value||"").normalize("NFKC").replace(/\s+/g,"").toLocaleLowerCase(),excluded=new Set([own,...selected].filter(Boolean).map(identity));
 return brandModelGroups(models.filter(model=>model&&!excluded.has(identity(model)))).map(group=>({brand:group.brand,models:group.models.map(model=>({value:model,label:modelNameUnderBrand(group.brand,model)}))}));
}
function renderSocialCompetitorPicker(){
 const brandSelect=document.querySelector("#social-trend-competitor-brand"),modelSelect=document.querySelector("#social-trend-competitor-add"),chips=document.querySelector("#social-trend-competitors");if(!brandSelect||!modelSelect||!chips)return;
 const keywordInput=document.querySelector("#social-trend-keyword"),own=keywordInput?.value.trim()||state.config.model||"",previousBrand=brandSelect.value;socialTrendState.competitors=sanitizeSocialCompetitors(own,socialTrendState.competitors);
 const groups=socialCompetitorCatalog(modelOptions(),own,socialTrendState.competitors),atLimit=socialTrendState.competitors.length>=3;
 const activeBrand=groups.some(group=>group.brand===previousBrand)?previousBrand:"",activeGroup=groups.find(group=>group.brand===activeBrand);
 brandSelect.innerHTML=`<option value="">${atLimit?"已选满 3 台竞品":"选择品牌"}</option>${groups.map(group=>`<option value="${escapeAttr(group.brand)}" ${group.brand===activeBrand?"selected":""}>${escapeHtml(group.brand)}</option>`).join("")}`;brandSelect.disabled=atLimit;
 modelSelect.innerHTML=`<option value="">${atLimit?"已选满 3 台竞品":activeBrand?"选择车型":"请先选择品牌"}</option>${(activeGroup?.models||[]).map(model=>`<option value="${escapeAttr(model.value)}">${escapeHtml(model.label)}</option>`).join("")}`;modelSelect.disabled=atLimit||!activeBrand;
 chips.innerHTML=socialTrendState.competitors.map(x=>`<button type="button" data-social-competitor-remove="${escapeAttr(x)}" aria-label="移除竞品 ${escapeAttr(x)}"><span>${escapeHtml(x)}</span><i>×</i></button>`).join("")||'<small>从 MMN 品牌车型库添加对比车型</small>';
 brandSelect.onchange=()=>renderSocialCompetitorPicker();
 if(keywordInput)keywordInput.oninput=()=>{socialTrendState.competitors=sanitizeSocialCompetitors(keywordInput.value,socialTrendState.competitors);renderSocialCompetitorPicker()};
 modelSelect.onchange=()=>{const value=modelSelect.value;if(value&&socialTrendState.competitors.length<3)socialTrendState.competitors=sanitizeSocialCompetitors(own,[...socialTrendState.competitors,value]);renderSocialCompetitorPicker()};
 chips.querySelectorAll("[data-social-competitor-remove]").forEach(button=>button.onclick=()=>{const removeKey=socialVehicleIdentityKey(button.dataset.socialCompetitorRemove);socialTrendState.competitors=socialTrendState.competitors.filter(x=>socialVehicleIdentityKey(x)!==removeKey);renderSocialCompetitorPicker()});
}
function socialPlatformSampleStatus(model,platform,point){
 if(Number(point?.contentCount||0)>0)return null;
 const collection=model?.collection||{},warning=(collection.warnings||[]).find(item=>item.platform===platform);
 if(warning)return{kind:"error",label:"采集异常",detail:"本轮接口未返回可用结果"};
 const rejected=collection.admission?.rejectedByPlatform?.[platform]||{},rejectedCount=Object.values(rejected).reduce((sum,value)=>sum+Number(value||0),0);
 if(rejectedCount){const labels={commercial_vehicle_entity:"非乘用车实体",model_not_relevant:"车型不相关",publish_time_unverified:"发布时间无法验证",outside_time_range:"超出时间窗",below_like_threshold:"低于热度阈值"},reason=Object.entries(rejected).sort((a,b)=>Number(b[1])-Number(a[1]))[0]?.[0];return{kind:"filtered",label:"无有效样本",detail:`${rejectedCount} 条候选未入池${reason?`：${labels[reason]||reason}`:""}`}}
 const sources=(collection.sources||[]).filter(item=>item.platform===platform),candidateCount=sources.reduce((sum,item)=>sum+Number(item.itemCount||0),0);
 if(sources.length)return candidateCount?{kind:"filtered",label:"无有效样本",detail:`${candidateCount} 条候选未通过当前规则`}:{kind:"empty",label:"未检索到候选",detail:"本轮搜索未返回匹配内容"};
 return{kind:"empty",label:"本轮无有效样本",detail:"历史快照未保留采集详情"};
}
function socialPositiveHeat(items=[]){
 return Math.round(items.filter(item=>item?.sentiment==="positive").reduce((sum,item)=>sum+Number(item?.heat||0),0)*100)/100;
}
function bindSocialRiskPopover(){
 const trigger=document.querySelector(".social-risk-trigger"),popover=trigger?.querySelector(".social-risk-popover");if(!trigger||!popover)return;
 const setOpen=open=>{trigger.classList.toggle("open",open);trigger.setAttribute("aria-expanded",String(open));popover.hidden=!open};
 trigger.onclick=event=>{if(event.target.closest("a"))return;if(event.target.closest("[data-social-risk-close]")){event.stopPropagation();setOpen(false);trigger.focus();return}if(event.target.closest(".social-risk-popover"))return;setOpen(!trigger.classList.contains("open"))};
 trigger.onkeydown=event=>{if(event.target!==trigger&&event.target.closest("a,button"))return;if(event.key==="Enter"||event.key===" "){event.preventDefault();setOpen(!trigger.classList.contains("open"))}if(event.key==="Escape")setOpen(false)};
}
function socialEvidenceProjectId(centerType,subject){return `${centerType}:${activeEdition()}:${String(subject||"未选择").trim()}`}
function socialEvidenceDateWindow(timeRange,startDate="",endDate=""){
 const end=endDate||localIsoDate(),days=Number(String(timeRange||"30d").replace(/\D/g,""))||30,start=startDate||(()=>{const date=new Date(`${end}T12:00:00`);date.setDate(date.getDate()-Math.max(0,days-1));return date.toISOString().slice(0,10)})();
 return{start,end};
}
function socialEvidenceJobPayload({centerType,subject,competitors=[],platforms=["douyin","xiaohongshu","weibo"],timeRange="30d",startDate="",endDate=""}){
 const model=centerType==="social_trend"?subject:"",brand=centerType==="brand_penetration"?subject:(state.config.brand||""),dateWindow=socialEvidenceDateWindow(timeRange,startDate,endDate),windowDays=Math.max(1,Math.round((new Date(`${dateWindow.end}T12:00:00`)-new Date(`${dateWindow.start}T12:00:00`))/86400000)+1),longWindow=windowDays>7;
 const sampling=longWindow?{maxPages:5,pageSize:20,maxCandidatesPerPlatform:100,maxEvidencePerTargetPerPlatform:30,commentDepth:0}:{maxPages:3,pageSize:20,maxCandidatesPerPlatform:60,maxEvidencePerTargetPerPlatform:20,commentDepth:0};
 return{projectId:socialEvidenceProjectId(centerType,subject),centerType,subject:{brand,model,aliases:[]},competitors,platforms,dateWindow,themes:[],scenes:[],issueTerms:[],eventTerms:[],exclusionTerms:[],sampling,budget:{maxRequests:longWindow?100:60,maxEstimatedCost:longWindow?100:60},edition:activeEdition()};
}
function renderSocialEvidencePlan(plan=socialTrendState.queryPlan,mart=socialTrendState.mart){
 const planBox=document.querySelector("#social-evidence-plan"),coverageBox=document.querySelector("#social-evidence-coverage");if(!planBox||!coverageBox)return;
 planBox.hidden=!socialEvidenceCapabilities.enabled;coverageBox.hidden=!socialEvidenceCapabilities.enabled;
 if(!socialEvidenceCapabilities.enabled)return;
 const scope=mart?.queryScope||plan||{},platforms=scope.platforms||mart?.coverage?.platforms?.map(x=>x.platform)||[],window=scope.dateWindow||{};
 planBox.innerHTML=`<div><span>证据链路</span><b>公开社媒证据 V2</b></div><div><span>查询计划</span><b>${plan?escapeHtml(plan.planVersion||"v2.0"):"等待分析"}</b></div><div><span>时间窗口</span><b>${window.start?`${escapeHtml(window.start)} 至 ${escapeHtml(window.end)}`:"运行时确认"}</b></div><div><span>平台范围</span><b>${platforms.length} 个平台</b></div><p>查询计划、预算和准入规则会在外部采集前冻结；供应商信息仅保留在内部运维层。</p>`;
 const coverage=mart?.coverage,missing=coverage?.missingPlatforms||[];
 coverageBox.innerHTML=`<div><span>证据覆盖</span><b>${coverage?`${coverage.contentCount||0} 条公开内容`:"尚未运行"}</b></div><div><span>已覆盖平台</span><b>${coverage?.platforms?.length||0}</b></div><div><span>缺失平台</span><b>${missing.length?missing.map(escapeHtml).join("、"):coverage?"无":"待确认"}</b></div><div><span>证据状态</span><b>${mart?.status==="verified"?"已形成证据集":mart?"证据有限":"等待分析"}</b></div><p>平台原生互动指标按各平台口径保留，不直接相加为市场结论。</p>`;
}
async function loadSocialEvidenceCapabilities(){
 try{const data=await api("/api/social-evidence/capabilities");socialEvidenceCapabilities={...socialEvidenceCapabilities,...data,enabled:Boolean(data.clientEnabled)};renderSocialEvidencePlan();if(document.querySelector("#socialtrends")?.classList.contains("active"))loadLatestSocialTrendSnapshot();if(document.querySelector("#brandpenetration")?.classList.contains("active"))loadBrandPenetrationSnapshot()}
 catch{socialEvidenceCapabilities={enabled:false,workerMode:"off",supportedCenters:[],schemaVersion:""};renderSocialEvidencePlan()}
}
async function waitForSocialEvidenceJob(jobId,isCurrent,onProgress){
 const deadline=Date.now()+15*60*1000;let job=null;
 while(Date.now()<deadline){
  if(typeof isCurrent==="function"&&!isCurrent())return null;
  job=(await api(`/api/social-evidence/jobs/${encodeURIComponent(jobId)}`)).job;if(!job)throw new Error("证据任务状态不可用，请重新发起分析");
  if(onProgress)onProgress(job);
  if(["ready","degraded","manual_required","failed"].includes(job.status))return job;
  await opportunityPause(700);
 }
 throw new Error("采集分析超过15分钟，请检查数据源后重试");
}
async function latestSocialEvidenceMart(projectId,martType){
 const query=new URLSearchParams({projectId,martType,edition:activeEdition()});
 return(await api("/api/social-evidence/marts/latest?"+query.toString())).mart;
}
async function loadLatestSocialTrendEvidenceMart(){
 if(!socialEvidenceCapabilities.enabled)return;const keyword=document.querySelector("#social-trend-keyword")?.value.trim()||state.config.model||"";if(!keyword)return;
 const payload=socialEvidenceJobPayload({centerType:"social_trend",subject:keyword,competitors:socialTrendState.competitors,timeRange:document.querySelector("#social-trend-time")?.value||"7d"});
 try{const mart=await latestSocialEvidenceMart(payload.projectId,"social_trend");if(mart){socialTrendState.mart=mart;socialTrendState.queryPlan=payload;renderSocialTrends()}else renderSocialEvidencePlan(payload,null)}
 catch(_){renderSocialEvidencePlan(payload,null)}
}
function restoreSocialTrendScope(result){
 const filters=result?.snapshot?.filters||{},comparisonCompetitors=(result?.modelComparisons||[]).filter(item=>item.role!=="own").map(item=>item.model),restoredCompetitors=sanitizeSocialCompetitors(result?.keyword,comparisonCompetitors.length?comparisonCompetitors:(filters.competitors||[]));
 socialTrendState.competitors=restoredCompetitors;
 const timeRange=String(filters.timeRange||"");if(timeRange){const input=document.querySelector("#social-trend-time");if(input)input.value=timeRange;document.querySelectorAll("[data-social-time]").forEach(button=>button.classList.toggle("active",button.dataset.socialTime===timeRange));const custom=document.querySelector("#social-custom-dates");if(custom)custom.hidden=timeRange!=="custom"}
 const platforms=Array.isArray(filters.platforms)?filters.platforms.filter(Boolean):[];if(platforms.length){document.querySelectorAll('[name="social-platform"]').forEach(input=>{input.checked=platforms.includes(input.value)});document.querySelectorAll("[data-social-platform]").forEach(button=>button.classList.toggle("active",button.dataset.socialPlatform==="all"?[...document.querySelectorAll('[name="social-platform"]')].every(input=>input.checked):platforms.includes(button.dataset.socialPlatform)))}
}
function cancelSocialTrendRestore(){socialTrendState.restoreKey="";socialTrendState.restoring=false}
async function loadLatestLegacySocialTrendSnapshot(){
 if(socialEvidenceCapabilities.enabled||socialTrendState.loading)return;
 const keyword=document.querySelector("#social-trend-keyword")?.value.trim()||state.config.model||"";if(!keyword)return;
 const restoreKey=`${activeEdition()}::${keyword}`;if(socialTrendState.restoring&&socialTrendState.restoreKey===restoreKey)return;
 socialTrendState.restoring=true;socialTrendState.restoreKey=restoreKey;socialTrendState.error="";renderSocialTrends();
 try{
  const query=new URLSearchParams({keyword,edition:activeEdition(),centerType:"social_trend"}),data=await api(`/api/social-trends/latest?${query.toString()}`);
  if(socialTrendState.restoreKey!==restoreKey)return;
  const result=data.result||null;socialTrendState.result=result;socialTrendState.mart=null;socialTrendState.visibleModels=(result?.modelComparisons||[]).map(item=>item.model).filter(Boolean);
  if(result)restoreSocialTrendScope(result);
 }catch(error){if(socialTrendState.restoreKey===restoreKey)socialTrendState.error=error.message||"最近一次结果读取失败"}
 finally{if(socialTrendState.restoreKey===restoreKey){socialTrendState.restoring=false;renderSocialTrends()}}
}
async function loadLatestSocialTrendSnapshot(){
 return socialEvidenceCapabilities.enabled?loadLatestSocialTrendEvidenceMart():loadLatestLegacySocialTrendSnapshot();
}
function renderSocialTrendEvidenceMart(mart){
 if(!mart||mart.martType!=="social_trend")throw new Error("社媒趋势证据集类型不匹配");
 const box=document.querySelector("#social-trend-dashboard"),quotes=mart.userLanguage||[],occupancy=mart.competitorOccupancy||[],change=mart.changeSignals?.[0]||{},delta=change.delta; if(!box)return;
 box.innerHTML=`<div class="social-kpi-grid"><article><div><span>公开内容证据</span><strong>${mart.coverage?.contentCount||0}</strong><small>${delta===null||delta===undefined?"首次形成可比较基线":`较上周期 ${delta>=0?"+":""}${delta} 条`}</small></div></article><article><div><span>覆盖平台</span><strong>${mart.coverage?.platforms?.length||0}</strong><small>缺失平台保持可见</small></div></article><article><div><span>用户原话</span><strong>${quotes.length}</strong><small>可回到公开来源</small></div></article><article><div><span>竞品占位观察</span><strong>${occupancy.length}</strong><small>仅为同批证据内提及</small></div></article></div><article class="panel"><div class="panel-title"><div><span>变化信号</span><h2>本周期公开讨论证据</h2></div><em>${mart.status==="verified"?"已形成证据集":"证据有限"}</em></div><div class="social-v2-quotes">${quotes.map(x=>`<article class="social-v2-quote"><p>${escapeHtml(x.text)}</p><small>${escapeHtml(x.platform)} · 原生指标 ${Object.keys(x.nativeMetrics||{}).join(" / ")||"未返回"}</small>${x.sourceUrl?`<a class="social-source-link" href="${escapeAttr(x.sourceUrl)}" target="_blank" rel="noopener">查看原文 ↗</a>`:""}</article>`).join("")||'<p class="empty">本轮没有通过时间、链接与相关性准入的公开内容。</p>'}</div></article>`;
 renderSocialEvidencePlan(socialTrendState.queryPlan,mart);
}
function renderSocialTrends(){
 const box=document.querySelector("#social-trend-dashboard"),status=document.querySelector("#social-trend-status");if(!box)return;
 renderSocialCompetitorPicker();
 renderSocialTrendProgress();
 if(socialTrendState.loading||socialTrendState.restoring){box.innerHTML=`<div class="social-dashboard-skeleton" aria-busy="true" aria-label="${socialTrendState.restoring?"正在恢复最近一次社媒趋势快照":"社媒趋势看板生成中"}"><i></i><i></i><i></i><i></i></div>`;return}
 if(socialTrendState.error){status.hidden=false;status.innerHTML=`<p class="social-progress-error">分析未完成：${escapeHtml(socialTrendState.error)}。请重试。</p>`;box.innerHTML="";return}
 if(socialTrendState.mart){renderSocialTrendEvidenceMart(socialTrendState.mart);return}
 const r=socialTrendState.result;if(!r){box.innerHTML='<article class="panel social-empty-state" role="status"><span>SOCIAL TREND SNAPSHOT</span><h2>当前车型尚未形成可用快照</h2><p>点击“开始分析”采集公开平台证据，或通过“导入数据”使用已有材料。未通过时间、链接与相关性准入的内容不会生成结论。</p></article>';return}
 const items=r.items||[],totalHeat=(r.platforms||[]).reduce((sum,x)=>sum+Number(x.heat||0),0),positive=items.filter(x=>x.sentiment==="positive").length,risk=items.filter(x=>x.sentiment==="negative").length,positiveRate=items.length?positive/items.length*100:0;
 const allComparisonModels=(r.modelComparisons||[]).map(x=>x.model),visibleModels=socialTrendState.visibleModels.length?socialTrendState.visibleModels:allComparisonModels,allEvidence=(r.comparisonEvidence||r.contentRanking||[]).filter(x=>visibleModels.includes(x.normalizedModel||r.keyword)),evidenceItems=allEvidence.filter(x=>(socialTrendState.evidencePlatform==="all"||x.platform===socialTrendState.evidencePlatform)&&(socialTrendState.evidenceScope==="all"||(socialTrendState.evidenceScope==="own"?socialVehicleIdentityKey(x.normalizedModel||r.keyword)===socialVehicleIdentityKey(r.keyword):socialVehicleIdentityKey(x.normalizedModel||r.keyword)!==socialVehicleIdentityKey(r.keyword)))),rankings=evidenceItems.map((x,i)=>{const m=x.metrics||{},isOwn=socialVehicleIdentityKey(x.normalizedModel||r.keyword)===socialVehicleIdentityKey(r.keyword);return `<tr><td><b class="social-rank-no">${i+1}</b></td><td><span class="social-model-tag ${isOwn?'own':'competitor'}">${escapeHtml(x.normalizedModel||r.keyword)}${isOwn?'<i>本品</i>':''}</span></td><td>${socialPlatformBadge(x.platform,x.platformLabel)}</td><td><a href="${escapeAttr(x.sourceUrl)}" target="_blank" rel="noopener">${escapeHtml(x.text||"原始内容")}</a><small>${escapeHtml(x.author||"未知作者")} · ${x.matrixContent?"矩阵内容":"自然内容"}</small></td><td><div class="social-raw-metrics"><span>赞 <b>${socialMetric(m.likes)}</b></span><span>评 <b>${socialMetric(m.comments)}</b></span><span>转 <b>${socialMetric(m.shares)}</b></span><span>藏 <b>${socialMetric(m.collects)}</b></span><span>播 <b>${socialMetric(m.views)}</b></span></div></td><td><span class="social-heat-value">♨ ${socialMetric(x.heat)}</span></td><td><span class="sentiment ${x.sentiment}">${x.sentiment==="positive"?"正向":x.sentiment==="negative"?"负向":"中性"}</span></td><td><a class="social-source-link" href="${escapeAttr(x.sourceUrl)}" target="_blank" rel="noopener">查看原文 ↗</a></td></tr>`}).join("");
 const heatBars=(r.contentRanking||[]).slice(0,5).map((x,i)=>`<li><b><i>${i+1}</i>${escapeHtml(x.text||"相关内容")}</b><span><i style="width:${Math.max(8,Math.min(100,x.heat||0))}%"></i></span><em>${socialMetric(x.heat)}</em></li>`).join("")||'<p class="empty">未形成高热度内容</p>';
 const words=(r.hotWords||[]).slice(0,8),wordMax=Math.max(1,...words.map(x=>x.count));const wordBars=words.map(x=>`<li><b>${escapeHtml(x.word)}</b><span><i style="width:${x.count/wordMax*100}%"></i></span><em>${x.count}</em></li>`).join("")||'<p class="empty">尚未形成稳定热词</p>';
 const own=(r.modelHeatRanking||r.ownModelRanking||[]).slice(0,5),ownMax=Math.max(1,...own.map(x=>x.heat));const ownBars=own.map((x,i)=>`<li><b><i>${i+1}</i>${escapeHtml(x.model)}${x.model===r.keyword?'<small class="social-own-mark">本品</small>':''}</b><span><i style="width:${x.heat/ownMax*100}%"></i></span><em>${socialMetric(x.heat)}</em></li>`).join("");
 const competitors=(r.positiveCompetitorsTop5||[]).slice(0,5),ownPositiveHeat=socialPositiveHeat(items),compMax=Math.max(1,ownPositiveHeat,...competitors.map(x=>Number(x.positiveHeat||0)));const ownPositiveBar=`<li class="social-own-benchmark"><b><i>本品</i>${escapeHtml(r.keyword)}<small class="social-own-mark">基准</small></b><span class="own"><i style="width:${ownPositiveHeat/compMax*100}%"></i></span><em>${socialMetric(ownPositiveHeat)}</em></li>`,compBars=competitors.map((x,i)=>`<li><b><i>${i+1}</i>${escapeHtml(x.model)}</b><span class="green"><i style="width:${Number(x.positiveHeat||0)/compMax*100}%"></i></span><em>${socialMetric(x.positiveHeat)}</em></li>`).join("")||'<p class="empty">当前证据不足，未形成竞品正向 Top 5</p>';
 const comparisonDatasets=(r.modelComparisons||[]).filter(x=>visibleModels.includes(x.model)),selectedPlatformKeys=[...new Set(comparisonDatasets.flatMap(x=>(x.platforms||[]).map(p=>p.platform)))],platformLabels=Object.fromEntries(comparisonDatasets.flatMap(x=>(x.platforms||[]).map(p=>[p.platform,p.label])));const shares=selectedPlatformKeys.map(platform=>{const max=Math.max(1,...comparisonDatasets.map(x=>Number((x.platforms||[]).find(p=>p.platform===platform)?.heat||0))),rows=comparisonDatasets.map(model=>{const point=(model.platforms||[]).find(p=>p.platform===platform)||{},status=socialPlatformSampleStatus(model,platform,point),value=status?`<strong class="social-platform-empty-status ${status.kind}" title="${escapeAttr(status.detail)}"><span>${escapeHtml(status.label)}</span><small>${escapeHtml(status.detail)}</small></strong>`:`<strong>${socialMetric(point.heat)} 分 · ${point.contentCount||0} 条</strong>`;return `<span class="social-platform-model-row ${model.role} ${status?"sample-status":""}"><b>${escapeHtml(model.model)}${model.role==='own'?'<i>本品</i>':''}</b><em><i style="width:${Number(point.heat||0)/max*100}%"></i></em>${value}</span>`}).join("");return `<li class="social-platform-group"><header>${socialPlatformBadge(platform,platformLabels[platform])}</header><div>${rows}</div></li>`}).join("");
 const creators=(r.creatorRanking||[]).slice(0,6).map((x,i)=>`<li><b><i>${i+1}</i>${escapeHtml(x.author)}</b><span class="${x.matrixContent?'green':''}"><i style="width:${Math.max(5,Math.min(100,x.heat||0))}%"></i></span><em>${socialMetric(x.heat)}</em></li>`).join("")||'<p class="empty">暂无可识别账号</p>';
 const risks=(r.riskTopics||[]).slice(0,6).map(x=>`<li><b>${escapeHtml(x.topic)}</b><span class="red"><i style="width:${Math.max(5,Math.min(100,x.heat||0))}%"></i></span><em>${x.contentCount}</em></li>`).join("")||'<p class="empty">未形成集中风险主题</p>';
 const clusters=(r.contentClusters||[]).slice(0,8).map(x=>`<span><b>${escapeHtml(x.topic)}</b><small>${x.contentCount} 条 · 热度 ${socialMetric(x.heat)}</small></span>`).join("")||'<p class="empty">证据不足，暂未形成内容聚类</p>';
 const comments=r.commentInsights||{},commentTotal=Number(comments.total||0),commentPositive=Number(comments.positive||0),commentNegative=Number(comments.negative||0),riskItems=items.filter(x=>x.sentiment==="negative").sort((a,b)=>Number(b.heat||0)-Number(a.heat||0)),riskPopover=riskItems.length?`<div class="social-risk-popover" role="dialog" aria-label="本品风险内容明细" hidden><header><div><span>风险内容明细</span><b>${riskItems.length} 条负向内容</b></div><button type="button" data-social-risk-close aria-label="关闭风险内容明细">×</button></header><ol>${riskItems.map(item=>`<li><div><b>${escapeHtml(item.text||"未命名内容")}</b><small>${escapeHtml(item.platformLabel||item.platform||"未知平台")} · ${escapeHtml(item.author||"未知作者")} · 热度 ${socialMetric(item.heat)}</small></div>${item.sourceUrl?`<a href="${escapeAttr(item.sourceUrl)}" target="_blank" rel="noopener">查看原文 ↗</a>`:""}</li>`).join("")}</ol></div>`:"";
 const history=r.historyComparison||{},delta=history.delta||{},deltaLabel=history.available?`较上次：热度 ${Number(delta.heat||0)>=0?"+":""}${socialMetric(delta.heat)} · 内容 ${Number(delta.contentCount||0)>=0?"+":""}${delta.contentCount||0}`:"首次形成历史基线";
 const timeline=(r.timeline||[]).slice(-12),timelineMax=Math.max(1,...timeline.map(x=>x.heat)),undated=r.timelineUndated||{};const trendBars=timeline.map(x=>`<span class="social-trend-point" tabindex="0" style="height:${Math.max(8,x.heat/timelineMax*100)}%"><i></i><b>${escapeHtml(x.date)}<small>总热度 ${socialMetric(x.heat)} 分 · 总内容 ${x.contentCount||0} 条</small>${(x.platforms||[]).map(p=>`<small>${escapeHtml(p.label)}：${p.contentCount||0} 条 · ${socialMetric(p.heat)} 分</small>`).join("")}</b></span>`).join("")||'<small>缺少可靠发布时间，暂不生成日期走势</small>';
 const sparkPoints=(timeline.length?timeline:[{heat:0},{heat:0}]).map((x,i,a)=>`${i*(88/Math.max(1,a.length-1))+4},${34-Number(x.heat||0)/timelineMax*26}`).join(" "),spark=`<svg class="social-spark" viewBox="0 0 96 40" aria-hidden="true"><polyline points="${sparkPoints}"/></svg>`;
 const hotLists=(r.hotLists||[]).map(x=>`<section><b>${escapeHtml(x.platformLabel)}实时热榜</b><ol>${(x.items||[]).slice(0,5).map((v,i)=>`<li><i>${i+1}</i><span>${escapeHtml(v)}</span></li>`).join("")||'<li>暂无匹配热榜</li>'}</ol></section>`).join("")||'<p class="empty">所选平台暂无可用实时热榜</p>';
 const comparisons=(r.modelComparisons||[]).filter(x=>visibleModels.includes(x.model)),comparisonMax=Math.max(1,...comparisons.map(x=>x.heat));const comparisonRows=comparisons.map(x=>{const complete=x.collectionStatus?.status==="complete",sentimentRate=x.analysisCoverage?.sentiment?.rate;return `<article class="social-model-comparison ${x.role}"><header><div><b>${escapeHtml(x.model)}</b>${x.role==="own"?'<span>本品·基准</span>':'<span>竞品</span>'}</div><strong>${socialMetric(x.heat)}<small> 热度分</small></strong></header><div class="social-compare-track"><i style="width:${x.heat/comparisonMax*100}%"></i></div><dl><div><dt>相关内容量</dt><dd>${socialMetric(x.contentCount)}</dd></div><div><dt>正文正向率</dt><dd>${socialPercent(x.positiveRate)}</dd></div><div><dt>风险内容</dt><dd>${socialMetric(x.riskCount)}</dd></div><div><dt>数据完整性</dt><dd class="${complete?'':'limited'}">${complete?'已采尽':'部分采集'}${sentimentRate!==undefined?` · ${socialMetric(sentimentRate)}%已分析`:''}</dd></div></dl><div class="social-platform-matrix">${(x.platforms||[]).map(p=>`<span>${socialPlatformBadge(p.platform,p.label)}<b>${socialMetric(p.heat)} 分</b></span>`).join("")}</div><p>${(x.hotWords||[]).slice(0,5).map(v=>`<i>${escapeHtml(v.word)}</i>`).join("")||"尚未形成稳定热词"}</p></article>`}).join("");
 const resultModelControls=(r.modelComparisons||[]).map(x=>`<button type="button" data-social-result-model="${escapeAttr(x.model)}" class="${visibleModels.includes(x.model)?'active':''} ${x.role}">${x.role==='own'?'✓ ':visibleModels.includes(x.model)?'✓ ':''}${escapeHtml(x.model)}<small>${x.role==='own'?'本品固定':'竞品'}</small></button>`).join("");
 const collectionComplete=r.collectionStatus?.status==="complete",sentimentCoverage=r.analysisCoverage?.sentiment||{},riskCoverage=r.analysisCoverage?.risk||{},insight=r.unifiedInsight||{},insightStatus={aligned:"三路审阅一致",conditional:"条件性结论",disagreement:"存在分歧",insufficient_evidence:"证据不足",pending_configuration:"等待配置"}[insight.validationStatus]||({published:"三路审阅一致",conditional:"条件性结论",withheld:"暂缓发布"}[insight.publicationStatus]||"等待统一结论"),riskHint=risk?"发现负向内容，建议优先下钻":collectionComplete&&riskCoverage.rate===100?"采集完整且风险分析已覆盖，未发现负向内容":"暂未发现；当前采集或风险分析不完整";
 const insightMarkup=`<article class="panel social-unified-insight ${escapeAttr(insight.publicationStatus||'withheld')}"><div class="panel-title"><div><span>${insight.scopeType==='own_period'?'本品周期洞察':'本品 × 竞品统一对比洞察'}</span><h2>${escapeHtml(insight.headline||"证据不足，暂不发布统一结论")}</h2></div><em>${escapeHtml(insightStatus)}</em></div><div class="social-unified-meta"><span>范围：${(insight.models||[]).map(escapeHtml).join(" × ")||escapeHtml(r.keyword)}</span><span>证据：${socialMetric((insight.evidenceIds||[]).length)} 条通过一致性复核</span><span>数据：${collectionComplete?'已采尽':'部分采集'}</span></div>${(insight.limitations||[]).length?`<ul>${insight.limitations.map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul>`:""}<p>统一结论绑定当前时间窗、平台和车型范围；切换筛选条件需重新分析。</p></article>`;
 box.innerHTML=`<div class="social-kpi-grid"><article><i class="social-kpi-icon heat">♨</i><div><span>本品综合热度</span><strong>${socialMetric(totalHeat)}</strong><small>${escapeHtml(deltaLabel)}</small></div>${spark}</article><article><i class="social-kpi-icon content">▤</i><div><span>本品相关内容</span><strong>${items.length}</strong><small>跨平台去重 · ${r.statusHint}</small></div>${spark}</article><article class="positive"><i class="social-kpi-icon positive">👍</i><div><span>本品正向率</span><strong>${positiveRate.toFixed(0)}%</strong><small>${positive} 条正向 · 评论 ${commentPositive} 条</small></div>${spark}</article><article class="risk"><i class="social-kpi-icon risk">!</i><div><span>本品风险内容</span><strong>${risk}</strong><small>${commentNegative?`评论风险 ${commentNegative} 条`:risk?"建议优先下钻":"当前风险可控"}</small></div>${spark}</article></div>${comparisons.length>1?`<article class="panel social-comparison-board"><div class="panel-title"><div><span>本品 × 竞品对比</span><h2>已选车型全部进入分析结果</h2></div><em>${comparisons.length} 台车型 · 同口径</em></div><div class="social-model-comparisons">${comparisonRows}</div></article>`:""}<div class="social-board-grid"><article class="panel"><div class="panel-title"><div><span>内容热度排行榜</span><h2>按互动量综合排序</h2></div><em>Top 5</em></div><ol class="social-bar-list heat">${heatBars}</ol></article><article class="panel"><div class="panel-title"><div><span>本品相关热词榜</span><h2>${escapeHtml(r.keyword)} 高频关联词</h2></div><em>Top 8</em></div><ol class="social-bar-list words">${wordBars}</ol></article><article class="panel"><div class="panel-title"><div><span>车型综合热度排行</span><h2>本品与已选竞品同口径对比</h2></div><em>${comparisons.length||1} 台车型</em></div><ol class="social-bar-list own">${ownBars}</ol></article><article class="panel"><div class="panel-title"><div><span>竞品正向热度 Top 5</span><h2>证据一致的正向内容</h2></div><em>Top 5</em></div><ol class="social-bar-list competitors">${compBars}</ol></article></div><div class="social-insight-grid"><article class="panel"><div class="panel-title"><div><span>本品平台声量结构</span><h2>热度份额与跨平台分布</h2></div><em>三平台</em></div><ol class="social-bar-list shares">${shares}</ol></article><article class="panel"><div class="panel-title"><div><span>账号与矩阵识别</span><h2>本品创作者综合热度</h2></div><em>${r.matrixSummary?.creatorCount||0} 个矩阵账号</em></div><ol class="social-bar-list creators">${creators}</ol></article><article class="panel"><div class="panel-title"><div><span>本品风险议题</span><h2>负向内容聚集主题</h2></div><em>${risk} 条风险证据</em></div><ol class="social-bar-list risks">${risks}</ol></article><article class="panel social-trend-history"><div class="panel-title"><div><span>本品热度走势</span><h2>${escapeHtml(deltaLabel)}</h2></div><em>${timeline.length} 个时间点</em></div><div class="social-mini-trend">${trendBars}</div><div class="social-comment-split"><span>评论样本 <b>${commentTotal}</b></span><span class="positive">正向 <b>${commentPositive}</b></span><span class="negative">负向 <b>${commentNegative}</b></span></div></article></div><div class="social-context-grid"><article class="panel"><div class="panel-title"><div><span>本品内容主题聚类</span><h2>高频主题 × 热度 × 情感</h2></div></div><div class="social-clusters">${clusters}</div></article><article class="panel"><div class="panel-title"><div><span>平台实时热榜</span><h2>发现车型内容之外的趋势机会</h2></div></div><div class="social-hot-lists">${hotLists}</div></article></div><article class="panel social-evidence-board"><div class="panel-title"><div><span>本品与竞品内容证据</span><h2>原始内容下钻</h2><small>排序依据：综合热度 = log10(1 + 点赞 + 2×评论 + 3×分享 + 2.5×收藏 + 0.08×播放) × 20，单条封顶 100</small></div><em>${escapeHtml(r.confidenceLabel||"")}置信度 · ${evidenceItems.length} 条</em></div><div class="table-wrap"><table class="social-ranking"><thead><tr><th>排名</th><th>车型</th><th>平台</th><th>内容标题</th><th>原始互动指标</th><th>综合热度</th><th>情感</th><th>操作</th></tr></thead><tbody>${rankings||'<tr><td colspan="8">未形成高热度内容</td></tr>'}</tbody></table></div></article>`;
 const kpiCards=[...box.querySelectorAll(".social-kpi-grid article")];
 if(kpiCards[0]){kpiCards[0].title="单条热度=log10(1+点赞+2×评论+3×分享+2.5×收藏+0.08×播放)×20，单条封顶100";kpiCards[0].querySelector("small").textContent="相关内容单条热度求和 · 无绝对高低线，仅同口径比较"}
 if(kpiCards[1]){kpiCards[1].querySelector("span").textContent="本品相关内容量";kpiCards[1].querySelector("small").textContent=`所选时间窗可访问公开结果 · ${collectionComplete?'已采尽':'部分采集'}`}
 if(kpiCards[2]){kpiCards[2].querySelector("span").textContent="本品正文正向率";kpiCards[2].querySelector("small").textContent=`${sentimentCoverage.analyzed||0}/${sentimentCoverage.total||items.length} 条正文已分析 · 评论正向 ${commentPositive} 条`}
 const riskCard=box.querySelector(".social-kpi-grid article.risk");if(riskCard){riskCard.querySelector("small").textContent=riskHint;if(riskItems.length){riskCard.classList.add("social-risk-trigger");riskCard.setAttribute("role","button");riskCard.setAttribute("tabindex","0");riskCard.setAttribute("aria-haspopup","dialog");riskCard.setAttribute("aria-expanded","false");riskCard.querySelector("small").textContent="点击查看具体内容";riskCard.insertAdjacentHTML("beforeend",riskPopover)}}
 box.querySelector(".social-kpi-grid")?.insertAdjacentHTML("afterend",insightMarkup);
 const evidenceStatus=box.querySelector(".social-evidence-board .panel-title>em"),heatMethod=box.querySelector(".social-evidence-board .panel-title small");if(evidenceStatus)evidenceStatus.textContent=`${collectionComplete?'已采尽':'部分采集'} · 正文已分析 ${socialMetric(sentimentCoverage.rate||0)}% · ${evidenceItems.length} 条热门证据`;if(heatMethod)heatMethod.textContent+="；不存在跨车型、跨周期通用的高/低分阈值。";
 box.querySelector(".social-bar-list.competitors")?.insertAdjacentHTML("afterbegin",ownPositiveBar);
 box.insertAdjacentHTML("afterbegin",`<article class="panel social-result-model-filter"><div><span>本次分析车型</span><b>选择需要在对比图与证据表中显示的车型</b><small>Benchmark：本品为固定基准；所有车型使用相同时间窗、平台范围与热度公式</small></div><section>${resultModelControls}</section></article>`);
 if(r.admission){const imported=r.sourceMode==="social_assistant_import",reasonLabels={platform_not_selected:"平台未选择",model_not_relevant:"车型不相关",publish_time_unverified:"发布时间无法验证",outside_time_range:"超出所选时间",below_like_threshold:"低于点赞阈值"},reasonText=Object.entries(r.admission.rejectedReasons||{}).filter(([,count])=>Number(count)>0).map(([reason,count])=>`${reasonLabels[reason]||reason} ${count} 条`).join(" · ");box.querySelector(".social-result-model-filter")?.insertAdjacentHTML("afterend",`<div class="social-import-summary"><div><span>${imported?"导入记录":"抓取候选"}</span><b>${r.admission.inputCount}</b></div><div><span>有效入池</span><b>${r.admission.admittedCount}</b></div><div><span>未入池</span><b>${r.admission.rejectedCount}</b></div><div><span>重复内容</span><b>${r.admission.duplicateCount}</b></div>${reasonText?`<p><b>${imported?"导入":"抓取"}筛选说明：</b>${escapeHtml(reasonText)}</p>`:""}</div>`)}
 if(comparisons.length===1){box.querySelector(".social-unified-insight")?.insertAdjacentHTML("afterend",`<article class="panel social-comparison-board"><div class="panel-title"><div><span>当前显示车型</span><h2>本品 Benchmark</h2></div><em>1 台车型 · 同口径</em></div><div class="social-model-comparisons">${comparisonRows}</div></article>`)}
 const positivePanel=box.querySelector(".social-bar-list.competitors")?.closest("article");if(positivePanel){positivePanel.querySelector(".panel-title span").textContent="本品与竞品正向内容热度";positivePanel.querySelector(".panel-title h2").textContent="正向内容的综合热度之和（热度分）";positivePanel.querySelector(".panel-title em").textContent=`${r.keyword} 为 Benchmark`}
 const platformPanel=box.querySelector(".social-bar-list.shares")?.closest("article");if(platformPanel){platformPanel.querySelector(".panel-title span").textContent="所选车型平台热度";platformPanel.querySelector(".panel-title h2").textContent="本品与竞品分平台热度及内容量";platformPanel.querySelector(".panel-title em").textContent=`${selectedPlatformKeys.length} 个已选平台`}
 const trendPanel=box.querySelector(".social-trend-history");if(trendPanel){trendPanel.querySelector(".social-comment-split")?.insertAdjacentHTML("beforebegin",`<p class="social-trend-definition">维度：真实发布日期 × 当日内容综合热度；柱高为当日热度分之和。${undated.contentCount?`另有 ${undated.contentCount} 条内容缺少可靠发布时间，未计入走势。`:""}</p>`)}
 const evidencePanel=box.querySelector(".social-evidence-board"),evidenceHead=evidencePanel?.querySelector(".panel-title");if(evidenceHead){const platformButtons=`<button type="button" data-social-evidence-platform="all" class="${socialTrendState.evidencePlatform==='all'?'active':''}">全部平台</button>${selectedPlatformKeys.map(p=>`<button type="button" data-social-evidence-platform="${escapeAttr(p)}" class="${socialTrendState.evidencePlatform===p?'active':''}">${escapeHtml(platformLabels[p]||p)}</button>`).join("")}`,scopeButtons=[['all','全部车型'],['own','本品'],['competitor','竞品']].map(([value,label])=>`<button type="button" data-social-evidence-scope="${value}" class="${socialTrendState.evidenceScope===value?'active':''}">${label}</button>`).join("");evidenceHead.insertAdjacentHTML("beforeend",`<div class="social-evidence-filters"><section aria-label="排行榜平台筛选">${platformButtons}</section><section aria-label="排行榜车型筛选">${scopeButtons}</section></div>`)}
 bindSocialResultModels();
 bindSocialEvidenceFilters();
 bindSocialRiskPopover();
}
async function runSocialTrendAnalysis(event){
 event.preventDefault();cancelSocialTrendRestore();const keyword=document.querySelector("#social-trend-keyword").value.trim(),platforms=[...document.querySelectorAll('[name="social-platform"]:checked')].map(x=>x.value);socialTrendState.competitors=sanitizeSocialCompetitors(keyword,socialTrendState.competitors);socialTrendState.evidenceScope="all";
 const runButton=document.querySelector("#social-trend-run"),importButton=document.querySelector("#social-trend-import");if(!keyword||!platforms.length)return;if(runButton){runButton.disabled=true;runButton.textContent="分析进行中…"}if(importButton)importButton.disabled=true;
 clearTimeout(socialTrendState.stageTimer);clearInterval(socialTrendState.progressTimer);const runToken=socialTrendState.runToken+1;socialTrendState.runToken=runToken;socialTrendState.loading=true;socialTrendState.result=null;socialTrendState.mart=null;socialTrendState.error="";socialTrendState.stage="collecting";socialTrendState.progress=1;socialTrendState.startedAt=Date.now();renderSocialTrends();
 try{
  const window=socialTrendRequestWindow();
  if(socialEvidenceCapabilities.enabled){
   const payload=socialEvidenceJobPayload({centerType:"social_trend",subject:keyword,competitors:socialTrendState.competitors,platforms,timeRange:window.timeRange,startDate:window.startDate,endDate:window.endDate});
   const preview=await api("/api/social-evidence/query-plans/preview",{method:"POST",body:JSON.stringify(payload)});socialTrendState.queryPlan=preview.plan;renderSocialEvidencePlan();
   const data=await api("/api/social-evidence/jobs",{method:"POST",body:JSON.stringify(payload)}),job=data.job;if(!job?.jobId)throw new Error("证据任务未成功创建");socialTrendState.jobId=job.jobId;
   const finished=await waitForSocialEvidenceJob(job.jobId,()=>runToken===socialTrendState.runToken,current=>{socialTrendState.progress=Number(current.progress||1);socialTrendState.stage=current.status==="ready"?"success":"collecting";renderSocialTrendProgress()});
   if(!finished||runToken!==socialTrendState.runToken)return;if(finished.status!=="ready")throw new Error(finished.message||"本轮公开证据不足");
   const mart=await latestSocialEvidenceMart(payload.projectId,"social_trend");if(!mart)throw new Error("证据任务完成但未形成社媒趋势证据集");socialTrendState.mart=mart;socialTrendState.stage="success";socialTrendState.progress=100;
  }else{
   const data=await api("/api/social-trends/jobs",{method:"POST",body:JSON.stringify({keyword,platforms,competitors:socialTrendState.competitors,thresholds:socialThresholdValues(),timeRange:window.timeRange,startDate:window.startDate,endDate:window.endDate,edition:activeEdition(),pages:0,count:20})}),job=data.job;if(!job?.jobId)throw new Error("采集任务未成功创建");socialTrendState.jobId=job.jobId;socialTrendState.stage=socialTrendUiStage(job);socialTrendState.progress=Number(job.progress||1);renderSocialTrendProgress();const result=await waitForSocialTrendJob(job.jobId,runToken,job);if(!result||runToken!==socialTrendState.runToken)return;socialTrendState.result=result;socialTrendState.visibleModels=(result.modelComparisons||[]).map(x=>x.model);socialTrendState.stage="success";socialTrendState.progress=100;
  }
 }
 catch(err){if(runToken===socialTrendState.runToken){socialTrendState.error=err.message;socialTrendState.stage="error"}}finally{if(runToken===socialTrendState.runToken){clearTimeout(socialTrendState.stageTimer);clearInterval(socialTrendState.progressTimer);socialTrendState.loading=false;socialTrendState.jobId="";if(runButton){runButton.disabled=false;runButton.textContent="重新分析"}if(importButton)importButton.disabled=false;renderSocialTrends()}}
}
function socialThresholdValue(selector,fallback){const raw=document.querySelector(selector)?.value;const value=nullableNumber(raw);return value===null?fallback:value}
function socialThresholdValues(){return {douyin:socialThresholdValue("#social-threshold-douyin",8000),xiaohongshu:socialThresholdValue("#social-threshold-xiaohongshu",500),weibo:socialThresholdValue("#social-threshold-weibo",500)}}
async function importSocialTrendFile(file){
 cancelSocialTrendRestore();const keyword=document.querySelector("#social-trend-keyword")?.value.trim(),platforms=[...document.querySelectorAll('[name="social-platform"]:checked')].map(x=>x.value),thresholds=socialThresholdValues();if(!keyword)throw new Error("请先填写车型关键词");
 const runToken=socialTrendState.runToken+1,runButton=document.querySelector("#social-trend-run"),importButton=document.querySelector("#social-trend-import");socialTrendState.runToken=runToken;clearTimeout(socialTrendState.stageTimer);clearInterval(socialTrendState.progressTimer);if(runButton)runButton.disabled=true;if(importButton)importButton.disabled=true;socialTrendState.loading=true;socialTrendState.error="";socialTrendState.stage="collecting";socialTrendState.progress=15;socialTrendState.startedAt=Date.now();renderSocialTrends();
 try{const window=socialTrendRequestWindow(),query=new URLSearchParams({filename:file.name,keyword,platforms:platforms.join(","),timeRange:window.timeRange,startDate:window.startDate,endDate:window.endDate,edition:activeEdition(),douyinMinLikes:thresholds.douyin,xiaohongshuMinLikes:thresholds.xiaohongshu,weiboMinLikes:thresholds.weibo}),data=await api(`/api/social-trends/import?${query}`,{method:"POST",headers:{"Content-Type":"application/octet-stream"},body:file});if(runToken!==socialTrendState.runToken)return;data.result.sourceMode=data.result.sourceMode||"social_assistant_import";socialTrendState.result=data.result;socialTrendState.visibleModels=(data.result.modelComparisons||[]).map(x=>x.model);socialTrendState.stage="success";socialTrendState.progress=100}
 catch(error){if(runToken===socialTrendState.runToken){socialTrendState.error=error.message;socialTrendState.stage="error"}}finally{if(runToken===socialTrendState.runToken){socialTrendState.loading=false;if(runButton)runButton.disabled=false;if(importButton)importButton.disabled=false;renderSocialTrends()}}
}
function renderEditionChrome(){
 const cfg=currentEdition();
 document.body.dataset.edition=edition;
 document.body.dataset.domesticMode=edition==="china"&&managementDashboardVisible?"management":"standard";
 document.title=cfg.title;
 document.querySelectorAll("[data-edition]").forEach(b=>b.classList.toggle("active",b.dataset.edition===edition));
 const managementButton=document.querySelector("button[data-domestic-mode=\"management\"]");
 if(managementButton){const active=edition==="china"&&managementDashboardVisible;managementButton.hidden=edition!=="china";managementButton.classList.toggle("active",active);managementButton.setAttribute("aria-pressed",String(active));managementButton.setAttribute("aria-expanded",String(active));const hint=managementButton.querySelector("small");if(hint)hint.textContent=active?"收起集团看板":"打开集团看板"}
 const managementPanel=document.querySelector("#management-dashboard-panel");if(managementPanel)managementPanel.hidden=!(edition==="china"&&managementDashboardVisible);
 const leadPanel=document.querySelector("#lead-dashboard-panel");if(leadPanel)leadPanel.hidden=!(edition==="china"&&managementDashboardVisible&&managementWarningContextReady);
 const eyebrow=document.querySelector("#edition-eyebrow");if(eyebrow)eyebrow.textContent=cfg.eyebrow;
 const sideTitle=document.querySelector("#side-run-title");if(sideTitle)sideTitle.textContent=cfg.sideTitle;
 const sideDesc=document.querySelector("#side-run-desc");if(sideDesc)sideDesc.textContent=cfg.sideDesc;
 const logo=document.querySelector(".brand-logo");if(logo&&logo.getAttribute("src")!==cfg.logo){logo.src=cfg.logo;logo.alt=edition==="china"?"MMN 艾姆恩多模态营销引擎":"MMN Multi-Marketing Network";}
 renderSalesMarquee();
}
function renderSalesMarquee(){
 const wrap=document.querySelector("#sales-marquee"),label=document.querySelector(".sales-marquee-label"),track=document.querySelector("#sales-marquee-track");
 if(!wrap||!track)return;
 label.textContent=edition==="china"?"国内销量快讯":"Global Watch";
 const liveItems=salesMarquee.edition===edition&&salesMarquee.items?.length?salesMarquee.items:null;
 const baseItems=edition==="china"
  ?(liveItems||[{text:"懂车帝销量榜接入中..."}])
  :(liveItems||currentEdition().ticker||[{text:"Global market data sources pending"}]);
 const suffix=edition==="china"?(salesMarquee.status==="live"?"实时页":"接入状态"):(salesMarquee.status==="local"?"Thailand data":"Global sources");
 const texts=baseItems.map(x=>x.text||`${x.label||"销量榜"} ${x.month||""}`).filter(Boolean);
 const repeated=edition==="china"
  ?[...texts, ...texts, `${suffix}：${salesMarquee.note||"等待数据源刷新"}`]
  :[...texts, ...texts, `${suffix}：${salesMarquee.edition===edition&&salesMarquee.note?salesMarquee.note:"Thailand / ASEAN / TikTok / YouTube data pipeline"} `];
 track.innerHTML=repeated.map(t=>`<span>${escapeHtml(t)}</span>`).join("");
}
async function loadSalesMarquee(){
 try{
  const targetEdition=edition;
  const data=await api(targetEdition==="global"?"/api/global-sales-marquee":"/api/sales-marquee");
  salesMarquee={edition:targetEdition,status:data.status||"limited",items:data.items||[],note:data.note||""};
 }catch(e){
  salesMarquee={edition,status:"limited",items:[{text:edition==="global"?"泰国汽车市场数据接入受限：请检查月度更新日志":"懂车帝销量榜接入受限：请稍后刷新或接入正式数据接口"}],note:e.message};
 }
 renderSalesMarquee();
}
function renderAccount(){
 const btn=document.querySelector("#account-button");if(!btn)return;
 btn.textContent=session?`客户空间：${session.org} / ${session.name}${session.role?` · ${session.role==="admin"?"管理员":"试用"}`:""}`:"客户空间：未登录";
 btn.classList.toggle("primary",!!session);
 applyRoleRestrictions();
}
function applyRoleRestrictions(){
 const trial=session?.role==="trial";
 const selectors=[
	  "#add-row",".file-button","#save-row","#sync-project-state","#clear-learning","#clear-video-data","#clear-vertical-data","#clear-strategy-kb",
	  "#import-rag-seed","#import-strategy-kb","#run-founder-crawl","#seed-founder-archive","#scan-blogger-skill","#import-blogger-skill-url","[data-plugin-sync]"
	 ];
 document.querySelectorAll(selectors.join(",")).forEach(el=>{
  el.disabled=trial;
  el.classList.toggle("permission-locked",trial);
  if(trial)el.title="试用账号仅可查看演示和运行策略，不可修改云端数据。";
  else if(el.classList.contains("permission-locked"))el.removeAttribute("title");
 });
}
function renderModelSwitcher(){
 const models=modelOptions(),wrap=document.querySelector("#dash-model");
 if(!wrap)return;
 if(edition==="china"&&managementDashboardVisible){
  wrap.innerHTML=`<span class="dash-model-management-context">销量预警统一控制 · ${escapeHtml(state.config.model)}</span>`;
  return;
 }
 const groups=brandModelGroups(models);
 if(!dashBrandOpen||!groups.some(g=>g.brand===dashBrandOpen))dashBrandOpen=brandForDisplay(state.config.model);
 const activeGroup=groups.find(g=>g.brand===dashBrandOpen)||groups[0]||{brand:"",models:[]};
 const activeModels=activeGroup.models;
 wrap.innerHTML=`<div class="dash-model-selects"><select id="dash-brand-select" aria-label="选择品牌">${groups.map(g=>`<option value="${escapeAttr(g.brand)}" ${g.brand===dashBrandOpen?"selected":""}>${g.brand}</option>`).join("")}</select><select id="dash-model-select" aria-label="选择车型">${activeModels.map(m=>`<option value="${escapeAttr(m)}" ${m===state.config.model?"selected":""}>${m}</option>`).join("")}</select></div>`;
	 const brandSelect=wrap.querySelector("#dash-brand-select"),modelSelect=wrap.querySelector("#dash-model-select");
 brandSelect.onchange=()=>{dashBrandOpen=brandSelect.value;const nextModel=groups.find(group=>group.brand===dashBrandOpen)?.models?.[0];if(nextModel)selectDashboardVehicleContext(nextModel,{source:"dashboard-switcher"});else renderModelSwitcher()};
	 modelSelect.onchange=()=>selectDashboardVehicleContext(modelSelect.value,{source:"dashboard-switcher"});
	}
function syncDashboardModelFromControls(){
 const modelSelect=document.querySelector("#dash-model-select");
 const selected=modelSelect?.value;
 if(selected&&selected!==state.config.model){
  applyModelSelection(selected);
  dashBrandOpen=brandForDisplay(selected);
  dashboardTopicPlanState={loading:false,result:null,error:""};
  save();
 }
 return state.config.model;
}
function localIsoDate(){const now=new Date(),offset=now.getTimezoneOffset()*60000;return new Date(now-offset).toISOString().slice(0,10)}
function defaultMarketingModelContext(model=state.config.model){
 return{firstDate:"",t0Date:"",assessmentDate:localIsoDate(),selectedPhase:"auto",claims:[],competitors:{},productEvidence:null,salesWarningCycle:null};
}
function marketingModelContextKey(model=state.config.model){
 const context=opportunityCacheContext(),selected=String(model||"unselected").trim()||"unselected";
 return[context.orgId,context.edition,selected].map(value=>encodeURIComponent(value)).join(":");
}
function rawMarketingModelContext(model=state.config.model){
 const defaults=defaultMarketingModelContext(model);
 try{const parsed=JSON.parse(opportunityStorageValue("mmnMarketingModelContext",marketingModelContextKey(model))||"null");return parsed&&typeof parsed==="object"?{...defaults,...parsed,claims:Array.isArray(parsed.claims)?parsed.claims:[],competitors:parsed.competitors&&typeof parsed.competitors==="object"?parsed.competitors:{}}:defaults}catch(_){return defaults}
}
function loadMarketingModelContext(model=state.config.model){
 const stored=rawMarketingModelContext(model),cycleContext=stored.salesWarningCycle;
 if(cycleContext?.status==="verified")return{...stored,t0Date:cycleContext.launchDate,assessmentDate:cycleContext.assessmentDate,cycleSource:cycleContext.source,cycleStatus:cycleContext.status,phaseKey:cycleContext.phaseKey,phaseLabel:cycleContext.phaseLabel,phaseRange:cycleContext.phaseRange};
 if(cycleContext?.status)return{...stored,t0Date:"",selectedPhase:"auto",cycleSource:cycleContext.source,cycleStatus:cycleContext.status,phaseKey:"",phaseLabel:cycleContext.phaseLabel||"",phaseRange:""};
 return stored;
}
function saveMarketingModelContext(value,model=state.config.model,{authoritativeSync=false}={}){
 const stored=rawMarketingModelContext(model),protectedCycle=stored.salesWarningCycle?.status==="verified",next={...defaultMarketingModelContext(model),...(value||{}),claims:Array.isArray(value?.claims)?value.claims:[],competitors:value?.competitors&&typeof value.competitors==="object"?value.competitors:{}};
 if(protectedCycle&&!authoritativeSync){next.firstDate=stored.firstDate;next.t0Date=stored.t0Date;next.assessmentDate=stored.assessmentDate;next.salesWarningCycle=stored.salesWarningCycle}
 try{localStorage.setItem(opportunityScopedStorageKey("mmnMarketingModelContext",marketingModelContextKey(model)),JSON.stringify(next))}catch(_){}
 return next;
}
function syncMarketingModelCycleContext(cycleContext,model=state.config.model){
 if(!cycleContext||String(cycleContext.model||model)!==String(model))return rawMarketingModelContext(model);
 const stored=rawMarketingModelContext(model),normalized={...cycleContext,model,seriesId:String(cycleContext.seriesId||""),source:String(cycleContext.source||"sales-warning")};
 const next=saveMarketingModelContext({...stored,selectedPhase:"auto",salesWarningCycle:normalized},model,{authoritativeSync:true});
 const rail=document.querySelector("#t-cycle-rail");if(rail&&model===state.config.model)delete rail.dataset.positioned;
 return next;
}
function marketingModelPhase(context=loadMarketingModelContext()){
 const offset=globalThis.MmnTCycle?.dayOffset(context.t0Date,context.assessmentDate),current=globalThis.MmnTCycle?.phaseForOffset(offset),selected=context.selectedPhase&&context.selectedPhase!=="auto"?globalThis.MmnTCycle?.phases.find(item=>item.key===context.selectedPhase):current;
 return{offset,current,selected:selected||current||null};
}
function tCycleTopicStage(phase){return phase?`${phase.label}（${phase.range}）`:"周期待设置"}
function renderTCyclePanel(){
 const rail=document.querySelector("#t-cycle-rail"),currentLabel=document.querySelector("#t-cycle-current"),contextBox=document.querySelector("#t-cycle-context");if(!rail||!currentLabel||!contextBox||!globalThis.MmnTCycle)return;
 if(rail.dataset.model!==state.config.model){rail.dataset.model=state.config.model;delete rail.dataset.positioned}
 const context=loadMarketingModelContext(),cycleContext=context.salesWarningCycle,managed=Boolean(cycleContext?.status),verified=cycleContext?.status==="verified",phaseState=marketingModelPhase(context),actual=phaseState.current,selected=phaseState.selected,offset=phaseState.offset,tLabel=globalThis.MmnTCycle.tLabel(offset),displayPhase=verified?cycleContext.phaseLabel:actual?.label;
 const firstInput=document.querySelector("#t-cycle-first-date"),t0Input=document.querySelector("#t-cycle-t0-date"),assessmentInput=document.querySelector("#t-cycle-assessment-date");
 if(firstInput)firstInput.value=context.firstDate||"";if(t0Input)t0Input.value=context.t0Date||"";if(assessmentInput)assessmentInput.value=context.assessmentDate||localIsoDate();
 const saveButton=document.querySelector("#t-cycle-save");[firstInput,t0Input,assessmentInput,saveButton].forEach(control=>{if(control)control.disabled=managed});
 if(t0Input)t0Input.title=managed?"正式上市日由管理层销量预警维护":"";if(saveButton)saveButton.title=managed?"请回到销量预警维护正式上市日期":"";
 currentLabel.textContent=verified&&actual?`${tLabel} · ${displayPhase}`:cycleContext?.status==="pending_review"?"上市日期待复核":cycleContext?.status==="missing"?"尚未设置正式上市日期":"待设置T0";
 const selectedDates=globalThis.MmnTCycle.phaseDates(context.t0Date,selected),total=selected?.end===null?null:selected?selected.end-selected.start+1:null,covered=selected&&Number.isFinite(offset)?Math.max(0,Math.min(total??Math.max(1,offset-selected.start+1),offset-selected.start+1)):0;
 const sourceLabel=verified?(cycleContext.refreshStatus==="stale"?"由销量预警同步 · 数据暂未刷新":cycleContext.source==="sales-warning-cache"?"由销量预警同步 · 上次成功缓存":"由销量预警同步"):cycleContext?.status==="pending_review"?"上市日期待复核":cycleContext?.status==="missing"?"请在销量预警补录":"手工周期";
 contextBox.innerHTML=`<div><span>分析车型</span><b>${escapeHtml(state.config.model)}</b></div><div><span>当前阶段</span><b>${escapeHtml(actual?`${tLabel} ${displayPhase}`:"待设置")}</b></div><div><span>正在查看</span><b>${escapeHtml(selected?.label||"待设置")}</b></div><div><span>实际日期</span><b>${escapeHtml(selectedDates.start?`${selectedDates.start}${selectedDates.end?` — ${selectedDates.end}`:" 起"}`:"等待T0")}</b></div><div><span>数据进度</span><b>${context.t0Date&&selected?`${covered}${total?`/${total}`:""}天`:"待接入"}</b></div><div><span>周期来源</span><b>${escapeHtml(sourceLabel)}</b></div>`;
 rail.innerHTML=globalThis.MmnTCycle.phases.map(phase=>{const dates=globalThis.MmnTCycle.phaseDates(context.t0Date,phase),isActual=actual?.key===phase.key,isSelected=selected?.key===phase.key,status=!Number.isFinite(offset)?"waiting":isActual?"current":phase.end!==null&&offset>phase.end?"completed":offset<phase.start?"upcoming":"current";return`<button type="button" class="t-cycle-card ${status} ${isSelected?"selected":""}" data-t-cycle-phase="${escapeAttr(phase.key)}" aria-pressed="${isSelected?"true":"false"}"><span>${escapeHtml(phase.label)}</span><b>${escapeHtml(phase.range)}</b><small>${escapeHtml(dates.start?`${dates.start.slice(5)}${dates.end?`—${dates.end.slice(5)}`:"起"}`:"日期待设置")}</small><em>${status==="current"?"当前阶段":status==="completed"?"已完成":status==="upcoming"?"未开始":"待设置"}</em></button>`}).join("");
 const topicStage=document.querySelector("#dashboard-topic-stage");if(topicStage&&selected)topicStage.value=tCycleTopicStage(selected);
 rail.querySelectorAll("[data-t-cycle-phase]").forEach(button=>button.onclick=()=>{const next=loadMarketingModelContext();next.selectedPhase=button.dataset.tCyclePhase;saveMarketingModelContext(next);renderTCyclePanel();renderSellingPointDecisionWorkbench();const topic=document.querySelector("#dashboard-topic-stage"),chosen=globalThis.MmnTCycle.phases.find(item=>item.key===next.selectedPhase);if(topic)topic.value=tCycleTopicStage(chosen)});
 const activeCard=rail.querySelector(".t-cycle-card.selected");if(activeCard&&!rail.dataset.positioned){rail.dataset.positioned="true";requestAnimationFrame(()=>activeCard.scrollIntoView({behavior:"smooth",block:"nearest",inline:"center"}))}
}
function bindTCyclePanel(){
 const saveButton=document.querySelector("#t-cycle-save");if(saveButton)saveButton.onclick=()=>{const context=loadMarketingModelContext();if(context.salesWarningCycle?.status){toast("该车型周期由销量预警维护，请回到上方日期入口修改");return}context.firstDate=document.querySelector("#t-cycle-first-date")?.value||"";context.t0Date=document.querySelector("#t-cycle-t0-date")?.value||"";context.assessmentDate=document.querySelector("#t-cycle-assessment-date")?.value||localIsoDate();context.selectedPhase="auto";saveMarketingModelContext(context);const rail=document.querySelector("#t-cycle-rail");if(rail)delete rail.dataset.positioned;renderTCyclePanel();renderSellingPointDecisionWorkbench();toast("T周期已更新")};
 document.querySelectorAll("[data-t-cycle-scroll]").forEach(button=>button.onclick=()=>document.querySelector("#t-cycle-rail")?.scrollBy({left:Number(button.dataset.tCycleScroll)*320,behavior:"smooth"}));
}
const SELLING_POINT_LAUNCH_MODELS=["奥迪E7X","奥迪E5 Sportback","智己LS8","MG4","荣威i6","别克至境E7","ID.ERA 9X","尚界Z7"];
let sellingPointInputModel="",sellingPointInputCollapsed=true;
function sellingPointLabels(context=loadMarketingModelContext(),model=state.config.model){
 return [...new Set([...(context.claims||[]).map(item=>item.tag),...(state.rows||[]).filter(row=>row[0]===model).map(row=>row[4]),...OPPORTUNITY_REVIEW_LABELS].filter(Boolean))];
}
function renderSellingPointInput(){
 const panel=document.querySelector("#dashboard-selling-point-input"),body=document.querySelector("#selling-point-input-body"),modelSelect=document.querySelector("#selling-point-model-select"),toggle=document.querySelector("#selling-point-panel-toggle"),list=document.querySelector("#selling-point-list"),status=document.querySelector("#selling-point-input-status"),options=document.querySelector("#selling-point-tag-options"),form=document.querySelector("#selling-point-form");if(!panel||!body||!modelSelect||!toggle||!list||!status||!options||!form)return;
 const models=[...new Set([state.config.model,...SELLING_POINT_LAUNCH_MODELS].filter(Boolean))];if(!models.includes(sellingPointInputModel))sellingPointInputModel=state.config.model||models[0]||"";modelSelect.innerHTML=models.map(model=>`<option value="${escapeAttr(model)}" ${model===sellingPointInputModel?"selected":""}>${escapeHtml(model)}</option>`).join("");
 const context=loadMarketingModelContext(sellingPointInputModel),claims=context.claims||[],labels=sellingPointLabels(context,sellingPointInputModel);options.innerHTML=labels.map(label=>`<option value="${escapeAttr(label)}"></option>`).join("");status.textContent=`${sellingPointInputModel||"未选择车型"} · ${claims.length?`${claims.length}条卖点映射`:"等待卖点"}`;
 panel.classList.toggle("collapsed",sellingPointInputCollapsed);body.hidden=sellingPointInputCollapsed;toggle.textContent=sellingPointInputCollapsed?"展开":"收起";toggle.setAttribute("aria-expanded",sellingPointInputCollapsed?"false":"true");list.setAttribute("aria-label",`${sellingPointInputModel}的卖点映射列表`);
 list.innerHTML=claims.length?claims.map(item=>`<article class="selling-point-map-card"><div><span>品牌语言 · ${escapeHtml(item.model||sellingPointInputModel)}</span><b>${escapeHtml(item.claim)}</b></div><i aria-hidden="true">→</i><div><span>标准标签</span><b>${escapeHtml(item.tag||"待映射")}</b></div><i aria-hidden="true">→</i><div><span>用户语言</span><b>${escapeHtml(item.userLanguage||"待补充")}</b></div><button type="button" data-selling-point-delete="${escapeAttr(item.id)}" aria-label="删除${escapeAttr(item.model||sellingPointInputModel)}卖点映射">删除</button></article>`).join(""):`<div class="selling-point-empty"><b>${escapeHtml(sellingPointInputModel)}暂未录入集团卖点</b><span>选择该车型后，可直接建立“品牌语言 → 标准标签 → 用户语言”映射，不影响其他车型数据。</span></div>`;
 modelSelect.onchange=()=>{sellingPointInputModel=modelSelect.value;renderSellingPointInput()};toggle.onclick=()=>{sellingPointInputCollapsed=!sellingPointInputCollapsed;renderSellingPointInput();if(!sellingPointInputCollapsed)modelSelect.focus()};
 form.onsubmit=event=>{event.preventDefault();const data=new FormData(form),claim=String(data.get("claim")||"").trim();if(!claim)return;const next=loadMarketingModelContext(sellingPointInputModel);next.claims=[...(next.claims||[]),{id:`claim_${Date.now()}`,model:sellingPointInputModel,claim,tag:String(data.get("tag")||"").trim(),userLanguage:String(data.get("userLanguage")||"").trim()}];saveMarketingModelContext(next,sellingPointInputModel);form.reset();renderSellingPointInput();renderSellingPointDecisionWorkbench();toast(`${sellingPointInputModel}企业卖点映射已保存`)};
 list.querySelectorAll("[data-selling-point-delete]").forEach(button=>button.onclick=()=>{const next=loadMarketingModelContext(sellingPointInputModel);next.claims=(next.claims||[]).filter(item=>item.id!==button.dataset.sellingPointDelete);saveMarketingModelContext(next,sellingPointInputModel);renderSellingPointInput();renderSellingPointDecisionWorkbench()});
}
function activeSellingPointSignal(label){return dashboardDecisionSignals().find(item=>item.label===label)||null}
function sellingPointCompetitorOptions(signal){
 const configured=String(state.config.competitor||"").split(/[\/、,]/).map(item=>item.trim()),vertical=dashboardLatestCompetitorRows().slice(0,8).map(item=>item.competitor),scored=(signal?.rivals||[]).map(item=>item.model);
 return [...new Set([signal?.best?.model,...scored,...vertical,...configured].filter(item=>item&&item!==state.config.model))];
}
function sellingPointPlanningCompetitors(){
 const context=loadMarketingModelContext(),selected=context.competitors?.[sellingPointActiveLabel]||sellingPointActiveCompetitor,configured=String(state.config.competitor||"").split(/[\/、,]/).map(item=>item.trim());return[...new Set([selected,...configured].filter(Boolean))];
}
function sellingPointSignalForCompetitor(signal,competitor){
 if(!signal)return null;const rival=(signal.rivals||[]).find(item=>item.model===competitor);return{...signal,best:rival||null,gap:rival?signal.ownAvg-rival.score:null};
}
function parseMarketingDateRange(value){
 const dates=String(value||"").match(/\d{4}[.\/-]\d{1,2}[.\/-]\d{1,2}/g)||[],iso=dates.slice(0,2).map(value=>{const [year,month,day]=value.split(/[.\/-]/).map(Number);return`${String(year).padStart(4,"0")}-${String(month).padStart(2,"0")}-${String(day).padStart(2,"0")}`});return iso.length===2?{start:iso[0],end:iso[1]}:null;
}
function productEvidenceForLabel(context,label){
 const stateResult=state?.productWhitepaperEvidence?.[state.config.model],result=stateResult&&typeof stateResult==="object"?stateResult:context?.productEvidence&&typeof context.productEvidence==="object"?context.productEvidence:null,capabilities=Array.isArray(result?.capabilities)?result.capabilities:[],items=capabilities.filter(item=>item.label===label);
 return{result,items,verified:result?.status==="dual_model_verified"&&items.length>0};
}
async function restoreProductWhitepaperEvidence(model=state.config.model){
 const key=`${edition}:${model}`;if(productWhitepaperRestoreKeys.has(key))return;productWhitepaperRestoreKeys.add(key);
 try{
  const payload=await api(`/api/product-whitepaper/latest?${new URLSearchParams({model,edition})}`);if(!payload?.result)return;
  state.productWhitepaperEvidence={...(state.productWhitepaperEvidence||{}),[model]:payload.result};const context=loadMarketingModelContext(model);context.productEvidence=payload.result;saveMarketingModelContext(context,model);if(state.config.model===model)renderSellingPointDecisionWorkbench();
 }catch(_){productWhitepaperRestoreKeys.delete(key)}
}
async function uploadProductWhitepaper(file){
 if(!file)return;
 if(!/\.pdf$/i.test(file.name)){toast("请选择PDF格式的产品白皮书");return}
 const uploadModel=state.config.model;productWhitepaperUploadState={loading:true,error:""};renderSellingPointDecisionWorkbench();
 try{
  const query=new URLSearchParams({filename:file.name,model:uploadModel,edition:state.edition||"china"}),response=await fetch(`/api/product-whitepaper/analyze?${query}`,{method:"POST",headers:authHeaders({"Content-Type":file.type||"application/pdf"}),body:await file.arrayBuffer()}),payload=await response.json().catch(()=>({}));
  if(!response.ok||!payload.ok)throw new Error(payload.error||"白皮书解析失败");
  const next=loadMarketingModelContext(uploadModel);next.productEvidence=payload.result;saveMarketingModelContext(next,uploadModel);state.productWhitepaperEvidence={...(state.productWhitepaperEvidence||{}),[uploadModel]:payload.result};save();productWhitepaperUploadState={loading:false,error:""};renderSellingPointDecisionWorkbench();
  const count=payload.result?.capabilities?.length||0;toast(count?`白皮书已完成双旗舰复核：${count}条产品证据`:`白皮书已解析，暂未形成双旗舰一致证据`);
 }catch(error){productWhitepaperUploadState={loading:false,error:error.message||"白皮书解析失败"};renderSellingPointDecisionWorkbench();toast(`白皮书上传失败：${productWhitepaperUploadState.error}`)}
}
function sellingPointMarketingMatch({context,phaseState,signal,claim}){
 const dataLabel=dashboardTimeDimension(),dataRange=parseMarketingDateRange(dataLabel),phaseDates=globalThis.MmnTCycle?.phaseDates(context.t0Date,phaseState.selected),assessment=context.assessmentDate,phaseEnd=phaseDates?.end||assessment,expectedEnd=assessment&&phaseEnd&&assessment<phaseEnd?assessment:phaseEnd;
 let cycleRatio=null;if(dataRange&&phaseDates?.start&&expectedEnd&&expectedEnd>=phaseDates.start){const expectedDays=globalThis.MmnTCycle.dayOffset(phaseDates.start,expectedEnd)+1,overlapStart=dataRange.start>phaseDates.start?dataRange.start:phaseDates.start,overlapEnd=dataRange.end<expectedEnd?dataRange.end:expectedEnd,overlapDays=overlapEnd>=overlapStart?globalThis.MmnTCycle.dayOffset(overlapStart,overlapEnd)+1:0;cycleRatio=expectedDays>0?Math.max(0,Math.min(1,overlapDays/expectedDays)):null}
 const productEvidence=productEvidenceForLabel(context,sellingPointActiveLabel),cyclePoints=cycleRatio===null?0:Math.round(cycleRatio*35),nsrPoints=signal?.best?35:signal?18:0,claimPoints=claim?.userLanguage?20:claim?10:0,productPoints=productEvidence.verified?10:0,score=cyclePoints+nsrPoints+claimPoints+productPoints,status=score>=75?"高匹配":score>=50?"部分匹配":signal?"低匹配":"暂不可判断",tone=score>=75?"strong":score>=50?"partial":"risk",period=phaseState.selected?.label||"当前T阶段";
 const cycleNote=cycleRatio===null?"缺少可识别的数据周期，暂不能校验":cycleRatio>=.8?`${dataLabel}覆盖当前${period}考核窗口`:cycleRatio>0?`${dataLabel}仅覆盖当前${period}的${Math.round(cycleRatio*100)}%`:`${dataLabel}未覆盖当前${period}考核窗口`;
 return{score,status,tone,cyclePoints,nsrPoints,claimPoints,productPoints,cycleNote,cycleRatio};
}
function sellingPointDecision(signal){
 if(!signal)return{tone:"pending",title:"等待用户感知数据",action:"先补充该标签的提及量、正负样本与NSR，再进入机会判断。"};
 if(!signal.best||signal.gap===null)return{tone:"pending",title:"等待所选竞品同维NSR",action:"本品已有用户感知，但所选竞品缺少同标签NSR，暂不能判断领先或弱势。"};
 const positive=signal.ownAvg>=.6,leading=signal.gap===null?null:signal.gap>=0;
 if(positive&&leading!==false)return{tone:"strength",title:"已打透｜持续放大",action:"保持核心表达，并用产品事实与真实用户证词扩大相对优势。"};
 if(positive&&leading===false)return{tone:"opportunity",title:"口碑机会｜重点追赶",action:"用户评价健康，但竞品占位更强；增加差异化内容与同场景对比。"};
 if(!positive&&leading)return{tone:"opportunity",title:"相对机会｜先建正面认知",action:"本品尚未形成正面感知，但相对竞品仍有空间；先修正用户理解。"};
 return{tone:"risk",title:"判断依据待补强",action:"用户评价与竞品对比均不利，先补产品证据或调整表达，不建议直接放大。"};
}
const SELLING_POINT_EVIDENCE_LABELS={market_fact:"市场事实",user_perception:"用户感知",competitor_performance:"竞品表现",product_capability:"产品能力",communication_content:"传播内容"};
const SELLING_POINT_STATUS_LABELS={verified:"已验证",partial:"部分验证",conflict:"来源冲突",missing:"待补充"};
const SELLING_POINT_ADVISORY_STATUS_LABELS={aligned:"一致",partially_aligned:"部分一致",manual_required:"需要人工裁决",insufficient_evidence:"证据不足",degraded:"部分通道未完成",reviewing:"分析中",stale:"证据已变化"};
const SELLING_POINT_VERDICT_LABELS={amplify:"可考虑放大",optimize_expression:"优化表达",repair:"先修复",supplement_evidence:"补充证据",hold:"暂缓动作",manual_review:"人工复核"};
const SELLING_POINT_REVIEW_FALLBACK_LABELS=["独立建议一","独立建议二","独立建议三"];
function ensureSellingPointDecisionSidebar(){
 const layout=document.querySelector(".selling-point-decision-layout"),evidence=document.querySelector("#selling-point-evidence"),action=document.querySelector("#selling-point-action");if(!layout||!evidence||!action)return;
 let sidebar=layout.querySelector(".selling-point-decision-sidebar");if(!sidebar){sidebar=document.createElement("aside");sidebar.className="selling-point-decision-sidebar";sidebar.setAttribute("aria-label","当前标签决策侧栏");layout.insertBefore(sidebar,evidence);sidebar.append(evidence,action)}
}
function sellingPointEvidenceItemsSignature(packet){
 const value=packet||{};return JSON.stringify({edition:value.edition,brand:value.brand,model:value.model,competitor:value.competitor,label:value.label,tCycle:value.tCycle,items:value.items,conflicts:value.conflicts,gaps:value.gaps,windowCoverage:value.windowCoverage});
}
function stableSellingPointJson(value){if(Array.isArray(value))return`[${value.map(stableSellingPointJson).join(",")}]`;if(value&&typeof value==="object")return`{${Object.keys(value).sort().map(key=>`${JSON.stringify(key)}:${stableSellingPointJson(value[key])}`).join(",")}}`;return JSON.stringify(value)}
async function sellingPointEvidenceFingerprint(payload){
 const packet={edition:payload.edition,brand:payload.brand,model:payload.model,competitor:payload.competitor,label:payload.label,tCycle:payload.tCycle,...payload.evidencePacket},bytes=new TextEncoder().encode(stableSellingPointJson(packet)),digest=await crypto.subtle.digest("SHA-256",bytes);return[...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,"0")).join("");
}
function buildSellingPointEvidencePacket({context,phaseState,signal,claim,productEvidence,match,competitor}){
 const dataWindow=dashboardTimeDimension(),rows=(state.rows||[]).filter(row=>row[0]===state.config.model&&row[4]===sellingPointActiveLabel),productItems=productEvidence.items||[],productResult=productEvidence.result||{},productStatus=productEvidence.verified?"verified":productResult.readablePages?"partial":"missing",userConflict=String(signal?.evidence?.status||signal?.evidence?.label||"").includes("冲突"),userStatus=userConflict?"conflict":signal?"verified":"missing";
 const items=[
  {evidenceId:`evidence-market-${state.config.model}-${phaseState.selected?.key||"unset"}`,category:"market_fact",fact:context.t0Date?match.cycleNote:"当前尚未取得可校验的T周期窗口事实",status:match.cycleRatio>=.8?"verified":match.cycleRatio>0?"partial":"missing",impact:match.cycleRatio>=.8?"当前数据窗口可支撑本周期判断":"当前窗口不足以支撑完整周期判断",sourceRefs:[context.salesWarningCycle?.source||"T周期记录",dataWindow].filter(Boolean),timeRange:dataWindow||"待补充",sampleScope:`${state.config.model} · ${phaseState.selected?.label||"周期待设置"}`,limitations:"只说明时间窗口覆盖，不代表卖点营销价值"},
  {evidenceId:`evidence-user-${state.config.model}-${sellingPointActiveLabel}`,category:"user_perception",fact:signal?`${sellingPointActiveLabel}属性NSR为${(signal.ownAvg*100).toFixed(1)}%`:"当前标签缺少可用用户感知样本",status:userStatus,impact:userConflict?"不同来源方向不一致，必须先查看分平台差异":signal?"可用于判断当前属性认知，但不能外推为需求或销量":"不能形成属性级认知判断",sourceRefs:[signal?.evidence?.label,state.sourceNote].filter(Boolean),timeRange:dataWindow||"待补充",sampleScope:`${rows.length}条当前车型与标签记录`,limitations:"属性NSR是认知证据，不等于需求、订单或成交"},
  {evidenceId:`evidence-competitor-${competitor}-${sellingPointActiveLabel}`,category:"competitor_performance",fact:signal?.best?`${competitor}同标签NSR为${(signal.best.score*100).toFixed(1)}%，本品${signal.gap>=0?"领先":"落后"}${Math.abs(signal.gap*100).toFixed(1)}%`:"所选竞品缺少同标签可比证据",status:signal?.best?"verified":"missing",impact:signal?.best?"可用于识别相对认知位置，不直接代表产品强弱":"不能形成同维竞品比较",sourceRefs:[signal?.evidence?.label,state.sourceNote].filter(Boolean),timeRange:dataWindow||"待补充",sampleScope:`${state.config.model} 对标 ${competitor}`,limitations:"车型总量或平台热度不能替代属性级证据"},
  {evidenceId:String(productItems[0]?.evidenceId||`evidence-product-${state.config.model}-${sellingPointActiveLabel}`),category:"product_capability",fact:productEvidence.verified?`白皮书中有${productItems.length}条事实支持当前标签`:productResult.readablePages?"白皮书可读，但当前标签尚未形成双路一致产品事实":"当前标签缺少产品能力事实",status:productStatus,impact:productEvidence.verified?"可约束传播表达边界":"暂不能确认产品能力是否支持当前卖点",sourceRefs:productItems.flatMap(item=>[item.evidenceId,item.page?`白皮书P${item.page}`:""]).filter(Boolean),timeRange:productResult.updatedAt||productResult.createdAt||"当前白皮书版本",sampleScope:`${productItems.length}条当前标签产品事实`,limitations:"仅保留可引用产品事实；解析页数本身不构成证据"},
  {evidenceId:String(claim?.id||`evidence-content-${state.config.model}-${sellingPointActiveLabel}`),category:"communication_content",fact:claim?.userLanguage?`已建立用户语言映射：${claim.userLanguage}`:"当前标签缺少既有传播内容与用户语言映射",status:claim?.userLanguage?"partial":"missing",impact:claim?.userLanguage?"已有表达草案，但尚未验证真实传播表现":"无法判断表达是否已被用户理解",sourceRefs:[claim?.id,"卖点映射记录"].filter(Boolean),timeRange:"当前项目版本",sampleScope:claim?.userLanguage?"1条卖点语言映射":"0条可用传播映射",limitations:"语言映射不是传播结果，不能作为Learning"}
 ];
 return{items,conflicts:items.filter(item=>item.status==="conflict").map(item=>item.evidenceId),gaps:items.filter(item=>item.status==="missing").map(item=>item.evidenceId),windowCoverage:match.cycleRatio,updatedAt:String(productResult.updatedAt||state.datasetVersion||"")};
}
function sellingPointAdvisoryContext({context,phaseState,signal,claim,productEvidence,match,competitor}){
 return{edition:state.edition||edition||"china",brand:state.config.brand||"",model:state.config.model||"",competitor,label:sellingPointActiveLabel,tCycle:{phase:phaseState.selected?.key||"",display:phaseState.selected?`${globalThis.MmnTCycle?.tLabel(phaseState.offset)||""} · ${phaseState.selected.label}`:"周期待设置"},evidencePacket:buildSellingPointEvidencePacket({context,phaseState,signal,claim,productEvidence,match,competitor})};
}
function sellingPointAdvisoryKey(payload){return sellingPointEvidenceItemsSignature({...payload,...payload.evidencePacket})}
async function restoreSellingPointAdvisory(payload,key){
 if(sellingPointAdvisoryState.restoredKeys.has(key))return;sellingPointAdvisoryState.restoredKeys.add(key);
 try{const evidenceFingerprint=await sellingPointEvidenceFingerprint(payload),query=new URLSearchParams({edition:payload.edition,brand:payload.brand,model:payload.model,competitor:payload.competitor,label:payload.label,phase:payload.tCycle.phase,tDisplay:payload.tCycle.display,evidenceFingerprint}),response=await api(`/api/selling-point-advisory/latest?${query}`),result=response?.result;if(key!==sellingPointAdvisoryState.key)return;if(result){const matches=sellingPointEvidenceItemsSignature(result.evidencePacket)===sellingPointEvidenceItemsSignature({...payload,...payload.evidencePacket});sellingPointAdvisoryState.result=matches?result:{...result,status:"stale",canEnterMarketingAction:false}}renderSellingPointDecisionWorkbench()}catch(error){if(key===sellingPointAdvisoryState.key){sellingPointAdvisoryState.error=error.message||"最近建议恢复失败";renderSellingPointDecisionWorkbench()}}
}
async function runSellingPointAdvisory(payload,{force=false}={}){
 const key=sellingPointAdvisoryKey(payload);sellingPointAdvisoryState={...sellingPointAdvisoryState,key,loading:true,error:""};renderSellingPointDecisionWorkbench();
 try{const response=await api("/api/selling-point-advisory/run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...payload,force})});if(key!==sellingPointAdvisoryState.key)return;sellingPointAdvisoryState.result=response.result;sellingPointAdvisoryState.loading=false;renderSellingPointDecisionWorkbench()}catch(error){if(key!==sellingPointAdvisoryState.key)return;sellingPointAdvisoryState.loading=false;sellingPointAdvisoryState.error=error.message||"三路建议未完成";renderSellingPointDecisionWorkbench()}
}
async function submitSellingPointManualReview(runId,reason,decision){
 try{const response=await api("/api/selling-point-advisory/manual-review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({runId,reason,decision})});sellingPointAdvisoryState.result=response.result;sellingPointAdvisoryState.error="";renderSellingPointDecisionWorkbench();toast("人工确认已记录，但不会自动生成Learning")}catch(error){sellingPointAdvisoryState.error=error.message||"人工确认保存失败";renderSellingPointDecisionWorkbench()}
}
function renderSellingPointDecisionWorkbench(){
 ensureSellingPointDecisionSidebar();
 const controls=document.querySelector("#selling-point-decision-controls"),evidenceBox=document.querySelector("#selling-point-evidence"),actionBox=document.querySelector("#selling-point-action");if(!controls||!evidenceBox||!actionBox)return;
 const context=loadMarketingModelContext(),labels=sellingPointLabels(context),preferred=sellingPointActiveLabel||summaryAttributeActiveLabel||context.claims?.find(item=>item.tag)?.tag||labels[0]||"";sellingPointActiveLabel=labels.includes(preferred)?preferred:labels[0]||"";restoreProductWhitepaperEvidence(state.config.model);
 const phaseState=marketingModelPhase(context),rawSignal=activeSellingPointSignal(sellingPointActiveLabel),competitorOptions=sellingPointCompetitorOptions(rawSignal),storedCompetitor=context.competitors?.[sellingPointActiveLabel]||"",preferredCompetitor=[storedCompetitor,sellingPointActiveCompetitor,rawSignal?.best?.model,competitorOptions[0]].find(item=>competitorOptions.includes(item));sellingPointActiveCompetitor=preferredCompetitor||"";
 const signal=sellingPointSignalForCompetitor(rawSignal,sellingPointActiveCompetitor),claim=(context.claims||[]).find(item=>item.tag===sellingPointActiveLabel),competitor=sellingPointActiveCompetitor||"暂无可选竞品",period=phaseState.selected?.label||"周期待设置",tPeriod=phaseState.selected?`${globalThis.MmnTCycle?.tLabel(phaseState.offset)||""} · ${period}`:period;
 controls.innerHTML=`<label><span>穿透标签</span><select id="selling-point-active-label">${labels.map(label=>`<option value="${escapeAttr(label)}" ${label===sellingPointActiveLabel?"selected":""}>${escapeHtml(label)}</option>`).join("")}</select></label><div><span>当前车型</span><b>${escapeHtml(state.config.model)}</b></div><div><span>当前周期</span><b>${escapeHtml(tPeriod)}</b></div><label><span>选择对标车型</span><select id="selling-point-active-competitor" ${competitorOptions.length?"":"disabled"}>${competitorOptions.length?competitorOptions.map(model=>`<option value="${escapeAttr(model)}" ${model===sellingPointActiveCompetitor?"selected":""}>${escapeHtml(model)}</option>`).join(""):'<option>暂无可选竞品</option>'}</select></label>`;
 const productEvidence=productEvidenceForLabel(context,sellingPointActiveLabel),productResult=productEvidence.result||{},match=sellingPointMarketingMatch({context,phaseState,signal,claim}),payload=sellingPointAdvisoryContext({context,phaseState,signal,claim,productEvidence,match,competitor}),packet=payload.evidencePacket,key=sellingPointAdvisoryKey(payload);
 if(sellingPointAdvisoryState.key!==key){sellingPointAdvisoryState.key=key;sellingPointAdvisoryState.loading=false;sellingPointAdvisoryState.result=null;sellingPointAdvisoryState.error=""}
 restoreSellingPointAdvisory(payload,key);
 const verifiedCount=packet.items.filter(item=>item.status==="verified").length,conflictCount=packet.items.filter(item=>item.status==="conflict").length,missingCount=packet.items.filter(item=>item.status==="missing").length,coverage=packet.windowCoverage===null?"待校验":`${Math.round(packet.windowCoverage*100)}%`;
 evidenceBox.innerHTML=`<div class="selling-point-column-title"><span>02 事实与证据</span><b>只呈现事实、范围、冲突与缺口</b></div><div class="selling-point-evidence-summary"><b>${verifiedCount}/5类已验证</b><span>${conflictCount}项冲突</span><span>${missingCount}项待补充</span><span>周期覆盖${coverage}</span><small>证据包更新：${escapeHtml(packet.updatedAt||"待记录")}</small></div><div class="selling-point-evidence-list">${packet.items.map(item=>`<article class="${escapeAttr(item.status)} ${item.category==="product_capability"?"product-whitepaper-evidence":""}"><header><b>${escapeHtml(SELLING_POINT_EVIDENCE_LABELS[item.category])}</b><em>${escapeHtml(SELLING_POINT_STATUS_LABELS[item.status])}</em></header><p>${escapeHtml(item.fact||"当前没有可确认事实")}</p><details class="selling-point-evidence-detail"><summary>查看证据边界</summary><dl><div><dt>判断影响</dt><dd>${escapeHtml(item.impact)}</dd></div><div><dt>来源</dt><dd>${escapeHtml(item.sourceRefs.join(" · ")||"待补充")}</dd></div><div><dt>时间</dt><dd>${escapeHtml(item.timeRange||"待补充")}</dd></div><div><dt>样本</dt><dd>${escapeHtml(item.sampleScope||"待补充")}</dd></div><div><dt>限制</dt><dd>${escapeHtml(item.limitations||"待补充")}</dd></div><div><dt>证据ID</dt><dd>${escapeHtml(item.evidenceId)}</dd></div></dl></details>${item.category==="product_capability"?`<input type="file" id="product-whitepaper-file" accept="application/pdf,.pdf" hidden><button type="button" class="product-whitepaper-upload" id="product-whitepaper-upload" ${productWhitepaperUploadState.loading?"disabled":""}>${productWhitepaperUploadState.loading?"事实提取与复核中…":productResult.readablePages?"更新产品白皮书PDF":"上传产品白皮书PDF"}</button>${productEvidence.items.length?`<ul class="product-whitepaper-citations">${productEvidence.items.slice(0,3).map(capability=>`<li><b>${escapeHtml(capability.claim)}</b><details><summary>P${capability.page} · 查看原文</summary><span>“${escapeHtml(capability.quote)}”</span></details></li>`).join("")}</ul>`:""}`:""}</article>`).join("")}</div>`;
 const result=sellingPointAdvisoryState.result,status=sellingPointAdvisoryState.loading?"reviewing":result?.status||"insufficient_evidence",reviews=result?.reviews||[],channelErrors=result?.channelErrors||[],synthesis=result?.synthesis||{alignment:"insufficient",commonJudgment:"当前尚未形成三路独立建议",disagreements:[],recommendation:"先核对事实证据，再启动分析",nextAction:"启动三路分析",citedEvidenceIds:[]},readiness=result?.readiness||{level:missingCount||conflictCount?"low":verifiedCount>=4?"medium":"low",verifiedCount,totalCount:5,conflictCount,missingCount,reason:`${verifiedCount}/5类证据已验证${conflictCount?`，存在${conflictCount}项冲突`:""}${missingCount?`，${missingCount}项待补充`:""}`};
 const reviewSlots=[0,1,2].map(index=>{const review=reviews.find(item=>item.reviewId===String(index+1)),failed=channelErrors.find(item=>item.reviewId===String(index+1));return review?`<details class="selling-point-review-card completed"><summary><span>${escapeHtml(review.label)}</span><b>${escapeHtml(SELLING_POINT_VERDICT_LABELS[review.verdict]||review.verdict)}</b><small>${escapeHtml(review.summary)}</small></summary><div><p>${escapeHtml(review.rationale)}</p><dl><div><dt>建议动作</dt><dd>${escapeHtml(review.recommendedAction)}</dd></div><div><dt>不确定性</dt><dd>${escapeHtml(review.uncertainty)}</dd></div><div><dt>引用证据</dt><dd>${escapeHtml(review.citedEvidenceIds.join(" · "))}</dd></div></dl></div></details>`:failed?`<article class="selling-point-review-card failed"><header><span>${escapeHtml(failed.label)}</span><b>未完成</b></header><p>${escapeHtml(failed.error)}</p></article>`:`<article class="selling-point-review-card pending"><header><span>${SELLING_POINT_REVIEW_FALLBACK_LABELS[index]}</span><b>${sellingPointAdvisoryState.loading?"分析中":"待启动"}</b></header><p>${sellingPointAdvisoryState.loading?"正在读取同一锁定证据包":"启动后将形成独立结论、动作和不确定性"}</p></article>`}).join("");
 const statusLabel=SELLING_POINT_ADVISORY_STATUS_LABELS[status]||status,actionButtons=[];
 if(!result&&!sellingPointAdvisoryState.loading)actionButtons.push('<button type="button" class="primary" id="selling-point-run-advisory">启动三路独立分析</button>');
 if(status==="insufficient_evidence")actionButtons.push('<button type="button" class="secondary" id="selling-point-create-evidence-task">创建补证任务</button>');
 if(conflictCount||status==="partially_aligned")actionButtons.push('<button type="button" class="secondary" id="selling-point-view-differences">查看分平台差异</button>');
 if(status==="manual_required"||status==="partially_aligned")actionButtons.push('<button type="button" class="secondary" id="selling-point-manual-review">进入人工裁决</button>');
 if(status==="degraded")actionButtons.push('<button type="button" class="secondary" id="selling-point-retry-advisory">重试失败通道</button>');
 if(status==="stale")actionButtons.push('<button type="button" class="secondary" id="selling-point-rerun-advisory">基于最新证据重新分析</button>');
 if(productEvidence.verified&&(!signal||signal.ownAvg<.6))actionButtons.push('<button type="button" class="secondary" id="selling-point-language-plan">生成用户语言方案</button>');
 actionButtons.push(`<button type="button" class="secondary" id="selling-point-to-topic" ${result?.canEnterMarketingAction?"":"disabled"}>带入营销动作</button>`);
 if(result&&status!=="reviewing"&&!result.manualReview)actionButtons.push('<button type="button" class="tertiary" id="selling-point-manual-confirm">人工确认</button>');
 actionBox.innerHTML=`<div class="selling-point-column-title"><span>03 三路独立洞察与综合动作</span><b>同证据盲审 · 确定性聚合 · 人工最终裁决</b></div><div class="selling-point-advisory-progress" aria-live="polite"><span>${escapeHtml(statusLabel)}</span><b>${sellingPointAdvisoryState.loading?"分析进行中":`${result?.completedCount||0}/3路完成`}</b>${sellingPointAdvisoryState.error?`<p>${escapeHtml(sellingPointAdvisoryState.error)}</p>`:""}</div><section class="selling-point-independent-reviews" aria-label="三路独立洞察">${reviewSlots}</section><section class="selling-point-synthesis"><header><span>MMN综合判断</span><b>${escapeHtml(statusLabel)}</b></header><h3>${escapeHtml(synthesis.commonJudgment)}</h3>${synthesis.disagreements?.length?`<p><strong>主要分歧：</strong>${escapeHtml(synthesis.disagreements.join("；"))}</p>`:""}<p><strong>综合建议：</strong>${escapeHtml(synthesis.recommendation)}</p>${synthesis.citedEvidenceIds?.length?`<small>综合引用：${escapeHtml(synthesis.citedEvidenceIds.join(" · "))}</small>`:""}</section><section class="selling-point-readiness ${escapeAttr(readiness.level)}"><span>决策准备度</span><b>${readiness.level==="high"?"高":readiness.level==="medium"?"中":"低"}</b><p>${escapeHtml(readiness.reason)}</p><small>${result?.canEnterMarketingAction?"证据与发布门禁已通过":"当前不可直接进入传播放大"}</small></section><div class="selling-point-action-buttons">${actionButtons.join("")}</div><p class="selling-point-guardrail">本模块止于 Evidence → Insight → Decision → Action；只有行动产生真实结果并完成复盘后，才可进入 Learning / Know-how。</p>`;
 const selector=document.querySelector("#selling-point-active-label");if(selector)selector.onchange=()=>{sellingPointActiveLabel=selector.value;summaryAttributeActiveLabel=selector.value;renderSellingPointDecisionWorkbench()};
 const competitorSelector=document.querySelector("#selling-point-active-competitor");if(competitorSelector)competitorSelector.onchange=()=>{sellingPointActiveCompetitor=competitorSelector.value;const next=loadMarketingModelContext();next.competitors={...(next.competitors||{}),[sellingPointActiveLabel]:sellingPointActiveCompetitor};saveMarketingModelContext(next);renderSellingPointDecisionWorkbench()};
 const whitepaperButton=document.querySelector("#product-whitepaper-upload"),whitepaperInput=document.querySelector("#product-whitepaper-file");if(whitepaperButton&&whitepaperInput){whitepaperButton.onclick=()=>whitepaperInput.click();whitepaperInput.onchange=()=>uploadProductWhitepaper(whitepaperInput.files?.[0])}
 const runButton=document.querySelector("#selling-point-run-advisory");if(runButton)runButton.onclick=()=>runSellingPointAdvisory(payload);
 const retryButton=document.querySelector("#selling-point-retry-advisory");if(retryButton)retryButton.onclick=()=>runSellingPointAdvisory(payload,{force:true});
 const rerunButton=document.querySelector("#selling-point-rerun-advisory");if(rerunButton)rerunButton.onclick=()=>runSellingPointAdvisory(payload,{force:true});
 const differenceButton=document.querySelector("#selling-point-view-differences");if(differenceButton)differenceButton.onclick=()=>{const detail=[...evidenceBox.querySelectorAll("article.conflict details")][0];if(detail){detail.open=true;detail.scrollIntoView({behavior:"smooth",block:"center"})}else toast("当前证据包没有可展开的来源冲突")};
 const evidenceTaskButton=document.querySelector("#selling-point-create-evidence-task");if(evidenceTaskButton)evidenceTaskButton.onclick=()=>result?.runId?submitSellingPointManualReview(result.runId,"按综合门禁创建补证任务",{verdict:"supplement_evidence",taskType:"evidence_supplement",status:"created",nextAction:"补齐缺失与冲突证据"}):runSellingPointAdvisory(payload);
 const manualAction=()=>{if(!result?.runId)return;const reason=prompt("请填写人工裁决理由");if(reason?.trim())submitSellingPointManualReview(result.runId,reason.trim(),{verdict:"manual_review",nextAction:synthesis.nextAction||"人工确认下一步"})};
 const manualReviewButton=document.querySelector("#selling-point-manual-review"),manualConfirmButton=document.querySelector("#selling-point-manual-confirm");if(manualReviewButton)manualReviewButton.onclick=manualAction;if(manualConfirmButton)manualConfirmButton.onclick=manualAction;
 const languageButton=document.querySelector("#selling-point-language-plan");if(languageButton)languageButton.onclick=()=>{const goal=document.querySelector("#dashboard-topic-goal"),stage=document.querySelector("#dashboard-topic-stage");if(goal)goal.value=`围绕${sellingPointActiveLabel}，将已验证产品能力转为可被用户复述的场景语言`;if(stage)stage.value=tCycleTopicStage(phaseState.selected);document.querySelector("#dashboard-topic-planner")?.scrollIntoView({behavior:"smooth",block:"start"});toast("已带入用户语言方案")};
 const topicButton=document.querySelector("#selling-point-to-topic");if(topicButton)topicButton.onclick=()=>{if(!result?.canEnterMarketingAction)return;const goal=document.querySelector("#dashboard-topic-goal"),stage=document.querySelector("#dashboard-topic-stage");if(goal)goal.value=`围绕${sellingPointActiveLabel}，对标${competitor}，${synthesis.recommendation}`;if(stage)stage.value=tCycleTopicStage(phaseState.selected);document.querySelector("#dashboard-topic-planner")?.scrollIntoView({behavior:"smooth",block:"start"});toast("已通过门禁并带入营销动作")};
}
function renderDashboard(a){
	 renderTCyclePanel();
	 bindTCyclePanel();
	 renderSellingPointInput();
	 renderDashboardCompetitorTrend();
	 renderDashboardProductProof();
	 renderDashboardStrategyChoice();
	 renderModelJudgmentWorkbench();
 renderDashboardTopicPlanner(a);
	 renderDashboardData(a);
 renderDashboardCognition(a);
 renderOpportunityMap(a);
 renderStrategyReportExport();
	 renderSellingPointDecisionWorkbench();
 renderCockpitDecisionLoop();
}

function dashboardLatestCompetitorRows(model=state.config.model){
 const comparisonModels=new Set((state.models||[]).filter(value=>value&&value!==model));
 const all=canonicalVerticalItems(verticalState.items||[]).filter(x=>x.ownModel===model&&x.competitor&&Number(x.positiveRank)>0&&(!comparisonModels.size||comparisonModels.has(x.competitor)));
 const automotiveHome=all.filter(x=>x.platform==="汽车之家"&&nullableNumber(x.share)!==null);
 const items=automotiveHome.length?automotiveHome:all;
 if(!items.length)return[];
 const latestOrder=[...items].sort((a,b)=>String(a.periodOrder||a.period).localeCompare(String(b.periodOrder||b.period))).at(-1)?.periodOrder;
 const latestRows=latestOrder?items.filter(x=>x.periodOrder===latestOrder):items.filter(x=>x.period===uniquePeriods(items).at(-1));
 return latestRows.sort((a,b)=>(a.positiveRank||999)-(b.positiveRank||999)||(nullableNumber(b.share)??-1)-(nullableNumber(a.share)??-1));
}
function dashboardCompetitorSeries(model=state.config.model){
 const rows=canonicalVerticalItems(verticalState.items||[]).filter(x=>x.ownModel===model&&x.competitor&&x.platform==="汽车之家");
 const grouped=new Map();
 rows.forEach(x=>{const key=x.competitor,item=grouped.get(key)||{competitor:key,rows:[]};item.rows.push(x);grouped.set(key,item)});
 const sorted=[...grouped.values()].map(item=>({...item,rows:dashboardDistinctCompetitorRows(item.rows)})).sort((a,b)=>(a.rows.at(-1)?.positiveRank||999)-(b.rows.at(-1)?.positiveRank||999));
 const cutoff=sorted[7]?.rows.at(-1)?.positiveRank;
 return cutoff?sorted.filter(item=>(item.rows.at(-1)?.positiveRank||999)<=cutoff):sorted;
}
function canonicalVerticalItems(items=[]){
 const observations=new Map();
 (items||[]).forEach(row=>{const sheet=String(row.sheet||"").trim(),period=String(row.period||"").trim(),grain=sheet||String(row.periodOrder||period),key=[row.source||row.platform||"",row.platform||"",grain,row.ownModel||"",row.competitor||"",row.share,row.positiveRank,row.negativeRank].join("|");const current=observations.get(key),isReadableRange=/^\d{1,2}[.\/-]\d{1,2}\s*[-–—]/.test(period);if(!current||isReadableRange)observations.set(key,row)});
 return [...observations.values()];
}
function dashboardDistinctCompetitorRows(rows=[]){
 return canonicalVerticalItems(rows).sort((a,b)=>String(a.periodOrder||a.period).localeCompare(String(b.periodOrder||b.period),"zh-CN",{numeric:true}));
}
function renderDashboardCompetitorTrend(){
 const box=document.querySelector("#dashboard-competitor-trend");if(!box)return;
 const series=dashboardCompetitorSeries(),periods=[...new Set(series.flatMap(x=>x.rows.map(r=>r.period)))];
 if(!series.length){box.innerHTML=`<p class="empty">当前车型尚无可用的垂媒正反向关系数据。</p>`;return}
 const latestRows=series.map(item=>item.rows.at(-1)),rankCounts=key=>latestRows.reduce((counts,row)=>{const rank=String(row?.[key]||"");if(rank)counts.set(rank,(counts.get(rank)||0)+1);return counts},new Map()),positiveCounts=rankCounts("positiveRank"),negativeCounts=rankCounts("negativeRank"),allShares=series.flatMap(item=>item.rows.map(row=>nullableNumber(row.share))).filter(value=>value!==null),maxShare=Math.max(.01,...allShares),rangeLabel=periods.length>1?`${periods[0]} → ${periods.at(-1)}`:periods[0]||"当前周期";
 box.innerHTML=`<div class="competitor-trend-definition"><span><b>车系对比次数占比</b> 表示用户把本品与该车型放入同一对比集合的比例；不代表偏好、口碑或销量。点击任一车型可查看完整走势。</span><b>${escapeHtml(rangeLabel)}</b></div><div class="competitor-trend-head"><b>竞品</b><span>正向序位 / 反向序位 <i class="competitor-trend-help" tabindex="0" data-tip="序位按最新周期对应榜单计算；占比相同时保留并列名次，因此名次可以重复。">?</i></span><span>本周占比</span><span>对比热度走势</span><span>较上周</span></div>${series.map(item=>{const latest=item.rows.at(-1),previous=item.rows.at(-2),share=nullableNumber(latest.share),prior=nullableNumber(previous?.share),delta=share!==null&&prior!==null?share-prior:null,change=delta===null?null:delta*100,flat=change!==null&&Math.abs(change)<.05,stable=change!==null&&Math.abs(change)<.5,latestText=share!==null?`${(share*100).toFixed(1)}%`:"—",priorText=prior!==null?`${(prior*100).toFixed(1)}%`:"—",changeText=change===null?"暂无环比":flat?"持平":`${change>0?"+":""}${change.toFixed(1)}%`,direction=change===null||flat?"→":change>0?"↑":"↓",periodText=previous?`${priorText} → ${latestText}`:`仅 ${latest.period}`,positiveRank=String(latest.positiveRank||""),negativeRank=String(latest.negativeRank||"");const chartWidth=240,chartHeight=44,baseY=39,topY=5,values=item.rows.map(row=>nullableNumber(row.share)),points=values.map((value,index)=>({x:values.length===1?chartWidth:index*(chartWidth/(values.length-1)),y:value===null?baseY:baseY-(value/maxShare)*(baseY-topY)})),validPoints=points.filter((point,index)=>values[index]!==null),pointText=validPoints.map(point=>`${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" "),areaPath=validPoints.length?`M ${validPoints[0].x.toFixed(1)} ${baseY} L ${pointText.replaceAll(" "," L ")} L ${validPoints.at(-1).x.toFixed(1)} ${baseY} Z`:"",lastPoint=validPoints.at(-1);return`<button type="button" class="competitor-trend-row" data-competitor-trend="${escapeAttr(item.competitor)}" aria-label="查看${escapeAttr(state.config.model)}与${escapeAttr(item.competitor)}完整竞争走势"><b>${escapeHtml(item.competitor)}</b><span class="competitor-ranks"><em class="${positiveCounts.get(positiveRank)>1?"tied":""}">正向 ${positiveRank?`第${escapeHtml(positiveRank)}`:"—"}</em><em class="negative ${negativeCounts.get(negativeRank)>1?"tied":""}">反向 ${negativeRank?`第${escapeHtml(negativeRank)}`:"—"}</em></span><i class="competitor-trend-share"><strong>${latestText}</strong><small>本周</small></i><svg class="competitor-trend-chart" viewBox="0 0 ${chartWidth} ${chartHeight}" role="img" aria-label="${escapeAttr(item.competitor)} ${escapeAttr(rangeLabel)} 对比热度走势"><line class="competitor-trend-grid" x1="0" y1="${baseY}" x2="${chartWidth}" y2="${baseY}"></line>${areaPath?`<path class="competitor-trend-area" d="${areaPath}"></path>`:""}${pointText?`<polyline class="competitor-trend-line" points="${pointText}"></polyline>`:""}${lastPoint?`<circle class="competitor-trend-point" cx="${lastPoint.x.toFixed(1)}" cy="${lastPoint.y.toFixed(1)}" r="3.5"></circle>`:""}</svg><strong class="competitor-trend-change ${stable?"stable":delta>0?"up":delta<0?"down":""}"><span>${direction}</span><b>${changeText}</b><small>${escapeHtml(periodText)}</small></strong></button>`}).join("")}`;
 const periodKey=row=>String(row?.periodOrder||row?.period||""),currentPeriodRow=latestRows.slice().sort((a,b)=>periodKey(a).localeCompare(periodKey(b),"zh-CN",{numeric:true})).at(-1),currentPeriod=currentPeriodRow?.period||"",positiveTieCounts=latestRows.reduce((counts,row)=>{const rank=String(row?.positiveRank||""),share=nullableNumber(row?.share);if(rank&&share!==null){const key=[row.period,rank,share.toFixed(6)].join("|");counts.set(key,(counts.get(key)||0)+1)}return counts},new Map());
 const rankHead=box.querySelector(".competitor-trend-head span:nth-child(2)");if(rankHead)rankHead.innerHTML=`本品→该车 / 该车→本品 <i class="competitor-trend-help" tabindex="0" data-tip="本品→该车：从本品出发，该车型在共同对比车系中的名次；该车→本品：反向从竞品出发，本品在其共同对比车系中的名次。同一周期占比完全相同时共享名次。">?</i>`;
 box.querySelectorAll(".competitor-trend-row").forEach((button,index)=>{const latest=series[index]?.rows.at(-1);if(!latest)return;const badges=button.querySelectorAll(".competitor-ranks em"),rank=String(latest.positiveRank||""),share=nullableNumber(latest.share),tieKey=share===null?"|":[latest.period,rank,share.toFixed(6)].join("|"),sameShare=(positiveTieCounts.get(tieKey)||0)>1;if(badges[0]){badges[0].classList.toggle("tied",sameShare);badges[0].textContent=`本品→该车 ${rank?`${sameShare?"同占比":""}第${rank}`:"—"}`}if(badges[1]){badges[1].classList.remove("tied");badges[1].textContent=`该车→本品 ${latest.negativeRank?`第${latest.negativeRank}`:"—"}`}const period=button.querySelector(".competitor-trend-share small");if(period)period.textContent=latest.period||"周期未知";button.classList.toggle("stale",Boolean(currentPeriod&&latest.period!==currentPeriod))});
 box.querySelectorAll("[data-competitor-trend]").forEach(button=>button.onclick=()=>{const item=series.find(value=>value.competitor===button.dataset.competitorTrend);if(item)openTrendDialog(item.rows,item.competitor,state.config.model,item.rows.map(row=>row.period))});
}
function dashboardDecisionSignals(){
 const model=state.config.model,competitors=dashboardLatestCompetitorRows(model).map(x=>x.competitor),labels=[...new Set((state.rows||[]).filter(r=>r[0]===model&&r[4]).map(r=>r[4]))];
 return labels.map(label=>{const ownScores=attributeSourceScores(state.rows,model,label),ownAvg=meanNumbers(ownScores.map(item=>item.score));if(ownAvg===null)return null;const rivals=competitors.map(competitor=>({model:competitor,score:meanNumbers(attributeSourceScores(state.rows,competitor,label).map(item=>item.score))})).filter(item=>item.score!==null).sort((a,b)=>b.score-a.score),benchmark=nullableNumber(state.summaryAttributeBenchmark?.["全网"]?.[label]),best=rivals[0]||(benchmark===null?null:{model:state.importQuality?.attributeBenchmarkLabel||"竞品均值",score:benchmark,benchmark:true}),evidence=attributeEvidenceStatus(state.rows,label,model),gap=best?ownAvg-best.score:null;return{label,ownAvg,best,rivals,evidence,gap,benchmarkUsed:Boolean(best?.benchmark)}}).filter(Boolean).sort((a,b)=>Math.abs(b.gap||0)-Math.abs(a.gap||0));
}
function dashboardProductEvidenceTask(label){
 const text=String(label||"");
 if(/安全/.test(text))return{missing:"官方安全配置与权威测试结果",action:"核对安全配置表，并补充碰撞或主动安全场景验证"};
 if(/质量/.test(text))return{missing:"耐久、故障与长期车主样本",action:"补充长期使用样本，核验高频故障是否真实存在"};
 if(/辅助|自动驾驶|智驾/.test(text))return{missing:"功能边界与典型场景实测",action:"按城区、高速、泊车场景验证能力边界与接管情况"};
 if(/动力|操控/.test(text))return{missing:"加速、制动与操控场景实测",action:"用同场景实测对比核心竞品，确认差异是否成立"};
 if(/价格|权益|成本/.test(text))return{missing:"价格权益与使用成本明细",action:"统一配置和周期口径，核算本品与竞品真实成本差"};
 if(/空间|舒适/.test(text))return{missing:"尺寸数据与乘坐体验实测",action:"补充前后排、储物和长途乘坐的可视化实测"};
 if(/外观|内饰|造型|设计/.test(text))return{missing:"设计细节、材质与工艺实拍",action:"用同角度实拍和细节特写证明感知差异"};
 if(/服务|口碑/.test(text))return{missing:"服务政策与真实用户案例",action:"核对服务政策，并补充可追溯的车主体验案例"};
 return{missing:"车型官方资料与关键场景实测",action:"先补齐可核验资料，再决定放大、解释或避战"};
}
function renderDashboardProductProof(){
 const box=document.querySelector("#dashboard-product-proof");if(!box)return;
 const signals=dashboardDecisionSignals().slice(0,8),verified=opportunityEvidenceState.result?.qa?.verifiedLabelCount||0;
 const proofItems=signals.map(item=>{const task=dashboardProductEvidenceTask(item.label),priority=item.evidence.tone==="conflict"||item.evidence.tone==="risk"||item.gap<=-.12?"urgent":item.gap>=.12?"opportunity":"routine",status=priority==="urgent"?"优先核验":priority==="opportunity"?"可放大，先补证":"常规补证",comparison=item.best&&item.gap!==null?`相对 ${item.best.model} ${item.gap>=0?"领先":"落后"} ${Math.abs(item.gap*100).toFixed(1)}%`:"暂无同维竞品数据";return{...item,task,priority,status,comparison}}),counts={urgent:proofItems.filter(item=>item.priority==="urgent").length,opportunity:proofItems.filter(item=>item.priority==="opportunity").length,routine:proofItems.filter(item=>item.priority==="routine").length};
 box.innerHTML=`<div class="panel-title"><div><span>从认知判断到产品核验任务</span><h2>哪些结论能用，哪些需要先补证</h2></div><em>${verified?`${verified}项已验证`:"不臆造产品事实"}</em></div><div class="product-proof-summary"><span class="urgent">优先核验 <b>${counts.urgent}</b></span><span class="opportunity">可放大，先补证 <b>${counts.opportunity}</b></span><span>常规补证 <b>${counts.routine}</b></span></div><div class="product-proof-cards">${proofItems.map(item=>`<article class="product-proof-card ${item.priority}"><header><div><small>属性标签</small><b>${escapeHtml(item.label)}</b></div><em>${item.status}</em></header><dl><div><dt>当前判断</dt><dd><strong>${escapeHtml(item.comparison)}</strong><span>${escapeHtml(item.evidence.label)} · ${escapeHtml(item.evidence.note)}</span></dd></div><div><dt>还缺什么</dt><dd>${escapeHtml(item.task.missing)}</dd></div></dl><footer><span>下一步核验</span><p>${escapeHtml(item.task.action)}</p></footer></article>`).join("")}</div>`;
}
function renderDashboardStrategyChoice(){
 const box=document.querySelector("#dashboard-strategy-choice");if(!box)return;
 const signals=dashboardDecisionSignals().slice(0,6);
 box.innerHTML=`<div class="panel-title"><div><span>人工决策层</span><h2>证据之后选择动作，而不是由声量自动下结论</h2></div><em>可追溯 · 可沉淀</em></div><div class="strategy-choice-table">${signals.map(item=>{const action=item.evidence.tone==="conflict"?"补证":item.gap>=.12?"放大":item.gap<=-.12?"避战/反证":"解释";return`<div data-strategy-label="${escapeAttr(item.label)}"><span>${escapeHtml(item.label)}</span><b>${action}</b><p>${item.best?`相对 ${escapeHtml(item.best.model)} ${item.gap>=0?"领先":"落后"} ${Math.abs(item.gap*100).toFixed(1)}%；`:"竞品同维数据不足；"}${item.evidence.note}。</p><button type="button" class="ghost" data-dashboard-learning="${escapeAttr(item.label)}">沉淀Learning</button><button type="button" class="ghost" data-dashboard-knowhow="${escapeAttr(item.label)}">沉淀Know-how</button></div>`}).join("")}</div>`;
 box.querySelectorAll("[data-dashboard-learning]").forEach(button=>button.onclick=()=>persistDashboardLearningAndKnowhow("learning",button.dataset.dashboardLearning));
 box.querySelectorAll("[data-dashboard-knowhow]").forEach(button=>button.onclick=()=>persistDashboardLearningAndKnowhow("knowhow",button.dataset.dashboardKnowhow));
 const loop=document.querySelector("#dashboard-learning-loop");if(loop)loop.innerHTML=`<b>决策资产回流</b><span>Learning 保存本项目已验证判断；Know-how 保存跨车型可复用的方法、适用条件与反例。二者都会进入后续 RAG 检索。</span>`;
}
async function persistDashboardLearningAndKnowhow(kind,label){
 const signal=dashboardDecisionSignals().find(item=>item.label===label);if(!signal)return;
 const now=new Date().toISOString(),competitor=signal.best?.model||"暂无同维竞品",basis=`NSR周期 ${dashboardTimeDimension()}；垂媒周期 ${dashboardVerticalTimeDimension()}；NSR来源 ${(state.importQuality?.attributeNsrSources||[]).join("/")||"现有全网及分平台"}；垂媒来源 汽车之家`;
 if(kind==="learning"){
  const item={edition:activeEdition(),model:state.config.model,label,conclusion:`${label}本品NSR ${(signal.ownAvg*100).toFixed(1)}%，${signal.best?`相对${competitor}${signal.gap>=0?"领先":"落后"}${Math.abs(signal.gap*100).toFixed(1)}%`:"竞品同维证据不足"}，证据状态为${signal.evidence.label}。`,recommendation:signal.evidence.tone==="conflict"?"先补来源与场景实测，不直接放大":signal.gap>=.12?"验证产品事实后作为主传播认知放大":signal.gap<=-.12?"先做竞品差异验证，再决定反证或避战":"补充用户场景解释",evidence:basis,platform:"全网/分平台NSR + 汽车之家",stage:"策略驾驶舱",savedAt:now};
  if(session){const data=await api("/api/learnings",{method:"POST",body:JSON.stringify({...item,org_id:session.org_id,user_id:session.user_id})});serverLearnings.unshift({...data.item,savedAt:data.item.saved_at})}else{saveLearnings([...learnings(),item])}
  toast(`已将「${label}」沉淀为 Learning`);render();return;
 }
 const item={id:`cockpit_knowhow_${state.config.model}_${label}`.replace(/\s+/g,"_"),type:"决策驾驶舱Know-how",title:`${label}｜NSR与竞品占位交叉判断`,body:`先用全网及分平台NSR判断用户语言和来源一致性，再用垂媒正反向关系确定真实竞争集合，最后经产品事实验证后选择放大、补证、反证或避战。`,keywords:[state.config.model,label,competitor,"NSR","竞品占位"],tags:[label,signal.evidence.label],targets:["决策驾驶舱","打法知识库","报告"],source:"dashboard_decision_loop",createdAt:now,metadata:{model:state.config.model,competitor,period:dashboardTimeDimension(),basis,applicability:"有属性NSR且存在真实车型比较关系",counterexample:"来源冲突或缺少产品事实时不可直接转为传播主张"}};
 mergeStrategyKnowledge([item]);toast(`已将「${label}」沉淀为 Know-how`);render();
}
function opportunityMarketSignals(){
 const rows=[];
 for(const row of state.rows||[]){
  const nsr=nullableNumber(row[14]);
  if(!row[4]||nsr===null)continue;
  rows.push({model:row[0],attribute:row[4],nsr,volume:nullableNumber(row[8])??0,interaction:nullableNumber(row[15])??0,purchaseImpact:nullableNumber(row[9])??3,platform:row[2]||"",timeWindow:dashboardTimeDimension()});
 }
 for(const cycle of cockpitDecisionState.cycles||[]){
  const feedback=cycle.feedbackSignal;
  if(!feedback||feedback.model!==state.config.model)continue;
  const nsr=nullableNumber(feedback.nsr);if(nsr===null)continue;
  rows.push({model:feedback.model,attribute:feedback.attribute||feedback.label,nsr,volume:nullableNumber(feedback.volume)??0,interaction:nullableNumber(feedback.interaction)??0,purchaseImpact:nullableNumber(feedback.purchaseImpact)??3,platform:feedback.platform||"",timeWindow:dashboardTimeDimension(),source:"cockpit_execution_monitoring"});
 }
 return rows;
}
function cockpitEvidenceStage(label,detail,status="pending"){return `<li class="${escapeAttr(status)}"><b>${escapeHtml(label)}</b><small>${escapeHtml(detail)}</small></li>`}
function renderCockpitEvidenceChain(){
 const box=document.querySelector("#cockpit-evidence-chain");if(!box)return;
 const run=opportunityEvidenceState.result,signals=opportunityMarketSignals(),hasRows=(state.rows||[]).length>0,hasSignals=signals.length>0,hasNsr=signals.some(item=>Number.isFinite(Number(item.nsr))),hasVertical=(verticalState.items||[]).length>0,verticalEvidence=run?.verticalEvidence||[],verified=Number(run?.qa?.verifiedLabelCount||0),recommendations=run?.executionRecommendations||[],cycles=cockpitDecisionState.cycles||[],planned=cycles.filter(item=>item.status==="planned").length,feedback=cycles.filter(item=>item.status==="feedback_recorded").length;
 const groups=[
  {title:"社会传播证据",items:[cockpitEvidenceStage("传播事实",hasRows?`已接入 ${state.rows.length} 条声量/互动记录`:"待导入声量与互动",hasRows?"ready":"pending"),cockpitEvidenceStage("真实属性诊断",hasSignals?`已归因 ${new Set(signals.map(item=>item.attribute||item.label).filter(Boolean)).size} 个属性`:"待属性级数据",hasSignals?"ready":"pending"),cockpitEvidenceStage("真实属性 NSR 对比",hasNsr?"属性级 NSR 已对齐":"待补充属性级 NSR",hasNsr?"ready":"pending")]},
  {title:"产品事实验证",items:[cockpitEvidenceStage("属性分类",hasSignals?"按 MMN 统一标签归类":"等待属性信号",""+(hasSignals?"ready":"pending")),cockpitEvidenceStage("垂媒交叉验证",verticalEvidence.length?`已纳入 ${verticalEvidence.length} 条匹配的正反向关系`:run&&hasVertical?"当前车型无匹配的垂媒关系":"待接入汽车之家 / 懂车帝",verticalEvidence.length?"ready":"pending"),cockpitEvidenceStage("车型官方产品事实",opportunityEvidenceState.document?"本品资料已解析":"待上传本品资料",opportunityEvidenceState.document?"ready":"pending"),cockpitEvidenceStage("双旗舰交叉验证",verified?`已验证 ${verified} 个标签`:run?"仍有待确认标签":"待运行",verified?"ready":"pending")]},
  {title:"决策执行闭环",items:[cockpitEvidenceStage("竞品攻防与机会地图",run?.opportunities?.length?`已形成 ${run.opportunities.length} 个地图标签`:"待生成机会地图",run?.opportunities?.length?"ready":"pending"),cockpitEvidenceStage("下一步传播建议",recommendations.length?`已生成 ${recommendations.length} 项可执行建议`:"仅对验证标签生成",recommendations.length?"ready":"pending"),cockpitEvidenceStage("传播执行",planned||feedback?`已纳入 ${planned+feedback} 项传播执行`:"待纳入执行",planned||feedback?"ready":"pending"),cockpitEvidenceStage("结果监测 → 证据回流",feedback?`${feedback} 项结果将进入下一轮属性信号`:"待记录监测结果",feedback?"ready":"pending")]}
 ];
 box.innerHTML=`<div class="cockpit-evidence-chain-head"><b>决策驾驶舱证据链</b><small>按 Social 规划串联；只有双旗舰验证通过的属性才会进入传播执行。</small></div><div class="cockpit-evidence-chain-groups">${groups.map(group=>`<section><h3>${escapeHtml(group.title)}</h3><ol>${group.items.join("")}</ol></section>`).join("")}</div>`;
}
function cockpitStrategyOptions(item){
 const options=Array.isArray(item?.options)?item.options.filter(option=>String(option?.id||"").trim()):[];
 if(options.length)return options;
 return [{id:"legacy_default",title:item?.action||"既有策略",action:item?.action||"既有策略",competitorModel:item?.competitorModel||"待补充竞品",platform:item?.platform||"待补充平台",contentScenario:item?.contentScenario||`${item?.label||"该属性"}真实使用场景`,description:"历史单一策略记录，沿用原执行方案。"}];
}
function cockpitStrategyOptionsMarkup(item,options){
 const recommended=options.find(option=>option.id===item.recommendedOptionId);
 return `<fieldset class="cockpit-strategy-options" data-cockpit-options="${escapeAttr(item.label)}"><legend>策略选项 <small>${recommended?`推荐路径：${escapeHtml(recommended.title)}；`:""}请人工选择后再纳入执行。</small></legend><div>${options.map(option=>`<label class="cockpit-strategy-option"><input type="radio" name="cockpit-strategy-${escapeAttr(item.label)}" value="${escapeAttr(option.id)}" data-cockpit-option="${escapeAttr(option.id)}"><span><b>${escapeHtml(option.title||option.action||"策略选项")}</b><small>${escapeHtml(option.description||option.contentScenario||"")}</small></span></label>`).join("")}</div></fieldset>`;
}
function cockpitSelectedStrategy(plan){
 const selected=plan?.selectedOption;
 if(selected)return selected;
 return {title:plan?.action||"既有策略",action:plan?.action||"既有策略",contentScenario:plan?.contentScenario||""};
}
function renderCockpitDecisionLoop(){
 const box=document.querySelector("#cockpit-decision-loop");if(!box)return;
 box.innerHTML=`<div class="cockpit-decision-empty"><b>数据驱动策略提示</b><span>上方机会地图已直接根据导入的属性 NSR 生成。选择车型后即可识别可巩固、需加强、风险和数据缺口；需要内容策略时，再使用 MMN 策略输出生成表达方案。</span></div>`;
 return;
 const run=opportunityEvidenceState.result,recommendations=run?.executionRecommendations||[],cycles=cockpitDecisionState.cycles||[];
 if(!run){box.innerHTML=`<div class="cockpit-decision-empty"><b>传播执行与结果监测</b><span>机会地图完成双旗舰验证后，这里将明确输出：贴靠哪台车、主打哪个产品点、优先哪个平台与内容场景。</span></div>`;return}
 if(!recommendations.length){box.innerHTML=`<div class="cockpit-decision-empty"><b>尚无可执行传播建议</b><span>冲突或证据不足的标签仍留在人工确认台；完成双旗舰验证后会自动进入此处。</span></div>`;return}
 const cards=recommendations.map(item=>{
  const cycle=cycles.find(value=>value.runId===run.runId&&value.label===item.label),monitoring=cycle?.monitoring||{},recorded=cycle?.status==="feedback_recorded",plan=cycle?.plan||item,options=cockpitStrategyOptions(item),selectedStrategy=cycle?cockpitSelectedStrategy(plan):null,verticalForCompetitor=(run.verticalEvidence||[]).filter(evidence=>evidence.competitor===(plan.competitorModel||item.competitorModel)),verticalProof=verticalForCompetitor.length?verticalForCompetitor.map(evidence=>`${evidence.platform} · ${evidence.period}`).join(" / "):"当前车型暂无匹配的垂媒关系";
  const executionBlock=cycle?`<p class="cockpit-selected-strategy"><b>人工已选策略</b><span>${escapeHtml(selectedStrategy.title||selectedStrategy.action||"既有策略")}${selectedStrategy.contentScenario?` · ${escapeHtml(selectedStrategy.contentScenario)}`:""}</span></p><div class="cockpit-monitoring" data-cockpit-cycle="${escapeAttr(cycle.id)}"><div class="cockpit-monitoring-head"><b>结果监测</b><small>${recorded?"已回流到下一轮属性信号，可继续更新":"记录后将回流到下一轮机会地图"}</small></div><div class="cockpit-monitoring-fields"><label>声量<input data-cockpit-volume type="number" min="0" value="${escapeAttr(monitoring.volume??"")}"></label><label>互动<input data-cockpit-interaction type="number" min="0" value="${escapeAttr(monitoring.interaction??"")}"></label><label>NSR<input data-cockpit-nsr type="number" min="-1" max="1" step="0.01" value="${escapeAttr(monitoring.nsr??"")}"></label><label>观察备注<input data-cockpit-observation value="${escapeAttr(monitoring.observation||"")}" placeholder="例如：收藏/评论表现"></label></div><button type="button" class="secondary" data-cockpit-monitor="${escapeAttr(cycle.id)}">${recorded?"更新结果并回流":"记录结果并回流"}</button></div>`:`${cockpitStrategyOptionsMarkup(item,options)}<button type="button" class="secondary" data-cockpit-execute="${escapeAttr(item.label)}">确认纳入传播执行</button>`;
  return `<article class="cockpit-decision-card ${recorded?"feedback":""}"><header><div><span>${escapeHtml(item.categoryLabel||plan.action)}</span><b>${escapeHtml(item.label)}</b></div><em>${recorded?"已回流":cycle?"执行已立项":"待人工选择"}</em></header><dl><div><dt>贴靠车型</dt><dd>${escapeHtml(plan.competitorModel||"待补充竞品")}</dd></div><div><dt>主打产品点</dt><dd>${escapeHtml(item.label)}</dd></div><div><dt>优先平台</dt><dd>${escapeHtml(plan.platform||"待补充平台")}</dd></div><div><dt>内容场景</dt><dd>${escapeHtml(plan.contentScenario||"待补充内容场景")}</dd></div></dl><p class="cockpit-vertical-proof"><b>垂媒交叉验证</b><span>${escapeHtml(verticalProof)}</span></p>${executionBlock}</article>`;
 }).join("");
 box.innerHTML=`<div class="cockpit-decision-head"><div><span>传播执行与结果监测</span><b>机会地图 → 策略选项 → 执行回流</b></div><small>仅保存本地决策记录，不会直接触发外部投放。</small></div><div class="cockpit-decision-list">${cards}</div>${cockpitDecisionState.error?`<p class="cockpit-decision-error" role="alert">${escapeHtml(cockpitDecisionState.error)}</p>`:""}`;
 box.querySelectorAll("[data-cockpit-execute]").forEach(button=>button.onclick=async()=>{
  const contextKey=opportunityCacheContext().key;
  const card=button.closest(".cockpit-decision-card"),selected=card?.querySelector("[data-cockpit-option]:checked");
  if(!selected){toast("请先选择策略选项，再纳入传播执行");card?.querySelector("[data-cockpit-option]")?.focus();return}
  button.disabled=true;
  try{const data=await api("/api/cockpit/execution-cycles",{method:"POST",body:JSON.stringify({runId:run.runId,label:button.dataset.cockpitExecute,optionId:selected.value})}),nextCycles=[data.cycle,...cycles.filter(item=>item.id!==data.cycle.id)];saveCockpitDecisionCycleCache(nextCycles,contextKey);if(contextKey!==opportunityCacheContext().key)return;cockpitDecisionState={cycles:nextCycles,loading:false,error:""};renderCockpitEvidenceChain();renderCockpitDecisionLoop();toast("已记录人工策略选择，等待结果监测")}
  catch(err){if(contextKey!==opportunityCacheContext().key)return;cockpitDecisionState={...cockpitDecisionState,error:err.message};renderCockpitDecisionLoop();toast(`传播执行记录失败：${err.message}`)}
 });
 box.querySelectorAll("[data-cockpit-monitor]").forEach(button=>button.onclick=async()=>{const contextKey=opportunityCacheContext().key,panel=button.closest("[data-cockpit-cycle]");button.disabled=true;try{const data=await api("/api/cockpit/execution-cycles/monitoring",{method:"POST",body:JSON.stringify({cycleId:button.dataset.cockpitMonitor,volume:panel.querySelector("[data-cockpit-volume]").value,interaction:panel.querySelector("[data-cockpit-interaction]").value,nsr:panel.querySelector("[data-cockpit-nsr]").value,observation:panel.querySelector("[data-cockpit-observation]").value})}),nextCycles=[data.cycle,...cycles.filter(item=>item.id!==data.cycle.id)];saveCockpitDecisionCycleCache(nextCycles,contextKey);if(contextKey!==opportunityCacheContext().key)return;cockpitDecisionState={cycles:nextCycles,loading:false,error:""};renderCockpitEvidenceChain();renderCockpitDecisionLoop();toast("监测结果已回流，下一次机会地图会纳入该属性信号")}catch(err){if(contextKey!==opportunityCacheContext().key)return;cockpitDecisionState={...cockpitDecisionState,error:err.message};renderCockpitDecisionLoop();toast(`监测结果保存失败：${err.message}`)}});
}
function opportunityJobProgressMarkup(job,view){
 if(!job||!view||!['queued','running','completed','failed'].includes(job.status))return"";
 const stages=Array.isArray(globalThis.OPPORTUNITY_JOB_STAGES)?globalThis.OPPORTUNITY_JOB_STAGES:[];
 const running=opportunityJobRunning(job);
 return `<div class="opportunity-job-progress ${job.status}" role="status" aria-live="polite" aria-atomic="true"><div class="opportunity-job-progress-head"><span class="opportunity-job-spinner" aria-hidden="true"></span><div><strong>${escapeHtml(view.statusLabel)}</strong><small>${escapeHtml(view.detail)}</small></div><span>${escapeHtml(view.elapsedLabel)}</span></div><progress max="100" value="${view.progress}" aria-label="机会地图生成进度 ${view.progress}%"></progress><ol>${stages.map((stage,index)=>`<li class="${job.status==='completed'||index<view.activeStage?'done':index===view.activeStage&&running?'active':''}"><i aria-hidden="true"></i><span>${escapeHtml(stage.label)}</span></li>`).join("")}</ol></div>`;
}
function opportunityReviewStatusMeta(status){
 const value=String(status||"pending");
 if(value.endsWith("_pending_recheck"))return{label:"待双模型复核",className:"recheck"};
 if(value==="needs_evidence")return{label:"待补证",className:"evidence"};
 if(value==="verified")return{label:"已验证",className:"verified"};
 if(value==="rejected")return{label:"已驳回",className:"rejected"};
 return{label:"待处理",className:"pending"};
}
function opportunityReviewMatchesFilter(item){
 const filter=opportunityReviewState.filter,status=String(item?.status||"pending");
 if(filter==="all")return true;
 if(filter==="pending_recheck")return status.endsWith("_pending_recheck");
 if(filter==="processed")return status==="verified"||status==="rejected";
 return status===filter;
}
function opportunityReviewFilteredItems(){
 const query=opportunityReviewState.search.trim().toLowerCase();
 return (opportunityReviewState.queue?.items||[]).filter(item=>{
  if(!opportunityReviewMatchesFilter(item))return false;
  if(!query)return true;
  const evidence=item.evidence||{};
  return [item.title,item.claim,(item.candidateLabels||[]).join(" "),(item.reasons||[]).join(" "),evidence.sourceRef,evidence.excerpt,evidence.pageNo].join(" ").toLowerCase().includes(query);
 });
}
function opportunityReviewDraft(item){
 if(!item)return{selectedLabel:"",note:"",action:"corrected"};
 if(!opportunityReviewState.drafts.has(item.id)){
  const decision=item.decision||{},candidates=item.candidateLabels||[];
  opportunityReviewState.drafts.set(item.id,{selectedLabel:decision.selectedLabel||candidates[0]||"",note:decision.note||"",action:decision.action||"corrected"});
 }
 return opportunityReviewState.drafts.get(item.id);
}
function opportunityReviewCaptureDraft(item){
 if(!item)return opportunityReviewDraft(item);
 const draft=opportunityReviewDraft(item),label=document.querySelector("#opportunity-review-label"),note=document.querySelector("#opportunity-review-note");
 if(label)draft.selectedLabel=label.value;
 if(note)draft.note=note.value;
 return draft;
}
function opportunityReviewSetMessage(message,isError=false){
 opportunityReviewState.message=isError?"":message;
 opportunityReviewState.error=isError?message:"";
 const node=document.querySelector("#opportunity-review-message");
 if(node){node.textContent=message||"";node.classList.toggle("error",isError)}
}
function opportunityReviewDetailMarkup(item){
 if(!item)return`<div class="opportunity-review-empty"><strong>当前筛选暂无待确认项</strong><span>可切换状态或清除搜索查看其他记录。</span></div>`;
 const evidence=item.evidence||{},status=opportunityReviewStatusMeta(item.status),draft=opportunityReviewDraft(item),candidates=[...new Set(item.candidateLabels||[])],labels=[...new Set([...candidates,...OPPORTUNITY_REVIEW_LABELS])],processed=["verified","rejected"].includes(item.status),disabled=opportunityReviewState.saving||processed,summaryOnly=!item.factId&&item.type==="fact_alignment_summary";
 if(summaryOnly&&["accepted","corrected"].includes(draft.action))draft.action="needs_evidence";
 const action=draft.action||"corrected";
 const actionCopy={accepted:"采纳现有标签",corrected:"保存人工修正",rejected:"驳回该事实",needs_evidence:"标记待补证"};
 return `<header class="opportunity-review-detail-head"><div><span>当前证据项</span><h3 tabindex="-1">${escapeHtml(item.title||item.claim||"待确认产品点")}</h3></div><em class="opportunity-review-status ${status.className}">${status.label}</em></header>
 <div class="opportunity-review-evidence"><div><span>事实原文</span><p>${escapeHtml(item.claim||evidence.excerpt||"未提供可引用原文")}</p></div><div class="opportunity-review-source"><span>证据定位</span><b>${escapeHtml(evidence.sourceRef||"本品资料")}${evidence.pageNo?` · 第 ${escapeHtml(evidence.pageNo)} 页`:""}</b><small>${escapeHtml(evidence.excerpt||"暂无摘录")}</small></div></div>
 <div class="opportunity-review-reasons"><span>进入人工确认的原因</span><ul>${(item.reasons||["证据不足，需要人工确认"]).map(reason=>`<li>${escapeHtml(reason)}</li>`).join("")}</ul></div>
 <div class="opportunity-review-candidates"><span>模型候选标签</span><div>${candidates.length?candidates.map(label=>`<button type="button" data-review-candidate="${escapeAttr(label)}" ${disabled||summaryOnly?"disabled":""}>${escapeHtml(label)}</button>`).join(""):`<small>没有可靠候选，请从统一标签中选择或标记待补证。</small>`}</div></div>
 ${summaryOnly?'<p class="opportunity-review-summary-notice">这是未归类事实的汇总项，缺少可定位的事实 ID，不能直接采纳或修正。请标记待补证，或确认整组内容无效后驳回。</p>':""}
 <div class="opportunity-review-fields"><label><span>最终统一标签</span><select id="opportunity-review-label" ${disabled||summaryOnly?"disabled":""}><option value="">请选择统一标签</option>${labels.map(label=>`<option value="${escapeAttr(label)}" ${label===draft.selectedLabel?"selected":""}>${escapeHtml(label)}</option>`).join("")}</select></label><label><span>人工依据${opportunityReviewState.selectedIds.size>1?"（批量待补证将共用此依据）":""}</span><textarea id="opportunity-review-note" rows="4" ${disabled?"disabled":""} placeholder="说明适用版本、证据页码、修正理由或需要补充的材料">${escapeHtml(draft.note||"")}</textarea></label></div>
 <div class="opportunity-review-actions" role="group" aria-label="人工确认处理方式">${[["accepted","采纳"],["corrected","修正"],["rejected","驳回"],["needs_evidence","待补证"]].map(([value,label])=>{const actionDisabled=disabled||(summaryOnly&&(value==="accepted"||value==="corrected"));return`<button type="button" data-review-action="${value}" class="${action===value?"active":""}" aria-pressed="${action===value}" ${actionDisabled?"disabled":""}>${label}</button>`}).join("")}</div>
 ${processed?`<p class="opportunity-review-readonly">该项已${item.status==="verified"?"通过双模型复核":"驳回"}，当前为只读记录。</p>`:`<button type="button" id="opportunity-review-save" class="primary" ${opportunityReviewState.saving?"disabled":""}>${opportunityReviewState.saving?"正在保存…":actionCopy[action]}</button>`}`;
}
function renderOpportunityReviewDialog(){
 const dialog=document.querySelector("#opportunity-review-dialog"),countsNode=document.querySelector("#opportunity-review-counts"),list=document.querySelector("#opportunity-review-list"),detail=document.querySelector("#opportunity-review-detail"),filter=document.querySelector("#opportunity-review-status-filter"),search=document.querySelector("#opportunity-review-search"),selectedCount=document.querySelector("#opportunity-review-selected-count"),bulk=document.querySelector("#opportunity-review-bulk-needs-evidence"),message=document.querySelector("#opportunity-review-message"),recheck=document.querySelector("#opportunity-review-recheck");
 if(!dialog||!countsNode||!list||!detail)return;
 if(filter)filter.value=opportunityReviewState.filter;
 if(search&&search.value!==opportunityReviewState.search)search.value=opportunityReviewState.search;
 if(opportunityReviewState.loading){
  countsNode.innerHTML='<span class="active">正在读取人工确认队列…</span>';
  list.innerHTML='<div class="opportunity-review-loading" aria-busy="true"><i></i><i></i><i></i></div>';
  detail.innerHTML='<div class="opportunity-review-empty"><strong>正在装载证据</strong><span>将展示事实原文、页码与候选统一标签。</span></div>';
 }else{
  const counts=opportunityReviewState.queue?.counts||{total:0,pending:0,pendingRecheck:0,needsEvidence:0,processed:0,blocking:0},items=opportunityReviewFilteredItems();
  countsNode.innerHTML=`<span>全部 <b>${counts.total||0}</b></span><span class="pending">待处理 <b>${counts.pending||0}</b></span><span class="recheck">待复核 <b>${counts.pendingRecheck||0}</b></span><span class="evidence">待补证 <b>${counts.needsEvidence||0}</b></span><span class="verified">已处理 <b>${counts.processed||0}</b></span>`;
  if(!items.some(item=>item.id===opportunityReviewState.selectedId))opportunityReviewState.selectedId=items[0]?.id||"";
  list.innerHTML=items.length?items.map(item=>{const meta=opportunityReviewStatusMeta(item.status),selected=item.id===opportunityReviewState.selectedId,canBulk=item.status==="pending";return`<article class="opportunity-review-item ${selected?"selected":""}"><label class="opportunity-review-check" title="选择后可批量标记待补证"><input type="checkbox" data-review-select="${escapeAttr(item.id)}" ${opportunityReviewState.selectedIds.has(item.id)?"checked":""} ${canBulk?"":"disabled"}><span class="sr-only">选择 ${escapeHtml(item.title||item.claim||"待确认项")}</span></label><button type="button" data-review-item-id="${escapeAttr(item.id)}" aria-current="${selected?"true":"false"}"><span>${escapeHtml(item.title||item.claim||"待确认项")}</span><small>${escapeHtml((item.candidateLabels||[]).join(" / ")||item.type||"证据核验")}</small></button><em class="opportunity-review-status ${meta.className}">${meta.label}</em></article>`}).join(""):`<div class="opportunity-review-empty compact"><strong>没有匹配项</strong><span>尝试切换状态或调整搜索词。</span></div>`;
  const current=(opportunityReviewState.queue?.items||[]).find(item=>item.id===opportunityReviewState.selectedId);
  detail.innerHTML=opportunityReviewDetailMarkup(current);
  if(selectedCount)selectedCount.textContent=`已选 ${opportunityReviewState.selectedIds.size} 项`;
  if(bulk){bulk.disabled=!opportunityReviewState.selectedIds.size||opportunityReviewState.saving}
  if(recheck){recheck.hidden=!(counts.pendingRecheck>0);recheck.disabled=opportunityReviewState.saving;recheck.textContent=`验证并更新已确认标签（${counts.pendingRecheck||0}）`}
  list.querySelectorAll("[data-review-item-id]").forEach(button=>button.onclick=()=>{opportunityReviewState.selectedId=button.dataset.reviewItemId;renderOpportunityReviewDialog();document.querySelector("#opportunity-review-detail h3")?.focus?.()});
  list.querySelectorAll("[data-review-select]").forEach(input=>input.onchange=()=>{input.checked?opportunityReviewState.selectedIds.add(input.dataset.reviewSelect):opportunityReviewState.selectedIds.delete(input.dataset.reviewSelect);if(input.checked)opportunityReviewState.selectedId=input.dataset.reviewSelect;renderOpportunityReviewDialog()});
  detail.querySelectorAll("[data-review-candidate]").forEach(button=>button.onclick=()=>{const select=document.querySelector("#opportunity-review-label");if(select){select.value=button.dataset.reviewCandidate;select.dispatchEvent(new Event("change"))}});
  const label=document.querySelector("#opportunity-review-label"),note=document.querySelector("#opportunity-review-note");
  if(current&&label)label.onchange=()=>{opportunityReviewDraft(current).selectedLabel=label.value};
  if(current&&note)note.oninput=()=>{opportunityReviewDraft(current).note=note.value};
  detail.querySelectorAll("[data-review-action]").forEach(button=>button.onclick=()=>{if(!current)return;opportunityReviewCaptureDraft(current).action=button.dataset.reviewAction;renderOpportunityReviewDialog();const target=button.dataset.reviewAction==="corrected"||button.dataset.reviewAction==="accepted"?"#opportunity-review-label":"#opportunity-review-note";document.querySelector(target)?.focus()});
  const save=document.querySelector("#opportunity-review-save");if(save&&current)save.onclick=()=>saveOpportunityManualReview(opportunityReviewDraft(current).action,[current.id]);
 }
 if(filter)filter.onchange=()=>{opportunityReviewState.filter=filter.value;opportunityReviewState.selectedId="";renderOpportunityReviewDialog()};
 if(search)search.oninput=()=>{opportunityReviewState.search=search.value;opportunityReviewState.selectedId="";renderOpportunityReviewDialog()};
 if(message){message.textContent=opportunityReviewState.error||opportunityReviewState.message||"";message.classList.toggle("error",Boolean(opportunityReviewState.error))}
 if(bulk)bulk.onclick=()=>{const ids=[...opportunityReviewState.selectedIds];if(!ids.length)return;const current=(opportunityReviewState.queue?.items||[]).find(item=>item.id===opportunityReviewState.selectedId);saveOpportunityManualReview("needs_evidence",ids,opportunityReviewCaptureDraft(current).note)};
 if(recheck)recheck.onclick=()=>runOpportunityManualRecheck();
}
function bindOpportunityReviewDialog(){
 if(opportunityReviewDialogBound)return;
 const dialog=document.querySelector("#opportunity-review-dialog"),close=document.querySelector("#opportunity-review-dialog-close"),done=document.querySelector("#opportunity-review-done");
 if(!dialog)return;
 opportunityReviewDialogBound=true;
 if(close)close.onclick=()=>dialog.close();
 if(done)done.onclick=()=>dialog.close();
 dialog.addEventListener("close",()=>{const trigger=opportunityReviewTrigger;opportunityReviewTrigger=null;requestAnimationFrame(()=>{if(trigger?.isConnected)trigger.focus();else document.querySelector("#opportunity-review-button")?.focus()})});
}
async function openOpportunityReview(trigger){
 const documentId=opportunityEvidenceState.document?.documentId,dialog=document.querySelector("#opportunity-review-dialog");
 if(!documentId||!dialog){toast("请先上传并解析本品产品资料");return}
 bindOpportunityReviewDialog();
 opportunityReviewTrigger=trigger||document.activeElement;
 if(opportunityReviewState.queue?.document?.documentId!==documentId)opportunityReviewState={loading:false,saving:false,queue:null,selectedId:"",selectedIds:new Set(),filter:"pending",search:"",message:"",error:"",drafts:new Map()};
 opportunityReviewState.loading=true;opportunityReviewState.error="";opportunityReviewState.message="";
 if(!dialog.open)dialog.showModal();
 renderOpportunityReviewDialog();
 document.querySelector("#opportunity-review-dialog-close")?.focus();
 try{
  const runId=opportunityEvidenceState.result?.runId||"",query=new URLSearchParams({documentId,runId});
  const queue=await api(`/api/opportunity-map/manual-reviews?${query}`);
  opportunityReviewState.queue=queue;
  if(!(queue.items||[]).some(item=>item.status==="pending")&&queue.counts?.pendingRecheck)opportunityReviewState.filter="pending_recheck";
  opportunityReviewState.selectedId=opportunityReviewFilteredItems()[0]?.id||queue.items?.[0]?.id||"";
  if(opportunityEvidenceState.document){opportunityEvidenceState.document={...opportunityEvidenceState.document,manualReviewCount:Number(queue.counts?.blocking||0)};saveOpportunityDocument(opportunityEvidenceState.document)}
 }catch(err){opportunityReviewState.error=err.message||"人工确认队列读取失败"}finally{opportunityReviewState.loading=false;renderOpportunityReviewDialog()}
}
async function saveOpportunityManualReview(action,itemIds,noteOverride=""){
 const queue=opportunityReviewState.queue,item=(queue?.items||[]).find(entry=>entry.id===opportunityReviewState.selectedId),draft=opportunityReviewCaptureDraft(item),selectedLabel=draft.selectedLabel||"",note=String(noteOverride||draft.note||"").trim();
 if(!itemIds?.length)return;
 if(!item?.factId&&item?.type==="fact_alignment_summary"&&(action==="accepted"||action==="corrected")){opportunityReviewSetMessage("汇总项缺少事实 ID，只能标记待补证或驳回",true);return}
 if((action==="accepted"||action==="corrected")&&!selectedLabel){opportunityReviewSetMessage("请先选择最终统一标签",true);document.querySelector("#opportunity-review-label")?.focus();return}
 if(["corrected","rejected","needs_evidence"].includes(action)&&!note){opportunityReviewSetMessage("请填写人工依据，说明修正、驳回或补证原因",true);document.querySelector("#opportunity-review-note")?.focus();return}
 opportunityReviewState.saving=true;opportunityReviewState.error="";opportunityReviewState.message="正在保存人工判断…";renderOpportunityReviewDialog();
 try{
  const data=await api("/api/opportunity-map/manual-reviews",{method:"POST",body:JSON.stringify({documentId:queue.document?.documentId||opportunityEvidenceState.document?.documentId,runId:queue.runId||opportunityEvidenceState.result?.runId||"",itemIds,action,selectedLabel,note})});
  opportunityReviewState.queue=data.queue;
  itemIds.forEach(id=>{opportunityReviewState.selectedIds.delete(id);opportunityReviewState.drafts.delete(id)});
  const counts=data.queue?.counts||{};
  opportunityReviewState.message=action==="accepted"||action==="corrected"?"已进入双模型复核队列；可立即验证并更新已确认标签，不必等待其他标签确认。":action==="needs_evidence"?"已标记待补证，不会进入机会地图。":"已驳回该事实，不会进入机会地图。";
  if(opportunityEvidenceState.document){opportunityEvidenceState.document={...opportunityEvidenceState.document,manualReviewCount:Number(counts.blocking||0)};saveOpportunityDocument(opportunityEvidenceState.document)}
  let items=opportunityReviewFilteredItems();
  if(!items.length&&opportunityReviewState.filter==="pending"&&counts.pendingRecheck){opportunityReviewState.filter="pending_recheck";items=opportunityReviewFilteredItems()}
  opportunityReviewState.selectedId=items[0]?.id||"";
  renderOpportunityEvidence();
 }catch(err){opportunityReviewState.error=err.message||"人工确认保存失败"}finally{opportunityReviewState.saving=false;renderOpportunityReviewDialog()}
}
function runOpportunityManualRecheck(){
 const pending=Number(opportunityReviewState.queue?.counts?.pendingRecheck||0);
 if(!pending)return;
 const generate=document.querySelector("#opportunity-generate-button");
 if(!opportunityEvidenceState.competitorSourceText.trim()){opportunityReviewSetMessage("请先在证据链中填写竞品官网产品页，再运行双旗舰复核",true);return}
 if(!generate||generate.disabled){opportunityReviewSetMessage("机会地图当前无法启动复核，请等待正在运行的任务结束",true);return}
 opportunityReviewState.message="";opportunityReviewState.error="";
 document.querySelector("#opportunity-review-dialog")?.close();
 requestAnimationFrame(()=>{const button=document.querySelector("#opportunity-generate-button");if(button&&!button.disabled)button.click()});
}
function opportunityCompetitorProductMarkup(run){
 const fallback=source=>({model:String(source?.model||"竞品"),statusLabel:source?.status==="verified"?"官网已核验":"待补官网证据",className:source?.status==="verified"?"verified":"manual",sourceUrl:String(source?.finalUrl||source?.url||""),coreProductStrengths:source?.status==="verified"?(source?.coreProductStrengths||[]).filter(item=>item?.label&&item?.claim):[],detail:source?.status==="verified"?"已从双模型共同引用的官网事实中提炼核心产品力。":String(source?.failureReason||"官网事实尚未达到外显标准。")});
 const summaries=(run?.competitorProducts||[]).map(source=>typeof competitorProductView==="function"?competitorProductView(source):fallback(source)).filter(source=>source.model);
 if(!summaries.length)return"";
 if(!summaries.some(source=>source.model===opportunityCompetitorPopoverModel))opportunityCompetitorPopoverModel="";
 return `<section class="opportunity-competitor-products" aria-label="竞品官网核心产品力"><div class="opportunity-competitor-products-head"><span>竞品官网核心产品力</span><small>点击车型查看双模型验证后的 NSR 属性产品力</small></div><div class="opportunity-competitor-product-list">${summaries.map(source=>{const open=source.model===opportunityCompetitorPopoverModel,strengths=source.coreProductStrengths||[];return`<article class="opportunity-competitor-product ${escapeAttr(source.className)} ${open?"open":""}"><button type="button" class="opportunity-competitor-trigger" data-opportunity-competitor-model="${escapeAttr(source.model)}" aria-expanded="${open?"true":"false"}" aria-controls="opportunity-competitor-popover-${escapeAttr(source.model)}"><span><b>${escapeHtml(source.model)}</b><small>${escapeHtml(source.statusLabel)}</small></span><em>${strengths.length?`${strengths.length} 个已验证属性`:"待补证"}</em></button>${open?`<div class="opportunity-competitor-popover" id="opportunity-competitor-popover-${escapeAttr(source.model)}" role="status"><div class="opportunity-competitor-popover-head"><div><span>${escapeHtml(source.model)}</span><b>核心产品力</b></div><button type="button" data-opportunity-competitor-close="${escapeAttr(source.model)}" aria-label="关闭${escapeAttr(source.model)}产品力气泡">×</button></div>${strengths.length?`<ul>${strengths.map(strength=>`<li><strong>${escapeHtml(strength.label)}</strong><p>${escapeHtml(strength.claim)}</p><small>双旗舰模型共同引用 · 事实强度 ${(Number(strength.factStrength||0)*100).toFixed(0)}%</small></li>`).join("")}</ul>`:`<p class="opportunity-competitor-empty">${escapeHtml(source.detail)}</p>`}${source.sourceUrl?`<a href="${escapeAttr(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">查看官网原页</a>`:""}</div>`:""}</article>`}).join("")}</div></section>`;
}
function renderOpportunityEvidence(){
 const box=document.querySelector("#opportunity-evidence-workbench");if(!box)return;
 const doc=opportunityEvidenceState.document,run=opportunityEvidenceState.result,job=opportunityEvidenceState.job;
 const jobView=typeof opportunityJobView==="function"?opportunityJobView(job):{statusLabel:"待运行",buttonLabel:"生成/更新机会地图",detail:"",elapsedLabel:"",activeStage:-1,progress:0};
 const resultView=typeof opportunityResultView==="function"?opportunityResultView(run):{statusLabel:run?.status==="completed"?"双模型交叉验证完成":"需人工确认",detail:"",className:run?.status==="completed"?"ok":"warn"};
 const running=opportunityJobRunning(job)||opportunityEvidenceState.loading;
 const documentFactCount=Number(doc?.factCount??doc?.facts?.length??0);
 const documentManualCount=Number(doc?.manualReviewCount??doc?.manualReviewItems?.length??0);
 const manual=(run?.validation?.manualItems||[]).length+documentManualCount;
 const modelStatus=run?resultView.statusLabel:job?.status?jobView.statusLabel:"待运行";
 const modelStatusClass=run?resultView.className:job?.status==="completed"?"ok":running?"active":"warn";
 const competitorStatus=running?"核验中":run?`已核验 ${run.competitorSources?.filter(item=>item.status==="verified").length||0}/${run.competitorSources?.length||0} 个`:"待核验";
 const jobMarkup=opportunityJobProgressMarkup(job,jobView),competitorProductMarkup=opportunityCompetitorProductMarkup(run);
 box.setAttribute("aria-busy",running?"true":"false");
 box.innerHTML=`<div class="opportunity-evidence-copy"><strong>证据链：产品事实 × 市场认知 × 传播热度</strong><small>本品使用 PDF / Word / PPT 人工投喂；竞品仅采信指定官网页面。属性级声量/互动缺失时不会用车型总量代填。</small><div class="opportunity-evidence-status"><span class="${doc?"ok":"warn"}">本品资料：${doc?`已解析 ${documentFactCount} 个事实`:`未上传`}</span><span class="${run?.competitorSources?.length&&!running?"ok":"warn"}">竞品官网：${competitorStatus}</span><span class="${modelStatusClass}">MMN双模型：${escapeHtml(modelStatus)}</span><span class="${manual?"warn":""}">人工确认：${manual} 项</span></div>${competitorProductMarkup}</div><div class="opportunity-evidence-controls"><input id="opportunity-own-file" type="file" accept=".pdf,.doc,.docx,.ppt,.pptx" aria-label="上传本品PDF或Office产品资料"><textarea id="opportunity-official-sources" placeholder="竞品官网，一行一个：车型|https://官方产品页地址"></textarea><div class="opportunity-evidence-actions"><button type="button" id="opportunity-upload-button" class="secondary" ${running?"disabled":""}>解析本品资料</button><button type="button" id="opportunity-generate-button" ${!doc||running?"disabled":""}>${running?'<span class="opportunity-button-spinner" aria-hidden="true"></span>':""}${escapeHtml(jobView.buttonLabel)}</button>${manual&&!running?`<button type="button" id="opportunity-review-button" class="secondary">人工确认</button>`:""}</div></div>${jobMarkup}${opportunityEvidenceState.error?`<p class="opportunity-evidence-manual error" role="alert">${escapeHtml(opportunityEvidenceState.error)}</p>`:manual&&!running?`<p class="opportunity-evidence-manual">${escapeHtml(resultView.detail||`有 ${manual} 个产品点需要人工确认：版本冲突、标签歧义、证据不足或双模型分歧不会自动发布。`)}</p>`:""}`;
 const file=document.querySelector("#opportunity-own-file"),sourceInput=document.querySelector("#opportunity-official-sources"),upload=document.querySelector("#opportunity-upload-button"),generate=document.querySelector("#opportunity-generate-button"),reviewButton=document.querySelector("#opportunity-review-button"),controls=box.querySelector(".opportunity-evidence-controls"),actions=box.querySelector(".opportunity-evidence-actions");
 const fileField=document.createElement("label");fileField.className="opportunity-source-field";fileField.innerHTML='<span class="opportunity-source-label"><b>1. 本品产品资料</b><em>PDF / Word / PPT</em></span>';fileField.append(file);fileField.insertAdjacentHTML("beforeend",'<small>上传本品白皮书、配置表或产品说明文件。</small>');controls.insertBefore(fileField,actions);
 const competitorField=document.createElement("label");competitorField.className="opportunity-source-field opportunity-competitor-field";competitorField.innerHTML='<span class="opportunity-source-label" id="opportunity-official-label"><b>2. 竞品官网产品页</b><em class="required">生成前填写</em></span>';sourceInput.value=opportunityEvidenceState.competitorSourceText||"";sourceInput.placeholder="例如：小米YU7 https://品牌官网/车型产品页";sourceInput.setAttribute("aria-labelledby","opportunity-official-label");competitorField.append(sourceInput);competitorField.insertAdjacentHTML("beforeend",'<small>一行一个竞品：车型名称 + 空格 + 官网产品页链接，也兼容“车型|链接”。请填写具体车型页，不要填搜索结果页。</small>');controls.insertBefore(competitorField,actions);
 const syncCompetitorSource=()=>{opportunityEvidenceState.competitorSourceText=saveOpportunitySourceText(sourceInput.value);if(generate){generate.disabled=!opportunityEvidenceState.document||!sourceInput.value.trim()||running;generate.title=!sourceInput.value.trim()?"请先填写至少一个竞品官网产品页":""}};sourceInput.oninput=syncCompetitorSource;syncCompetitorSource();
 box.querySelectorAll("[data-opportunity-competitor-model]").forEach(button=>button.onclick=()=>{opportunityCompetitorPopoverModel=opportunityCompetitorPopoverModel===button.dataset.opportunityCompetitorModel?"":button.dataset.opportunityCompetitorModel;renderOpportunityEvidence();if(opportunityCompetitorPopoverModel)document.querySelector(`[data-opportunity-competitor-close="${CSS.escape(opportunityCompetitorPopoverModel)}"]`)?.focus()});
 box.querySelectorAll("[data-opportunity-competitor-close]").forEach(button=>button.onclick=()=>{opportunityCompetitorPopoverModel="";renderOpportunityEvidence();document.querySelector(`[data-opportunity-competitor-model="${CSS.escape(button.dataset.opportunityCompetitorClose)}"]`)?.focus()});
 if(upload)upload.onclick=async()=>{const selected=file?.files?.[0];if(!selected){toast("请先选择本品 PDF、Word 或 PPT 文件");return}const contextKey=opportunityCacheContext().key;opportunityEvidenceState.loading=true;opportunityEvidenceState.error="";renderOpportunityEvidence();try{const params=new URLSearchParams({filename:selected.name,brand:state.config.brand||"",model:state.config.model||"",edition:activeEdition()});const res=await fetch(`/api/opportunity-map/own-document?${params}`,{method:"POST",headers:authHeaders(),body:await selected.arrayBuffer()});const json=await res.json();if(!json.ok)throw new Error(json.error||"产品资料解析失败");saveOpportunityDocument(json.document,contextKey);if(contextKey!==opportunityCacheContext().key)return;opportunityEvidenceState.document=json.document;toast(`本品资料已解析：${json.document.facts?.length||0} 个事实`)}catch(err){if(contextKey===opportunityCacheContext().key){opportunityEvidenceState.error=err.message;toast(`本品资料解析失败：${err.message}`)}}finally{if(contextKey===opportunityCacheContext().key){opportunityEvidenceState.loading=false;renderOpportunityEvidence();renderOpportunityMap(analysis())}}};
 if(generate)generate.onclick=async()=>{
  const contextKey=opportunityCacheContext().key;
  opportunityEvidenceState.error="";
  try{
   const parsedSources=parseOpportunityCompetitorSources(opportunityEvidenceState.competitorSourceText);
   if(parsedSources.errors.length){const first=parsedSources.errors[0];opportunityEvidenceState.error=`第 ${first.line} 行：${first.reason}。原文：${first.text}`;toast("竞品官网地址格式需要检查");renderOpportunityEvidence();document.querySelector("#opportunity-official-sources")?.focus();return}
   opportunityEvidenceState.loading=true;
   opportunityEvidenceState.job={status:"queued",stage:"official_sources",progress:1,message:`任务已提交，准备核验 ${parsedSources.items.length} 个竞品官网`,elapsedSeconds:0};
   renderOpportunityEvidence();
   toast("机会地图任务已提交，双旗舰模型将在后台独立分析");
   const data=await api("/api/opportunity-map/generate",{method:"POST",body:JSON.stringify({documentId:opportunityEvidenceState.document.documentId,edition:activeEdition(),competitorSources:parsedSources.items,marketSignals:opportunityMarketSignals()})});
   saveOpportunityJobId(data.jobId,contextKey);
   if(contextKey!==opportunityCacheContext().key)return;
   opportunityEvidenceState.job=data.job;
   opportunityEvidenceState.jobId=data.jobId;
   renderOpportunityEvidence();
   const result=await waitForOpportunityMapJob(data.jobId,contextKey);
   if(!result||contextKey!==opportunityCacheContext().key)return;
   opportunityEvidenceState.result=result;
   toast(result.status==="completed"?"机会地图已完成双模型交叉验证":"机会地图已生成，部分产品点待人工确认");
  }catch(err){
   if(contextKey!==opportunityCacheContext().key)return;
   opportunityEvidenceState.error=err.message;
   if(!opportunityEvidenceState.job||opportunityJobRunning(opportunityEvidenceState.job))opportunityEvidenceState.job={...(opportunityEvidenceState.job||{}),status:"failed",stage:"failed",progress:100,error:err.message,message:"机会地图生成失败"};
   opportunityEvidenceState.jobId="";
   saveOpportunityJobId("",contextKey);
   toast(`机会地图生成失败：${err.message}`);
  }finally{
   if(contextKey===opportunityCacheContext().key){opportunityEvidenceState.loading=false;render()}
  }
 };
 if(reviewButton)reviewButton.onclick=()=>openOpportunityReview(reviewButton);
}
function renderDashboardTopicPlanner(a=analysis()){
 const box=document.querySelector("#dashboard-topic-plan");
 if(!box)return;
 const model=state.config.model;
 const competitor=sellingPointPlanningCompetitors().join(" / ")||"核心竞品";
 const stage=document.querySelector("#dashboard-topic-stage");
 const selectedPhase=marketingModelPhase().selected;if(stage&&selectedPhase)stage.value=tCycleTopicStage(selectedPhase);
 if(stage)state.config.stage=stage.value||"周期待设置";
 if(dashboardTopicPlanState.loading){
  box.innerHTML=`<div class="topic-plan-loading"><b>MMN正在生成车型传播选题规划</b><span>${model} · ${competitor} · ${state.config.targetIdentity||"目标人群"}</span></div>`;
  return;
 }
 if(dashboardTopicPlanState.result){
  box.innerHTML=renderTopicPlanPanel(dashboardTopicPlanState.result);
  return;
 }
 const labels=(a.labels||[]).filter(x=>x.priority>0).slice(0,5).map(x=>x.label).join(" / ")||"核心卖点";
	 box.innerHTML=`<div class="topic-plan-empty"><b>${model} 选题规划待生成</b><span>当前诊断重点：${escapeHtml(labels)}｜竞品：${escapeHtml(competitor||"待补充")}</span></div>`;
}
function dashboardTopicPlanningPayload({model,stage,platform,goal,report,competitors,coreSellingPoints}){
 return{org_id:session?.org_id,user_id:session?.user_id,edition:activeEdition(),project:{...strategyProjectContext(),model,stage,launchStage:stage,communicationPlatform:platform},launchStage:stage,stage,communicationPlatform:platform,platforms:[platform],coreSellingPoints,competitors,budget:state.config.budget,targetAudience:state.config.targetIdentity,communicationGoal:goal,question:`${model} ${stage} ${platform}车型传播选题规划`,signal:report};
}
async function buildFallbackDashboardTopicPlan(payload,modelText="",modelLabel="MMN深度策略"){
 const data=await api("/api/topic-planning/run",{method:"POST",body:JSON.stringify(payload)});
 const plan=data.topicPlan;
 if(!plan)throw new Error("topic_planning_engine 未返回选题规划。");
 plan.modelNarrative=modelText||"MMN深度策略已完成判断；结构化选题由 topic_planning_engine 基于当前车型、阶段、目标、竞品和预算自动补齐。";
 plan.modelLabel=`${modelLabel} + topic_planning_engine`;
 return plan;
}
function localTopicFormats(platform){
 if(platform==="小红书")return["场景图文笔记","体验清单","口碑短视频"];
 if(platform==="B站")return["深度评测视频","技术解析视频","长周期用车报告"];
 return["竖屏短视频","直播切片","热点话题视频"];
}
function localTopicItem(id,topic,stage,platform,goal,priority,competitors){
 const comp=competitors.length?competitors.join(" / "):"核心竞品";
 return{id,topic,taxonomy:["媒体角度","单车类",stage,platform,goal],communicationStages:[stage],applicableModels:["全车型"],contentGoals:[goal],userDecisionStages:["兴趣建立","方案比较","下单转化"],creatorTypes:["专业汽车评测达人","家庭场景KOC","车主口碑达人"],recommendedFormats:localTopicFormats(platform),priority,fitReason:`围绕${state.config.model}在${stage}面向${platform}建立核心购买理由，把${comp}对比、真实场景和转化疑虑拆成平台适配内容。`,conditions:["当前车型、传播阶段、平台与目标已明确","需要快速形成选题排期"],exclusions:["缺少车型定位时不建议直接投放","重大舆情期需先做风险复核"]};
}
function buildLocalDashboardTopicPlan(payload,reason=""){
 const summary=payload.project||{},model=summary.model||state.config.model||"当前车型",stage=payload.launchStage||summary.stage||"上市中",platform=payload.communicationPlatform||"抖音/视频号",goal=payload.communicationGoal||"建立核心购买理由",competitors=payload.competitors||[];
 const topics=[
  localTopicItem("local_compare",`产品竞争分析：${model} 对比 ${competitors[0]||"核心竞品"}`,stage,platform,"竞品比较",96,competitors),
  localTopicItem("local_scene",`${model} 家庭场景真实用车选题`,stage,platform,"场景种草",92,competitors),
  localTopicItem("local_owner",`${model} 车主口碑与高频疑虑澄清`,stage,platform,"口碑验证",90,competitors),
  localTopicItem("local_cost",`${model} 用车成本、权益与保值解释`,stage,platform,"转化承接",86,competitors),
  localTopicItem("local_tech",`${model} 核心技术与智能体验拆解`,stage,platform,"卖点教育",84,competitors),
  localTopicItem("local_store",`${model} 到店试驾与下订决策内容`,stage,platform,"到店转化",82,competitors)
 ];
 const phaseStrategy=`${model}在${stage}以${platform}为主阵地，先用竞品对比建立入口，再用平台适配的场景实测和车主口碑补齐信任，最后用权益和试驾内容承接转化。`;
 return{engine:"local_topic_planning_fallback",taxonomyVersion:"2026-07-10.mmn.local-topic-fallback.v2",inputSummary:{brand:summary.brand||state.config.brand||"",model,launchStage:stage,communicationPlatform:platform,coreSellingPoints:payload.coreSellingPoints||[],competitors,budgetTier:String(payload.budget||state.config.budget||"预算待定"),targetAudience:payload.targetAudience||state.config.targetIdentity||"目标购车人群",communicationGoal:goal},taxonomy:topics,selectedTopics:topics,phases:[{phase:stage,strategy:phaseStrategy,topics:topics.slice(0,4)}],creatorMatches:topics.slice(0,5).map((x,i)=>({topic:x.topic,primaryCreatorType:x.creatorTypes[i%3],backupCreatorType:x.creatorTypes[(i+1)%3],brief:`在${platform}用${x.recommendedFormats[0]}讲清${x.topic}；必须出现车型、场景、对比对象和明确购买理由。`})),schedule:topics.slice(0,6).map((x,i)=>({week:`第${i+1}周`,phase:stage,topic:x.topic,format:x.recommendedFormats[i%3],kpi:i<2?"搜索讨论与完播率":"互动咨询与到店线索"})),strategyConclusion:`${phaseStrategy}${reason?` 本次为前端兜底规划，原因：${reason}`:""}`,modelNarrative:"当前入口未稳定命中MMN后端接口，页面先基于车型、传播阶段、平台、目标、竞品和预算生成可执行选题；接口恢复后仍会优先使用旗舰策略模型结果。",modelLabel:"前端兜底选题规划"};
}
async function runDashboardTopicPlanning(){
	 const model=syncDashboardModelFromControls();
	 const stage=document.querySelector("#dashboard-topic-stage")?.value||state.config.stage||"上市中";
	 const platform=document.querySelector("#dashboard-topic-platform")?.value||"抖音/视频号";
	 const goal=document.querySelector("#dashboard-topic-goal")?.value?.trim()||"建立核心购买理由并抢占竞品对比搜索";
	 state.config.stage=stage;
 dashboardTopicPlanState={loading:true,result:null,error:""};
 renderDashboardTopicPlanner();
 try{
	  const report=reportPayload();
	  const competitors=sellingPointPlanningCompetitors();
	  const coreSellingPoints=(report.knowhow||[]).slice(0,8).map(x=>x.label||x.message).filter(Boolean);
	  const planningPayload=dashboardTopicPlanningPayload({model,stage,platform,goal,report,competitors,coreSellingPoints});
		  const question=[
	   `${model} ${stage}车型传播选题规划`,
	   `传播平台：${platform}`,
	   `传播目标：${goal}`,
	   `核心卖点：${coreSellingPoints.join("、")||state.config.project}`,
   `核心竞品：${competitors.join("、")||"待补充"}`,
	   `目标人群：${state.config.targetIdentity}`,
	   "请使用MMN深度策略链路输出分阶段选题、达人匹配、内容形式和排期，并给出明确策略结论。"
	  ].join("\n");
	  const data=await api("/api/agents/run",{method:"POST",body:JSON.stringify({...planningPayload,question,project:strategyProjectContext(),references:ragSearch({query:[model,...competitors,stage,goal,"车型传播选题","达人匹配","内容排期"].join(" "),limit:8}),mode:"deep",task_type:"strategy_reasoning"})});
	  const plan=data.topicPlan||data.agentRun?.final_output?.topicPlan||await buildFallbackDashboardTopicPlan(planningPayload,data.text,data.modelLabel);
	  plan.modelNarrative=plan.modelNarrative||data.text||"";
	  plan.modelLabel=plan.modelLabel||data.modelLabel||"MMN深度策略";
	  dashboardTopicPlanState={loading:false,result:plan,error:""};
  save();
  renderDashboardTopicPlanner();
  toast("MMN深度策略已生成车型传播选题规划");
	 }catch(err){
  const report=reportPayload();
  const competitors=sellingPointPlanningCompetitors();
  const coreSellingPoints=(report.knowhow||[]).slice(0,8).map(x=>x.label||x.message).filter(Boolean);
  const fallback=buildLocalDashboardTopicPlan(dashboardTopicPlanningPayload({model,stage,platform,goal,report,competitors,coreSellingPoints}),err.message);
  dashboardTopicPlanState={loading:false,result:fallback,error:""};
  renderDashboardTopicPlanner();
  toast("接口暂未命中，已先生成本地兜底选题规划");
 }
}
function renderModelJudgmentWorkbench(){
 const box=document.querySelector("#model-judgment-result");if(!box)return;
 const items=modelJudgmentsFor(state.config.model).slice(0,5);
 box.innerHTML=items.length?`<div class="model-judgment-list">${items.map(item=>`<article class="model-judgment-card"><div><span>${escapeHtml(item.dimension||"综合判断")} · ${escapeHtml(item.brand_name||state.config.brand)}</span><b>${escapeHtml(item.model_name||state.config.model)}</b></div><p>${renderModelHighlight(item.viewpoint||item.source_text||"",item,"viewpoint")}</p><dl><dt>归因</dt><dd>${renderModelHighlight(item.attribution||"待补充",item,"attribution")}</dd><dt>策略动作</dt><dd>${renderModelHighlight(item.strategy_implication||"待补充",item,"strategy_implication")}</dd><dt>还缺证据</dt><dd>${renderModelHighlight(item.evidence_needed||"待补充",item,"evidence_needed")}</dd></dl><small>${item.highlight_status==="model_verified"?"✓ 模型认定后已标注重点 · ":""}${(item.tags||[]).slice(0,8).map(x=>`#${escapeHtml(x)}`).join(" ")}｜${escapeHtml((item.created_at||item.createdAt||"").slice(0,10))}</small></article>`).join("")}</div>`:`<p class="empty">还没有沉淀到 ${escapeHtml(state.config.model)} 的车型判断。你可以直接输入一句判断，MMN会自动拆成车型资产。</p>`;
}
const emotionQuadrantDefinitions=[
 {key:"active-positive",title:"高唤醒正向",subtitle:"正向效价 · 高表达强度"},
 {key:"steady-positive",title:"稳态正向",subtitle:"正向效价 · 稳定认可"},
 {key:"concern-negative",title:"疑虑负向",subtitle:"负向效价 · 决策疑虑"},
 {key:"damaged-negative",title:"受损负向",subtitle:"负向效价 · 高风险受损"}
];
function emotionQuadrantData(rows){
 const valence={兴奋:1,惊喜:1,期待:.65,信任:.8,认可:.75,自豪:1,怀疑:-.45,焦虑:-.65,嘲讽:-.75,失望:-.85,愤怒:-1,后悔:-.9};
 const activation={兴奋:1,惊喜:.95,自豪:.85,期待:.4,信任:.25,认可:.3,怀疑:.35,焦虑:.65,嘲讽:.75,失望:.7,愤怒:1,后悔:.85};
 const grouped=new Map();
 rows.forEach(r=>{if(!r[4])return;const samples=+r[8]||0,item=grouped.get(r[4])||{label:r[4],category:r[3],samples:0,valenceTotal:0,activationTotal:0,emotions:new Set()};item.samples+=samples;item.valenceTotal+=(valence[r[5]]??0)*samples;item.activationTotal+=(activation[r[5]]??.5)*samples;item.emotions.add(r[5]);grouped.set(r[4],item)});
 const items=[...grouped.values()].map(x=>({...x,valence:x.samples?x.valenceTotal/x.samples:0,activation:x.samples?x.activationTotal/x.samples:0}));
 if(!items.length)return new Map(emotionQuadrantDefinitions.map(q=>[q.key,[]]));
 const byValence=[...items].sort((a,b)=>b.valence-a.valence||b.samples-a.samples),positiveCount=items.length>=4?Math.max(2,Math.min(items.length-2,Math.ceil(items.length/2))):Math.ceil(items.length/2),positive=byValence.slice(0,positiveCount),negative=byValence.slice(positiveCount);
 const split=(source,metric,descending=true)=>{const sorted=[...source].sort((a,b)=>(descending?b[metric]-a[metric]:a[metric]-b[metric])||b.samples-a.samples),cut=Math.max(1,Math.ceil(sorted.length/2));return[sorted.slice(0,cut),sorted.slice(cut)]};
 const [active,steady]=split(positive,"activation",true),[damaged,concern]=split(negative,"activation",true),result=new Map([["active-positive",active],["steady-positive",steady],["concern-negative",concern],["damaged-negative",damaged]]);
 emotionQuadrantDefinitions.forEach(q=>result.set(q.key,(result.get(q.key)||[]).sort((a,b)=>b.samples-a.samples).slice(0,3)));
 return result;
}
function renderSummaryAttributeMatrix(rows,models,source){
 const selectedModels=models.filter(Boolean),byLabel=new Map();
 rows.forEach(r=>{const score=nullableNumber(r[14]);if(r[2]!==source||!selectedModels.includes(r[0])||!r[4]||score===null)return;const item=byLabel.get(r[4])||{label:r[4],category:r[3],scores:new Map()};const values=item.scores.get(r[0])||[];values.push(score);item.scores.set(r[0],values);byLabel.set(r[4],item)});
 const items=[...byLabel.values()];
 if(!items.length)return`<div class="empty-state">当前平台没有可展示的真实属性 NSR。</div>`;
 const columns=`minmax(160px,1.2fr) repeat(${Math.max(selectedModels.length,1)},minmax(125px,1fr))`;
 return`<div class="summary-attribute-head" style="grid-template-columns:${columns}"><b>产品点</b>${selectedModels.map(model=>`<b>${escapeHtml(model)}</b>`).join("")}</div><div class="summary-attribute-body">${items.map(item=>`<div class="summary-attribute-row" style="grid-template-columns:${columns}"><div class="summary-attribute-label"><b>${escapeHtml(item.label)}</b><small>${escapeHtml(item.category)}</small></div>${selectedModels.map(model=>{const score=meanNumbers(item.scores.get(model)||[]);if(score===null)return`<div class="summary-attribute-cell missing">—</div>`;const percent=score*100,tone=score>=.25?"positive":score<0?"negative":"neutral";return`<button type="button" class="summary-attribute-cell ${tone}" data-summary-attribute-model="${escapeAttr(model)}" data-summary-attribute-label="${escapeAttr(item.label)}" aria-label="查看${escapeAttr(item.label)}本品与竞品属性对比，${escapeAttr(model)} ${percent.toFixed(1)}%"><span class="summary-attribute-value">${percent.toFixed(1)}%</span><i style="width:${Math.min(Math.abs(percent),100).toFixed(1)}%"></i></button>`}).join("")}</div>`).join("")}</div>`;
}
function summaryAttributeOpportunityItems(rows,models,source){
 const ownModel=state.config.model,competitors=models.filter(model=>model&&model!==ownModel),byLabel=new Map();
 rows.forEach(row=>{const score=nullableNumber(row[14]);if(row[2]!==source||!models.includes(row[0])||!row[4]||score===null)return;const item=byLabel.get(row[4])||{label:row[4],category:row[3]||"其他赛道",modelScores:new Map(),impacts:[]};const values=item.modelScores.get(row[0])||[];values.push(score);item.modelScores.set(row[0],values);if(row[0]===ownModel&&nullableNumber(row[9])!==null)item.impacts.push(nullableNumber(row[9]));byLabel.set(row[4],item)});
 return[...byLabel.values()].map(item=>{const ownNsr=meanNumbers(item.modelScores.get(ownModel)||[]),competitorScores=competitors.map(model=>meanNumbers(item.modelScores.get(model)||[])).filter(value=>value!==null),recordedMean=meanNumbers(competitorScores),benchmark=nullableNumber(state.summaryAttributeBenchmark?.[source]?.[item.label]),competitorMean=recordedMean??benchmark,gap=ownNsr!==null&&competitorMean!==null?ownNsr-competitorMean:null,impact=meanNumbers(item.impacts)??3,evidence=attributeEvidenceStatus(rows,item.label,ownModel),priority=impact*20+Math.max(0,-(gap??0))*80+Math.max(0,-(ownNsr??0))*60+(evidence.tone==="risk"||evidence.tone==="conflict"?18:0);return{...item,ownNsr,competitorMean,gap,impact,evidence,priority,benchmarkUsed:recordedMean===null&&benchmark!==null}}).filter(item=>item.ownNsr!==null).sort((left,right)=>right.priority-left.priority||left.label.localeCompare(right.label,"zh-CN"));
}
function summaryAttributeCategoryTone(category,label){
 const text=`${category||""} ${label||""}`;
 if(/价格|权益/.test(text))return"price";
 if(/动力|操控/.test(text))return"performance";
 if(/外观|内饰|造型|设计/.test(text))return"design";
 if(/安全|质量/.test(text))return"safety";
 if(/智能|辅助|驾驶|座舱/.test(text))return"technology";
 if(/空间|舒适/.test(text))return"comfort";
 return"other";
}
function summaryAttributeJudgment(item){
 if(item.ownNsr<0&&item.gap!==null&&item.gap<0)return`${item.label}认知为负且落后竞品，是当前优先修复项。`;
 if(item.gap!==null&&item.gap<=-.1)return`${item.label}相对竞品存在明显差距，需要补强证据与传播表达。`;
 if(item.ownNsr>=.25&&item.gap!==null&&item.gap>=0)return`${item.label}已形成相对优势，可作为当前传播资产持续放大。`;
 if(item.evidence.tone==="conflict")return`${item.label}在不同来源间结论冲突，需要先核查来源与样本口径。`;
 return`${item.label}处于中性观察区，需要结合来源覆盖和竞品表现继续判断。`;
}
function summaryAttributeGapBubbleSize(gap){const value=gap===null?NaN:Number(gap),normalized=Number.isFinite(value)?Math.min(Math.abs(value)/.55,1):0;return Math.round(58+Math.sqrt(normalized)*58)}
function resetSummaryQuadrantCollapse(){summaryAttributeCollapsedQuadrants.clear();summaryAttributeExpandedQuadrants.clear()}
function syncSummaryQuadrantOverflow(a){let changed=false;document.querySelectorAll("[data-summary-quadrant-cloud]").forEach(cloud=>{const key=cloud.dataset.summaryQuadrantCloud,count=Number(cloud.dataset.summaryQuadrantCount||0);if(count<2||summaryAttributeCollapsedQuadrants.has(key)||summaryAttributeExpandedQuadrants.has(key))return;const readableHeight=Math.max(190,Math.min(340,Math.round(cloud.clientWidth*.9)));if(cloud.scrollHeight>readableHeight+1){summaryAttributeCollapsedQuadrants.add(key);changed=true}});if(changed)renderSummaryHeatDashboard(a)}
function renderSummaryAttributeOpportunityMap(rows,models,source){
 const ownModel=state.config.model,items=summaryAttributeOpportunityItems(rows,models,source);
 if(!items.length)return`<div class="empty-state">当前平台没有可展示的真实属性 NSR。</div>`;
 if(!items.some(item=>item.label===summaryAttributeActiveLabel))summaryAttributeActiveLabel=items[0].label;
 const active=items.find(item=>item.label===summaryAttributeActiveLabel)||items[0],bubbleInputs=items.map(item=>{const size=summaryAttributeGapBubbleSize(item.gap),gap=item.gap??0;return{...item,left:50+Math.max(-1,Math.min(1,item.ownNsr))*43,bottom:50+Math.max(-1,Math.min(1,gap))*43,w:size,h:size,quadrantX:item.ownNsr<0?"left":item.ownNsr>0?"right":"axis",quadrantY:gap>0?"high":gap<0?"low":"axis"}}),placed=layoutBubbles(bubbleInputs,720,430),sources=state.importQuality?.attributeNsrSources||[...new Set(rows.map(row=>row[2]).filter(Boolean))],competitors=models.filter(model=>model!==ownModel),scoreFor=(model,platform)=>meanNumbers(rows.filter(row=>row[0]===model&&row[2]===platform&&row[4]===active.label).map(row=>nullableNumber(row[14])).filter(value=>value!==null)),sourceRows=sources.map(platform=>{const own=scoreFor(ownModel,platform),competitor=meanNumbers(competitors.map(model=>scoreFor(model,platform)).filter(value=>value!==null));return{platform,own,competitor,gap:own!==null&&competitor!==null?own-competitor:null}}),gapText=active.gap===null?"—":`${active.gap>=0?"领先":"落后"} ${Math.abs(active.gap*100).toFixed(1)}%`,evidenceRows=sourceRows.map(item=>`<div class="summary-attribute-evidence-row"><b>${escapeHtml(item.platform)}</b><span>本品 ${summaryNsrDisplay(item.own)}</span><span>竞品均值 ${summaryNsrDisplay(item.competitor)}</span><strong class="${item.gap!==null&&item.gap<0?"risk":""}">${item.gap===null?"不可比":`${item.gap>=0?"领先":"落后"} ${Math.abs(item.gap*100).toFixed(1)}%`}</strong></div>`).join("");
 return`<div class="summary-attribute-opportunity"><section class="summary-attribute-map"><header><div><span>车型属性机会总览</span><b>认知属性机会地图</b></div><small>点击气泡查看该标签专项诊断</small></header><div class="summary-attribute-bubble-chart" role="group" aria-label="${escapeAttr(ownModel)}认知属性机会地图"><div class="summary-attribute-axis horizontal" aria-hidden="true"><span>负向 NSR</span><span>正向 NSR</span></div><div class="summary-attribute-axis vertical" aria-hidden="true"><span>领先竞品</span><span>落后竞品</span></div>${placed.map(item=>`<button type="button" class="summary-attribute-bubble ${summaryAttributeCategoryTone(item.category,item.label)} ${item.label===active.label?"active":""}" data-summary-attribute-bubble="${escapeAttr(item.label)}" aria-pressed="${item.label===active.label?"true":"false"}" aria-label="查看${escapeAttr(item.label)}专项诊断，NSR ${summaryNsrDisplay(item.ownNsr)}，${item.gap===null?"暂无竞品对比":`${item.gap>=0?"领先":"落后"}竞品${Math.abs(item.gap*100).toFixed(1)}%`}" style="--bubble-x:${item.x.toFixed(2)}%;--bubble-y:${item.y.toFixed(2)}%;--bubble-size:${item.w}px"><span>${escapeHtml(item.label)}</span><small>${summaryNsrDisplay(item.ownNsr)}</small></button>`).join("")}</div><footer><span>气泡大小＝与竞品 NSR 差距</span><span>颜色＝一级赛道</span><span>边框＝当前选中</span><b>差距越大，气泡越大；大小不代表声量。</b></footer></section><aside class="summary-attribute-diagnosis" aria-live="polite"><header><div><span>${escapeHtml(active.category)}</span><b>${escapeHtml(active.label)} · 专项诊断</b></div><em class="${active.evidence.tone}">${escapeHtml(active.evidence.label)} · ${escapeHtml(active.evidence.note)}</em></header><div class="summary-attribute-kpis"><article><span>本品 NSR</span><strong class="${active.ownNsr<0?"risk":""}">${summaryNsrDisplay(active.ownNsr)}</strong></article><article><span>竞品均值</span><strong>${summaryNsrDisplay(active.competitorMean)}</strong></article><article><span>竞品差距</span><strong class="${active.gap!==null&&active.gap<0?"risk":""}">${gapText}</strong></article><article><span>差距幅度</span><strong>${active.gap===null?"—":`${Math.abs(active.gap*100).toFixed(1)}%`}</strong></article></div><section class="summary-attribute-source-board"><h3>分平台 / 来源对比（NSR）</h3>${sourceRows.map(item=>`<div class="summary-attribute-source-row"><b>${escapeHtml(item.platform)}</b><span><small>本品 ${summaryNsrDisplay(item.own)}</small><i class="summary-nsr-track"><em style="${summaryNsrTrackStyle(item.own)}" ${item.own===null?"hidden":""}></em></i></span><span><small>竞品均值 ${summaryNsrDisplay(item.competitor)}</small><i class="summary-nsr-track competitor"><em style="${summaryNsrTrackStyle(item.competitor)}" ${item.competitor===null?"hidden":""}></em></i></span></div>`).join("")}</section><section class="summary-attribute-judgment"><span>关键判断</span><p>${escapeHtml(summaryAttributeJudgment(active))}</p></section><div class="summary-attribute-actions"><button type="button" data-summary-attribute-evidence aria-expanded="${summaryAttributeEvidenceExpanded?"true":"false"}">${summaryAttributeEvidenceExpanded?"收起NSR证据明细":"查看NSR证据明细"}</button><button type="button" class="primary" data-summary-attribute-strategy>进入策略判断</button></div>${summaryAttributeEvidenceExpanded?`<section class="summary-attribute-evidence" aria-label="${escapeAttr(active.label)}NSR证据明细"><header><b>NSR证据明细</b><small>按来源分类，不把标准化记录解释为真实评论量。</small></header>${evidenceRows}</section>`:""}</aside></div><details class="summary-attribute-audit"><summary>查看完整车型对比表（数据审计）</summary><p>仅用于导入校验与异常排查，不作为默认策略判断界面。</p><div class="summary-attribute-matrix">${renderSummaryAttributeMatrix(rows,models,source)}</div></details>`;
}
function renderSummaryAttributeOpportunityBoard(rows,models,source){
 const ownModel=state.config.model,items=summaryAttributeOpportunityItems(rows,models,source);
 if(!items.length)return`<div class="empty-state">当前平台没有可展示的真实属性 NSR。</div>`;
 const competitors=models.filter(model=>model&&model!==ownModel),categories=["全部",...new Set(items.map(item=>item.category).filter(Boolean))];
 if(!categories.includes(summaryAttributeActiveCategory))summaryAttributeActiveCategory="全部";
 const visibleItems=summaryAttributeActiveCategory==="全部"?items:items.filter(item=>item.category===summaryAttributeActiveCategory);
 if(!visibleItems.some(item=>item.label===summaryAttributeActiveLabel))summaryAttributeActiveLabel=visibleItems[0]?.label||items[0].label;
 const active=items.find(item=>item.label===summaryAttributeActiveLabel)||visibleItems[0]||items[0],sources=state.importQuality?.attributeNsrSources||[...new Set(rows.map(row=>row[2]).filter(Boolean))],scoreFor=(model,platform)=>meanNumbers(rows.filter(row=>row[0]===model&&row[2]===platform&&row[4]===active.label).map(row=>nullableNumber(row[14])).filter(value=>value!==null)),sourceRows=sources.map(platform=>{const own=scoreFor(ownModel,platform),recorded=meanNumbers(competitors.map(model=>scoreFor(model,platform)).filter(value=>value!==null)),benchmark=nullableNumber(state.summaryAttributeBenchmark?.[platform]?.[active.label]),competitor=recorded??benchmark;return{platform,own,competitor,gap:own!==null&&competitor!==null?own-competitor:null,benchmarkUsed:recorded===null&&benchmark!==null}}),gapText=active.gap===null?"—":`${active.gap>=0?"领先":"落后"} ${Math.abs(active.gap*100).toFixed(1)}%`;
 const quadrants=[
  {key:"weak",title:"认知待建立",note:"用户评价偏负，但表现好于竞品",action:"先建立正面认知",filter:item=>item.ownNsr<0&&(item.gap===null||item.gap>=0)},
  {key:"strength",title:"领先优势",note:"用户评价偏正，且优于竞品",action:"重点放大",filter:item=>item.ownNsr>=0&&(item.gap??0)>=0},
  {key:"repair",title:"双重风险",note:"用户评价偏负，且落后竞品",action:"优先修复",filter:item=>item.ownNsr<0&&item.gap!==null&&item.gap<0},
  {key:"pressure",title:"对标短板",note:"用户评价偏正，但落后竞品",action:"重点追赶",filter:item=>item.ownNsr>=0&&item.gap!==null&&item.gap<0}
 ];
 const bubbleMarkup=(item,quadrantKey)=>{const gap=item.gap===null?"待补对标":`${item.gap>=0?"领先":"落后"}${Math.abs(item.gap*100).toFixed(1)}%`,size=summaryAttributeGapBubbleSize(item.gap);return`<button type="button" class="summary-quadrant-bubble ${summaryAttributeCategoryTone(item.category,item.label)} ${item.label===active.label?"active":""}" data-summary-attribute-item="${escapeAttr(item.label)}" data-summary-attribute-quadrant="${escapeAttr(quadrantKey)}" aria-pressed="${item.label===active.label?"true":"false"}" aria-label="下钻${escapeAttr(item.label)}，一级赛道${escapeAttr(item.category)}，本品NSR ${summaryNsrDisplay(item.ownNsr)}，${escapeAttr(gap)}" style="--bubble-size:${size}px"><span>${escapeHtml(item.label)}</span><small>NSR ${summaryNsrDisplay(item.ownNsr)}</small><em class="${item.gap!==null&&item.gap<0?"risk":""}">${escapeHtml(gap)}</em></button>`};
 const quadrantMarkup=quadrants.map(quadrant=>{const quadrantItems=visibleItems.filter(quadrant.filter),expanded=summaryAttributeExpandedQuadrants.has(quadrant.key),collapsed=summaryAttributeCollapsedQuadrants.has(quadrant.key)&&!expanded,preview=collapsed?`<div class="summary-quadrant-cluster-preview">${quadrantItems.map((item,index)=>{const angle=-Math.PI/2+index/Math.max(quadrantItems.length,1)*Math.PI*2,radiusX=70+(index%3)*7,radiusY=38+(index%2)*10,x=Math.round(Math.cos(angle)*radiusX),y=Math.round(Math.sin(angle)*radiusY),size=Math.round(24+(summaryAttributeGapBubbleSize(item.gap)-58)*.36);return`<span class="summary-quadrant-preview-orb ${summaryAttributeCategoryTone(item.category,item.label)} ${item.label===active.label?"active":""}" data-summary-preview-label="${escapeAttr(item.label)}" title="${escapeAttr(item.label)} · ${item.gap===null?"待补对标":`${item.gap>=0?"领先":"落后"}${Math.abs(item.gap*100).toFixed(1)}%`}" aria-hidden="true" style="--preview-x:${x}px;--preview-y:${y}px;--preview-size:${size}px;--preview-order:${index}"></span>`}).join("")}<button type="button" data-summary-quadrant-expand="${escapeAttr(quadrant.key)}" aria-expanded="false" aria-label="展开${escapeAttr(quadrant.title)}的${quadrantItems.length}个标签"><b>${quadrantItems.length}</b><span>个标签</span><em>点击展开</em></button></div>`:"",content=!quadrantItems.length?`<p>暂无标签</p>`:collapsed?preview:quadrantItems.map(item=>bubbleMarkup(item,quadrant.key)).join("");return`<section class="summary-quadrant-cell ${quadrant.key} ${collapsed?"is-collapsed":""} ${expanded?"is-expanded":""}"><header><div><b>${quadrant.title}</b><small>${quadrant.note}</small><em>管理动作：${quadrant.action}</em></div><span class="summary-quadrant-count"><strong>${quadrantItems.length}</strong>${expanded?`<button type="button" data-summary-quadrant-collapse="${escapeAttr(quadrant.key)}" aria-label="收起${escapeAttr(quadrant.title)}气泡">收起气泡</button>`:""}</span></header><div class="summary-quadrant-cloud" data-summary-quadrant-cloud="${escapeAttr(quadrant.key)}" data-summary-quadrant-count="${quadrantItems.length}">${content}</div></section>`}).join("");
 const modelRows=models.filter(Boolean).map(model=>{const score=meanNumbers(active.modelScores.get(model)||[]),isOwn=model===ownModel;return`<div class="summary-attribute-model-row ${isOwn?"own":"competitor"}"><b><small>${isOwn?"本品":"竞品"}</small>${escapeHtml(model)}</b><i class="summary-nsr-track"><em style="${summaryNsrTrackStyle(score)}" ${score===null?"hidden":""}></em></i><strong class="${score!==null&&score<0?"risk":""}">${summaryNsrDisplay(score)}</strong></div>`}).join("");
 const evidenceRows=sourceRows.map(item=>`<div class="summary-attribute-evidence-row"><b>${escapeHtml(item.platform)}</b><span>${escapeHtml(ownModel)} ${summaryNsrDisplay(item.own)}</span><span>竞品均值 ${summaryNsrDisplay(item.competitor)}</span><strong class="${item.gap!==null&&item.gap<0?"risk":""}">${item.gap===null?"不可比":`${item.gap>=0?"领先":"落后"} ${Math.abs(item.gap*100).toFixed(1)}%`}</strong></div>`).join("");
 return`<div class="summary-attribute-comparison-context"><div><span>本品</span><strong>${escapeHtml(ownModel)}</strong></div><i>VS</i><div class="competitors"><span>当前对标竞品</span><strong>${competitors.length?competitors.map(model=>`<b>${escapeHtml(model)}</b>`).join(""):"尚未选择竞品"}</strong></div><small>平台：${escapeHtml(source)} · 每个气泡对应一个二级属性标签</small></div><nav class="summary-attribute-category-tabs" aria-label="按一级赛道下钻">${categories.map(category=>`<button type="button" class="${category===summaryAttributeActiveCategory?"active":""}" data-summary-attribute-category="${escapeAttr(category)}" aria-pressed="${category===summaryAttributeActiveCategory?"true":"false"}">${escapeHtml(category)}</button>`).join("")}</nav><div class="summary-attribute-opportunity quadrant-mode"><section class="summary-attribute-map"><header><div><span>车型属性机会总览</span><b>属性 NSR 四象限</b></div><small>点击任一标签气泡，下钻本品与每台竞品</small></header><div class="summary-quadrant-guide" aria-label="四象限读图说明"><span><b>X轴：</b>消费者怎么看本品这个属性，越右越正面</span><span><b>Y轴：</b>本品比竞品好还是差，越上越领先</span></div><div class="summary-quadrant-stage" role="group" aria-label="${escapeAttr(ownModel)}与${escapeAttr(competitors.join("、"))}属性NSR四象限"><span class="summary-quadrant-y top">相对竞品领先 ↑</span><span class="summary-quadrant-y bottom">相对竞品落后 ↓</span>${quadrantMarkup}<div class="summary-quadrant-x"><span>← 负向 NSR</span><b>本品属性认知</b><span>正向 NSR →</span></div></div><footer><span>每个圆＝一个二级属性标签</span><span>大小＝与竞品 NSR 差距</span><span>颜色＝一级赛道</span><span>双环＝当前下钻标签</span><b>上半区越大代表领先越多；下半区越大代表落后越多。大小不代表声量。</b></footer></section><aside class="summary-attribute-diagnosis" aria-live="polite"><header><div><span>${escapeHtml(active.category)} · 二级标签下钻</span><b>${escapeHtml(active.label)} · 本竞品专项诊断</b></div><em class="${active.evidence.tone}">${escapeHtml(active.evidence.label)} · ${escapeHtml(active.evidence.note)}</em></header><section class="summary-attribute-model-compare"><h3>当前平台逐车型 NSR</h3>${modelRows}</section><div class="summary-attribute-kpis"><article><span>${escapeHtml(ownModel)} NSR</span><strong class="${active.ownNsr<0?"risk":""}">${summaryNsrDisplay(active.ownNsr)}</strong></article><article><span>${escapeHtml(competitors.join(" / ")||"竞品")}均值</span><strong>${summaryNsrDisplay(active.competitorMean)}</strong></article><article><span>NSR 差值</span><strong class="${active.gap!==null&&active.gap<0?"risk":""}">${gapText}</strong></article><article><span>差距幅度</span><strong>${active.gap===null?"—":`${Math.abs(active.gap*100).toFixed(1)}%`}</strong></article></div><section class="summary-attribute-source-board"><h3>分平台 / 来源对比（NSR）</h3>${sourceRows.map(item=>`<div class="summary-attribute-source-row"><b>${escapeHtml(item.platform)}</b><span><small>${escapeHtml(ownModel)} ${summaryNsrDisplay(item.own)}</small><i class="summary-nsr-track"><em style="${summaryNsrTrackStyle(item.own)}" ${item.own===null?"hidden":""}></em></i></span><span><small>竞品均值 ${summaryNsrDisplay(item.competitor)}</small><i class="summary-nsr-track competitor"><em style="${summaryNsrTrackStyle(item.competitor)}" ${item.competitor===null?"hidden":""}></em></i></span></div>`).join("")}</section><section class="summary-attribute-judgment"><span>关键判断</span><p>${escapeHtml(summaryAttributeJudgment(active))}</p></section><div class="summary-attribute-actions"><button type="button" data-summary-attribute-evidence aria-expanded="${summaryAttributeEvidenceExpanded?"true":"false"}">${summaryAttributeEvidenceExpanded?"收起来源证据":"查看来源证据"}</button><button type="button" class="primary" data-summary-attribute-strategy>进入策略判断</button></div>${summaryAttributeEvidenceExpanded?`<section class="summary-attribute-evidence" aria-label="${escapeAttr(active.label)}NSR证据明细"><header><b>NSR证据明细</b><small>逐来源核验，不把标准化记录解释为真实评论量。</small></header>${evidenceRows}</section>`:""}</aside></div><details class="summary-attribute-audit"><summary>查看完整车型对比表（数据审计）</summary><p>仅用于导入校验与异常排查，不作为默认策略判断界面。</p><div class="summary-attribute-matrix">${renderSummaryAttributeMatrix(rows,models,source)}</div></details>`;
}
function attributeEvidenceStatus(rows,label,model){
 const sourceScores=attributeSourceScores(rows,model,label),scores=sourceScores.map(item=>item.score),expected=state.importQuality?.attributeNsrSources?.length||scores.length,coverage=`${scores.length}/${expected}来源`;
 if(scores.length<Math.min(2,expected))return{label:"待补来源",note:coverage,tone:"pending"};
 const spread=Math.max(...scores)-Math.min(...scores),average=scores.reduce((sum,value)=>sum+value,0)/scores.length;
 if(spread>=.35)return{label:"来源冲突",note:`差值 ${(spread*100).toFixed(0)}%`,tone:"conflict"};
 if(scores.length===expected&&average>=.6&&scores.every(value=>value>=.4))return{label:"稳定优势",note:coverage,tone:"stable"};
 if(average<=0||scores.some(value=>value<=-.2)||average<.25)return{label:"风险待核",note:coverage,tone:"risk"};
 return{label:"需要解释",note:scores.length<expected?coverage:`差值 ${(spread*100).toFixed(0)}%`,tone:"review"};
}
function openSummaryAttributePopover(model,label,trigger){
 closeSummaryPlatformPopover();
 const panel=trigger.closest(".summary-attribute-section"),ownModel=state.config.model,sources=state.importQuality?.attributeNsrSources||[...new Set((state.rows||[]).map(r=>r[2]).filter(Boolean))];
 if(!panel)return;
 const scoreFor=(target,source)=>attributeSourceScores(state.rows,target,label).find(item=>item.source===source)?.score??null;
 const popover=document.createElement("section");
 popover.className="summary-platform-popover summary-attribute-popover";popover.setAttribute("role","dialog");popover.setAttribute("aria-label",`${label}本品与竞品属性对比`);
 popover.innerHTML=`<header><div><span>本品与竞品属性对比</span><b>${escapeHtml(label)} · ${escapeHtml(ownModel)} vs ${escapeHtml(model)}</b></div><button type="button" aria-label="关闭属性对比气泡"></button></header><div class="summary-attribute-compare">${sources.map(source=>{const own=scoreFor(ownModel,source),competitor=scoreFor(model,source),hasOwn=Number.isFinite(own),hasCompetitor=Number.isFinite(competitor),delta=hasOwn&&hasCompetitor?own-competitor:null;return`<section><span>${escapeHtml(source)}</span><div><b class="own">本品 ${hasOwn?summaryNsrDisplay(own):"—"}</b><i><em class="own" style="width:${hasOwn?Math.abs(own)*100:0}%"></em></i></div><div><b class="competitor">${escapeHtml(model)} ${hasCompetitor?summaryNsrDisplay(competitor):"—"}</b><i><em class="competitor" style="width:${hasCompetitor?Math.abs(competitor)*100:0}%"></em></i></div><small>${Number.isFinite(delta)?`本品${delta>=0?"领先":"落后"} ${Math.abs(delta*100).toFixed(1)}%`:"当前来源缺少可比较数据"}</small></section>`}).join("")}</div><footer><span>${attributeEvidenceStatus(state.rows,label,ownModel).label}</span><b>点击用于证据下钻，不代表市场全量需求或成交。</b></footer>`;
 panel.appendChild(popover);popover.style.top=`${Math.max(70,trigger.offsetTop-20)}px`;summaryPlatformPopoverTrigger=trigger;
 popover.querySelector("button").onclick=event=>{event.stopPropagation();closeSummaryPlatformPopover(true)};
 const onOutsideClick=event=>{if(!popover.contains(event.target)&&event.target!==trigger&&!trigger.contains(event.target))closeSummaryPlatformPopover()};
 const onKeydown=event=>{if(event.key==="Escape")closeSummaryPlatformPopover(true)};
 setTimeout(()=>document.addEventListener("click",onOutsideClick),0);document.addEventListener("keydown",onKeydown);
 summaryPlatformPopoverCleanup=()=>{document.removeEventListener("click",onOutsideClick);document.removeEventListener("keydown",onKeydown)};popover.querySelector("button").focus();
}
function summaryHeatNumber(value){return Math.max(0,Number(value)||0)}
function summaryHeatDisplay(value){const number=summaryHeatNumber(value);return number>=10000?`${(number/10000).toFixed(1)}万`:number.toLocaleString()}
function summaryHeatPercentage(value,total){return total?Math.min(summaryHeatNumber(value)/summaryHeatNumber(total)*100,100):0}
function summaryHeatPercentageDisplay(value){return`${value.toFixed(1)}%`}
function summaryNsrDisplay(value){const number=nullableNumber(value);return number!==null?`${(number*100).toFixed(1)}%`:"—"}
function summaryNsrTrackStyle(value){
 const score=Math.max(-1,Math.min(1,Number(value)||0)),size=Math.abs(score)*50,left=score<0?50-size:50;
 return`--nsr-left:${left.toFixed(4)}%;--nsr-size:${size.toFixed(4)}%`;
}
function summaryPlatformNsrSources(all,configured=[]){const preferred=Array.isArray(configured)?configured.filter(Boolean):[],observed=[...new Set(Object.values(all||{}).flatMap(item=>Object.keys(item||{})).filter(Boolean))],sources=[...new Set([...preferred,...observed])];return sources.includes("全网")?["全网",...sources.filter(source=>source!=="全网")]:sources}
function closeSummaryPlatformPopover(restoreFocus=false){
 const popover=document.querySelector(".summary-platform-popover");
 if(popover)popover.remove();
 if(summaryPlatformPopoverCleanup){summaryPlatformPopoverCleanup();summaryPlatformPopoverCleanup=null}
 if(restoreFocus&&summaryPlatformPopoverTrigger?.isConnected)summaryPlatformPopoverTrigger.focus();
 summaryPlatformPopoverTrigger=null;
}
function openSummaryNsrPopover(model,trigger){
 closeSummaryPlatformPopover();
 const chart=trigger.closest(".summary-nsr-chart"),ownModel=state.config.model,all=state.summaryPlatformNsr||{},values=all[model]||{},ownValues=all[ownModel]||{},isCompetitor=model!==ownModel;
 if(!chart)return;
 const sources=summaryPlatformNsrSources({[model]:values,[ownModel]:ownValues},state.importQuality?.platformNsrSources),popover=document.createElement("section");
 popover.className="summary-platform-popover summary-nsr-popover";
 popover.setAttribute("role","dialog");
 popover.setAttribute("aria-label",isCompetitor?`${model}与${ownModel}整体平台口碑NSR对比`:`${model}整体平台口碑NSR表现`);
 popover.innerHTML=`<header><div><span>${isCompetitor?"各平台本品 vs 竞品":"车型整体平台口碑"}</span><b>${escapeHtml(model)}${isCompetitor?` vs ${escapeHtml(ownModel)}`:""} · 全平台 NSR</b></div><button type="button" aria-label="关闭整体平台NSR气泡"></button></header>${sources.length?`<div class="summary-platform-bars summary-nsr-platform-bars">${sources.map(source=>{const score=nullableNumber(values[source]),ownScore=nullableNumber(ownValues[source]),hasScore=score!==null,hasOwn=ownScore!==null,modelRole=isCompetitor?"competitor":"own";return`<section class="summary-platform-group"><span class="summary-platform-name">${escapeHtml(source)}</span><div class="summary-platform-series"><div class="${modelRole} ${hasScore&&score<0?"negative":""}"><small>${isCompetitor?escapeHtml(model):`本品 · ${escapeHtml(model)}`}</small><i title="${hasScore?`NSR ${summaryNsrDisplay(score)}`:"源表无数据"}"><em style="${summaryNsrTrackStyle(score)}" ${hasScore?"":"hidden"}></em></i></div>${isCompetitor?`<div class="own ${hasOwn&&ownScore<0?"negative":""}"><small>本品 · ${escapeHtml(ownModel)}</small><i title="${hasOwn?`NSR ${summaryNsrDisplay(ownScore)}`:"源表无数据"}"><em style="${summaryNsrTrackStyle(ownScore)}" ${hasOwn?"":"hidden"}></em></i></div>`:""}</div></section>`}).join("")}</div>`:`<div class="summary-platform-empty">当前导入版本未保留整体平台NSR，请重新导入原表。</div>`}`;
 chart.appendChild(popover);
 const desiredTop=trigger.offsetTop+trigger.offsetHeight-4,chartHeight=chart.clientHeight,popoverHeight=popover.offsetHeight;
 popover.style.top=`${Math.max(46,Math.min(desiredTop,chartHeight-popoverHeight-12))}px`;
 summaryPlatformPopoverTrigger=trigger;
 popover.querySelector("button").onclick=event=>{event.stopPropagation();closeSummaryPlatformPopover(true)};
 const onOutsideClick=event=>{if(!popover.contains(event.target)&&event.target!==trigger&&!trigger.contains(event.target))closeSummaryPlatformPopover()};
 const onKeydown=event=>{if(event.key==="Escape")closeSummaryPlatformPopover(true)};
 setTimeout(()=>document.addEventListener("click",onOutsideClick),0);
 document.addEventListener("keydown",onKeydown);
 summaryPlatformPopoverCleanup=()=>{document.removeEventListener("click",onOutsideClick);document.removeEventListener("keydown",onKeydown)};
 popover.querySelector("button").focus();
}
function openSummaryPlatformPopover(model,trigger){
 closeSummaryPlatformPopover();
 const chart=trigger.closest(".summary-heat-chart"),ownModel=state.config.model,heat=state.summaryHeat||{},values=heat[model]?.platformVolume||{},ownValues=heat[ownModel]?.platformVolume||{},modelTotal=summaryHeatNumber(heat[model]?.volume),ownTotal=summaryHeatNumber(heat[ownModel]?.volume),isCompetitor=model!==ownModel;
 if(!chart)return;
 const entries=Object.entries(values).map(([platform,value])=>{const count=summaryHeatNumber(value),ownCount=summaryHeatNumber(ownValues[platform]),percentage=summaryHeatPercentage(count,modelTotal),ownPercentage=summaryHeatPercentage(ownCount,ownTotal),platformMax=Math.max(percentage,ownPercentage);return{platform,value:count,ownValue:ownCount,percentage,ownPercentage,trendPercentage:isCompetitor&&platformMax?percentage/platformMax*100:percentage,ownTrendPercentage:isCompetitor&&platformMax?ownPercentage/platformMax*100:ownPercentage}}),popover=document.createElement("section");
 popover.className="summary-platform-popover";
 popover.setAttribute("role","dialog");
 popover.setAttribute("aria-label",isCompetitor?`${model}与${ownModel}分平台声量对比`:`${model}分平台声量表现`);
 const title=isCompetitor?`${escapeHtml(model)} vs ${escapeHtml(ownModel)} · 分平台声量对比`:`${escapeHtml(model)} · 分平台声量表现`;
 popover.innerHTML=`<header><div><span>${isCompetitor?"各平台内本品 vs 竞品相对趋势":"平台声量占本品全网声量"}</span><b>${title}</b></div><button type="button" aria-label="关闭分平台声量气泡"></button></header>${entries.length?`<div class="summary-platform-bars">${entries.map(item=>`<section class="summary-platform-group"><span class="summary-platform-name">${escapeHtml(item.platform)}</span><div class="summary-platform-series"><div class="competitor"><small>${escapeHtml(model)}</small><i title="占车型全网声量 ${summaryHeatPercentageDisplay(item.percentage)} · 绝对声量 ${item.value.toLocaleString()}"><em style="width:${item.trendPercentage.toFixed(4)}%"></em></i></div>${isCompetitor?`<div class="own"><small>本品 · ${escapeHtml(ownModel)}</small><i title="占车型全网声量 ${summaryHeatPercentageDisplay(item.ownPercentage)} · 绝对声量 ${item.ownValue.toLocaleString()}"><em style="width:${item.ownTrendPercentage.toFixed(4)}%"></em></i></div>`:""}</div></section>`).join("")}</div>`:`<div class="summary-platform-empty">当前导入版本未保留分平台声量，请重新导入原表。</div>`}`;
 chart.appendChild(popover);
 const desiredTop=trigger.offsetTop+trigger.offsetHeight-4,chartHeight=chart.clientHeight,popoverHeight=popover.offsetHeight;
 popover.style.top=`${Math.max(46,Math.min(desiredTop,chartHeight-popoverHeight-12))}px`;
 summaryPlatformPopoverTrigger=trigger;
 popover.querySelector("button").onclick=event=>{event.stopPropagation();closeSummaryPlatformPopover(true)};
 const onOutsideClick=event=>{if(!popover.contains(event.target)&&event.target!==trigger&&!trigger.contains(event.target))closeSummaryPlatformPopover()};
 const onKeydown=event=>{if(event.key==="Escape")closeSummaryPlatformPopover(true)};
 setTimeout(()=>document.addEventListener("click",onOutsideClick),0);
 document.addEventListener("keydown",onKeydown);
 summaryPlatformPopoverCleanup=()=>{document.removeEventListener("click",onOutsideClick);document.removeEventListener("keydown",onKeydown)};
 popover.querySelector("button").focus();
}
function summaryHeatSelection(){
 const available=(state.models||[]).filter(Boolean);
 summaryDashboardModels=summaryDashboardModels.filter(model=>available.includes(model));
 const own=state.config.model;
 if(!summaryDashboardModels.length&&available.length)summaryDashboardModels=[...available];
 if(own&&available.includes(own))summaryDashboardModels=[own,...summaryDashboardModels.filter(model=>model!==own)];
 return summaryDashboardModels;
}
function renderSummaryOverallNsr(selected){
 const all=state.summaryPlatformNsr||{},sources=summaryPlatformNsrSources(all,state.importQuality?.platformNsrSources);
 const rows=selected.map(model=>({model,values:Object.fromEntries(sources.map(source=>[source,nullableNumber(all[model]?.[source])]))})),hasData=sources.length&&rows.some(row=>Object.values(row.values).some(score=>score!==null)),ownModel=state.config.model,ownRow=rows.find(row=>row.model===ownModel);
 const tone=score=>score===null?"missing":score<0?"risk":score<.2?"weak":score<.5?"medium":"strong";
 const ownScores=sources.filter(source=>source!=="全网").map(source=>({source,score:ownRow?.values[source]??null})).filter(item=>item.score!==null).sort((a,b)=>b.score-a.score),overall=ownRow?.values["全网"]??null,lowest=ownScores.at(-1),highSources=ownScores.filter(item=>overall!==null&&item.score>=overall).slice(0,3),leaders=(highSources.length?highSources:ownScores.slice(0,3)).map(item=>item.source),gap=overall!==null&&lowest?Math.max(0,overall-lowest.score):null;
 const insight=ownRow&&lowest?`<div class="summary-nsr-insight"><p><b>${escapeHtml(ownModel)} 平台机会：</b>${leaders.length?`${escapeHtml(leaders.join("、"))}已形成高位认知；`:""}${escapeHtml(lowest.source)} NSR 为 ${summaryNsrDisplay(lowest.score)}${gap!==null&&gap>0?`，较全网低 ${(gap*100).toFixed(1)}%`:""}，应单独诊断内容语言和人群预期。</p></div>`:"";
 return`<section class="summary-nsr-section"><header><div><span>平台 NSR 指纹矩阵</span><b>同一款车在不同平台呈现怎样的认知面貌</b><small>整体口碑与各平台并列展示；不与下方产品点属性 NSR 混用。</small></div><em>颜色越绿，净喜好度越高</em></header><div class="summary-nsr-chart">${hasData?`<div class="summary-nsr-matrix-scroll"><div class="summary-nsr-matrix" style="--nsr-columns:${sources.length}" role="table" aria-label="车型平台NSR指纹矩阵"><div class="summary-nsr-matrix-head" role="row"><b role="columnheader">车型</b>${sources.map(source=>`<span role="columnheader">${escapeHtml(source)}</span>`).join("")}</div>${rows.map(row=>`<div class="summary-nsr-matrix-row ${row.model===ownModel?"own":"competitor"}" role="row"><b role="rowheader">${escapeHtml(row.model)}${row.model===ownModel?"<small>本品</small>":""}</b>${sources.map(source=>{const score=row.values[source],hasScore=score!==null;return`<button type="button" class="summary-nsr-cell ${tone(score)}" data-summary-nsr-model="${escapeAttr(row.model)}" role="cell" aria-label="查看${escapeAttr(row.model)}全平台NSR，${escapeAttr(source)}${hasScore?summaryNsrDisplay(score):"样本不足"}"><strong>${hasScore?summaryNsrDisplay(score):"样本不足"}</strong></button>`}).join("")}</div>`).join("")}</div></div>${insight}`:`<div class="empty-state">当前导入版本没有整体平台NSR，请重新导入原始产品评价表。</div>`}</div></section>`;
}
function renderSummaryHeatDashboard(a){
 closeSummaryPlatformPopover();
 const available=(state.models||[]).filter(Boolean),selected=summaryHeatSelection(),heat=state.summaryHeat||{},ownRows=a?.own||state.rows.filter(r=>r[0]===state.config.model);
 const volumeMetricLabel=state.importQuality?.volumeMetricLabel||"全网声量",interactionAvailable=state.importQuality?.interactionAvailable!==false;
 const sources=[...new Set(ownRows.map(r=>r[2]).filter(Boolean))],labels=[...new Set(ownRows.map(r=>r[4]).filter(Boolean))],referenceModels=available.filter(model=>model!==state.config.model);
 if(!sources.includes(summaryAttributePlatform))summaryAttributePlatform=sources.includes("全网")?"全网":sources[0]||"";
 const rows=selected.map(model=>({model,volume:summaryHeatNumber(heat[model]?.volume),interaction:summaryHeatNumber(heat[model]?.interaction)}));
 const maxVolume=Math.max(...rows.map(row=>row.volume),1),maxInteraction=Math.max(...rows.map(row=>row.interaction),1);
 document.querySelector(".dashboard-data-title-copy span").textContent="产品评价汇总";
 document.querySelector(".dashboard-data-title-copy h2").textContent=`${volumeMetricLabel}${interactionAvailable?"及互动量":""}对比`;
 document.querySelector("#dashboard-data-note").textContent=`${labels.length} 个可用产品点 · ${referenceModels.length} 台可选竞品`;
 document.querySelector("#dashboard-platform-control").innerHTML="";
 document.querySelector("#dashboard-data-context").innerHTML=[
  ["本品车型",state.config.model,"own-model"],
  ["数据参照车型",referenceModels.join(" / ")||"暂无参照车型","reference-models"],
  ["时间维度",dashboardTimeDimension(),"time-dimension"],
  ["数据维度",`${volumeMetricLabel}${interactionAvailable?" × 互动量":""} × 属性NSR评分`,"data-dimension"],
  ["当前可用产品点",labels.slice(0,6).join(" / ")||"暂无可用产品点","label-dimension"]
 ].map(([name,value,cls])=>`<div class="${cls}"><span>${name}</span><b title="${escapeAttr(value)}">${escapeHtml(value)}</b></div>`).join("");
 const summary=document.querySelector("#dashboard-data-summary");
 summary.innerHTML="";
 summary.hidden=true;
 const surface=document.querySelector("#dashboard-emotion-quadrant");
 surface.className="summary-dashboard-workbench";
 const ownModel=state.config.model,competitorModels=available.filter(model=>model!==ownModel);
 const selectorHtml=`<aside class="summary-heat-selector"><section class="summary-heat-own"><label for="summary-own-model">主车型</label><select id="summary-own-model" aria-label="选择主车型">${available.map(model=>`<option value="${escapeAttr(model)}" ${model===ownModel?"selected":""}>${escapeHtml(model)}</option>`).join("")}</select><small>切换后，所有 NSR 与竞品差距同步重算</small></section><section class="summary-heat-competitors"><span>对比竞品</span><div class="summary-heat-model-list">${competitorModels.map(model=>`<label><input type="checkbox" value="${escapeAttr(model)}" ${selected.includes(model)?"checked":""}><span>${escapeHtml(model)}</span></label>`).join("")}</div><label class="summary-heat-add"><span>添加竞品</span><select id="summary-heat-add-model"><option value="">选择竞品</option>${competitorModels.filter(model=>!selected.includes(model)).map(model=>`<option value="${escapeAttr(model)}">${escapeHtml(model)}</option>`).join("")}</select></label></section></aside>`;
 const chartRows=rows.map(row=>`<button type="button" class="summary-heat-row" data-summary-heat-model="${escapeAttr(row.model)}" aria-label="查看${escapeAttr(row.model)}分平台${escapeAttr(volumeMetricLabel)}表现"><b>${escapeHtml(row.model)}</b><span class="summary-heat-bars"><span><small>${escapeHtml(volumeMetricLabel)}</small><i class="volume" style="width:${row.volume/maxVolume*100}%"></i><strong>${summaryHeatDisplay(row.volume)}</strong></span>${interactionAvailable?`<span><small>互动量</small><i class="interaction" style="width:${row.interaction/maxInteraction*100}%"></i><strong>${summaryHeatDisplay(row.interaction)}</strong></span>`:""}</span></button>`).join("");
 const chartHtml=`<section class="summary-heat-chart"><div class="summary-heat-chart-head"><small>${interactionAvailable?`${escapeHtml(volumeMetricLabel)}与互动量按各自独立尺度展示，不可直接比较绝对柱长。`:`${escapeHtml(volumeMetricLabel)}来自源数据聚合；源表未提供互动量。`}</small><div class="summary-heat-legend"><span><i class="volume"></i>${escapeHtml(volumeMetricLabel)}</span>${interactionAvailable?`<span><i class="interaction"></i>全网互动量</span>`:""}</div></div>${chartRows||`<div class="empty-state">暂无可展示车型。</div>`}</section>`;
 surface.innerHTML=`<div class="summary-heat-workbench">${selectorHtml}${chartHtml}</div>${renderSummaryOverallNsr(selected)}<section class="summary-attribute-section"><header><div><span>属性诊断</span><b>真实属性 NSR 四象限</b><small>先确认本竞品，再按一级赛道和二级标签下钻。</small></div>${sources.length?`<label class="summary-nsr-platform-select"><span>选择平台</span><select id="summary-attribute-platform" aria-label="选择真实属性NSR平台">${sources.map(source=>`<option value="${escapeAttr(source)}" ${source===summaryAttributePlatform?"selected":""}>${escapeHtml(source)}</option>`).join("")}</select></label>`:""}</header>${renderSummaryAttributeOpportunityBoard(state.rows,selected,summaryAttributePlatform)}</section>`;
 const ownModelSelect=document.querySelector("#summary-own-model");if(ownModelSelect)ownModelSelect.onchange=event=>{const nextModel=event.target.value;summaryAttributeActiveLabel="";summaryAttributeActiveCategory="全部";summaryAttributeEvidenceExpanded=false;resetSummaryQuadrantCollapse();summaryDashboardModels=[nextModel,...available.filter(model=>model!==nextModel).slice(0,3)];selectDashboardVehicleContext(nextModel,{source:"product-evaluation"})};
 document.querySelectorAll(".summary-heat-model-list input").forEach(input=>input.onchange=()=>{summaryDashboardModels=[ownModel,...document.querySelectorAll(".summary-heat-model-list input:checked")].map(node=>node.value);resetSummaryQuadrantCollapse();renderSummaryHeatDashboard()});
 const add=document.querySelector("#summary-heat-add-model");if(add)add.onchange=()=>{if(add.value&&!summaryDashboardModels.includes(add.value)){summaryDashboardModels=[...summaryDashboardModels,add.value];resetSummaryQuadrantCollapse();renderSummaryHeatDashboard()}};
 document.querySelectorAll("[data-summary-heat-model]").forEach(row=>row.onclick=event=>{event.stopPropagation();openSummaryPlatformPopover(row.dataset.summaryHeatModel,row)});
 document.querySelectorAll("[data-summary-nsr-model]").forEach(row=>row.onclick=event=>{event.stopPropagation();openSummaryNsrPopover(row.dataset.summaryNsrModel,row)});
 document.querySelectorAll("[data-summary-attribute-model]").forEach(cell=>cell.onclick=event=>{event.stopPropagation();openSummaryAttributePopover(cell.dataset.summaryAttributeModel,cell.dataset.summaryAttributeLabel,cell)});
 document.querySelectorAll("[data-summary-attribute-item]").forEach(item=>item.onclick=()=>{summaryAttributeActiveLabel=item.dataset.summaryAttributeItem;sellingPointActiveLabel=summaryAttributeActiveLabel;summaryAttributeEvidenceExpanded=false;renderSummaryHeatDashboard(a);renderSellingPointDecisionWorkbench()});
 document.querySelectorAll("[data-summary-attribute-category]").forEach(category=>category.onclick=()=>{summaryAttributeActiveCategory=category.dataset.summaryAttributeCategory;summaryAttributeActiveLabel="";summaryAttributeEvidenceExpanded=false;resetSummaryQuadrantCollapse();renderSummaryHeatDashboard(a)});
 document.querySelectorAll("[data-summary-quadrant-expand]").forEach(button=>button.onclick=()=>{const key=button.dataset.summaryQuadrantExpand;summaryAttributeCollapsedQuadrants.delete(key);summaryAttributeExpandedQuadrants.add(key);renderSummaryHeatDashboard(a)});
 document.querySelectorAll("[data-summary-quadrant-collapse]").forEach(button=>button.onclick=()=>{const key=button.dataset.summaryQuadrantCollapse;summaryAttributeExpandedQuadrants.delete(key);summaryAttributeCollapsedQuadrants.add(key);renderSummaryHeatDashboard(a)});
 const evidenceButton=document.querySelector("[data-summary-attribute-evidence]");if(evidenceButton)evidenceButton.onclick=()=>{summaryAttributeEvidenceExpanded=!summaryAttributeEvidenceExpanded;renderSummaryHeatDashboard(a)};
 const strategyButton=document.querySelector("[data-summary-attribute-strategy]");if(strategyButton)strategyButton.onclick=()=>{const form=document.querySelector("#model-judgment-form");form?.scrollIntoView({behavior:"smooth",block:"center"});setTimeout(()=>form?.querySelector("textarea")?.focus({preventScroll:true}),450)};
 const attributePlatform=document.querySelector("#summary-attribute-platform");if(attributePlatform)attributePlatform.onchange=event=>{summaryAttributePlatform=event.target.value;summaryAttributeActiveLabel="";summaryAttributeEvidenceExpanded=false;resetSummaryQuadrantCollapse();renderSummaryHeatDashboard(a)};
 requestAnimationFrame(()=>syncSummaryQuadrantOverflow(a));
}
function dashboardTimeDimension(){
 const importedRange=String(state.importQuality?.timeRange||"").trim();
 if(importedRange)return importedRange;
 const text=String(state.sourceNote||""),range=text.match(/(20\d{2}[.\/-]\d{1,2}[.\/-]\d{1,2})\s*(?:-|—|–|至|到)\s*(20\d{2}[.\/-]\d{1,2}[.\/-]\d{1,2})/);
 if(range)return`${range[1]} — ${range[2]}`;
 const items=canonicalVerticalItems(verticalState.items||[]).sort(sortVerticalItem);
 return items.length?`${items[0].period} — ${items.at(-1).period}`:"当前导入周期";
}
function dashboardVerticalTimeDimension(){const items=canonicalVerticalItems(verticalState.items||[]).filter(item=>item.ownModel===state.config.model).sort(sortVerticalItem);return items.length?`${items[0].period} — ${items.at(-1).period}`:"暂无垂媒周期"}
function renderDashboardData(a){
 if(isSummaryImport()){
  renderSummaryHeatDashboard(a);
  return;
 }
 const platforms=[...new Set(a.own.map(r=>r[2]).filter(Boolean))];
 if(dashboardPlatformFilter!=="all"&&!platforms.includes(dashboardPlatformFilter))dashboardPlatformFilter="all";
 const filteredRows=dashboardPlatformFilter==="all"?a.own:a.own.filter(r=>r[2]===dashboardPlatformFilter);
 const categories=[...new Set(a.own.map(r=>r[3]).filter(Boolean))],labels=[...new Set(a.own.map(r=>r[4]).filter(Boolean))],filteredLabels=[...new Set(filteredRows.map(r=>r[4]).filter(Boolean))],referenceModels=[...new Set(state.rows.map(r=>r[0]).filter(x=>x&&x!==state.config.model))];
 document.querySelector("#dashboard-data-note").textContent=isBlockedImport()?state.importQuality.message:(a.own.length?`${filteredLabels.length} 个有效标签`:`${state.config.model} 暂无数据`);
 document.querySelector(".dashboard-data-title-copy span").textContent="声量数据中心";
 document.querySelector(".dashboard-data-title-copy h2").textContent="平台情绪标签四象限";
 document.querySelector("#dashboard-platform-control").innerHTML=`<label class="platform-filter-bubble dashboard-platform-bubble"><span>平台</span><select id="dashboard-platform-filter" aria-label="按平台筛选四象限"><option value="all">全部平台</option>${platforms.map(platform=>`<option value="${escapeAttr(platform)}" ${platform===dashboardPlatformFilter?"selected":""}>${escapeHtml(platform)}</option>`).join("")}</select></label>`;
 document.querySelector("#dashboard-data-context").innerHTML=[
  ["本品车型",state.config.model,"own-model"],
  ["数据参照车型",referenceModels.join(" / ")||"暂无参照车型","reference-models"],
  ["时间维度",dashboardTimeDimension(),"time-dimension"],
  ["数据维度","平台 × 情绪效价 × 表达强度 × 认知赛道","data-dimension"],
  ["当前标签",filteredLabels.slice(0,6).join(" / ")||"暂无有效标签","label-dimension"]
 ].map(([name,value,cls])=>`<div class="${cls}"><span>${name}</span><b title="${escapeAttr(value)}">${escapeHtml(value)}</b></div>`).join("");
 const summary=document.querySelector("#dashboard-data-summary");
 summary.hidden=false;
 summary.innerHTML=[
  ["本品车型数",a.own.length?1:0],
  ["平台数",platforms.length],
  ["主要赛道",categories[0]||"—"],
  ["主要标签",labels[0]||"—"]
 ].map(x=>`<div><span>${x[0]}</span><b>${x[1]}</b></div>`).join("");
 const surface=document.querySelector("#dashboard-emotion-quadrant");
 surface.className="emotion-quadrant";
 const quadrantData=emotionQuadrantData(filteredRows);
 const filteredTotal=filteredRows.reduce((sum,r)=>sum+(+r[8]||0),0);
 surface.innerHTML=filteredRows.length?emotionQuadrantDefinitions.map(q=>{const top=quadrantData.get(q.key)||[];return`<section class="emotion-quadrant-cell ${q.key}" data-quadrant="${q.key}"><header><div><span>${q.title}</span><small>${q.subtitle}</small></div><b>TOP ${top.length}</b></header><div class="emotion-tag-list">${top.map((x,i)=>`<button type="button" class="emotion-tag" data-emotion-label="${escapeAttr(x.label)}" data-emotion-quadrant="${q.key}" aria-label="查看${escapeAttr(x.label)}赛道与竞品表现"><span>${String(i+1).padStart(2,"0")}</span><b>${escapeHtml(x.label)}</b><small>${escapeHtml(x.category)} · ${filteredTotal?(x.samples/filteredTotal*100).toFixed(1):"0.0"}%</small></button>`).join("")}</div></section>`}).join(""):`<div class="empty-state">当前平台暂无 ${state.config.model} 的情绪标签数据。</div>`;
 document.querySelector("#dashboard-platform-filter").onchange=event=>{dashboardPlatformFilter=event.target.value;renderDashboardData(a)};
 document.querySelectorAll("#dashboard-emotion-quadrant [data-emotion-label]").forEach(button=>button.onclick=()=>openEmotionLabelDialog(button.dataset.emotionLabel,button.dataset.emotionQuadrant,dashboardPlatformFilter));
}
function openEmotionLabelDialog(label,quadrantKey,platform){
 const definition=emotionQuadrantDefinitions.find(x=>x.key===quadrantKey)||{title:"情绪象限",subtitle:"效价 × 强度动态划分"},quadrantTitle=definition.title;
 const rows=state.rows.filter(r=>r[4]===label&&(platform==="all"||r[2]===platform));
 const models=[...new Set(rows.map(r=>r[0]).filter(Boolean))],values=models.map(model=>{const modelRows=rows.filter(r=>r[0]===model),samples=modelRows.reduce((sum,r)=>sum+(+r[8]||0),0),modelTotal=state.rows.filter(r=>r[0]===model&&(platform==="all"||r[2]===platform)).reduce((sum,r)=>sum+(+r[8]||0),0),share=modelTotal?samples/modelTotal*100:0,categories=[...new Set(modelRows.map(r=>r[3]).filter(Boolean))],emotionNames=[...new Set(modelRows.map(r=>r[5]).filter(Boolean))];return{model,share,categories,emotionNames,isOwn:model===state.config.model}}).sort((a,b)=>Number(b.isOwn)-Number(a.isOwn)||b.share-a.share),max=Math.max(...values.map(x=>x.share),1),own=values.find(x=>x.isOwn),competitors=values.filter(x=>!x.isOwn),category=[...new Set(rows.map(r=>r[3]).filter(Boolean))].join(" / ")||"待补充";
 const dialog=document.querySelector("#emotion-label-dialog"),body=document.querySelector("#emotion-label-dialog-body");
 document.querySelector("#emotion-label-dialog-title").textContent=`${label}｜赛道与竞品表现`;
 body.innerHTML=`<div class="trend-summary emotion-dialog-summary"><div><span>情绪象限</span><b>${quadrantTitle}</b><small>${definition.subtitle}</small></div><div><span>所属赛道</span><b>${escapeHtml(category)}</b><small>${platform==="all"?"全部平台":escapeHtml(platform)}</small></div><div><span>本品标签占比</span><b>${own?`${own.share.toFixed(1)}%`:"暂无样本"}</b><small>占本品当前平台总声量</small></div><div><span>竞品覆盖</span><b>${competitors.length} 个</b><small>统一使用车型内占比</small></div></div><div class="emotion-competitor-list">${values.length?values.map(x=>{const delta=x.share-(own?.share||0);return`<div class="emotion-competitor-row ${x.isOwn?"own":""}"><div><span>${x.isOwn?"本品":"竞品"}</span><b>${escapeHtml(x.model)}</b><small>${escapeHtml(x.emotionNames.join(" / "))}</small></div><div class="emotion-competitor-track"><i style="width:${x.share/max*100}%"></i></div><strong>${x.share.toFixed(1)}%</strong><em>${x.isOwn?"占车型总声量":`${delta>0?"+":""}${delta.toFixed(1)}%`}</em></div>`}).join(""):`<div class="empty-state">暂无可对比的车型数据</div>`}</div>`;
 dialog.showModal();
}
function renderDashboardCognition(a){
 const rows=a.labels.slice(0,8);
 document.querySelector("#dashboard-cognition-table").innerHTML=`<thead><tr><th>认知标签</th><th>诊断</th><th>本品负向</th><th>Gap</th><th>优先级</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><b>${x.label}</b><small>${x.category}</small></td><td><span class="tag ${x.diagnosis==="优先修复"?"risk":x.diagnosis==="持续放大"?"asset":""}">${x.diagnosis}</span></td><td class="negative">${Math.round(x.on).toLocaleString()}</td><td>${(x.gap*100).toFixed(1)}%</td><td>${x.priority.toFixed(1)}</td></tr>`).join(""):`<tr><td colspan="5" class="empty-cell">暂无 ${state.config.model} 的认知诊断数据，导入该车型声量后会自动计算。</td></tr>`}</tbody>`;
}
function summaryOpportunityMapLabels(){
 const rows=state.rows.filter(r=>Number.isFinite(Number(r[14]))),labels=[...new Set(rows.map(r=>r[4]).filter(Boolean))],ownModel=state.config.model;
 const mean=values=>values.length?values.reduce((sum,value)=>sum+value,0)/values.length:NaN;
 return labels.map(label=>{
  const labelRows=rows.filter(r=>r[4]===label),ownRows=labelRows.filter(r=>r[0]===ownModel),ownNsr=mean(ownRows.map(r=>Number(r[14]))),competitorModels=[...new Set(labelRows.filter(r=>r[0]!==ownModel).map(r=>r[0]))],competitorScores=competitorModels.map(model=>mean(labelRows.filter(r=>r[0]===model).map(r=>Number(r[14])))).filter(Number.isFinite),competitorNsr=mean(competitorScores);
  if(!Number.isFinite(ownNsr)||!Number.isFinite(competitorNsr))return null;
  const gap=competitorNsr-ownNsr,impact=mean(ownRows.map(r=>Number(r[9])).filter(Number.isFinite))||3,mapDiagnosis=ownNsr<0?"优先修复":gap>=.08?"抢占空位":"持续放大",priority=mapDiagnosis==="优先修复"?Math.abs(ownNsr)*100+impact*10:mapDiagnosis==="抢占空位"?gap*100+impact*5:Math.max(ownNsr,0)*100+impact*3;
  return{label,category:(ownRows[0]||labelRows[0]||[])[3]||"",ownNsr,competitorNsr,gap,impact,priority,mapDiagnosis,diagnosis:mapDiagnosis,op:Math.max(ownNsr,0)*100,on:Math.max(-ownNsr,0)*100,cp:Math.max(competitorNsr,0)*100,cn:Math.max(-competitorNsr,0)*100,white:Math.max(gap,0)*100};
 }).filter(Boolean);
}
function opportunityMapLabels(labels){
 if(isSummaryImport())return summaryOpportunityMapLabels();
 const types=["优先修复","抢占空位","持续放大"],groups=new Map(types.map(type=>[type,[]])),base=Math.floor(labels.length/types.length),remainder=labels.length%types.length,capacity=new Map(types.map((type,i)=>[type,base+(i<remainder?1:0)]));
 const fit=(x,type)=>{const total=Math.max(x.op+x.on,1),original=x.diagnosis===type ? .12 : 0;if(type==="优先修复")return x.on/total+(x.impact||0)/10+original;if(type==="抢占空位")return Math.max(x.gap||0,0)*4+(x.white||0)/20+(x.impact||0)/20+original;return x.op/total+Math.max(-(x.gap||0),0)*2+original};
 const pairs=labels.flatMap(x=>types.map(type=>({x,type,score:fit(x,type)}))).sort((a,b)=>b.score-a.score),assigned=new Set();
 pairs.forEach(({x,type})=>{if(assigned.has(x.label)||groups.get(type).length>=capacity.get(type))return;groups.get(type).push({...x,mapDiagnosis:type,mapRebalanced:x.diagnosis!==type});assigned.add(x.label)});
 labels.filter(x=>!assigned.has(x.label)).forEach(x=>{const type=types.find(t=>groups.get(t).length<capacity.get(t))||types[0];groups.get(type).push({...x,mapDiagnosis:type,mapRebalanced:x.diagnosis!==type})});
 return types.flatMap(type=>groups.get(type));
}
function renderServerOpportunityMap(){
 const source=(opportunityEvidenceState.result&&opportunityEvidenceState.result.opportunities)||[];
 const all=source.map(item=>{const diagnosis=item.categoryLabel||"待人工确认",score=nullableNumber(item.opportunityScore),mapX=nullableNumber(item.mapX),mapY=nullableNumber(item.mapY),recognition=nullableNumber(item.recognition),competitorLead=nullableNumber(item.competitorLead);return{...item,mapDiagnosis:diagnosis,diagnosis,priority:score??0,gap:mapX??competitorLead??0,impact:mapY??3,ownNsr:recognition===null?NaN:recognition*2-1,competitorNsr:recognition===null?NaN:recognition*2-1+(mapX??0),on:0,op:0,cp:Math.max(mapX??0,0)*100,cn:0}});
 const filtered=mapFilter==="all"?all:all.filter(item=>item.mapDiagnosis===mapFilter),ranked=[...filtered].sort((a,b)=>b.priority-a.priority),shown=ranked.slice(0,mapLimit),counts=all.reduce((map,item)=>map.set(item.mapDiagnosis,(map.get(item.mapDiagnosis)||0)+1),new Map());
 document.querySelectorAll("#map-filters button").forEach(button=>{const count=button.dataset.filter==="all"?all.length:(counts.get(button.dataset.filter)||0);button.dataset.baseLabel=button.dataset.baseLabel||button.textContent.trim().replace(/\s+\d+$/,'');button.textContent=`${button.dataset.baseLabel} ${count}`;button.classList.toggle("active",button.dataset.filter===mapFilter);button.disabled=false;button.classList.toggle("empty-filter",count===0);button.title=count?String(count)+" 个标签":"当前数据没有"+button.dataset.filter+"，仍可查看空状态"});
 document.querySelector("#map-limit").value=String(mapLimit);
 document.querySelector("#map-summary").textContent="证据增强地图：当前筛选 "+filtered.length+" 个产品点，显示 Top "+shown.length+"。横轴按交叉验证后的竞品领先度，纵轴按购买影响重新计算。"+(opportunityEvidenceState.result.status==="completed"?"产品事实、市场认知和传播热度已完成MMN双模型交叉验证。":"已通过的标签同步更新地图，冲突或证据不足项保留待人工确认。");
 const surface=document.querySelector("#opportunity-map"),surfaceWidth=Math.max(surface.clientWidth,320),surfaceHeight=Math.max(surface.clientHeight,360),maxGap=Math.max(...all.map(x=>Math.abs(x.gap)),.01);
 surface.innerHTML=shown.length?layoutBubbles(shown.map(item=>{const left=50+(item.gap/maxGap)*42,bottom=Math.min(88,Math.max(9,((item.impact-1)/4)*79+9)),cls=item.mapDiagnosis==="优先修复"?"risk":item.mapDiagnosis==="抢占空位"?"chance":item.mapDiagnosis==="待人工确认"?"pending":"asset";return{...item,left,bottom,quadrantX:item.gap<0?"left":item.gap>0?"right":"axis",quadrantY:item.impact>3?"high":item.impact<3?"low":"axis",cls,w:Math.max(58,String(item.label||"").length*13+24),h:30}}),surfaceWidth,surfaceHeight).map(b=>'<button type="button" class="bubble '+b.cls+'" style="left:'+b.x+'%;bottom:'+b.y+'%" title="'+escapeAttr(String(b.label||"")+"｜"+String(b.mapDiagnosis||"")+"｜竞品领先度 "+Number(b.gap||0).toFixed(2)+"｜购买影响 "+Number(b.impact||0).toFixed(1))+'">'+escapeHtml(b.label||"")+'</button>').join(""):"<div class='map-empty'>当前筛选暂无有效标签</div>";
 document.querySelector("#opportunity-table").innerHTML="<thead><tr><th>产品点</th><th>诊断</th><th>事实强度</th><th>认知/热度</th><th>机会分</th></tr></thead><tbody>"+ranked.map(item=>{const factStrength=nullableNumber(item.factStrength),recognition=nullableNumber(item.recognition),heat=nullableNumber(item.heat),opportunityScore=nullableNumber(item.opportunityScore);return"<tr><td><b>"+escapeHtml(item.label||"—")+"</b></td><td><span class='tag "+(item.mapDiagnosis==="优先修复"?"risk":item.mapDiagnosis==="持续放大"?"asset":"")+"'>"+escapeHtml(item.mapDiagnosis)+"</span></td><td>"+(factStrength===null?"—":(factStrength*100).toFixed(0)+"%")+"</td><td>"+(recognition===null?"—":(recognition*100).toFixed(0)+"% / "+(heat===null?"—":(heat*100).toFixed(0)+"%"))+"</td><td>"+(opportunityScore===null?"待确认":opportunityScore.toFixed(1))+"</td></tr>"}).join("")+"</tbody>";
}
function renderOpportunityMap(a){
 return renderDataFirstNsrMap();
 if(opportunityEvidenceState.result){renderServerOpportunityMap();return}
 const all=opportunityMapLabels(a.labels.filter(x=>x.op+x.on+x.cp+x.cn>0)),filtered=mapFilter==="all"?all:all.filter(x=>x.mapDiagnosis===mapFilter),ranked=[...filtered].sort((x,y)=>bigness(y)-bigness(x)),shown=ranked.slice(0,mapLimit),maxGap=Math.max(...all.map(x=>Math.abs(x.gap)),.01);
 document.querySelectorAll("#map-filters button").forEach(button=>{const count=button.dataset.filter==="all"?all.length:all.filter(x=>x.mapDiagnosis===button.dataset.filter).length;button.classList.toggle("active",button.dataset.filter===mapFilter);button.disabled=false;button.classList.toggle("empty-filter",count===0);button.title=count?String(count)+" 个标签":"当前数据没有"+button.dataset.filter+"，仍可查看空状态"});
 document.querySelector("#map-limit").value=String(mapLimit);
 document.querySelector("#map-summary").textContent=isSummaryImport()?`当前筛选 ${filtered.length} 个产品点，地图显示 Top ${shown.length}。横轴按本品与各竞品车型的真实属性 NSR 均值计算，纵轴使用购买影响。`:`当前筛选 ${filtered.length} 个标签，地图显示 Top ${shown.length}。策略分类已按风险、竞品领先度与本品资产动态校准。`;
 const surface=document.querySelector("#opportunity-map"),surfaceWidth=Math.max(surface.clientWidth,320),surfaceHeight=Math.max(surface.clientHeight,360);
 surface.innerHTML=shown.length?layoutBubbles(shown.map(x=>{const left=50+(x.gap/maxGap)*42,bottom=Math.min(88,Math.max(9,x.impact/5*84)),cls=x.mapDiagnosis==="优先修复"?"risk":x.mapDiagnosis==="抢占空位"?"chance":"asset";return{...x,left,bottom,cls,w:Math.max(58,x.label.length*13+24),h:30}}),surfaceWidth,surfaceHeight).map(b=>{const title=Number.isFinite(b.ownNsr)?`${b.label}｜${b.mapDiagnosis}｜本品NSR ${(b.ownNsr*100).toFixed(1)}%｜竞品均值 ${(b.competitorNsr*100).toFixed(1)}%｜Gap ${b.gap>=0?"+":""}${(b.gap*100).toFixed(1)}%`:`${b.label}｜${b.mapDiagnosis}｜Gap ${(b.gap*100).toFixed(1)}%｜优先级 ${b.priority.toFixed(1)}`;return`<span class="bubble ${b.cls}" style="left:${b.x}%;bottom:${b.y}%" title="${title}">${b.label}</span>`}).join(""):`<div class="map-empty">当前筛选暂无有效标签</div>`;
 document.querySelector("#opportunity-table").innerHTML=`<thead><tr><th>认知标签</th><th>赛道</th><th>诊断</th><th>本品负向</th><th>认知 Gap</th><th>Impact</th><th>优先级</th></tr></thead><tbody>${ranked.map(x=>`<tr><td><b>${x.label}</b></td><td>${x.category}</td><td><span class="tag ${x.mapDiagnosis==="优先修复"?"risk":x.mapDiagnosis==="持续放大"?"asset":""}">${x.mapDiagnosis}</span></td><td class="negative">${Math.round(x.on).toLocaleString()}</td><td>${(x.gap*100).toFixed(1)}%</td><td>${x.impact.toFixed(1)}</td><td>${x.priority.toFixed(1)}</td></tr>`).join("")}</tbody>`;
}
function bigness(x){return (x.priority||0)*1000+(x.on||0)+Math.max(x.op||0,x.cp||0)}
function layoutBubbles(items,vw=860,vh=380){
 const placed=[],pad=8,maxRadius=Math.hypot(vw/2,vh/2),overlap=(a,b)=>!(a.x+a.w/2+pad<b.x-b.w/2||a.x-a.w/2-pad>b.x+b.w/2||a.y+a.h/2+pad<b.y-b.h/2||a.y-a.h/2-pad>b.y+b.h/2);
 const boundsFor=it=>{let minX=it.w/2+4,maxX=vw-it.w/2-4,minY=it.h/2+4,maxY=vh-it.h/2-4;const axisPad=pad/2;if(it.quadrantX==="left")maxX=Math.min(maxX,vw/2-it.w/2-axisPad);if(it.quadrantX==="right")minX=Math.max(minX,vw/2+it.w/2+axisPad);if(it.quadrantY==="high")maxY=Math.min(maxY,vh/2-it.h/2-axisPad);if(it.quadrantY==="low")minY=Math.max(minY,vh/2+it.h/2+axisPad);return{minX,maxX,minY,maxY}};
 return items.sort((a,b)=>b.priority-a.priority).map(it=>{const baseX=it.left/100*vw,baseY=(100-it.bottom)/100*vh,candidates=[],bounds=boundsFor(it),clamp=(value,min,max)=>Math.min(max,Math.max(min,value));for(let r=0;r<=maxRadius;r+=12){for(let deg=0;deg<360;deg+=24){const rad=deg*Math.PI/180,x=clamp(baseX+Math.cos(rad)*r,bounds.minX,bounds.maxX),y=clamp(baseY+Math.sin(rad)*r,bounds.minY,bounds.maxY);candidates.push({x,y,dist:Math.hypot(x-baseX,y-baseY)})}}candidates.sort((a,b)=>a.dist-b.dist);const pick=candidates.find(c=>!placed.some(p=>overlap({...c,w:it.w,h:it.h},p)))||candidates[0];const b={...it,x:pick.x/vw*100,y:100-pick.y/vh*100,_x:pick.x,_y:pick.y,w:it.w,h:it.h};placed.push({x:pick.x,y:pick.y,w:it.w,h:it.h});return b}).sort((a,b)=>a.left-b.left);
}
function nsrMapInputRows(){
 return (state.rows||[]).map(row=>({model:row[0],source:row[2],category:row[3],label:row[4],impact:nullableNumber(row[9]),nsr:nullableNumber(row[14])})).filter(row=>row.model&&row.source&&row.label&&row.nsr!==null);
}
function nsrMapModelCode(model){
 const value=String(model||"").trim();
 const known=value.match(/Q6L|E7X|YU7|M7|Model\s*Y/i)?.[0];
 if(known)return known.replace(/\s+/g," ");
 const code=value.replace(/奥迪|问界|小米|特斯拉|Tesla/gi,"").replace(/\s+/g,"").trim();
 return (code||value||"车型").slice(0,10);
}
function nsrMapSelection(rows){
 const models=[...new Set(rows.map(row=>row.model).filter(Boolean))];
 const own=models.includes(state.config.model)?state.config.model:(models[0]||"");
 nsrMapSelectedModels=nsrMapSelectedModels.filter(model=>models.includes(model)&&model!==own);
 if(!nsrMapSelectionInitialized){nsrMapSelectedModels=models.filter(model=>model!==own);nsrMapSelectionInitialized=true}
 return {models,own,selected:[own,...nsrMapSelectedModels]};
}
function nsrMapItemKey(item){return `${item.model}::${item.label}`}
// Opportunity pills are CSS-capped at 132px; keep a small collision margin
// without letting long labels force the whole quadrant into one column.
function nsrMapBubbleWidth(label,benchmarkLabel){return 136}
function nsrMapRequiredHeight(items,width){
 const groups=new Map();
 items.forEach(item=>{const x=item.quadrantX||"axis",y=item.quadrantY||"axis",key=`${x}:${y}`,group=groups.get(key)||{count:0,x};group.count+=1;groups.set(key,group)});
 const widest=Math.max(...items.map(item=>item.w||136),136),mapWidth=Math.max(width,320),rows=Math.max(...[...groups.values()].map(group=>{const availableWidth=group.x==="axis"?mapWidth-16:mapWidth/2-12,columns=Math.max(1,Math.floor(availableWidth/(widest+8)));return Math.ceil(group.count/columns)}),1);
 return Math.max(450,(rows*60+30)*2);
}
function nsrMapOwnDecisionItems(result,own){
 return result.items.filter(item=>item.model===own).map(item=>{
  const ranked=MmnNsrMap.rankNsrLabel(result,item.label),ownRow=ranked.find(row=>row.isOwn),rankedCompetitors=ranked.filter(row=>!row.isOwn&&row.rank),benchmark=ownRow?.rank===1?rankedCompetitors[0]:rankedCompetitors.find(row=>row.rank===1)||rankedCompetitors[0],gap=benchmark&&Number.isFinite(benchmark.nsr)&&Number.isFinite(item.nsr)?benchmark.nsr-item.nsr:0;
  return{...item,gap,benchmarkModel:benchmark?.model||"",benchmarkNsr:benchmark?.nsr??null,ownRank:ownRow?.rank||null,ownRankTotal:ownRow?.rankTotal||0,benchmarkLabel:!benchmark?"待补竞品":ownRow?.rank===1?"本品领先":`对标 ${nsrMapModelCode(benchmark.model)}`,priority:item.priority+Math.abs(gap)*25};
 }).sort((a,b)=>b.priority-a.priority||a.label.localeCompare(b.label,"zh-CN"));
}
function nsrMapDetailMarkup(result,item){
 const ranked=MmnNsrMap.rankNsrLabel(result,item.label),own=ranked.find(row=>row.isOwn),sourceDetail=result.expectedSources.map(source=>`${source} ${Number.isFinite(item.sourceScores[source])?(item.sourceScores[source]*100).toFixed(1)+"%":"—"}`).join(" / ");
 const ownRank=own?.rank?`第 ${own.rank} / ${own.rankTotal}`:"数据不足";
 return `<section class="nsr-map-detail" data-nsr-map-detail="${escapeAttr(nsrMapItemKey(item))}" role="dialog" aria-label="${escapeAttr(`${item.label}车型排名`)}"><header><div><span>属性竞争判断 · 已含本品</span><b>${escapeHtml(item.label)} <small>${own?.rank?`本品第 ${own.rank}/${own.rankTotal}`:"本品待补数"}</small></b></div><button type="button" data-nsr-map-close aria-label="关闭${escapeAttr(item.label)}排名气泡">×</button></header><div class="nsr-map-detail-metrics"><div><span>本品排名</span><b>${escapeHtml(ownRank)}</b></div><div><span>主要对标</span><b>${escapeHtml(item.benchmarkModel||"暂无有效竞品")}</b></div><div><span>本品状态</span><b>${escapeHtml(item.statusLabel)}</b></div></div><ol aria-label="${escapeAttr(`${item.label}当前已选车型排名`)}">${ranked.map(row=>`<li class="${row.isOwn?"own ":""}${row.status==="data_missing"?"missing":""}"><em>${row.rank?`#${row.rank}`:"补数"}</em><div><b>${escapeHtml(row.model)}${row.isOwn?"<span>本品</span>":""}</b><small>${row.rank?`NSR ${(row.nsr*100).toFixed(1)}% · ${escapeHtml(row.coverageLabel)}`:escapeHtml(row.coverageLabel||"数据不足，不参与排名")}</small></div></li>`).join("")}</ol><p>判断基准：${item.benchmarkModel?`${escapeHtml(state.config.model)} vs ${escapeHtml(item.benchmarkModel)}`:"当前竞品数据不足"}<small>${escapeHtml(sourceDetail)}</small></p></section>`;
}
function nsrMapItemNames(items,own){
 return items.slice(0,4).map(item=>item.model===own?item.label:`${item.label}（${nsrMapModelCode(item.model)}）`).join("、")||"暂无";
}
function nsrMapInsights(result,own){
 const box=document.querySelector("#nsr-map-insights");if(!box)return;
 const ownItems=result.items.filter(item=>item.model===own),strength=ownItems.filter(item=>item.status==="strength"),neutral=ownItems.filter(item=>item.status==="neutral"),risk=ownItems.filter(item=>item.status==="risk"),missing=ownItems.filter(item=>item.status==="data_missing");
 box.innerHTML=`<article class="nsr-map-insight strength"><b>可巩固</b><span>${escapeHtml(own)}：${escapeHtml(nsrMapItemNames(strength,own))}${strength.length?"可持续放大。":"暂无达到稳定优势门槛的属性。"}</span></article><article class="nsr-map-insight neutral"><b>需加强</b><span>${neutral.length?`${escapeHtml(nsrMapItemNames(neutral,own))}跨来源表现不稳定，优先优化用户认知与表达。`:"当前本品暂无中性待加强标签。"}</span></article><article class="nsr-map-insight risk"><b>风险与数据完整性</b><span>${risk.length?`${escapeHtml(nsrMapItemNames(risk,own))}存在负向风险。`:"暂无显著负向风险。"}${missing.length?` ${escapeHtml(nsrMapItemNames(missing,own))}数据不足，仅作补数提示。`:""}</span></article>`;
}
function renderDataFirstNsrMap(){
 const controls=document.querySelector("#nsr-map-models"),legend=document.querySelector("#nsr-map-legend"),surface=document.querySelector("#opportunity-map"),summary=document.querySelector("#map-summary");
 if(!controls||!legend||!surface||!summary)return;
 const rows=nsrMapInputRows(),selection=nsrMapSelection(rows);
 if(!rows.length||!selection.own||typeof MmnNsrMap==="undefined"||typeof MmnNsrMap.buildDataFirstNsrMap!=="function"){
  const partialSummary=isSummaryImport()&&state.importQuality?.attributeNsrAvailable===false;
  controls.innerHTML=`<span class="nsr-map-empty-controls">${partialSummary?"当前汇总表已导入整体指标，但未提供属性 NSR。":"请先导入包含属性 NSR 的产品评价数据。"}</span>`;
  legend.innerHTML="";surface.style.height="";surface.innerHTML=`<div class="map-empty">${partialSummary?"源表没有属性 NSR，机会地图不计算、不推断。":"当前数据没有可计算的属性 NSR 地图。"}</div>`;summary.textContent=partialSummary?"整体声量、互动量与全网 NSR 已保留；补充属性 NSR 后，本图会自动生成。":"机会地图只依据导入数据中的属性 NSR 计算，不调用官网、双模型或人工确认链路。";document.querySelector("#nsr-map-insights").innerHTML="";return;
 }
 const expectedSources=state.importQuality?.attributeNsrSources?.length?state.importQuality.attributeNsrSources:[...new Set(rows.map(row=>row.source))];
 const result=MmnNsrMap.buildDataFirstNsrMap({rows,ownModel:selection.own,selectedModels:selection.selected,expectedSources});
 controls.innerHTML=`<section class="nsr-map-own"><span>本品基准</span><select id="nsr-map-own-model" aria-label="选择本品基准">${selection.models.map(model=>`<option value="${escapeAttr(model)}" ${model===selection.own?"selected":""}>${escapeHtml(model)}</option>`).join("")}</select><small class="nsr-map-own-fixed">本品固定展示</small></section><section class="nsr-map-compare"><span>对比车型</span><div>${selection.models.filter(model=>model!==selection.own).map(model=>`<button type="button" class="nsr-map-model-toggle ${nsrMapSelectedModels.includes(model)?"selected":""}" data-nsr-map-model="${escapeAttr(model)}" aria-pressed="${nsrMapSelectedModels.includes(model)?"true":"false"}">${escapeHtml(model)}</button>`).join("")}</div></section><small>车型可多选；标签按导入数据自动排序，无需再筛选标签。</small>`;
 legend.innerHTML='<b>本品竞争力状态</b><span class="strength">优势，可巩固</span><span class="neutral">中性，需加强</span><span class="risk">风险，优先补强</span><span class="data-missing">数据不足</span><small>每项属性只显示一次；灰色标签表示主要对标车型或本品领先</small>';
 const decisions=nsrMapOwnDecisionItems(result,selection.own),primary=decisions.filter(item=>item.status!=="data_missing"),coverage=decisions.filter(item=>item.status==="data_missing"),shown=[...primary,...coverage].sort((left,right)=>right.priority-left.priority),maxGap=Math.max(...shown.map(item=>Math.abs(item.gap)),.01),width=Math.max(surface.clientWidth,320);
 if(nsrMapActiveItemKey&&!shown.some(item=>nsrMapItemKey(item)===nsrMapActiveItemKey))nsrMapActiveItemKey="";
 const activeItem=shown.find(item=>nsrMapItemKey(item)===nsrMapActiveItemKey);
 const bubbleInputs=shown.map(item=>{const left=50+(item.gap/maxGap)*42,bottom=Math.min(88,Math.max(9,item.impact/5*84)),cls=item.status==="strength"?"asset":item.status==="risk"?"risk":item.status==="neutral"?"chance":"pending";return{...item,left,bottom,cls,quadrantX:item.gap<0?"left":item.gap>0?"right":"axis",quadrantY:item.impact>3?"high":item.impact<3?"low":"axis",w:nsrMapBubbleWidth(item.label,item.benchmarkLabel),h:32}}),requiredHeight=nsrMapRequiredHeight(bubbleInputs,width);
 surface.style.height=`${requiredHeight}px`;
 surface.innerHTML=shown.length?layoutBubbles(bubbleInputs,width,requiredHeight).map(item=>{const sourceDetail=result.expectedSources.map(source=>`${source} ${Number.isFinite(item.sourceScores[source])?(item.sourceScores[source]*100).toFixed(1)+"%":"—"}`).join(" / "),title=`${state.config.model}｜${item.label}｜${item.statusLabel}｜${item.benchmarkModel?`主要对标 ${item.benchmarkModel}｜`:""}${sourceDetail}`,key=nsrMapItemKey(item);return`<button type="button" class="bubble ${item.cls}${key===nsrMapActiveItemKey?" active":""}" data-nsr-map-detail="${escapeAttr(key)}" style="left:${item.x}%;bottom:${item.y}%" title="${escapeAttr(title)}" aria-pressed="${key===nsrMapActiveItemKey?"true":"false"}"><span>${escapeHtml(item.label)}</span><small>${escapeHtml(item.benchmarkLabel)}</small></button>`}).join("")+(activeItem?nsrMapDetailMarkup(result,activeItem):""):'<div class="map-empty">当前所选车型没有可展示的属性 NSR。</div>';
 summary.textContent=`基于导入的 ${result.expectedSources.join(" / ")} 属性 NSR 自动计算；当前展示 ${shown.length} 个优先标签。蓝色仅提示数据缺口，不参与竞争力强弱判断。`;
 nsrMapInsights(result,selection.own);
 document.querySelector("#nsr-map-own-model").onchange=event=>{nsrMapActiveItemKey="";nsrMapSelectedModels=nsrMapSelectedModels.filter(model=>model!==event.target.value);selectDashboardVehicleContext(event.target.value,{source:"nsr-map"})};
 controls.querySelectorAll("[data-nsr-map-model]").forEach(button=>button.onclick=()=>{const model=button.dataset.nsrMapModel;nsrMapSelectedModels=nsrMapSelectedModels.includes(model)?nsrMapSelectedModels.filter(value=>value!==model):[...nsrMapSelectedModels,model];renderDataFirstNsrMap()});
 surface.querySelectorAll("button[data-nsr-map-detail]").forEach(button=>button.onclick=()=>{nsrMapActiveItemKey=button.dataset.nsrMapDetail;renderDataFirstNsrMap()});
 surface.querySelector("[data-nsr-map-close]")?.addEventListener("click",()=>{nsrMapActiveItemKey="";renderDataFirstNsrMap()});
 return result;
}
function dataRowsForView(){
 return state.rows.map((r,i)=>({r,i})).filter(x=>(dataBrandFilter==="all"||brandForDisplay(x.r[0])===dataBrandFilter)&&(dataModelFilter==="all"||x.r[0]===dataModelFilter)&&(dataTrafficFilter==="all"||trafficType(x.r)===dataTrafficFilter)&&x.r.join(" ").toLowerCase().includes(dataSearch.toLowerCase()));
}
function isContentPlatform(platform){return ["抖音","小红书"].includes(String(platform||"").trim())}
function trafficType(r){
 if(!isContentPlatform(r[2]))return"其他平台";
 const explicit=String(r[12]||"").trim();
 if(/商业|投放|广告|合作|报备|达人|kol|KOL|官方|品牌|蒲公英|巨量|dou\+|DOU\+/i.test(explicit))return"商业化声量";
 if(/自然|自来水|用户|车主|口碑|ugc|UGC|真实|体验/i.test(explicit))return"自然声量";
 const text=r.join(" ");
 if(/信息流|广告|投放|商业化|达人合作|KOL|kol|报备|品牌号|官方|挑战赛|硬广|软广|蒲公英|巨量|dou\+|DOU\+/i.test(text))return"商业化声量";
 if(/车主|真实|提车|用车|口碑|吐槽|长测|测评|试驾|路人|自来水|UGC|ugc|用户证词|真实口碑/i.test(text))return"自然声量";
 return"未识别";
}
function aggregateRows(rows,idx){
 const m={};rows.forEach(({r})=>{const k=r[idx]||"未识别";if(!m[k])m[k]={key:k,count:0,positive:0,negative:0};const s=score(r);m[k].count+=+r[8]||0;m[k].positive+=s.positive;m[k].negative+=s.negative});return Object.values(m).sort((a,b)=>b.count-a.count);
}
function aggregateTraffic(rows){
 const m={};rows.filter(x=>isContentPlatform(x.r[2])).forEach(({r})=>{const k=`${r[2]} · ${trafficType(r)}`;if(!m[k])m[k]={key:k,count:0};m[k].count+=+r[8]||0});return Object.values(m).sort((a,b)=>b.count-a.count);
}
function renderDataBars(sel,data,mode="count",drill=""){
 const max=Math.max(...data.map(x=>x[mode]||0),1);
 document.querySelector(sel).innerHTML=data.slice(0,8).map(x=>`<button type="button" class="data-bar" data-drill="${drill}" data-key="${escapeAttr(x.key)}" title="点击查看${x.key}拆解"><b>${x.key}</b><div><i class="${mode==="negative"?"neg":""}" style="width:${(x[mode]||0)/max*100}%"></i></div><span>${Math.round(x[mode]||0).toLocaleString()}</span></button>`).join("")||"<p class='empty'>暂无数据</p>";
 document.querySelectorAll(`${sel} [data-drill]`).forEach(b=>b.onclick=()=>openDataDrill(b.dataset.drill,b.dataset.key));
}
function emotionMeaning(name){
 return {
  兴奋:"强正向情绪，代表用户被卖点、体验或内容强烈打动，适合放大为核心传播资产。",
  惊喜:"超预期正向反馈，通常来自配置、价格、体验反差或内容创意，可转化成破圈素材。",
  期待:"潜在购买兴趣，用户还在等待价格、权益、交付、实测或口碑证据，需要持续转化。",
  信任:"稳定正向信号，说明证据链有效，可沉淀为品牌传播口径和长期口碑资产。",
  认可:"理性正向评价，说明用户接受某个产品点或品牌动作，适合做垂媒/社区解释型内容。",
  自豪:"身份认同型正向情绪，适合做车主故事、社群传播和用户共创。",
  怀疑:"低强度疑虑，用户还没被证据说服，需要补第三方验证、真实车主和透明解释。",
  焦虑:"购买阻力正在形成，常见于价格、权益、补能、质量和交付，需要优先释疑。",
  失望:"明确负向反馈，说明用户预期落空，需要定位触发点并用产品改进或证据修复。",
  愤怒:"高风险负向情绪，可能扩散成公关问题，需要快速响应、统一口径和闭环机制。",
  后悔:"强购买后负向，影响口碑推荐和复购，需要售后、车主沟通和问题闭环。",
  嘲讽:"社交化负向表达，容易二创扩散，需要避免硬刚，用事实证据和轻量化回应降温。"
 }[name]||"该标签代表一类用户情绪，需要结合平台、赛道、认知标签和样本明细判断下一步动作。";
}
function rowsForDrill(type,key){
 const base=dataRowsForView();
 const idx={platform:2,category:3,emotion:5,label:4}[type];
 if(type==="traffic")return base.filter(x=>`${x.r[2]} · ${trafficType(x.r)}`===key);
 if(idx!==undefined)return base.filter(x=>String(x.r[idx]||"未识别")===key);
 return base;
}
function topBreakdown(rows,idx,limit=5){
 return aggregateRows(rows,idx).slice(0,limit);
}
function drillPlan(type,key,rows){
 const total=rows.reduce((s,x)=>s+(+x.r[8]||0),0),scores=rows.reduce((m,x)=>{const s=score(x.r);m.p+=s.positive;m.n+=s.negative;return m},{p:0,n:0});
 const topLabel=topBreakdown(rows,4,1)[0]?.key||key,topPlatform=topBreakdown(rows,2,1)[0]?.key||"核心平台",topCategory=topBreakdown(rows,3,1)[0]?.key||"核心赛道";
 const isBad=scores.n>scores.p||["失望","焦虑","怀疑","愤怒","后悔","嘲讽"].includes(key);
 const direction=isBad?"先修复，再转化":"先放大，再转化";
 const action=isBad?`围绕“${topLabel}”建立证据链：第三方实测、车主真实反馈、官方解释三层内容同步上。`:`把“${topLabel}”包装成可复述卖点：短视频强画面、垂媒理性解释、车主证词共同放大。`;
 return{total,scores,lines:[
  `判断：${key} 当前主要集中在 ${topPlatform} / ${topCategory}，有效样本 ${total.toLocaleString()}。`,
  `策略：${direction}。${action}`,
  `下一步：把该拆解结果进入“行动与预算”，优先制作 ${topPlatform} 内容包，并跟踪该情绪占比和负向风险变化。`
 ]};
}
function qwenContext(type,key,rows,plan){
 const rag=ragSearch({query:key,rows,limit:5});
 return {
  project: state.config.project,
  brand: state.config.brand,
  model: state.config.model,
  competitor: state.config.competitor,
  drillType: type,
  drillKey: key,
  summary: {
   samples: plan.total,
   positiveScore: Math.round(plan.scores.p),
   negativeScore: Math.round(plan.scores.n)
  },
  breakdown: {
   models: topBreakdown(rows,0),
   platforms: topBreakdown(rows,2),
   categories: topBreakdown(rows,3),
   labels: topBreakdown(rows,4),
   emotions: topBreakdown(rows,5)
  },
  wordCloud: wordCloudForRows(rows),
  knowhow: plan.lines,
  learning: rows.length ? similarLearnings(topBreakdown(rows,4,1)[0]?.key||key,3) : [],
  ragReferences: rag
 };
}
function wordCloudForRows(rows){
 const dict=[
  ["产品卖点",["智驾","智能驾驶","座舱","空间","舒适","底盘","操控","续航","补能","安全","质量","内饰","外观","动力"]],
  ["价格权益",["价格","权益","优惠","补贴","金融","定价","性价比","贵","值"]],
  ["使用场景",["家庭","通勤","长途","露营","亲子","城市","高速","二排","后备箱"]],
  ["信任风险",["怀疑","焦虑","失望","愤怒","后悔","吐槽","质量","安全","故障","投诉","品牌信任"]],
  ["内容表达",["抖音","小红书","达人","KOL","测评","试驾","长测","车主","口碑","官方","投放"]],
  ["竞品对比",["竞品","对比","PK","理想","小米","蔚来","极氪","特斯拉","问界"]]
 ];
 const m={};
 rows.forEach(({r})=>{
  const text=r.join(" ");
  dict.forEach(([group,words])=>words.forEach(w=>{if(text.includes(w)){const key=`${group} / ${w}`;m[key]=(m[key]||0)+(+r[8]||1)}}));
 });
 return Object.entries(m).map(([key,count])=>({key,count})).sort((a,b)=>b.count-a.count).slice(0,18);
}
function drillKnowhowHtml(type,key,rows){
 const topLabel=topBreakdown(rows,4,1)[0]?.key||key,topCategory=topBreakdown(rows,3,1)[0]?.key||"",scores=rows.reduce((m,x)=>{const s=score(x.r);m.p+=s.positive;m.n+=s.negative;return m},{p:0,n:0});
 const diagnosis=scores.n>scores.p?"优先修复":"持续放大",k=knowhowFor({label:topLabel,category:topCategory,diagnosis,priority:0}),learned=latestLearning(topLabel)||similarLearnings(topLabel,1)[0],kb=ragSearch({query:`${key} ${topLabel} ${topCategory}`,rows,limit:3});
 return `<div class="drill-grid drill-knowledge">
  <article><h3>Know-how 建议</h3><dl><dt>核心判断</dt><dd>${k.why}</dd><dt>参考打法</dt><dd>${k.message}</dd><dt>证据链</dt><dd>${learned?.evidence||k.proof}</dd><dt>平台动作</dt><dd>${learned?.platform||k.platform}</dd><dt>KPI</dt><dd>${learned?.kpi||k.kpi}</dd></dl></article>
  <article><h3>Learning / RAG引用依据</h3>${learned?`<div class="learned-tip"><b>已学习案例</b><span>${learned.conclusion||"已保存人工判断"}</span><em>${learned.recommendation||""}</em></div>`:`<p class="empty">当前还没有针对“${topLabel}”的人工学习案例。可以在“人工结论学习”里补充判断，之后这里会自动引用。</p>`}${kb.length?`<div class="kb-tip"><b>RAG召回知识</b>${kb.map(item=>`<span><strong>${item.title}</strong>｜${item.body}<em>依据：${item.reason}｜分数 ${item.score}</em></span>`).join("")}</div>`:`<p class="empty">RAG知识库暂无匹配片段。</p>`}</article>
 </div>`;
}
function drillWordCloudHtml(rows){
 const words=wordCloudForRows(rows);
 return `<article class="drill-wordcloud"><h3>词云分类</h3><div>${words.length?words.map((x,i)=>`<span style="--s:${Math.max(12,22-i)}px">${x.key}<em>${Math.round(x.count).toLocaleString()}</em></span>`).join(""):`<p class="empty">当前导入数据缺少原始评论、标题、字幕或关键词，只能基于赛道/标签做弱分类。建议补充原文或词云字段。</p>`}</div><small>建议补充：原始评论、内容标题、字幕全文、话题标签、搜索词、作者类型、互动量、商业化/自然声量标记。</small></article>`;
}
function openDataDrill(type,key){
 const rows=rowsForDrill(type,key),dialog=document.querySelector("#data-drill-dialog"),body=document.querySelector("#data-drill-body");
 const labels={platform:"平台",category:"赛道",emotion:"情绪",label:"认知标签",traffic:"声量性质"},plan=drillPlan(type,key,rows);
 currentDrillContext=qwenContext(type,key,rows,plan);
 document.querySelector("#data-drill-title").textContent=`${labels[type]||"声量"}拆解｜${key}`;
 const summary=[["样本量",plan.total.toLocaleString()],["正向分",Math.round(plan.scores.p).toLocaleString()],["负向风险",Math.round(plan.scores.n).toLocaleString()],["涉及车型",new Set(rows.map(x=>x.r[0])).size.toLocaleString()]];
 const detailRows=rows.slice().sort((a,b)=>(+b.r[8]||0)-(+a.r[8]||0)).slice(0,12);
 body.innerHTML=`${type==="emotion"?`<div class="drill-meaning"><b>${key}是什么</b><p>${emotionMeaning(key)}</p></div>`:""}
 <div class="trend-summary">${summary.map(x=>`<div><span>${x[0]}</span><b>${x[1]}</b><small>${key}</small></div>`).join("")}</div>
 <div class="drill-grid">
  <article><h3>按车型拆</h3>${drillMiniBars(topBreakdown(rows,0))}</article>
  <article><h3>按平台拆</h3>${drillMiniBars(topBreakdown(rows,2))}</article>
  <article><h3>按赛道拆</h3>${drillMiniBars(topBreakdown(rows,3))}</article>
  <article><h3>按认知标签拆</h3>${drillMiniBars(topBreakdown(rows,4))}</article>
 </div>
 ${drillWordCloudHtml(rows)}
 ${drillKnowhowHtml(type,key,rows)}
 <article class="drill-plan"><div class="drill-plan-head"><h3>归总后的下一步营销规划</h3><div class="multi-model-actions"><button type="button" class="primary" data-strategy-engine="fusion" id="qwen-strategy">MMN策略</button></div></div>${plan.lines.map(x=>`<p>${x}</p>`).join("")}<div id="qwen-strategy-result" class="qwen-result"></div></article>
 <div class="table-wrap mini"><table><thead><tr><th>车型</th><th>平台</th><th>赛道</th><th>标签</th><th>情绪</th><th>声量类型</th><th>样本</th></tr></thead><tbody>${detailRows.map(({r})=>`<tr><td><b>${r[0]}</b></td><td>${r[2]}</td><td>${r[3]}</td><td>${r[4]}</td><td>${r[5]}</td><td>${trafficType(r)}</td><td>${(+r[8]||0).toLocaleString()}</td></tr>`).join("")}</tbody></table></div>`;
 document.querySelectorAll("[data-strategy-engine]").forEach(b=>b.onclick=()=>generateModelStrategy(b.dataset.strategyEngine,b));
 dialog.showModal();
}
async function generateModelStrategy(engine,btn){
 const result=document.querySelector("#qwen-strategy-result");
 if(!result||!currentDrillContext)return;
 const oldText=btn.textContent;
 btn.disabled=true;btn.textContent="生成中…";
 const label={qwen:"MMN策略",openai:"MMN策略",fusion:"MMN策略"}[engine]||"MMN策略";
 const endpoint={qwen:"/api/ai/qwen-strategy",openai:"/api/ai/openai-strategy",fusion:"/api/ai/fusion-strategy"}[engine]||"/api/ai/fusion-strategy";
 result.innerHTML=`<h4>${label}生成中</h4><p>正在分析当前拆解、词云、Know-how、Learning 和 RAG 引用。通常需要 10-45 秒。</p>`;
 result.scrollIntoView({block:"nearest",behavior:"smooth"});
 try{
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
  const res=await fetch(endpoint,{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({context:currentDrillContext}),signal:controller.signal});
  clearTimeout(timer);
  const data=await res.json().catch(()=>({ok:false,error:"模型接口返回格式异常"}));
  if(!res.ok||!data.ok)throw new Error(data.error||`${label}生成失败`);
  const partLabels={qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"};
  const parts=data.parts?`<details class="model-parts"><summary>查看MMN引擎过程记录</summary>${Object.entries(data.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${partLabels[k]||k}</b>${String(v).split(/\n+/).filter(Boolean).map(x=>`<p>${x}</p>`).join("")}</section>`).join("")}${data.errors&&Object.keys(data.errors).length?`<section><b>缺席/错误</b>${Object.entries(data.errors).map(([k,v])=>`<p>${partLabels[k]||k}: ${v}</p>`).join("")}</section>`:""}</details>`:"";
  result.innerHTML=`<h4>${label}建议</h4>${String(data.text||"").split(/\n+/).filter(Boolean).map(x=>`<p>${x}</p>`).join("")}${parts}`;
 }catch(e){
  const msg=e.name==="AbortError"?"生成超过 90 秒，已自动停止。建议缩小筛选范围，或稍后重试。":e.message;
  result.innerHTML=`<h4>${label}暂未生成</h4><p>${msg}</p><p>请检查MMN多模态能力配置、网络连通性和额度。本土规则引擎会作为策略兜底。</p>`;
 }finally{btn.disabled=false;btn.textContent=oldText}
}
function drillMiniBars(data){
 const max=Math.max(...data.map(x=>x.count),1);
 return `<div class="drill-bars">${data.map(x=>`<div><b>${x.key}</b><span><i style="width:${x.count/max*100}%"></i></span><em>${Math.round(x.count).toLocaleString()}</em></div>`).join("")||"<p class='empty'>暂无数据</p>"}</div>`;
}
const semanticLayerLabels={
 vehicle_models:"车型",
 product_attributes:"产品属性",
 emotion_tendency:"情绪倾向",
 purchase_blockers:"购买阻塞点",
 competitor_relations:"竞品关系",
 identity_expression:"身份表达",
 scene_needs:"场景需求",
 strategy_actions:"策略动作"
};
function semanticItemsToText(items){
 return (items||[]).map(x=>x.model||x.label||x.raw||"").filter(Boolean).join("，");
}
function semanticTextToItems(text,layer){
 return String(text||"").split(/[，,、\n]+/).map(x=>x.trim()).filter(Boolean).map(x=>layer==="vehicle_models"?{raw:x,model:x,label:x,confidence:"manual"}:{label:x,evidence:"人工校准",confidence:"manual"});
}
function semanticCorrectedPayload(){
 const layers={};
 Object.keys(semanticLayerLabels).forEach(key=>{
  const el=document.querySelector(`[data-semantic-edit="${key}"]`);
  layers[key]=semanticTextToItems(el?.value||"",key);
 });
 return{...semanticState.result,layers,calibratedAt:new Date().toISOString(),calibratedBy:"manual"};
}
function renderSemanticResult(){
 const box=document.querySelector("#semantic-result");
 if(!box)return;
 const result=semanticState.result;
 if(!result){box.innerHTML="";return}
 const layers=result.layers||{};
 const cards=Object.entries(semanticLayerLabels).map(([key,label])=>{
  const items=layers[key]||[];
  const chips=items.length?items.map(x=>`<span title="${escapeAttr(x.evidence||"")}"><b>${escapeAttr(x.model||x.label||x.raw)}</b><em>${escapeAttr(x.confidence||"medium")}</em></span>`).join(""):`<small>未识别，可人工补充</small>`;
  return `<article><div><h3>${label}</h3><small>${semanticState.schema?.[key]||""}</small></div><div class="semantic-chips">${chips}</div><textarea data-semantic-edit="${key}">${escapeAttr(semanticItemsToText(items))}</textarea></article>`;
 }).join("");
 box.innerHTML=`<div class="semantic-summary"><b>${result.summary||"已完成多层语义识别"}</b><span>${result.model||"MMN语义识别"}｜置信度 ${result.confidence||"medium"}</span></div><div class="semantic-grid">${cards}</div><div class="semantic-calibration"><input id="semantic-note" placeholder="人工校准备注，例如：把‘家用’强制归入家庭场景，后续同类表达参考"><button type="button" class="primary" id="semantic-save-calibration">保存人工校准</button></div>`;
 document.querySelector("#semantic-save-calibration").onclick=saveSemanticCalibration;
}
async function analyzeSemanticText(){
 const input=document.querySelector("#semantic-input"),btn=document.querySelector("#semantic-analyze");
 const text=input?.value.trim();
 if(!text){toast("请先输入一条用户原文");return}
 const old=btn.textContent;btn.disabled=true;btn.textContent="识别中…";
 try{
  const data=await api("/api/semantic/analyze",{method:"POST",body:JSON.stringify({edition:activeEdition(),text})});
  semanticState={result:data.result,schema:data.schema};
  renderSemanticResult();
  toast("已输出多层语义标签，可人工校准");
 }catch(err){toast(`语义识别失败：${err.message}`)}
 finally{btn.disabled=false;btn.textContent=old}
}
async function saveSemanticCalibration(){
 if(!semanticState.result){toast("请先完成语义识别");return}
 try{
  const corrected=semanticCorrectedPayload();
  const note=document.querySelector("#semantic-note")?.value||"";
  await api("/api/semantic/calibrate",{method:"POST",body:JSON.stringify({edition:activeEdition(),sourceText:semanticState.result.sourceText,predicted:semanticState.result,corrected,userNote:note})});
  semanticState.result=corrected;
  renderSemanticResult();
  toast("人工校准已保存，后续可用于优化语义识别");
 }catch(err){toast(`保存校准失败：${err.message}`)}
}
function renderData(){
 const sourceNote=state.sourceNote||"当前数据已载入。";
 const legacyImportNote=sourceNote.includes("属性层级 NSR 已拆分为正/负两类聚合行");
 document.querySelector("#data-source-note").textContent=legacyImportNote
  ?"本次分析聚焦 2026.5.1—6.4 的六款车用户讨论，重点对比智己L6与小米SU7、Model 3、蔚来ET5T、蔚来ET5、极氪007，看看哪些卖点真正被认可、哪些问题正在拖累口碑。"
  :sourceNote;
 renderSemanticResult();
 const models=dataModelOptions();if(dataModelFilter!=="all"&&!models.includes(dataModelFilter))dataModelFilter="all";
 ensureModelIdentities(models);
 const groups=brandModelGroups(models);
 if(dataBrandFilter!=="all"&&!groups.some(g=>g.brand===dataBrandFilter)){dataBrandFilter="all";dataModelFilter="all"}
 document.querySelector("#data-model-filter").innerHTML=`<button class="${dataBrandFilter==="all"&&dataModelFilter==="all"?"active":""}" data-data-brand="all" data-data-model="all">全部品牌 / 全部车型</button>${groups.map(g=>`<details class="brand-model-group" ${dataBrandFilter===g.brand||g.models.includes(dataModelFilter)?"open":""}><summary><button type="button" class="${dataBrandFilter===g.brand&&dataModelFilter==="all"?"active":""}" data-data-brand="${escapeAttr(g.brand)}" data-data-model="all">${g.brand}<small>${g.models.length}款</small></button></summary><div>${g.models.map(m=>`<button title="${escapeAttr(canonicalModelLabel(m))}" class="${m===dataModelFilter?"active":""}" data-data-brand="${escapeAttr(g.brand)}" data-data-model="${escapeAttr(m)}">${canonicalModelLabel(m)}</button>`).join("")}</div></details>`).join("")}`;
 document.querySelectorAll("[data-data-model]").forEach(b=>b.onclick=e=>{e.preventDefault();dataBrandFilter=b.dataset.dataBrand||"all";dataModelFilter=b.dataset.dataModel||"all";renderData()});
 document.querySelector("#data-traffic-filter").innerHTML=[["all","全部声量"],["商业化声量","商业化声量"],["自然声量","自然声量"],["未识别","未识别"]].map(([value,label])=>`<button class="${value===dataTrafficFilter?"active":""}" data-traffic-type="${value}">${label}</button>`).join("");
 document.querySelectorAll("[data-traffic-type]").forEach(b=>b.onclick=()=>{dataTrafficFilter=b.dataset.trafficType;renderData()});
 const rows=dataRowsForView(),total=rows.reduce((s,x)=>s+(+x.r[8]||0),0),scores=rows.reduce((m,x)=>{const s=score(x.r);m.p+=s.positive;m.n+=s.negative;return m},{p:0,n:0}),platforms=new Set(rows.map(x=>x.r[2]).filter(Boolean));
 document.querySelector("#data-model-samples").textContent=total.toLocaleString();
 document.querySelector("#data-positive-score").textContent=Math.round(scores.p).toLocaleString();
 document.querySelector("#data-negative-score").textContent=Math.round(scores.n).toLocaleString();
 document.querySelector("#data-platform-count").textContent=platforms.size.toLocaleString();
 renderDataBars("#data-traffic-chart",aggregateTraffic(rows),"count","traffic");
 document.querySelector("#data-traffic-rule").innerHTML=[
  ["商业化声量","投放、广告、达人合作、KOL、报备、官方、品牌号、蒲公英、巨量等线索。"],
  ["自然声量","车主、真实体验、提车、用车、口碑、吐槽、测评、试驾、自来水、UGC 等线索。"],
  ["未识别","导入数据没有声量类型字段，且文本线索不足；建议在模板中补充“声量类型”。"]
 ].map(x=>`<div><b>${x[0]}</b><span>${x[1]}</span></div>`).join("");
 renderDataBars("#data-platform-chart",aggregateRows(rows,2),"count","platform");
 renderDataBars("#data-category-chart",aggregateRows(rows,3),"count","category");
 renderDataBars("#data-emotion-chart",aggregateRows(rows,5),"count","emotion");
 renderDataBars("#data-label-chart",aggregateRows(rows,4),"count","label");
 const shownHeaders=[...headers,"声量类型","关键词/原文"];
 document.querySelector("#data-table").innerHTML=`<thead><tr>${shownHeaders.map(h=>`<th>${h}</th>`).join("")}<th>正向分</th><th>负向分</th><th>操作</th></tr></thead><tbody>${rows.map(({r,i})=>{const s=score(r),shown=[...r.slice(0,12).map((v,idx)=>idx===1?(r[0]===state.config.model?"本品":"竞品"):v),trafficType(r),r[13]||""];return`<tr>${shown.map(v=>`<td>${typeof v==="number"?v.toLocaleString():v}</td>`).join("")}<td class="positive">${Math.round(s.positive).toLocaleString()}</td><td class="negative">${Math.round(s.negative).toLocaleString()}</td><td><button class="ghost delete-row" data-i="${i}">删除</button></td></tr>`}).join("")}</tbody>`;
 document.querySelectorAll(".delete-row").forEach(b=>b.onclick=()=>{state.rows.splice(+b.dataset.i,1);save();render();toast("数据已删除")});
}
function renderCognition(a){
 const models=cognitionModelOptions();
 renderCognitionSelectors(a,models);
 renderCognitionMmnStrategy(a);
 const rows=a.labels||[];
 document.querySelector("#cognition-table").innerHTML=`<thead><tr><th>认知标签</th><th>一级赛道</th><th>本品正向</th><th>本品负向</th><th>竞品正向</th><th>本品占有率</th><th>竞品占有率</th><th>认知 Gap</th><th>Impact</th><th>White Space</th><th>诊断</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><b>${x.label}</b></td><td>${x.category}</td><td class="positive">${Math.round(x.op).toLocaleString()}</td><td class="negative">${Math.round(x.on).toLocaleString()}</td><td>${Math.round(x.cp).toLocaleString()}</td><td>${(x.oShare*100).toFixed(1)}%</td><td>${(x.cShare*100).toFixed(1)}%</td><td>${(x.gap*100).toFixed(1)}%</td><td>${x.impact.toFixed(1)}</td><td>${x.white.toFixed(1)}</td><td><span class="tag ${x.diagnosis==="优先修复"?"risk":x.diagnosis==="持续放大"?"asset":""}">${x.diagnosis}</span></td></tr>`).join(""):`<tr><td class="empty-cell" colspan="11">当前车型还没有可用于认知诊断的声量标签。请先在声量数据中心或内容资产中心导入相关数据。</td></tr>`}</tbody>`;
}
function renderCognitionSelectors(a,models){
 const brandSel=document.querySelector("#cognition-brand-select"),modelSel=document.querySelector("#cognition-model-select"),note=document.querySelector("#cognition-model-note");
 if(!brandSel||!modelSel)return;
 const groups=cognitionBrandModelGroups(models);
 const currentBrand=brandForDisplay(state.config.model)||brandForModel(state.config.model)||groups[0]?.brand||"待确认品牌";
 cognitionBrandOpen=groups.some(g=>g.brand===cognitionBrandOpen)?cognitionBrandOpen:currentBrand;
 const activeGroup=groups.find(g=>g.brand===cognitionBrandOpen)||groups[0]||{brand:"暂无品牌",models:[]};
 const activeModels=activeGroup.models||[];
 brandSel.innerHTML=groups.length?groups.map(g=>`<option value="${escapeAttr(g.brand)}" ${g.brand===activeGroup.brand?"selected":""}>${g.brand}（${g.models.length}款）</option>`).join(""):`<option>暂无可选品牌</option>`;
 modelSel.innerHTML=activeModels.length?activeModels.map(m=>`<option value="${escapeAttr(m)}" ${m===state.config.model?"selected":""}>${canonicalModelLabel(m)}</option>`).join(""):`<option>暂无可选车型</option>`;
 brandSel.onchange=()=>{
  cognitionBrandOpen=brandSel.value;
  const next=cognitionBrandModelGroups(cognitionModelOptions()).find(g=>g.brand===cognitionBrandOpen)?.models?.[0];
  if(next){
   cognitionStrategyState={loading:false,result:null,error:""};
   selectDashboardVehicleContext(next,{source:"cognition"});
  }
 };
 modelSel.onchange=()=>{
  if(!modelSel.value)return;
  cognitionStrategyState={loading:false,result:null,error:""};
  cognitionBrandOpen=brandForDisplay(modelSel.value)||brandForModel(modelSel.value);selectDashboardVehicleContext(modelSel.value,{source:"cognition"});
 };
 if(note)note.textContent=`${brandForDisplay(state.config.model)} / ${canonicalModelLabel(state.config.model)}｜${(a.labels||[]).length} 个认知标签`;
}
function cognitionStrategyContext(a=analysis()){
 const model=state.config.model,competitors=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
 const ownRows=state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]===model);
 const compRows=state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]!==model&&(competitors.includes(x.r[0])||x.r[1]==="竞品"));
 const scopedRows=ownRows.length?[...ownRows,...compRows]:state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]===model||competitors.includes(x.r[0]));
 const verticalItems=(verticalState.items||[]).filter(x=>x.ownModel===model||x.competitor===model||competitors.includes(x.competitor)||competitors.includes(x.ownModel));
 const periods=uniquePeriods(verticalItems),latestPeriod=periods[periods.length-1]||"",latestVertical=latestPeriod?verticalItems.filter(x=>x.period===latestPeriod):verticalItems.slice(-12);
 return{
  drillType:"cognition_strategy",
  drillKey:model,
  question:"请基于认知赛道诊断，调用决策驾驶舱、声量数据中心和垂媒竞争格局，为当前品牌车型输出可执行营销策略。外显结果必须是MMN多模态策略输出。",
  project:{edition:activeEdition(),brand:brandForDisplay(model),model,competitors,project:state.config.project,stage:state.config.stage||"上市/增长期"},
  summary:{...metricValues(a),positiveScore:Math.round(a.pos||0),negativeScore:Math.round(a.neg||0),ownSamples:isSummaryImport()?null:a.ownComments||0,assetCount:(a.labels||[]).filter(x=>x.diagnosis==="持续放大").length,riskCount:(a.labels||[]).filter(x=>x.diagnosis==="优先修复").length,spaceCount:(a.labels||[]).filter(x=>x.diagnosis==="抢占空位").length},
  breakdown:{labels:(a.labels||[]).slice(0,12).map(x=>({label:x.label,category:x.category,diagnosis:x.diagnosis,priority:+(x.priority||0).toFixed(2),gap:+(x.gap||0).toFixed(3),white:+(x.white||0).toFixed(2),ownPositive:Math.round(x.op||0),ownNegative:Math.round(x.on||0),competitorPositive:Math.round(x.cp||0)})),platforms:topBreakdown(scopedRows,2,8),categories:topBreakdown(scopedRows,3,8),emotions:topBreakdown(scopedRows,5,8)},
  verticalCompetition:{latestPeriod,relations:latestVertical.slice(0,16).map(x=>({platform:x.platform,period:x.period,ownModel:x.ownModel,competitor:x.competitor,positiveRank:x.positiveRank,negativeRank:x.negativeRank,share:x.share,status:rankStatus(x)}))},
  references:ragSearch({query:[model,...competitors,"认知资产","认知负债","空位","营销策略"].join(" "),rows:scopedRows,limit:6}),
  outputPolicy:{visibleBrand:"MMN多模态策略输出",requiredModels:["qwen","deepseek"],requiredSections:["Executive Conclusion","Key Findings","Evidence","Strategic Implication","Action Recommendation"]}
 };
}
function localCognitionStrategyDraft(ctx){
 const model=ctx.project?.model||"当前车型",labels=ctx.breakdown?.labels||[];
 const asset=labels.find(x=>x.diagnosis==="持续放大")||labels[0]||{},risk=labels.find(x=>x.diagnosis==="优先修复")||labels.find(x=>x.ownNegative>0)||{},space=labels.find(x=>x.diagnosis==="抢占空位")||labels.find(x=>x.white>0)||{};
 const topPlatform=ctx.breakdown?.platforms?.[0]?.key||"核心平台",relation=ctx.verticalCompetition?.relations?.[0];
 const comp=relation?.competitor||(ctx.project?.competitors||[])[0]||"核心竞品";
 const relationLine=relation?`${relation.platform}${relation.period?` ${relation.period}`:""}中，${model}与${comp}的关系是“${relation.status}”，正向排名${relation.positiveRank||"未上榜"}、反向排名${relation.negativeRank||"未上榜"}。`:`垂媒竞争格局用于校准竞品口径，避免只在内部标签里自我判断。`;
 return consultingOutputText({
  conclusion:`${model}应把“${asset.label||"已有好评"}”沉淀为认知资产，优先用证据修复“${risk.label||"购买疑虑"}”，再抢占“${space.label||"竞品空位"}”。`,
  findings:[`- “${asset.label||"核心正向标签"}”具备继续放大的条件。[Evidence: E1]`,`- “${risk.label||"高风险疑虑"}”是当前购买阻塞点。[Evidence: E1]`,`- “${space.label||"认知空位"}”可用于建立与 ${comp} 的同场景差异。[Evidence: E2]`],
  evidence:[`- E1：当前诊断已区分认知资产、负债与空位，具体数值沿用当前页面口径。`,`- E2：${relationLine}`,`- E3：当前优先平台为 ${topPlatform}。`],
  implication:"先修复认知负债可避免传播放大疑虑；再放大资产和空位，才能把内容互动转成差异化购买理由。",
  actions:[`- P0｜7天｜内容团队：在 ${topPlatform} 完成“一个疑虑一个证据”内容包；以负向疑虑占比验证。`,`- P1｜14天｜竞品团队：围绕 ${comp} 做同场景对比；以认知Gap和垂媒排名验证。`,`- P2｜30天｜品牌与达人团队：用评测证据、车主场景和品牌FAQ承接询价与试驾。`]
 });
}
function renderCognitionMmnStrategy(a){
 const box=document.querySelector("#cognition-mmn-output"),status=document.querySelector("#cognition-mmn-status");
 if(!box)return;
 const ctx=cognitionStrategyContext(a),result=cognitionStrategyState.result||{text:localCognitionStrategyDraft(ctx),parts:{rules:localCognitionStrategyDraft(ctx)},context:ctx};
 if(status)status.textContent=cognitionStrategyState.loading?"MMN正在交叉验证":mmnTraceLabel(result);
 const parts=result.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(result.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"}[k]||publicMmnProviderLabel(k)}</b>${markdownish(String(v))}</section>`).join("")}${result.errors&&Object.keys(result.errors).length?`<section><b>缺席/错误</b>${Object.entries(result.errors).map(([k,v])=>`<p>${publicMmnProviderLabel(k)}: ${publicMmnText(v)}</p>`).join("")}</section>`:""}</details>`:"";
 box.innerHTML=`<div class="content-mmn-head"><div><b>${cognitionStrategyState.loading?"MMN正在生成认知策略":"MMN多模态策略输出"}</b><span>决策驾驶舱 + 声量数据中心 + 垂媒竞争格局｜${ctx.project.brand} / ${canonicalModelLabel(ctx.project.model)}｜MMN交叉验证</span></div><button type="button" class="primary" id="run-cognition-mmn-strategy" ${cognitionStrategyState.loading?"disabled":""}>${cognitionStrategyState.loading?"生成中…":"生成/刷新MMN策略"}</button></div><div class="content-mmn-output">${consultingMarkdown(String(result.text||""))}</div>${cognitionStrategyState.error?`<p class="empty">模型生成失败，已使用MMN本地策略输出：${cognitionStrategyState.error}</p>`:""}${parts}`;
 const btn=document.querySelector("#run-cognition-mmn-strategy");
 if(btn)btn.onclick=()=>runCognitionMmnStrategy();
}
async function runCognitionMmnStrategy(silent=false){
 const ctx=cognitionStrategyContext(analysis()),fallback=localCognitionStrategyDraft(ctx);
 cognitionStrategyState={loading:true,result:{text:fallback,parts:{rules:fallback},context:ctx},error:""};
 renderCognitionMmnStrategy(analysis());
 try{
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
  const res=await fetch("/api/ai/fusion-strategy",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({context:ctx}),signal:controller.signal});
  clearTimeout(timer);
  const data=await res.json().catch(()=>({ok:false,error:"模型接口返回格式异常"}));
  if(!res.ok||!data.ok)throw new Error(data.error||"MMN认知策略生成失败");
  cognitionStrategyState={loading:false,result:{...data,context:ctx},error:""};
  if(!silent)toast("MMN已完成认知赛道多模态策略交叉验证");
 }catch(err){
  cognitionStrategyState={loading:false,result:{text:fallback,parts:{rules:fallback},context:ctx},error:err.name==="AbortError"?"模型生成超过90秒":err.message};
  if(!silent)toast("MMN认知策略暂用本地规则兜底");
 }
 renderCognitionMmnStrategy(analysis());
}
function renderVertical(){
 const allItems=canonicalVerticalItems(verticalState.items||[]),allSources=verticalState.sources||[];
 if(!allItems.length)restoreVerticalAssetsFromServer();
 const platformOptions=["all",...[...new Set(allItems.map(x=>x.platform).filter(Boolean))].sort()];
 const selectedPlatform=platformOptions.includes(verticalState.selectedPlatform)?verticalState.selectedPlatform:"all";
 verticalState.selectedPlatform=selectedPlatform;
 const platformItems=selectedPlatform==="all"?allItems:allItems.filter(x=>x.platform===selectedPlatform);
 const availableSources=[...new Set(platformItems.map(x=>x.source).filter(Boolean))];
 const sourceOptions=["all",...availableSources];
 const selectedSource=sourceOptions.includes(verticalState.selectedSource)?verticalState.selectedSource:"all";
 verticalState.selectedSource=selectedSource;
 const scopedItems=selectedSource==="all"?platformItems:platformItems.filter(x=>x.source===selectedSource);
 const models=[...new Set(scopedItems.map(x=>x.ownModel).filter(Boolean))].sort();
 if(models.length&&!models.includes(verticalState.selectedModel))verticalState.selectedModel=models[0];
 if(!models.length)verticalState.selectedModel="";
 const model=verticalState.selectedModel||models[0]||"";
 const modelItems=scopedItems.filter(x=>x.ownModel===model);
 const competitors=[...new Set(modelItems.map(x=>x.competitor).filter(Boolean))].sort();
 if(competitors.length&&!competitors.includes(verticalState.selectedCompetitor))verticalState.selectedCompetitor=competitors[0];
 if(!competitors.length)verticalState.selectedCompetitor="";
 const comp=verticalState.selectedCompetitor||competitors[0]||"";
 const modelPeriods=uniquePeriods(modelItems),latest=modelPeriods[modelPeriods.length-1]||"—",activePeriod=verticalState.selectedPeriod&&verticalState.selectedPeriod!=="latest"&&modelPeriods.includes(verticalState.selectedPeriod)?verticalState.selectedPeriod:latest,latestRows=modelItems.filter(x=>x.period===activePeriod).sort((a,b)=>(a.positiveRank||999)-(b.positiveRank||999));
 verticalState.selectedPeriod=activePeriod||"latest";
 const filtered=modelItems.filter(x=>[x.platform,x.period,x.ownModel,x.competitor,x.source].join(" ").toLowerCase().includes(verticalSearch.toLowerCase()));
 const sourceLabel=selectedPlatform==="all"?"全部来源":selectedPlatform;
 const asset=verticalState.assetSummary;
 const assetCopy=asset?`车型资产库：${asset.brandCount||0} 个品牌、${asset.modelCount||0} 个车型、${asset.relationCount||0} 条正反向关系、${asset.periodCount||0} 个周期。`:"";
 document.querySelector("#vertical-source-note").textContent=allItems.length?`已导入 ${allSources.length||availableSources.length} 份垂媒排名文件。${assetCopy} 当前口径：${sourceLabel} / ${model||"未选择本品"}。`:"支持汽车之家、懂车帝正反向排名 Excel。导入后会沉淀车型、品牌、周期和正反向关系，形成长期车型数据资产。";
 const learningBox=document.querySelector("#vertical-ai-learning");
 if(learningBox)learningBox.innerHTML=modelItems.length?`<div class="ai-learning-bar"><div><b>MMN智能体学习</b><span>把 ${model} 在 ${sourceLabel} / ${activePeriod||"当前周期"} 的正反向关系交给三路旗舰能力分析，并融合为一个MMN策略结论后写入RAG。</span></div><button type="button" class="primary" id="vertical-ai-learn">MMN学习正反向</button></div><div id="vertical-ai-learning-result"></div>`:"";
 document.querySelector("#vertical-model-count").textContent=models.length.toLocaleString();
 document.querySelector("#vertical-pair-count").textContent=new Set(modelItems.map(x=>`${x.ownModel}|${x.competitor}`)).size.toLocaleString();
 document.querySelector("#vertical-period-count").textContent=modelPeriods.length.toLocaleString();
 document.querySelector("#vertical-latest-period").textContent=`${sourceLabel}｜${activePeriod||"—"}`;
 const platformSelect=document.querySelector("#vertical-platform"),sourceSelect=document.querySelector("#vertical-source-file"),modelSelect=document.querySelector("#vertical-model"),compSelect=document.querySelector("#vertical-competitor");
 platformSelect.innerHTML=platformOptions.map(p=>`<option value="${p}" ${p===selectedPlatform?"selected":""}>${p==="all"?"全部来源":p}</option>`).join("");
 if(sourceSelect)sourceSelect.innerHTML=sourceOptions.map(s=>`<option value="${escapeAttr(s)}" ${s===selectedSource?"selected":""}>${s==="all"?"全部文件":shortSourceName(s)}</option>`).join("");
 modelSelect.innerHTML=models.map(m=>`<option ${m===model?"selected":""}>${m}</option>`).join("");
 compSelect.innerHTML=competitors.map(c=>`<option ${c===comp?"selected":""}>${c}</option>`).join("");
 platformSelect.onchange=e=>{verticalState.selectedPlatform=e.target.value;verticalState.selectedSource="all";verticalState.selectedModel="";verticalState.selectedCompetitor="";verticalState.selectedPeriod="latest";saveVerticalState();renderVertical()};
 if(sourceSelect)sourceSelect.onchange=e=>{verticalState.selectedSource=e.target.value;verticalState.selectedModel="";verticalState.selectedCompetitor="";verticalState.selectedPeriod="latest";saveVerticalState();renderVertical()};
 modelSelect.onchange=e=>{verticalState.selectedModel=e.target.value;verticalState.selectedCompetitor="";verticalState.selectedPeriod="latest";saveVerticalState();renderVertical()};
 compSelect.onchange=e=>{verticalState.selectedCompetitor=e.target.value;saveVerticalState();renderVertical()};
 const latestComp=latestRows.find(x=>x.competitor===comp),bestPos=latestRows[0],bestNeg=[...latestRows].sort((a,b)=>(a.negativeRank||999)-(b.negativeRank||999))[0];
 document.querySelector("#vertical-rank-board").innerHTML=modelItems.length?[
  ["当前选择",`${model||"—"} vs ${comp||"—"}`,latestComp?`${latestComp.platform}｜${activePeriod}｜正向第 ${latestComp.positiveRank||"—"}｜反向第 ${latestComp.negativeRank||"—"}`:"当前本品所选周期暂无该竞品"],
  ["正向第一",bestPos?.competitor||"—",bestPos?`${bestPos.platform}｜正向第 ${bestPos.positiveRank}｜反向第 ${bestPos.negativeRank||"—"}`:"—"],
  ["反向第一",bestNeg?.competitor||"—",bestNeg?`${bestNeg.platform}｜正向第 ${bestNeg.positiveRank||"—"}｜反向第 ${bestNeg.negativeRank}`:"—"]
 ].map(x=>`<div class="rank-card"><span>${x[0]}</span><b>${x[1]}</b><small>${x[2]}</small></div>`).join(""):"<p class='empty'>请先导入垂媒排名 Excel。</p>";
 renderVerticalTrend(modelItems.filter(x=>x.competitor===comp),modelPeriods);
 renderPeriodPicker(modelPeriods,activePeriod);
 const matrix=enforceVerticalMatrixPeriod(competitors.map(c=>buildCompetitionMatrixRow(modelItems,c,activePeriod,modelPeriods)).filter(x=>x.current),activePeriod);
 document.querySelector("#vertical-ranking-table").innerHTML=`<thead><tr><th>竞品车型</th><th><button class="th-period" id="period-toggle" title="选择数据抓取周期">当前周期：${activePeriod||"—"}</button></th><th>正向排名</th><th>较上一周期</th><th>反向排名</th><th>较上一周期</th><th>完整趋势</th><th>对比占比</th><th>状态</th></tr></thead><tbody>${matrix.length?matrix.sort((a,b)=>(a.current.positiveRank||999)-(b.current.positiveRank||999)).map(x=>`<tr><td><b>${x.competitor}</b><small>${x.current.platform}</small></td><td><b>${activePeriod}</b><small>${x.prev?`对比 ${x.prev.period}`:"无上一周期记录"}</small></td><td title="同一来源、同一周期、同一本品车型内的相同名次会标记为并列">${rankDisplay(x,"positiveRank",matrix)}</td><td>${rankDelta(x.posDelta)}</td><td title="同一来源、同一周期、同一本品车型内的相同名次会标记为并列">${rankDisplay(x,"negativeRank",matrix)}</td><td>${rankDelta(x.negDelta)}</td><td><button class="trend-open" data-competitor="${escapeAttr(x.competitor)}" title="查看完整周期趋势">${miniTrend(x.rows)}</button></td><td>${formatShare(x.current.share)}</td><td><span class="tag ${rankStatus(x.current)==="高关注高对比"?"risk":rankStatus(x.current)==="正向关注强"?"asset":""}">${rankStatus(x.current)}</span></td></tr>`).join(""):`<tr><td colspan="9"><p class="empty">当前周期 ${activePeriod||"—"} 没有该本品的竞品关系记录。请切换周期或检查原始排名文件。</p></td></tr>`}</tbody>`;
 document.querySelector("#period-toggle").onclick=()=>{verticalPeriodPickerOpen=!verticalPeriodPickerOpen;renderVertical()};
 document.querySelectorAll(".trend-open").forEach(b=>b.onclick=()=>openTrendDialog(modelItems,b.dataset.competitor,model,modelPeriods));
 const learnButton=document.querySelector("#vertical-ai-learn");
 if(learnButton)learnButton.onclick=()=>runVerticalAiLearning({model,platform:selectedPlatform==="all"?(latestRows[0]?.platform||sourceLabel):selectedPlatform,period:activePeriod,source:selectedSource==="all"?(latestRows[0]?.source||""):selectedSource,rows:latestRows});
 document.querySelector("#vertical-table").innerHTML=`<thead><tr><th>来源</th><th>文件</th><th>周期</th><th>本品车型</th><th>竞品车型</th><th>正向排名</th><th>反向排名</th><th>对比占比</th></tr></thead><tbody>${filtered.sort((a,b)=>sortVerticalItem(a,b)||(a.positiveRank||999)-(b.positiveRank||999)).map(x=>`<tr><td>${x.platform}</td><td>${shortSourceName(x.source)}</td><td>${x.period}</td><td><b>${x.ownModel}</b></td><td>${x.competitor}</td><td>${x.positiveRank||"—"}</td><td>${x.negativeRank||"—"}</td><td>${formatShare(x.share)}</td></tr>`).join("")}</tbody>`;
}
async function runVerticalAiLearning(context){
 const box=document.querySelector("#vertical-ai-learning-result"),button=document.querySelector("#vertical-ai-learn"),originalLabel=button?.textContent;
 if(!context?.rows?.length){toast("当前车型没有可学习的正反向数据");return}
 if(button){button.disabled=true;button.textContent="分析融合中…"}
 if(box)box.innerHTML="<p>MMN正在完成三路分析，并融合为一个策略结论…</p>";
 try{
  const data=await api("/api/ai/vertical-rank-learning",{method:"POST",body:JSON.stringify({edition:activeEdition(),context:{...context,rows:context.rows.slice(0,30).map(x=>({competitor:x.competitor,positiveRank:x.positiveRank,negativeRank:x.negativeRank,share:x.share,status:rankStatus(x)}))}})});
  if(data.knowledgeItem)mergeStrategyKnowledge([data.knowledgeItem]);
  const persisted=Boolean(data.knowledgeItem),stateLabel=data.statusLabel||"三路分析状态待确认";
  const checks=data.analysisChecks||{},completed=Object.values(checks).filter(value=>value==="completed").length;
  if(box)box.innerHTML=`<article class="rag-card mmn-consulting-card"><span>${escapeHtml(stateLabel)}｜${context.platform}｜${context.period}</span><b>${context.model} 正反向竞争格局融合结论</b><div class="mmn-consulting-body">${consultingMarkdown(data.text)}</div><small>${persisted?"三路分析已融合为唯一结论并写入RAG知识库，可被巡检和MMN策略召回。":`当前仅完成 ${completed}/4 个分析与融合步骤；只展示规则预览，不写入RAG知识库。`}</small></article>`;
  if(persisted){renderStrategyKb();toast("MMN已把三路分析融合为一个结论，并写入RAG知识库")}else toast(stateLabel);
 }catch(err){
  if(box)box.innerHTML=`<p class="empty">MMN学习失败：${err.message}</p>`;
  toast(`MMN学习失败：${err.message}`);
 }finally{if(button){button.disabled=false;button.textContent=originalLabel||"MMN学习正反向"}}
}
function shortSourceName(s){return String(s||"").replace(/\.xlsx$/i,"").replace(/[-_]?更新到\d+/,"")}
function formatShare(v){const n=nullableNumber(v);if(n===null||n<0)return"—";return `${(n>1?n:n*100).toFixed(1)}%`}
function escapeAttr(s){return String(s||"").replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}
function renderPeriodPicker(periods,activePeriod){
 const el=document.querySelector("#vertical-period-picker");if(!el)return;
 el.classList.toggle("open",verticalPeriodPickerOpen);
 el.innerHTML=`<div><b>数据抓取周期</b><span>选择一个周期查看当期竞争格局，变化值对比上一周期</span></div><div class="period-chips">${periods.map(p=>`<button class="${p===activePeriod?"active":""}" data-period="${p}">${p}</button>`).join("")}</div>`;
 el.querySelectorAll("[data-period]").forEach(b=>b.onclick=()=>{verticalState.selectedPeriod=b.dataset.period;verticalPeriodPickerOpen=false;saveVerticalState();renderVertical()});
}
function buildCompetitionMatrixRow(items,competitor,activePeriod,periods=[]){
 const rows=items.filter(x=>x.competitor===competitor).sort(sortVerticalItem);
 const current=rows.find(x=>x.period===activePeriod)||null;
 const activeIdx=periods.indexOf(activePeriod);
 const previousPeriods=activeIdx>0?periods.slice(0,activeIdx).reverse():[];
 const prev=previousPeriods.map(p=>rows.find(x=>x.period===p)).find(Boolean)||null;
 return{competitor,rows,current,prev,posDelta:prev&&current?.positiveRank&&prev.positiveRank?prev.positiveRank-current.positiveRank:null,negDelta:prev&&current?.negativeRank&&prev.negativeRank?prev.negativeRank-current.negativeRank:null};
}
function enforceVerticalMatrixPeriod(matrix,activePeriod){
 const bad=matrix.filter(x=>x.current?.period!==activePeriod);
 if(bad.length)console.error("MMN周期矩阵发现非当前周期记录，已过滤", {activePeriod,bad:bad.map(x=>({competitor:x.competitor,period:x.current?.period}))});
 return matrix.filter(x=>x.current?.period===activePeriod);
}
function rankDelta(v){
 if(v===null||v===undefined)return"<span class='delta flat'>—</span>";
 if(v>0)return`<span class="delta up">↑${v}</span>`;
 if(v<0)return`<span class="delta down">↓${Math.abs(v)}</span>`;
 return"<span class='delta flat'>持平</span>";
}
function rankDisplay(item,field,matrix=[]){
 const current=item?.current||item,rank=Number(current?.[field]);
 if(!Number.isFinite(rank)||rank<=0)return"—";
 const sourceKey=current.source||current.platform||"";
 const ties=matrix.filter(entry=>{
  const peer=entry.current||entry;
  return peer&&peer.period===current.period&&peer.ownModel===current.ownModel&&peer.platform===current.platform&&(peer.source||peer.platform||"")===sourceKey&&Number(peer[field])===rank;
 }).length;
 return ties>1?`并列第 ${rank}`:`第 ${rank}`;
}
function miniTrend(rows){
 const data=[...rows].sort(sortVerticalItem).slice(-6),maxRank=Math.max(10,...data.flatMap(x=>[x.positiveRank||0,x.negativeRank||0])),w=120,h=34,pad=4;
 if(!data.length)return"—";
 const pts=key=>data.map((x,i)=>{const vx=i/Math.max(1,data.length-1),rank=x[key]||maxRank,y=pad+(rank-1)/(maxRank-1)*(h-pad*2);return`${pad+vx*(w-pad*2)},${y}`}).join(" ");
 return`<svg class="mini-trend" viewBox="0 0 ${w} ${h}"><polyline class="pos-line" points="${pts("positiveRank")}"></polyline><polyline class="neg-line" points="${pts("negativeRank")}"></polyline></svg>`;
}
function openTrendDialog(modelItems,competitor,ownModel,allPeriods=[]){
 const rows=modelItems.filter(x=>x.competitor===competitor).sort(sortVerticalItem);
 if(!rows.length)return;
 const dialog=document.querySelector("#trend-dialog"),body=document.querySelector("#trend-dialog-body");
 document.querySelector("#trend-dialog-title").textContent=`${ownModel} vs ${competitor}｜竞争趋势详情`;
 const latest=rows[rows.length-1],first=rows[0],posChange=first?.positiveRank&&latest?.positiveRank?first.positiveRank-latest.positiveRank:null,negChange=first?.negativeRank&&latest?.negativeRank?first.negativeRank-latest.negativeRank:null;
 const periods=(allPeriods&&allPeriods.length?allPeriods:uniquePeriods(rows)),byPeriod=new Map(rows.map(x=>[x.period,x]));
 body.innerHTML=`<div class="trend-summary"><div><span>数据来源</span><b>${latest.platform}</b><small>${shortSourceName(latest.source)}</small></div><div><span>周期范围</span><b>${periods[0]} → ${periods[periods.length-1]}</b><small>${rows.length}/${periods.length} 个周期有排名</small></div><div><span>正向变化</span><b>${plainRankDelta(posChange)}</b><small>排名越小越靠前</small></div><div><span>反向变化</span><b>${plainRankDelta(negChange)}</b><small>排名越小越强</small></div></div><div class="trend-large">${largeTrend(rows,periods)}</div><div class="table-wrap mini"><table><thead><tr><th>周期</th><th>正向排名</th><th>正向变化</th><th>反向排名</th><th>反向变化</th><th>对比占比</th><th>状态</th></tr></thead><tbody>${periods.map((p,i)=>{const x=byPeriod.get(p),prev=[...periods.slice(0,i)].reverse().map(pp=>byPeriod.get(pp)).find(Boolean),pos=x&&prev&&x.positiveRank&&prev.positiveRank?prev.positiveRank-x.positiveRank:null,neg=x&&prev&&x.negativeRank&&prev.negativeRank?prev.negativeRank-x.negativeRank:null;return x?`<tr><td><b>${x.period}</b></td><td>${x.positiveRank||"—"}</td><td>${rankDelta(pos)}</td><td>${x.negativeRank||"—"}</td><td>${rankDelta(neg)}</td><td>${formatShare(x.share)}</td><td><span class="tag ${rankStatus(x)==="高关注高对比"?"risk":rankStatus(x)==="正向关注强"?"asset":""}">${rankStatus(x)}</span></td></tr>`:`<tr><td><b>${p}</b></td><td colspan="6"><span class="empty">该周期未进入当前排名表 / 原始表无该竞品记录</span></td></tr>`}).join("")}</tbody></table></div>`;
 dialog.showModal();
}
function plainRankDelta(v){if(v===null||v===undefined)return"—";if(v>0)return`上升 ${v} 位`;if(v<0)return`下降 ${Math.abs(v)} 位`;return"持平"}
function trendPointLabelY(point,peer,series){const base=series==="pos"?-9:18;if(!peer||Math.abs(point.y-peer.y)>=32||point.y===peer.y)return point.y+base;return point.y<peer.y?point.y-9:point.y+18}
function trendLineSegments(points){const segments=[];let current=[];points.forEach(point=>{if(point){current.push(point);return}if(current.length){segments.push(current);current=[]}});if(current.length)segments.push(current);return segments}
function trendPolylineMarkup(points,className){return trendLineSegments(points).filter(segment=>segment.length>1).map(segment=>`<polyline class="${className}" points="${segment.map(point=>`${point.x},${point.y}`).join(" ")}"></polyline>`).join("")}
function trendGapConnectorMarkup(points,className){const observed=points.map((point,index)=>point?{point,index}:null).filter(Boolean);return observed.slice(1).map((current,index)=>{const previous=observed[index];if(current.index-previous.index<=1)return"";return`<line class="${className} gap-line" x1="${previous.point.x}" y1="${previous.point.y}" x2="${current.point.x}" y2="${current.point.y}"></line>`}).join("")}
function trendXAxisLabelIndexes(periods,maxLabels=6){if(periods.length<=maxLabels)return periods.map((_,index)=>index);const indexes=new Set([0,periods.length-1]);for(let slot=1;slot<maxLabels-1;slot++)indexes.add(Math.round(slot*(periods.length-1)/(maxLabels-1)));return [...indexes].sort((a,b)=>a-b)}
function trendXAxisMarkup(periods,present,w,pad,h){const indexes=new Set(trendXAxisLabelIndexes(periods));return periods.map((period,index)=>indexes.has(index)?`<text class="x-label ${present.has(period)?"":"missing"}" x="${pad+index/Math.max(1,periods.length-1)*(w-pad*2)}" y="${h-10}" text-anchor="middle"><title>${period}</title>${period}</text>`:"").join("")}
function largeTrend(rows,allPeriods=[]){
 const data=[...rows].sort(sortVerticalItem),periods=(allPeriods&&allPeriods.length?allPeriods:uniquePeriods(data)),byPeriod=new Map(data.map(x=>[x.period,x])),maxRank=Math.max(10,...data.flatMap(x=>[x.positiveRank||0,x.negativeRank||0])),w=760,h=280,pad=42,den=Math.max(1,periods.length-1);
 const pts=key=>periods.map((p,i)=>{const x=byPeriod.get(p);if(!x||!x[key])return null;const rank=x[key],y=pad+(rank-1)/(maxRank-1)*(h-pad*2);return{x:pad+i/den*(w-pad*2),y,rank,period:p}});
 const pos=pts("positiveRank"),neg=pts("negativeRank"),present=new Set(data.map(x=>x.period));
 return`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="正反向排名趋势；虚线表示跨越无记录周期">${[1,Math.ceil(maxRank/2),maxRank].map(r=>`<line x1="${pad}" y1="${pad+(r-1)/(maxRank-1)*(h-pad*2)}" x2="${w-pad}" y2="${pad+(r-1)/(maxRank-1)*(h-pad*2)}"></line><text x="10" y="${pad+(r-1)/(maxRank-1)*(h-pad*2)+4}">${r}</text>`).join("")}${trendPolylineMarkup(pos,"pos-line")}${trendPolylineMarkup(neg,"neg-line")}${trendGapConnectorMarkup(pos,"pos-line")}${trendGapConnectorMarkup(neg,"neg-line")}${pos.map((p,index)=>p?`<circle class="pos-dot" cx="${p.x}" cy="${p.y}" r="5"></circle><text class="point-label" x="${p.x}" y="${trendPointLabelY(p,neg[index],"pos")}" text-anchor="middle">${p.rank}</text>`:"").join("")}${neg.map((p,index)=>p?`<circle class="neg-dot" cx="${p.x}" cy="${p.y}" r="5"></circle><text class="point-label" x="${p.x}" y="${trendPointLabelY(p,pos[index],"neg")}" text-anchor="middle">${p.rank}</text>`:"").join("")}${trendXAxisMarkup(periods,present,w,pad,h)}</svg><div class="trend-legend"><span><i class="green"></i>正向排名</span><span><i class="red"></i>反向排名</span><span><i class="gap-key"></i>虚线跨越无记录周期</span></div>`;
}
function rankStatus(x){
 const p=x.positiveRank||999,n=x.negativeRank||999;
 if(p<=3&&n<=3)return"高关注高对比";
 if(p<=3)return"正向关注强";
 if(n<=3)return"反向被比强";
 return"常规竞品";
}
function uniquePeriods(items){const m=new Map();items.forEach(x=>{if(!x.period)return;const cur=m.get(x.period);if(!cur||String(x.periodOrder||x.period)>String(cur.order||cur.period))m.set(x.period,{period:x.period,order:x.periodOrder||x.period})});return [...m.values()].sort((a,b)=>String(a.order).localeCompare(String(b.order),"zh-CN",{numeric:true})).map(x=>x.period)}
function sortVerticalItem(a,b){return String(a.periodOrder||a.period||"").localeCompare(String(b.periodOrder||b.period||""), "zh-CN", {numeric:true})}
function sortPeriod(a,b){return String(a||"").localeCompare(String(b||""), "zh-CN", {numeric:true})}
function renderVerticalTrend(rows,allPeriods=[]){
 const el=document.querySelector("#vertical-trend-chart");
 if(!rows.length){el.innerHTML="<p class='empty'>选择一个竞品后展示时间轴趋势。</p>";return}
 const data=[...rows].sort(sortVerticalItem),periods=(allPeriods&&allPeriods.length?allPeriods:uniquePeriods(data));
 const byPeriod=new Map(data.map(x=>[x.period,x]));
 const maxRank=Math.max(10,...data.flatMap(x=>[x.positiveRank||0,x.negativeRank||0])),w=520,h=230,pad=34,den=Math.max(1,periods.length-1);
 const point=(x,i,key)=>{if(!x||!x[key])return null;const rank=x[key],y=pad+(rank-1)/(maxRank-1)*(h-pad*2);return{x:pad+i/den*(w-pad*2),y,rank,period:periods[i]}};
 const pts=key=>periods.map((p,i)=>point(byPeriod.get(p),i,key));
 const pos=pts("positiveRank"),neg=pts("negativeRank"),presentPeriods=new Set(data.map(x=>x.period));
 const missing=periods.length-data.length;
 el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="正反向排名趋势">${[1,Math.ceil(maxRank/2),maxRank].map(r=>`<line x1="${pad}" y1="${pad+(r-1)/(maxRank-1)*(h-pad*2)}" x2="${w-pad}" y2="${pad+(r-1)/(maxRank-1)*(h-pad*2)}"></line><text x="6" y="${pad+(r-1)/(maxRank-1)*(h-pad*2)+4}">${r}</text>`).join("")}${trendPolylineMarkup(pos,"pos-line")}${trendPolylineMarkup(neg,"neg-line")}${pos.filter(Boolean).map(p=>`<circle class="pos-dot" cx="${p.x}" cy="${p.y}" r="4"><title>${p.period} 正向第${p.rank}</title></circle>`).join("")}${neg.filter(Boolean).map(p=>`<circle class="neg-dot" cx="${p.x}" cy="${p.y}" r="4"><title>${p.period} 反向第${p.rank}</title></circle>`).join("")}${periods.map((p,i)=>`<text class="x-label ${presentPeriods.has(p)?"":"missing"}" x="${pad+i/den*(w-pad*2)}" y="${h-8}" text-anchor="middle">${p}</text>`).join("")}</svg><div class="trend-legend"><span><i class="green"></i>正向排名</span><span><i class="red"></i>反向排名</span>${missing>0?`<em>${missing} 个周期该竞品未进入当前排名表</em>`:""}</div>`;
}
function renderVideos(){
 videoState=normalizeVideoState(videoState);
 if(edition==="global"&&contentAssetView!=="assets")contentAssetView="assets";
 renderContentSubnav();
 renderSocialPluginPanel();
 renderAssetConfig();
 renderUploadMatrix();
 const all=allVideoItems(),catAgg=aggregateVideos(all,"category"),hotLine=all.length?[...all].sort((a,b)=>(b.engagement||0)-(a.engagement||0))[Math.max(0,Math.floor(all.length*.2)-1)]?.engagement||0:0;
 const items=all.filter(x=>[x.title,x.assetModel,x.model,x.platform,x.author,x.category,x.assetRole].join(" ").toLowerCase().includes(videoSearch.toLowerCase()));
 const importedSlots=assetPlatforms.flatMap(p=>assetSlots.map(s=>videoState.files?.[p.key]?.[s.key]).filter(Boolean));
 document.querySelector("#video-source-note").textContent=importedSlots.length?`已创建 ${importedSlots.length} 个自动抓取任务，共沉淀 ${all.length} 条内容。每个槽位按平台和车型独立同步，系统会自动分类并合并成看板。`:"按当前本品和核心竞品自动生成抖音 / 小红书抓取任务。先打开采集页完成平台采集，再同步最新导出沉淀为内容资产。";
 document.querySelector("#video-total").textContent=all.length.toLocaleString();
 document.querySelector("#video-cats").textContent=catAgg.length.toLocaleString();
 document.querySelector("#video-top-cat").textContent=catAgg[0]?.key||"—";
 document.querySelector("#video-hot").textContent=all.filter(x=>(x.engagement||0)>=hotLine&&hotLine>0).length.toLocaleString();
 renderPlatformBoard("douyin","#douyin-category-chart","#douyin-board-note");
 renderPlatformBoard("xiaohongshu","#xhs-category-chart","#xhs-board-note");
 window.MmnXhsContentRanking?.render(all);
 renderContentStrategyPath(all);
 renderContentMmnStrategy();
 renderContentPptPlanner();
 document.querySelector("#video-table").innerHTML=`<thead><tr><th>分类</th><th>平台</th><th>资产车型</th><th>车型</th><th>标题</th><th>点赞</th><th>评论</th><th>收藏</th><th>分享</th><th>互动分</th><th>链接</th></tr></thead><tbody>${items.sort((a,b)=>(b.engagement||0)-(a.engagement||0)).map(x=>`<tr><td><span class="tag">${x.category}</span></td><td>${x.platform||""}</td><td>${x.assetModel||x.model||x.assetRole||""}</td><td>${x.assetModel||x.model||""}</td><td><b>${x.title||""}</b></td><td>${Math.round(x.likes||0).toLocaleString()}</td><td>${Math.round(x.comments||0).toLocaleString()}</td><td>${Math.round(x.collects||0).toLocaleString()}</td><td>${Math.round(x.shares||0).toLocaleString()}</td><td>${Math.round(x.engagement||0).toLocaleString()}</td><td>${x.url?`<a href="${x.url}" target="_blank">打开</a>`:""}</td></tr>`).join("")}</tbody>`;
 renderCreatorLibrary();
}
function renderSocialPluginPanel(){
 const panel=document.querySelector("#social-plugin-panel");
 if(!panel)return;
 const showPlugin=edition==="china"&&["assets","douyinCreators","xhsCreators"].includes(contentAssetView);
 panel.hidden=!showPlugin;
 if(panel.hidden)return;
 const status=document.querySelector("#social-plugin-status"),dy=document.querySelector("#douyin-plugin-note"),xhs=document.querySelector("#xhs-plugin-note");
 if(!socialPluginStatus){status.textContent="等待检测";dy.textContent="等待MMN采集状态";xhs.textContent="等待MMN采集状态";return}
 status.textContent=socialPluginStatus.installed?"MMN采集能力已连接":"MMN采集能力未连接";
 const d=socialPluginStatus.platforms?.douyin||{},x=socialPluginStatus.platforms?.xiaohongshu||{};
 dy.textContent=d.latestFile?`已发现最新采集结果｜共 ${d.count} 份可同步`:"暂未发现可同步的抖音采集结果";
 xhs.textContent=x.latestFile?`已发现最新采集结果｜共 ${x.count} 份可同步`:"暂未发现可同步的小红书采集结果";
}
async function loadSocialPluginStatus(){
 try{const data=await api("/api/social-plugin/status");socialPluginStatus=data.plugin;renderSocialPluginPanel()}
 catch(e){socialPluginStatus={installed:false,platforms:{},note:e.message};renderSocialPluginPanel()}
}
function socialSearchUrl(platform,query){
 const q=encodeURIComponent(query||"");
 return platform==="xiaohongshu"?`https://www.xiaohongshu.com/search_result?keyword=${q}`:`https://www.douyin.com/search/${q}`;
}
async function openSocialPlugin(platform,query=""){
 try{const data=await api("/api/social-plugin/open",{method:"POST",body:JSON.stringify({platform,url:query?socialSearchUrl(platform,query):undefined})});toast(query?`已打开${assetPlatformName(platform)}采集页：${query}`:data.message||"已打开采集页面");return true}
 catch(e){toast(`打开采集页失败：${e.message}`);return false}
}
function mergePluginCreators(platform,creators=[]){
 if(!creators.length)return 0;
 creatorState=normalizeCreatorState(creatorState);
 const list=creatorState.creators?.[platform]||[];
 const map=new Map(list.map(x=>[x.uid||x.id||x.name,x]));
 creators.forEach(x=>{
  const key=x.uid||x.id||x.name;
  if(!key)return;
  const old=map.get(key)||{};
  map.set(key,{...old,...x,id:old.id||x.id||`plugin_${platform}_${key}`,importedAt:new Date().toISOString()});
 });
 creatorState.creators[platform]=[...map.values()];
 return creators.length;
}
async function syncSocialPluginExport(platform){
 try{
  toast(`正在同步${assetPlatformName(platform)}MMN采集结果到独立达人库…`);
  const data=await api("/api/social-plugin/import-latest",{method:"POST",body:JSON.stringify({platform})});
  const creatorCount=mergePluginCreators(platform,data.dataset.creators||[]);
  saveCreatorState();
  await loadSocialPluginStatus();
  renderVideos();
  toast(`已同步到${assetPlatformName(platform)}独立达人库：沉淀 ${creatorCount} 位达人；未写入车型内容库`);
 }catch(e){toast(`同步失败：${e.message}`)}
}
async function startAssetCrawl(platformKey,slot){
 const model=assetModel(slot),role=assetSlots.find(s=>s.key===slot)?.label||"";
 if(!model)return toast("请先设置车型，再启动自动抓取");
 const query=model;
 try{
  toast(`正在自动驱动${assetPlatformName(platformKey)}MMN采集：${query}`);
  const data=await api("/api/social-plugin/auto-crawl",{method:"POST",body:JSON.stringify({platform:platformKey,query,limit:50})});
  videoState.files[platformKey][slot]={...(videoState.files?.[platformKey]?.[slot]||{}),source:"自动抓取任务",count:0,items:videoState.files?.[platformKey]?.[slot]?.items||[],crawlTask:{...data.task,platform:platformKey,slot,role,model,startedAt:new Date().toISOString()},taskStatus:"driving"};
  resetContentPptPlan();
  saveVideoState();
  renderVideos();
  runContentMmnStrategy(true);
  toast(data.task?.message||"MMN采集任务已开始");
 }catch(e){toast(`自动抓取启动失败：${e.message}`)}
}
async function syncAssetCrawl(platformKey,slot){
 const model=assetModel(slot),role=assetSlots.find(s=>s.key===slot)?.label||"";
 if(!model)return toast("请先设置车型，再同步抓取结果");
 try{
  toast(`正在同步${assetPlatformName(platformKey)} · ${model} 的最新抓取结果…`);
  const data=await api("/api/social-plugin/import-latest",{method:"POST",body:JSON.stringify({platform:platformKey})});
  const rawItems=data.dataset.items||[];
  const items=cleanAssetItemsForSlot(rawItems,platformKey,slot,model,role,data.dataset.source||"MMN自动抓取");
  const creatorCount=mergePluginCreators(platformKey,data.dataset.creators||[]);
  if(!items.length&&creatorCount)toast("最新导出只识别到达人画像，未识别到内容明细");
  videoState.files[platformKey][slot]={source:data.dataset.source||"MMN自动抓取",count:items.length,syncedAt:new Date().toISOString(),items,pluginExportPath:data.dataset.exportPath||"",exportedAt:data.dataset.exportedAt||"",crawlTask:{query:model,platform:platformKey,slot,role,model},taskStatus:"synced"};
  resetContentPptPlan();
  saveVideoState();saveCreatorState();await loadSocialPluginStatus();renderVideos();runContentMmnStrategy(true);
  toast(`已同步 ${model} ${assetPlatformName(platformKey)}内容 ${items.length} 条${rawItems.length!==items.length?`，已过滤 ${rawItems.length-items.length} 条非本车型内容`:""}${creatorCount?`，并沉淀达人 ${creatorCount} 位`:""}`);
 }catch(e){toast(`同步抓取结果失败：${e.message}`)}
}
function mountContentDistillViews(){
 const move=(sourceId,targetId)=>{
  const source=document.querySelector(sourceId),target=document.querySelector(targetId);
  if(!source||!target||target.dataset.mounted)return;
  while(source.firstChild)target.appendChild(source.firstChild);
  source.remove();
  target.dataset.mounted="1";
 };
 move("#founder","#content-founder-distill-view");
 move("#bloggerskill","#content-blogger-distill-view");
}
function renderContentSubnav(){
 mountContentDistillViews();
 const subnav=document.querySelector("#content-subnav"),assetView=document.querySelector("#content-asset-view"),creatorView=document.querySelector("#creator-library-view"),founderView=document.querySelector("#content-founder-distill-view"),bloggerView=document.querySelector("#content-blogger-distill-view"),capabilityView=document.querySelector("#content-capability-view");
 if(!subnav||!assetView||!creatorView||!founderView||!bloggerView||!capabilityView)return;
 const isChina=edition==="china";
 subnav.hidden=!isChina;
 if(!isChina)contentAssetView="assets";
 assetView.hidden=contentAssetView!=="assets";
 creatorView.hidden=!["douyinCreators","xhsCreators"].includes(contentAssetView);
 founderView.hidden=contentAssetView!=="founderDistill";
 bloggerView.hidden=contentAssetView!=="bloggerDistill";
 capabilityView.hidden=contentAssetView!=="contentCapability";
 subnav.querySelectorAll("[data-content-view]").forEach(b=>b.classList.toggle("active",b.dataset.contentView===contentAssetView));
}
function creatorPlatformKey(){
 return contentAssetView==="xhsCreators"?"xiaohongshu":"douyin";
}
function creatorTypeName(type){return{review:"评测型",lifestyle:"生活方式",owner:"车主/KOC"}[type]||type}
function creatorInfluenceTier(platform,fans){
 fans=+fans||0;
 if(platform!=="douyin"||!fans)return{role:"待补充",tier:"待补充",label:"粉丝待补充"};
 if(fans<100000)return{role:"KOC",tier:"KOC",label:"KOC"};
 if(fans<200000)return{role:"KOL",tier:"踝部",label:"KOL · 踝部"};
 if(fans<500000)return{role:"KOL",tier:"膝部",label:"KOL · 膝部"};
 if(fans<1000000)return{role:"KOL",tier:"腰部",label:"KOL · 腰部"};
 if(fans<2000000)return{role:"KOL",tier:"肩部",label:"KOL · 肩部"};
 return{role:"KOL",tier:"头部",label:"KOL · 头部"};
}
function creatorDisplayTier(platform,creator){
 if(+creator.fans)return creatorInfluenceTier(platform,creator.fans);
 if(+creator.estimatedFansValue){
  const t=creatorInfluenceTier(platform,creator.estimatedFansValue);
  return{role:t.role,tier:t.tier,label:`MMN补全 · ${t.label}`};
 }
 if(creator.estimatedInfluenceLabel)return{role:creator.estimatedInfluenceRole||"待核验",tier:creator.estimatedInfluenceTier||"待核验",label:creator.estimatedInfluenceLabel};
 if(creator.influenceLabel&&creator.influenceLabel!=="粉丝待补充")return{role:creator.influenceRole||"待核验",tier:creator.influenceTier||"待核验",label:creator.influenceLabel};
 return{role:"待核验",tier:"待核验",label:"MMN待分析"};
}
function splitCreatorField(value){return Array.isArray(value)?value.map(x=>String(x).trim()).filter(Boolean):String(value||"").split(/[,，、/|｜;；\n]+/).map(x=>x.trim()).filter(Boolean)}
function creatorKey(x){return x?.uid||x?.id||x?.name}
function findCreator(platform,id){return (creatorState.creators?.[platform]||[]).find(x=>(x.id===id||creatorKey(x)===id))}
function updateCreator(platform,id,patch){
 const list=creatorState.creators?.[platform]||[];
 const idx=list.findIndex(x=>x.id===id||creatorKey(x)===id);
 if(idx<0)return false;
 const merged={...list[idx],...patch,updatedAt:new Date().toISOString()};
 const tier=creatorDisplayTier(platform,merged);
 list[idx]={...merged,influenceRole:tier.role,influenceTier:tier.tier,influenceLabel:tier.label};
 creatorState.creators[platform]=list;
 saveCreatorState();
 return true;
}
function mergeDistilledCreatorLibraries(libraries={}){
 let changed=false;
 ["douyin","xiaohongshu"].forEach(platform=>{
  const incoming=Array.isArray(libraries[platform])?libraries[platform]:[];
  if(!incoming.length)return;
  const list=creatorState.creators?.[platform]||[];
  incoming.forEach(item=>{
   if(!item?.name)return;
   const idx=list.findIndex(x=>x.id===item.id||x.name===item.name||creatorKey(x)===creatorKey(item));
   if(idx>=0){
    const current=list[idx];
    list[idx]={
     ...item,
     ...current,
     categories:[...new Set([...(current.categories||[]),...(item.categories||[])])],
     strengths:[...new Set([...(current.strengths||[]),...(item.strengths||[])])],
     fitStages:[...new Set([...(current.fitStages||[]),...(item.fitStages||[])])],
     strategyAssets:item.strategyAssets||current.strategyAssets||[],
     scriptAssets:item.scriptAssets||current.scriptAssets||[],
     source:current.source||item.source,
     sampleCount:Math.max(+current.sampleCount||0,+item.sampleCount||0),
     distilledAt:item.updatedAt||current.distilledAt||""
    };
   }else{
    list.push(item);
   }
   changed=true;
  });
  creatorState.creators[platform]=list;
 });
 if(changed)saveCreatorState();
 return changed;
}
function creatorFitScore(creator){
 const a=analysis(),labels=a.labels.slice().sort((x,y)=>y.priority-x.priority).slice(0,6).map(x=>`${x.label} ${x.category}`).join(" ");
 const text=[labels,state.config.model,state.config.brand,state.config.project].join(" ");
 let score=50;
 (creator.categories||[]).forEach(x=>{if(text.includes(x))score+=12});
 (creator.strengths||[]).forEach(x=>{if(/真实|评测|场景|技术|疑虑|家庭|智能|安全|能耗/.test(x)&&text.match(/信任|怀疑|焦虑|智能|安全|能耗|家庭|底盘|价格/))score+=4});
 score+=Math.min(14,(+creator.engagementRate||0));
 score+=creator.type==="owner"&&a.labels.some(x=>x.diagnosis==="优先修复")?8:0;
 score+=creator.type==="review"&&a.labels.some(x=>/智能|底盘|安全|价格/.test(x.category+x.label))?6:0;
 return Math.max(0,Math.min(99,Math.round(score)));
}
function renderCreatorLibrary(){
 const wrap=document.querySelector("#creator-library-view");
 if(!wrap||wrap.hidden)return;
 document.querySelectorAll("[data-creator-filter]").forEach(x=>x.classList.toggle("active",x.dataset.creatorFilter===creatorFilter));
 const platform=creatorPlatformKey(),platformName=assetPlatformName(platform),creators=creatorState.creators?.[platform]||[],query=creatorSearch.trim().toLowerCase();
 const enriched=creators.map(x=>{const tier=creatorDisplayTier(platform,x);return{...x,influenceRole:tier.role,influenceTier:tier.tier,influenceLabel:tier.label,fitScore:creatorFitScore(x)}}).filter(x=>(creatorFilter==="all"||x.type===creatorFilter)&&[x.name,x.city,x.type,x.influenceRole,x.influenceTier,x.influenceLabel,...(x.categories||[]),...(x.strengths||[])].join(" ").toLowerCase().includes(query)).sort((a,b)=>b.fitScore-a.fitScore);
 const top=enriched.filter(x=>x.fitScore>=78);
 const cats=new Set(enriched.flatMap(x=>x.categories||[]));
 document.querySelector("#creator-library-title").textContent=`${platformName}达人库`;
 document.querySelector("#creator-library-desc").textContent=`用于沉淀${platformName}达人能力标签、内容赛道、成本等级与历史表现，后续由MMN策略引擎按Campaign自动推荐。`;
 document.querySelector("#creator-recommend-score").textContent=top.length.toLocaleString();
 document.querySelector("#creator-total").textContent=enriched.length.toLocaleString();
 document.querySelector("#creator-category-count").textContent=cats.size.toLocaleString();
 document.querySelector("#creator-avg-fit").textContent=enriched.length?Math.round(enriched.reduce((s,x)=>s+x.fitScore,0)/enriched.length):"—";
 document.querySelector("#creator-top-count").textContent=top.length.toLocaleString();
 document.querySelector("#creator-card-grid").innerHTML=enriched.length?enriched.map(x=>{const id=x.id||creatorKey(x),city=x.city&&x.city!=="待补充"?x.city:(x.estimatedCity||"城市待核验"),fanText=nullableNumber(x.fans)!==null?formatShortNumber(x.fans):x.estimatedFansText?`MMN补全 ${x.estimatedFansText}`:"未采集",engagementRate=nullableNumber(x.engagementRate);return`<article class="creator-card ${x.fitScore>=78?"recommended":""}"><div class="creator-head"><div><span>${x.influenceLabel} · ${city}</span><b>${x.name}</b></div><strong>${x.fitScore}</strong></div><div class="creator-meta"><span>粉丝 ${fanText}</span><span>${x.influenceLabel}</span><span>均播 ${formatShortNumber(x.avgViews,"待补充")}</span><span>互动率 ${engagementRate===null?"待补充":`${engagementRate}%`}</span><span>成本 ${x.costLevel||"待评估"}</span></div><div class="creator-tags"><em class="tier">${x.influenceLabel}</em>${(x.categories||[]).map(t=>`<em>${t}</em>`).join("")}${x.strategyAssets?.length?`<em>策略资产${x.strategyAssets.length}</em>`:""}${x.scriptAssets?.length?`<em>脚本资产${x.scriptAssets.length}</em>`:""}</div><p>${(x.summary||x.publicProfile||x.strengths?.join(" / ")||"等待补充达人能力判断")}</p><small>推荐场景：${(x.fitStages||[]).join("、")||"待MMN分析或手动补充"}｜风险提示：${x.risk||"需结合具体brief复核"}${x.confidence?`｜MMN置信度：${x.confidence}`:""}</small>${x.profileUrl?`<a class="creator-profile" href="${x.profileUrl}" target="_blank">打开主页</a>`:""}<div class="creator-actions"><button type="button" class="ghost" data-creator-edit="${id}">编辑</button><button type="button" class="primary" data-creator-ai="${id}">MMN分析标签</button></div></article>`}).join(""):`<p class="empty">当前筛选下暂无达人。可以调整类型或搜索条件。</p>`;
 document.querySelectorAll("[data-creator-edit]").forEach(b=>b.onclick=()=>openCreatorEditor(platform,b.dataset.creatorEdit));
 document.querySelectorAll("[data-creator-ai]").forEach(b=>b.onclick=()=>analyzeCreatorWithQwen(platform,b.dataset.creatorAi,b));
 document.querySelector("#creator-planner-flow").innerHTML=["导入达人基础库","识别当前Campaign目标","匹配认知标签与平台赛道","计算达人适配分","生成达人组合与brief","复盘表现并回写学习库"].map((x,i)=>`<div><span>${String(i+1).padStart(2,"0")}</span><b>${x}</b></div>`).join("");
}
function formatShortNumber(n,empty="0"){
 n=+n||0;
 if(!n)return empty;
 if(n>=10000)return`${(n/10000).toFixed(n>=100000?0:1)}万`;
 return n.toLocaleString();
}
function openCreatorEditor(platform,id){
 const creator=findCreator(platform,id);
 if(!creator)return toast("未找到达人画像");
 const dialog=document.querySelector("#creator-dialog"),form=document.querySelector("#creator-form");
 form.elements.platform.value=platform;
 form.elements.id.value=creator.id||creatorKey(creator);
 form.elements.name.value=creator.name||"";
 form.elements.type.value=creator.type||"review";
 form.elements.city.value=creator.city||"";
 form.elements.fans.value=+creator.fans||"";
 form.elements.avgViews.value=+creator.avgViews||"";
 form.elements.engagementRate.value=nullableNumber(creator.engagementRate)??"";
 form.elements.costLevel.value=creator.costLevel||"";
 form.elements.profileUrl.value=creator.profileUrl||"";
 form.elements.categories.value=(creator.categories||[]).join("，");
 form.elements.strengths.value=(creator.strengths||[]).join("，");
 form.elements.fitStages.value=(creator.fitStages||[]).join("，");
 form.elements.risk.value=creator.risk||"";
 document.querySelector("#creator-dialog-title").textContent=`编辑达人画像｜${creator.name||""}`;
 dialog.showModal();
}
async function analyzeCreatorWithQwen(platform,id,button){
 const creator=findCreator(platform,id);
 if(!creator)return toast("未找到达人画像");
 const old=button.textContent;
 button.disabled=true;button.textContent="分析中…";
 try{
  const campaign={edition:activeEdition(),brand:state.config.brand,model:state.config.model,project:state.config.project,competitor:state.config.competitor,priorityLabels:analysis().labels.slice(0,6).map(x=>({label:x.label,category:x.category,diagnosis:x.diagnosis,priority:x.priority}))};
  const data=await api("/api/ai/creator-tags",{method:"POST",body:JSON.stringify({creator,campaign})});
  const t=data.tags||{};
  const patch={
   type:t.type||creator.type,
   categories:splitCreatorField(t.categories||creator.categories),
   strengths:splitCreatorField(t.strengths||creator.strengths),
   fitStages:splitCreatorField(t.fitStages||creator.fitStages),
   risk:t.risk||creator.risk,
   costLevel:t.costLevel||creator.costLevel||"待评估",
   summary:t.summary||creator.summary,
   estimatedCity:t.estimatedCity||creator.estimatedCity||"",
   estimatedInfluenceRole:t.estimatedInfluenceRole||creator.estimatedInfluenceRole||"",
   estimatedInfluenceTier:t.estimatedInfluenceTier||creator.estimatedInfluenceTier||"",
   estimatedInfluenceLabel:t.estimatedInfluenceLabel||creator.estimatedInfluenceLabel||"",
   estimatedFansText:t.estimatedFansText||creator.estimatedFansText||"",
   estimatedFansValue:+t.estimatedFansValue||+creator.estimatedFansValue||0,
   publicProfile:t.publicProfile||creator.publicProfile||"",
   confidence:t.confidence||creator.confidence||"",
   aiTaggedAt:new Date().toISOString()
  };
  updateCreator(platform,id,patch);
  renderCreatorLibrary();
  toast(`MMN已完成 ${creator.name} 的达人标签分析`);
 }catch(e){toast(`MMN分析失败：${e.message}`)}
 finally{button.disabled=false;button.textContent=old}
}
function renderAssetConfig(){
 const el=document.querySelector("#content-asset-config");if(!el)return;
 el.innerHTML=assetSlots.map(s=>`<div class="field"><label>${s.label}车型</label><input data-asset-model="${s.field}" value="${videoState.config?.[s.field]||""}" placeholder="${s.key==="own"?"例如：智己LS8":"可留空"}"></div>`).join("");
 document.querySelectorAll("[data-asset-model]").forEach(input=>input.onchange=input.oninput=()=>{videoState.config[input.dataset.assetModel]=input.value.trim();resetContentPptPlan();saveVideoState();renderUploadMatrix();renderContentStrategyPath(allVideoItems());renderContentMmnStrategy();renderContentPptPlanner()});
}
function renderUploadMatrix(){
 const el=document.querySelector("#content-upload-matrix");if(!el)return;
 el.innerHTML=assetPlatforms.map(p=>`<article class="asset-platform-card capture-card"><div class="asset-platform-head"><div><span>${p.name==="抖音"?"DOUYIN AUTO CAPTURE":"XHS AUTO CAPTURE"}</span><b>${p.name}</b></div><em>${p.name==="抖音"?"短视频车型资产":"种草笔记车型资产"}</em></div><div class="asset-slots">${assetSlots.map(s=>{const model=assetModel(s.key),file=videoState.files?.[p.key]?.[s.key],count=storedAssetItems(p.key,s.key).length,rawCount=+file?.count||file?.items?.length||0,driving=file?.taskStatus==="driving",opened=file?.taskStatus==="opened",synced=file?.taskStatus==="synced"||count>0,query=file?.crawlTask?.query||model||"车型";return`<div class="asset-slot ${synced?"filled":driving||opened?"pending":""}"><div class="asset-slot-main"><small>${s.key==="own"?"本品车型":"核心竞品"}</small><b>${model||"未设置车型"}</b><span>${synced?`已沉淀 ${count} 条车型内容${rawCount&&rawCount!==count?`｜过滤 ${rawCount-count} 条非本车型内容`:""}`:driving?`自动驱动中｜${query}`:opened?`采集任务已打开｜${query}`:"等待自动抓取"}</span></div><div class="asset-slot-actions"><button type="button" class="${model?"primary":"ghost"}" data-asset-crawl="${p.key}:${s.key}" ${model?"":"disabled"}>${driving?"重新抓取":"开始抓取"}</button><button type="button" class="ghost" data-asset-sync="${p.key}:${s.key}" ${model?"":"disabled"}>同步结果</button></div></div>`}).join("")}</div></article>`).join("");
 document.querySelectorAll("[data-asset-crawl]").forEach(b=>b.onclick=()=>{const [platform,slot]=b.dataset.assetCrawl.split(":");startAssetCrawl(platform,slot)});
 document.querySelectorAll("[data-asset-sync]").forEach(b=>b.onclick=()=>{const [platform,slot]=b.dataset.assetSync.split(":");syncAssetCrawl(platform,slot)});
}
function renderPlatformBoard(platformKey,chartSel,noteSel){
 const name=assetPlatformName(platformKey),items=allVideoItems().filter(x=>x.assetPlatform===platformKey||x.platform===name);
 const el=document.querySelector(chartSel),note=document.querySelector(noteSel);
 if(!el)return;
 const rows=assetSlots.map(s=>{const model=assetModel(s.key),its=items.filter(x=>x.assetSlot===s.key||x.assetModel===model||x.model===model),agg=aggregateVideos(its,"category").slice(0,5);return{s,model,items:its,agg}});
 const topModel=rows.filter(r=>r.items.length).sort((a,b)=>b.items.length-a.items.length)[0];
 if(note)note.textContent=topModel?`${topModel.model}｜${topModel.items.length.toLocaleString()} 条｜Top：${topModel.agg[0]?.key||"综合评测"}`:"暂无车型内容";
 el.innerHTML=rows.map(r=>`<div class="model-tag-board ${r.items.length?"":"empty"}"><div class="model-tag-head"><span>${r.s.key==="own"?"本品":"竞品"}</span><b>${r.model||"未设置车型"}</b><em>${r.items.length.toLocaleString()} 条</em></div>${r.agg.length?`<div class="model-tag-bars">${r.agg.map(x=>{const count=+x.count||0,max=+r.agg[0]?.count||1;return`<div><label>${x.key}</label><i><span style="width:${Math.max(4,count/max*100)}%"></span></i><strong>${count.toLocaleString()}</strong></div>`}).join("")}</div>`:`<p>暂无该车型${name}内容</p>`}</div>`).join("");
}
function renderModelBoard(items){
 const target=document.querySelector("#content-model-board");
 if(!target)return;
 const rows=assetSlots.map(s=>{const model=assetModel(s.key),its=items.filter(x=>x.assetSlot===s.key),dy=its.filter(x=>x.assetPlatform==="douyin").length,xhs=its.filter(x=>x.assetPlatform==="xiaohongshu").length,top=aggregateVideos(its,"category")[0]?.key||"—",eng=its.reduce((n,x)=>n+(+x.engagement||0),0);return{s,model,all:its.length,dy,xhs,top,eng}});
 target.innerHTML=`<div class="table-wrap mini"><table><thead><tr><th>角色</th><th>车型</th><th>总内容</th><th>抖音</th><th>小红书</th><th>主分类</th><th>互动分</th></tr></thead><tbody>${rows.map(r=>`<tr><td><span class="tag ${r.s.key==="own"?"asset":""}">${r.s.label}</span></td><td><b>${r.model||"未设置"}</b></td><td>${r.all.toLocaleString()}</td><td>${r.dy.toLocaleString()}</td><td>${r.xhs.toLocaleString()}</td><td>${r.top}</td><td>${Math.round(r.eng).toLocaleString()}</td></tr>`).join("")}</tbody></table></div>`;
}
function renderContentStrategyPath(items){
 const el=document.querySelector("#content-strategy-path"),status=document.querySelector("#content-strategy-path-status");
 if(!el)return;
 const hasOwn=items.some(x=>x.assetSlot==="own"),hasCompetitor=items.some(x=>x.assetSlot&&x.assetSlot!=="own"),hasBoth=hasOwn&&hasCompetitor;
 const steps=[
  {name:"车型内容抓取",desc:"按本品和竞品分别沉淀抖音 / 小红书内容资产",ok:items.length>0},
  {name:"MMN语义归类",desc:"识别产品属性、购买阻塞点、竞品关系、身份表达和场景需求",ok:items.length>0},
  {name:"交叉质检",desc:"结合决策驾驶舱、声量数据中心、垂媒竞争格局做策略复核",ok:hasBoth},
  {name:"策略输出",desc:"生成MMN模型外显策略，并可进入策略PPT方案",ok:!!contentStrategyState.result||hasBoth}
 ];
 if(status)status.textContent=hasBoth?"可进入MMN策略输出":items.length?"等待竞品/本品补齐":"等待自动抓取";
 el.innerHTML=`<div class="strategy-path-steps">${steps.map((s,i)=>`<div class="${s.ok?"done":""}"><span>${String(i+1).padStart(2,"0")}</span><b>${s.name}</b><small>${s.desc}</small></div>`).join("")}</div><div class="strategy-path-action"><p>${hasBoth?"本品和竞品内容已经进入同一条策略链路，下一步应刷新MMN策略，形成可汇报结论。":"先完成本品和至少一个核心竞品的抓取同步，再由MMN输出交叉质检后的营销策略。"}</p><button type="button" class="primary" id="strategy-path-run" ${items.length?"":"disabled"}>生成/刷新MMN策略</button></div>`;
 const btn=document.querySelector("#strategy-path-run");
 if(btn)btn.onclick=()=>runContentMmnStrategy();
}
function upstreamStrategySignals(model,competitors=[]){
 const a=analysis(),ownRows=state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]===state.config.model),compRows=state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]!==state.config.model&&(competitors.includes(x.r[0])||x.r[1]==="竞品"));
 const scopedRows=ownRows.length?[...ownRows,...compRows]:state.rows.map((r,i)=>({r,i}));
 const verticalItems=(verticalState.items||[]).filter(x=>x.ownModel===model||x.competitor===model||competitors.includes(x.competitor)||competitors.includes(x.ownModel));
 const periods=uniquePeriods(verticalItems),latestPeriod=periods[periods.length-1]||"",latestVertical=latestPeriod?verticalItems.filter(x=>x.period===latestPeriod):verticalItems.slice(-12);
 return{
  cockpit:{
   model:state.config.model,
   project:state.config.project,
   nsr:+(a.nsr||0).toFixed(3),
   intent:+(a.intent||0).toFixed(3),
   ips:+(a.ips||0).toFixed(3),
   positiveScore:Math.round(a.pos||0),
   negativeScore:Math.round(a.neg||0),
   ownSamples:a.ownComments||0,
   priorityLabels:a.labels.slice(0,8).map(x=>({label:x.label,category:x.category,diagnosis:x.diagnosis,priority:+x.priority.toFixed(2),gap:+(x.gap||0).toFixed(3),ownNegative:Math.round(x.on||0)}))
  },
  voiceCenter:{
   platforms:topBreakdown(scopedRows,2,8),
   categories:topBreakdown(scopedRows,3,8),
   labels:topBreakdown(scopedRows,4,10),
   emotions:topBreakdown(scopedRows,5,8)
  },
  verticalCompetition:{
   latestPeriod,
   relations:latestVertical.slice(0,16).map(x=>({platform:x.platform,period:x.period,ownModel:x.ownModel,competitor:x.competitor,positiveRank:x.positiveRank,negativeRank:x.negativeRank,share:x.share,status:rankStatus(x)}))
  }
 };
}
function contentAssetStrategyContext(){
 const items=allVideoItems(),catAgg=aggregateVideos(items,"category"),platformAgg=aggregateVideos(items.map(x=>({...x,category:x.platform||assetPlatformName(x.assetPlatform)||"未知平台"})),"category");
 const modelRows=assetSlots.map(s=>{const model=assetModel(s.key),its=items.filter(x=>x.assetSlot===s.key||x.assetModel===model||x.model===model),cats=aggregateVideos(its,"category"),blockers={};its.forEach(x=>(x.mmnLabels?.blockers||[]).forEach(b=>blockers[b]=(blockers[b]||0)+1));return{role:s.label,model,count:its.length,topCategory:cats[0]?.key||"暂无",topBlockers:Object.entries(blockers).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([key,count])=>({key,count}))}});
 const tasks=assetPlatforms.flatMap(p=>assetSlots.map(s=>{const f=videoState.files?.[p.key]?.[s.key];return f?{platform:p.name,role:s.label,model:assetModel(s.key),status:f.taskStatus||"synced",query:f.crawlTask?.query||"",count:+f.count||f.items?.length||0,source:f.source||"",exportedAt:f.exportedAt||f.syncedAt||f.crawlTask?.startedAt||""}:null}).filter(Boolean));
 const topContents=[...items].sort((a,b)=>(b.engagement||0)-(a.engagement||0)).slice(0,18).map(x=>({platform:x.platform,role:x.assetRole,model:x.assetModel||x.model,title:x.title,author:x.author,category:x.category,blockers:x.mmnLabels?.blockers||[],actions:x.mmnLabels?.actions||[],engagement:Math.round(x.engagement||0),url:x.url||""}));
 const competitors=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
 const model=state.config.model,upstream=upstreamStrategySignals(model,competitors);
 return{
  drillType:"content_asset_strategy",
  drillKey:model,
  question:"请调用并综合决策驾驶舱、声量数据中心、垂媒竞争格局三大板块，再结合自动抓取内容资产归类，为当前车型输出一个专业营销结论。外显结果只呈现MMN策略，不输出数据缺口。",
  project:{edition:activeEdition(),brand:state.config.brand,model,competitors,project:state.config.project,stage:state.config.stage||"上市/增长期"},
  summary:{samples:Math.max(items.length,upstream.cockpit.ownSamples||0),contentSamples:items.length,crawlTasks:tasks.length,categories:catAgg.length,topCategory:catAgg[0]?.key||upstream.voiceCenter.labels?.[0]?.key||"核心标签",topPlatform:platformAgg[0]?.key||upstream.voiceCenter.platforms?.[0]?.key||"核心平台",hotItems:items.filter(x=>(x.engagement||0)>0).length,positiveScore:upstream.cockpit.positiveScore,negativeScore:upstream.cockpit.negativeScore},
  upstream,
  breakdown:{categories:catAgg.slice(0,12),platforms:platformAgg.slice(0,8),models:modelRows},
  crawlTasks:tasks,
  topContents,
  references:ragSearch({query:[model,...competitors,"决策驾驶舱","声量数据中心","垂媒竞争格局","抖音","小红书","营销策略"].join(" "),limit:6}),
  outputPolicy:{hideDataGaps:true,visibleBrand:"MMN模型输出策略",requiredSections:["Executive Conclusion","Key Findings","Evidence","Strategic Implication","Action Recommendation"]}
 };
}
function localContentStrategyDraft(ctx){
 const top=ctx.upstream?.cockpit?.priorityLabels?.[0]?.label||ctx.breakdown?.categories?.[0]?.key||"核心卖点",second=ctx.upstream?.voiceCenter?.platforms?.[0]?.key||ctx.breakdown?.platforms?.[0]?.key||"核心平台",model=ctx.project?.model||"本品车型",competitors=(ctx.project?.competitors||[]).join(" / ")||"核心竞品";
 const mainModel=(ctx.breakdown?.models||[]).find(x=>x.role==="本品")||{};
 const blocker=mainModel.topBlockers?.[0]?.key||ctx.upstream?.cockpit?.priorityLabels?.find(x=>x.diagnosis==="优先修复")?.label||top;
 const relation=ctx.upstream?.verticalCompetition?.relations?.[0],verticalCopy=relation?`${relation.platform}${relation.period?` ${relation.period}`:""}显示，${model}与${relation.competitor}已形成${relation.status}关系，正向排名${relation.positiveRank||"未上榜"}、反向排名${relation.negativeRank||"未上榜"}。`:`垂媒竞争格局用于校准竞品表达，策略上必须把对比从参数表转成真实场景。`;
 return consultingOutputText({
  conclusion:`${model}不应继续堆内容数量，应把“${top}”、${second}主阵地和竞品关系合并成一个清晰购买理由，优先用证据修复“${blocker}”。`,
  findings:[`- “${top}”是当前第一传播任务。[Evidence: E1]`,`- ${second}是当前主平台，资源不应平均分配。[Evidence: E2]`,`- 与 ${competitors} 的表达应从参数表转为真实场景比较。[Evidence: E3]`],
  evidence:[`- E1：决策驾驶舱 NSR ${(ctx.upstream?.cockpit?.nsr||0).toFixed(2)}，优先标签为“${top}”。`,`- E2：声量数据中心当前主平台为 ${second}。`,`- E3：${verticalCopy}`],
  implication:"把三类上游判断合并后，内容预算才能从增加发布量转向建立购买确定性，并减少无差别投放造成的资源损耗。",
  actions:[`- P0｜7天｜内容团队：围绕“${top}”建立实测、车主证词、场景短视频和品牌FAQ。`,`- P1｜14天｜平台团队：在 ${second} 围绕 ${competitors} 做同场景对比。`,`- P2｜30天｜项目负责人：按正向声量、负向疑虑、垂媒排名和试驾/询价线索复盘。`]
 });
}
function mmnTraceLabel(result){
 const p=result?.parts||{};
 if(p.qwen&&p.deepseek)return"MMN交叉验证完成";
 if(p.qwen||p.deepseek)return"MMN单模型 + 规则复核";
 return"MMN规则兜底";
}
function renderContentMmnStrategy(){
 const box=document.querySelector("#content-mmn-strategy"),status=document.querySelector("#content-mmn-strategy-status");
 if(!box)return;
 const ctx=contentAssetStrategyContext(),result=contentStrategyState.result||{text:localContentStrategyDraft(ctx),parts:{rules:localContentStrategyDraft(ctx)},context:ctx};
 if(status)status.textContent=contentStrategyState.loading?"MMN正在交叉验证":mmnTraceLabel(result);
 const parts=result.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(result.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"}[k]||publicMmnProviderLabel(k)}</b>${markdownish(String(v))}</section>`).join("")}${result.errors&&Object.keys(result.errors).length?`<section><b>缺席/错误</b>${Object.entries(result.errors).map(([k,v])=>`<p>${publicMmnProviderLabel(k)}: ${publicMmnText(v)}</p>`).join("")}</section>`:""}</details>`:"";
 box.innerHTML=`<div class="content-mmn-head"><div><b>${contentStrategyState.loading?"MMN正在生成营销策略":"MMN模型输出策略"}</b><span>决策驾驶舱 + 声量数据中心 + 垂媒竞争格局｜内容资产 ${ctx.summary.contentSamples.toLocaleString()} 条｜主类：${ctx.summary.topCategory}</span></div><button type="button" class="primary" id="run-content-mmn-strategy" ${contentStrategyState.loading?"disabled":""}>${contentStrategyState.loading?"生成中…":"生成/刷新MMN策略"}</button></div><div class="content-mmn-output">${consultingMarkdown(String(result.text||""))}</div>${contentStrategyState.error?`<p class="empty">模型生成失败，已使用MMN本地策略输出：${contentStrategyState.error}</p>`:""}${parts}`;
 const btn=document.querySelector("#run-content-mmn-strategy");
 if(btn)btn.onclick=()=>runContentMmnStrategy();
}
async function runContentMmnStrategy(silent=false){
 const ctx=contentAssetStrategyContext();
 const requestedModel=ctx.project.model;
 contentStrategyState={loading:true,result:{text:localContentStrategyDraft(ctx),parts:{rules:localContentStrategyDraft(ctx)},context:ctx},error:""};
 renderContentMmnStrategy();
 try{
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
  const res=await fetch("/api/ai/fusion-strategy",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({context:ctx}),signal:controller.signal});
  clearTimeout(timer);
  const data=await res.json().catch(()=>({ok:false,error:"模型接口返回格式异常"}));
  if(!res.ok||!data.ok)throw new Error(data.error||"MMN策略生成失败");
  if(state.config.model!==requestedModel)return;
  contentStrategyState={loading:false,result:{...data,context:ctx},error:""};
  if(!silent)toast("MMN已完成内容资产营销策略交叉验证");
 }catch(err){
  if(state.config.model!==requestedModel)return;
  contentStrategyState={loading:false,result:{text:localContentStrategyDraft(ctx),parts:{rules:localContentStrategyDraft(ctx)},context:ctx},error:err.name==="AbortError"?"模型生成超过90秒":err.message};
  if(!silent)toast("MMN策略暂用本地规则兜底");
 }
 renderContentMmnStrategy();
 renderContentPptPlanner();
}
function strategyPptContext(){
 const base=contentAssetStrategyContext(),model=base.project?.model||state.config.model,competitors=base.project?.competitors||[];
 const creatorAssets=["douyin","xiaohongshu"].flatMap(platform=>(creatorState.creators?.[platform]||[]).slice(0,8).map(x=>({platform:assetPlatformName(platform),name:x.name,type:x.type,categories:x.categories||[],strengths:x.strengths||[],fitStages:x.fitStages||[],strategyAssets:x.strategyAssets||[],scriptAssets:x.scriptAssets||[],summary:x.summary||x.publicProfile||""})));
 const distilledBloggerAssets=(bloggerSkillState.profiles||[]).slice(0,8).map(x=>({name:x.name,platform:x.platform||"",categories:x.categories||[],strengths:x.strengths||[],strategyAssets:x.strategyAssets||[],scriptAssets:x.scriptAssets||[],summary:x.summary||""}));
 const manual=learnings().filter(x=>x.model===model||competitors.includes(x.model)).slice(-10);
 return{
  ...base,
  drillType:"strategy_ppt_brief",
  question:"请综合决策驾驶舱、垂媒竞争格局、声量数据中心、抖音/小红书自动抓取内容资产、达人蒸馏和RAG知识，为选中车型输出可直接生成专业PPT的策略方案。外显只呈现MMN多模态策略输出。",
  presentation:{
   title:`${model} 内容资产与营销策略方案`,
   audience:"汽车品牌市场负责人 / 管理层 / MCN内容合作负责人",
   format:"10页中文策略PPT，咨询腔但通俗易懂",
   sections:["Executive Conclusion","Key Findings","Evidence","Strategic Implication","Action Recommendation"]
  },
  knowledge:{
   manual,
   strategyKb:strategyKb.slice(-12),
   creatorAssets,
   distilledBloggerAssets,
   modelJudgments:modelJudgmentsFor(model).slice(-10)
  },
  outputPolicy:{hideProviders:true,hideDataGaps:true,visibleBrand:"MMN多模态策略输出",gammaReady:true,pptReady:true}
 };
}
function localStrategyPptBrief(ctx){
 const model=ctx.project?.model||"当前车型",competitors=(ctx.project?.competitors||[]).filter(Boolean),competitorText=competitors.join(" / ")||"核心竞品";
 const cockpit=ctx.upstream?.cockpit||{},voice=ctx.upstream?.voiceCenter||{},vertical=ctx.upstream?.verticalCompetition||{};
 const topLabel=(cockpit.priorityLabels?.[0]?.label||ctx.summary?.topCategory||"核心认知"),risk=(cockpit.priorityLabels||[]).find(x=>x.diagnosis==="优先修复")?.label||topLabel;
 const platform=voice.platforms?.[0]?.key||ctx.summary?.topPlatform||"核心平台",relation=vertical.relations?.[0]||{};
 const dy=ctx.breakdown?.platforms?.find(x=>/抖音/.test(x.key))?.count||0,xhs=ctx.breakdown?.platforms?.find(x=>/小红书/.test(x.key))?.count||0;
 const creators=[...(ctx.knowledge?.creatorAssets||[]),...(ctx.knowledge?.distilledBloggerAssets||[])].slice(0,3).map(x=>x.name).filter(Boolean).join(" / ")||"评测型达人、生活方式达人、真实车主";
 const relationLine=relation.competitor?`${relation.platform||"垂媒"} ${relation.period||"当前周期"}中，${model}与${relation.competitor}形成“${relation.status||"竞争对比"}”关系。`:`当前垂媒资料仅能确认 ${model} 处于与 ${competitorText} 的比较语境，具体排名待补。`;
 return consultingOutputText({
  conclusion:`${model}应采用“证据先行、场景解释、竞品校准”的内容策略：先修复“${risk}”，再放大“${topLabel}”。`,
  findings:[`- 当前阻力不是曝光不足，而是缺少稳定购买理由。[Evidence: E1]`,`- “${topLabel}”应作为认知资产放大，“${risk}”应优先修复。[Evidence: E1]`,`- 资源应优先配置在 ${platform} 并围绕 ${competitorText} 的真实比较关系表达。[Evidence: E2] [Evidence: E3]`],
  evidence:[`- E1：决策驾驶舱正向分 ${cockpit.positiveScore||0}、负向风险 ${cockpit.negativeScore||0}，优先标签为“${topLabel}”。`,`- E2：声量数据中心主平台为 ${platform}；抖音资产 ${dy} 条、小红书资产 ${xhs} 条。`,`- E3：${relationLine}`],
  implication:"若继续以发布量为中心，预算会放大尚未解决的购买疑虑；把证据沉淀为可复用购买理由，才能提升内容效率与试驾/询价承接。",
  actions:[`- P0｜7天｜内容团队：围绕“${risk}”完成疑虑实测和品牌FAQ。`,`- P1｜14天｜平台与达人团队：在 ${platform} 上线同场景竞品对比；优先调用 ${creators}。`,`- P2｜30天｜项目负责人：沉淀五段式脚本资产；按正向声量、负向疑虑、收藏/评论质量和试驾/询价线索复盘。`]
 });
}
function resetContentPptPlan(){
 contentPptState={loading:false,result:null,error:""};
}
function strategyPptResult(){
 const ctx=strategyPptContext();
 return contentPptState.result||{text:localStrategyPptBrief(ctx),parts:{rules:localStrategyPptBrief(ctx)},context:ctx};
}
function strategyPptBriefText(){
 const result=strategyPptResult(),ctx=result.context||strategyPptContext();
 return publicMmnText([`# ${ctx.presentation?.title||"MMN策略PPT方案"}`,"","请基于以下MMN策略方案生成一份中文汽车营销策略PPT。风格：专业、克制、有咨询感，但表达要让非数据团队也能听懂。","建议比例：16:9；建议页数：10页；每页保留一个核心判断、一个依据、一个动作。","",result.text||localStrategyPptBrief(ctx)].join("\n"));
}
function strategyPptPayload(){
 const result=strategyPptResult(),ctx=result.context||strategyPptContext(),a=analysis(),text=publicMmnText(result.text||"");
 const sections=text.split(/\n###\s+/).map(x=>x.trim()).filter(Boolean);
 const manual=(ctx.knowledge?.manual||[]).map(x=>({label:x.label||"人工判断",conclusion:x.conclusion||x.body||"",recommendation:x.recommendation||"",evidence:x.evidence||"",platform:x.platform||"",kpi:x.kpi||""}));
 return{deckType:"mmn_strategy_consulting",title:ctx.presentation?.title||`${ctx.project?.model||state.config.model} MMN策略方案`,model:ctx.project?.model||state.config.model,brand:state.config.brand,competitor:(ctx.project?.competitors||[]).join(" / ")||state.config.competitor,competitors:ctx.project?.competitors||[],account:"MMN多模态策略输出",strategyText:text,sections,context:ctx,visualReview:{status:"pending_verified_image",rule:"封面车型图必须由MMN视觉识别与策略主控双重复核；未取得已复核车型图时不展示伪车型图。",model:ctx.project?.model||state.config.model,checks:["车型外观与车型名一致","图片来源可信","无竞品误配","无渲染/概念图误导"]},metrics:{...metricDisplay(a),positive:isSummaryImport()?"不适用":Math.round(a.pos||0).toLocaleString(),negative:isSummaryImport()?"不适用":Math.round(a.neg||0).toLocaleString()},diagnostics:(a.labels||[]).slice(0,8).map(x=>({label:x.label,category:x.category,diagnosis:x.diagnosis,negative:isSummaryImport()?"未提供量级":Math.round(x.on).toLocaleString(),gap:(x.gap*100).toFixed(1)+"%",priority:x.priority.toFixed(1),impact:x.impact?.toFixed?x.impact.toFixed(1):x.impact,white:x.white?.toFixed?x.white.toFixed(1):x.white})),manual:manual.length?manual:sections.slice(1,6).map((x,i)=>({label:`策略页 ${i+1}`,conclusion:x.slice(0,160),recommendation:x.slice(160,330)})),knowhow:sections.slice(0,6).map((x,i)=>({label:`P${i+1}`,message:x.slice(0,180),evidence:"MMN融合决策驾驶舱、声量数据中心、垂媒竞争格局与内容资产",kpi:"按核心标签、疑虑占比、竞品对比搜索、试驾/询价线索复盘"})),calendar:[{week:"第1周",theme:"内容资产校准",task:"完成抖音/小红书抓取、分类、达人脚本方向筛选"},{week:"第2周",theme:"证据内容上线",task:"围绕核心疑虑发布实测、车主证词和竞品同场景对比"},{week:"第3-4周",theme:"策略复盘",task:"按标签声量、评论质量、询价/试驾线索调整投放与达人组合"}]};
}
function renderContentPptPlanner(){
 const box=document.querySelector("#content-ppt-planner"),status=document.querySelector("#content-ppt-status");
 if(!box)return;
 const result=strategyPptResult(),ctx=result.context||strategyPptContext(),summary=ctx.summary||{},creators=[...(ctx.knowledge?.creatorAssets||[]),...(ctx.knowledge?.distilledBloggerAssets||[])];
 if(status)status.textContent=contentPptState.loading?"MMN正在交叉验证":mmnTraceLabel(result);
 const parts=result.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(result.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"}[k]||k}</b>${consultingMarkdown(String(v))}</section>`).join("")}</details>`:"";
 box.innerHTML=`<div class="content-mmn-head"><div><b>${contentPptState.loading?"MMN正在生成策略PPT方案":"MMN策略PPT方案"}</b><span>决策驾驶舱 + 垂媒竞争格局 + 声量数据中心 + 抖音/小红书内容资产 + 达人蒸馏｜外显为MMN多模态策略输出</span></div><div class="content-ppt-actions"><button type="button" class="primary ppt-main-action" id="download-content-pptx">一键生成PPT</button><button type="button" class="ghost" id="run-content-ppt-plan" ${contentPptState.loading?"disabled":""}>${contentPptState.loading?"生成中…":"刷新策略方案"}</button><button type="button" class="ghost" id="copy-content-ppt-brief">复制Gamma Brief</button><button type="button" class="ghost" id="download-content-ppt-brief">下载PPT素材</button></div></div><div class="content-ppt-meta"><div><span>策略对象</span><b>${ctx.project?.model||state.config.model}</b></div><div><span>核心竞品</span><b>${(ctx.project?.competitors||[]).join(" / ")||state.config.competitor||"待选择"}</b></div><div><span>内容资产</span><b>${summary.contentSamples?`${summary.topCategory}`:"自动抓取中"}</b></div><div><span>达人资产</span><b>${creators.length?`${creators.length}类可调用资产`:"待蒸馏沉淀"}</b></div></div><div class="content-mmn-output">${consultingMarkdown(String(result.text||""))}</div>${contentPptState.error?`<p class="empty">方案生成失败，已使用MMN本地策略输出：${contentPptState.error}</p>`:""}${parts}`;
 document.querySelector("#run-content-ppt-plan").onclick=()=>runContentPptPlan();
 document.querySelector("#copy-content-ppt-brief").onclick=copyContentPptBrief;
 document.querySelector("#download-content-ppt-brief").onclick=downloadContentPptBrief;
 document.querySelector("#download-content-pptx").onclick=downloadContentPptx;
}
async function runContentPptPlan(){
 const ctx=strategyPptContext();
 const requestedModel=ctx.project.model;
 contentPptState={loading:true,result:{text:localStrategyPptBrief(ctx),parts:{rules:localStrategyPptBrief(ctx)},context:ctx},error:""};
 renderContentPptPlanner();
 try{
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),90000);
  const res=await fetch("/api/ai/fusion-strategy",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({context:ctx}),signal:controller.signal});
  clearTimeout(timer);
  const data=await res.json().catch(()=>({ok:false,error:"模型接口返回格式异常"}));
  if(!res.ok||!data.ok)throw new Error(data.error||"MMN策略PPT方案生成失败");
  if(state.config.model!==requestedModel)return;
  contentPptState={loading:false,result:{...data,context:ctx,text:publicMmnText(data.text)},error:""};
  toast("MMN已完成策略PPT方案交叉验证");
 }catch(err){
  if(state.config.model!==requestedModel)return;
  contentPptState={loading:false,result:{text:localStrategyPptBrief(ctx),parts:{rules:localStrategyPptBrief(ctx)},context:ctx},error:err.name==="AbortError"?"模型生成超过90秒":err.message};
  toast("MMN策略PPT方案暂用本地规则兜底");
 }
 renderContentPptPlanner();
}
async function copyContentPptBrief(){
 const text=strategyPptBriefText();
 try{await navigator.clipboard.writeText(text);toast("Gamma Brief 已复制")}
 catch{downloadContentPptBrief();toast("浏览器不允许直接复制，已下载PPT素材")}
}
function downloadContentPptBrief(){
 const ctx=strategyPptContext();
 download(`${ctx.presentation?.title||"MMN策略PPT方案"}_GammaBrief.md`,strategyPptBriefText(),"text/markdown");
}
async function downloadContentPptx(){
 try{
  toast("正在生成策略PPTX…");
  const res=await fetch("/api/export-pptx",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify(strategyPptPayload())});
  if(!res.ok){const err=await res.json().catch(()=>({error:"PPTX生成失败"}));throw new Error(err.error)}
  const blob=await res.blob(),a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=`${strategyPptPayload().title}.pptx`;a.click();URL.revokeObjectURL(a.href);
  toast("策略PPTX已导出");
 }catch(err){toast(`PPTX导出失败：${err.message}`)}
}
async function handleAssetUpload(e){
 const file=e.target.files[0],platformKey=e.target.dataset.platform,slot=e.target.dataset.slot,model=assetModel(slot),role=assetSlots.find(s=>s.key===slot)?.label||"";
 if(!file||!platformKey||!slot||!model)return;
 toast(`正在导入${assetPlatformName(platformKey)} · ${role}内容…`);
 try{
  const res=await fetch(`/api/import-video-xlsx?filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});
  const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");
  const items=cleanAssetItemsForSlot(json.dataset.items,platformKey,slot,model,role,file.name);
  videoState.files[platformKey][slot]={source:file.name,count:items.length,uploadedAt:new Date().toISOString(),items};
  resetContentPptPlan();
  saveVideoState();renderVideos();runContentMmnStrategy(true);toast(`已导入 ${model} ${assetPlatformName(platformKey)} ${items.length} 条`);
 }catch(err){toast(`内容资产导入失败：${err.message}`)}
 finally{e.target.value=""}
}
function aggregateVideos(items,key){
 const m={};items.forEach(x=>{const k=x[key]||"未识别";if(!m[k])m[k]={key:k,count:0,engagement:0};m[k].count++;m[k].engagement+=+x.engagement||0});return Object.values(m).sort((a,b)=>b.count-a.count);
}
function classifyKnowledge(text){
 const t=String(text||"");
 if(/抖音|小红书|标题|达人|种草|短视频|内容|爆款|互动|收藏|转发/.test(t))return"内容打法";
 if(/懂车帝|汽车之家|垂媒|PK|对比|正向|反向|排名|竞品关系/.test(t))return"垂媒判断";
 if(/报告|汇报|PPT|客户|结论|建议|表达|管理层/.test(t))return"报告表达";
 if(/车型|本品|竞品|用户|价格|智驾|空间|安全|质量|口碑|认知/.test(t))return"车型洞察";
 return"方法论";
}
function knowledgeTargets(type){
 return{方法论:["决策驾驶舱","打法知识库","报告"],车型洞察:["决策驾驶舱","认知赛道诊断","打法知识库"],内容打法:["内容资产中心","打法知识库","报告"],垂媒判断:["垂媒竞争格局","报告"],报告表达:["报告","打法知识库"]}[type]||["打法知识库"];
}
function extractKeywords(text){
 const dict=["上汽集团","上汽奥迪","上汽大众","智己","小米","理想","蔚来","极氪","特斯拉","问界","荣威","MG","别克","凯迪拉克","五菱","大通","奥迪","大众","价格","智驾","空间","安全","质量","口碑","底盘","舒适","内容","抖音","小红书","懂车帝","汽车之家","垂媒","报告","PPT","上市","竞品","用户","家庭","科技"];
 return dict.filter(k=>String(text||"").includes(k)).slice(0,8);
}
function knowledgeHaystack(item){
 const meta=item.metadata||{};
 return [item.title,item.body,item.type,meta.domain,meta.module,meta.topic,meta.entity,...(item.keywords||[]),...(item.tags||[])].join(" ");
}
function knowledgeClusterKey(item){
 const text=knowledgeHaystack(item);
 const brands=["上汽集团","上汽奥迪","上汽大众","智己","别克","凯迪拉克","五菱","上汽大通","大通","荣威","MG","奥迪","大众","小米","理想","蔚来","极氪","特斯拉","问界","岚图","固特异"];
 const brand=brands.find(b=>text.includes(b));
 if(brand)return brand==="大通"?"上汽大通":brand;
 if(/KOC|KOL|KOS|达人|脚本|内容|短视频|抖音|小红书/.test(text))return"内容与达人";
 if(/RAG|NSR|Gap|数据|指标|Cockpit|引擎/.test(text))return"数据与RAG";
 if(/底盘|电池|增程|轮胎|NVH|安全|音响|车身|技术/.test(text))return"汽车技术";
 if(/MMN|BAS|营销方法论|品牌DNA|车型DNA|GTM|IPMS/.test(text))return"MMN方法论";
 if(/合规|风险|测评规范|法务/.test(text))return"合规与风险";
 return item.type||"其他知识";
}
function knowledgeClusterType(key){
 return /上汽|智己|别克|凯迪拉克|五菱|荣威|MG|奥迪|大众|小米|理想|蔚来|极氪|特斯拉|问界|岚图|固特异/.test(key)?"品牌/车型":"能力模块";
}
function knowledgeClusters(){
 const m={};
 strategyKb.forEach(item=>{
  const key=knowledgeClusterKey(item);
  if(!m[key])m[key]={key,type:knowledgeClusterType(key),items:[],domains:{}};
  m[key].items.push(item);
  const domain=item.metadata?.domain||item.type||"未分类";
  m[key].domains[domain]=(m[key].domains[domain]||0)+1;
 });
 return Object.values(m).sort((a,b)=>b.items.length-a.items.length);
}
function ragTagsFromRows(rows=[]){
 const tags=new Set([state.config.model,state.config.brand]);
 rows.forEach(({r})=>[r[0],r[2],r[3],r[4],r[5],trafficType(r)].forEach(x=>x&&tags.add(x)));
 return [...tags].filter(Boolean);
}
function ragScore(item,terms,filters={}){
 const meta=item.metadata||{};
 const hay=[item.title,item.body,item.type,meta.domain,meta.module,meta.topic,meta.entity,meta.knowledge_type,...(meta.retrieval_queries||[]),...(item.keywords||[]),...(item.targets||[]),...(item.tags||[])].join(" ");
 let score=0,reasons=[];
 terms.filter(Boolean).forEach(t=>{if(hay.includes(t)){score+=3;reasons.push(t)}});
 ["platform","emotion","category","stage"].forEach(k=>{const v=filters[k];if(v&&hay.includes(v)){score+=4;reasons.push(`${k}:${v}`)}});
 if(item.targets?.includes("打法知识库"))score+=1;
 return{score,reason:[...new Set(reasons)].join("、")||"语义/标签弱相关"};
}
function builtInRagCorpus(){
 const knowhow=Object.entries(knowhowLibrary).map(([label,k])=>({id:`builtin_${label}`,type:"MMN内置Know-how",title:`${label}｜${k.crowd||"营销打法"}`,body:[k.why,k.message,k.proof,k.creator,k.risk].filter(Boolean).join(" "),keywords:extractKeywords(`${label} ${k.why} ${k.message} ${k.proof}`),tags:[label,k.crowd,k.message,k.proof].filter(Boolean),targets:["打法知识库","报告"],source:"builtin"}));
 const learned=learnings().map((x,i)=>({id:x.id||`learning_${i}`,type:"人工Learning",title:`${x.model||"车型"}｜${x.label||"人工结论"}`,body:[x.conclusion,x.recommendation,x.evidence,x.platform,x.kpi,x.stage].filter(Boolean).join(" "),keywords:extractKeywords([x.model,x.label,x.conclusion,x.recommendation,x.platform].join(" ")),tags:[x.model,x.label,x.platform,x.stage].filter(Boolean),targets:["人工结论学习","报告"],source:"learning"}));
 const judgments=(modelJudgments||[]).map((x,i)=>({id:x.knowledge_id||x.id||`model_judgment_${i}`,type:"车型判断资产",title:`${x.model_name||x.model||"车型"}｜${x.dimension||"综合判断"}`,body:[x.viewpoint,x.attribution,x.strategy_implication,x.evidence_needed].filter(Boolean).join(" "),keywords:[x.brand_name,x.model_name,x.dimension,...(x.tags||[])].filter(Boolean),tags:[x.brand_name,x.model_name,x.dimension,...(x.tags||[])].filter(Boolean),targets:["决策驾驶舱","RAG知识库管理","MMN策略"],source:"model_judgment",metadata:{entity:x.model_name||x.model,domain:"车型判断资产",module:x.dimension||"综合判断"}}));
 const blogger=(bloggerSkillState.knowledgeItems||[]).map(x=>({...x,source:x.source||"blogger_skill"}));
 const contentCapability=(contentCapabilityState.knowledgeItems||[]).map(x=>({...x,source:x.source||"content_capability_kb"}));
 return [...strategyKb.map(x=>({...x,source:x.source||"imported"})),...blogger,...contentCapability,...knowhow,...learned,...judgments];
}
function ragSearch({query="",rows=[],limit=6,filters={}}={}){
 const terms=[...new Set([...extractKeywords(query),...String(query).split(/[\\s,，、/｜|]+/),...ragTagsFromRows(rows)])].filter(x=>x&&x.length>1);
 return builtInRagCorpus().map(item=>{const s=ragScore(item,terms,filters);return{...item,score:s.score,reason:s.reason}}).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,limit);
}
function summarizeKnowledgeText(text){
 const cleaned=String(text||"").replace(/\r/g,"\n").split("\n").map(x=>x.trim()).filter(Boolean);
 const chunks=cleaned.flatMap(line=>line.split(/(?<=[。！？；;])/)).map(x=>x.trim()).filter(x=>x.length>=12);
 const candidates=chunks.filter(x=>/应该|需要|关键|核心|建议|判断|打法|证据|客户|用户|竞品|内容|报告|趋势|风险|机会|转化|认知/.test(x)).slice(0,24);
 const source=candidates.length?candidates:chunks.slice(0,16);
 return source.map((body,i)=>{const type=classifyKnowledge(body),keywords=extractKeywords(body);return{id:`kb_${Date.now()}_${i}_${Math.random().toString(16).slice(2,7)}`,type,title:keywords.length?`${type}｜${keywords.slice(0,3).join(" / ")}`:`${type}｜策略片段`,body:body.slice(0,220),keywords,tags:keywords,targets:knowledgeTargets(type),createdAt:new Date().toISOString()}}).filter(x=>x.body);
}
function relatedKnowledge(label,limit=2){
 return ragSearch({query:label,limit});
}
function renderVideoBars(sel,data){
 const max=Math.max(...data.map(x=>x.count),1);document.querySelector(sel).innerHTML=data.slice(0,10).map(x=>`<div class="video-bar"><b>${x.key}</b><div><i style="width:${x.count/max*100}%"></i></div><span>${x.count}</span></div>`).join("")||"<p class='empty'>暂无数据</p>";
}
function renderActions(a){const list=a.labels.filter(x=>x.priority>0).slice(0,10),sum=list.reduce((s,x)=>s+x.priority,0)||1;document.querySelector("#budget-total").textContent=money(+state.config.budget);document.querySelector("#action-list").innerHTML=list.map((x,i)=>{const ac=actionFor(x),budget=state.config.budget*x.priority/sum,learned=latestLearning(x.label);return`<div class="action-item"><div class="rank">${String(i+1).padStart(2,"0")}</div><div class="action-main"><h3>${x.label} · ${x.diagnosis}</h3><p>系统结果：本品负向 ${Math.round(x.on).toLocaleString()}，竞品占有率 ${(x.cShare*100).toFixed(1)}%，认知 Gap ${(x.gap*100).toFixed(1)}%。${learned?`<br><b>你的历史建议：</b>${learned.recommendation}`:""}</p></div><div class="action-meta"><b>参考框架</b><span>${ac.evidence}</span></div><div class="action-meta"><b>参考平台</b><span>${learned?.platform||ac.platform}</span></div><div class="money"><strong>${money(budget)}</strong><span class="tag">优先级 ${x.priority.toFixed(1)}</span></div></div>`}).join("")}
function renderKnowhow(a){
 const list=a.labels.filter(x=>x.priority>0).slice(0,6),risks=a.labels.filter(x=>x.diagnosis==="优先修复").slice(0,3),assets=a.labels.filter(x=>x.diagnosis==="持续放大").slice(0,3);
 const identity=standardIdentityFor(state.config.model),source=document.querySelector("#knowhow-model-source"),sourceBrand=identity.brand_name||state.config.brand||"未识别品牌",sourceModel=identity.display_model_name||state.config.model||"未选择车型";
 if(source)source.innerHTML=`<div><span>当前车型来源</span><b>策略驾驶舱</b></div><div><span>品牌</span><b>${escapeAttr(sourceBrand)}</b></div><div><span>车型</span><b>${escapeAttr(sourceModel)}</b></div><small>本页跟随策略驾驶舱顶部“分析对象”同步刷新；这里展示的是该车型的打法知识，不是独立车型选择器。</small>`;
 const main=list[0],kh=main?knowhowFor(main):null;
 document.querySelector("#war-room").innerHTML=kh?`<div class="war-statement"><b>${state.config.model} 当前不是缺曝光，而是需要把“${main.label}”疑虑转化为可验证信任。</b><p>${kh.mode}。优先处理 ${risks.map(x=>x.label).join("、")||main.label}，再放大 ${assets.map(x=>x.label).join("、")||"已有正向资产"}。</p></div><div class="war-metrics"><span>主战场</span><strong>${main.category}</strong><span>优先打法</span><strong>${kh.type}</strong><span>成败指标</span><strong>${kh.kpi}</strong></div>`:"<p>暂无足够数据生成作战判断。</p>";
 document.querySelector("#evidence-chain").innerHTML=list.slice(0,4).map(x=>{const k=knowhowFor(x);return`<div class="evidence-item"><span>${x.label}</span><b>${k.proof}</b><small>${k.risk}</small></div>`}).join("");
 document.querySelector("#knowhow-cards").innerHTML=list.map((x,i)=>{const k=knowhowFor(x),learned=latestLearning(x.label),kb=relatedKnowledge(x.label,2);return`<article class="knowhow-card ${x.diagnosis==="优先修复"?"risk":x.diagnosis==="抢占空位"?"chance":"asset"}"><div class="kh-head"><span>${String(i+1).padStart(2,"0")}</span><div><b>${x.label}</b><small>${x.diagnosis} · 优先级 ${x.priority.toFixed(1)}</small></div></div><p class="kh-why">${k.why}</p>${learned?`<div class="learned-tip"><b>已学习你的判断</b><span>${learned.conclusion}</span><em>${learned.recommendation}</em></div>`:""}${kb.length?`<div class="kb-tip"><b>策略知识库补充</b>${kb.map(item=>`<span>${item.body}</span>`).join("")}</div>`:""}<dl><dt>参考人群</dt><dd>${k.crowd}</dd><dt>参考打法</dt><dd>${k.message}</dd><dt>证据链</dt><dd>${learned?.evidence||k.proof}</dd><dt>谁来讲</dt><dd>${k.creator}</dd><dt>平台</dt><dd>${learned?.platform||k.platform}</dd><dt>KPI</dt><dd>${learned?.kpi||k.kpi}</dd></dl></article>`}).join("");
 const platformScores=Object.entries(a.own.reduce((m,r)=>{m[r[2]]=(m[r[2]]||0)+(+r[8]||0);return m},{})).sort((a,b)=>b[1]-a[1]).slice(0,6);
 document.querySelector("#platform-playbook").innerHTML=platformScores.map(([p,n])=>`<div class="platform-row"><b>${p}</b><p>${platformAdvice(p)}</p><span>${Math.round(n).toLocaleString()} 条样本</span></div>`).join("");
 const c1=risks[0]?.label||list[0]?.label||"核心风险",c2=risks[1]?.label||list[1]?.label||"关键疑虑",c3=assets[0]?.label||list[2]?.label||"正向资产";
 document.querySelector("#campaign-calendar").innerHTML=[
  ["第1周","止血澄清",`围绕“${c1}”建立统一口径，发布官方解释、第三方实测和 FAQ。`],
  ["第2周","证据扩散",`把“${c1}/${c2}”做成抖音短视频、垂媒横评、B站深度拆解三种证据形态。`],
  ["第3周","场景转化",`组织车主/KOC用真实通勤、家庭、长途场景复现产品价值，承接试驾。`],
  ["第4周","资产放大",`把“${c3}”包装成可复述卖点，形成话题挑战、内容Brief和品牌传播口径。`]
	 ].map(x=>`<div class="time-item"><span>${x[0]}</span><b>${x[1]}</b><p>${x[2]}</p></div>`).join("");
	}
function renderFounderDistill(){
 const list=document.querySelector("#founder-archive-list");if(!list)return;
 const rows=founderRows();
 const archive=(founderState.archive||[]).filter(isValidFounderArchiveItem);
 const brands=["all",...[...new Set(archive.map(x=>x.brand).filter(Boolean))]];
 const persons=["all",...[...new Set(archive.map(x=>x.person).filter(Boolean))]];
 const topics=["all",...[...new Set(archive.flatMap(x=>[x.event_type||x.type,x.topic]).filter(Boolean))]];
 const fill=(sel,items,label)=>{const el=document.querySelector(sel);if(!el)return;const val=el.value||"all";el.innerHTML=items.map(x=>`<option value="${escapeAttr(x)}">${x==="all"?label:x}</option>`).join("");el.value=items.includes(val)?val:"all"};
 fill("#founder-brand-filter",brands,"全部品牌");
 fill("#founder-person-filter",persons,"全部人物");
 fill("#founder-topic-filter",topics,"全部事件");
 const speaker=document.querySelector("#founder-speaker");
 if(speaker){const current=speaker.value||founderState.selectedPerson||"";speaker.innerHTML=persons.filter(x=>x!=="all").map(x=>`<option value="${escapeAttr(x)}">${x}</option>`).join("");if([...speaker.options].some(o=>o.value===current))speaker.value=current}
 document.querySelector("#founder-archive-count").textContent=`${rows.length} 条`;
 list.innerHTML=rows.length?rows.map(x=>`<article class="founder-archive-card" data-founder-person="${escapeAttr(x.person)}"><div><span>${x.brand} · ${x.person}</span><b>${x.event_type||x.type||x.topic||"公开表达"}</b></div><p>${x.originalSummary||x.original_summary||x.content||""}</p><small>${x.published_at||x.date||""}｜${x.platform||"公开平台"}｜${x.sourceName||x.source_name||"公开来源"}</small><div>${(x.languageStyleTags||x.language_style_tags||x.tags||[]).slice(0,5).map(t=>`<em>${t}</em>`).join("")}</div></article>`).join(""):`<p class="empty">当前没有可蒸馏的高管公开表达。请补充具体文章、采访、发布会、直播文字稿或社媒公开链接；媒体首页、导航页和车型筛选页不会进入归档。</p>`;
 list.querySelectorAll("[data-founder-person]").forEach(card=>card.onclick=()=>{founderState.selectedPerson=card.dataset.founderPerson;saveFounderState();renderFounderDistill()});
 const activePerson=founderState.selectedPerson||persons.find(x=>x!=="all")||"";
 const profile=founderProfile(activePerson);
 const next=founderState.scheduler?.nextRunInSeconds;
 document.querySelector("#founder-distill-source").textContent=activePerson?`${profile.brand} · ${profile.person}`:"选择人物后生成";
 document.querySelector("#founder-profile").innerHTML=`<div class="founder-profile-head"><span>${profile.brand}</span><b>${profile.person}</b><small>${profile.role}</small></div><dl><dt>语言风格</dt><dd>${profile.style}</dd><dt>品牌叙事</dt><dd>${profile.narrative}</dd><dt>技术表达</dt><dd>${profile.tech}</dd><dt>用户沟通</dt><dd>${profile.user}</dd><dt>舆论攻防</dt><dd>${profile.defense}</dd><dt>Prompt模板</dt><dd>${profile.prompt}</dd></dl><p class="founder-schedule">自动任务：每周日 23:00 Asia/Shanghai${next?`｜下次约 ${Math.round(next/3600)} 小时后`:""}｜仅公开源，遵守 robots 与平台权限。</p>`;
 if(speaker&&activePerson&&[...speaker.options].some(o=>o.value===activePerson))speaker.value=activePerson;
 const output=document.querySelector("#founder-output");if(output&&!output.innerHTML&&founderState.lastOutput)output.innerHTML=founderState.lastOutput;
}
function renderStrategyKb(){
 const count=document.querySelector("#strategy-kb-count");if(!count)return;
 const byType=aggregateVideos(strategyKb.map(x=>({...x,category:x.type,engagement:1})),"category");
 count.textContent=`${strategyKb.length} 条知识`;
 document.querySelector("#strategy-kb-summary").innerHTML=strategyKb.length?byType.map(x=>`<div class="video-bar"><b>${x.key}</b><div><i style="width:${x.count/Math.max(...byType.map(y=>y.count),1)*100}%"></i></div><span>${x.count}</span></div>`).join(""):"<p class='empty'>还没有导入知识。你可以把策略对话、客户复盘或方法论文档粘贴到左侧，系统会先做本地归纳。</p>";
 renderKnowledgeMap();
 renderRagResults();
}
function renderKnowledgeMap(){
 const map=document.querySelector("#strategy-kb-map"),list=document.querySelector("#strategy-kb-list");if(!map||!list)return;
 const clusters=knowledgeClusters();
 if(!clusters.length){map.innerHTML="";list.innerHTML="<p class='empty'>暂无知识地图。导入MMN训练包后，会按品牌、车型和能力模块生成下钻入口。</p>";return}
 if(!selectedKnowledgeCluster||!clusters.some(x=>x.key===selectedKnowledgeCluster))selectedKnowledgeCluster=clusters[0].key;
 const max=Math.max(...clusters.map(x=>x.items.length),1);
 map.innerHTML=clusters.map(x=>`<button type="button" class="kb-cluster ${x.key===selectedKnowledgeCluster?"active":""}" data-kb-cluster="${x.key}"><span>${x.type}</span><b>${x.key}</b><em>${x.items.length} 条</em><i style="width:${Math.max(18,x.items.length/max*100)}%"></i></button>`).join("");
 const cluster=clusters.find(x=>x.key===selectedKnowledgeCluster)||clusters[0];
 const domainRows=Object.entries(cluster.domains).sort((a,b)=>b[1]-a[1]).slice(0,8);
 const samples=cluster.items.slice(0,8);
 list.innerHTML=`<div class="kb-cluster-detail"><div><span>${cluster.type}</span><h3>${cluster.key}</h3><p>已归入 ${cluster.items.length} 条知识。点击“巡检这个气泡”会把该品牌/模块带入RAG问题，进一步召回可引用依据。</p></div><button class="primary" data-kb-query="${cluster.key}">巡检这个气泡</button></div><div class="kb-domain-grid">${domainRows.map(([k,v])=>`<button type="button" data-kb-query="${cluster.key} ${k}"><b>${k}</b><span>${v} 条</span></button>`).join("")}</div><div class="kb-sample-list">${samples.map(x=>`<article class="kb-card compact"><div><span>${x.metadata?.doc_id||x.id||"local"}｜${x.type}</span><b>${x.title}</b></div><p>${x.body}</p><small>来源：${x.source||"imported"}｜关键词：${(x.keywords||[]).slice(0,8).join("、")||"—"}</small></article>`).join("")}</div>`;
 document.querySelectorAll("[data-kb-cluster]").forEach(b=>b.onclick=()=>{selectedKnowledgeCluster=b.dataset.kbCluster;renderKnowledgeMap();pulseFocus(`[data-kb-cluster="${CSS.escape(selectedKnowledgeCluster)}"]`);pulseFocus(".kb-cluster-detail")});
 document.querySelectorAll("[data-kb-query]").forEach(b=>b.onclick=()=>{pulseFocus(b);document.querySelector("#rag-query").value=b.dataset.kbQuery;ragResultsExpanded=false;renderRagResults();pulseFocus("#rag-results-toggle");document.querySelector("#rag-results").scrollIntoView({behavior:"smooth",block:"start"})});
}
function renderRagResults(){
 const box=document.querySelector("#rag-results");if(!box)return;
 const query=document.querySelector("#rag-query")?.value||`${state.config.model} ${state.config.brand} ${state.config.project}`;
 const filters={platform:document.querySelector("#rag-platform")?.value||"",emotion:document.querySelector("#rag-emotion")?.value||"",category:document.querySelector("#rag-category")?.value||"",stage:document.querySelector("#rag-stage")?.value||""};
 const results=ragSearch({query,limit:8,filters});
 const detail=results.length&&ragResultsExpanded?`<div class="rag-detail-list">${results.map((x,i)=>`<article class="rag-card"><span>${String(i+1).padStart(2,"0")}｜${x.type}｜${x.metadata?.doc_id||x.id||"local"}｜分数 ${x.score}</span><b>${x.title}</b><p>${x.body}</p><small>引用依据：${x.reason}｜来源：${x.source||"imported"}｜关键词：${(x.keywords||[]).join("、")||"—"}｜赋能：${(x.targets||[]).join("、")}</small></article>`).join("")}</div>`:results.length?"":`<p class="empty">没有找到匹配知识。可以换一个问法，或导入方法论、历史项目复盘、人工结论、平台打法文本。</p>`;
 box.innerHTML=`<button type="button" class="rag-summary-pill ${ragResultsExpanded?"open":""}" id="rag-results-toggle"><b>策略准备完成：召回 ${results.length} 条相关依据</b><span>${ragResultsExpanded?"收起引用依据":"点击展开引用依据"} · 查询：${query||"当前项目上下文"}</span></button>${detail}`;
 document.querySelector("#rag-results-toggle").onclick=()=>{ragResultsExpanded=!ragResultsExpanded;renderRagResults();pulseFocus("#rag-results-toggle");if(ragResultsExpanded)setTimeout(()=>pulseFocus(".rag-card"),80)};
}
function strategyProjectContext(){
 return{edition:activeEdition(),brand:state.config.brand,model:state.config.model,project:state.config.project,competitor:state.config.competitor,targetIdentity:state.config.targetIdentity,budget:state.config.budget,stage:state.config.stage||"上市中"};
}
function strategyReportSourceType(){
 const source=`${state.datasetVersion||""} ${state.sourceNote||""} ${state.importQuality?.kind||""}`.toLowerCase();
 if(/demo|演示|seed|种子/.test(source))return"demo";
 if(/cache|缓存/.test(source))return"cache";
 if(/degrad|降级|unavailable|不可用/.test(source))return"degraded";
 if(/import|xlsx|csv|导入|product_evaluation/.test(source))return"user_imported";
 return source.trim()?"unknown":"unknown";
}
function strategyReportTimeRange(){
 const label=dashboardTimeDimension()||"当前证据时间范围未知",dates=[...String(label).matchAll(/\d{4}-\d{2}-\d{2}/g)].map(match=>match[0]);
 return{start:dates[0]||"",end:dates.at(-1)||"",label};
}
function strategyReportProjectId(){
 const exact=(workspaceState.snapshots||[]).find(item=>item.project===state.config.project&&item.model===state.config.model);
 return exact?.id||"";
}
function strategyReportTContext(){
 const context=loadMarketingModelContext(),phase=marketingModelPhase(context),selected=phase.selected,current=phase.current;
 return{
  firstDate:context.firstDate||"",t0Date:context.t0Date||"",assessmentDate:context.assessmentDate||"",
  offset:Number.isFinite(phase.offset)?phase.offset:null,display:globalThis.MmnTCycle?.tLabel(phase.offset)||"待设置",
  phaseKey:selected?.key||"",phaseLabel:selected?.label||"未知",phaseRange:selected?.range||"",
  currentPhaseKey:current?.key||"",source:context.cycleSource||context.salesWarningCycle?.source||"unknown",
  status:context.cycleStatus||context.salesWarningCycle?.status||"unknown"
 };
}
function buildStrategyReportExportInput({force=false}={}){
 const model=state.config.model,configured=String(state.config.competitor||"").split(/[\/、,，|｜]/).map(item=>item.trim()).filter(Boolean),allowedModels=new Set([model,...configured,...nsrMapSelectedModels].filter(Boolean));
 const rows=(state.rows||[]).filter(row=>allowedModels.has(String(row?.[0]||""))),verticalRows=(verticalState.items||[]).filter(item=>String(item.ownModel||item.own_model||"")===model),videos=allVideoItems().filter(item=>itemMatchesAssetModel(item,model)).slice(0,120);
 const a=analysis(),sourceType=strategyReportSourceType(),phase=strategyReportTContext(),manualLearnings=learnings().filter(item=>item.model===model),judgments=(modelJudgments||[]).filter(item=>String(item.model_name||item.model||"")===model);
 const diagnostics=(a.labels||[]).map(item=>({label:item.label,category:item.category,diagnosis:item.diagnosis,priority:item.priority,gap:item.gap,ownScore:item.ownAvg,evidenceStatus:item.attributeEvidenceStatus||"unknown"}));
 const moduleStatuses={
  project:{status:model&&state.config.project?"available":"missing",sourceType},
  tCycle:{status:phase.t0Date?phase.status:"missing",sourceType:phase.status==="verified"?"real":"unknown"},
  salesAndMarket:{status:phase.status||"unknown",sourceType:phase.status==="verified"?"real":"unknown"},
  brandPenetration:{status:"read_from_server_if_available",sourceType:"unknown"},
  socialTrends:{status:"read_from_server_if_available",sourceType:"unknown"},
  douyinInsights:{status:videos.length?"available":"missing",sourceType:videos.length?sourceType:"unknown"},
  nsrAndCognition:{status:rows.length?"available":"missing",sourceType},
  verticalCompetition:{status:verticalRows.length?"available":"missing",sourceType:verticalRows.length?"user_imported":"unknown"},
  policyImpact:{status:"read_from_server_if_available",sourceType:"unknown"},
  productWhitepaper:{status:productWhitepaperUploadState.error?"degraded":"read_from_server_if_available",sourceType:productWhitepaperUploadState.error?"degraded":"unknown"},
  sellingPointDecision:{status:sellingPointAdvisoryState.result?.status||"missing",sourceType:sellingPointAdvisoryState.result?.cached?"cache":sourceType},
  contentStrategy:{status:dashboardTopicPlanState.result?"available":"missing",sourceType:dashboardTopicPlanState.result?.local?"degraded":"unknown"},
  actionResultLearningKnowhow:{status:cockpitDecisionState.cycles.length||manualLearnings.length?"available":"missing",sourceType:manualLearnings.length?"user_imported":"unknown"},
  chartData:{status:diagnostics.length||verticalRows.length?"available":"missing",sourceType}
 };
 return{
  force,
  scope:{edition:activeEdition(),projectId:strategyReportProjectId(),project:state.config.project,brand:state.config.brand,model,timeRange:strategyReportTimeRange(),tCycle:phase,cockpitVersion:APP_VERSION},
  moduleStatuses,
  moduleData:{
   projectAndVehicle:{sourceType,config:{...state.config},datasetVersion:state.datasetVersion||"unknown",sourceNote:state.sourceNote||"未知"},
   tCycle:{sourceType:moduleStatuses.tCycle.sourceType,...phase},
   productEvaluation:{sourceType,rows,summaryMetrics:state.summaryMetrics||{},summaryHeat:state.summaryHeat||{},summaryPlatformNsr:state.summaryPlatformNsr||{},importQuality:state.importQuality||{}},
   verticalCompetition:{sourceType:moduleStatuses.verticalCompetition.sourceType,rows:verticalRows},
   douyinAndContentAssets:{sourceType:moduleStatuses.douyinInsights.sourceType,items:videos},
   sellingPointDecision:{sourceType:moduleStatuses.sellingPointDecision.sourceType,result:sellingPointAdvisoryState.result||null},
   contentStrategy:{sourceType:moduleStatuses.contentStrategy.sourceType,result:dashboardTopicPlanState.result||null}
  },
  chartData:{perceptionDiagnostics:diagnostics,competitorTrend:dashboardCompetitorSeries(model),verticalTrend:verticalRows,summaryHeat:state.summaryHeat||{},rawScopedRows:rows},
  evidence:{sellingPoint:sellingPointAdvisoryState.result?.evidencePacket||null,opportunityDocument:opportunityEvidenceState.document||null,contentItems:videos},
  decisions:{humanLearnings:manualLearnings,humanModelJudgments:judgments,actionCycles:cockpitDecisionState.cycles,topicPlan:dashboardTopicPlanState.result||null,sellingPointAdvisory:sellingPointAdvisoryState.result||null}
 };
}
function renderStrategyReportExport(){
 const status=document.querySelector("#strategy-report-export-status"),run=document.querySelector("#strategy-report-export-run"),download=document.querySelector("#strategy-report-export-download"),regenerate=document.querySelector("#strategy-report-export-regenerate");if(!status||!run||!download||!regenerate)return;
 run.disabled=strategyReportExportState.loading;run.hidden=Boolean(strategyReportExportState.result)&&!strategyReportExportState.loading;
 download.hidden=!strategyReportExportState.result;regenerate.hidden=!strategyReportExportState.result||strategyReportExportState.loading;
 if(strategyReportExportState.loading){status.textContent="三路整理中；三路均使用同一冻结快照和证据指纹。";return}
 if(strategyReportExportState.error){status.textContent=`生成失败：${strategyReportExportState.error}`;return}
 const pkg=strategyReportExportState.result?.package,snapshot=strategyReportExportState.result?.snapshot;
 if(pkg){status.textContent=`${pkg.status==="completed"?"资料包已生成":"资料包部分完成"} · ${pkg.completedChannelCount}/3路 · 快照 ${snapshot.snapshotId} · 证据指纹 ${snapshot.evidenceFingerprint.slice(0,12)}…`;return}
 status.textContent="冻结当前驾驶舱数据，交由三路独立整理后生成Codex资料包。";
}
async function runStrategyReportExport(force=false){
 strategyReportExportState={loading:true,result:strategyReportExportState.result,error:""};renderStrategyReportExport();
 const status=document.querySelector("#strategy-report-export-status");if(status)status.textContent="正在冻结数据…";
 const progressTimer=setTimeout(()=>{if(strategyReportExportState.loading&&status)status.textContent="三路整理中；三路均使用同一冻结快照和证据指纹。"},350);
 try{
  const data=await api("/api/strategy-report-packages",{method:"POST",body:JSON.stringify(buildStrategyReportExportInput({force}))});
  strategyReportExportState={loading:false,result:{snapshot:data.snapshot,package:data.package},error:""};renderStrategyReportExport();
  toast(data.package.status==="completed"?"策略汇报资料包已生成":"资料包部分完成，失败通道已如实标记");
 }catch(err){strategyReportExportState={loading:false,result:null,error:err.message};renderStrategyReportExport();toast(`资料包生成失败：${err.message}`)}finally{clearTimeout(progressTimer)}
}
async function downloadStrategyReportPackage(){
 const pkg=strategyReportExportState.result?.package;if(!pkg)return;
 try{const response=await fetch(pkg.downloadUrl,{headers:authHeaders()});if(!response.ok){const error=await response.json().catch(()=>({error:"下载失败"}));throw new Error(error.error||"下载失败")}const blob=await response.blob(),link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=pkg.filename;link.click();URL.revokeObjectURL(link.href);toast("资料包已下载")}catch(err){toast(`资料包下载失败：${err.message}`)}
}
async function submitModelJudgment(e){
 e.preventDefault();
 const form=e.target,textarea=form.elements.judgment,btn=document.querySelector("#model-judgment-submit"),text=textarea.value.trim();
 if(!text){toast("先输入一句车型判断");return}
 const old=btn.textContent;btn.disabled=true;btn.textContent="MMN学习中…";
 try{
  const data=await api("/api/ai/model-judgment",{method:"POST",body:JSON.stringify({edition:activeEdition(),text,project:strategyProjectContext()})});
  if(data.item)upsertModelJudgment(data.item);
  if(data.knowledgeItem)mergeStrategyKnowledge([data.knowledgeItem]);
  const modelName=data.item?.model_name||state.config.model;
  if(modelName&&modelName!==state.config.model){applyModelSelection(modelName)}
  textarea.value="";
  save();render();
  toast(data.model==="local-rule"?"MMN已用本地规则先入库，模型兜底暂未完成":"MMN已完成车型判断并写入资产库");
 }catch(err){
  toast(`车型判断学习失败：${err.message}`);
 }finally{
  btn.disabled=false;btn.textContent=old;
 }
}
function markdownish(text){
 return publicMmnText(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").split(/\n{2,}/).map(block=>`<p>${block.replace(/\n/g,"<br>")}</p>`).join("");
}
function escapeHtml(text){
 return publicMmnText(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function publicMmnText(text){
 return String(text||"").trim()
  .replace(/Qwen|千问/gi,"MMN主控")
  .replace(/DeepSeek/gi,"MMN质检")
  .replace(/TikHub/gi,"补充采集服务")
  .replace(/社媒助手/gi,"公开数据工具")
  .replace(/Kimi/gi,"MMN校验")
  .replace(/OpenAI|ChatGPT/gi,"MMN外部网关");
}
function publicMmnProviderLabel(value){
 const key=String(value||"").trim().toLowerCase();
 return({qwen:"MMN主控",deepseek:"MMN质检",kimi:"MMN校验",openai:"MMN外部网关",tikhub:"补充采集服务",rules:"MMN本地规则"})[key]||publicMmnText(value)||"能力服务";
}
function consultingMarkdown(text){
 const safe=publicMmnText(text).replace(/\*\*/g,"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
 return safe.split(/\n+/).map(line=>{
  const s=line.trim();
  if(!s)return"";
  if(s.startsWith("### "))return`<h3>${s.replace(/^###\s+/,"")}</h3>`;
  return`<p>${s}</p>`;
 }).join("");
}
function consultingOutputText({conclusion,findings=[],evidence=[],implication,actions=[]}){
 return ["### Executive Conclusion",conclusion,"### Key Findings",...findings,"### Evidence",...evidence,"### Strategic Implication",implication,"### Action Recommendation",...actions].join("\n\n");
}
function loadStrategyAnswerCache(){try{return JSON.parse(localStorage.getItem(storageKey("mmnStrategyAnswerCache")))||{items:{},order:[]}}catch{return{items:{},order:[]}}}
function saveStrategyAnswerCache(cache){localStorage.setItem(storageKey("mmnStrategyAnswerCache"),JSON.stringify(cache))}
function strategyCacheKey(mode,query,references=[]){
 const refKeys=references.map(x=>x.id||x.metadata?.doc_id||x.title||"").slice(0,8).join("|");
 return [mode,activeEdition(),state.config.model,state.config.project,query,refKeys].join("::");
}
function getCachedStrategy(mode,query,references){
 const cache=loadStrategyAnswerCache(),key=strategyCacheKey(mode,query,references);
 return cache.items[key]||null;
}
function setCachedStrategy(mode,query,references,data){
 const cache=loadStrategyAnswerCache(),key=strategyCacheKey(mode,query,references);
 cache.items[key]={...data,cachedAt:new Date().toISOString()};
 cache.order=[key,...(cache.order||[]).filter(x=>x!==key)].slice(0,24);
 Object.keys(cache.items).forEach(k=>{if(!cache.order.includes(k))delete cache.items[k]});
 saveStrategyAnswerCache(cache);
}
function renderMmnStrategyBubble({query,references,data,cached=false}){
 const box=document.querySelector("#rag-results");if(!box)return;
 const modelCopy=data.model==="local-rag"?"MMN本地规则兜底":data.model==="local-rule"?"MMN本地规则兜底":"MMN多模型引擎";
 const cachedCopy=cached?" · 已缓存":"";
 const qa=data.qa||data.agentRun?.qa_summary||null;
 const decision=data.routerDecision||data;
 const conflict=decision.conflict||data.conflict||null;
 const evidence=data.evidence||data.agentRun?.evidence||[];
 const topicPlan=data.topicPlan||data.agentRun?.final_output?.topicPlan||null;
 const qaLabel=qa?qa.verdict==="pass"?"Evidence QA 通过":qa.verdict==="needs_review"?"Evidence QA 待复核":"Evidence QA 未通过":"Evidence QA 未运行";
 const qaClass=qa?.verdict==="pass"?"pass":qa?.verdict==="fail"?"fail":"review";
 const findings=(qa?.findings||[]).slice(0,3);
 const qaHtml=qa?`<div class="agent-run-panel ${qaClass}"><div><b>${qaLabel}</b><span>Run ${data.run_id||data.agentRun?.id||"local"} · 证据 ${qa.evidence_count??evidence.length} 条 · 诊断 ${qa.diagnostic_count??0} 项</span></div>${findings.length?`<ul>${findings.map(x=>`<li>${String(x.message||x.category||"QA提示").replace(/&/g,"&amp;").replace(/</g,"&lt;")}</li>`).join("")}</ul>`:""}</div>`:"";
 const isReviewPending=conflict?.status==="review_pending"||data.reviewStatus==="queued"||data.reviewStatus==="running";
 const reviewActions=isReviewPending?`<div class="router-review-actions"><button type="button" class="primary" data-router-deep-review="${decision.id||data.id||""}">深度复核</button><button type="button" class="ghost" data-router-refresh-review="${decision.id||data.id||""}">刷新复核</button></div>`:conflict?.status==="needs_human_review"?`<div class="router-review-actions"><button type="button" class="ghost" data-router-choice="primary">采纳主分析</button><button type="button" class="ghost" data-router-choice="reviewer">采纳复核意见</button><button type="button" class="primary" data-router-choice="manual">保存人工结论</button></div>`:"";
 const conflictHtml=conflict?`<div class="agent-run-panel ${conflict.status==="aligned"?"pass":"review"}"><div><b>${conflict.label||"MMN交叉复核"}</b><span>任务：${decision.taskType||data.taskType||"strategy"} · 置信度 ${Math.round((conflict.confidence||0)*100)}% · 主分析与独立复核</span></div>${reviewActions}</div>`:"";
 const phaseCopy=isReviewPending?"后台深度复核进行中，初版结果可先使用":data.cached?"命中缓存":data.asyncReview?"已进入后台复核":"策略链路完成";
 box.innerHTML=`<div class="mmn-strategy-chat"><div class="mmn-user-bubble">${escapeHtml(query)}</div><article class="mmn-ai-bubble"><div class="mmn-ai-head"><b>${data.modelLabel||"MMN智能策略"}</b><span>RAG巡检 + ${modelCopy}${cachedCopy} · ${phaseCopy}</span></div>${qaHtml}${conflictHtml}<div class="mmn-ai-content">${consultingMarkdown(data.text)}</div>${renderTopicPlanPanel(topicPlan)}<button type="button" class="rag-summary-pill" id="rag-results-toggle"><b>查看引用依据：${evidence.length||references.length} 条</b><span>点击展开本次策略引用了哪些知识</span></button><div class="mmn-engine-signature">该策略由MMN营销引擎输出</div></article></div>`;
 document.querySelector("#rag-results-toggle").onclick=()=>{ragResultsExpanded=!ragResultsExpanded;renderRagResults();if(ragResultsExpanded)setTimeout(()=>pulseFocus(".rag-card"),80)};
 document.querySelectorAll("[data-router-choice]").forEach(btn=>btn.onclick=()=>confirmRouterDecision(btn.dataset.routerChoice,decision));
 document.querySelectorAll("[data-router-deep-review]").forEach(btn=>btn.onclick=()=>requestDeepRouterReview(btn.dataset.routerDeepReview,query,references,data));
 document.querySelectorAll("[data-router-refresh-review]").forEach(btn=>btn.onclick=()=>refreshRouterReview(btn.dataset.routerRefreshReview,query,references,data));
 if(isReviewPending&&(decision.id||data.id))scheduleRouterReviewPoll(decision.id||data.id,query,references,data);
}
function renderTopicPlanPanel(plan){
 if(!plan)return"";
 const summary=plan.inputSummary||{};
 const phases=(plan.phases||[]).slice(0,4);
 const creators=(plan.creatorMatches||[]).slice(0,5);
 const schedule=(plan.schedule||[]).slice(0,8);
 const selected=(plan.selectedTopics||[]).slice(0,6);
 const topicCards=selected.map(x=>`<article><span>${escapeHtml((x.taxonomy||[]).join(" / "))}</span><b>${escapeHtml(x.topic)}</b><p>${escapeHtml(x.fitReason)}</p><small>阶段：${escapeHtml((x.communicationStages||[]).join("、"))}｜目标：${escapeHtml((x.contentGoals||[]).join("、"))}｜优先级 ${escapeHtml(x.priority)}</small></article>`).join("");
 const phaseHtml=phases.map(x=>`<div><b>${escapeHtml(x.phase)}</b><span>${escapeHtml(x.strategy)}</span><small>${(x.topics||[]).slice(0,3).map(t=>escapeHtml(t.topic)).join(" / ")}</small></div>`).join("");
 const creatorHtml=creators.map(x=>`<tr><td>${escapeHtml(x.topic)}</td><td>${escapeHtml(x.primaryCreatorType)}</td><td>${escapeHtml(x.backupCreatorType)}</td><td>${escapeHtml(x.brief)}</td></tr>`).join("");
 const scheduleHtml=schedule.map(x=>`<tr><td>${escapeHtml(x.week)}</td><td>${escapeHtml(x.phase)}</td><td>${escapeHtml(x.topic)}</td><td>${escapeHtml(x.format)}</td><td>${escapeHtml(x.kpi)}</td></tr>`).join("");
 const modelNarrative=plan.modelNarrative?`<details class="topic-model-narrative"><summary>${escapeHtml(plan.modelLabel||"MMN深度策略结论")}</summary><div>${markdownish(plan.modelNarrative)}</div></details>`:"";
 return`<section class="topic-plan-panel"><div class="topic-plan-head"><div><b>车型传播选题规划器</b><span>${escapeHtml(plan.taxonomyVersion)} · ${escapeHtml(summary.model||"当前车型")} · ${escapeHtml(summary.launchStage||"传播阶段")} · ${escapeHtml(summary.communicationPlatform||"传播平台")} · ${escapeHtml(summary.budgetTier||"预算层级")}</span></div><em>${escapeHtml(plan.modelLabel||plan.engine||"topic_planning_engine")}</em></div><p class="topic-plan-conclusion">${escapeHtml(plan.strategyConclusion||"")}</p>${modelNarrative}<div class="topic-phase-grid">${phaseHtml}</div><div class="topic-card-grid">${topicCards}</div><div class="topic-table-wrap"><table><thead><tr><th>选题</th><th>主达人</th><th>备选达人</th><th>Brief要点</th></tr></thead><tbody>${creatorHtml}</tbody></table></div><div class="topic-table-wrap"><table><thead><tr><th>周期</th><th>阶段</th><th>选题</th><th>形式</th><th>KPI</th></tr></thead><tbody>${scheduleHtml}</tbody></table></div></section>`;
}
function immediateStrategyDraft(query,references,mode){
 const titles=references.slice(0,3).map(x=>x.title).filter(Boolean).join("、")||"当前知识库";
 const model=state.config.model||"当前车型";
 return{
  ok:true,
  model:"local-rag",
  mode,
  modelLabel:mode==="deep"?"MMN深度策略":"MMN快速策略",
  text:[
   "### Executive Conclusion",
   `${model}应先基于已召回依据形成可执行初稿，再决定投放和内容节奏。`,
   "### Key Findings",
   `- 当前优先问题是把用户最难理解、最容易犹豫的点拆成证据。[Evidence: E1]`,
   "- 证据解释应先于平台扩散和市场转化承接。[Evidence: E2]",
   "### Evidence",
   `- E1：本次已召回的主要依据为：${titles}。`,
   "- E2：模型完整版本仍在生成，当前内容属于RAG初稿，尚未完成最终交叉复核。",
   "### Strategic Implication",
   "若先追求大曝光，预算可能放大尚未解决的用户疑虑，降低后续市场转化效率。",
   "### Action Recommendation",
   "- P0｜现在：把问题拆成3条可验证证据；P1｜首轮内容：选择对应平台表达并补充车主或垂媒视角；P2｜复盘后：把有效说法写回MMN学习库。"
  ].join("\n\n")
 };
}
async function runMmnSmartStrategy(mode="fast"){
 const box=document.querySelector("#rag-results");if(!box)return;
 const query=(document.querySelector("#rag-query")?.value||"").trim()||`${state.config.model} 下一步营销策略怎么打`;
 const filters={platform:document.querySelector("#rag-platform")?.value||"",emotion:document.querySelector("#rag-emotion")?.value||"",category:document.querySelector("#rag-category")?.value||"",stage:document.querySelector("#rag-stage")?.value||""};
 const references=ragSearch({query,limit:8,filters});
 const cached=getCachedStrategy(mode,query,references);
 if(cached){renderMmnStrategyBubble({query,references,data:cached,cached:true});return}
 const label=mode==="deep"?"MMN深度策略":"MMN快速策略";
 renderMmnStrategyBubble({query,references,data:immediateStrategyDraft(query,references,mode)});
 toast(`${label}已先给出RAG初稿，模型完成后会自动刷新`);
 try{
  let data;
  const report=reportPayload();
  const payload={org_id:session?.org_id,user_id:session?.user_id,edition:activeEdition(),question:query,project:strategyProjectContext(),references,mode,signal:report,launchStage:document.querySelector("#rag-stage")?.value||state.config.stage||"上市中",coreSellingPoints:(report.knowhow||[]).slice(0,6).map(x=>x.label||x.message).filter(Boolean),competitors:String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean),budget:state.config.budget,targetAudience:state.config.targetIdentity,communicationGoal:query};
  try{
   data=await api("/api/agents/run",{method:"POST",body:JSON.stringify(payload)});
  }catch(agentErr){
   data=await api("/api/ai/rag-strategy",{method:"POST",body:JSON.stringify({question:query,project:strategyProjectContext(),references,mode})});
   data.qa={verdict:"needs_review",severity:"medium",evidence_count:references.length,diagnostic_count:0,findings:[{message:`Agent账本暂未记录，已回退旧策略接口：${agentErr.message}`}]};
  }
  setCachedStrategy(mode,query,references,data);
  renderMmnStrategyBubble({query,references,data});
 }catch(err){
  box.innerHTML=`<div class="mmn-strategy-chat"><div class="mmn-user-bubble">${query.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div><article class="mmn-ai-bubble"><b>${label}生成失败</b><p>${err.message}</p><div class="mmn-engine-signature">该策略由MMN营销引擎输出</div></article></div>`;
	 toast(`${label}失败：${err.message}`);
	 }
}
let routerReviewPollTimer=null;
function scheduleRouterReviewPoll(id,query,references,data){
 if(routerReviewPollTimer)clearTimeout(routerReviewPollTimer);
 routerReviewPollTimer=setTimeout(()=>refreshRouterReview(id,query,references,data,true),3600);
}
async function requestDeepRouterReview(id,query,references,data){
 if(!id){toast("当前结果缺少复核记录ID");return}
 try{
  await api("/api/ai/router-review",{method:"POST",body:JSON.stringify({id,mode:"deep"})});
  toast("深度复核已进入后台，完成后会刷新到当前结果");
  scheduleRouterReviewPoll(id,query,references,data);
 }catch(err){toast(`深度复核启动失败：${err.message}`)}
}
async function refreshRouterReview(id,query,references,data,silent=false){
 if(!id)return;
 try{
  const res=await api(`/api/ai/router-review?id=${encodeURIComponent(id)}`);
  const next={...data,...(res.decision||{}),routerDecision:res.decision,conflict:res.decision?.conflict||data.conflict,reviewStatus:res.reviewTask?.status||res.decision?.conflict?.status};
  renderMmnStrategyBubble({query,references,data:next});
  if(!silent)toast(next.conflict?.status==="review_pending"?"深度复核仍在后台进行":"深度复核结果已刷新");
 }catch(err){if(!silent)toast(`复核刷新失败：${err.message}`)}
}
async function seedFounderArchive(){
 try{
  toast("正在导入公开表达样例…");
  const data=await api("/api/founder-archives/seed",{method:"POST",body:JSON.stringify({edition:activeEdition()})});
  await loadFounderArchives();
  toast(`已导入 ${data.count||0} 条创始人蒸馏样例`);
 }catch(err){toast(`导入失败：${err.message}`)}
}
async function confirmRouterDecision(choice,decision){
 if(!decision?.id){toast("当前结果缺少复核记录ID，无法回流");return}
 const finalText=choice==="reviewer"?(decision.reviewText||decision.reviewer_output||""):choice==="manual"?prompt("请输入人工最终结论，保存后会回流到MMN策略知识库：",decision.primaryText||decision.text||""):(decision.primaryText||decision.text||"");
 if(choice==="manual"&&!finalText)return;
 try{
  const data=await api("/api/ai/router-feedback",{method:"POST",body:JSON.stringify({id:decision.id,choice:choice==="primary"?"采纳主分析":choice==="reviewer"?"采纳复核意见":"人工最终结论",finalText,org_id:session?.org_id,user_id:session?.user_id})});
  if(data.knowledgeItem)mergeStrategyKnowledge([data.knowledgeItem]);
  renderStrategyKb();
  toast("人工确认已回流到MMN策略知识库");
 }catch(err){toast(`复核回流失败：${err.message}`)}
}
async function runFounderWeeklyCrawl(){
 const btn=document.querySelector("#run-founder-distill"),old=btn?.textContent;
 if(btn){btn.disabled=true;btn.textContent="周度抓取中…"}
	 try{
	  const data=await api("/api/founder-archives/run-weekly",{method:"POST",body:JSON.stringify({edition:activeEdition()})});
	  await loadFounderArchives();
	  const count=data.items?.length||0;
	  if(count){
	   toast(`周度巡检完成：新增 ${count} 条可蒸馏公开表达`);
	  }else{
	   toast("本次未发现可蒸馏公开表达；媒体首页和导航页已自动拦截，请导入公开数据文件或补充具体文章链接");
	  }
	 }catch(err){toast(`周度抓取失败：${err.message}`)}
 finally{if(btn){btn.disabled=false;btn.textContent=old}}
}
async function generateFounderTalk(){
 const person=document.querySelector("#founder-speaker")?.value||founderState.selectedPerson;
 const scene=document.querySelector("#founder-scene")?.value||"发布会";
 const brief=document.querySelector("#founder-brief")?.value.trim()||"围绕当前品牌传播重点生成高管IP表达";
 const box=document.querySelector("#founder-output");
 if(!person){toast("请先选择一位创始人/高管");return}
 box.innerHTML=`<div class="mmn-ai-bubble"><b>MMN正在生成高管IP表达…</b><p>MMN高管蒸馏模型正在完成表达生成、策略推理与风险质检。</p></div>`;
 try{
  const data=await api("/api/ai/founder-talk",{method:"POST",body:JSON.stringify({edition:activeEdition(),person,scene,brief})});
  const html=`<div class="mmn-strategy-chat"><article class="mmn-ai-bubble"><div class="mmn-ai-head"><b>${person} · ${scene}表达</b><span>MMN高管蒸馏模型</span></div><div class="mmn-ai-content">${markdownish(data.draft)}</div><div class="founder-review"><b>MMN策略质检</b>${markdownish(data.review)}</div><div class="mmn-engine-signature">该表达由MMN营销引擎输出，基于公开表达风格蒸馏，不代表本人原话</div></article></div>`;
	  box.innerHTML=html;
	  founderState.lastOutput=html;saveFounderState();
	  const profile=founderProfile(person);mergeStrategyKnowledge([founderKnowledgeItem(profile,`${data.draft}\n\n${data.review}`)]);
	  await loadFounderArchives();
	  toast(data.archiveItem?"高管IP表达已生成，并沉淀到创始人蒸馏库":"高管IP表达已生成并写入策略知识库");
 }catch(err){
  box.innerHTML=`<div class="mmn-ai-bubble"><b>生成失败</b><p>${err.message}</p></div>`;
  toast(`生成失败：${err.message}`);
	 }
	}
async function loadBloggerSkill(){
 try{
  const data=await api(`/api/blogger-skill?edition=${encodeURIComponent(activeEdition())}`);
  bloggerSkillState={...bloggerSkillState,...data};
  mergeDistilledCreatorLibraries(data.creatorLibraries);
  renderBloggerSkill();
  renderCreatorLibrary();
  const job=data.importJob;
  if(job?.id&&["queued","running"].includes(job.status)&&bloggerImportPollingJobId!==job.id){
   pollBloggerImportJob(job.id).catch(err=>toast(`导入进度跟踪失败：${err.message}`));
  }
 }catch(err){
  bloggerSkillState={...bloggerSkillState,error:err.message};
  renderBloggerSkill();
 }
}
const BLOGGER_IMPORT_PHASES=[
 ["import","导入","识别文件与达人身份"],
 ["distillation","蒸馏","拆解内容与判断方法"],
 ["analysis","分析","生成画像并完成证据质检"],
 ["delivery","交付","保存完整能力卡与可调用资产"],
];
function bloggerImportProgressMarkup(job){
 if(!job?.id)return "";
 const progress=Math.max(0,Math.min(100,Number(job.progress)||0));
 const currentIndex=Math.max(0,BLOGGER_IMPORT_PHASES.findIndex(([key])=>key===job.stage));
 const completed=job.status==="completed",failed=job.status==="failed";
 const stateLabel=completed?"已完成":failed?"未完成":job.status==="queued"?"等待开始":"处理中";
 return `<section class="blogger-import-progress ${completed?"completed":failed?"failed":"running"}" aria-live="polite">
  <div class="blogger-import-progress-head"><div><span>公开主证据 · 能力卡生成任务</span><b>${escapeHtml(job.creatorName||job.filename||"新达人")}</b><small>${escapeHtml(job.message||"任务已提交")}</small></div><strong>${stateLabel} · ${progress}%</strong></div>
  <div class="blogger-import-meter"><progress max="100" value="${progress}" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}" aria-label="达人能力卡生成进度"></progress></div>
  <div class="blogger-import-phases">${BLOGGER_IMPORT_PHASES.map(([key,label,desc],index)=>{
   const phaseState=completed||index<currentIndex?"done":failed&&index===currentIndex?"failed":index===currentIndex?"active":"pending";
   return `<div class="${phaseState}"><i>${completed||index<currentIndex?"✓":index+1}</i><span><b>${label}</b><small>${desc}</small></span></div>`;
  }).join("")}</div>
  ${job.error?`<p class="blogger-import-error">${escapeHtml(publicMmnText(job.error))}</p>`:""}
  ${failed?`<button type="button" class="secondary" data-blogger-import-retry="${escapeAttr(job.id)}">重新处理此文件</button>`:""}
  <small class="blogger-import-job-id">任务 ID：${escapeHtml(job.id)} · 页面刷新后仍会保留进度</small>
 </section>`;
}
function renderBloggerSkill(){
 const root=document.querySelector("#blogger-skill-samples");if(!root)return;
 const stats=bloggerSkillState.stats||{};
 const set=(sel,text)=>{const el=document.querySelector(sel);if(el)el.textContent=text};
 set("#blogger-skill-source-count",(stats.sources||0).toLocaleString());
 set("#blogger-skill-sample-count",(stats.samples||0).toLocaleString());
 set("#blogger-skill-profile-count",(stats.profiles||0).toLocaleString());
 set("#blogger-skill-rag-count",(stats.ragChunks||0).toLocaleString());
 set("#blogger-skill-strategy-count",(stats.strategyAssets||0).toLocaleString());
 set("#blogger-skill-script-count",(stats.scriptAssets||0).toLocaleString());
 const allSamples=bloggerSkillState.samples||[];
 const allProfiles=bloggerSkillState.profiles||[];
 const allWorkbenches=bloggerSkillState.creatorWorkbenches||[];
 const creatorNameKey=value=>String(value||"").replace(/[\s·・_-]+/g,"").toLowerCase();
 const names=[...new Set([...allProfiles.map(x=>x.blogger_name),...allSamples.map(x=>x.blogger_name),...allWorkbenches.map(x=>x.displayName)].filter(Boolean))];
 if(!bloggerSkillPersonFilter||!names.includes(bloggerSkillPersonFilter))bloggerSkillPersonFilter=names[0]||"";
 const personSelect=document.querySelector("#blogger-skill-person-select");
 if(personSelect){
  personSelect.innerHTML=names.length?names.map(x=>`<option value="${escapeAttr(x)}">${x}</option>`).join(""):`<option value="">暂无蒸馏对象</option>`;
  personSelect.value=bloggerSkillPersonFilter;
 }
 const samples=bloggerSkillPersonFilter?allSamples.filter(x=>x.blogger_name===bloggerSkillPersonFilter):allSamples;
 set("#blogger-skill-sample-count",samples.length.toLocaleString());
 set("#blogger-skill-status",bloggerSkillState.error?`加载失败：${bloggerSkillState.error}`:`${samples.length} 条`);
 const title=document.querySelector("#blogger-skill-samples")?.closest(".panel")?.querySelector(".panel-title span");
 if(title)title.textContent=bloggerSkillPersonFilter?`${bloggerSkillPersonFilter}样本库`:"蒸馏样本库";
 const clip=(v,n=96)=>{const s=String(v||"").replace(/\s+/g," ").trim();return s.length>n?s.slice(0,n)+"…":s};
 const chipList=arr=>(arr||[]).slice(0,5).map(t=>`<em>${t}</em>`).join("");
 root.innerHTML=samples.length?samples.slice(0,12).map(x=>`<article class="blogger-skill-card">
  <div class="blogger-card-top"><span>${x.vertical_domain||"垂直专业"} · ${x.platform||"公开平台"}</span><b>${x.model||"车型待识别"}</b></div>
  <h3>${clip(x.original_topic||x.rag_chunk||"公开内容样本",42)}</h3>
  <dl><dt>专业维度</dt><dd>${(x.professional_dimensions||[]).slice(0,4).join(" / ")||x.vertical_domain||"待识别"}</dd><dt>核心判断</dt><dd>${clip(x.subjective_judgment||x.phenomenon_description||x.rag_chunk,90)}</dd><dt>工程归因</dt><dd>${clip(x.engineering_reasoning||x.objective_evidence||"待补充工程证据",86)}</dd><dt>营销转译</dt><dd>${clip(x.marketing_expression||x.user_translation||x.reusable_judgment_rule,92)}</dd></dl>
  <div>${chipList(x.professional_dimensions)}</div><small>来源已记录｜${x.blogger_name||"公开样本"}｜${(x.ingest_time||"").slice(0,10)}</small>
 </article>`).join(""):`<p class="empty">还没有博主能力样本。请导入公开内容文件，或先记录公开链接后人工补全文本。</p>`;
 const profile=bloggerSkillPersonFilter?allProfiles.find(x=>x.blogger_name===bloggerSkillPersonFilter):allProfiles[0];
 const workbench=allWorkbenches.find(x=>creatorNameKey(x.displayName)===creatorNameKey(bloggerSkillPersonFilter));
 renderBloggerIncubationWorkbench(workbench,profile,clip);
 const profileBox=document.querySelector("#blogger-skill-profile");
 if(profileBox){
  const validationLabel={dual_model_approved:"已通过双模型质检",manual_required:"待人工复核",insufficient_evidence:"证据不足",legacy:"历史画像待复核"}[profile?.validation_status]||"质检状态待确认";
  const evidenceCount=profile?.model_trace?.common_evidence_ids?.length||0;
  profileBox.innerHTML=profile?`<div class="founder-profile-head"><span>MMN模型交叉蒸馏 · ${validationLabel}${evidenceCount?` · 共同证据 ${evidenceCount} 条`:""}</span><b>${profile.blogger_name}｜${profile.vertical_domain} Skill</b></div><dl><dt>能力定位</dt><dd>${profile.professional_background||"公开内容能力蒸馏"}</dd><dt>评价框架</dt><dd>${(profile.evaluation_framework||[]).join(" → ")}</dd><dt>术语体系</dt><dd>${(profile.terminology_system||[]).slice(0,16).join("、")}</dd><dt>判断规则</dt><dd>${(profile.judgment_rules||[]).slice(0,4).map(x=>clip(x,64)).join("；")}</dd><dt>短视频模板</dt><dd>${clip(profile.script_template,160)}</dd><dt>客户报告模板</dt><dd>${clip(profile.report_template,160)}</dd></dl>`:`<p class="empty">导入样本后生成博主能力画像、标签体系和可复用脚本模板。</p>`;
 }
 const strategyBox=document.querySelector("#blogger-skill-strategy-assets"),scriptBox=document.querySelector("#blogger-skill-script-assets");
 const renderAssetList=(assets,type)=>assets?.length?assets.map(asset=>`<article class="distilled-asset-card ${type}">
  <div><span>${type==="strategy"?"策略资产":"脚本资产"}</span><b>${asset.name||"未命名资产"}</b></div>
  <p>${clip(asset.purpose||asset.assetText||asset.template,150)}</p>
  <dl>${asset.scenarios?`<dt>适用场景</dt><dd>${(asset.scenarios||[]).slice(0,4).join(" / ")}</dd>`:""}${asset.outputs?`<dt>输出内容</dt><dd>${(asset.outputs||[]).slice(0,5).join(" / ")}</dd>`:""}${asset.structure?`<dt>结构</dt><dd>${(asset.structure||[]).slice(0,5).join(" → ")}</dd>`:""}${asset.template?`<dt>模板</dt><dd>${clip(asset.template,110)}</dd>`:""}${asset.evidenceSlots?`<dt>证据槽</dt><dd>${(asset.evidenceSlots||[]).slice(0,5).join(" / ")}</dd>`:""}</dl>
  <small>${clip(asset.assetText||"已进入MMN可调用资产库",120)}</small>
 </article>`).join(""):`<p class="empty">当前达人还没有生成${type==="strategy"?"策略资产":"脚本资产"}。导入样本后会自动沉淀。</p>`;
 if(strategyBox)strategyBox.innerHTML=renderAssetList(profile?.strategy_assets||profile?.strategyAssets||[],"strategy");
 if(scriptBox)scriptBox.innerHTML=renderAssetList(profile?.script_assets||profile?.scriptAssets||[],"script");
 const rag=document.querySelector("#blogger-skill-rag-list");
 if(rag){
  const chunks=(bloggerSkillState.knowledgeItems||[]).filter(x=>!bloggerSkillPersonFilter||[x.title,x.body,x.keywords,x.metadata?.author,x.metadata?.source_account_name,x.metadata?.entity].join(" ").includes(bloggerSkillPersonFilter));
  rag.innerHTML=chunks.length?chunks.slice(0,10).map(x=>`<div class="skill-rag-card"><span>${x.metadata?.entity||x.metadata?.domain||"垂直专业样本"}</span><b>${x.title}</b><p>${clip(x.body,180)}</p><small>已进入MMN RAG｜来源与导入时间保存在后台</small></div>`).join(""):`<p class="empty">暂无可进入RAG的专业内容片段。</p>`;
 }
}
function bloggerIncubationStatusLabel(value){return value==="incubation_ready"?"已审核，可进入账号孵化":value==="evidence_ready"?"证据已入库，档案待审核":"等待账号采集与证据补全"}
function bloggerPlatformMetric(profile,key){const item=profile?.[key];return item&&item.availability==="available"&&item.value!=null?Number(item.value).toLocaleString():"未返回"}
function renderBloggerIncubationWorkbench(workbench,profile,clip){
 const root=document.querySelector("#blogger-incubation-workbench"),status=document.querySelector("#blogger-incubation-status");if(!root)return;
 const importPanel=bloggerImportProgressMarkup(bloggerSkillState.importJob);
 if(!workbench){
  if(status)status.textContent=profile?"能力 Skill 已存在，等待关联平台档案":"等待选择孵化对象";
  root.innerHTML=importPanel+(profile?`<div class="blogger-incubation-empty"><b>${escapeHtml(profile.blogger_name)}的能力蒸馏结果已安全保留</b><p>公开导出数据作为主证据；如仍缺少平台档案，可按需补充账号字段和异步任务状态，且不会改写现有样本。</p></div>`:`<p class="empty">选择博主后加载平台档案与孵化准备状态。</p>`);
  return;
 }
 const platformProfile=workbench.platformProfile||{},dna=workbench.dna||{},incubation=workbench.incubation||{},task=workbench.latestTask||{};
 const taskProgress=Math.max(0,Math.min(100,Number(task.progress)||0)),taskFailed=["failed","degraded"].includes(task.status),taskComplete=task.status==="completed";
 const statusText=taskFailed?"账号补充采集失败（不影响主证据）":task.id&&!taskComplete?`账号补充采集 · ${creatorTaskStageLabel(task.stage)} ${taskProgress}%`:bloggerIncubationStatusLabel(workbench.lifecycleStatus);if(status)status.textContent=statusText;
 const steps=[
  ["账号档案",Boolean(workbench.creatorId),workbench.identityStatus==="needs_review"?"待身份复核":"已建立"],
  ["代表作证据",workbench.assetCount>0,`${workbench.assetCount||0} 条作品`],
  ["能力蒸馏",workbench.sampleCount>0,`${workbench.sampleCount||0} 条拆解`],
  ["账号孵化",workbench.lifecycleStatus==="incubation_ready",workbench.lifecycleStatus==="incubation_ready"?"可执行":"待人工审核"],
 ];
 const list=(items,empty)=>(items||[]).length?`<ul>${items.map(item=>`<li>${escapeHtml(item)}</li>`).join("")}</ul>`:`<p class="empty">${empty}</p>`;
 const taskError=publicMmnText(task.error_message||task.degraded_reason||""),taskCopy=task.id?clip(`${creatorTaskStageLabel(task.stage)} · ${taskProgress}%${taskError?` · ${taskError}`:""}`,60):"暂无关联任务记录";
 const taskPanel=task.id?`<section class="blogger-task-progress ${taskFailed?"failed":taskComplete?"completed":"running"}" aria-live="polite">
  <div><span>账号补充采集任务</span><b>${escapeHtml(workbench.displayName)} · ${escapeHtml(creatorTaskStageLabel(task.stage))}</b><small>任务 ID：${escapeHtml(task.id)}</small></div>
  <div class="blogger-task-progress-meter"><progress max="100" value="${taskProgress}" aria-label="${escapeAttr(workbench.displayName)}蒸馏进度"></progress><strong>${taskProgress}%</strong></div>
  ${taskError?`<p>${escapeHtml(taskError)}</p>`:""}
  ${taskFailed?`<button type="button" class="secondary" data-blogger-task-retry="${escapeAttr(task.id)}" data-blogger-name="${escapeAttr(workbench.displayName)}">重试补充采集</button>`:""}
 </section>`:"";
 root.innerHTML=`${importPanel}<div class="blogger-incubation-head"><div><span>${assetPlatformName(workbench.platform)}平台档案</span><h3>${escapeHtml(workbench.displayName)}</h3><p>${escapeHtml(platformProfile.signature||dna.summary||"等待补充账号说明")}</p></div><b class="blogger-readiness ${workbench.lifecycleStatus}">${statusText}</b></div>
 ${taskPanel}
 <div class="blogger-incubation-steps">${steps.map(([name,done,note])=>`<div class="${done?"done":"pending"}"><i></i><b>${name}</b><small>${escapeHtml(note)}</small></div>`).join("")}</div>
 <div class="blogger-profile-metrics"><div><span>粉丝</span><b>${bloggerPlatformMetric(platformProfile,"followers")}</b></div><div><span>公开作品</span><b>${bloggerPlatformMetric(platformProfile,"postCount")}</b></div><div><span>获赞与收藏</span><b>${bloggerPlatformMetric(platformProfile,"likesAndCollects")}</b></div><div><span>最新任务</span><b>${escapeHtml(taskCopy)}</b></div></div>
 <div class="blogger-incubation-grid">
  <section><span>CONTENT DNA</span><h4>能力证据与账号定位</h4><p>${escapeHtml(clip(incubation.positioning||dna.summary,220))}</p><div class="blogger-pillars">${(incubation.contentPillars||[]).map(item=>`<em>${escapeHtml(item)}</em>`).join("")}</div><small>${dna.contentValidation?.status==="aligned"?"双模型共同证据质检通过；":"模型质检未通过，禁止发布；"}${dna.generationMode?` 当前草稿：${escapeHtml(dna.generationMode)}；`:""}未经人工确认的 DNA 不作为最终孵化结论。</small></section>
  <section><span>30-DAY INCUBATION</span><h4>首月账号孵化节奏</h4>${list(incubation.phases,"完成内容 DNA 审核后生成首月孵化节奏。")}</section>
  <section><span>TOPIC BENCHMARK</span><h4>首批选题参考</h4>${list(incubation.benchmarkTopics,"代表作证据不足，暂不生成选题。")}</section>
  <section><span>PRODUCTION ASSETS</span><h4>可调用策略与脚本资产</h4>${list([...(incubation.strategyAssets||[]),...(incubation.scriptAssets||[])],"完成样本蒸馏后生成 brief 与脚本资产。")}</section>
 </div><p class="blogger-incubation-boundary">${escapeHtml(incubation.boundary||"只迁移方法论，不复制原文或个人身份。")}</p>`;
}
async function pollBloggerCreatorTask(taskId,expectedName){
 const token=++bloggerTaskPollToken,deadline=Date.now()+20*60*1000;
 while(token===bloggerTaskPollToken&&Date.now()<deadline){
  const data=await api(`/api/creator-distillation/tasks/${encodeURIComponent(taskId)}`),task=data.task;
  if(expectedName)bloggerSkillPersonFilter=expectedName;
  await loadBloggerSkill();
  if(!task)throw new Error("蒸馏任务状态不可用");
  if(["completed","failed","degraded","paused"].includes(task.status)){
   toast(task.status==="completed"?`${expectedName||"新达人"}蒸馏完成`:`${expectedName||"新达人"}蒸馏${task.status==="paused"?"已暂停":"失败"}：${task.error_message||task.degraded_reason||"请查看任务详情"}`);
   return task;
  }
  await new Promise(resolve=>setTimeout(resolve,900));
 }
 if(token===bloggerTaskPollToken)throw new Error("蒸馏任务超过20分钟，请检查任务状态后重试");
}
async function retryBloggerCreatorTask(button){
 const taskId=button.dataset.bloggerTaskRetry,expectedName=button.dataset.bloggerName||"新达人";
 button.disabled=true;button.textContent="正在重新排队…";
 try{
  const data=await api(`/api/creator-distillation/tasks/${encodeURIComponent(taskId)}/retry`,{method:"POST",body:"{}"});
  bloggerSkillPersonFilter=expectedName;await loadBloggerSkill();toast(`${expectedName}已重新进入蒸馏队列`);
  pollBloggerCreatorTask(data.task?.id||taskId,expectedName).catch(err=>toast(`任务跟踪失败：${err.message}`));
 }catch(err){toast(`重新采集失败：${err.message}`);button.disabled=false;button.textContent="修正后重试"}
}
async function createBloggerCreatorTask(e){
 e.preventDefault();const form=e.currentTarget,f=new FormData(form),url=f.get("creatorUrl"),expectedCreatorName=f.get("expectedCreatorName");
 try{
  await api(`/api/creator-distillation/preflight?url=${encodeURIComponent(url)}`);
  const data=await api("/api/creator-distillation/tasks",{method:"POST",body:JSON.stringify({creatorUrl:url,expectedCreatorName,range:"180",sampleCount:50})}),task=data.task;
  if(!task?.id)throw new Error("任务未成功创建");
  bloggerSkillPersonFilter=expectedCreatorName;form.reset();await Promise.all([loadBloggerSkill(),loadCreatorAssets()]);toast(`${expectedCreatorName}已进入蒸馏队列，正在显示实时进度`);
  pollBloggerCreatorTask(task.id,expectedCreatorName).catch(err=>toast(`任务跟踪失败：${err.message}`));
 }catch(err){toast(`账号导入失败：${err.message}`)}
}
async function importBloggerSkillUrl(){
 const input=document.querySelector("#blogger-skill-url"),url=input?.value.trim();
 if(!url){toast("请先粘贴公开内容链接");return}
 try{
  toast("正在记录公开链接…");
  const data=await api("/api/blogger-skill/import-url",{method:"POST",body:JSON.stringify({edition:activeEdition(),source_url:url})});
  bloggerSkillState={...bloggerSkillState,...data};
  mergeDistilledCreatorLibraries(data.creatorLibraries);
  if(input)input.value="";
  renderBloggerSkill();renderCreatorLibrary();renderStrategyKb();
  toast("已记录链接，等待人工补全文本或导入授权文件");
 }catch(err){toast(`链接记录失败：${err.message}`)}
}
async function scanBloggerSkillImports(){
 try{
  toast("正在扫描本地导入目录…");
  const data=await api("/api/blogger-skill/scan-imports",{method:"POST",body:JSON.stringify({edition:activeEdition()})});
  if(!data.job?.id)throw new Error("未取得本地文件处理任务");
  bloggerSkillState={...bloggerSkillState,importJob:data.job};renderBloggerSkill();
  toast(data.remainingFiles?`最新文件已进入队列；另有 ${data.remainingFiles} 个文件需逐个处理`:"最新文件已进入能力卡生成队列");
  await pollBloggerImportJob(data.job.id);
 }catch(err){toast(`扫描失败：${err.message}`)}
}
async function pollBloggerImportJob(jobId){
 const token=++bloggerImportPollToken,deadline=Date.now()+30*60*1000;
 bloggerImportPollingJobId=jobId;
 try{
  while(token===bloggerImportPollToken&&Date.now()<deadline){
   const data=await api(`/api/blogger-skill/import-jobs/${encodeURIComponent(jobId)}`),job=data.job;
   if(!job)throw new Error("导入任务状态不可用");
   bloggerSkillState={...bloggerSkillState,importJob:job};
   renderBloggerSkill();
   if(["completed","failed"].includes(job.status)){
    bloggerImportPollingJobId="";
    if(job.status==="completed"){
     if(job.result?.creatorName)bloggerSkillPersonFilter=job.result.creatorName;
     await loadBloggerSkill();renderStrategyKb();
     toast(`${job.result?.creatorName||"达人"}完整能力卡已生成：${job.importedCount||0} 条样本`);
    }else toast(`能力卡生成未完成：${job.error||"请查看任务详情后重试"}`);
    return job;
   }
   await new Promise(resolve=>setTimeout(resolve,800));
  }
  if(token===bloggerImportPollToken)throw new Error("任务处理超过30分钟，进度已保留，可刷新页面继续查看");
 }finally{
  if(token===bloggerImportPollToken)bloggerImportPollingJobId="";
 }
}
async function retryBloggerImportJob(button){
 const jobId=button.dataset.bloggerImportRetry;
 button.disabled=true;button.textContent="正在重新排队…";
 try{
  const data=await api(`/api/blogger-skill/import-jobs/${encodeURIComponent(jobId)}/retry`,{method:"POST",body:"{}"});
  bloggerSkillState={...bloggerSkillState,importJob:data.job};renderBloggerSkill();
  toast("文件已重新进入处理队列，进度会持续保留");
  await pollBloggerImportJob(data.job?.id||jobId);
 }catch(err){toast(`重新处理失败：${err.message}`);button.disabled=false;button.textContent="重新处理此文件"}
}
async function importBloggerSkillFile(file){
 if(!file)return;
 try{
  const socialAssistant=file.name.includes("社媒助手");
  toast(socialAssistant?"公开主证据已提交，正在建立处理任务…":"补充样本已提交，正在建立处理任务…");
  const res=await fetch(`/api/blogger-skill/import-file?edition=${encodeURIComponent(activeEdition())}&filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});
  const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");
  if(!json.job?.id)throw new Error("未取得导入任务状态");
  bloggerSkillState={...bloggerSkillState,importJob:json.job};
  contentAssetView="bloggerDistill";
  renderBloggerSkill();showPage("videos");
  toast("任务已开始：导入 → 蒸馏 → 分析 → 交付");
  await pollBloggerImportJob(json.job.id);
 }catch(err){toast(`样本导入失败：${err.message}`)}
}
function contentCapabilityQueryString(){
 const params=new URLSearchParams({edition:activeEdition()});
 if(contentCapabilitySearch)params.set("q",contentCapabilitySearch);
 if(contentCapabilitySelectedTags.length)params.set("tags",contentCapabilitySelectedTags.join(","));
 return params.toString();
}
async function loadContentCapabilityKb(){
 try{
  const data=await api(`/api/content-capability-kb?${contentCapabilityQueryString()}`);
  contentCapabilityState={...contentCapabilityState,...data};
  renderContentCapabilityKb();
 }catch(err){
  contentCapabilityState={...contentCapabilityState,error:err.message};
 renderContentCapabilityKb();
 }
}
function creatorScriptStageLabel(stage){return {brief:"理解任务",draft:"生成初稿",review:"交叉复核",final:"成稿优化",delivery:"完成交付"}[stage]||"等待开始"}
function ensureCreatorScriptWorkspace(){
 let dialog=document.querySelector("#creator-script-workspace");if(dialog)return dialog;
 dialog=document.createElement("dialog");dialog.id="creator-script-workspace";dialog.className="creator-script-dialog";
 dialog.innerHTML=`<div class="creator-script-shell">
  <header><div><span>MMN ORIGINAL SCRIPT WORKBENCH</span><h2>达人方法论原创脚本</h2><p>三重能力协同生成：平台成稿、独立复核、自然表达优化。只迁移方法论，不复制达人身份或原文。</p></div><button type="button" class="creator-script-close" aria-label="关闭脚本工作台">×</button></header>
  <div class="creator-script-layout">
   <form id="creator-script-form" class="creator-script-brief">
    <label><span>选择达人</span><select name="creatorAssetId" required></select></label>
    <fieldset><legend>发布平台</legend><div class="creator-platform-choice">
     <label><input type="radio" name="platform" value="douyin" checked><span>抖音</span></label>
     <label><input type="radio" name="platform" value="wechat_channels"><span>视频号</span></label>
     <label><input type="radio" name="platform" value="bilibili"><span>B站</span></label>
     <label><input type="radio" name="platform" value="xiaohongshu"><span>小红书</span></label>
    </div></fieldset>
    <div class="creator-script-pair"><label><span>品牌</span><input name="brand" required placeholder="例如：上汽奥迪"></label><label><span>车型</span><input name="model" required placeholder="例如：奥迪E7X"></label></div>
    <label><span>标题 / 主题 <small>可留空由MMN生成</small></span><input name="title" placeholder="例如：家庭用户该不该选这台车"></label>
    <label><span>传播重点</span><textarea name="focus" required rows="4" placeholder="写清希望用户记住的核心判断、使用场景和不能越过的表达边界"></textarea></label>
    <button type="submit" class="primary creator-script-generate">MMN自动生成</button>
   </form>
   <section class="creator-script-delivery" aria-live="polite"><div id="creator-script-status"></div><div id="creator-script-output"></div></section>
  </div>
 </div>`;
 document.body.appendChild(dialog);
 dialog.querySelector(".creator-script-close").onclick=()=>{creatorScriptPollToken++;dialog.close()};
 dialog.addEventListener("cancel",()=>{creatorScriptPollToken++});
 dialog.querySelector("#creator-script-form").onsubmit=submitCreatorScriptJob;
 dialog.querySelector('[name="creatorAssetId"]').onchange=async e=>{
  creatorScriptWorkspaceAsset=(contentCapabilityState.creatorAssets||[]).find(x=>x.id===e.target.value)||null;
  creatorScriptCurrentJob=null;renderCreatorScriptWorkspace();
  await restoreLatestCreatorScriptJob(e.target.value);
 };
 return dialog;
}
function creatorScriptJobStatusMarkup(job){
 if(!job)return `<div class="creator-script-empty"><b>填写任务后开始生成</b><p>生成过程中可关闭窗口；进度、成稿和失败原因都会持久化，重新打开后可继续查看。</p></div>`;
 const failed=job.status==="failed",done=job.status==="completed",progress=Math.max(0,Math.min(100,Number(job.progress)||0));
 const phases=[["brief","理解任务"],["draft","生成初稿"],["review","交叉复核"],["final","成稿优化"],["delivery","完成交付"]];
 const order=phases.map(x=>x[0]),current=order.indexOf(job.stage);
 return `<div class="creator-script-progress ${failed?"failed":done?"completed":"running"}">
  <div class="creator-script-progress-head"><div><span>${failed?"生成未完成":done?"可直接交付":"正在生成"}</span><b>${escapeHtml(job.message||creatorScriptStageLabel(job.stage))}</b><small>任务 ${escapeHtml(job.id)} · 第 ${job.revisionNo||1} 版</small></div><strong>${progress}%</strong></div>
  <progress max="100" value="${progress}" aria-label="原创脚本生成进度"></progress>
  <div class="creator-script-phases">${phases.map(([key,label],i)=>`<div class="${failed&&key===job.stage?"failed":i<current||done?"done":i===current?"active":"pending"}"><i>${i<current||done?"✓":i+1}</i><span>${label}</span></div>`).join("")}</div>
  ${job.error?`<p class="creator-script-error"><b>失败原因</b>${escapeHtml(job.error)}</p>`:""}
  ${failed?`<button type="button" class="secondary" data-creator-script-retry="${escapeAttr(job.id)}">修正后重试</button>`:""}
 </div>`;
}
function creatorScriptCopyText(job){
 const r=job?.result||{},visuals=(r.visualSuggestions||[]).map(x=>`${x.timing?`[${x.timing}] `:""}${x.shot}${x.subtitle?`｜字幕：${x.subtitle}`:""}`).join("\n");
 return [`标题：${r.title||""}`,`开头钩子：${r.openingHook||""}`,"完整口播稿：",r.spokenScript||"","字幕重点：",...(r.subtitleHighlights||[]).map(x=>`- ${x}`),"画面建议：",visuals].join("\n");
}
function creatorScriptResultMarkup(job){
 const r=job?.result||{};if(job?.status!=="completed"||!r.spokenScript)return "";
 return `<article class="creator-script-result">
  <div class="creator-script-result-head"><div><span>${escapeHtml(job.platformLabel||"")} · 第 ${job.revisionNo||1} 版</span><h3>${escapeHtml(r.title)}</h3></div><div><button type="button" class="secondary" data-creator-script-copy="all">一键复制</button><button type="button" class="secondary" data-creator-script-export="${escapeAttr(job.id)}">导出Word</button></div></div>
  <section><div><span>开头钩子</span><button type="button" data-creator-script-copy="hook">复制</button></div><p class="creator-script-hook">${escapeHtml(r.openingHook)}</p></section>
  <section><div><span>完整口播稿</span><button type="button" data-creator-script-copy="script">复制</button></div><div class="creator-script-spoken">${escapeHtml(r.spokenScript).replace(/\n/g,"<br>")}</div></section>
  <section><div><span>字幕重点</span></div><ul>${(r.subtitleHighlights||[]).map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul></section>
  <section><div><span>画面建议</span></div><div class="creator-script-shots">${(r.visualSuggestions||[]).map(x=>`<article><b>${escapeHtml(x.timing||"镜头")}</b><p>${escapeHtml(x.shot)}</p>${x.subtitle?`<small>字幕：${escapeHtml(x.subtitle)}</small>`:""}</article>`).join("")}</div></section>
  <form id="creator-script-revision-form" class="creator-script-revision"><label><span>修改要求</span><textarea name="revisionRequest" required rows="3" placeholder="例如：开头更直接，删掉泛泛的品牌介绍，把家庭长途场景讲具体"></textarea></label><button type="submit" class="primary">按要求重新生成</button></form>
  <small class="creator-script-quality">已完成平台适配、事实边界与自然表达复核。</small>
 </article>`;
}
function renderCreatorScriptWorkspace(){
 const dialog=ensureCreatorScriptWorkspace(),assets=contentCapabilityState.creatorAssets||[],select=dialog.querySelector('[name="creatorAssetId"]');
 const selectedId=creatorScriptWorkspaceAsset?.id||select.value||assets[0]?.id||"";
 select.innerHTML=assets.map(x=>`<option value="${escapeAttr(x.id)}">${escapeHtml(x.account_name)} · ${escapeHtml(x.platform||"公开平台")} · ${x.sample_count||0}条样本</option>`).join("");select.value=selectedId;
 creatorScriptWorkspaceAsset=assets.find(x=>x.id===select.value)||creatorScriptWorkspaceAsset;
 dialog.querySelector("#creator-script-status").innerHTML=creatorScriptJobStatusMarkup(creatorScriptCurrentJob);
 dialog.querySelector("#creator-script-output").innerHTML=creatorScriptResultMarkup(creatorScriptCurrentJob);
 const retry=dialog.querySelector("[data-creator-script-retry]");if(retry)retry.onclick=()=>retryCreatorScriptJob(retry);
 dialog.querySelectorAll("[data-creator-script-copy]").forEach(btn=>btn.onclick=()=>copyCreatorScript(btn.dataset.creatorScriptCopy));
 const exportBtn=dialog.querySelector("[data-creator-script-export]");if(exportBtn)exportBtn.onclick=()=>exportCreatorScriptWord(exportBtn.dataset.creatorScriptExport);
 const revision=dialog.querySelector("#creator-script-revision-form");if(revision)revision.onsubmit=submitCreatorScriptRevision;
}
async function openCreatorScriptWorkspace(asset){
 creatorScriptWorkspaceAsset=asset;creatorScriptCurrentJob=null;const dialog=ensureCreatorScriptWorkspace();renderCreatorScriptWorkspace();
 if(typeof dialog.showModal==="function"&&!dialog.open)dialog.showModal();else dialog.setAttribute("open","");
 dialog.querySelector('[name="creatorAssetId"]')?.focus();await restoreLatestCreatorScriptJob(asset.id);
}
async function restoreLatestCreatorScriptJob(assetId){
 try{const data=await api(`/api/content-capability-kb/script-jobs/latest?edition=${encodeURIComponent(activeEdition())}&creatorAssetId=${encodeURIComponent(assetId)}`);creatorScriptCurrentJob=data.job||null;renderCreatorScriptWorkspace();if(data.job&&["queued","running"].includes(data.job.status))pollCreatorScriptJob(data.job.id)}catch(err){toast(`历史脚本读取失败：${err.message}`)}
}
async function submitCreatorScriptJob(e){
 e.preventDefault();const form=e.currentTarget,body=Object.fromEntries(new FormData(form));body.edition=activeEdition();
 const btn=form.querySelector("button[type=submit]");btn.disabled=true;btn.textContent="任务提交中…";
 try{const data=await api("/api/content-capability-kb/script-jobs",{method:"POST",body:JSON.stringify(body)});creatorScriptCurrentJob=data.job;renderCreatorScriptWorkspace();pollCreatorScriptJob(data.job.id)}catch(err){toast(`脚本任务创建失败：${err.message}`);btn.disabled=false;btn.textContent="MMN自动生成"}
}
async function pollCreatorScriptJob(jobId){
 const token=++creatorScriptPollToken,deadline=Date.now()+20*60*1000;
 while(token===creatorScriptPollToken&&Date.now()<deadline){
  try{const data=await api(`/api/content-capability-kb/script-jobs/${encodeURIComponent(jobId)}`);creatorScriptCurrentJob=data.job;renderCreatorScriptWorkspace();if(["completed","failed"].includes(data.job.status)){toast(data.job.status==="completed"?"原创脚本已完成，可直接复制或导出Word":`脚本生成未完成：${data.job.error||"请查看失败原因"}`);return}}
  catch(err){toast(`进度读取失败：${err.message}`);return}
  await new Promise(resolve=>setTimeout(resolve,1000));
 }
}
async function retryCreatorScriptJob(button){
 button.disabled=true;button.textContent="正在重新排队…";
 try{const data=await api(`/api/content-capability-kb/script-jobs/${encodeURIComponent(button.dataset.creatorScriptRetry)}/retry`,{method:"POST",body:"{}"});creatorScriptCurrentJob=data.job;renderCreatorScriptWorkspace();pollCreatorScriptJob(data.job.id)}catch(err){toast(`重试失败：${err.message}`);button.disabled=false;button.textContent="修正后重试"}
}
async function submitCreatorScriptRevision(e){
 e.preventDefault();const requirement=new FormData(e.currentTarget).get("revisionRequest")?.trim();if(!requirement)return;
 const btn=e.currentTarget.querySelector("button");btn.disabled=true;btn.textContent="正在提交修改…";
 try{const data=await api(`/api/content-capability-kb/script-jobs/${encodeURIComponent(creatorScriptCurrentJob.id)}/revise`,{method:"POST",body:JSON.stringify({revisionRequest:requirement})});creatorScriptCurrentJob=data.job;renderCreatorScriptWorkspace();pollCreatorScriptJob(data.job.id)}catch(err){toast(`重新生成失败：${err.message}`);btn.disabled=false;btn.textContent="按要求重新生成"}
}
async function copyCreatorScript(part){
 const r=creatorScriptCurrentJob?.result||{},text=part==="hook"?r.openingHook:part==="script"?r.spokenScript:creatorScriptCopyText(creatorScriptCurrentJob);
 try{await navigator.clipboard.writeText(text||"");toast("脚本内容已复制")}catch(err){toast("复制失败，请检查浏览器剪贴板权限")}
}
async function exportCreatorScriptWord(jobId){
 try{toast("正在生成Word文档…");const res=await fetch(`/api/content-capability-kb/script-jobs/${encodeURIComponent(jobId)}/export.docx`,{headers:authHeaders()});if(!res.ok){const data=await res.json().catch(()=>({}));throw new Error(data.error||"Word导出失败")};const blob=await res.blob(),a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`${creatorScriptCurrentJob?.creatorName||"达人"}-${creatorScriptCurrentJob?.result?.title||"MMN原创脚本"}.docx`;a.click();URL.revokeObjectURL(a.href);toast("Word文档已导出")}catch(err){toast(`Word导出失败：${err.message}`)}
}
function renderContentCapabilityKb(){
 const root=document.querySelector("#content-capability-list");if(!root)return;
 const evidenceRoot=document.querySelector("#content-capability-evidence");
 const stats=contentCapabilityState.stats||{},set=(sel,text)=>{const el=document.querySelector(sel);if(el)el.textContent=text};
 set("#content-cap-source-count",(stats.sources||0).toLocaleString());
 set("#content-cap-chunk-count",(stats.chunks||0).toLocaleString());
 set("#content-cap-match-count",(stats.matched||0).toLocaleString());
 set("#content-cap-tag-count",(stats.tagTypes||0).toLocaleString());
 set("#content-capability-status",contentCapabilityState.error?`加载失败：${contentCapabilityState.error}`:`已匹配 ${(stats.matched||0).toLocaleString()} 条能力片段`);
 const search=document.querySelector("#content-capability-search");if(search&&search.value!==contentCapabilitySearch)search.value=contentCapabilitySearch;
 const tagBox=document.querySelector("#content-capability-tags");
 const tagOptions=contentCapabilityState.tagOptions||{};
 if(tagBox){
  const groups=["技术标签","场景标签","表达风格标签","脚本结构标签","专业领域标签","适用任务标签","车型标签","品牌标签"];
  tagBox.innerHTML=groups.map(group=>{
   const values=(tagOptions[group]||[]).slice(0,18);
   if(!values.length)return "";
   return `<section><b>${group}</b><div>${values.map(tag=>`<button type="button" class="${contentCapabilitySelectedTags.includes(tag)?"active":""}" data-content-cap-tag="${escapeAttr(tag)}">${tag}</button>`).join("")}</div></section>`;
  }).join("")||`<p class="empty">导入样本后会形成平台、账号、车型、技术、场景、脚本结构、表达风格等标签。</p>`;
 tagBox.querySelectorAll("[data-content-cap-tag]").forEach(btn=>btn.onclick=()=>toggleContentCapabilityTag(btn.dataset.contentCapTag));
 }
 const clip=(v,n=150)=>{const s=String(v||"").replace(/\s+/g," ").trim();return s.length>n?s.slice(0,n)+"…":s};
 const dnaText=(asset,action)=>{
  const name=asset.account_name||"该达人",domain=(asset.content_motifs||[])[0]||"汽车垂直内容",style=asset.language_style||"专业表达";
  const formulas={
   script:`按${name}风格生成新脚本：${asset.script_template?.opening||"场景问题开场"}；${asset.script_template?.body||"专业拆解"}；${asset.script_template?.ending||"结尾给出适合谁和验证方式"}。`,
   incubate:`用${name}作为benchmark孵化新账号：${(asset.account_incubation_advice||[]).join(" / ")||`围绕${domain}建立固定栏目和独立账号人格。`}`,
   match:`按客户课题检索适配达人风格：${name}适合${(asset.fit_tasks||[]).slice(0,4).join("、")}；brief要求：${asset.client_brief_template?.deliverable||"输出选题方向、证据要求和边界表达"}。`
  };
  return formulas[action]||"MMN已生成达人能力调用建议。";
 };
 const assets=contentCapabilityState.creatorAssets||[];
 root.innerHTML=assets.length?assets.slice(0,18).map(asset=>`<article class="creator-dna-card">
  <div class="creator-dna-head"><div><span>${asset.platform||"公开平台"} · ${asset.sample_count||0} 条样本</span><h3>${asset.account_name||"待确认账号"}</h3></div><b>${asset.confidence||"待评估"}</b></div>
  <p class="dna-positioning">${clip(asset.account_positioning,150)}</p>
  <div class="dna-fields">
    <section><span>账号定位</span><p>${clip(asset.account_positioning,130)}</p></section>
    <section><span>内容母题</span><p>${(asset.content_motifs||[]).slice(0,6).join(" / ")||"汽车产品认知"}</p></section>
    <section><span>选题公式</span><p>${clip(asset.topic_formula,150)}</p></section>
    <section><span>脚本模板</span><p>${clip([asset.script_template?.opening,asset.script_template?.body,asset.script_template?.ending].filter(Boolean).join(" / ")||asset.script_structure,160)}</p></section>
    <section><span>语言规则</span><p>${(asset.language_rules||[asset.language_style||"专业表达"]).slice(0,4).join(" / ")}</p></section>
    <section><span>可迁移边界</span><p>${clip(asset.transfer_boundary,120)}</p></section>
    <section><span>适配任务</span><p>${(asset.fit_tasks||[]).slice(0,6).join(" / ")}</p></section>
    <section><span>30天选题库</span><p>${(asset.topic_calendar_30d||[]).slice(0,3).map(x=>`${x.day}.${x.topic}`).join(" / ")}</p></section>
    <section><span>客户brief模板</span><p>${clip(asset.client_brief_template?.deliverable||"输出选题方向、脚本结构、证据要求和风险边界",130)}</p></section>
  </div>
  <div class="dna-actions">
    <button type="button" data-dna-action="script" data-dna-id="${escapeAttr(asset.id)}">调用TA方法论生成原创脚本</button>
    <button type="button" data-dna-action="incubate" data-dna-id="${escapeAttr(asset.id)}">用TA作为benchmark孵化新账号</button>
    <button type="button" data-dna-action="match" data-dna-id="${escapeAttr(asset.id)}">按客户课题检索适配达人风格</button>
  </div>
  <div class="capability-tags">${(asset.tags||[]).slice(0,16).map(tag=>`<em>${tag}</em>`).join("")}</div>
  <small>${asset.asset_status||"已加入MMN达人库资产候选"}｜${asset.rag_status||"已进入MMN RAG"}｜${asset.transfer_boundary||"仅迁移方法论，不复刻原文"}</small>
 </article>`).join(""):`<p class="empty">还没有达人DNA资产包。导入公开数据文件或输入账号后，MMN会自动沉淀账号定位、内容母题、选题公式、脚本结构、语言风格和调用场景。</p>`;
 root.querySelectorAll("[data-dna-action]").forEach(btn=>btn.onclick=()=>{
  const asset=(contentCapabilityState.creatorAssets||[]).find(x=>x.id===btn.dataset.dnaId);
  if(!asset)return;
  if(btn.dataset.dnaAction==="script")openCreatorScriptWorkspace(asset);
  else toast(dnaText(asset,btn.dataset.dnaAction));
 });
 const chunks=contentCapabilityState.chunks||[];
 if(evidenceRoot)evidenceRoot.innerHTML=chunks.length?chunks.slice(0,12).map(x=>`<article class="capability-card">
  <div class="capability-card-head"><span>${x.platform||"公开平台"} · ${x.account_name||"公开账号"}</span><b>${x.knowledge_structure||"观点拆解"}</b></div>
  <h3>${clip(x.title||"内容能力样本",56)}</h3>
  <p>${clip(x.chunk_text,160)}</p>
  <dl><dt>核心选题</dt><dd>${clip(x.content_breakdown?.core_topic,80)}</dd><dt>开头钩子</dt><dd>${clip(x.content_breakdown?.opening_hook,120)}</dd><dt>主观点</dt><dd>${clip(x.content_breakdown?.main_viewpoint,140)}</dd><dt>论证结构</dt><dd>${clip(x.content_breakdown?.argument_structure,120)}</dd><dt>可迁移方法</dt><dd>${clip(x.content_breakdown?.transferable_method,140)}</dd><dt>不可复制风险</dt><dd>${clip(x.content_breakdown?.noncopy_risk,140)}</dd></dl>
  <div class="capability-tags">${(x.flat_tags||[]).slice(0,12).map(tag=>`<em>${tag}</em>`).join("")}</div>
  <small>已进入MMN RAG｜仅迁移方法论，不复刻原文｜${(x.created_at||"").slice(0,10)}</small>
 </article>`).join(""):`<p class="empty">达人DNA资产包生成后，样本片段会作为辅助证据留在这里。</p>`;
}
function toggleContentCapabilityTag(tag){
 if(!tag)return;
 contentCapabilitySelectedTags=contentCapabilitySelectedTags.includes(tag)?contentCapabilitySelectedTags.filter(x=>x!==tag):[...contentCapabilitySelectedTags,tag];
 loadContentCapabilityKb();
}
async function importContentCapabilityFile(file){
 if(!file)return;
 try{
  toast("正在导入内容样本并沉淀能力标签…");
  const res=await fetch(`/api/content-capability-kb/import-file?edition=${encodeURIComponent(activeEdition())}&filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});
  const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");
  contentCapabilityState={...contentCapabilityState,...json};
  contentAssetView="contentCapability";
  renderContentCapabilityKb();renderStrategyKb();showPage("videos");
  toast(`内容能力蒸馏完成：导入 ${json.imported||0} 条样本，生成 ${json.stats?.chunks||0} 条RAG能力片段`);
 }catch(err){toast(`内容能力导入失败：${err.message}`)}
}
async function distillContentCapabilityAccount(){
 const account=document.querySelector("#content-capability-account")?.value.trim();
 const sourceUrl=document.querySelector("#content-capability-url")?.value.trim();
 const platform=document.querySelector("#content-capability-platform")?.value||"all";
 if(!account&&!sourceUrl){toast("请先输入达人/账号名，或粘贴公开主页/作品链接");return}
 const btn=document.querySelector("#content-capability-distill"),old=btn?.textContent;
 const status=document.querySelector("#content-capability-collect-status");
 if(btn){btn.disabled=true;btn.textContent=sourceUrl?"MMN采集中…":"MMN蒸馏中…"}
 if(status)status.textContent=sourceUrl?"MMN正在读取公开可见页面，遇到登录/验证码/风控会自动停止。":"MMN正在检索本地样本与历史蒸馏资产。";
 try{
  toast(sourceUrl?`MMN正在内置采集 ${account||"公开账号"} 的公开内容…`:`MMN正在检索 ${account} 的本地样本…`);
  const endpoint=sourceUrl?"/api/content-capability-kb/collect-public":"/api/content-capability-kb/distill-account";
  const data=await api(endpoint,{method:"POST",body:JSON.stringify({edition:activeEdition(),account,platform,source_url:sourceUrl})});
  contentCapabilitySearch=account||data.collection?.source?.account_name||"";
  contentCapabilityState={...contentCapabilityState,...data};
  contentAssetView="contentCapability";
  renderContentCapabilityKb();renderStrategyKb();showPage("videos");
  if(data.distillStatus==="needs_source"){
   toast(data.message||"未找到本地样本，请先采集或导入该账号内容");
   if(status)status.textContent=data.message||"未找到本地样本。";
  }else if(data.distillStatus==="manual_required"){
   toast(data.message||"公开页面暂不能自动读取，请补全文本或导入授权文件");
   if(status)status.textContent=data.message||"需要人工补全文本。";
  }else{
   const evidence=(data.evidence||[]).map(x=>`${x.source}${x.count?` ${x.count}条`:""}`).join("，");
   toast(`${data.message||"账号能力蒸馏完成"}${evidence?`｜来源：${evidence}`:""}`);
   if(status)status.textContent=`${data.message||"MMN内置采集与蒸馏完成"}${evidence?`｜来源：${evidence}`:""}`;
   const urlInput=document.querySelector("#content-capability-url");if(urlInput)urlInput.value="";
  }
 }catch(err){toast(`账号蒸馏失败：${err.message}`)}
 finally{if(btn){btn.disabled=false;btn.textContent=old}}
}
function modelEvidenceContext(model,label="整体判断"){
 const rowMatches=state.rows.map((r,i)=>({r,i})).filter(x=>x.r[0]===model);
 const scores=rowMatches.reduce((m,x)=>{const s=score(x.r);m.p+=s.positive;m.n+=s.negative;m.samples+=+x.r[8]||0;return m},{p:0,n:0,samples:0});
 const countBy=(idx)=>Object.entries(rowMatches.reduce((m,x)=>{const k=x.r[idx]||"未识别";m[k]=(m[k]||0)+(+x.r[8]||1);return m},{})).map(([key,count])=>({key,count})).sort((a,b)=>b.count-a.count).slice(0,8);
 const vertical=(verticalState.items||[]).filter(x=>x.ownModel===model||x.competitor===model);
 const periods=uniquePeriods(vertical),latestPeriod=periods[periods.length-1]||"";
 const latestVertical=latestPeriod?vertical.filter(x=>x.period===latestPeriod):vertical.slice(-20);
 const judgments=modelJudgmentsFor(model),identity=standardIdentityFor(model),learned=learnings().filter(x=>x.model===model).slice(-8);
 const references=ragSearch({query:[model,label,identity.brand_name,identity.model_family].filter(Boolean).join(" "),rows:rowMatches,limit:6});
 const hasData=!!(rowMatches.length||vertical.length||judgments.length||learned.length||references.length||identity);
 return{
  drillType:"model_learning",
  drillKey:model,
  question:`请基于现有资产为${model}生成可保存为人工学习案例的结论草案`,
  project:{edition:activeEdition(),brand:identity.brand_name||brandForDisplay(model),model,project:state.config.project,selectedLabel:label},
  summary:{samples:rowMatches.length,voiceSamples:Math.round(scores.samples),positiveScore:Math.round(scores.p),negativeScore:Math.round(scores.n),verticalRelations:vertical.length,modelJudgments:judgments.length,ragReferences:references.length,hasData},
  breakdown:{labels:countBy(4),platforms:countBy(2),categories:countBy(3),emotions:countBy(5)},
  modelIdentity:identity,
  verticalLatest:latestVertical.slice(0,12).map(x=>({platform:x.platform,period:x.period,ownModel:x.ownModel,competitor:x.competitor,positiveRank:x.positiveRank,negativeRank:x.negativeRank,share:x.share,source:shortSourceName(x.source)})),
  judgments:judgments.slice(0,8),
  learned,
  references,
  dataGaps:[
   rowMatches.length?"":"缺少声量/认知拆解数据",
   vertical.length?"":"缺少垂媒正反向关系数据",
   judgments.length?"":"缺少车型判断资产",
   references.length?"":"缺少RAG引用材料"
  ].filter(Boolean)
 };
}
function localLearningDraft(ctx){
 const s=ctx.summary||{},gaps=ctx.dataGaps||[],topLabel=ctx.breakdown?.labels?.[0]?.key||ctx.project?.selectedLabel||"整体判断",topPlatform=ctx.breakdown?.platforms?.[0]?.key||"待补充平台";
 const direction=(s.negativeScore||0)>(s.positiveScore||0)?"优先修复负向疑虑":"优先放大正向资产";
 return consultingOutputText({
  conclusion:`${ctx.project.model}当前应围绕“${topLabel}”采取“${direction}”。`,
  findings:[`- 当前策略方向由正向分与负向风险的相对关系决定。[Evidence: E1]`,`- ${topPlatform}是现阶段优先验证平台。[Evidence: E2]`],
  evidence:[`- E1：声量样本 ${s.samples||0} 条、正向分 ${s.positiveScore||0}、负向风险 ${s.negativeScore||0}、正反向关系 ${s.verticalRelations||0} 条、车型判断 ${s.modelJudgments||0} 条。`,`- E2：当前页面识别的优先平台为 ${topPlatform}。${gaps.length?`待补：${gaps.join("、")}。`:"暂无明显结构性缺口，但仍需复核最新数据。"}`],
  implication:"把可验证证据先做成用户能复述的内容，可降低无依据扩散对预算与品牌认知的损耗。",
  actions:[`- P0｜本周｜内容团队：围绕“${topLabel}”制作第三方测试、车主反馈、工程解释和竞品对比。`,`- P1｜首轮发布｜平台团队：在 ${topPlatform} 验证表达效率。`,`- P2｜复盘｜项目负责人：按负面占比、核心标签正向声量和询价/试驾线索决定是否扩大。`]
 });
}
async function generateLearningMmnDraft(button){
 const form=document.querySelector("#learning-form"),box=document.querySelector("#learning-ai-output"),status=document.querySelector("#learning-ai-status");
 if(!form||!box)return;
 const model=form.elements.model.value,label=form.elements.label.value||"整体判断",ctx=modelEvidenceContext(model,label);
 const old=button?.textContent;
 if(button){button.disabled=true;button.textContent="生成中…"}
 if(status)status.textContent=`MMN正在分析 ${model}`;
 box.innerHTML=`<h4>MMN生成中</h4><p>正在汇总声量、正反向、车型身份、模型判断和RAG材料。</p>`;
 try{
  const res=await fetch("/api/ai/fusion-strategy",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify({context:ctx})});
  const data=await res.json();
  const text=data.ok?data.text:localLearningDraft(ctx);
  box.innerHTML=consultingMarkdown(text);
  if(status)status.textContent=data.ok?`已生成｜${ctx.summary.hasData?"基于现有资产":"基于缺口模板"}`:"模型失败，已用本地规则输出";
 }catch(err){
  box.innerHTML=consultingMarkdown(localLearningDraft(ctx));
  if(status)status.textContent=`模型失败，已用本地规则输出`;
 }finally{
  if(button){button.disabled=false;button.textContent=old}
 }
}
function renderLearning(a){
 const form=document.querySelector("#learning-form");if(!form)return;
 const groups=brandModelGroups(learningModelOptions());
 const selectedModel=form.elements.model.value||state.config.model;
 if(!learningBrandOpen||!groups.some(g=>g.brand===learningBrandOpen))learningBrandOpen=brandForDisplay(selectedModel);
 const activeGroup=groups.find(g=>g.brand===learningBrandOpen)||groups[0]||{brand:"",models:[]};
 const activeModels=activeGroup.models;
 const model=activeModels.includes(selectedModel)?selectedModel:(activeModels[0]||selectedModel||state.config.model);
 form.elements.brand.innerHTML=groups.map(g=>`<option value="${escapeAttr(g.brand)}" ${g.brand===learningBrandOpen?"selected":""}>${g.brand}</option>`).join("");
 form.elements.model.innerHTML=activeModels.map(m=>`<option value="${escapeAttr(m)}" ${m===model?"selected":""}>${modelNameUnderBrand(learningBrandOpen,m)}</option>`).join("");
 const modelRows=state.rows.filter(r=>r[0]===model),rowLabels=[...new Set(modelRows.map(r=>r[4]).filter(Boolean))];
 const labels=[...new Set([...rowLabels,...modelJudgmentsFor(model).map(x=>x.dimension).filter(Boolean),...a.labels.slice(0,12).map(x=>x.label),"整体判断"])];
 const current=form.elements.label.value;
 form.elements.label.innerHTML=labels.map(x=>`<option ${x===current?"selected":""}>${x}</option>`).join("");
 const selected=form.elements.label.value||labels[0],allLearnings=learnings();
 const similar=allLearnings.filter(x=>x.model===model||x.label===selected).sort((a,b)=>(b.savedAt||b.saved_at||"").localeCompare(a.savedAt||a.saved_at||"")).slice(0,4);
 const history=allLearnings;
 const ctx=modelEvidenceContext(model,selected),status=document.querySelector("#learning-ai-status");
 if(status)status.textContent=`${ctx.summary.hasData?"可生成":"无直接数据，输出缺口建议"}｜声量 ${ctx.summary.samples}｜正反向 ${ctx.summary.verticalRelations}｜车型判断 ${ctx.summary.modelJudgments}`;
 document.querySelector("#similar-learnings").innerHTML=similar.length?similar.map(x=>`<div class="learn-item"><b>${x.model}｜${x.label}</b><p>${x.conclusion}</p><small>${x.recommendation}</small></div>`).join(""):"<p class='empty'>还没有相似案例。可以先用 MMN 生成草案，再人工修改保存。</p>";
 document.querySelector("#learning-history").innerHTML=history.length?history.slice().reverse().map(x=>`<div class="history-item"><span>${(x.savedAt||x.saved_at||"").slice(0,10)}</span><b>${x.model}｜${x.label}</b><p>${x.conclusion}</p><small>${x.recommendation}</small></div>`).join(""):`<p class='empty'>暂无学习记录。${session?"当前企业空间知识库为空。":"未登录时记录只保存在本机浏览器；登录客户空间后会保存到服务端企业知识库。"}</p>`;
 form.elements.brand.onchange=()=>{learningBrandOpen=form.elements.brand.value;renderLearning(a)};
 form.elements.model.onchange=()=>renderLearning(a);
 form.elements.label.onchange=()=>renderLearning(a);
 const gen=document.querySelector("#learning-ai-generate");if(gen)gen.onclick=()=>generateLearningMmnDraft(gen);
}
function renderArchitecture(){
 const root=document.querySelector("#architecture-flow");if(!root)return;
 const arch=currentEdition().architecture;
 document.querySelector("#architecture-eyebrow").textContent=arch.eyebrow;
 document.querySelector("#architecture-title").textContent=arch.title;
 document.querySelector("#architecture-version-button").textContent=arch.button;
 document.querySelector("#architecture-mode").textContent=arch.mode;
 document.querySelector("#architecture-headline").textContent=arch.headline;
 document.querySelector("#architecture-desc").textContent=arch.desc;
 document.querySelector("#architecture-status").innerHTML=arch.status.map(x=>`<div><span>${x[0]}</span><b>${x[1]}</b></div>`).join("");
 root.innerHTML=arch.flow.map((x,i)=>`<div class="flow-step"><span>${String(i+1).padStart(2,"0")}</span><b>${x}</b></div>`).join("");
 document.querySelector("#architecture-data-title").textContent=edition==="china"?"国内版数据接入优先级":"出海版数据接入预留";
 document.querySelector("#architecture-data-note").textContent=edition==="china"?"可逐步自动化":"按区域逐步接入";
 document.querySelector("#architecture-data-list").innerHTML=arch.data.map(x=>`<div class="architecture-item"><span>${x[2]}</span><b>${x[0]}</b><p>${x[1]}</p></div>`).join("");
 document.querySelector("#architecture-ai-title").textContent=edition==="china"?"MMN策略生成与学习闭环":"全球模型与多语言策略闭环";
 document.querySelector("#architecture-ai-note").textContent=edition==="china"?"模型隐藏在MMN路由后":"可走海外模型网关或企业网关";
 document.querySelector("#architecture-ai-list").innerHTML=arch.ai.map(x=>`<div class="architecture-item"><span>${x[2]}</span><b>${x[0]}</b><p>${x[1]}</p></div>`).join("");
 document.querySelector("#architecture-roadmap-title").textContent=edition==="china"?"国内版下一步建设顺序":"出海版同步建设顺序";
 document.querySelector("#architecture-roadmap").innerHTML=arch.roadmap.map(x=>`<div class="roadmap-step"><span>${x[0]}</span><b>${x[1]}</b><p>${x[2]}</p></div>`).join("");
}
function renderWorkspace(){
 const el=document.querySelector("#workspace-tree");if(!el)return;
 const h=workspaceState.hierarchy||defaultWorkspaceState().hierarchy,cfg=currentEdition(),k=cfg.knowledge.map((x,i)=>({...x,items:i===1?(workspaceState.knowledge?.[1]?.items||x.items):i===2?learnings().length:x.items})),snapshots=workspaceState.snapshots||[];
 const r=edition==="china"?[
  {provider:cfg.routerTitle,role:cfg.routerRole,status:"当前优先"},
  {provider:"MMN任务路由层",role:"按任务类型分层调度：快速模型处理日常识别与摘要，旗舰模型只进入策略主结论和后台critic。",status:"已启用"},
  {provider:"MMN策略推理链路",role:aiStatus?.deepseek?.configured&&aiStatus?.qwen?.configured?"策略生成先由一个旗舰模型输出初版，另一个旗舰模型后台异步复核逻辑、证据、竞品和风险。":"待补齐底层模型密钥，配置后由MMN自动调用。",status:aiStatus?.deepseek?.configured&&aiStatus?.qwen?.configured?"已启用":"待配置"},
  {provider:"MMN快速交付链路",role:aiStatus?.qwen?.configured?"标签识别、内容摘要、达人风格拆解和客户交付草案优先走flash/plus快速模型。":"待补齐快速模型密钥，配置后由MMN自动调用。",status:aiStatus?.qwen?.configured?"已启用":"待配置"},
  {provider:"本土化RAG / 结构化数据",role:"参数、销量、价格、配置、上市时间等事实类问题先查MMN数据资产和可追溯来源，模型只负责解释。",status:"事实优先"},
  {provider:"客户私有模型 / 专属云",role:"面向集团客户私有化部署，隔离客户数据和项目学习库。",status:"架构预留"},
  {provider:"本土规则引擎",role:"本地评分、拆解、融合评审底线，无模型也可运行。",status:"已启用"}
 ]:[
  {provider:cfg.routerTitle,role:cfg.routerRole,status:"同步开发"},
  {provider:"MMN海外模型网关",role:aiStatus?.openai?.configured?"已接入本地后端；额度可用后参与出海策略生成":"待配置海外模型密钥或客户可控网关",status:aiStatus?.openai?.configured?"已配置":"待配置"},
  {provider:"TikTok / YouTube / Instagram / Reddit",role:"海外社媒、视频、社区和媒体声量数据源预留。",status:"数据源预留"},
  {provider:"多语言RAG / 翻译层",role:"支持英文、东南亚语种、中东/欧洲市场资料的召回和策略归纳。",status:"预留"},
  {provider:aiStatus?.rules?.model||"MMN规则引擎",role:"跨市场基础分类、规则评分和合规检查底线。",status:"已启用"}
 ];
 document.querySelector("#workspace-org").textContent=session?session.org:"未登录";
 document.querySelector("#workspace-scope").textContent=cfg.scopeSuffix;
 document.querySelector("#workspace-version").textContent=state.datasetVersion||"demo";
 document.querySelector("#workspace-snapshots-count").textContent=snapshots.length.toLocaleString();
 document.querySelector("#workspace-updated").textContent=workspaceState.updatedAt?`更新于 ${workspaceState.updatedAt.slice(0,19).replace("T"," ")}`:"等待登录同步";
 el.innerHTML=`<div class="tree-root"><b>${edition==="global"?"Global Market Space":h.group||session?.org||"客户集团"}</b><span>${edition==="global"?"区域管理员可见国家、品牌、车型和出海项目；国家市场可进一步隔离。":"集团管理员可见全部品牌、车型和项目"}</span></div>${edition==="global"?`<div class="tree-brand"><div><b>海外区域</b><span>区域空间 / 国家市场</span></div><div class="tree-model"><b>东南亚 / 欧洲 / 中东</b><small>TikTok、YouTube、Instagram、Reddit 数据源预留</small></div><div class="tree-model"><b>海外上市项目</b><small>跨语言RAG / 本地法规 / 海外KOC素材学习</small></div></div>`:(h.brands||[]).map(b=>`<div class="tree-brand"><div><b>${b.name}</b><span>${b.role||"品牌空间"}</span></div>${(b.models||[]).map(m=>`<div class="tree-model"><b>${m.name}</b><small>${(m.projects||[]).join(" / ")||"待创建项目"}</small></div>`).join("")}</div>`).join("")||"<p class='empty'>登录客户空间后展示集团、品牌、车型和项目层级。</p>"}`;
 document.querySelector("#knowledge-tiers").innerHTML=k.map(x=>`<div class="tier-card"><span>${x.storage}</span><b>${x.tier}</b><p>${x.scope}</p><strong>${(+x.items||0).toLocaleString()} 条</strong></div>`).join("");
 document.querySelector("#model-router").innerHTML=r.map(x=>`<div class="router-row"><span>${x.status}</span><b>${x.provider}</b><p>${x.role}</p></div>`).join("");
 document.querySelector("#snapshot-list").innerHTML=snapshots.length?snapshots.map(x=>`<div class="snapshot-item"><span>${(x.created_at||"").slice(0,19).replace("T"," ")}</span><b>${x.project||"未命名项目"}</b><p>${x.brand||"—"} / ${x.model||"—"} / ${x.data_version||"—"}</p></div>`).join(""):`<p class="empty">${session?"还没有数据库快照。点击“保存项目快照”会把当前项目写入 SQLite。":"当前仍是本机临时模式；进入客户空间后可保存数据库快照。"}</p>`;
}
const mmnEvalTaskLabels={strategy:"整合策略",opportunity_map:"机会地图",social_evidence:"社媒证据",content_strategy:"内容策略",brief:"营销 Brief",vehicle_configuration:"车型配置核验"};
const mmnEvalVerdictLabels={pass:"通过",human_review:"人工复核",fail:"失败",regression:"回归"};
function mmnEvalPercent(value){return value===null||value===undefined?null:Math.round(Number(value)*100)}
async function loadMmnEvalDashboard(){
 mmnEvalState.loading=true;mmnEvalState.error="";renderMmnEval();
 try{mmnEvalState.data=await api("/api/eval/report")}catch(err){mmnEvalState.error=err.message||"MMN Eval 报告加载失败"}finally{mmnEvalState.loading=false;renderMmnEval()}
}
async function runMmnEval(){
 if(mmnEvalState.running)return;
 mmnEvalState.running=true;mmnEvalState.error="";renderMmnEval();
 try{mmnEvalState.data=await api("/api/eval/run",{method:"POST",body:"{}"});toast("MMN Eval 已完成")}catch(err){mmnEvalState.error=err.message||"MMN Eval 运行失败";toast(mmnEvalState.error)}finally{mmnEvalState.running=false;renderMmnEval()}
}
function mmnEvalSourceNotice(payload){return payload?.sourceKind==="seed_fixture"?"当前为种子验证集，只证明评测机制可工作，不代表 MMN 真实业务能力成绩":"当前展示已接入的正式评测报告"}
function mmnEvalCaseReason(item){return[...(item.hardGateMessages||[]),...(item.humanReviewReasons||[])].join("；")||"未触发硬门禁"}
function mmnEvalStatus(item){
 const decision=item.humanDecision?.decision;
 if(decision==="approved")return{key:"approved",label:"人工通过"};
 if(decision==="rejected")return{key:"rejected",label:"人工驳回"};
 return{key:item.verdict,label:mmnEvalVerdictLabels[item.verdict]||item.verdict||"未知"};
}
function renderMmnEval(){
 const root=document.querySelector("#mmn-eval-root"),run=document.querySelector("#mmn-eval-run"),exportButton=document.querySelector("#mmn-eval-export");if(!root)return;
 if(run){run.disabled=mmnEvalState.running;run.textContent=mmnEvalState.running?"评测运行中…":"运行 Eval";run.onclick=runMmnEval}
 if(exportButton){exportButton.disabled=!mmnEvalState.data;exportButton.onclick=()=>{if(!mmnEvalState.data)return;download(`MMN_Eval_${new Date().toISOString().slice(0,10)}.json`,JSON.stringify(mmnEvalState.data.report,null,2),"application/json");toast("Eval 报告已导出")}}
 if(mmnEvalState.loading){root.innerHTML='<div class="mmn-eval-state" aria-busy="true"><b>正在加载 MMN Eval 报告</b><span>读取评测结果与人工复核记录…</span></div>';return}
 if(mmnEvalState.error){root.innerHTML=`<div class="mmn-eval-state error"><b>MMN Eval 报告加载失败</b><span>${escapeHtml(mmnEvalState.error)}</span><button type="button" id="mmn-eval-retry">重新加载</button></div>`;root.querySelector("#mmn-eval-retry").onclick=loadMmnEvalDashboard;return}
 const payload=mmnEvalState.data;if(!payload?.report){root.innerHTML='<div class="mmn-eval-state"><b>当前没有可展示的 Eval 报告</b><span>点击“运行 Eval”生成第一份真实种子验证报告。</span></div>';return}
 const report=payload.report,summary=report.summary||report.candidate?.summary||{},dimensions=summary.dimensionAverages||{},progress=payload.reviewProgress||{total:0,resolved:0,pending:0},cases=payload.cases||[];
 const filtered=mmnEvalState.filter==="all"?cases:cases.filter(item=>item.verdict===mmnEvalState.filter);
 const dimensionRows=[["evidence","证据质量","30%"],["reasoning","推理质量","25%"],["actionability","可执行性","20%"],["fit","任务适配","15%"],["uncertainty","不确定性","10%"]];
 const comparison=payload.comparison;
 root.innerHTML=`<div class="mmn-eval-source-note"><b>${escapeHtml(mmnEvalSourceNotice(payload))}</b><span>Rubric：${escapeHtml(report.rubricVersion||"—")} · Run：${escapeHtml(report.runName||"candidate")}</span></div>
 <div class="mmn-eval-summary"><article class="mmn-eval-verdict ${escapeAttr(report.releaseVerdict||"fail")}"><span>当前发布判断</span><strong>${escapeHtml((report.releaseVerdict||"unknown").toUpperCase())}</strong><small>${summary.fail||0} 个失败 · ${progress.pending} 个待人工复核</small></article><article><span>综合平均分</span><strong>${summary.averageScore??"—"}</strong><small>已观测维度归一化</small></article><article class="pass"><span>通过</span><strong>${summary.pass||0}</strong><small>≥80 且无硬门禁</small></article><article class="review"><span>人工复核</span><strong>${summary.humanReview||0}</strong><small>${progress.resolved} 已处理 / ${progress.pending} 待处理</small></article><article class="fail"><span>失败</span><strong>${summary.fail||0}</strong><small>命中硬门禁或低于阈值</small></article></div>
 <div class="mmn-eval-analysis"><article class="panel"><div class="panel-title"><div><span>RUBRIC DIMENSIONS</span><h2>五维质量表现</h2></div><em>满分 100 · 权重已折算</em></div><div class="mmn-eval-dimensions">${dimensionRows.map(([key,label,weight])=>{const score=mmnEvalPercent(dimensions[key]);return`<div><label><b>${label}</b><small>权重 ${weight}</small></label><span class="mmn-eval-dimension-track"><i style="width:${score??0}%"></i></span><strong>${score??"—"}</strong></div>`}).join("")}</div></article><article class="panel mmn-eval-comparison"><div class="panel-title"><div><span>VERSION COMPARE</span><h2>版本回归</h2></div><em>candidate vs baseline</em></div>${comparison?`<div class="mmn-eval-comparison-ready"><b>${escapeHtml(comparison.releaseVerdict||"—")}</b><span>${(comparison.regressions||[]).length} 个回归 · ${(comparison.fixedCases||[]).length} 个修复</span></div>`:`<div class="mmn-eval-empty-compare"><b>尚无可对比基线</b><span>保存首个稳定版本后，这里再展示真实分数变化、回归案例与修复项。</span></div>`}</article></div>
 ${progress.total?`<div class="mmn-eval-review-banner"><div><b>${progress.pending?`有 ${progress.pending} 个案例需要你做最终判断`:`本轮人工复核已完成`}</b><span>人工结论只覆盖复核队列，不会绕过硬门禁。</span></div>${progress.pending?'<button type="button" id="mmn-eval-review-next">开始人工复核</button>':""}</div>`:""}
 <section class="panel mmn-eval-cases"><div class="mmn-eval-toolbar"><h2>案例明细</h2><div class="mmn-eval-filters" aria-label="MMN Eval结果筛选">${[["all","全部"],["pass","通过"],["human_review","待复核"],["fail","失败"]].map(([key,label])=>`<button type="button" data-eval-filter="${key}" class="${mmnEvalState.filter===key?"active":""}">${label}</button>`).join("")}</div></div><div class="mmn-eval-table-wrap"><table class="mmn-eval-table"><thead><tr><th>案例 / 任务类型</th><th>综合分</th><th>结果</th><th>硬门禁 / 复核原因</th><th>操作</th></tr></thead><tbody>${filtered.map(item=>{const status=mmnEvalStatus(item);return`<tr><td><b>${escapeHtml(item.caseId)}</b><small>${escapeHtml(mmnEvalTaskLabels[item.taskType]||item.taskType)}</small></td><td><strong>${item.score??"—"}</strong></td><td><span class="mmn-eval-status ${escapeAttr(status.key)}">${escapeHtml(status.label)}</span></td><td>${escapeHtml(mmnEvalCaseReason(item))}</td><td><button type="button" data-eval-case="${escapeAttr(item.caseId)}">${item.verdict==="human_review"?"人工判断":"查看详情"}</button></td></tr>`}).join("")||'<tr><td colspan="5" class="empty">当前筛选下没有案例。</td></tr>'}</tbody></table></div></section>`;
 root.querySelectorAll("[data-eval-filter]").forEach(button=>button.onclick=()=>{mmnEvalState.filter=button.dataset.evalFilter;renderMmnEval()});
 root.querySelectorAll("[data-eval-case]").forEach(button=>button.onclick=()=>openMmnEvalReview(button.dataset.evalCase));
 const next=root.querySelector("#mmn-eval-review-next");if(next)next.onclick=()=>{const item=cases.find(x=>x.verdict==="human_review"&&!x.humanDecision);if(item)openMmnEvalReview(item.caseId)};
 renderMmnEvalReviewDialog();
}
function renderMmnEvalReviewDialog(){
 const dialog=document.querySelector("#mmn-eval-review-dialog"),body=document.querySelector("#mmn-eval-review-body"),title=document.querySelector("#mmn-eval-review-title"),note=document.querySelector("#mmn-eval-review-note"),message=document.querySelector("#mmn-eval-review-message"),approve=document.querySelector("#mmn-eval-review-approve"),reject=document.querySelector("#mmn-eval-review-reject");if(!dialog||!body)return;
 const item=(mmnEvalState.data?.cases||[]).find(entry=>entry.caseId===mmnEvalState.activeCaseId);
 if(!item){body.innerHTML='<p class="empty">请选择一个案例查看详情。</p>';return}
 const status=mmnEvalStatus(item),dimensionLabels={evidence:"证据",reasoning:"推理",actionability:"可执行性",fit:"适配",uncertainty:"不确定性"};
 title.textContent=item.caseId;
 body.innerHTML=`<div class="mmn-eval-review-meta"><div><span>综合分</span><b>${item.score??"—"}</b></div><div><span>当前判断</span><b class="${escapeAttr(status.key)}">${escapeHtml(status.label)}</b></div></div><section><h3>任务与问题</h3><p>${escapeHtml(mmnEvalTaskLabels[item.taskType]||item.taskType)} · ${escapeHtml(item.question||"未提供问题文本")}</p></section><section><h3>为什么需要处理</h3><div class="mmn-eval-review-reason">${escapeHtml(mmnEvalCaseReason(item))}</div></section><section><h3>五维评分</h3><div class="mmn-eval-review-dimensions">${Object.entries(item.dimensions||{}).map(([key,value])=>`<span>${escapeHtml(dimensionLabels[key]||key)}<b>${value===null?"缺失":mmnEvalPercent(value)}</b></span>`).join("")}</div></section>`;
 note.value=item.humanDecision?.note||"";
 message.textContent=item.humanDecision?`已由 ${item.humanDecision.reviewer||"人工"} 于 ${(item.humanDecision.decidedAt||"").slice(0,19).replace("T"," ")} 提交，可重新判断。`:"";
 const reviewable=item.verdict==="human_review";approve.hidden=!reviewable;reject.hidden=!reviewable;
 approve.onclick=()=>saveMmnEvalReview("approved");reject.onclick=()=>saveMmnEvalReview("rejected");
}
function openMmnEvalReview(caseId){
 const dialog=document.querySelector("#mmn-eval-review-dialog");if(!dialog)return;
 mmnEvalState.activeCaseId=caseId;renderMmnEvalReviewDialog();
 if(!dialog.open)dialog.showModal();
}
async function saveMmnEvalReview(decision){
 const note=document.querySelector("#mmn-eval-review-note"),message=document.querySelector("#mmn-eval-review-message"),approve=document.querySelector("#mmn-eval-review-approve"),reject=document.querySelector("#mmn-eval-review-reject"),caseId=mmnEvalState.activeCaseId;
 if(decision==="rejected"&&!note.value.trim()){message.textContent="驳回时请填写人工判断依据。";note.focus();return}
 approve.disabled=true;reject.disabled=true;message.textContent="正在保存人工结论…";
 try{
  await api("/api/eval/human-review",{method:"POST",body:JSON.stringify({caseId,decision,note:note.value.trim()})});
  await loadMmnEvalDashboard();
  document.querySelector("#mmn-eval-review-dialog")?.close();toast(decision==="approved"?"人工通过结论已记录":"人工驳回结论已记录");
 }catch(err){message.textContent=err.message||"人工结论保存失败"}finally{approve.disabled=false;reject.disabled=false}
}
function field(name,label,value,type="text",options=[]){return`<div class="field"><label>${label}</label>${options.length?`<select data-config="${name}">${options.map(o=>`<option ${o===value?"selected":""}>${o}</option>`).join("")}</select>`:`<input data-config="${name}" type="${type}" value="${value}">`}</div>`}
function renderConfig(){
 document.querySelector("#project-form").innerHTML=field("project","项目名称",state.config.project)+field("brand","本品品牌",state.config.brand)+field("model","本品车型",state.config.model,"text",modelOptions())+field("competitor","核心竞品",state.config.competitor)+field("targetIdentity","目标身份",state.config.targetIdentity,"text",Object.keys(identityWeights))+field("budget","营销预算（万元）",state.config.budget,"number");
 document.querySelector("#threshold-form").innerHTML=field("priorityThreshold","行动优先级阈值",state.config.priorityThreshold,"number")+field("riskThreshold","风险预警阈值",state.config.riskThreshold,"number");
 document.querySelectorAll("[data-config]").forEach(el=>{if(el.dataset.config==="model"){el.onchange=()=>selectDashboardVehicleContext(el.value,{source:"project-config"});return}const update=()=>{state.config[el.dataset.config]=el.type==="number"?+el.value:el.value;save()};el.oninput=update;el.onchange=()=>{update();toast("项目参数已保存")}});
 document.querySelector("#platform-weights").innerHTML=Object.entries(state.platforms).map(([k,v])=>`<div class="weight-item"><b>${k}</b><input type="number" step=".05" value="${v}" data-platform="${k}"></div>`).join("");
 document.querySelectorAll("[data-platform]").forEach(el=>el.onchange=()=>{state.platforms[el.dataset.platform]=+el.value;save();render();toast("平台权重已更新")});
}
function showPage(id){
 if(hiddenPages.has(id))id="dashboard";
 const requestedId=id;
 if(id==="founder"){contentAssetView="founderDistill";id="videos"}
 if(id==="bloggerskill"){contentAssetView="bloggerDistill";id="videos";loadBloggerSkill()}
 render();
 document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));
 document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===requestedId));
 const activeNav=document.querySelector(`#nav button[data-page="${CSS.escape(requestedId)}"]`);
 if(activeNav){
  const group=activeNav.closest("details.nav-section");
  if(group)group.open=true;
 }
 document.querySelector("#page-title").textContent=pageNames[requestedId]||pageNames[id]||"内容资产中心";
 if(id==="creatorassets")loadCreatorAssets();
 if(id==="socialtrends"&&!socialTrendState.result&&!socialTrendState.mart){const input=document.querySelector("#social-trend-keyword");if(input&&!input.value)input.value=state.config.model||"";if(!socialTrendState.competitors.length)socialTrendState.competitors=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);socialTrendState.competitors=sanitizeSocialCompetitors(input?.value||state.config.model,socialTrendState.competitors);renderSocialCompetitorPicker();loadLatestSocialTrendSnapshot()}
 if(id==="brandpenetration")loadBrandPenetrationSnapshot();
 if(id==="policyintelligence")window.PolicyIntelligenceModule?.load?.();
 if(id==="eval"&&!mmnEvalState.data&&!mmnEvalState.loading)loadMmnEvalDashboard();
}

function brandPenetrationDisplayItems(result){
 const qa=result?.qa||{},approved=["aligned","disagreement","conditional"].includes(qa?.threeFlagships?.status)||qa?.legacyEvidence?.status==="aligned"||qa?.dualModel?.status==="aligned";
 if(!approved)return[];
 const source=result?.verifiedComparisonItems||[],seen=new Set();
 return source.filter(item=>{const brand=String(item.brandName||item.normalizedModel||item.keyword||"").trim(),key=`${brand}|${item.id||item.sourceUrl||item.platformItemId||""}`;if(seen.has(key))return false;seen.add(key);return true});
}
function brandPenetrationSnapshotKeyword(config){
 const competitors=Array.isArray(config?.competitors)?config.competitors:[],official=String(config?.range||"")==="30"&&config?.ownBrand==="上汽奥迪"&&competitors.length===5&&["奔驰","理想","蔚来","问界","小米"].every(brand=>competitors.includes(brand));
 return official||!config?.ownBrand?"上汽奥迪品牌传播穿透":config.ownBrand;
}
function brandPenetrationProjectModels(config){return [String(config?.ownBrand||"").trim(),...(Array.isArray(config?.competitors)?config.competitors:[])].filter(Boolean)}
function brandPenetrationResultMatchesProject(result,config){
 const expected=brandPenetrationProjectModels(config),actual=(result?.modelComparisons||[]).map(item=>String(item?.model||"").trim()).filter(Boolean);
 return expected.length===actual.length&&expected.every((model,index)=>model===actual[index]);
}
let brandPenetrationRunToken=0;
async function loadBrandPenetrationSnapshot(){
 const frame=document.querySelector("#brand-penetration-frame"),status=document.querySelector("#brand-penetration-snapshot-state"),meta=document.querySelector("#brand-penetration-snapshot-meta");
 if(!frame)return;
 try{
  let config=null;try{config=JSON.parse(localStorage.getItem("mmnBrandPenetrationProject")||"null")}catch(_){}
  if(config)frame.contentWindow?.postMessage({type:"mmn-brand-penetration-project-config",config},"*");
  if(socialEvidenceCapabilities.enabled){
   const active=config||{ownBrand:"上汽奥迪",competitors:["奔驰","理想","蔚来","问界","小米"],range:"30"},payload=socialEvidenceJobPayload({centerType:"brand_penetration",subject:active.ownBrand,competitors:(active.competitors||[]).slice(0,5),timeRange:`${active.range||30}d`});
   const mart=await latestSocialEvidenceMart(payload.projectId,"brand_penetration");if(!mart)throw new Error("当前品牌组合尚未形成公开传播证据集，请点击开始分析");
   if(status)status.textContent="公开传播证据集";if(meta)meta.textContent=`MMN · ${mart.coverage?.contentCount||0}条证据 · ${String(mart.createdAt||"").slice(0,10)}`;
   frame.contentWindow?.postMessage({type:"mmn-brand-penetration-mart",mart},"*");return;
  }
  const keyword=brandPenetrationSnapshotKeyword(config),projectQuery=keyword==="上汽奥迪品牌传播穿透"?"":`${(config?.competitors||[]).map(brand=>`&competitor=${encodeURIComponent(brand)}`).join("")}&timeRange=${encodeURIComponent(`${config?.range||30}d`)}`;
  const data=await api(`/api/social-trends/latest?keyword=${encodeURIComponent(keyword)}&edition=${encodeURIComponent(activeEdition())}&centerType=brand_penetration${projectQuery}`),result=data.result;
  const matchingCount=brandPenetrationDisplayItems(result).length;
  if(!matchingCount)throw new Error("当前品牌组合还没有可用项目快照，请点击开始分析");
  if(keyword!=="上汽奥迪品牌传播穿透"&&!brandPenetrationResultMatchesProject(result,config))throw new Error("已有快照与当前品牌组合不一致，请重新分析");
  if(status)status.textContent="真实数据库快照";
  if(meta)meta.textContent=`MMN 三平台 · ${matchingCount}条品牌匹配内容 · ${String(result.snapshot?.createdAt||"").slice(0,10)}`;
  frame.contentWindow?.postMessage({type:"mmn-brand-penetration-snapshot",result},"*");
 }catch(error){if(status)status.textContent="快照读取失败";if(meta)meta.textContent=error.message||"请重新采集";frame.contentWindow?.postMessage({type:"mmn-brand-penetration-unavailable",message:error.message||"真实快照不可用"},"*")}
}
function updateBrandPenetrationProgress(job){
 const frame=document.querySelector("#brand-penetration-frame"),status=document.querySelector("#brand-penetration-snapshot-state"),meta=document.querySelector("#brand-penetration-snapshot-meta"),progress=Math.max(0,Math.min(100,Number(job?.progress)||0));
 if(status)status.textContent=["completed","ready"].includes(job?.status)?"分析完成":["failed","degraded","manual_required"].includes(job?.status)?"分析未完成":`正在分析 ${progress}%`;
 if(meta)meta.textContent=job?.message||"正在准备数据源";
 frame?.contentWindow?.postMessage({type:"mmn-brand-penetration-progress",progress,status:job?.status||"running",stage:job?.stage||"prepare",message:job?.message||"正在准备数据源"},"*");
}
async function runBrandPenetrationProject(config){
 const frame=document.querySelector("#brand-penetration-frame"),status=document.querySelector("#brand-penetration-snapshot-state"),meta=document.querySelector("#brand-penetration-snapshot-meta");
 const runToken=++brandPenetrationRunToken,deadline=Date.now()+15*60*1000;
 const isOfficial=brandPenetrationSnapshotKeyword(config)==="上汽奥迪品牌传播穿透";
 try{
  updateBrandPenetrationProgress({progress:0,status:"queued",stage:"queued",message:isOfficial&&!socialEvidenceCapabilities.enabled?"正在读取已验证证据并启动三路独立复核":"采集任务正在排队"});
  if(socialEvidenceCapabilities.enabled){
   const payload=socialEvidenceJobPayload({centerType:"brand_penetration",subject:config.ownBrand,competitors:(config.competitors||[]).slice(0,5),timeRange:`${config.range||30}d`});
   const preview=await api("/api/social-evidence/query-plans/preview",{method:"POST",body:JSON.stringify(payload)});if(!preview.plan)throw new Error("品牌传播查询计划未形成");
   const started=await api("/api/social-evidence/jobs",{method:"POST",body:JSON.stringify(payload)}),created=started.job;if(!created?.jobId)throw new Error("证据任务未成功创建");
   const finished=await waitForSocialEvidenceJob(created.jobId,()=>runToken===brandPenetrationRunToken,updateBrandPenetrationProgress);if(runToken!==brandPenetrationRunToken)return;
   if(finished.status!=="ready")throw new Error(finished.message||"本轮品牌传播证据不足");
   const mart=await latestSocialEvidenceMart(payload.projectId,"brand_penetration");if(!mart)throw new Error("任务完成但未形成品牌传播证据集");
   if(status)status.textContent="公开传播证据集";if(meta)meta.textContent=`MMN · ${mart.coverage?.contentCount||0}条证据 · 刚刚更新`;
   frame.contentWindow?.postMessage({type:"mmn-brand-penetration-mart",mart},"*");return;
  }
  const started=await api("/api/social-trends/jobs",{method:"POST",body:JSON.stringify({keyword:config.ownBrand,competitors:(config.competitors||[]).slice(0,5),platforms:["douyin","xiaohongshu","weibo"],timeRange:`${config.range||30}d`,edition:activeEdition(),centerType:"brand_penetration",analysisOnly:isOfficial,snapshotKeyword:isOfficial?"上汽奥迪品牌传播穿透":""})});
  let job=started.job;
  if(!job?.jobId)throw new Error("采集任务未成功创建");
  updateBrandPenetrationProgress(job);
  while(!["completed","failed"].includes(job.status)){
   if(Date.now()>=deadline)throw new Error("采集分析超过15分钟，请检查数据源后重试");
   await new Promise(resolve=>setTimeout(resolve,700));
   job=(await api(`/api/social-trends/jobs/${encodeURIComponent(job.jobId)}`)).job;
   if(runToken!==brandPenetrationRunToken)return;
   if(!job)throw new Error("采集任务状态不可用，请重新发起分析");
   updateBrandPenetrationProgress(job);
  }
  if(runToken!==brandPenetrationRunToken)return;
  if(job.status==="failed")throw new Error(job.error||job.message||"采集任务失败");
  const result=job.result;
  if(!brandPenetrationDisplayItems(result).length)throw new Error("本次采集没有返回可用内容");
  if(!brandPenetrationResultMatchesProject(result,config))throw new Error("采集结果与当前品牌组合不一致，已阻止旧结果覆盖");
  if(status)status.textContent="真实数据库快照";
  const thresholdFallback=result.admission?.thresholdFallback?.applied;
  if(meta)meta.textContent=`MMN 三平台 · ${brandPenetrationDisplayItems(result).length}条品牌匹配内容${thresholdFallback?" · 高热门槛无结果，已回退时间窗内有效内容":""} · 刚刚更新`;
  frame.contentWindow?.postMessage({type:"mmn-brand-penetration-snapshot",result},"*");
 }catch(error){if(runToken!==brandPenetrationRunToken)return;if(status)status.textContent="分析失败";if(meta)meta.textContent=error.message||"请稍后重试";frame.contentWindow?.postMessage({type:"mmn-brand-penetration-unavailable",message:error.message||"分析失败"},"*")}
}
document.querySelector("#brand-penetration-frame")?.addEventListener("load",()=>{if(document.querySelector("#brandpenetration")?.classList.contains("active"))loadBrandPenetrationSnapshot()});
window.addEventListener("message",event=>{const frame=document.querySelector("#brand-penetration-frame"),config=event.data?.config;if(event.source!==frame?.contentWindow||!["mmn-brand-penetration-project-save","mmn-brand-penetration-project-request"].includes(event.data?.type)||!config||typeof config!=="object"||Array.isArray(config))return;try{localStorage.setItem("mmnBrandPenetrationProject",JSON.stringify(config))}catch(_){}if(event.data?.type==="mmn-brand-penetration-project-request")runBrandPenetrationProject(config)});

function creatorTaskStageLabel(stage){return({preflight:"链接预检",awaiting_worker:"等待任务 Worker",resolve_identity:"账号身份解析",collect:"数据采集",normalize:"字段标准化与评分",persist:"资产入库",review:"等待人工审核",media:"素材获取",transcribe:"转写",ocr:"OCR",shots:"镜头与视觉",comments:"评论采集",opinion:"车型舆情辅助验证",evidence:"证据结构化",dna:"DNA 生成",paused:"已暂停",retry:"等待重试"})[stage]||stage||"等待处理"}
function creatorAvailabilityLabel(value){return value==="available"?"可用":value==="not_returned"?"接口未返回":value||"未知"}
function creatorEvidenceLabel(type){return({comment:"评论",transcript:"字幕转写",ocr:"画面文字",shot:"镜头",visual_summary:"视觉摘要",visual_structure:"内容结构"})[type]||type||"证据"}
function creatorDegradedMessage(value){const text=publicMmnText(value);if(text.includes("Download multimodal file timed out"))return `${text.split("；媒体处理部分降级")[0]}；部分媒体源下载超时，其他代表作已继续处理`;return text.length>260?`${text.slice(0,260)}…`:text}
function creatorOpinionStatusLabel(value){return value==="aligned"?"双模型共同证据已通过":"待复核，不发布为正式判断"}
function creatorOpinionScopeLabel(value){return value==="platform_candidate"?"达人受众中的平台级候选":value==="content_signal"?"内容级信号":"证据范围未确认"}
function renderCreatorOpinionPanel(opinion,comments,creatorId){
 const completeness=opinion?.completeness||{},signals=opinion?.issueSignals||[],judgments=opinion?.judgments||[],validation=opinion?.modelValidation||{};
 const monitoredModel=state?.config?.model||"未选择重点车型",normalizedModel=String(monitoredModel).toLowerCase().replace(/\s+/g,"");
 const detectedModels=[...new Set(signals.flatMap(item=>item.vehicleEntities||[]))],directMatch=detectedModels.some(name=>{const normalized=String(name).toLowerCase().replace(/\s+/g,"");return normalized.includes(normalizedModel)||normalizedModel.includes(normalized)});
 const signalRows=signals.map(item=>`<div class="creator-opinion-issue"><div><b>${escapeHtml(item.label||item.issueKey)}</b><span>${item.opinionCount||0} 位用户 · ${item.workCount||0} 条作品</span></div><p>${item.dominantStance==="concern"?"主要表现为担忧":item.dominantStance==="question"?"主要表现为疑问":item.dominantStance==="correction"?"存在专业纠偏":"存在正向或混合反馈"}${item.purchaseImpactCount?` · ${item.purchaseImpactCount} 条明确涉及购买决策`:""}</p>${(item.vehicleEntities||[]).length?`<small>关联车型：${item.vehicleEntities.map(escapeHtml).join("、")}</small>`:""}</div>`).join("");
 const judgmentRows=judgments.map(item=>`<div class="creator-opinion-judgment"><span>${escapeHtml(item.label)} · ${Math.round((item.confidence||0)*100)}%</span><b>${escapeHtml(item.conclusion||"共同证据支持该议题方向")}</b><p>购买影响：${escapeHtml(item.purchaseImpact||"未明确")}</p>${item.correction?`<p>专业纠偏：${escapeHtml(item.correction)}</p>`:""}<small>共同证据 ${item.evidenceIds?.length||0} 条</small></div>`).join("");
 const raw=comments.slice(0,30).map(item=>`<div class="creator-evidence-item"><b>评论证据</b><p>${escapeHtml(item.quote_text||"")}</p><small>置信度 ${item.confidence??"—"} · ${escapeHtml(item.provenance?.sourceEndpoint||"来源已记录")}</small></div>`).join("");
 return `<article class="panel creator-opinion-panel"><div class="panel-title"><div><span>VEHICLE OPINION AUXILIARY VALIDATION</span><h2>重点车型舆情辅助验证</h2></div><em>${creatorOpinionStatusLabel(opinion?.status)}</em></div>${opinion?`<div class="creator-monitoring-fit"><b>当前重点车型：${escapeHtml(monitoredModel)}</b><span>${directMatch?"本批评论存在直接车型提及，可作为辅助验证":"本批评论未直接提及，不计入该车型正式监测结论"}</span>${detectedModels.length?`<small>评论识别车型：${detectedModels.map(escapeHtml).join("、")}</small>`:""}</div><div class="creator-opinion-summary"><span>${creatorOpinionScopeLabel(opinion.scope)}</span><h3>${escapeHtml(opinion.summary||"")}</h3><p>有效汽车评论 ${completeness.validAutomotiveCommentCount||0}/${completeness.rawCommentCount||0} · 独立用户 ${completeness.uniqueUserCount||0} · 覆盖作品 ${completeness.worksCovered||0}/${completeness.creatorAssetCount||0}</p></div>${judgmentRows||`<div class="creator-opinion-warning">已形成议题线索，但双模型尚未在共同证据上达成一致，当前不发布为正式判断。</div>`}<div class="creator-opinion-issues">${signalRows||'<p class="empty">尚未识别到可用的车型或汽车部件议题。</p>'}</div><small class="creator-opinion-boundary">评论只用于车型营销监测的辅助验证，不进入博主内容 DNA；单达人样本不能外推为全市场舆情。已完成 ${(validation.completedProviders||[]).length} 路模型验证。</small>`:`<p class="empty">尚未生成评论舆情判断。可直接使用已入库评论生成，不会重新调用外部采集服务。</p>`}<button class="ghost" data-creator-action="opinion" data-id="${creatorId||""}">${opinion?"重新校验判断":"生成舆情辅助判断"}</button>${comments.length?`<details class="creator-raw-evidence"><summary>查看原始评论证据（当前作品 ${comments.length} 条）</summary><div class="creator-evidence-list">${raw}</div>${comments.length>30?`<p class="creator-evidence-limit">仅展示前 30 条；完整评论保存在资产 API。</p>`:""}</details>`:""}</article>`;
}
async function loadCreatorAssets(){
 creatorAssetState.loading=true;creatorAssetState.error="";renderCreatorAssets();
 try{
  const [tasks,creators,methods,library]=await Promise.all([api("/api/creator-distillation/tasks"),api("/api/creator-distillation/creators"),api("/api/creator-distillation/methodologies"),api(`/api/asset-library?edition=${encodeURIComponent(activeEdition())}`)]);
  const merged=new Map((creators.creators||[]).map(x=>[x.id,x]));
  (library.legacyCreators||[]).forEach(x=>{if(x?.id&&!merged.has(x.id))merged.set(x.id,x)});
  creatorAssetState.tasks=tasks.tasks||[];creatorAssetState.creators=[...merged.values()];creatorAssetState.methods=methods.items||[];
 }catch(e){creatorAssetState.error=e.message}finally{creatorAssetState.loading=false;renderCreatorAssets()}
}
function renderCreatorAssets(){
 const box=document.querySelector("#creator-asset-workspace");if(!box)return;
 document.querySelectorAll("[data-creator-asset-tab]").forEach(x=>x.classList.toggle("active",x.dataset.creatorAssetTab===creatorAssetState.tab));
 if(creatorAssetState.loading){box.innerHTML='<article class="panel"><p class="empty">正在读取达人资产库…</p></article>';return}
 if(creatorAssetState.error){box.innerHTML=`<article class="panel"><p class="empty">读取失败：${escapeHtml(creatorAssetState.error)}</p><button class="ghost" data-creator-action="reload">重试</button></article>`;return}
 if(creatorAssetState.tab==="distill"){
  const rows=creatorAssetState.tasks.map(t=>`<div class="creator-task-row"><div><b>${assetPlatformName(t.platform)} · ${escapeHtml(t.creator_url)}</b><span>${creatorTaskStageLabel(t.stage)} · ${t.progress||0}%</span>${t.degraded_reason?`<small class="degraded">降级：${escapeHtml(creatorDegradedMessage(t.degraded_reason))}</small>`:""}${t.error_message?`<small class="failed">失败：${escapeHtml(t.error_message)}</small>`:""}</div><div class="task-progress"><i style="width:${Math.max(0,Math.min(100,t.progress||0))}%"></i></div><div class="task-actions">${!["completed","paused"].includes(t.status)?`<button class="ghost" data-creator-action="pause" data-id="${t.id}">暂停</button>`:""}${["failed","degraded","paused"].includes(t.status)?`<button class="ghost" data-creator-action="retry" data-id="${t.id}">重试</button>`:""}</div></div>`).join("")||'<p class="empty">还没有蒸馏任务。</p>';
  box.innerHTML=`<article class="panel creator-task-form"><form id="creator-distill-form"><div class="field"><label>抖音 / 小红书达人主页链接</label><input name="creatorUrl" type="url" required placeholder="https://www.douyin.com/user/... 或 https://www.xiaohongshu.com/user/profile/..."></div><div class="field"><label>主页显示的达人名称（身份校验）</label><input name="expectedCreatorName" required placeholder="请与平台主页名称完全一致"></div><div class="field"><label>采集范围</label><select name="range"><option value="90">最近 90 天</option><option value="180" selected>最近 180 天</option><option value="all">全量</option></select></div><div class="field"><label>样本数量</label><input name="sampleCount" type="number" min="20" max="100" value="50"></div><button class="primary">预检并发起任务</button><small>任务会先核对主页 ID 与达人名称；任一不一致即停止，不抓作品、不抓评论、不入库。</small></form></article><article class="panel"><div class="panel-title"><div><span>异步任务</span><h2>处理中与历史任务</h2></div><em>本地 Worker / Celery</em></div><div class="creator-task-list">${rows}</div></article>`;
  const form=box.querySelector("#creator-distill-form");if(form)form.onsubmit=createCreatorDistillationTask;
 }else if(creatorAssetState.tab==="profiles"){
  box.innerHTML=`<article class="panel"><div class="panel-title"><div><span>CREATOR DNA</span><h2>达人档案</h2></div><em>版本化人工修正</em></div><div class="creator-profile-grid">${creatorAssetState.creators.map(c=>`<button class="creator-profile-card" data-creator-action="profile" data-id="${c.id}"><span>${assetPlatformName(c.platform)}</span><b>${escapeHtml(c.display_name||"待补全达人")}</b><p>${escapeHtml(c.profile?.summary||"等待内容 DNA 生成")}</p></button>`).join("")||'<p class="empty">完成首个账号蒸馏后，达人档案会在这里持续积累。</p>'}</div></article>`;
 }else if(creatorAssetState.tab==="breakdowns"){
  const selected=creatorAssetState.selectedCreator||{},assets=selected.assets||[],detail=creatorAssetState.selectedAsset,profile=selected.profile?.dna||{};
  const evidence=detail?.evidence||[],mediaEvidence=evidence.filter(x=>x.evidence_type!=="comment"),comments=evidence.filter(x=>x.evidence_type==="comment"),caps=detail?.asset?.capabilities||{};
  const mediaProcessing=detail?.asset?.analysis?.mediaProcessing||{},mediaBusy=creatorAssetState.processingAssetId===detail?.asset?.id;
  const themes=(profile.contentThemes||[]).map(x=>`<span>${escapeHtml(x.name)} · ${x.assetCount}</span>`).join("");
  const contentSummary=`<article class="panel creator-content-distill"><div class="panel-title"><div><span>CREATOR CONTENT DISTILLATION</span><h2>博主内容能力蒸馏</h2></div><em>服务同赛道账号孵化</em></div><h3>${escapeHtml(profile.summary||"选择作品后，可用字幕、OCR、画面与镜头证据提炼赛道和内容方法。")}</h3><div class="creator-theme-row">${themes||'<span>内容主题等待提炼</span>'}</div><small>只使用作品内容证据提炼赛道、选题、叙事结构和表达方式；评论不会写入博主 DNA。</small></article>`;
  const mediaHtml=detail?.asset?`<article class="panel creator-evidence-detail"><div class="panel-title"><div><span>CONTENT DISTILLATION EVIDENCE</span><h2>${escapeHtml(detail.asset.title||"内容蒸馏证据")}</h2></div><div class="task-actions"><em>${assetPlatformName(detail.asset.platform)}</em><button class="primary" data-creator-action="media" data-id="${detail.asset.id}" ${mediaBusy?"disabled":""}>${mediaBusy?"正在获取…":mediaEvidence.length?"重新获取媒体证据":"获取媒体证据"}</button></div></div><div class="asset-capability-row"><span>转写 ${caps.transcript?"可用":"未取得"}</span><span>OCR ${caps.ocr?"可用":"未取得"}</span><span>视觉 ${caps.visual?"可用":"未取得"}</span><span>镜头 ${caps.shots?"可用":"未取得"}</span></div>${mediaProcessing.message?`<p class="creator-media-status ${mediaProcessing.status||""}">${escapeHtml(mediaProcessing.message)}</p>`:""}<details class="creator-raw-evidence" ${mediaEvidence.length?"open":""}><summary>查看本作品的内容蒸馏证据（${mediaEvidence.length} 条）</summary><div class="creator-evidence-list">${mediaEvidence.slice(0,120).map(item=>`<div class="creator-evidence-item"><b>${creatorEvidenceLabel(item.evidence_type)}</b>${item.start_ms!=null?`<small>${Math.round(item.start_ms/100)/10}s${item.end_ms!=null?`–${Math.round(item.end_ms/100)/10}s`:""}</small>`:""}<p>${escapeHtml(item.quote_text||"")}</p><small>置信度 ${item.confidence??"—"} · ${escapeHtml(item.provenance?.processor||"来源已记录")}</small></div>`).join("")||'<p class="empty">点击“获取媒体证据”，系统会单独处理这条作品并返回具体结果。</p>'}</div></details></article>`:"";
  box.innerHTML=`${contentSummary}${mediaHtml}${renderCreatorOpinionPanel(selected.opinionJudgment,comments,selected.creator?.id)}<article class="panel"><div class="panel-title"><div><span>CANONICAL ASSETS</span><h2>选择作品查看两类证据</h2></div><em>内容蒸馏 / 舆情辅助验证严格分区</em></div>${assets.map(a=>`<button class="asset-breakdown-row" data-creator-action="asset" data-id="${a.id}"><b>${escapeHtml(a.title||"未命名作品")}</b><span>${a.asset_type||"video"} · 综合分 ${a.performance_score??"未计算"}</span><small>${a.degraded_reason?`降级：${escapeHtml(a.degraded_reason)}`:"内容证据用于账号孵化；评论用于车型舆情辅助验证"}</small></button>`).join("")||'<p class="empty">请先在达人档案中选择账号，或完成蒸馏任务。</p>'}</article>`;
 }else{
  box.innerHTML=`<article class="panel"><div class="panel-title"><div><span>SOURCED METHODOLOGY</span><h2>内容方法论库</h2></div><em>所有结论保留来源与证据</em></div>${creatorAssetState.methods.map(m=>`<div class="method-card"><span>${m.methodology_type}</span><b>${escapeHtml(m.title)}</b><p>${escapeHtml(JSON.stringify(m.body||{}))}</p><small>来源达人 ${(m.source_creator_ids||[]).length} · 证据 ${(m.evidence_ids||[]).length}</small></div>`).join("")||'<p class="empty">至少 20 条有效样本形成 DNA 后，可复用方法论会在这里聚合。</p>'}</article>`;
 }
}
async function createCreatorDistillationTask(e){
 e.preventDefault();const f=new FormData(e.target);const payload={creatorUrl:f.get("creatorUrl"),expectedCreatorName:f.get("expectedCreatorName"),range:f.get("range"),sampleCount:+f.get("sampleCount")};
 try{await api(`/api/creator-distillation/preflight?url=${encodeURIComponent(payload.creatorUrl)}`);await api("/api/creator-distillation/tasks",{method:"POST",body:JSON.stringify(payload)});toast("达人蒸馏任务已进入后台队列");await loadCreatorAssets()}catch(err){toast(`任务创建失败：${err.message}`)}
}
function toast(text){const t=document.querySelector("#toast");t.textContent=publicMmnText(text);t.classList.add("show");setTimeout(()=>t.classList.remove("show"),1700)}
function pulseFocus(target){
 const el=typeof target==="string"?document.querySelector(target):target;
 if(!el)return;
 el.classList.remove("focus-pulse");
 void el.offsetWidth;
 el.classList.add("focus-pulse");
 setTimeout(()=>el.classList.remove("focus-pulse"),1150);
}
if(location.protocol==="file:"){const warn=document.createElement("div");warn.style.cssText="position:fixed;left:244px;right:0;top:0;z-index:9999;background:#bf4a4a;color:#fff;padding:12px 24px;font-weight:800;box-shadow:0 10px 30px rgba(0,0,0,.18)";warn.textContent="当前是本地 file:// 打开方式，导入文件会失败。请使用 http://127.0.0.1:8765/ 打开客户演示版。";document.body.appendChild(warn)}
document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>showPage(b.dataset.page));
const socialTrendForm=document.querySelector("#social-trend-form");if(socialTrendForm)socialTrendForm.onsubmit=runSocialTrendAnalysis;
bindSocialTrendSegments();
const socialImportButton=document.querySelector("#social-trend-import"),socialImportFile=document.querySelector("#social-trend-import-file");if(socialImportButton&&socialImportFile){socialImportButton.onclick=()=>socialImportFile.click();socialImportFile.onchange=async()=>{const file=socialImportFile.files?.[0];if(file)await importSocialTrendFile(file);socialImportFile.value=""}}
const socialThresholdReset=document.querySelector("#social-threshold-reset");if(socialThresholdReset)socialThresholdReset.onclick=()=>{document.querySelector("#social-threshold-douyin").value=8000;document.querySelector("#social-threshold-xiaohongshu").value=500;document.querySelector("#social-threshold-weibo").value=500};
document.addEventListener("click",async e=>{
 const bloggerImportRetry=e.target.closest("[data-blogger-import-retry]");if(bloggerImportRetry){await retryBloggerImportJob(bloggerImportRetry);return}
 const bloggerRetry=e.target.closest("[data-blogger-task-retry]");if(bloggerRetry){await retryBloggerCreatorTask(bloggerRetry);return}
 const tab=e.target.closest("[data-creator-asset-tab]");if(tab){creatorAssetState.tab=tab.dataset.creatorAssetTab;renderCreatorAssets();return}
 const action=e.target.closest("[data-creator-action]");if(!action)return;
 try{
  if(action.dataset.creatorAction==="reload")return loadCreatorAssets();
  if(action.dataset.creatorAction==="pause"||action.dataset.creatorAction==="retry"){await api(`/api/creator-distillation/tasks/${action.dataset.id}/${action.dataset.creatorAction}`,{method:"POST",body:"{}"});return loadCreatorAssets()}
  if(action.dataset.creatorAction==="opinion"){
   action.disabled=true;action.textContent="双模型校验中…";
   const result=await api(`/api/creator-distillation/creators/${action.dataset.id}/opinion-judgment`,{method:"POST",body:"{}"});
   creatorAssetState.selectedCreator.opinionJudgment=result.opinionJudgment;renderCreatorAssets();toast("车型舆情辅助判断已更新");return
  }
  if(action.dataset.creatorAction==="media"){
   creatorAssetState.processingAssetId=action.dataset.id;renderCreatorAssets();
   try{
    const result=await api(`/api/creator-distillation/assets/${action.dataset.id}/media`,{method:"POST",body:"{}"});
    creatorAssetState.selectedCreator=await api(`/api/creator-distillation/creators/${result.asset.creator_id}`);
    creatorAssetState.selectedAsset={asset:result.asset,evidence:result.evidence||[]};
    toast(result.status==="available"?"媒体证据已取得":result.message||"媒体证据处理完成");
   }finally{creatorAssetState.processingAssetId="";renderCreatorAssets()}
   return
  }
  if(action.dataset.creatorAction==="profile"){creatorAssetState.selectedCreator=await api(`/api/creator-distillation/creators/${action.dataset.id}`);creatorAssetState.selectedAsset=null;creatorAssetState.tab="breakdowns";renderCreatorAssets()}
  if(action.dataset.creatorAction==="asset"){creatorAssetState.selectedAsset=await api(`/api/creator-distillation/assets/${action.dataset.id}`);renderCreatorAssets();toast("已读取结构化证据资产")}
 }catch(err){toast(err.message)}
});
document.querySelectorAll("[data-edition]").forEach(b=>b.onclick=()=>setEdition(b.dataset.edition));
document.querySelectorAll("[data-domestic-mode]").forEach(b=>b.onclick=()=>setDomesticMode(b.dataset.domesticMode));
document.querySelectorAll("[data-page-jump]").forEach(b=>b.onclick=()=>showPage(b.dataset.pageJump));
const appHomeButton=document.querySelector("#app-home-button");if(appHomeButton)appHomeButton.onclick=()=>{showPage("dashboard");requestAnimationFrame(()=>window.scrollTo({top:0,behavior:"smooth"}))};
document.addEventListener("click",e=>{const btn=e.target.closest("[data-file-target]");if(!btn||btn.disabled)return;const input=document.getElementById(btn.dataset.fileTarget);if(input&&!input.disabled)input.click()});
document.querySelector("#data-search").oninput=e=>{dataSearch=e.target.value;renderData()};
document.querySelector("#vertical-search").oninput=e=>{verticalSearch=e.target.value;renderVertical()};
document.querySelector("#video-search").oninput=e=>{videoSearch=e.target.value;renderVideos()};
const founderSearchInput=document.querySelector("#founder-search");if(founderSearchInput)founderSearchInput.oninput=e=>{founderSearch=e.target.value;renderFounderDistill()};
["#founder-brand-filter","#founder-person-filter","#founder-topic-filter"].forEach(sel=>{const el=document.querySelector(sel);if(el)el.onchange=e=>{const key=sel.includes("brand")?"brand":sel.includes("person")?"person":"topic";founderFilters[key]=e.target.value;renderFounderDistill()}});
const founderSeedButton=document.querySelector("#founder-seed");if(founderSeedButton)founderSeedButton.onclick=seedFounderArchive;
const founderRunButton=document.querySelector("#run-founder-distill");if(founderRunButton)founderRunButton.onclick=runFounderWeeklyCrawl;
const founderGenerateButton=document.querySelector("#founder-generate");if(founderGenerateButton)founderGenerateButton.onclick=generateFounderTalk;
const founderSpeaker=document.querySelector("#founder-speaker");if(founderSpeaker)founderSpeaker.onchange=e=>{founderState.selectedPerson=e.target.value;saveFounderState();renderFounderDistill()};
const bloggerSkillUrlButton=document.querySelector("#import-blogger-skill-url");if(bloggerSkillUrlButton)bloggerSkillUrlButton.onclick=importBloggerSkillUrl;
const bloggerSkillScanButton=document.querySelector("#scan-blogger-skill");if(bloggerSkillScanButton)bloggerSkillScanButton.onclick=scanBloggerSkillImports;
const bloggerSkillFile=document.querySelector("#blogger-skill-file");if(bloggerSkillFile)bloggerSkillFile.onchange=async e=>{const file=e.target.files[0];await importBloggerSkillFile(file);e.target.value=""};
const bloggerSkillPersonSelect=document.querySelector("#blogger-skill-person-select");if(bloggerSkillPersonSelect)bloggerSkillPersonSelect.onchange=e=>{bloggerSkillPersonFilter=e.target.value;renderBloggerSkill()};
const bloggerCreatorForm=document.querySelector("#blogger-creator-form");if(bloggerCreatorForm)bloggerCreatorForm.onsubmit=createBloggerCreatorTask;
const contentCapabilityFile=document.querySelector("#content-capability-file");if(contentCapabilityFile)contentCapabilityFile.onchange=async e=>{const file=e.target.files[0];await importContentCapabilityFile(file);e.target.value=""};
const contentCapabilitySearchInput=document.querySelector("#content-capability-search");if(contentCapabilitySearchInput)contentCapabilitySearchInput.oninput=e=>{contentCapabilitySearch=e.target.value.trim();clearTimeout(contentCapabilitySearchInput._t);contentCapabilitySearchInput._t=setTimeout(loadContentCapabilityKb,260)};
const contentCapabilityClear=document.querySelector("#content-capability-clear");if(contentCapabilityClear)contentCapabilityClear.onclick=()=>{contentCapabilitySelectedTags=[];contentCapabilitySearch="";const input=document.querySelector("#content-capability-search");if(input)input.value="";loadContentCapabilityKb()};
const contentCapabilityDistill=document.querySelector("#content-capability-distill");if(contentCapabilityDistill)contentCapabilityDistill.onclick=distillContentCapabilityAccount;
document.querySelectorAll("[data-content-view]").forEach(b=>b.onclick=()=>{contentAssetView=b.dataset.contentView;creatorFilter="all";creatorSearch="";const input=document.querySelector("#creator-search");if(input)input.value="";if(contentAssetView==="bloggerDistill")loadBloggerSkill();if(contentAssetView==="contentCapability")loadContentCapabilityKb();renderVideos();if(contentAssetView==="founderDistill")renderFounderDistill();if(contentAssetView==="bloggerDistill")renderBloggerSkill();if(contentAssetView==="contentCapability")renderContentCapabilityKb()});
window.MmnXhsContentRanking?.bind(allVideoItems);
document.querySelectorAll("[data-creator-filter]").forEach(b=>b.onclick=()=>{creatorFilter=b.dataset.creatorFilter;document.querySelectorAll("[data-creator-filter]").forEach(x=>x.classList.toggle("active",x.dataset.creatorFilter===creatorFilter));renderCreatorLibrary()});
const creatorSearchInput=document.querySelector("#creator-search");if(creatorSearchInput)creatorSearchInput.oninput=e=>{creatorSearch=e.target.value;renderCreatorLibrary()};
document.querySelectorAll("[data-plugin-open]").forEach(b=>b.onclick=()=>openSocialPlugin(b.dataset.pluginOpen));
document.querySelectorAll("[data-plugin-sync]").forEach(b=>b.onclick=()=>syncSocialPluginExport(b.dataset.pluginSync));
const creatorForm=document.querySelector("#creator-form");
if(creatorForm)creatorForm.onsubmit=e=>{
 e.preventDefault();
 const f=e.target,platform=f.elements.platform.value,id=f.elements.id.value;
 const patch={
  name:f.elements.name.value.trim(),
  type:f.elements.type.value,
  city:f.elements.city.value.trim()||"待补充",
  fans:+f.elements.fans.value||0,
  avgViews:+f.elements.avgViews.value||0,
  engagementRate:+f.elements.engagementRate.value||0,
  costLevel:f.elements.costLevel.value.trim()||"待评估",
  profileUrl:f.elements.profileUrl.value.trim(),
  categories:splitCreatorField(f.elements.categories.value),
  strengths:splitCreatorField(f.elements.strengths.value),
  fitStages:splitCreatorField(f.elements.fitStages.value),
  risk:f.elements.risk.value.trim()
 };
 if(updateCreator(platform,id,patch)){document.querySelector("#creator-dialog").close();renderCreatorLibrary();toast("达人画像已保存")}
 else toast("保存失败：未找到达人");
};
const resetDemoButton=document.querySelector("#reset-demo");if(resetDemoButton)resetDemoButton.onclick=()=>{if(confirm(`确认恢复${currentEdition().label}演示数据？当前本地修改将被覆盖。`)){state=defaultStateForEdition();save();render();toast(`已恢复${currentEdition().label}导入数据`)}};
const modelJudgmentForm=document.querySelector("#model-judgment-form");if(modelJudgmentForm)modelJudgmentForm.onsubmit=submitModelJudgment;
const accountButton=document.querySelector("#account-button");if(accountButton)accountButton.onclick=()=>document.querySelector("#login-dialog").showModal();
document.querySelector("#login-submit").onclick=async e=>{e.preventDefault();const f=document.querySelector("#login-form");try{const data=await api("/api/login",{method:"POST",body:JSON.stringify({org:f.elements.org.value,name:f.elements.name.value,email:f.elements.email.value})});saveSession(data.session);document.querySelector("#login-dialog").close();restoreOpportunityContext();await Promise.all([loadServerLearnings(),loadWorkspace()]);toast(`已进入 ${data.session.org}`)}catch(err){toast(`登录失败：${err.message}`)}};
document.querySelector("#trend-dialog-close").onclick=()=>document.querySelector("#trend-dialog").close();
document.querySelector("#emotion-label-dialog-close").onclick=()=>document.querySelector("#emotion-label-dialog").close();
document.querySelector("#data-drill-close").onclick=()=>document.querySelector("#data-drill-dialog").close();
const semanticAnalyzeButton=document.querySelector("#semantic-analyze");
if(semanticAnalyzeButton)semanticAnalyzeButton.onclick=analyzeSemanticText;
const semanticClearButton=document.querySelector("#semantic-clear");
if(semanticClearButton)semanticClearButton.onclick=()=>{
 semanticState={result:null,schema:null};
 const input=document.querySelector("#semantic-input");if(input)input.value="";
 renderSemanticResult();
	 toast("语义识别内容已清空");
	};
const dashboardTopicRun=document.querySelector("#dashboard-topic-run");
if(dashboardTopicRun)dashboardTopicRun.onclick=runDashboardTopicPlanning;
const dashboardTopicStage=document.querySelector("#dashboard-topic-stage");
if(dashboardTopicStage)dashboardTopicStage.onchange=()=>{
 state.config.stage=dashboardTopicStage.value;
 dashboardTopicPlanState={loading:false,result:null,error:""};
 save();
 renderDashboardTopicPlanner();
};
document.querySelector("#sync-project-state").onclick=()=>syncProjectSnapshot(false);
const extendedHeaders=[...headers,"声量类型","关键词/原文"];
const platformFieldOptions=[...new Set([...Object.keys(defaultState.platforms),...Object.keys(defaultGlobalState.platforms)])];
const fieldDefs=[["model","车型","text"],["type","类型","select",["本品","竞品"]],["platform","平台","select",platformFieldOptions],["category","一级赛道","text"],["label","认知标签","text"],["emotion","情绪","select",Object.keys(emotions)],["identity","用户身份","select",Object.keys(identityWeights)],["intent","购买意向","select",Object.keys(intentWeights)],["comments","有效评论","number"],["impact","Impact 1-5","number"],["growth","Growth","number"],["competition","Competition","number"],["trafficType","声量类型","select",["未识别","商业化声量","自然声量"]],["keywords","关键词/原文","text"]];
document.querySelector("#row-fields").innerHTML=fieldDefs.map(([n,l,t,o])=>`<div class="field"><label>${l}</label>${t==="select"?`<select name="${n}">${o.map(x=>`<option>${x}</option>`).join("")}</select>`:`<input name="${n}" type="${t}" ${t==="number"?'value="1" step=".1"':""} required>`}</div>`).join("");
document.querySelector("#add-row").onclick=()=>document.querySelector("#row-dialog").showModal();
document.querySelector("#save-row").onclick=e=>{e.preventDefault();const f=new FormData(document.querySelector("#row-form")),vals=fieldDefs.map(([n,,t])=>t==="number"?+f.get(n):f.get(n));state.rows.push(vals);save();document.querySelector("#row-dialog").close();render();toast("新数据已加入并完成计算")};
function download(name,text,type="text/plain"){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
document.querySelector("#download-template").onclick=()=>download("中国汽车营销引擎_导入模板.csv",extendedHeaders.join(",")+"\n");
const dashboardTemplateButton=document.querySelector("#dashboard-template");if(dashboardTemplateButton)dashboardTemplateButton.onclick=()=>download("中国汽车营销引擎_导入模板.csv",extendedHeaders.join(",")+"\n");
async function importDataFile(file,{merge=false}={}){
 const previousOpportunityContext=opportunityCacheContext().key;
 if(merge&&isSummaryImport())throw new Error("产品评价汇总与原始 CSV 粒度不同，不能直接拼接；请在独立声量数据入口导入，避免覆盖 NSR 口径");
 toast(merge?"正在导入原始 CSV 声量数据…":"正在导入数据…");
 const endpoint=merge?"/api/import-data-file":"/api/import-xlsx";
 const res=await fetch(`${endpoint}?filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});
 const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");
 const dataset=json.dataset||{};
 if(merge){
  const currentRows=Array.isArray(state.rows)?state.rows:[];
  const incomingRows=Array.isArray(dataset.rows)?dataset.rows:[];
  const isDemoState=/演示数据|demo/i.test(`${state.sourceNote||""} ${state.datasetVersion||""}`);
  const baseRows=isDemoState?[]:currentRows;
  state={...state,rows:[...baseRows,...incomingRows],models:[...new Set([...(isDemoState?[]:(state.models||[])),...(dataset.models||[])])],datasetVersion:dataset.datasetVersion||state.datasetVersion,sourceNote:dataset.sourceNote||state.sourceNote,platforms:{...(state.platforms||{}),...(dataset.platforms||{})}};
  state.config={...state.config,...(dataset.config||{})};
  state.productEvaluationSourceModel=state.config.model;state.productEvaluationBoundModel=state.config.model;registerProductEvaluationDataset(state);
  if(!isDemoState&&baseRows.length&&dataset.config?.competitor){
   const comps=new Set(String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean));
   String(dataset.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean).forEach(x=>comps.add(x));
   [...new Set(baseRows.map(r=>r[0]).filter(Boolean))].forEach(x=>{if(x!==state.config.model)comps.add(x)});
   state.config.competitor=[...comps].filter(x=>x!==state.config.model).join(" / ");
  }
  nsrMapSelectedModels=[];nsrMapSelectionInitialized=false;
  ensureModelIdentities(state.models||[]);
  if(previousOpportunityContext!==opportunityCacheContext().key){resetOpportunityContextState();restoreOpportunityContext()}
  save();render();showPage("dashboard");
  toast(`已导入 ${dataset.sourceRowCount||incomingRows.length} 条原始记录，聚合为 ${incomingRows.length} 组，结果已刷新`);
  return;
 }
 state=dataset;
	 state.productEvaluationSourceModel=state.productEvaluationSourceModel||state.config?.model||"";state.productEvaluationBoundModel=state.config?.model||"";
	 registerProductEvaluationDataset(state);
	 syncProductEvaluationDatasetToServer(state);
 // 替换导入必须同步重置工作台上下文，避免旧项目的品牌下拉框覆盖新导入车型。
 dashBrandOpen=brandForDisplay(state.config?.model);
 dashboardPlatformFilter="all";
 summaryNsrPlatform="全网";
 summaryAttributePlatform="全网";
 summaryDashboardModels=[...(state.models||[])];
 nsrMapSelectedModels=[];nsrMapSelectionInitialized=false;
 if(previousOpportunityContext!==opportunityCacheContext().key){resetOpportunityContextState();restoreOpportunityContext()}
 ensureModelIdentities(state.models||[]);save();render();showPage("dashboard");toast(`已导入 ${state.rows.length} 行，结果已刷新`);
}
document.querySelector("#xlsx-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;try{await importDataFile(file,{merge:/\.csv$/i.test(file.name)})}catch(err){toast(`数据导入失败：${err.message}`)}finally{e.target.value=""}};
document.querySelector("#vertical-xlsx-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;toast("正在导入垂媒排名 Excel…");try{const res=await fetch(`/api/import-vertical-xlsx?filename=${encodeURIComponent(file.name)}&edition=${encodeURIComponent(activeEdition())}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");const sourceId=json.dataset.source;verticalState.sources=[...(verticalState.sources||[]).filter(x=>x.source!==sourceId),{source:sourceId,platform:json.dataset.platform,count:json.dataset.count,importedAt:new Date().toISOString(),remembered:json.dataset.remembered}];verticalState.items=[...(verticalState.items||[]).filter(x=>x.source!==sourceId),...json.dataset.items];verticalState.assetSummary=json.dataset.assetSummary||verticalState.assetSummary;if(json.dataset.knowledgeItems?.length)mergeStrategyKnowledge(json.dataset.knowledgeItems);if(!verticalState.selectedModel)verticalState.selectedModel=json.dataset.models?.[0]||"";saveVerticalState();renderVertical();renderStrategyKb();showPage("vertical");const asset=json.dataset.assetSummary;const kCount=json.dataset.knowledgeItems?.length||0;toast(asset?`已导入 ${json.dataset.platform} ${json.dataset.count} 条，生成 ${kCount} 条训练知识，资产库累计 ${asset.modelCount} 个车型`:`已导入 ${json.dataset.platform} ${json.dataset.count} 条正反向排名`)}catch(err){toast(`垂媒数据导入失败：${err.message}`)}finally{e.target.value=""}};
document.querySelector("#clear-vertical-data").onclick=()=>{if(confirm("确认清空当前垂媒看板数据？已沉淀的车型资产库不会删除。")){verticalState={sources:[],items:[],assetSummary:verticalState.assetSummary||null,selectedPlatform:"all",selectedSource:"all",selectedModel:"",selectedCompetitor:"",selectedPeriod:"latest"};verticalSearch="";verticalPeriodPickerOpen=false;document.querySelector("#vertical-search").value="";saveVerticalState();renderVertical();toast("当前看板已清空，车型资产库已保留")}};
document.querySelector("#clear-video-data").onclick=()=>{if(confirm("确认清空全部内容资产？车型预设会保留，已同步的抖音/小红书抓取结果会清空。")){videoState={...normalizeVideoState(videoState),files:emptyAssetFiles(),legacyItems:[]};videoSearch="";resetContentPptPlan();document.querySelector("#video-search").value="";saveVideoState();renderVideos();toast("内容资产已清空")}};
document.querySelector("#csv-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;try{await importDataFile(file,{merge:true})}catch(err){toast(`CSV导入失败：${err.message}`)}finally{e.target.value=""}};
document.querySelector("#learning-form").onsubmit=async e=>{e.preventDefault();const f=e.target,item={edition:activeEdition(),model:f.elements.model.value||state.config.model,label:f.elements.label.value,conclusion:f.elements.conclusion.value.trim(),recommendation:f.elements.recommendation.value.trim(),evidence:f.elements.evidence.value.trim(),platform:f.elements.platform.value.trim(),kpi:f.elements.kpi.value.trim(),stage:f.elements.stage.value,savedAt:new Date().toISOString()};if(!item.conclusion&&!item.recommendation){toast("请先填写结论或建议");return}try{if(session){const data=await api("/api/learnings",{method:"POST",body:JSON.stringify({...item,org_id:session.org_id,user_id:session.user_id})});serverLearnings.unshift({...data.item,savedAt:data.item.saved_at});}else{const items=learnings();items.push(item);saveLearnings(items)}f.elements.conclusion.value="";f.elements.recommendation.value="";f.elements.evidence.value="";f.elements.platform.value="";f.elements.kpi.value="";render();toast(session?"已保存到当前版本企业知识库":"已保存到当前版本本机学习库")}catch(err){toast(`保存失败：${err.message}`)}};
document.querySelector("#clear-learning").onclick=async()=>{if(confirm(session?"确认清空当前企业空间、当前版本的学习记录？":"确认清空本机当前版本学习记录？")){try{if(session){await api(`/api/learnings?org_id=${encodeURIComponent(session.org_id)}&edition=${encodeURIComponent(activeEdition())}`,{method:"DELETE"});serverLearnings=[]}else saveLearnings([]);render();toast("当前版本学习记录已清空")}catch(err){toast(`清空失败：${err.message}`)}}};
document.querySelector("#strategy-kb-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;toast("正在导入RAG材料…");try{const res=await fetch(`/api/import-rag-file?filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");mergeStrategyKnowledge(json.dataset.items||[]);render();showPage("strategykb");toast(`已导入 ${json.dataset.count} 条RAG知识`)}catch(err){toast(`RAG材料导入失败：${err.message}`)}finally{e.target.value=""}};
document.querySelector("#import-rag-seed").onclick=async()=>{toast("正在导入MMN训练包v1…");try{const data=await api("/api/import-rag-seed",{method:"POST",body:"{}"});mergeStrategyKnowledge(data.dataset.items||[]);render();showPage("strategykb");document.querySelector("#rag-query").value="智己LS8 最大传播问题 下一阶段怎么打";renderRagResults();toast(`MMN训练包已导入 ${data.dataset.count} 条知识`)}catch(err){toast(`训练包导入失败：${err.message}`)}};
document.querySelector("#import-strategy-kb").onclick=()=>{const input=document.querySelector("#strategy-kb-input"),text=input.value.trim();if(!text){toast("请先粘贴策略对话，或上传RAG材料");return}const items=summarizeKnowledgeText(text);if(!items.length){toast("暂未提取到可用策略知识，请补充更完整的对话内容");return}mergeStrategyKnowledge(items);input.value="";render();showPage("strategykb");toast(`已归纳 ${items.length} 条策略知识`)};
document.querySelector("#clear-strategy-kb").onclick=()=>{if(confirm("确认清空策略知识库？")){strategyKb=[];saveStrategyKb();renderStrategyKb();render();toast("策略知识库已清空")}};
document.querySelector("#run-rag-search").onclick=()=>{ragResultsExpanded=false;runMmnSmartStrategy("fast")};
document.querySelector("#run-rag-deep-strategy").onclick=()=>{ragResultsExpanded=false;runMmnSmartStrategy("deep")};
["#rag-query","#rag-platform","#rag-emotion","#rag-category","#rag-stage"].forEach(sel=>{const el=document.querySelector(sel);if(el)el.oninput=el.onchange=()=>{ragResultsExpanded=false;renderRagResults()}});
function reportPayload(){
 const a=analysis(),list=a.labels.filter(x=>x.priority>0).slice(0,10),risks=a.labels.filter(x=>x.diagnosis==="优先修复").slice(0,3),assets=a.labels.filter(x=>x.diagnosis==="持续放大").slice(0,3),manual=learnings().filter(x=>x.model===state.config.model);
 const calendar=[
  {week:"第1周",theme:"止血澄清",task:`围绕“${risks[0]?.label||list[0]?.label||"核心风险"}”建立统一口径，发布官方解释、第三方实测和 FAQ。`},
  {week:"第2周",theme:"证据扩散",task:"把高风险问题做成短视频、垂媒横评、B站深度拆解三种证据形态。"},
  {week:"第3周",theme:"场景转化",task:"组织车主/KOC用真实通勤、家庭、长途场景复现产品价值，承接试驾。"},
  {week:"第4周",theme:"资产放大",task:`把“${assets[0]?.label||list[2]?.label||"正向资产"}”包装成可复述卖点，形成话题、内容Brief和品牌传播口径。`}
 ];
 return{title:state.config.project,model:state.config.model,competitor:state.config.competitor,account:session?`${session.org} / ${session.email}`:"本机临时模式",metrics:metricDisplay(a),manual,diagnostics:list.map(x=>({label:x.label,diagnosis:x.diagnosis,negative:isSummaryImport()?"未提供量级":Math.round(x.on).toLocaleString(),gap:(x.gap*100).toFixed(1)+"%",priority:x.priority.toFixed(1)})),knowhow:list.slice(0,6).map(x=>{const k=knowhowFor(x),learned=latestLearning(x.label);return{label:x.label,message:learned?.recommendation||k.message,evidence:learned?.evidence||k.proof,kpi:learned?.kpi||k.kpi}}),strategyKnowledge:strategyKb.slice(-8),calendar};
}
const exportPptxButton=document.querySelector("#export-pptx");if(exportPptxButton)exportPptxButton.onclick=async()=>{try{toast("正在生成 PPT…");const res=await fetch("/api/export-pptx",{method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify(reportPayload())});if(!res.ok){const err=await res.json().catch(()=>({error:"PPT 生成失败"}));throw new Error(err.error)}const blob=await res.blob();const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`${state.config.project}_策略报告.pptx`;a.click();URL.revokeObjectURL(a.href);toast("PPT 已导出")}catch(err){toast(`PPT 导出失败：${err.message}`)}};
const exportGammaButton=document.querySelector("#export-gamma");if(exportGammaButton)exportGammaButton.onclick=()=>{const p=reportPayload();const text=[`# Gamma 提案生成大纲｜${p.title}`,``,`请基于以下内容生成一份中文汽车营销策略汇报 PPT。`,`风格：专业、简洁、有咨询感，适合给汽车品牌营销负责人/管理层汇报。`,`页数建议：8页，16:9。`,``,`## 1. 封面`,`标题：${p.title}`,`副标题：分析对象 ${p.model}｜竞品 ${p.competitor}`,``,`## 2. 核心数据结果`,`- NSR：${p.metrics.nsr}` ,`- IPS：${p.metrics.ips}`,`- 购买意向指数：${p.metrics.intent}`,`- 购买阻力风险：${p.metrics.risk}`,``,`## 3. 认知诊断排序`,...p.diagnostics.slice(0,8).map((x,i)=>`${i+1}. ${x.label}｜${x.diagnosis}｜负向 ${x.negative}｜Gap ${x.gap}｜优先级 ${x.priority}`),``,`## 4. 人工结论与建议`,...(p.manual.length?p.manual.map((x,i)=>`${i+1}. ${x.label}\n- 结论：${x.conclusion||"未填写"}\n- 建议：${x.recommendation||"未填写"}\n- 证据：${x.evidence||"未填写"}\n- 平台：${x.platform||"未填写"}\n- KPI：${x.kpi||"未填写"}`):["尚未填写人工结论，请在页面中补充后再生成正式提案。"]),``,`## 5. 参考 Know-how`,...p.knowhow.map((x,i)=>`${i+1}. ${x.label}：${x.message}；证据链：${x.evidence}；KPI：${x.kpi}`),``,`## 6. 策略知识库补充`,...(p.strategyKnowledge?.length?p.strategyKnowledge.map((x,i)=>`${i+1}. ${x.type}：${x.body}`):["暂无导入的策略知识。"]),``,`## 7. 30天行动节奏`,...p.calendar.map(x=>`- ${x.week}｜${x.theme}：${x.task}`),``,`## 8. 风险与下一步`,`强调：数据结果由系统计算，最终结论和建议以人工填写为准；企业知识库会持续学习人工判断。`,``,`## 9. 结尾页`,`输出：下一步需要确认的策略动作、内容证据、责任分工和复盘指标。`].join("\\n");download(`${p.title}_Gamma大纲.md`,text,"text/markdown");toast("Gamma 大纲已导出")};
const exportReportButton=document.querySelector("#export-report");if(exportReportButton)exportReportButton.onclick=()=>{
 const a=analysis(),list=a.labels.filter(x=>x.priority>0).slice(0,10),sum=list.reduce((s,x)=>s+x.priority,0)||1,risks=a.labels.filter(x=>x.diagnosis==="优先修复").slice(0,3),assets=a.labels.filter(x=>x.diagnosis==="持续放大").slice(0,3);
 const main=list[0],mainKh=main?knowhowFor(main):null;
 const calendar=[
  ["第1周","止血澄清",`围绕“${risks[0]?.label||main?.label||"核心风险"}”建立统一口径，发布官方解释、第三方实测和 FAQ。`],
  ["第2周","证据扩散",`把高风险问题做成短视频、垂媒横评、B站深度拆解三种证据形态。`],
  ["第3周","场景转化",`组织车主/KOC用真实通勤、家庭、长途场景复现产品价值，承接试驾。`],
  ["第4周","资产放大",`把“${assets[0]?.label||list[2]?.label||"正向资产"}”包装成可复述卖点，形成话题、内容Brief和品牌传播口径。`]
 ];
 const manual=learnings().filter(x=>x.model===state.config.model);
 const metrics=metricDisplay(a),report=[`# ${state.config.project}｜营销策略报告`,``,`版本：${currentEdition().label}`,`分析对象：${state.config.model}  ｜ 核心竞品：${state.config.competitor}`,session?`客户空间：${session.org} ｜ 账号：${session.email}`:"客户空间：未登录，本机临时模式",``,`## 数据结果`,`- 口碑健康 NSR：${metrics.nsr}`,`- 目标人群穿透 IPS：${metrics.ips}`,`- 购买意向指数：${metrics.intent}`,`- 购买阻力风险分：${metrics.risk}`,isSummaryImport()?`- 数据边界：${state.importQuality.message}`:"",``,`## 人工结论与建议`,...(manual.length?manual.map((x,i)=>`${i+1}. **${x.label}**\n   - 结论：${x.conclusion||"未填写"}\n   - 建议：${x.recommendation||"未填写"}\n   - 证据：${x.evidence||"未填写"}\n   - 平台：${x.platform||"未填写"}\n   - KPI：${x.kpi||"未填写"}`):["尚未填写人工结论。"]),``,`## 系统诊断参考`,...list.map((x,i)=>{const ac=actionFor(x),learned=latestLearning(x.label);return`${i+1}. **${x.label}｜${x.diagnosis}**：本品负向 ${isSummaryImport()?"源表未提供量级":Math.round(x.on).toLocaleString()}，认知 Gap ${(x.gap*100).toFixed(1)}%；参考证据：${learned?.evidence||ac.evidence}；参考平台：${learned?.platform||ac.platform}；建议预算参考：${money(state.config.budget*x.priority/sum)}。`}),``,`## 参考 Know-how`,...list.slice(0,6).map((x,i)=>{const k=knowhowFor(x),learned=latestLearning(x.label);return`${i+1}. **${x.label}**：${learned?.conclusion||k.why}\n   - 参考打法：${learned?.recommendation||k.message}\n   - 证据链：${learned?.evidence||k.proof}\n   - KPI：${learned?.kpi||k.kpi}`}),``,`## 30天排期参考`,...calendar.map(x=>`- **${x[0]}｜${x[1]}**：${x[2]}`),``,session?`> 数据结果由系统计算；结论和建议以人工填写内容为准；学习案例来自 ${session.org} 企业知识库。`:`> 数据结果由系统计算；结论和建议以人工填写内容为准；当前为本机临时学习模式。`].filter(Boolean).join("\n");
 download(`${state.config.project}_策略报告.md`,report,"text/markdown");toast("策略报告已导出");
};
const strategyReportRun=document.querySelector("#strategy-report-export-run");if(strategyReportRun)strategyReportRun.onclick=()=>runStrategyReportExport(false);
const strategyReportDownload=document.querySelector("#strategy-report-export-download");if(strategyReportDownload)strategyReportDownload.onclick=downloadStrategyReportPackage;
const strategyReportRegenerate=document.querySelector("#strategy-report-export-regenerate");if(strategyReportRegenerate)strategyReportRegenerate.onclick=()=>runStrategyReportExport(true);
function startAppDataLoads(){
 restoreOpportunityContext();
 restoreProductEvaluationCatalogFromServer();
 loadSocialEvidenceCapabilities();
 loadAiStatus();
	 loadServerAssetLibrary();
	 loadSalesMarquee();
	 loadFounderArchives();
	 loadBloggerSkill();
	 loadContentCapabilityKb();
	 loadSocialPluginStatus();
 if(session){loadServerLearnings();loadWorkspace()}else renderWorkspace();
}
function signalAppAuthReady(){
 window.mmnAuthReady=true;
 window.dispatchEvent(new CustomEvent("mmn:auth-ready"));
}
initCloudLoginGate().then(ok=>{
 if(!ok)return;
 reconcileProductEvaluationBinding();
 render();
 startAppDataLoads();
 signalAppAuthReady();
});
