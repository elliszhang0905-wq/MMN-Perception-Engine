const APP_VERSION="beta 1.01";
const emotions={兴奋:[1,0],惊喜:[.9,0],期待:[.75,.1],信任:[1,0],认可:[.85,0],自豪:[.95,0],怀疑:[-.4,.5],焦虑:[-.55,.7],失望:[-.75,.85],愤怒:[-1,1],后悔:[-.95,1],嘲讽:[-.7,.9]};
const identityWeights={目标核心人群:1.35,增量人群:1.2,高影响力车主:1.3,家庭用户:1.15,科技用户:1.15,性能用户:1.1,价格敏感用户:1,未知:.85};
const intentWeights={高意向:1.5,中意向:1.15,低意向:.8,无:.5};
const importedDataset=typeof window!=="undefined"?window.importedDataset20260608:null;
const defaultState={
 datasetVersion:importedDataset?.version||"demo_v1",
 sourceNote:importedDataset?.note||"演示数据",
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
 ]};
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
let edition=loadEdition();
let state=load();
let mapFilter="all",mapLimit=12;
let dataModelFilter="all",dataTrafficFilter="all",dataSearch="";
let dataBrandFilter="all";
let dashBrandOpen="";
let dashboardPlatformFilter="all";
let summaryDashboardModels=[];
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
let bloggerSkillState={stats:{sources:0,samples:0,profiles:0,ragChunks:0},sources:[],samples:[],profiles:[],knowledgeItems:[]},bloggerSkillPersonFilter="";
let contentCapabilityState={stats:{sources:0,chunks:0,matched:0},chunks:[],tagOptions:{},knowledgeItems:[]},contentCapabilitySearch="",contentCapabilitySelectedTags=[];
let selectedKnowledgeCluster="";
let ragResultsExpanded=false;
let dashboardTopicPlanState={loading:false,result:null,error:""};
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
const pageNames={dashboard:"决策驾驶舱",data:"声量数据",cognition:"认知诊断",vertical:"竞品格局",videos:"内容资产",contentstrategy:"MMN策略输出",actions:"行动预算",knowhow:"打法知识库",strategykb:"RAG策略台",learning:"人工结论",architecture:"版本架构",workspace:"空间权限",config:"项目权重"};
function activeEdition(){try{return typeof edition==="string"?edition:loadEdition()}catch{return"china"}}
function defaultStateForEdition(ed=activeEdition()){return structuredClone(ed==="global"?defaultGlobalState:defaultState)}
function storageKey(base,ed=activeEdition()){return `${base}:${ed}`}
function importedModelsFromSourceNote(note){
 const m=String(note||"").match(/识别车型[:：]\s*([^；。]+)/);
 return m?m[1].split(/[、,，/]/).map(x=>x.trim()).filter(Boolean):[];
}
function normalizeLoadedEngineState(saved){
 if(!saved||!Array.isArray(saved.rows))return saved;
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
function load(){try{const ed=activeEdition(),saved=JSON.parse(localStorage.getItem(storageKey("mmnEngineState",ed))||(ed==="china"?localStorage.getItem("mmnChinaState"):"null"));return saved&&Array.isArray(saved.rows)?normalizeLoadedEngineState(saved):defaultStateForEdition(ed)}catch{return defaultStateForEdition()}}
function save(){localStorage.setItem(storageKey("mmnEngineState"),JSON.stringify(state));queueWorkspaceSnapshot()}
function loadEdition(){try{return localStorage.getItem("mmnEngineEdition")==="global"?"global":"china"}catch{return"china"}}
function loadEditionData(){state=load();videoState=loadVideoState();creatorState=loadCreatorState();verticalState=loadVerticalState();strategyKb=loadStrategyKb();modelJudgments=loadModelJudgments();modelIdentities=loadModelIdentities();founderState=loadFounderState();serverLearnings=[];ragResultsExpanded=false;selectedKnowledgeCluster="";loadServerLearnings();loadWorkspace()}
function setEdition(next){edition=next==="global"?"global":"china";localStorage.setItem("mmnEngineEdition",edition);loadEditionData();render();loadSalesMarquee();toast(`已切换为${editions[edition].label}，数据域已隔离`)}
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
  const data=await api("/api/vertical-assets?platform=all&limit=5000");
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
function saveStrategyKb(){localStorage.setItem(storageKey("mmnStrategyKnowledgeBase"),JSON.stringify(strategyKb));queueWorkspaceSnapshot()}
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
function loadModelIdentities(){try{return JSON.parse(localStorage.getItem(storageKey("mmnModelIdentities")))||{items:{},updatedAt:""}}catch{return{items:{},updatedAt:""}}}
function saveModelIdentities(){localStorage.setItem(storageKey("mmnModelIdentities"),JSON.stringify(modelIdentities))}
function modelIdentityFor(model){return modelIdentities.items?.[model]||null}
const knownBrandNames=["沃尔沃","阿维塔","广汽埃安","埃安","奇瑞","别克","奥迪","宝马","奔驰","本田","东风本田","广汽本田","荣威","智己","启境","小米汽车","特斯拉","蔚来","乐道","极氪","理想","问界","比亚迪","吉利","吉利银河","领克","零跑","小鹏","广汽传祺","腾势","深蓝","长安","长安启源","五菱","宝骏","丰田","广汽丰田","一汽丰田","大众","日产","MG","smart","firefly","北京越野","奔腾","标致","MINI","雪铁龙","上汽大通","埃尚","极狐","东风纳米","待人工确认"];
function cleanModelText(model){return String(model||"").trim().replace(/\s+/g," ")}
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
  return{brand_name:"极氪",normalized_name:suffix?`${family} ${suffix}`:family,model_family:family,energy_type:/PHEV|插混/i.test(raw)?"PHEV":/增程|EREV/i.test(raw)?"EREV":/HEV|混动/i.test(raw)?"HEV":/燃油|ICE/i.test(raw)?"ICE":"UNKNOWN",variant_name:suffix,canonical_key:`极氪|${family}|UNKNOWN|${suffix}`};
 }
 const roewe=compact.match(/^荣威(i5|i6|D7|D5X|RX5|RX9|IMAX8)(.*)$/i);
 if(roewe){const code=/^i[56]$/i.test(roewe[1])?String(roewe[1]).toLowerCase():String(roewe[1]).toUpperCase();const family=`荣威${code}`;return{brand_name:"荣威",normalized_name:family+(roewe[2]?` ${roewe[2]}`:""),model_family:family,energy_type:/EV|纯电|BEV/i.test(raw)?"BEV":/DMH|插混|PHEV/i.test(raw)?"PHEV":"UNKNOWN",variant_name:roewe[2]||"",canonical_key:`荣威|${family}|UNKNOWN|${roewe[2]||""}`}}
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
 const onvo=compact.match(/^(?:乐道|ONVO)?(L60)(.*)$/i);
 if(onvo&&/(乐道|ONVO|L60)/i.test(raw)){const family=`乐道${String(onvo[1]).toUpperCase()}`;return{brand_name:"乐道",normalized_name:family+(onvo[2]?` ${onvo[2]}`:""),model_family:family,energy_type:"BEV",variant_name:onvo[2]||"",canonical_key:`乐道|${family}|BEV|${onvo[2]||""}`}}
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
function cleanAssetItemsForSlot(items,platformKey,slot,model,role,source="插件自动抓取"){
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
function saveSession(s){session=s;localStorage.setItem("mmnCommercialSession",JSON.stringify(s));renderAccount()}
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
 const comps=dcdTopPositiveCompetitors(state.config.model),next=comps.join(" / ");
 if(state.config.competitor!==next)state.config.competitor=next;
 return comps;
}
function applyModelSelection(model){
 const models=modelOptions();
 if(!models.includes(model))return;
 const changed=state.config.model!==model;
 state.config.model=model;
 state.config.brand=brandForModel(model);
 const comps=dcdTopPositiveCompetitors(model);
 state.config.competitor=comps.join(" / ");
 state.config.project=`${model}认知诊断${comps.length?`｜${comps.length}车核心竞品`:""}`;
 if(changed){
  videoState.config={...videoState.config,ownModel:model,competitor1:comps[0]||"",competitor2:comps[1]||"",competitor3:comps[2]||""};
  contentStrategyState={loading:false,result:null,error:""};
  resetContentPptPlan();
  saveVideoState();
 }
}
function isSummaryImport(){return state.importQuality?.kind==="PRODUCT_EVALUATION_SUMMARY"}
function isBlockedImport(){return state.importQuality?.kind==="INVALID_LEGACY_SUMMARY_IMPORT"}
function summaryMetric(model=state.config.model){return state.summaryMetrics?.[model]||{}}
function metricDisplay(a){
 const coverage=state.importQuality?.metricCoverage||{};
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
 renderDashboard(a);renderData();renderCognition(a);renderVertical();renderVideos();renderActions(a);renderKnowhow(a);renderFounderDistill();renderBloggerSkill();renderStrategyKb();renderLearning(a);renderArchitecture();renderWorkspace();renderConfig();
}
function renderEditionChrome(){
 const cfg=currentEdition();
 document.body.dataset.edition=edition;
 document.title=cfg.title;
 document.querySelectorAll("[data-edition]").forEach(b=>b.classList.toggle("active",b.dataset.edition===edition));
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
 track.innerHTML=repeated.map(t=>`<span>${t}</span>`).join("");
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
 const groups=brandModelGroups(models);
 if(!dashBrandOpen||!groups.some(g=>g.brand===dashBrandOpen))dashBrandOpen=brandForDisplay(state.config.model);
 const activeGroup=groups.find(g=>g.brand===dashBrandOpen)||groups[0]||{brand:"",models:[]};
 const activeModels=activeGroup.models;
 wrap.innerHTML=`<div class="dash-model-selects"><select id="dash-brand-select" aria-label="选择品牌">${groups.map(g=>`<option value="${escapeAttr(g.brand)}" ${g.brand===dashBrandOpen?"selected":""}>${g.brand}</option>`).join("")}</select><select id="dash-model-select" aria-label="选择车型">${activeModels.map(m=>`<option value="${escapeAttr(m)}" ${m===state.config.model?"selected":""}>${m}</option>`).join("")}</select></div>`;
	 const brandSelect=wrap.querySelector("#dash-brand-select"),modelSelect=wrap.querySelector("#dash-model-select");
 brandSelect.onchange=()=>{dashBrandOpen=brandSelect.value;renderModelSwitcher()};
	 modelSelect.onchange=()=>{applyModelSelection(modelSelect.value);dashBrandOpen=brandForDisplay(modelSelect.value);dashboardTopicPlanState={loading:false,result:null,error:""};save();render();toast(`已切换为 ${modelSelect.value}`)};
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
function renderDashboard(a){
 const top=[...a.labels].sort((x,y)=>Math.max(y.op,y.on)-Math.max(x.op,x.on)).slice(0,6);
 document.querySelector("#asset-chart").innerHTML=top.length?`<div class="asset-benchmark-legend"><span><i class="green"></i>高于 Benchmark</span><span><i class="yellow"></i>接近 Benchmark</span><span><i class="red"></i>低于 Benchmark</span></div>${top.map(x=>{const current=x.op+x.on?x.op/(x.op+x.on)*100:0,benchmark=x.cp+x.cn?x.cp/(x.cp+x.cn)*100:50,delta=current-benchmark,status=delta>=5?"green":delta<=-5?"red":"yellow";return`<button type="button" class="asset-benchmark-row" data-asset-label="${escapeAttr(x.label)}" aria-label="查看${escapeAttr(x.label)}的本品与竞品对比"><span class="asset-benchmark-label"><b>${escapeHtml(x.label)}</b><small>Benchmark ${benchmark.toFixed(1)}%</small></span><span class="asset-benchmark-track"><i class="asset-benchmark-bar ${status}" style="width:${current}%"></i><span class="asset-benchmark-marker" style="left:${benchmark}%" title="Benchmark ${benchmark.toFixed(1)}%"></span></span><strong class="${status}">${current.toFixed(1)}%</strong></button>`}).join("")}`:`<div class="empty-state">暂无 ${state.config.model} 的认知资产数据，请先导入该车型声量数据。</div>`;
 document.querySelectorAll("#asset-chart [data-asset-label]").forEach(row=>row.onclick=()=>openAssetBenchmarkDialog(row.dataset.assetLabel));
 const selected=a.labels.filter(x=>x.priority>0).slice(0,4);document.querySelector("#top-actions").innerHTML=selected.map(x=>{const ac=actionFor(x);return`<div class="action-card"><div><b>本周继续修复 · ${x.label}</b><p>${ac.proposition}</p></div></div>`}).join("")||"<p>暂无可执行建议，请补充数据。</p>";
	 renderModelJudgmentWorkbench();
 renderDashboardTopicPlanner(a);
	 renderDashboardData(a);
 renderDashboardCognition(a);
 renderOpportunityMap(a);
}
function openAssetBenchmarkDialog(label){
 const rows=state.rows.filter(r=>r[4]===label),models=[...new Set(rows.map(r=>r[0]).filter(Boolean))];
 if(!rows.length||!models.length)return;
 const values=models.map(model=>{const modelRows=rows.filter(r=>r[0]===model),scores=modelRows.reduce((sum,r)=>{const s=score(r);sum.positive+=s.positive;sum.negative+=s.negative;sum.samples+=+r[8]||0;return sum},{positive:0,negative:0,samples:0}),total=scores.positive+scores.negative;return{model,value:total?scores.positive/total*100:0,samples:scores.samples,isOwn:model===state.config.model}}).sort((a,b)=>Number(b.isOwn)-Number(a.isOwn)||b.value-a.value);
 const competitors=values.filter(x=>!x.isOwn),benchmark=competitors.length?competitors.reduce((sum,x)=>sum+x.value,0)/competitors.length:50,own=values.find(x=>x.isOwn),delta=own?own.value-benchmark:0;
 const dialog=document.querySelector("#asset-benchmark-dialog"),body=document.querySelector("#asset-benchmark-dialog-body");
 document.querySelector("#asset-benchmark-dialog-title").textContent=`${label}｜本品与竞品展现`;
 body.innerHTML=`<div class="trend-summary asset-dialog-summary"><div><span>当前标签</span><b>${escapeHtml(label)}</b><small>点击柱体或标签进入对比</small></div><div><span>本品</span><b>${escapeHtml(state.config.model)}</b><small>${own?`${own.value.toFixed(1)}% · ${own.samples.toLocaleString()} 条声量`:'暂无该标签样本'}</small></div><div><span>竞品 Benchmark</span><b>${benchmark.toFixed(1)}%</b><small>${competitors.length} 个竞品均值</small></div><div><span>本品相对竞品</span><b class="${delta>=5?'green':delta<=-5?'red':'yellow'}">${delta>0?'+':''}${delta.toFixed(1)}pp</b><small>${delta>=5?'高于 Benchmark':delta<=-5?'低于 Benchmark':'接近 Benchmark'}</small></div></div><div class="asset-dialog-list">${values.map(x=>{const d=x.value-benchmark,status=d>=5?'green':d<=-5?'red':'yellow';return`<div class="asset-dialog-row ${x.isOwn?'own':''}"><div><span>${x.isOwn?'本品':'竞品'}</span><b>${escapeHtml(x.model)}</b><small>${x.samples.toLocaleString()} 条声量</small></div><div class="asset-dialog-track"><i class="asset-benchmark-bar ${status}" style="width:${x.value}%"></i><span class="asset-benchmark-marker" style="left:${benchmark}%"></span></div><strong class="${status}">${x.value.toFixed(1)}%</strong><em>${x.isOwn?'当前车型':`${d>0?'+':''}${d.toFixed(1)}pp`}</em></div>`}).join("")}</div>`;
 dialog.showModal();
}
function renderDashboardTopicPlanner(a=analysis()){
 const box=document.querySelector("#dashboard-topic-plan");
 if(!box)return;
 const model=state.config.model;
 const competitor=state.config.competitor||"核心竞品";
 const stage=document.querySelector("#dashboard-topic-stage");
 if(stage&&!state.config.stage)state.config.stage=stage.value||"上市中";
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
	  const competitors=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
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
  const competitors=String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean);
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
 box.innerHTML=items.length?`<div class="model-judgment-list">${items.map(item=>`<article class="model-judgment-card"><div><span>${item.dimension||"综合判断"} · ${item.brand_name||state.config.brand}</span><b>${item.model_name||state.config.model}</b></div><p>${item.viewpoint||item.source_text||""}</p><dl><dt>归因</dt><dd>${item.attribution||"待补充"}</dd><dt>策略动作</dt><dd>${item.strategy_implication||"待补充"}</dd><dt>还缺证据</dt><dd>${item.evidence_needed||"待补充"}</dd></dl><small>${(item.tags||[]).slice(0,8).map(x=>`#${x}`).join(" ")}｜${(item.created_at||item.createdAt||"").slice(0,10)}</small></article>`).join("")}</div>`:`<p class="empty">还没有沉淀到 ${state.config.model} 的车型判断。你可以直接输入一句判断，MMN会自动拆成车型资产。</p>`;
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
function renderSummaryAttributeMatrix(rows){
 const sources=[...new Set(rows.map(r=>r[2]).filter(Boolean))],byLabel=new Map();
 rows.forEach(r=>{const score=Number(r[14]);if(!r[4]||!Number.isFinite(score))return;const item=byLabel.get(r[4])||{label:r[4],category:r[3],scores:new Map()};item.scores.set(r[2],score);byLabel.set(r[4],item)});
 const items=[...byLabel.values()].sort((a,b)=>(b.scores.get(sources[0])??-2)-(a.scores.get(sources[0])??-2)||String(a.label).localeCompare(String(b.label),"zh-CN"));
 if(!items.length)return`<div class="empty-state">当前数据来源没有可展示的属性 NSR。</div>`;
 const columns=`minmax(170px,1.2fr) repeat(${Math.max(sources.length,1)},minmax(125px,1fr))`;
 return`<div class="summary-attribute-head" style="grid-template-columns:${columns}"><b>属性标签</b>${sources.map(source=>`<b>${escapeHtml(source)}</b>`).join("")}</div><div class="summary-attribute-body">${items.map(item=>`<div class="summary-attribute-row" style="grid-template-columns:${columns}"><div class="summary-attribute-label"><b>${escapeHtml(item.label)}</b><small>${escapeHtml(item.category)}</small></div>${sources.map(source=>{const score=item.scores.get(source);if(!Number.isFinite(score))return`<div class="summary-attribute-cell missing">—</div>`;const percent=score*100,tone=score>=.25?"positive":score<0?"negative":"neutral";return`<div class="summary-attribute-cell ${tone}"><span class="summary-attribute-value">${percent.toFixed(1)}%</span><i style="width:${Math.min(Math.abs(percent),100).toFixed(1)}%"></i></div>`}).join("")}</div>`).join("")}</div>`;
}
function summaryHeatNumber(value){return Math.max(0,Number(value)||0)}
function summaryHeatDisplay(value){const number=summaryHeatNumber(value);return number>=10000?`${(number/10000).toFixed(1)}万`:number.toLocaleString()}
function summaryHeatPercentage(value,total){return total?Math.min(summaryHeatNumber(value)/summaryHeatNumber(total)*100,100):0}
function summaryHeatPercentageDisplay(value){return`${value.toFixed(1)}%`}
function closeSummaryPlatformPopover(restoreFocus=false){
 const popover=document.querySelector(".summary-platform-popover");
 if(popover)popover.remove();
 if(summaryPlatformPopoverCleanup){summaryPlatformPopoverCleanup();summaryPlatformPopoverCleanup=null}
 if(restoreFocus&&summaryPlatformPopoverTrigger?.isConnected)summaryPlatformPopoverTrigger.focus();
 summaryPlatformPopoverTrigger=null;
}
function openSummaryPlatformPopover(model,trigger){
 closeSummaryPlatformPopover();
 const chart=trigger.closest(".summary-heat-chart"),ownModel=state.config.model,heat=state.summaryHeat||{},values=heat[model]?.platformVolume||{},ownValues=heat[ownModel]?.platformVolume||{},modelTotal=summaryHeatNumber(heat[model]?.volume),ownTotal=summaryHeatNumber(heat[ownModel]?.volume),isCompetitor=model!==ownModel;
 if(!chart)return;
 const entries=Object.entries(values).map(([platform,value])=>{const count=summaryHeatNumber(value),ownCount=summaryHeatNumber(ownValues[platform]);return{platform,value:count,ownValue:ownCount,percentage:summaryHeatPercentage(count,modelTotal),ownPercentage:summaryHeatPercentage(ownCount,ownTotal)}}),popover=document.createElement("section");
 popover.className="summary-platform-popover";
 popover.setAttribute("role","dialog");
 popover.setAttribute("aria-label",isCompetitor?`${model}与${ownModel}分平台声量对比`:`${model}分平台声量表现`);
 const title=isCompetitor?`${escapeHtml(model)} vs ${escapeHtml(ownModel)} · 分平台声量对比`:`${escapeHtml(model)} · 分平台声量表现`;
 popover.innerHTML=`<header><div><span>平台声量占各车型全网声量</span><b>${title}</b></div><button type="button" aria-label="关闭分平台声量气泡"></button></header>${entries.length?`<div class="summary-platform-bars">${entries.map(item=>`<section class="summary-platform-group"><span class="summary-platform-name">${escapeHtml(item.platform)}</span><div class="summary-platform-series"><div class="competitor"><small>${escapeHtml(model)}</small><i><em style="width:${item.percentage.toFixed(4)}%"></em></i><strong title="绝对声量 ${item.value.toLocaleString()}">${summaryHeatPercentageDisplay(item.percentage)}</strong></div>${isCompetitor?`<div class="own"><small>本品 · ${escapeHtml(ownModel)}</small><i><em style="width:${item.ownPercentage.toFixed(4)}%"></em></i><strong title="绝对声量 ${item.ownValue.toLocaleString()}">${summaryHeatPercentageDisplay(item.ownPercentage)}</strong></div>`:""}</div></section>`).join("")}</div>`:`<div class="summary-platform-empty">当前导入版本未保留分平台声量，请重新导入原表。</div>`}`;
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
function renderSummaryHeatDashboard(a){
 closeSummaryPlatformPopover();
 const available=(state.models||[]).filter(Boolean),selected=summaryHeatSelection(),heat=state.summaryHeat||{},ownRows=a?.own||state.rows.filter(r=>r[0]===state.config.model);
 const sources=[...new Set(ownRows.map(r=>r[2]).filter(Boolean))],labels=[...new Set(ownRows.map(r=>r[4]).filter(Boolean))],referenceModels=available.filter(model=>model!==state.config.model);
 if(dashboardPlatformFilter!=="all"&&!sources.includes(dashboardPlatformFilter))dashboardPlatformFilter="all";
 const filteredRows=dashboardPlatformFilter==="all"?ownRows:ownRows.filter(r=>r[2]===dashboardPlatformFilter);
 const rows=selected.map(model=>({model,volume:summaryHeatNumber(heat[model]?.volume),interaction:summaryHeatNumber(heat[model]?.interaction)}));
 const maxVolume=Math.max(...rows.map(row=>row.volume),1),maxInteraction=Math.max(...rows.map(row=>row.interaction),1);
 document.querySelector(".dashboard-data-title-copy span").textContent="产品评价汇总";
 document.querySelector(".dashboard-data-title-copy h2").textContent="全网声量及互动量对比";
 document.querySelector("#dashboard-data-note").textContent=`${labels.length} 个可用产品点 · ${referenceModels.length} 台可选竞品`;
 document.querySelector("#dashboard-platform-control").innerHTML=`<label class="platform-filter-bubble dashboard-platform-bubble"><span>数据来源</span><select id="dashboard-platform-filter" aria-label="按数据来源筛选属性NSR"><option value="all">全部来源</option>${sources.map(source=>`<option value="${escapeAttr(source)}" ${source===dashboardPlatformFilter?"selected":""}>${escapeHtml(source)}</option>`).join("")}</select></label>`;
 document.querySelector("#dashboard-data-context").innerHTML=[
  ["本品车型",state.config.model,"own-model"],
  ["数据参照车型",referenceModels.join(" / ")||"暂无参照车型","reference-models"],
  ["时间维度",dashboardTimeDimension(),"time-dimension"],
  ["数据维度","全网声量 × 互动量 × 属性NSR评分","data-dimension"],
  ["当前可用产品点",labels.slice(0,6).join(" / ")||"暂无可用产品点","label-dimension"]
 ].map(([name,value,cls])=>`<div class="${cls}"><span>${name}</span><b title="${escapeAttr(value)}">${escapeHtml(value)}</b></div>`).join("");
 const summary=document.querySelector("#dashboard-data-summary");
 summary.innerHTML="";
 summary.hidden=true;
 const surface=document.querySelector("#dashboard-emotion-quadrant");
 surface.className="summary-dashboard-workbench";
 const ownModel=state.config.model,competitorModels=available.filter(model=>model!==ownModel);
 const selectorHtml=`<aside class="summary-heat-selector"><section class="summary-heat-own"><span>本品车型</span><label><input type="checkbox" checked disabled aria-label="本品车型固定展示"><b>${escapeHtml(ownModel)}</b></label></section><section class="summary-heat-competitors"><span>对比竞品</span><div class="summary-heat-model-list">${competitorModels.map(model=>`<label><input type="checkbox" value="${escapeAttr(model)}" ${selected.includes(model)?"checked":""}><span>${escapeHtml(model)}</span></label>`).join("")}</div><label class="summary-heat-add"><span>添加竞品</span><select id="summary-heat-add-model"><option value="">选择竞品</option>${competitorModels.filter(model=>!selected.includes(model)).map(model=>`<option value="${escapeAttr(model)}">${escapeHtml(model)}</option>`).join("")}</select></label></section></aside>`;
 const chartRows=rows.map(row=>`<button type="button" class="summary-heat-row" data-summary-heat-model="${escapeAttr(row.model)}" aria-label="查看${escapeAttr(row.model)}分平台声量表现"><b>${escapeHtml(row.model)}</b><span class="summary-heat-bars"><span><small>声量</small><i class="volume" style="width:${row.volume/maxVolume*100}%"></i><strong>${summaryHeatDisplay(row.volume)}</strong></span><span><small>互动量</small><i class="interaction" style="width:${row.interaction/maxInteraction*100}%"></i><strong>${summaryHeatDisplay(row.interaction)}</strong></span></span></button>`).join("");
 const chartHtml=`<section class="summary-heat-chart"><div class="summary-heat-chart-head"><small>声量与互动量按各自独立尺度展示，不可直接比较绝对柱长。</small><div class="summary-heat-legend"><span><i class="volume"></i>全网声量</span><span><i class="interaction"></i>全网互动量</span></div></div>${chartRows||`<div class="empty-state">暂无可展示车型。</div>`}</section>`;
 surface.innerHTML=`<div class="summary-heat-workbench">${selectorHtml}${chartHtml}</div><section class="summary-attribute-section"><header><div><span>属性诊断</span><b>真实属性 NSR 对比</b></div><small>${dashboardPlatformFilter==="all"?"全部来源":escapeHtml(dashboardPlatformFilter)}</small></header><div class="summary-attribute-matrix">${renderSummaryAttributeMatrix(filteredRows)}</div></section>`;
 document.querySelectorAll(".summary-heat-model-list input").forEach(input=>input.onchange=()=>{summaryDashboardModels=[ownModel,...document.querySelectorAll(".summary-heat-model-list input:checked")].map(node=>node.value);renderSummaryHeatDashboard()});
 const add=document.querySelector("#summary-heat-add-model");if(add)add.onchange=()=>{if(add.value&&!summaryDashboardModels.includes(add.value)){summaryDashboardModels=[...summaryDashboardModels,add.value];renderSummaryHeatDashboard()}};
 document.querySelectorAll("[data-summary-heat-model]").forEach(row=>row.onclick=event=>{event.stopPropagation();openSummaryPlatformPopover(row.dataset.summaryHeatModel,row)});
 document.querySelector("#dashboard-platform-filter").onchange=event=>{dashboardPlatformFilter=event.target.value;renderSummaryHeatDashboard(a)};
}
function dashboardTimeDimension(){
 const importedRange=String(state.importQuality?.timeRange||"").trim();
 if(importedRange)return importedRange;
 const text=String(state.sourceNote||""),range=text.match(/(20\d{2}[.\/-]\d{1,2}[.\/-]\d{1,2})\s*(?:-|—|–|至|到)\s*(20\d{2}[.\/-]\d{1,2}[.\/-]\d{1,2})/);
 if(range)return`${range[1]} — ${range[2]}`;
 const periods=[...new Set((verticalState.items||[]).map(x=>x.period).filter(Boolean))].sort();
 return periods.length?`${periods[0]} — ${periods[periods.length-1]}`:"当前导入周期";
}
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
 body.innerHTML=`<div class="trend-summary emotion-dialog-summary"><div><span>情绪象限</span><b>${quadrantTitle}</b><small>${definition.subtitle}</small></div><div><span>所属赛道</span><b>${escapeHtml(category)}</b><small>${platform==="all"?"全部平台":escapeHtml(platform)}</small></div><div><span>本品标签占比</span><b>${own?`${own.share.toFixed(1)}%`:"暂无样本"}</b><small>占本品当前平台总声量</small></div><div><span>竞品覆盖</span><b>${competitors.length} 个</b><small>统一使用车型内占比</small></div></div><div class="emotion-competitor-list">${values.length?values.map(x=>{const delta=x.share-(own?.share||0);return`<div class="emotion-competitor-row ${x.isOwn?"own":""}"><div><span>${x.isOwn?"本品":"竞品"}</span><b>${escapeHtml(x.model)}</b><small>${escapeHtml(x.emotionNames.join(" / "))}</small></div><div class="emotion-competitor-track"><i style="width:${x.share/max*100}%"></i></div><strong>${x.share.toFixed(1)}%</strong><em>${x.isOwn?"占车型总声量":`${delta>0?"+":""}${delta.toFixed(1)}pp`}</em></div>`}).join(""):`<div class="empty-state">暂无可对比的车型数据</div>`}</div>`;
 dialog.showModal();
}
function renderDashboardCognition(a){
 const rows=a.labels.slice(0,8);
 document.querySelector("#dashboard-cognition-table").innerHTML=`<thead><tr><th>认知标签</th><th>诊断</th><th>本品负向</th><th>Gap</th><th>优先级</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><b>${x.label}</b><small>${x.category}</small></td><td><span class="tag ${x.diagnosis==="优先修复"?"risk":x.diagnosis==="持续放大"?"asset":""}">${x.diagnosis}</span></td><td class="negative">${Math.round(x.on).toLocaleString()}</td><td>${(x.gap*100).toFixed(1)}%</td><td>${x.priority.toFixed(1)}</td></tr>`).join(""):`<tr><td colspan="5" class="empty-cell">暂无 ${state.config.model} 的认知诊断数据，导入该车型声量后会自动计算。</td></tr>`}</tbody>`;
}
function opportunityMapLabels(labels){
 const types=["优先修复","抢占空位","持续放大"],groups=new Map(types.map(type=>[type,[]])),base=Math.floor(labels.length/types.length),remainder=labels.length%types.length,capacity=new Map(types.map((type,i)=>[type,base+(i<remainder?1:0)]));
 const fit=(x,type)=>{const total=Math.max(x.op+x.on,1),original=x.diagnosis===type ? .12 : 0;if(type==="优先修复")return x.on/total+(x.impact||0)/10+original;if(type==="抢占空位")return Math.max(x.gap||0,0)*4+(x.white||0)/20+(x.impact||0)/20+original;return x.op/total+Math.max(-(x.gap||0),0)*2+original};
 const pairs=labels.flatMap(x=>types.map(type=>({x,type,score:fit(x,type)}))).sort((a,b)=>b.score-a.score),assigned=new Set();
 pairs.forEach(({x,type})=>{if(assigned.has(x.label)||groups.get(type).length>=capacity.get(type))return;groups.get(type).push({...x,mapDiagnosis:type,mapRebalanced:x.diagnosis!==type});assigned.add(x.label)});
 labels.filter(x=>!assigned.has(x.label)).forEach(x=>{const type=types.find(t=>groups.get(t).length<capacity.get(t))||types[0];groups.get(type).push({...x,mapDiagnosis:type,mapRebalanced:x.diagnosis!==type})});
 return types.flatMap(type=>groups.get(type));
}
function renderOpportunityMap(a){
 const all=opportunityMapLabels(a.labels.filter(x=>x.op+x.on+x.cp+x.cn>0)),filtered=mapFilter==="all"?all:all.filter(x=>x.mapDiagnosis===mapFilter),ranked=[...filtered].sort((x,y)=>bigness(y)-bigness(x)),shown=ranked.slice(0,mapLimit),maxGap=Math.max(...all.map(x=>Math.abs(x.gap)),.01);
 document.querySelectorAll("#map-filters button").forEach(b=>b.classList.toggle("active",b.dataset.filter===mapFilter));
 document.querySelector("#map-limit").value=String(mapLimit);
 document.querySelector("#map-summary").textContent=`当前筛选 ${filtered.length} 个标签，地图显示 Top ${shown.length}。策略分类已按风险、竞品领先度与本品资产动态校准。`;
 document.querySelector("#opportunity-map").innerHTML=shown.length?layoutBubbles(shown.map(x=>{const left=50+(x.gap/maxGap)*42,bottom=Math.min(88,Math.max(9,x.impact/5*84)),cls=x.mapDiagnosis==="优先修复"?"risk":x.mapDiagnosis==="抢占空位"?"chance":"asset";return{...x,left,bottom,cls,w:Math.max(54,x.label.length*13+22),h:27}})).map(b=>`<span class="bubble ${b.cls}" style="left:${b.x}%;bottom:${b.y}%" title="${b.label}｜${b.mapDiagnosis}｜Gap ${(b.gap*100).toFixed(1)}%｜优先级 ${b.priority.toFixed(1)}"><i style="width:${Math.hypot(b.x-b.left,b.y-b.bottom)*3.2}px;transform:rotate(${Math.atan2(b.bottom-b.y,b.left-b.x)}rad)"></i>${b.label}</span>`).join(""):`<div class="map-empty">暂无有效认知标签，请先导入当前车型数据</div>`;
 document.querySelector("#opportunity-table").innerHTML=`<thead><tr><th>认知标签</th><th>赛道</th><th>诊断</th><th>本品负向</th><th>认知 Gap</th><th>Impact</th><th>优先级</th></tr></thead><tbody>${ranked.map(x=>`<tr><td><b>${x.label}</b></td><td>${x.category}</td><td><span class="tag ${x.mapDiagnosis==="优先修复"?"risk":x.mapDiagnosis==="持续放大"?"asset":""}">${x.mapDiagnosis}</span></td><td class="negative">${Math.round(x.on).toLocaleString()}</td><td>${(x.gap*100).toFixed(1)}%</td><td>${x.impact.toFixed(1)}</td><td>${x.priority.toFixed(1)}</td></tr>`).join("")}</tbody>`;
}
function bigness(x){return (x.priority||0)*1000+(x.on||0)+Math.max(x.op||0,x.cp||0)}
function layoutBubbles(items){
 const placed=[],vw=860,vh=310,pad=5,overlap=(a,b)=>!(a.x+a.w/2+pad<b.x-b.w/2||a.x-a.w/2-pad>b.x+b.w/2||a.y+a.h/2+pad<b.y-b.h/2||a.y-a.h/2-pad>b.y+b.h/2);
 return items.sort((a,b)=>b.priority-a.priority).map(it=>{const baseX=it.left/100*vw,baseY=(100-it.bottom)/100*vh,candidates=[];for(let r=0;r<=120;r+=14){for(let deg=0;deg<360;deg+=30){const rad=deg*Math.PI/180,x=Math.min(vw-it.w/2,Math.max(it.w/2,baseX+Math.cos(rad)*r)),y=Math.min(vh-it.h/2,Math.max(it.h/2,baseY+Math.sin(rad)*r));candidates.push({x,y,dist:Math.hypot(x-baseX,y-baseY)})}}candidates.sort((a,b)=>a.dist-b.dist);let pick=candidates.find(c=>!placed.some(p=>overlap({...c,w:it.w,h:it.h},p)))||candidates[0];const b={...it,x:pick.x/vw*100,y:100-pick.y/vh*100,_x:pick.x,_y:pick.y,w:it.w,h:it.h};placed.push({x:pick.x,y:pick.y,w:it.w,h:it.h});return b}).sort((a,b)=>a.left-b.left);
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
   applyModelSelection(next);save();render();toast(`已切换到 ${canonicalModelLabel(next)} 的认知诊断`);
  }
 };
 modelSel.onchange=()=>{
  if(!modelSel.value)return;
  cognitionStrategyState={loading:false,result:null,error:""};
  applyModelSelection(modelSel.value);cognitionBrandOpen=brandForDisplay(modelSel.value)||brandForModel(modelSel.value);save();render();toast(`已切换到 ${canonicalModelLabel(modelSel.value)} 的认知诊断`);
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
  outputPolicy:{visibleBrand:"MMN多模态策略输出",requiredModels:["qwen","deepseek"],requiredSections:["核心认知判断","资产负债机会","策略动作","KPI"]}
 };
}
function localCognitionStrategyDraft(ctx){
 const model=ctx.project?.model||"当前车型",labels=ctx.breakdown?.labels||[];
 const asset=labels.find(x=>x.diagnosis==="持续放大")||labels[0]||{},risk=labels.find(x=>x.diagnosis==="优先修复")||labels.find(x=>x.ownNegative>0)||{},space=labels.find(x=>x.diagnosis==="抢占空位")||labels.find(x=>x.white>0)||{};
 const topPlatform=ctx.breakdown?.platforms?.[0]?.key||"核心平台",relation=ctx.verticalCompetition?.relations?.[0];
 const comp=relation?.competitor||(ctx.project?.competitors||[])[0]||"核心竞品";
 const relationLine=relation?`${relation.platform}${relation.period?` ${relation.period}`:""}中，${model}与${comp}的关系是“${relation.status}”，正向排名${relation.positiveRank||"未上榜"}、反向排名${relation.negativeRank||"未上榜"}。`:`垂媒竞争格局用于校准竞品口径，避免只在内部标签里自我判断。`;
 return[`### 核心认知判断`,`${model} 的认知诊断要同时处理三件事：把“${asset.label||"已有好评"}”做成可复述资产，把“${risk.label||"购买疑虑"}”转成可验证证据，把“${space.label||"竞品空位"}”抢成清晰的购买理由。`,`### 资产负债机会`,`1. 资产：${asset.label||"核心正向标签"} 可以继续放大，适合沉淀成短视频钩子、垂媒解释和品牌传播口径。\n2. 负债：${risk.label||"高风险疑虑"} 必须优先修复，先给证据，再谈卖点。\n3. 机会：${space.label||"认知空位"} 是与 ${comp} 拉开差异的入口，不能只做参数对比。`,`### 策略动作`,`1. 在 ${topPlatform} 先做“一个疑虑一个证据”的内容包，把用户问题直接改成标题。\n2. 竞品表达围绕 ${comp} 做同场景对比，用家庭、通勤、长途、价格权益等真实任务解释差异。\n3. 达人与内容协同：评测达人给证据，车主/KOC给使用场景，品牌FAQ承接高频疑虑。`,`### KPI`,`核心正向标签占比提升、负向疑虑评论占比下降、认知Gap收窄、垂媒正向排名改善、试驾/询价线索提升。`,`### MMN交叉验证结论`,`MMN主控已生成主策略，MMN质检已复核风险和过度承诺；两者冲突时，以可验证证据和当前数据结构为准。`].join("\n\n");
}
function renderCognitionMmnStrategy(a){
 const box=document.querySelector("#cognition-mmn-output"),status=document.querySelector("#cognition-mmn-status");
 if(!box)return;
 const ctx=cognitionStrategyContext(a),result=cognitionStrategyState.result||{text:localCognitionStrategyDraft(ctx),parts:{rules:localCognitionStrategyDraft(ctx)},context:ctx};
 if(status)status.textContent=cognitionStrategyState.loading?"MMN正在交叉验证":mmnTraceLabel(result);
 const parts=result.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(result.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"}[k]||k}</b>${markdownish(String(v))}</section>`).join("")}${result.errors&&Object.keys(result.errors).length?`<section><b>缺席/错误</b>${Object.entries(result.errors).map(([k,v])=>`<p>${k}: ${v}</p>`).join("")}</section>`:""}</details>`:"";
 box.innerHTML=`<div class="content-mmn-head"><div><b>${cognitionStrategyState.loading?"MMN正在生成认知策略":"MMN多模态策略输出"}</b><span>决策驾驶舱 + 声量数据中心 + 垂媒竞争格局｜${ctx.project.brand} / ${canonicalModelLabel(ctx.project.model)}｜MMN交叉验证</span></div><button type="button" class="primary" id="run-cognition-mmn-strategy" ${cognitionStrategyState.loading?"disabled":""}>${cognitionStrategyState.loading?"生成中…":"生成/刷新MMN策略"}</button></div><div class="content-mmn-output">${markdownish(String(result.text||""))}</div>${cognitionStrategyState.error?`<p class="empty">模型生成失败，已使用MMN本地策略输出：${cognitionStrategyState.error}</p>`:""}${parts}`;
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
 const allItems=verticalState.items||[],allSources=verticalState.sources||[];
 if(!allItems.length)restoreVerticalAssetsFromServer();
 const platformOptions=["all",...[...new Set(allItems.map(x=>x.platform).filter(Boolean))].sort()];
 const selectedPlatform=platformOptions.includes(verticalState.selectedPlatform)?verticalState.selectedPlatform:"all";
 verticalState.selectedPlatform=selectedPlatform;
 const platformItems=selectedPlatform==="all"?allItems:allItems.filter(x=>x.platform===selectedPlatform);
 const availableSources=[...new Set(platformItems.map(x=>x.source).filter(Boolean))];
 const sourceOptions=["all",...availableSources];
 const selectedSource="all";
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
 if(learningBox)learningBox.innerHTML=modelItems.length?`<div class="ai-learning-bar"><div><b>MMN智能体学习</b><span>把 ${model} 在 ${sourceLabel} / ${activePeriod||"当前周期"} 的正反向关系交给MMN营销引擎学习，并写入RAG知识库。</span></div><button type="button" class="primary" id="vertical-ai-learn">MMN学习正反向</button></div><div id="vertical-ai-learning-result"></div>`:"";
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
 const box=document.querySelector("#vertical-ai-learning-result");
 if(!context?.rows?.length){toast("当前车型没有可学习的正反向数据");return}
 if(box)box.innerHTML="<p>MMN正在学习这组正反向竞争关系…</p>";
 try{
  const data=await api("/api/ai/vertical-rank-learning",{method:"POST",body:JSON.stringify({context:{...context,rows:context.rows.slice(0,30).map(x=>({competitor:x.competitor,positiveRank:x.positiveRank,negativeRank:x.negativeRank,share:x.share,status:rankStatus(x)}))}})});
  if(data.knowledgeItem)mergeStrategyKnowledge([data.knowledgeItem]);
  const trace=data.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(data.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",rules:"MMN本地规则记录"}[k]||k}</b>${consultingMarkdown(String(v))}</section>`).join("")}${data.errors&&Object.keys(data.errors).length?`<section><b>缺席/错误</b>${Object.entries(data.errors).map(([k,v])=>`<p>${k}: ${v}</p>`).join("")}</section>`:""}</details>`:"";
  if(box)box.innerHTML=`<article class="rag-card mmn-consulting-card"><span>MMN学习完成｜${context.platform}｜${context.period}｜交叉验证完成</span><b>${context.model} 正反向竞争格局学习</b><div class="mmn-consulting-body">${consultingMarkdown(data.text)}</div><small>已写入RAG知识库，可被巡检和MMN策略召回。</small>${trace}</article>`;
  renderStrategyKb();
  toast("MMN已学习正反向排名，并写入RAG知识库");
 }catch(err){
  if(box)box.innerHTML=`<p class="empty">MMN学习失败：${err.message}</p>`;
  toast(`MMN学习失败：${err.message}`);
 }
}
function shortSourceName(s){return String(s||"").replace(/\.xlsx$/i,"").replace(/[-_]?更新到\d+/,"")}
function formatShare(v){const n=Number(v);if(!Number.isFinite(n)||n<=0)return"—";return `${(n>1?n:n*100).toFixed(1)}%`}
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
function largeTrend(rows,allPeriods=[]){
 const data=[...rows].sort(sortVerticalItem),periods=(allPeriods&&allPeriods.length?allPeriods:uniquePeriods(data)),byPeriod=new Map(data.map(x=>[x.period,x])),maxRank=Math.max(10,...data.flatMap(x=>[x.positiveRank||0,x.negativeRank||0])),w=760,h=280,pad=42,den=Math.max(1,periods.length-1);
 const pts=key=>periods.map((p,i)=>{const x=byPeriod.get(p);if(!x||!x[key])return null;const rank=x[key],y=pad+(rank-1)/(maxRank-1)*(h-pad*2);return{x:pad+i/den*(w-pad*2),y,rank,period:p}});
 const line=arr=>arr.filter(Boolean).map(p=>`${p.x},${p.y}`).join(" "),pos=pts("positiveRank"),neg=pts("negativeRank"),present=new Set(data.map(x=>x.period));
 return`<svg viewBox="0 0 ${w} ${h}">${[1,Math.ceil(maxRank/2),maxRank].map(r=>`<line x1="${pad}" y1="${pad+(r-1)/(maxRank-1)*(h-pad*2)}" x2="${w-pad}" y2="${pad+(r-1)/(maxRank-1)*(h-pad*2)}"></line><text x="10" y="${pad+(r-1)/(maxRank-1)*(h-pad*2)+4}">${r}</text>`).join("")}<polyline class="pos-line" points="${line(pos)}"></polyline><polyline class="neg-line" points="${line(neg)}"></polyline>${pos.filter(Boolean).map(p=>`<circle class="pos-dot" cx="${p.x}" cy="${p.y}" r="5"></circle><text class="point-label" x="${p.x}" y="${p.y-9}" text-anchor="middle">${p.rank}</text>`).join("")}${neg.filter(Boolean).map(p=>`<circle class="neg-dot" cx="${p.x}" cy="${p.y}" r="5"></circle><text class="point-label" x="${p.x}" y="${p.y+18}" text-anchor="middle">${p.rank}</text>`).join("")}${periods.map((p,i)=>`<text class="x-label ${present.has(p)?"":"missing"}" x="${pad+i/den*(w-pad*2)}" y="${h-10}" text-anchor="middle">${p}</text>`).join("")}</svg><div class="trend-legend"><span><i class="green"></i>正向排名</span><span><i class="red"></i>反向排名</span></div>`;
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
 const line=arr=>arr.filter(Boolean).map(p=>`${p.x},${p.y}`).join(" ");
 const pos=pts("positiveRank"),neg=pts("negativeRank"),presentPeriods=new Set(data.map(x=>x.period));
 const missing=periods.length-data.length;
 el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="正反向排名趋势">${[1,Math.ceil(maxRank/2),maxRank].map(r=>`<line x1="${pad}" y1="${pad+(r-1)/(maxRank-1)*(h-pad*2)}" x2="${w-pad}" y2="${pad+(r-1)/(maxRank-1)*(h-pad*2)}"></line><text x="6" y="${pad+(r-1)/(maxRank-1)*(h-pad*2)+4}">${r}</text>`).join("")}<polyline class="pos-line" points="${line(pos)}"></polyline><polyline class="neg-line" points="${line(neg)}"></polyline>${pos.filter(Boolean).map(p=>`<circle class="pos-dot" cx="${p.x}" cy="${p.y}" r="4"><title>${p.period} 正向第${p.rank}</title></circle>`).join("")}${neg.filter(Boolean).map(p=>`<circle class="neg-dot" cx="${p.x}" cy="${p.y}" r="4"><title>${p.period} 反向第${p.rank}</title></circle>`).join("")}${periods.map((p,i)=>`<text class="x-label ${presentPeriods.has(p)?"":"missing"}" x="${pad+i/den*(w-pad*2)}" y="${h-8}" text-anchor="middle">${p}</text>`).join("")}</svg><div class="trend-legend"><span><i class="green"></i>正向排名</span><span><i class="red"></i>反向排名</span>${missing>0?`<em>${missing} 个周期该竞品未进入当前排名表</em>`:""}</div>`;
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
 if(!socialPluginStatus){status.textContent="等待检测";dy.textContent="等待插件状态";xhs.textContent="等待插件状态";return}
 status.textContent=socialPluginStatus.installed?"已识别Chrome采集插件":"未识别插件";
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
  toast(`正在同步${assetPlatformName(platform)}插件导出到独立达人库…`);
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
  toast(`正在自动驱动${assetPlatformName(platformKey)}插件抓取：${query}`);
  const data=await api("/api/social-plugin/auto-crawl",{method:"POST",body:JSON.stringify({platform:platformKey,query,limit:50})});
  videoState.files[platformKey][slot]={...(videoState.files?.[platformKey]?.[slot]||{}),source:"自动抓取任务",count:0,items:videoState.files?.[platformKey]?.[slot]?.items||[],crawlTask:{...data.task,platform:platformKey,slot,role,model,startedAt:new Date().toISOString()},taskStatus:"driving"};
  resetContentPptPlan();
  saveVideoState();
  renderVideos();
  runContentMmnStrategy(true);
  toast(data.task?.message||"已自动驱动 Chrome 插件开始抓取");
 }catch(e){toast(`自动抓取启动失败：${e.message}`)}
}
async function syncAssetCrawl(platformKey,slot){
 const model=assetModel(slot),role=assetSlots.find(s=>s.key===slot)?.label||"";
 if(!model)return toast("请先设置车型，再同步抓取结果");
 try{
  toast(`正在同步${assetPlatformName(platformKey)} · ${model} 的最新抓取结果…`);
  const data=await api("/api/social-plugin/import-latest",{method:"POST",body:JSON.stringify({platform:platformKey})});
  const rawItems=data.dataset.items||[];
  const items=cleanAssetItemsForSlot(rawItems,platformKey,slot,model,role,data.dataset.source||"插件自动抓取");
  const creatorCount=mergePluginCreators(platformKey,data.dataset.creators||[]);
  if(!items.length&&creatorCount)toast("最新导出只识别到达人画像，未识别到内容明细");
  videoState.files[platformKey][slot]={source:data.dataset.source||"插件自动抓取",count:items.length,syncedAt:new Date().toISOString(),items,pluginExportPath:data.dataset.exportPath||"",exportedAt:data.dataset.exportedAt||"",crawlTask:{query:model,platform:platformKey,slot,role,model},taskStatus:"synced"};
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
 document.querySelector("#creator-card-grid").innerHTML=enriched.length?enriched.map(x=>{const id=x.id||creatorKey(x),city=x.city&&x.city!=="待补充"?x.city:(x.estimatedCity||"城市待核验"),fanText=+x.fans?formatShortNumber(x.fans):x.estimatedFansText?`MMN补全 ${x.estimatedFansText}`:"未采集";return`<article class="creator-card ${x.fitScore>=78?"recommended":""}"><div class="creator-head"><div><span>${x.influenceLabel} · ${city}</span><b>${x.name}</b></div><strong>${x.fitScore}</strong></div><div class="creator-meta"><span>粉丝 ${fanText}</span><span>${x.influenceLabel}</span><span>均播 ${formatShortNumber(x.avgViews,"待补充")}</span><span>互动率 ${x.engagementRate?`${x.engagementRate}%`:"待补充"}</span><span>成本 ${x.costLevel||"待评估"}</span></div><div class="creator-tags"><em class="tier">${x.influenceLabel}</em>${(x.categories||[]).map(t=>`<em>${t}</em>`).join("")}${x.strategyAssets?.length?`<em>策略资产${x.strategyAssets.length}</em>`:""}${x.scriptAssets?.length?`<em>脚本资产${x.scriptAssets.length}</em>`:""}</div><p>${(x.summary||x.publicProfile||x.strengths?.join(" / ")||"等待补充达人能力判断")}</p><small>推荐场景：${(x.fitStages||[]).join("、")||"待MMN分析或手动补充"}｜风险提示：${x.risk||"需结合具体brief复核"}${x.confidence?`｜MMN置信度：${x.confidence}`:""}</small>${x.profileUrl?`<a class="creator-profile" href="${x.profileUrl}" target="_blank">打开主页</a>`:""}<div class="creator-actions"><button type="button" class="ghost" data-creator-edit="${id}">编辑</button><button type="button" class="primary" data-creator-ai="${id}">MMN分析标签</button></div></article>`}).join(""):`<p class="empty">当前筛选下暂无达人。可以调整类型或搜索条件。</p>`;
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
 form.elements.engagementRate.value=+creator.engagementRate||"";
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
  outputPolicy:{hideDataGaps:true,visibleBrand:"MMN模型输出策略",requiredSections:["核心营销结论","三大数据依据","营销动作","KPI"]}
 };
}
function localContentStrategyDraft(ctx){
 const top=ctx.upstream?.cockpit?.priorityLabels?.[0]?.label||ctx.breakdown?.categories?.[0]?.key||"核心卖点",second=ctx.upstream?.voiceCenter?.platforms?.[0]?.key||ctx.breakdown?.platforms?.[0]?.key||"核心平台",model=ctx.project?.model||"本品车型",competitors=(ctx.project?.competitors||[]).join(" / ")||"核心竞品";
 const mainModel=(ctx.breakdown?.models||[]).find(x=>x.role==="本品")||{};
 const blocker=mainModel.topBlockers?.[0]?.key||ctx.upstream?.cockpit?.priorityLabels?.find(x=>x.diagnosis==="优先修复")?.label||top;
 const relation=ctx.upstream?.verticalCompetition?.relations?.[0],verticalCopy=relation?`${relation.platform}${relation.period?` ${relation.period}`:""}显示，${model}与${relation.competitor}已形成${relation.status}关系，正向排名${relation.positiveRank||"未上榜"}、反向排名${relation.negativeRank||"未上榜"}。`:`垂媒竞争格局用于校准竞品表达，策略上必须把对比从参数表转成真实场景。`;
 return[`### 核心营销结论`,`${model} 当前不应只追求内容数量，而要把决策驾驶舱里的“${top}”优先级、声量数据中心里的“${second}”主阵地，以及垂媒竞争关系合并成一个清晰购买理由：用可验证证据把“${blocker}”转成试驾和询价的触发点。`,`### 三大数据依据`,`1. 决策驾驶舱：NSR ${(ctx.upstream?.cockpit?.nsr||0).toFixed(2)}，优先标签是“${top}”，说明策略要先处理影响转化的核心认知。\n2. 声量数据中心：主平台是“${second}”，内容表达要围绕高声量平台重写，不做平均投放。\n3. 垂媒竞争格局：${verticalCopy}`,`### 营销动作`,`1. 内容：把“${top}”拆成第三方实测、车主证词、场景短视频和品牌FAQ四类资产。\n2. 竞品：围绕 ${competitors} 做同场景对比，避免参数堆砌，直接回答用户为什么选 ${model}。\n3. 达人：评测型达人负责证据，生活方式达人负责场景，车主/KOC负责评论区信任。`,`### KPI`,`核心标签正向声量提升、负向疑虑评论占比下降、垂媒正向排名提升、竞品对比搜索占比提升、试驾/询价线索提升。`].join("\n\n");
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
 const parts=result.parts?`<details class="model-parts content-mmn-trace"><summary>查看MMN交叉验证过程</summary>${Object.entries(result.parts).filter(([,v])=>v).map(([k,v])=>`<section><b>${{qwen:"MMN主控执行记录",deepseek:"MMN策略质检记录",openai:"MMN外部网关记录",rules:"MMN本地规则记录"}[k]||k}</b>${markdownish(String(v))}</section>`).join("")}${result.errors&&Object.keys(result.errors).length?`<section><b>缺席/错误</b>${Object.entries(result.errors).map(([k,v])=>`<p>${k}: ${v}</p>`).join("")}</section>`:""}</details>`:"";
 box.innerHTML=`<div class="content-mmn-head"><div><b>${contentStrategyState.loading?"MMN正在生成营销策略":"MMN模型输出策略"}</b><span>决策驾驶舱 + 声量数据中心 + 垂媒竞争格局｜内容资产 ${ctx.summary.contentSamples.toLocaleString()} 条｜主类：${ctx.summary.topCategory}</span></div><button type="button" class="primary" id="run-content-mmn-strategy" ${contentStrategyState.loading?"disabled":""}>${contentStrategyState.loading?"生成中…":"生成/刷新MMN策略"}</button></div><div class="content-mmn-output">${markdownish(String(result.text||""))}</div>${contentStrategyState.error?`<p class="empty">模型生成失败，已使用MMN本地策略输出：${contentStrategyState.error}</p>`:""}${parts}`;
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
   sections:["封面","核心结论","当前核心问题","认知资产 / 负债 / 空位","垂媒竞争格局","声量与用户情绪","抖音内容打法","小红书内容打法","达人脚本与内容资产","行动节奏与KPI"]
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
 return[`### 1. 封面`,`${model} 内容资产与营销策略方案\nMMN多模态策略输出｜面向品牌市场与内容增长团队`,`### 2. 核心结论`,`${model} 现在最需要的不是再多铺一层内容，而是围绕“${topLabel}”建立一个能被用户听懂、能被达人复述、能被线索承接的购买理由。策略主线建议锁定：用证据修复“${risk}”，用场景放大已有正向资产。`,`### 3. 当前核心问题`,`用户讨论已经把 ${model} 放进 ${competitorText} 的比较池。问题不只是声量大小，而是用户在比较时还缺少一句稳定答案：为什么在同样预算和同样场景下选择 ${model}。`,`### 4. 认知资产 / 负债 / 空位`,`资产：${topLabel} 可以继续放大。\n负债：${risk} 必须用第三方实测、车主证词和品牌FAQ优先处理。\n空位：把竞品对比从参数表改成家庭、通勤、长途、补能、智能驾驶等真实选择题。`,`### 5. 垂媒竞争格局`,relation.competitor?`${relation.platform||"垂媒"} ${relation.period||"当前周期"}里，${model} 与 ${relation.competitor} 形成“${relation.status||"竞争对比"}”关系。垂媒内容要少讲配置清单，多讲用户为什么会把两台车放在一起比。`:`垂媒侧的任务是校准竞品语境：用户不是在看孤立卖点，而是在用同价位、同场景、同风险感知做选择。`,`### 6. 声量与用户情绪`,`主平台建议优先看 ${platform}。抖音更适合把疑虑拍成短视频验证，小红书更适合沉淀车主账本、场景清单和避坑问答。当前内容资产中抖音与小红书都应服务同一条购买逻辑，而不是各讲各的。`,`### 7. 抖音内容打法`,`${dy?"已有抖音内容可直接归类复用。":"抖音先按自动抓取任务补齐内容资产。"}建议做三类短视频：一个疑虑一个实测、一个竞品一个同场景对比、一个场景一个车主回答。标题要直接回答“值不值得试驾”。`,`### 8. 小红书内容打法`,`${xhs?"已有小红书笔记可进入脚本拆解。":"小红书先围绕真实车主和场景关键词抓取。"}建议做清单型内容：家庭用车账本、通勤体验、长途补能、老人小孩乘坐、智能驾驶接管边界。重点是让用户收藏后能拿去做购买决策。`,`### 9. 达人脚本与内容资产`,`达人组合建议用：${creators}。评测型达人负责证据，生活方式达人负责场景，车主/KOC负责评论区信任。脚本资产要沉淀成可复用结构：开场疑虑、实测证据、竞品对比、适合人群、试驾行动。`,`### 10. 行动节奏与KPI`,`7天内完成内容资产抓取与分类；14天内上线疑虑验证内容；30天内形成达人脚本库和品牌FAQ。\nKPI看五个指标：核心标签正向声量、负向疑虑占比、竞品对比搜索、收藏/评论质量、试驾/询价线索。`].join("\n\n");
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
 return String(text??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function publicMmnText(text){
 return String(text||"").trim().replace(/Qwen|千问/gi,"MMN主控").replace(/DeepSeek/gi,"MMN质检");
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
 const conflictHtml=conflict?`<div class="agent-run-panel ${conflict.status==="aligned"?"pass":"review"}"><div><b>${conflict.label||"MMN交叉复核"}</b><span>任务：${decision.taskType||data.taskType||"strategy"} · 置信度 ${Math.round((conflict.confidence||0)*100)}% · 主分析 ${decision.model||data.model||"MMN"} · 复核 ${decision.reviewer||data.reviewer||"后台critic"}</span></div>${reviewActions}</div>`:"";
 const phaseCopy=isReviewPending?"后台深度复核进行中，初版结果可先使用":data.cached?"命中缓存":data.asyncReview?"已进入后台复核":"策略链路完成";
 box.innerHTML=`<div class="mmn-strategy-chat"><div class="mmn-user-bubble">${escapeHtml(query)}</div><article class="mmn-ai-bubble"><div class="mmn-ai-head"><b>${data.modelLabel||"MMN智能策略"}</b><span>RAG巡检 + ${modelCopy}${cachedCopy} · ${phaseCopy}</span></div>${qaHtml}${conflictHtml}<div class="mmn-ai-content">${markdownish(data.text)}</div>${renderTopicPlanPanel(topicPlan)}<button type="button" class="rag-summary-pill" id="rag-results-toggle"><b>查看引用依据：${evidence.length||references.length} 条</b><span>点击展开本次策略引用了哪些知识</span></button><div class="mmn-engine-signature">该策略由MMN营销引擎输出</div></article></div>`;
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
   `结论先说：${model}现在先不要等模型长推理，先基于已召回依据形成可执行初稿。`,
   `归因分析：当前问题与这些依据相关：${titles}。先把用户最难理解、最容易产生犹豫的点拆成证据，再决定投放和内容节奏。`,
   "策略结论：先做证据解释，再做平台扩散，最后承接市场转化。不要先追求大曝光。",
   "马上怎么做：1. 把问题拆成3条可验证证据；2. 选择最适合的平台表达方式；3. 找真实车主或垂媒补第三方视角；4. 把有效说法写回MMN学习库。",
   "系统正在继续调用模型生成更完整版本，完成后会自动刷新。"
  ].join("\\n\\n")
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
	   toast("本次未发现可蒸馏公开表达；媒体首页和导航页已自动拦截，请用社媒助手导出内容或补充具体文章链接");
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
 }catch(err){
  bloggerSkillState={...bloggerSkillState,error:err.message};
  renderBloggerSkill();
 }
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
 const names=[...new Set([...allProfiles.map(x=>x.blogger_name),...allSamples.map(x=>x.blogger_name)].filter(Boolean))];
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
 const profileBox=document.querySelector("#blogger-skill-profile");
 if(profileBox){
  profileBox.innerHTML=profile?`<div class="founder-profile-head"><span>MMN模型交叉蒸馏</span><b>${profile.blogger_name}｜${profile.vertical_domain}工程 Skill</b></div><dl><dt>能力定位</dt><dd>${profile.professional_background||"公开内容能力蒸馏"}</dd><dt>评价框架</dt><dd>${(profile.evaluation_framework||[]).join(" → ")}</dd><dt>术语体系</dt><dd>${(profile.terminology_system||[]).slice(0,16).join("、")}</dd><dt>判断规则</dt><dd>${(profile.judgment_rules||[]).slice(0,4).map(x=>clip(x,64)).join("；")}</dd><dt>短视频模板</dt><dd>${clip(profile.script_template,160)}</dd><dt>客户报告模板</dt><dd>${clip(profile.report_template,160)}</dd></dl>`:`<p class="empty">导入样本后生成博主能力画像、底盘标签体系和可复用脚本模板。</p>`;
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
  rag.innerHTML=chunks.length?chunks.slice(0,10).map(x=>`<div class="skill-rag-card"><span>${x.metadata?.entity||"底盘工程样本"}</span><b>${x.title}</b><p>${clip(x.body,180)}</p><small>已进入MMN RAG｜来源与导入时间保存在后台</small></div>`).join(""):`<p class="empty">暂无可进入RAG的底盘工程 chunk。</p>`;
 }
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
  bloggerSkillState={...bloggerSkillState,...data};
  mergeDistilledCreatorLibraries(data.creatorLibraries);
  renderBloggerSkill();renderCreatorLibrary();renderStrategyKb();
  toast(`扫描完成：导入 ${data.imported||0} 条样本`);
 }catch(err){toast(`扫描失败：${err.message}`)}
}
async function importBloggerSkillFile(file){
 if(!file)return;
 try{
  toast("正在导入并蒸馏样本…");
  const res=await fetch(`/api/blogger-skill/import-file?edition=${encodeURIComponent(activeEdition())}&filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});
  const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");
  bloggerSkillState={...bloggerSkillState,...json};
  mergeDistilledCreatorLibraries(json.creatorLibraries);
  contentAssetView="bloggerDistill";
  renderBloggerSkill();renderCreatorLibrary();renderStrategyKb();showPage("videos");
  toast(`MMN已完成样本蒸馏与交叉质检：${json.imported||0} 条样本，${json.stats?.ragChunks||0} 条RAG chunk`);
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
    <button type="button" data-dna-action="script" data-dna-id="${escapeAttr(asset.id)}">按TA风格生成脚本</button>
    <button type="button" data-dna-action="incubate" data-dna-id="${escapeAttr(asset.id)}">用TA作为benchmark孵化新账号</button>
    <button type="button" data-dna-action="match" data-dna-id="${escapeAttr(asset.id)}">按客户课题检索适配达人风格</button>
  </div>
  <div class="capability-tags">${(asset.tags||[]).slice(0,16).map(tag=>`<em>${tag}</em>`).join("")}</div>
  <small>${asset.asset_status||"已加入MMN达人库资产候选"}｜${asset.rag_status||"已进入MMN RAG"}｜${asset.transfer_boundary||"仅迁移方法论，不复刻原文"}</small>
 </article>`).join(""):`<p class="empty">还没有达人DNA资产包。导入社媒助手文件或输入账号后，MMN会自动沉淀账号定位、内容母题、选题公式、脚本结构、语言风格和调用场景。</p>`;
 root.querySelectorAll("[data-dna-action]").forEach(btn=>btn.onclick=()=>{
  const asset=(contentCapabilityState.creatorAssets||[]).find(x=>x.id===btn.dataset.dnaId);
  if(asset)toast(dnaText(asset,btn.dataset.dnaAction));
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
 return [`### 核心判断`,`${ctx.project.model} 当前应围绕“${topLabel}”采取“${direction}”。现有依据包含声量样本 ${s.samples||0} 条、正反向关系 ${s.verticalRelations||0} 条、车型判断 ${s.modelJudgments||0} 条。`,`### 内容策略`,`先把可验证证据做成用户能复述的短内容：第三方测试、车主反馈、工程解释和竞品对比。优先平台：${topPlatform}。`,`### 证据链`,`正向分 ${s.positiveScore||0}，负向风险 ${s.negativeScore||0}。如果分数较低，说明当前更多依赖车型库/正反向/RAG资产，需要补充原始声量。`,`### KPI`,`负面占比下降、核心标签正向声量提升、询价/试驾线索改善。`,`### 数据缺口`,gaps.length?gaps.map(x=>`- ${x}`).join("\n"):"- 暂无明显缺口，但仍需复核最新公开数据。"].join("\n\n");
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
  box.innerHTML=markdownish(text);
  if(status)status.textContent=data.ok?`已生成｜${ctx.summary.hasData?"基于现有资产":"基于缺口模板"}`:"模型失败，已用本地规则输出";
 }catch(err){
  box.innerHTML=markdownish(localLearningDraft(ctx));
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
function field(name,label,value,type="text",options=[]){return`<div class="field"><label>${label}</label>${options.length?`<select data-config="${name}">${options.map(o=>`<option ${o===value?"selected":""}>${o}</option>`).join("")}</select>`:`<input data-config="${name}" type="${type}" value="${value}">`}</div>`}
function renderConfig(){
 document.querySelector("#project-form").innerHTML=field("project","项目名称",state.config.project)+field("brand","本品品牌",state.config.brand)+field("model","本品车型",state.config.model,"text",modelOptions())+field("competitor","核心竞品",state.config.competitor)+field("targetIdentity","目标身份",state.config.targetIdentity,"text",Object.keys(identityWeights))+field("budget","营销预算（万元）",state.config.budget,"number");
 document.querySelector("#threshold-form").innerHTML=field("priorityThreshold","行动优先级阈值",state.config.priorityThreshold,"number")+field("riskThreshold","风险预警阈值",state.config.riskThreshold,"number");
 document.querySelectorAll("[data-config]").forEach(el=>{const update=()=>{state.config[el.dataset.config]=el.type==="number"?+el.value:el.value;if(el.dataset.config==="model")applyModelSelection(el.value);save()};el.oninput=update;el.onchange=()=>{update();if(el.dataset.config==="model")render();toast(el.dataset.config==="model"?`已切换为 ${el.value}`:"项目参数已保存")}});
 document.querySelector("#platform-weights").innerHTML=Object.entries(state.platforms).map(([k,v])=>`<div class="weight-item"><b>${k}</b><input type="number" step=".05" value="${v}" data-platform="${k}"></div>`).join("");
 document.querySelectorAll("[data-platform]").forEach(el=>el.onchange=()=>{state.platforms[el.dataset.platform]=+el.value;save();render();toast("平台权重已更新")});
}
function showPage(id){
 if(id==="founder"){contentAssetView="founderDistill";id="videos"}
 if(id==="bloggerskill"){contentAssetView="bloggerDistill";id="videos";loadBloggerSkill()}
 render();
 document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));
 document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===id));
 const activeNav=document.querySelector(`#nav button[data-page="${CSS.escape(id)}"]`);
 if(activeNav){
  const group=activeNav.closest("details.nav-section");
  if(group)group.open=true;
 }
 document.querySelector("#page-title").textContent=pageNames[id]||"内容资产中心";
}
function toast(text){const t=document.querySelector("#toast");t.textContent=text;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),1700)}
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
document.querySelectorAll("[data-edition]").forEach(b=>b.onclick=()=>setEdition(b.dataset.edition));
document.querySelectorAll("[data-page-jump]").forEach(b=>b.onclick=()=>showPage(b.dataset.pageJump));
document.addEventListener("click",e=>{const btn=e.target.closest("[data-file-target]");if(!btn||btn.disabled)return;const input=document.getElementById(btn.dataset.fileTarget);if(input&&!input.disabled)input.click()});
document.querySelectorAll("#map-filters button").forEach(b=>b.onclick=()=>{mapFilter=b.dataset.filter;render()});
document.querySelector("#map-limit").onchange=e=>{mapLimit=+e.target.value;render()};
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
const contentCapabilityFile=document.querySelector("#content-capability-file");if(contentCapabilityFile)contentCapabilityFile.onchange=async e=>{const file=e.target.files[0];await importContentCapabilityFile(file);e.target.value=""};
const contentCapabilitySearchInput=document.querySelector("#content-capability-search");if(contentCapabilitySearchInput)contentCapabilitySearchInput.oninput=e=>{contentCapabilitySearch=e.target.value.trim();clearTimeout(contentCapabilitySearchInput._t);contentCapabilitySearchInput._t=setTimeout(loadContentCapabilityKb,260)};
const contentCapabilityClear=document.querySelector("#content-capability-clear");if(contentCapabilityClear)contentCapabilityClear.onclick=()=>{contentCapabilitySelectedTags=[];contentCapabilitySearch="";const input=document.querySelector("#content-capability-search");if(input)input.value="";loadContentCapabilityKb()};
const contentCapabilityDistill=document.querySelector("#content-capability-distill");if(contentCapabilityDistill)contentCapabilityDistill.onclick=distillContentCapabilityAccount;
document.querySelectorAll("[data-content-view]").forEach(b=>b.onclick=()=>{contentAssetView=b.dataset.contentView;creatorFilter="all";creatorSearch="";const input=document.querySelector("#creator-search");if(input)input.value="";if(contentAssetView==="bloggerDistill")loadBloggerSkill();if(contentAssetView==="contentCapability")loadContentCapabilityKb();renderVideos();if(contentAssetView==="founderDistill")renderFounderDistill();if(contentAssetView==="bloggerDistill")renderBloggerSkill();if(contentAssetView==="contentCapability")renderContentCapabilityKb()});
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
document.querySelector("#login-submit").onclick=async e=>{e.preventDefault();const f=document.querySelector("#login-form");try{const data=await api("/api/login",{method:"POST",body:JSON.stringify({org:f.elements.org.value,name:f.elements.name.value,email:f.elements.email.value})});saveSession(data.session);document.querySelector("#login-dialog").close();await Promise.all([loadServerLearnings(),loadWorkspace()]);toast(`已进入 ${data.session.org}`)}catch(err){toast(`登录失败：${err.message}`)}};
document.querySelector("#trend-dialog-close").onclick=()=>document.querySelector("#trend-dialog").close();
document.querySelector("#asset-benchmark-dialog-close").onclick=()=>document.querySelector("#asset-benchmark-dialog").close();
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
  if(!isDemoState&&baseRows.length&&dataset.config?.competitor){
   const comps=new Set(String(state.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean));
   String(dataset.config.competitor||"").split("/").map(x=>x.trim()).filter(Boolean).forEach(x=>comps.add(x));
   [...new Set(baseRows.map(r=>r[0]).filter(Boolean))].forEach(x=>{if(x!==state.config.model)comps.add(x)});
   state.config.competitor=[...comps].filter(x=>x!==state.config.model).join(" / ");
  }
  ensureModelIdentities(state.models||[]);
  save();render();showPage("dashboard");
  toast(`已导入 ${dataset.sourceRowCount||incomingRows.length} 条原始记录，聚合为 ${incomingRows.length} 组，结果已刷新`);
  return;
 }
 state=dataset;
 // 替换导入必须同步重置工作台上下文，避免旧项目的品牌下拉框覆盖新导入车型。
 dashBrandOpen=brandForDisplay(state.config?.model);
 dashboardPlatformFilter="all";
 summaryDashboardModels=[...(state.models||[])];
 ensureModelIdentities(state.models||[]);save();render();showPage("dashboard");toast(`已导入 ${state.rows.length} 行，结果已刷新`);
}
document.querySelector("#xlsx-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;try{await importDataFile(file,{merge:/\.csv$/i.test(file.name)})}catch(err){toast(`数据导入失败：${err.message}`)}finally{e.target.value=""}};
document.querySelector("#vertical-xlsx-file").onchange=async e=>{const file=e.target.files[0];if(!file)return;toast("正在导入垂媒排名 Excel…");try{const res=await fetch(`/api/import-vertical-xlsx?filename=${encodeURIComponent(file.name)}`,{method:"POST",headers:authHeaders(),body:await file.arrayBuffer()});const json=await res.json();if(!json.ok)throw new Error(json.error||"导入失败");const sourceId=json.dataset.source;verticalState.sources=[...(verticalState.sources||[]).filter(x=>x.source!==sourceId),{source:sourceId,platform:json.dataset.platform,count:json.dataset.count,importedAt:new Date().toISOString(),remembered:json.dataset.remembered}];verticalState.items=[...(verticalState.items||[]).filter(x=>x.source!==sourceId),...json.dataset.items];verticalState.assetSummary=json.dataset.assetSummary||verticalState.assetSummary;if(json.dataset.knowledgeItems?.length)mergeStrategyKnowledge(json.dataset.knowledgeItems);if(!verticalState.selectedModel)verticalState.selectedModel=json.dataset.models?.[0]||"";saveVerticalState();renderVertical();renderStrategyKb();showPage("vertical");const asset=json.dataset.assetSummary;const kCount=json.dataset.knowledgeItems?.length||0;toast(asset?`已导入 ${json.dataset.platform} ${json.dataset.count} 条，生成 ${kCount} 条训练知识，资产库累计 ${asset.modelCount} 个车型`:`已导入 ${json.dataset.platform} ${json.dataset.count} 条正反向排名`)}catch(err){toast(`垂媒数据导入失败：${err.message}`)}finally{e.target.value=""}};
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
function startAppDataLoads(){
 loadAiStatus();
	 loadSalesMarquee();
	 loadFounderArchives();
	 loadBloggerSkill();
	 loadContentCapabilityKb();
	 loadSocialPluginStatus();
 if(session){loadServerLearnings();loadWorkspace()}else renderWorkspace();
}
render();
initCloudLoginGate().then(ok=>{if(ok)startAppDataLoads()});
