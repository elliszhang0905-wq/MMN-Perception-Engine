const { chromium } = require("playwright");

const baseUrl = process.env.MMN_URL || "http://localhost:8765/";
const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const runtimeErrors = [];

  page.on("pageerror", error => runtimeErrors.push(String(error.message || error)));
  page.on("console", message => {
    if (message.type() === "error") runtimeErrors.push(message.text());
  });

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(800);

  const checks = [];
  const add = (name, pass, detail = "") => checks.push({ name, pass: Boolean(pass), detail });

  const dashboard = await page.evaluate(() => ({
    project: document.querySelector("#dash-project")?.textContent.trim() || "",
    brand: document.querySelector("#dash-brand-select")?.value || "",
    model: document.querySelector("#dash-model-select")?.value || "",
    competitor: document.querySelector("#dash-competitor")?.textContent.trim() || "",
    samples: document.querySelector("#dash-samples")?.textContent.trim() || "",
    importButtons: [...document.querySelectorAll(".dashboard-import button")].map(button => button.textContent.trim()),
    appVersion: [...document.scripts].map(script => script.src).find(src => src.includes("app.js")) || ""
  }));

  add("dashboard project renders", dashboard.project.length > 0, dashboard.project);
  add("dashboard brand renders", dashboard.brand.length > 0, dashboard.brand);
  add("dashboard model renders", dashboard.model.length > 0, dashboard.model);
  add("dashboard sample size renders", /\d/.test(dashboard.samples), dashboard.samples);
  add("dashboard import actions are simplified", dashboard.importButtons.length === 2 && dashboard.importButtons[0] === "导入数据" && dashboard.importButtons[1] === "查看数据表", dashboard.importButtons.join(" / "));
  add("dashboard uses cache-busted app bundle", /app\.js\?v=beta-1\.01-strategy-options-5$/.test(dashboard.appVersion), dashboard.appVersion);
  const sourceParser = await page.evaluate(() => {
    if (typeof window.parseOpportunityCompetitorSources !== "function") return { available: false, count: 0, errors: -1 };
    const result=window.parseOpportunityCompetitorSources("小米YU7 https://www.xiaomiev.com/xiaomi/yu7");
    return { available: true, count: result.items.length, errors: result.errors.length };
  });
  add("competitor official source parser is available in the browser", sourceParser.available && sourceParser.count === 1 && sourceParser.errors === 0, JSON.stringify(sourceParser));

  const competitorSourceInput = page.locator("#opportunity-official-sources");
  const competitorSourceBefore = await page.evaluate(() => {
    const input=document.querySelector("#opportunity-official-sources"),rect=input?.getBoundingClientRect();
    return {label:document.querySelector("#opportunity-official-label")?.textContent.trim()||"",helper:input?.closest(".opportunity-source-field")?.querySelector("small")?.textContent.trim()||"",height:rect?.height||0,visible:Boolean(rect&&rect.width>0&&rect.height>0)};
  });
  await competitorSourceInput.fill("小米YU7|https://example.com/yu7");
  await page.locator('#map-filters button[data-filter="持续放大"]').click();
  const competitorSourceAfter = await page.locator("#opportunity-official-sources").inputValue();
  await page.locator('#map-filters button[data-filter="all"]').click();
  add("competitor official source field is labeled, visible, and survives dashboard rerenders", competitorSourceBefore.visible && competitorSourceBefore.height >= 60 && competitorSourceBefore.label.includes("竞品官网产品页") && competitorSourceBefore.helper.includes("一行一个竞品") && competitorSourceAfter === "小米YU7|https://example.com/yu7", JSON.stringify({before:competitorSourceBefore,after:competitorSourceAfter}));

  await page.route("**/api/opportunity-map/generate", route => route.fulfill({
    status: 202,
    contentType: "application/json",
    body: JSON.stringify({ok:true,jobId:"release-gate-job",job:{jobId:"release-gate-job",status:"queued",stage:"official_sources",progress:12,message:"正在核验竞品官网",elapsedSeconds:0}}),
  }));
  await page.route("**/api/opportunity-map/jobs/release-gate-job", async route => {
    await new Promise(resolve => setTimeout(resolve, 700));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ok:true,job:{jobId:"release-gate-job",status:"completed",stage:"completed",progress:100,message:"机会地图已完成双模型交叉验证",elapsedSeconds:1,result:{ok:true,runId:"release-gate-job",status:"manual_required",document:{facts:[],manualReviewItems:[]},competitorSources:[],opportunities:[],validation:{items:[],manualItems:[]},qa:{manualCount:0,evidenceCount:0}}}}),
    });
  });
  await page.evaluate(() => {
    opportunityEvidenceState.document={documentId:"release-gate-doc",facts:[],manualReviewItems:[]};
    opportunityEvidenceState.result=null;
    opportunityEvidenceState.error="";
    renderOpportunityEvidence();
  });
  await page.locator("#opportunity-official-sources").fill("小米YU7 https://www.xiaomiev.com/xiaomi/yu7");
  await page.locator("#opportunity-generate-button").click();
  await page.waitForTimeout(180);
  const opportunityLoading = await page.evaluate(() => {
    const button=document.querySelector("#opportunity-generate-button");
    const progress=document.querySelector(".opportunity-job-progress");
    return {
      buttonText:button?.textContent.trim()||"",
      disabled:Boolean(button?.disabled),
      ariaBusy:document.querySelector("#opportunity-evidence-workbench")?.getAttribute("aria-busy")||"",
      live:progress?.getAttribute("aria-live")||"",
      text:progress?.textContent.trim()||"",
    };
  });
  add("opportunity generation immediately exposes async dual-model progress", opportunityLoading.disabled && /运行中|生成中/.test(opportunityLoading.buttonText) && opportunityLoading.ariaBusy === "true" && opportunityLoading.live === "polite" && /官网|旗舰模型|交叉验证/.test(opportunityLoading.text), JSON.stringify(opportunityLoading));
  await page.waitForTimeout(750);
  await page.unroute("**/api/opportunity-map/generate");
  await page.unroute("**/api/opportunity-map/jobs/release-gate-job");
  await page.evaluate(() => {
    opportunityEvidenceState.result=null;
    opportunityEvidenceState.job=null;
    opportunityEvidenceState.loading=false;
    opportunityEvidenceState.error="";
    opportunityEvidenceState.document={documentId:"release-gate-review-doc",filename:"产品白皮书.pdf",factCount:2,manualReviewCount:2};
    render();
  });
  const hasManualReviewDialog = await page.locator("#opportunity-review-dialog").count() > 0;
  let manualReviewUi = {dialog:false,items:0,hasActions:false,ariaLive:false,saved:false,summaryGuard:false,recheckMap:false};
  if (hasManualReviewDialog) {
    let savedReviewBody=null,recheckRequestBody=null;
    const reviewQueueItems=[
      ...Array.from({length:80},(_,index)=>({id:`review-${index+1}`,factId:`fact-${index+1}`,type:"fact_alignment",title:`产品事实 ${index+1}`,claim:index===0?"座椅与配置升级":`待确认产品事实 ${index+1}`,candidateLabels:index===0?["舒适性","配置"]:["配置","外观"],reasons:["该段同时命中多个统一标签"],evidence:{pageNo:index+1,sourceRef:"产品白皮书.pdf",excerpt:index===0?"座椅与配置升级":`待确认产品事实 ${index+1}`},status:"pending"})),
      {id:"review-summary",factId:"",type:"fact_alignment_summary",title:"未归类文本",claim:"部分文本未归类",candidateLabels:[],reasons:["证据不足"],evidence:{sourceRef:"产品白皮书.pdf",excerpt:"部分文本未归类"},status:"pending"},
    ];
    await page.route("**/api/opportunity-map/manual-reviews?*", route => route.fulfill({
      status:200,
      contentType:"application/json",
      body:JSON.stringify({ok:true,document:{documentId:"release-gate-review-doc",filename:"产品白皮书.pdf"},counts:{total:81,pending:81,pendingRecheck:0,needsEvidence:0,processed:0,blocking:81},items:reviewQueueItems}),
    }));
    await page.route("**/api/opportunity-map/manual-reviews", async route => {
      savedReviewBody=route.request().postDataJSON();
      const updatedItems=reviewQueueItems.map(item=>item.id==="review-1"?{...item,status:"corrected_pending_recheck",decision:{action:"corrected",selectedLabel:"舒适性",note:"第12页核心为座椅舒适体验"}}:item);
      await route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({ok:true,savedCount:1,recheckRequired:true,queue:{ok:true,document:{documentId:"release-gate-review-doc",filename:"产品白皮书.pdf"},counts:{total:81,pending:80,pendingRecheck:1,needsEvidence:0,processed:0,blocking:81},items:updatedItems}})});
    });
    await page.locator("#opportunity-review-button").click();
    await page.waitForTimeout(120);
    manualReviewUi = await page.evaluate(() => ({
      dialog:Boolean(document.querySelector("#opportunity-review-dialog")?.open),
      items:document.querySelectorAll("[data-review-item-id]").length,
      hasActions:["accepted","corrected","rejected","needs_evidence"].every(action=>Boolean(document.querySelector(`[data-review-action="${action}"]`))),
      ariaLive:document.querySelector("#opportunity-review-counts")?.getAttribute("aria-live")==="polite",
      queueScrollable:(()=>{const list=document.querySelector("#opportunity-review-list"),dialog=document.querySelector("#opportunity-review-dialog");return Boolean(list&&dialog&&list.scrollHeight>list.clientHeight&&list.clientHeight<dialog.clientHeight)})(),
      assistiveTextHidden:(()=>{const node=document.querySelector(".opportunity-review-check .sr-only"),rect=node?.getBoundingClientRect();return Boolean(node&&rect&&rect.width<=1&&rect.height<=1&&getComputedStyle(node).position==="absolute")})(),
    }));
    await page.locator('[data-review-action="corrected"]').click();
    await page.locator("#opportunity-review-label").selectOption("舒适性");
    await page.locator("#opportunity-review-note").fill("第12页核心为座椅舒适体验");
    await page.locator("#opportunity-review-save").click();
    await page.waitForFunction(() => !document.querySelector("#opportunity-review-recheck")?.hidden);
    await page.locator('[data-review-item-id="review-summary"]').click();
    const reviewSavedState=await page.evaluate(() => ({
      pendingRecheck:document.querySelector("#opportunity-review-counts")?.textContent.includes("待复核 1"),
      acceptedDisabled:Boolean(document.querySelector('[data-review-action="accepted"]')?.disabled),
      correctedDisabled:Boolean(document.querySelector('[data-review-action="corrected"]')?.disabled),
      summaryNotice:document.querySelector(".opportunity-review-summary-notice")?.textContent||"",
    }));
    manualReviewUi.saved=Boolean(savedReviewBody&&savedReviewBody.action==="corrected"&&savedReviewBody.selectedLabel==="舒适性"&&savedReviewBody.note);
    manualReviewUi.summaryGuard=reviewSavedState.acceptedDisabled&&reviewSavedState.correctedDisabled&&reviewSavedState.summaryNotice.includes("不能直接采纳或修正");

    await page.route("**/api/opportunity-map/generate", async route => {
      recheckRequestBody=route.request().postDataJSON();
      await route.fulfill({status:202,contentType:"application/json",body:JSON.stringify({ok:true,jobId:"release-gate-recheck-job",job:{jobId:"release-gate-recheck-job",status:"queued",stage:"official_sources",progress:5,message:"正在复核人工修正",elapsedSeconds:0}})});
    });
    await page.route("**/api/opportunity-map/jobs/release-gate-recheck-job", route => route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({ok:true,job:{jobId:"release-gate-recheck-job",status:"completed",stage:"completed",progress:100,message:"地图已更新",elapsedSeconds:1,result:{ok:true,runId:"release-gate-recheck-job",status:"partial_completed",document:{documentId:"release-gate-review-doc",filename:"产品白皮书.pdf",factCount:2,manualReviewCount:1,manualReviewItems:[{type:"fact_alignment_summary"}]},competitorSources:[{model:"小米YU7",status:"verified",finalUrl:"https://example.com/yu7"}],competitorProducts:[{model:"小米YU7",status:"verified",finalUrl:"https://example.com/yu7",coreProductStrengths:[{label:"舒适性",claim:"前后排座椅通风加热",factStrength:0.85}]}],opportunities:[{label:"舒适性",category:"seize",categoryLabel:"抢占空位",opportunityScore:72,mapX:0.3,mapY:5,recognition:0.7,heat:0.5,factStrength:0.85,evidenceStatus:"aligned"}],validation:{items:[{label:"舒适性",evidenceStatus:"aligned"}],manualItems:[]},qa:{manualCount:1,verifiedLabelCount:1,evidenceCount:3}}}})}));
    await page.locator("#opportunity-review-recheck").click();
    await page.waitForFunction(() => document.querySelector("#opportunity-map .bubble")?.textContent.trim()==="舒适性");
    const recheckMapState=await page.evaluate(() => ({
      dialogOpen:Boolean(document.querySelector("#opportunity-review-dialog")?.open),
      bubble:document.querySelector("#opportunity-map .bubble")?.textContent.trim()||"",
      bubbleTitle:document.querySelector("#opportunity-map .bubble")?.getAttribute("title")||"",
      seizeFilter:[...document.querySelectorAll('#map-filters button')].find(button=>button.dataset.filter==="抢占空位")?.textContent.trim()||"",
      partialStatus:[...document.querySelectorAll(".opportunity-evidence-status span.ok")].some(node=>node.textContent.includes("已验证 1 个标签")),
      competitorCard:document.querySelector('[data-opportunity-competitor-model="小米YU7"]')?.textContent.trim()||"",
    }));
    const competitorCard=page.locator('[data-opportunity-competitor-model="小米YU7"]');
    const competitorCardCount=await competitorCard.count();
    if(competitorCardCount===1)await competitorCard.click();
    await page.waitForFunction(() => document.querySelector(".opportunity-competitor-popover")?.textContent.includes("前后排座椅通风加热"));
    const competitorPopover=await page.evaluate(() => document.querySelector(".opportunity-competitor-popover")?.textContent.trim()||"");
    manualReviewUi.recheckMap=Boolean(recheckRequestBody?.documentId==="release-gate-review-doc"&&!recheckMapState.dialogOpen&&recheckMapState.bubble==="舒适性"&&recheckMapState.bubbleTitle.includes("购买影响 5.0")&&recheckMapState.seizeFilter.endsWith("1")&&recheckMapState.partialStatus&&recheckMapState.competitorCard.includes("官网已核验")&&competitorCardCount===1&&competitorPopover.includes("舒适性")&&competitorPopover.includes("前后排座椅通风加热"));
    await page.unroute("**/api/opportunity-map/generate");
    await page.unroute("**/api/opportunity-map/jobs/release-gate-recheck-job");
    await page.unroute("**/api/opportunity-map/manual-reviews");
    await page.unroute("**/api/opportunity-map/manual-reviews?*");
    await page.evaluate(() => {opportunityEvidenceState.result=null;opportunityEvidenceState.job=null;opportunityEvidenceState.loading=false;opportunityEvidenceState.error="";render()});
  }
  add("manual review opens a structured evidence queue instead of a yes-no prompt", manualReviewUi.dialog && manualReviewUi.items===81 && manualReviewUi.hasActions && manualReviewUi.ariaLive && manualReviewUi.queueScrollable && manualReviewUi.assistiveTextHidden && manualReviewUi.saved && manualReviewUi.summaryGuard, JSON.stringify(manualReviewUi));
  add("manual correction recheck synchronizes the validated label and map position", manualReviewUi.recheckMap, JSON.stringify(manualReviewUi));

  let executionPost=null,monitoringPost=null;
  await page.route("**/api/cockpit/execution-cycles", async route => {
    executionPost=route.request().postDataJSON();
    await route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({ok:true,cycle:{id:"release-cycle-1",runId:"release-decision-run",label:"舒适性",status:"planned",plan:{competitorModel:"竞品A",platform:"小红书",action:"场景对比",contentScenario:"多人出行舒适对比",selectedOptionId:"scenario_compete",selectedOption:{id:"scenario_compete",title:"场景对比切入",action:"场景对比",competitorModel:"竞品A",platform:"小红书",contentScenario:"多人出行舒适对比"},options:[{id:"comparison_occupy",title:"对比占位",action:"对比占位",contentScenario:"长途乘坐舒适体验"},{id:"scenario_compete",title:"场景对比切入",action:"场景对比",contentScenario:"多人出行舒适对比"},{id:"search_answer",title:"对比搜索承接",action:"搜索承接",contentScenario:"对比搜索问答与购买理由解释"}]},monitoring:{}}})});
  });
  await page.route("**/api/cockpit/execution-cycles/monitoring", async route => {
    monitoringPost=route.request().postDataJSON();
    await route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({ok:true,cycle:{id:"release-cycle-1",runId:"release-decision-run",label:"舒适性",status:"feedback_recorded",plan:{competitorModel:"竞品A",platform:"小红书",action:"场景对比",contentScenario:"多人出行舒适对比",selectedOptionId:"scenario_compete",selectedOption:{id:"scenario_compete",title:"场景对比切入",action:"场景对比",competitorModel:"竞品A",platform:"小红书",contentScenario:"多人出行舒适对比"}},monitoring:{volume:120,interaction:360,nsr:.42,observation:"收藏与评论高于预期"},feedbackSignal:{model:"智己LS8",attribute:"舒适性",platform:"小红书",volume:120,interaction:360,nsr:.42}}})});
  });
  await page.evaluate(() => {
    opportunityEvidenceState.result={ok:true,runId:"release-decision-run",status:"partial_completed",document:{documentId:"release-gate-decision-doc",facts:[],manualReviewItems:[]},competitorSources:[],verticalEvidence:[{id:"vertical-1",platform:"汽车之家",period:"2026-06",competitor:"竞品A",claim:"汽车之家 2026-06：本品车型 对比 竞品A，正向第 1，反向第 5。"}],opportunities:[{label:"舒适性",category:"seize",categoryLabel:"抢占空位",evidenceStatus:"aligned",commonEvidenceIds:["fact-comfort"],leadCompetitorModel:"竞品A",factStrength:.86,opportunityScore:72}],executionRecommendations:[{label:"舒适性",category:"seize",categoryLabel:"抢占空位",competitorModel:"竞品A",platform:"小红书",action:"对比占位",contentScenario:"长途乘坐舒适体验",evidenceIds:["fact-comfort"],recommendedOptionId:"comparison_occupy",options:[{id:"comparison_occupy",title:"对比占位",action:"对比占位",competitorModel:"竞品A",platform:"小红书",contentScenario:"长途乘坐舒适体验",description:"以同级对比突出舒适优势。"},{id:"scenario_compete",title:"场景对比切入",action:"场景对比",competitorModel:"竞品A",platform:"小红书",contentScenario:"多人出行舒适对比",description:"以多人出行场景做舒适对比。"},{id:"search_answer",title:"对比搜索承接",action:"搜索承接",competitorModel:"竞品A",platform:"小红书",contentScenario:"对比搜索问答与购买理由解释",description:"承接舒适性对比搜索。"}]}],qa:{manualCount:1,verifiedLabelCount:1,evidenceCount:4}};
    cockpitDecisionState={cycles:[],loading:false,error:""};
    render();
  });
  const cockpitDecisionBefore=await page.evaluate(() => ({
    chainGroups:[...document.querySelectorAll("#cockpit-evidence-chain h3")].map(node=>node.textContent.trim()),
    chainStages:[...document.querySelectorAll("#cockpit-evidence-chain li b")].map(node=>node.textContent.trim()),
    verticalStage:[...document.querySelectorAll("#cockpit-evidence-chain li")].find(node=>node.textContent.includes("垂媒交叉验证"))?.textContent.replace(/\s+/g," ").trim()||"",
    card:document.querySelector(".cockpit-decision-card")?.textContent.replace(/\s+/g," ").trim()||"",
    execute:Boolean(document.querySelector('[data-cockpit-execute="舒适性"]')),
    strategyOptions:[...document.querySelectorAll("[data-cockpit-option]")].map(input=>input.value),
  }));
  await page.locator('[data-cockpit-execute="舒适性"]').click();
  const selectionGuard=await page.evaluate(() => ({toast:document.querySelector("#toast")?.textContent.trim()||""}));
  const executionBlockedBeforeSelection=executionPost===null;
  await page.locator('[data-cockpit-option="scenario_compete"]').check();
  await page.locator('[data-cockpit-execute="舒适性"]').click();
  await page.locator("[data-cockpit-volume]").fill("120");
  await page.locator("[data-cockpit-interaction]").fill("360");
  await page.locator("[data-cockpit-nsr]").fill("0.42");
  await page.locator("[data-cockpit-observation]").fill("收藏与评论高于预期");
  await page.locator('[data-cockpit-monitor="release-cycle-1"]').click();
  await page.waitForFunction(() => document.querySelector(".cockpit-decision-card header em")?.textContent.trim()==="已回流");
  const cockpitDecisionAfter=await page.evaluate(() => ({
    feedback:[...document.querySelectorAll("#cockpit-evidence-chain li")].some(node=>node.textContent.includes("结果监测 → 证据回流")&&node.textContent.includes("1 项结果")),
    status:document.querySelector(".cockpit-decision-card header em")?.textContent.trim()||"",
    card:document.querySelector(".cockpit-decision-card")?.textContent.replace(/\s+/g," ").trim()||"",
  }));
  const cockpitDecisionChecks={chainGroups:cockpitDecisionBefore.chainGroups.join("|")==="社会传播证据|产品事实验证|决策执行闭环",crossValidation:cockpitDecisionBefore.chainStages.includes("双旗舰交叉验证"),feedbackStage:cockpitDecisionBefore.chainStages.includes("结果监测 → 证据回流"),verticalEvidence:cockpitDecisionBefore.verticalStage.includes("已纳入 1 条匹配的正反向关系"),decisionFields:["贴靠车型","竞品A","优先平台","垂媒交叉验证","汽车之家 · 2026-06"].every(text=>cockpitDecisionBefore.card.includes(text)),execute:cockpitDecisionBefore.execute,strategyOptions:cockpitDecisionBefore.strategyOptions.join("|")==="comparison_occupy|scenario_compete|search_answer",selectionGuard:executionBlockedBeforeSelection&&selectionGuard.toast.includes("选择策略选项"),selectedRequest:executionPost?.runId==="release-decision-run"&&executionPost?.label==="舒适性"&&executionPost?.optionId==="scenario_compete",monitoringRequest:monitoringPost?.volume==="120"&&monitoringPost?.interaction==="360"&&monitoringPost?.nsr==="0.42",feedback:cockpitDecisionAfter.feedback&&cockpitDecisionAfter.status==="已回流",selectedDisplay:cockpitDecisionAfter.card.includes("场景对比切入")};
  add("cockpit exposes Social evidence chain and Rule execution feedback without moving the main layout", Object.values(cockpitDecisionChecks).every(Boolean), JSON.stringify({cockpitDecisionChecks,cockpitDecisionBefore,cockpitDecisionAfter,selectionGuard,executionBlockedBeforeSelection,executionPost,monitoringPost}));
  await page.unroute("**/api/cockpit/execution-cycles");
  await page.unroute("**/api/cockpit/execution-cycles/monitoring");
  await page.evaluate(() => {opportunityEvidenceState.result=null;cockpitDecisionState={cycles:[],loading:false,error:""};render()});

  const opportunityQuadrants = await page.evaluate(() => {
    const clustered = [
      ...Array.from({length:6},(_,index)=>({label:`右上${index}`,left:50.5,bottom:50.5,quadrantX:"right",quadrantY:"high",priority:20-index,w:92,h:30})),
      ...Array.from({length:6},(_,index)=>({label:`左下${index}`,left:49.5,bottom:49.5,quadrantX:"left",quadrantY:"low",priority:10-index,w:92,h:30})),
    ];
    const placed=layoutBubbles(clustered,860,380);
    const rightHigh=placed.filter(item=>item.quadrantX==="right").every(item=>item.x>50&&item.y>50);
    const leftLow=placed.filter(item=>item.quadrantX==="left").every(item=>item.x<50&&item.y<50);
    const noOverlap=placed.every((item,index)=>placed.slice(index+1).every(other=>Math.abs(item._x-other._x)>(item.w+other.w)/2+4||Math.abs(item._y-other._y)>(item.h+other.h)/2+4));
    return {rightHigh,leftLow,noOverlap,placed:placed.map(item=>({label:item.label,x:Number(item.x.toFixed(2)),y:Number(item.y.toFixed(2))}))};
  });
  add("opportunity bubble collision layout preserves the validated axis quadrant", opportunityQuadrants.rightHigh && opportunityQuadrants.leftLow && opportunityQuadrants.noOverlap, JSON.stringify(opportunityQuadrants));

  const dashboardKpis = await page.evaluate(() => {
    const node = document.querySelector(".dashboard-kpis");
    return { hidden: node?.hidden === true, height: node?.getBoundingClientRect().height || 0 };
  });
  add("dashboard does not display generic KPI cards", dashboardKpis.hidden && dashboardKpis.height === 0, JSON.stringify(dashboardKpis));

  const dashboardText = await page.locator(".dashboard-import").innerText();
  add("dashboard does not expose file format wording", !/Excel|CSV|模板/.test(dashboardText), dashboardText);

  const emotionQuadrants = await page.locator("#dashboard-emotion-quadrant .emotion-quadrant-cell").count().catch(() => 0);
  const cognitionRows = await page.locator("#dashboard-cognition-table tbody tr").count().catch(() => 0);
  add("dashboard emotion quadrant renders", emotionQuadrants === 4, String(emotionQuadrants));
  add("dashboard cognition panel renders", cognitionRows > 0, String(cognitionRows));

  const dataPanelLayout = await page.evaluate(() => {
    const workbench = document.querySelector(".dashboard-workbench")?.getBoundingClientRect();
    const panel = document.querySelector(".dashboard-data-panel")?.getBoundingClientRect();
    return { workbenchWidth: workbench?.width || 0, panelWidth: panel?.width || 0 };
  });
  add("dashboard data preview spans the full workbench width", dataPanelLayout.workbenchWidth > 0 && dataPanelLayout.panelWidth / dataPanelLayout.workbenchWidth > .98, JSON.stringify(dataPanelLayout));

  const dataContext = await page.evaluate(() => {
    const title=document.querySelector(".dashboard-data-title-copy h2"),rect=title?.getBoundingClientRect();
    return {
      title:title?.textContent.trim()||"",titleHeight:rect?.height||0,fontSize:parseFloat(getComputedStyle(title).fontSize)||0,
      own:document.querySelector("#dashboard-data-context .own-model b")?.textContent.trim()||"",
      references:document.querySelector("#dashboard-data-context .reference-models b")?.textContent.trim()||"",
      time:document.querySelector("#dashboard-data-context .time-dimension b")?.textContent.trim()||"",
      dimension:document.querySelector("#dashboard-data-context .data-dimension b")?.textContent.trim()||"",
      labels:document.querySelector("#dashboard-data-context .label-dimension b")?.textContent.trim()||""
    };
  });
  add("dashboard data header is single-line and exposes analysis context", dataContext.titleHeight <= dataContext.fontSize * 1.7 && dataContext.own && dataContext.references && dataContext.time && dataContext.dimension.includes("情绪") && dataContext.labels && !/\.xlsx|\.csv/i.test(Object.values(dataContext).join(" ")), JSON.stringify(dataContext));

  const platformFilter = page.locator("#dashboard-platform-filter");
  const platformOptions = await platformFilter.locator("option").allTextContents().catch(() => []);
  let platformFilterResult = { selected: "", quadrants: 0, tagCount: 0, uniqueTagCount: 0, maxTags: 0 };
  if (platformOptions.length > 1) {
    await platformFilter.selectOption({ index: 1 });
    platformFilterResult = await page.evaluate(() => {
      const counts=[...document.querySelectorAll("#dashboard-emotion-quadrant .emotion-tag-list")].map(list => list.querySelectorAll(".emotion-tag").length);
      const labels=[...document.querySelectorAll("#dashboard-emotion-quadrant .emotion-tag b")].map(node=>node.textContent.trim());
      return {selected:document.querySelector("#dashboard-platform-filter")?.value||"",quadrants:document.querySelectorAll("#dashboard-emotion-quadrant .emotion-quadrant-cell").length,tagCount:labels.length,uniqueTagCount:new Set(labels).size,maxTags:Math.max(...counts)};
    });
  }
  add("dashboard platform never duplicates labels to fill empty emotion quadrants", platformOptions.includes("全部平台") && platformFilterResult.selected && platformFilterResult.quadrants === 4 && platformFilterResult.tagCount > 0 && platformFilterResult.tagCount === platformFilterResult.uniqueTagCount && platformFilterResult.maxTags <= 3, JSON.stringify({ platformOptions, platformFilterResult }));

  const singleLabelQuadrants = await page.evaluate(() => {
    const result = emotionQuadrantData([["测试车型", "本品", "抖音", "整体口碑", "总体口碑", "认可", "目标核心人群", "无", 100, 4, 1, 4]]);
    const labels = emotionQuadrantDefinitions.flatMap(quadrant => (result.get(quadrant.key) || []).map(item => item.label));
    return { tagCount: labels.length, uniqueTagCount: new Set(labels).size };
  });
  add("a single emotion label appears in only one quadrant", singleLabelQuadrants.tagCount === 1 && singleLabelQuadrants.uniqueTagCount === 1, JSON.stringify(singleLabelQuadrants));

  const firstEmotionTag = page.locator("#dashboard-emotion-quadrant .emotion-tag").first();
  if (await firstEmotionTag.count()) await firstEmotionTag.click();
  const emotionDialog = await page.evaluate(() => ({
    open: document.querySelector("#emotion-label-dialog")?.open || false,
    title: document.querySelector("#emotion-label-dialog-title")?.textContent.trim() || "",
    hasTrack: document.querySelectorAll("#emotion-label-dialog .emotion-competitor-track").length > 0,
    values: [...document.querySelectorAll("#emotion-label-dialog .emotion-competitor-row>strong")].map(node => node.textContent.trim()),
    text: document.querySelector("#emotion-label-dialog-body")?.textContent.trim() || ""
  }));
  add("emotion label bubble only shows comparable percentages", emotionDialog.open && emotionDialog.hasTrack && emotionDialog.values.length > 0 && emotionDialog.values.every(value => /^\d+(?:\.\d+)?%$/.test(value)) && /所属赛道/.test(emotionDialog.text) && /百分点|pp|车型总声量/.test(emotionDialog.text), JSON.stringify(emotionDialog));
  if (emotionDialog.open) await page.locator("#emotion-label-dialog-close").click();

  const opportunityFilters = {};
  for (const type of ["优先修复", "抢占空位", "持续放大"]) {
    await page.locator(`#map-filters button[data-filter="${type}"]`).click();
    opportunityFilters[type] = await page.locator("#opportunity-map .bubble").count();
  }
  await page.locator('#map-filters button[data-filter="all"]').click();
  add("opportunity map keeps every strategy filter populated", Object.values(opportunityFilters).every(count => count > 0), JSON.stringify(opportunityFilters));

  const opportunityLayout = await page.evaluate(() => {
    const panel = document.querySelector(".dashboard-opportunity-panel");
    const workbench = document.querySelector(".dashboard-workbench");
    const dataPanel = document.querySelector(".dashboard-data-panel");
    const attribute = document.querySelector(".summary-attribute-section");
    const map = document.querySelector("#opportunity-map");
    const panelRect = panel?.getBoundingClientRect();
    const dataRect = dataPanel?.getBoundingClientRect();
    const attributeRect = attribute?.getBoundingClientRect();
    const mapRect = map?.getBoundingClientRect();
    const bubbles = [...document.querySelectorAll("#opportunity-map .bubble")].map(node => {
      const rect = node.getBoundingClientRect();
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom };
    });
    const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 3 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 3;
    return {
      removedModules: !document.querySelector("#asset-chart") && !document.querySelector("#top-actions") && !document.body.textContent.includes("资产与负债") && !document.body.textContent.includes("本周期应优先做什么"),
      followsWorkbench: panel?.previousElementSibling === workbench,
      aligned: Boolean(panelRect && dataRect && Math.abs(panelRect.left - dataRect.left) < 1 && Math.abs(panelRect.right - dataRect.right) < 1),
      followsAttribute: !attributeRect || Boolean(panelRect && panelRect.top > attributeRect.bottom && panelRect.top - attributeRect.bottom <= 48),
      mapSize: mapRect ? { width: mapRect.width, height: mapRect.height } : null,
      bubblesInside: Boolean(mapRect) && bubbles.every(b => b.left >= mapRect.left - 1 && b.right <= mapRect.right + 1 && b.top >= mapRect.top - 1 && b.bottom <= mapRect.bottom + 1),
      bubbleOverlaps: bubbles.reduce((count, bubble, index) => count + bubbles.slice(index + 1).filter(other => overlap(bubble, other)).length, 0)
    };
  });
  add(
    "opportunity map replaces obsolete modules and fills the width below real attribute NSR",
    opportunityLayout.removedModules && opportunityLayout.followsWorkbench && opportunityLayout.aligned && opportunityLayout.followsAttribute && opportunityLayout.mapSize?.width > 700 && opportunityLayout.mapSize?.height >= 360 && opportunityLayout.bubblesInside && opportunityLayout.bubbleOverlaps === 0,
    JSON.stringify(opportunityLayout)
  );
  await page.setViewportSize({ width: 768, height: 900 });
  await page.reload({ waitUntil: "networkidle" });
  const compactOpportunityLayout = await page.evaluate(() => {
    const panel = document.querySelector(".dashboard-opportunity-panel")?.getBoundingClientRect();
    const data = document.querySelector(".dashboard-data-panel")?.getBoundingClientRect();
    const map = document.querySelector("#opportunity-map")?.getBoundingClientRect();
    const bubbles = [...document.querySelectorAll("#opportunity-map .bubble")].map(node => node.getBoundingClientRect());
    const overlap = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 3 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 3;
    return {
      aligned: Boolean(panel && data && Math.abs(panel.left - data.left) < 1 && Math.abs(panel.right - data.right) < 1),
      mapSize: map ? { width: map.width, height: map.height } : null,
      bubblesInside: Boolean(map) && bubbles.every(b => b.left >= map.left - 1 && b.right <= map.right + 1 && b.top >= map.top - 1 && b.bottom <= map.bottom + 1),
      bubbleOverlaps: bubbles.reduce((count, bubble, index) => count + bubbles.slice(index + 1).filter(other => overlap(bubble, other)).length, 0),
      pageOverflow: document.documentElement.scrollWidth - window.innerWidth
    };
  });
  add("opportunity map stays usable on a compact viewport", compactOpportunityLayout.aligned && compactOpportunityLayout.mapSize?.width > 350 && compactOpportunityLayout.mapSize?.height >= 400 && compactOpportunityLayout.bubblesInside && compactOpportunityLayout.bubbleOverlaps === 0 && compactOpportunityLayout.pageOverflow <= 1, JSON.stringify(compactOpportunityLayout));
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload({ waitUntil: "networkidle" });

  const metricHelp = await page.evaluate(() => Object.fromEntries(
    ["nsr", "ips", "intent", "risk"].map(key => [key, document.querySelector(`#tip-kpi-${key}`)?.textContent.trim() || ""])
  ));
  const metricHelpText = Object.values(metricHelp).join(" ");
  add(
    "dashboard metric help uses marketing strategy language",
    metricHelp.nsr.includes("传播放大") && metricHelp.nsr.includes("核心阻力") &&
      metricHelp.ips.includes("达人") && metricHelp.ips.includes("投放定向") &&
      metricHelp.intent.includes("试驾") && metricHelp.intent.includes("转化承接") &&
      metricHelp.risk.includes("公关资源") && metricHelp.risk.includes("优势卖点") &&
      !/加权声量|样本均值|权重计算/.test(metricHelpText),
    JSON.stringify(metricHelp)
  );

  const identityCheck = await page.evaluate(() => {
    const groups = brandModelGroups(["极氪009", "Zeekr 009", "ZEEKR 009", "Zeeker 009", "阿维塔06", "沃尔沃EX90", "乐道L60", "银河L6", "智己L6", "智己LS7"]);
    const byBrand = Object.fromEntries(groups.map(group => [group.brand, group.models.map(model => canonicalModelLabel(model))]));
    return {
      byBrand,
      zeekrCount: byBrand["极氪"]?.length || 0,
      zeekrLabel: byBrand["极氪"]?.[0] || "",
      avatrBrand: brandForDisplay("阿维塔06"),
      volvoBrand: brandForDisplay("沃尔沃EX90"),
      onvoBrand: brandForDisplay("乐道L60"),
      galaxyBrand: brandForDisplay("银河L6"),
      imModels: byBrand["智己"] || [],
      hasPendingBrand: Object.keys(byBrand).includes("待确认品牌")
    };
  });
  add("vehicle identity assigns pending brands", identityCheck.avatrBrand === "阿维塔" && identityCheck.volvoBrand === "沃尔沃" && !identityCheck.hasPendingBrand, JSON.stringify(identityCheck));
  add("vehicle identity deduplicates Zeekr aliases", identityCheck.zeekrCount === 1 && identityCheck.zeekrLabel.includes("极氪009"), JSON.stringify(identityCheck));
  add("vehicle identity keeps IM Motors clean", identityCheck.onvoBrand === "乐道" && identityCheck.galaxyBrand === "吉利银河" && identityCheck.imModels.every(name => name.includes("智己")), JSON.stringify(identityCheck));

  const socialNav = await page.evaluate(() => ({
    parent: Boolean(document.querySelector('.cockpit-nav [data-page="dashboard"]')),
    child: Boolean(document.querySelector('.cockpit-nav [data-page="socialtrends"]')),
    nested: document.querySelector('.cockpit-nav [data-page="socialtrends"]')?.closest("details")?.classList.contains("cockpit-nav") || false,
    keyLeak: /TIKHUB_API_KEY\s*=\s*[^\s<]+/.test(document.documentElement.innerHTML),
  }));
  add("decision cockpit remains clickable parent with social trend child", socialNav.parent && socialNav.child && socialNav.nested && !socialNav.keyLeak, JSON.stringify(socialNav));
  const socialJobResult={keyword:"智己L6",statusHint:"已形成可识别热度",confidence:.8,confidenceLabel:"高",snapshot:{id:"social-release-gate"},items:[{id:"e1",sentiment:"positive"}],platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78,positive:1,negative:0},{platform:"xiaohongshu",label:"小红书",contentCount:0,heat:0,positive:0,negative:0},{platform:"weibo",label:"微博",contentCount:0,heat:0,positive:0,negative:0}],hotWords:[{word:"智能座舱",count:3}],ownModelRanking:[{model:"智己L6",heat:78,contentCount:1}],modelHeatRanking:[{model:"智己L6",heat:78,contentCount:1}],modelComparisons:[{model:"智己L6",role:"own",heat:78,contentCount:1,positiveRate:100,riskCount:0,confidence:.8,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78}],hotWords:[{word:"智能座舱"}]}],positiveCompetitorsTop5:[],contentRanking:[{platform:"douyin",platformLabel:"抖音",normalizedModel:"智己L6",text:"智己L6 智能座舱体验",author:"汽车媒体",sourceUrl:"https://www.douyin.com/video/1",matrixContent:true,heat:78,sentiment:"positive",metrics:{likes:1200,comments:0,shares:0,collects:0,views:0},evidence:{contentHash:"1234567890abcdef"}}],timeline:[],timelineUndated:{contentCount:0,heat:0,platforms:[]},methodology:{heat:"可复算热度口径"},qa:{dualModel:{status:"aligned"},strategyOutput:"基于双模型一致证据形成策略结论"}};
  await page.route("**/api/social-trends/jobs", route => route.fulfill({status:202,contentType:"application/json",body:JSON.stringify({ok:true,job:{jobId:"social-release-gate",status:"completed",stage:"completed",progress:100,result:socialJobResult}})}));
  await page.locator('#nav button[data-page="socialtrends"]').click();
  await page.locator("#social-trend-keyword").fill("智己L6");
  await page.locator("#social-trend-run").click();
  await page.waitForSelector(".social-ranking tbody tr");
  const socialSurface = await page.evaluate(() => ({active:document.querySelector("#socialtrends")?.classList.contains("active"),status:document.querySelector("#social-trend-status")?.textContent||"",rows:document.querySelectorAll(".social-ranking tbody tr").length,source:document.querySelector(".social-ranking a")?.getAttribute("href")||"",strategy:document.querySelector(".social-method")?.textContent||""}));
  add("social trend center renders rankings, confidence, evidence drill-down and strategy QA", socialSurface.active && /置信度 高/.test(socialSurface.status) && socialSurface.rows === 1 && /douyin/.test(socialSurface.source) && /双模型/.test(socialSurface.strategy), JSON.stringify(socialSurface));
  await page.unroute("**/api/social-trends/jobs");

  await page.locator('#nav button[data-page="data"]').click();
  add("data center opens", await page.locator("#data.page.active").count() === 1);

  await page.locator('#nav button[data-page="strategykb"]').click();
  add("strategy knowledge page opens", await page.locator("#strategykb.page.active").count() === 1);
  add("strategy CTA labels use MMN", await page.locator("#run-rag-search").innerText().then(text => text.includes("MMN")).catch(() => false));

  const bfNav = await page.locator('#nav button[data-page="bffactory"]').count();
  const bfLibraryNav = await page.locator('#nav button[data-page="bflibrary"]').count();
  add("BF factory and asset library have first-class navigation", bfNav === 1 && bfLibraryNav >= 1, JSON.stringify({ bfNav, bfLibraryNav }));
  if (bfNav) {
    await page.locator('#nav button[data-page="bffactory"]').first().click();
  }
  const bfSurface = await page.evaluate(() => ({
    active: document.querySelector("#bffactory")?.classList.contains("active") || false,
    seedCount: document.querySelectorAll("#bffactory [data-bf-profile]").length,
    hasInternalRuleLeak: /种子范式|不是封闭模板|动态编排|动态整理章节|学习最终版本|优质优先\s*[·・]\s*反例只做风险/.test(document.querySelector("#bffactory")?.textContent || ""),
    hasGeneratorSubnav: Boolean(document.querySelector("#bffactory > .bf-subnav")),
    hasCustomDirection: Boolean(document.querySelector("#bf-content-directions")),
    hasEditor: Boolean(document.querySelector("#bf-editor")),
    profileLabels: [...document.querySelectorAll("#bffactory [data-bf-profile] b")].map(node => node.textContent.trim()),
  }));
  const requiredBfProfiles = ["静态实拍", "动态实拍", "底盘实拍"];
  add("BF factory keeps a focused workbench with requested actual-shoot types", bfSurface.active && bfSurface.seedCount >= 7 && requiredBfProfiles.every(label => bfSurface.profileLabels.includes(label)) && !bfSurface.hasInternalRuleLeak && !bfSurface.hasGeneratorSubnav && bfSurface.hasCustomDirection && bfSurface.hasEditor, JSON.stringify(bfSurface));

  const bfCorrection = await page.evaluate(() => ({
    active: Boolean(document.querySelector("#bffactory")),
    type: Boolean(document.querySelector("#bf-correct-type")),
    summary: Boolean(document.querySelector("#bf-correct-summary")),
    strategy: Boolean(document.querySelector("#bf-correct-strategy")),
    content: Boolean(document.querySelector("#bf-correct-content")),
    risk: Boolean(document.querySelector("#bf-correct-risk")),
    tags: Boolean(document.querySelector("#bf-correct-tags")),
  }));
  add("BF editor exposes business-field correction before version return", bfCorrection.active && Object.values(bfCorrection).every(Boolean), JSON.stringify(bfCorrection));
  if (bfLibraryNav) {
    const libraryButton = page.locator('#nav button[data-page="bflibrary"]').first();
    await libraryButton.evaluate(node => { const group = node.closest("details.nav-section"); if (group) group.open = true; });
    await libraryButton.click();
  }
  const bfUpload = await page.evaluate(() => ({
    active: document.querySelector("#bflibrary")?.classList.contains("active") || false,
    accept: document.querySelector("#bf-document-file")?.getAttribute("accept") || "",
    hasProjectScope: Boolean(document.querySelector("#bf-library-project")),
  }));
  add("BF asset library exposes project-scoped multi-format upload", bfUpload.active && /\.docx/.test(bfUpload.accept) && /\.pptx/.test(bfUpload.accept) && /\.pdf/.test(bfUpload.accept) && /\.png/.test(bfUpload.accept) && bfUpload.hasProjectScope, JSON.stringify(bfUpload));

  await page.locator('#nav button[data-page="dashboard"]').click();
  let chooserOpened = false;
  const chooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { chooserOpened = true; }).catch(() => {});
  await page.locator(".dashboard-import [data-file-target]").click();
  await chooser;
  add("dashboard import opens file chooser", chooserOpened);

  const summaryModels = ["小米YU7", "Model Y", "问界M7", "奥迪E7X", "奥迪Q6L e-tron"];
  const summaryHeat = {
    "小米YU7": { volume: 1300345, interaction: 9260761, platformVolume: { "抖音": 901729, "小红书": 140498, "微博": 74294, "B站": 59092, "视频号": 44588, "快手": 25393, "今日头条": 22519, "汽车垂媒": 12552, "其他": 19680 } },
    "Model Y": { volume: 730202, interaction: 3519781, platformVolume: { "抖音": 427206, "小红书": 137260, "微博": 20150, "B站": 15451, "视频号": 43161, "快手": 19739, "今日头条": 34073, "汽车垂媒": 11898, "其他": 21264 } },
    "问界M7": { volume: 252720, interaction: 1145264, platformVolume: { "抖音": 159650, "小红书": 36410, "微博": 11830, "B站": 3393, "视频号": 5420, "快手": 2493, "今日头条": 20197, "汽车垂媒": 5583, "其他": 7744 } },
    "奥迪E7X": { volume: 235579, interaction: 2169813, platformVolume: { "抖音": 103589, "小红书": 35439, "微博": 69977, "B站": 2562, "视频号": 6083, "快手": 1658, "今日头条": 7045, "汽车垂媒": 6052, "其他": 3174 } },
    "奥迪Q6L e-tron": { volume: 20741, interaction: 55736, platformVolume: { "抖音": 7732, "小红书": 7868, "微博": 1016, "B站": 25, "视频号": 843, "快手": 351, "今日头条": 1554, "汽车垂媒": 561, "其他": 791 } }
  };
  const summaryPlatformNsr = {
    "小米YU7": { "全网": .308521, "垂媒车主口碑": .627981, "抖音": .087413, "小红书": .121951, "微博": .804196, "B站": -.195531, "视频号": -.150685 },
    "Model Y": { "全网": .299366, "垂媒车主口碑": .617391, "抖音": .043025, "小红书": .242424, "微博": .647416, "B站": -.056075, "视频号": -.064039 },
    "问界M7": { "全网": .703560, "垂媒车主口碑": .723772, "抖音": .709132, "小红书": .401198, "微博": .879032, "B站": .489177, "视频号": .698730 },
    "奥迪E7X": { "全网": .751287, "垂媒车主口碑": .790541, "抖音": .713814, "小红书": .330128, "微博": .851852, "B站": .666507, "视频号": .840779 },
    "奥迪Q6L e-tron": { "全网": .809392, "抖音": .721311, "小红书": .410256, "微博": .995316, "B站": .995316, "视频号": .525424 }
  };
  const summaryAttributeNsr = {
    "全网": {
      "外观": { "小米YU7": .726804, "Model Y": .561224, "问界M7": .838480, "奥迪E7X": .722617, "奥迪Q6L e-tron": .944134 },
      "价格": { "小米YU7": -.180556, "Model Y": .065831, "问界M7": .323671, "奥迪E7X": .624859, "奥迪Q6L e-tron": .513514 },
      "安全": { "小米YU7": .137778, "Model Y": -.092486, "问界M7": .617021, "奥迪E7X": .503686, "奥迪Q6L e-tron": .795918 }
    },
    "垂媒车主口碑": {
      "外观": { "小米YU7": .865031, "Model Y": .698113, "问界M7": .855670, "奥迪E7X": .826484 },
      "价格": { "小米YU7": .090909, "Model Y": .571429, "问界M7": .739130, "奥迪E7X": .927273 },
      "安全": { "小米YU7": -.375000, "Model Y": .454545, "问界M7": .263158, "奥迪E7X": .642857 }
    },
    "抖音": {
      "外观": { "小米YU7": .727273, "Model Y": .466667, "问界M7": .837500, "奥迪E7X": .760832, "奥迪Q6L e-tron": .920000 },
      "价格": { "小米YU7": -.396226, "Model Y": -.118644, "问界M7": -.035714, "奥迪E7X": .596154, "奥迪Q6L e-tron": .272727 },
      "安全": { "小米YU7": .118644, "Model Y": -.236364, "问界M7": .673913, "奥迪E7X": .067797, "奥迪Q6L e-tron": 0 }
    }
  };
  const summaryRows = [];
  for (const [source, labels] of Object.entries(summaryAttributeNsr)) {
    for (const [label, modelScores] of Object.entries(labels)) {
      for (const [model, nsr] of Object.entries(modelScores)) {
        summaryRows.push([model, model === "奥迪E7X" ? "本品" : "竞品", source, label === "价格" ? "价格权益" : "安全质量", label, nsr >= 0 ? "认可" : "失望", "未知", "无", 100, 4, 1, 4, "汇总NSR评分", "release-gate", nsr]);
      }
    }
  }
  await page.evaluate(({ summaryModels, summaryRows, summaryHeat, summaryPlatformNsr }) => {
    localStorage.setItem("mmnEngineState:china", JSON.stringify({
      datasetVersion: "summary_xlsx_audi",
      sourceNote: "已从产品评价汇总表导入。",
      config: { project: "奥迪E7X认知诊断｜产品评价导入", brand: "奥迪", model: "奥迪E7X", competitor: "小米YU7 / Model Y / 问界M7 / 奥迪Q6L e-tron", targetIdentity: "", budget: 800, priorityThreshold: 60, riskThreshold: 500 },
      platforms: { "全网": 1, "垂媒车主口碑": 1.15, "抖音": 1.35 },
      models: summaryModels,
      rows: summaryRows,
      summaryHeat,
      summaryPlatformNsr,
      summaryMetrics: { "奥迪E7X": { overallNsr: .7512874630645843 } },
      importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false }, attributeVolumeAvailable: false, platformNsrAvailable: true, platformNsrSources: ["全网", "垂媒车主口碑", "抖音", "小红书", "微博", "B站", "视频号"], message: "源表未提供目标人群、购买意向、标签声量和风险量级。" }
    }));
  }, { summaryModels, summaryRows, summaryHeat, summaryPlatformNsr });
  await page.reload({ waitUntil: "networkidle" });
  const summaryImport = await page.evaluate(() => ({
    model: document.querySelector("#dash-model-select")?.value || "",
    nsr: document.querySelector("#kpi-nsr")?.textContent.trim() || "",
    ips: document.querySelector("#kpi-ips")?.textContent.trim() || "",
    ipsNote: document.querySelector("#kpi-ips-note")?.textContent.trim() || "",
    intent: document.querySelector("#kpi-intent")?.textContent.trim() || "",
    intentNote: document.querySelector("#kpi-intent-note")?.textContent.trim() || "",
    surfaceTitle: document.querySelector(".dashboard-data-title-copy h2")?.textContent.trim() || "",
    selectableModels: [document.querySelector(".summary-heat-own b")?.textContent.trim(), ...[...document.querySelectorAll(".summary-heat-model-list label span")].map(node => node.textContent.trim())].filter(Boolean),
    selectedModels: [document.querySelector(".summary-heat-own b")?.textContent.trim(), ...[...document.querySelectorAll(".summary-heat-model-list input:checked")].map(node => node.value)].filter(Boolean),
    heatRows: [...document.querySelectorAll(".summary-heat-row")].map(node => node.textContent.replace(/\s+/g, " ").trim()),
    addOptions: [...document.querySelectorAll("#summary-heat-add-model option")].map(node => node.textContent.trim()),
    ownModel: document.querySelector(".summary-heat-own b")?.textContent.trim() || "",
    ownLocked: Boolean(document.querySelector(".summary-heat-own input:checked:disabled")),
    competitorModels: [...document.querySelectorAll(".summary-heat-model-list label span")].map(node => node.textContent.trim()),
    summaryCardsHidden: Boolean(document.querySelector("#dashboard-data-summary")?.hidden),
    productPointName: document.querySelector("#dashboard-data-context .label-dimension span")?.textContent.trim() || "",
    scaleNote: document.querySelector(".summary-heat-chart-head>small")?.textContent.trim() || "",
    topBrands: [...document.querySelectorAll("#dash-brand-select option")].map(node => node.textContent.trim()),
    attributeRows: document.querySelectorAll(".summary-attribute-row").length,
    attributeValues: [...document.querySelectorAll(".summary-attribute-value")].map(node => node.textContent.trim()),
    attributePlatformOptions: [...document.querySelectorAll("#summary-attribute-platform option")].map(node => node.textContent.trim()),
    attributeSelectedPlatform: document.querySelector("#summary-attribute-platform")?.value || "",
    attributeHeaders: [...document.querySelectorAll(".summary-attribute-head>b")].map(node => node.textContent.trim()),
    attributeRowData: [...document.querySelectorAll(".summary-attribute-row")].map(node => ({
      label: node.querySelector(".summary-attribute-label b")?.textContent.trim() || "",
      values: [...node.querySelectorAll(".summary-attribute-value")].map(value => value.textContent.trim())
    })),
    nsrTitle: document.querySelector(".summary-nsr-section>header b")?.textContent.trim() || "",
    nsrPlatformOptions: [...document.querySelectorAll("#summary-nsr-platform option")].map(node => node.textContent.trim()),
    nsrRows: [...document.querySelectorAll(".summary-nsr-row")].map(node => ({ model: node.querySelector("b")?.textContent.trim(), value: node.querySelector("strong")?.textContent.trim(), role: node.classList.contains("own") ? "own" : "competitor" })),
    opportunityBubbles: [...document.querySelectorAll("#opportunity-map .bubble")].map(node => ({ label: node.textContent.trim(), title: node.title })),
    opportunitySummary: document.querySelector("#map-summary")?.textContent.trim() || "",
    opportunityPlacement: (() => { const panel = document.querySelector(".dashboard-opportunity-panel")?.getBoundingClientRect(), attribute = document.querySelector(".summary-attribute-section")?.getBoundingClientRect(); return panel && attribute ? { gap: panel.top - attribute.bottom, alignedRight: Math.abs(panel.right - document.querySelector(".dashboard-data-panel").getBoundingClientRect().right) < 1 } : null; })(),
    quadrants: document.querySelectorAll("#dashboard-emotion-quadrant .emotion-quadrant-cell").length
  }));
  add("summary workbook keeps verified NSR and suppresses unsupported metrics", summaryImport.model === "奥迪E7X" && summaryImport.nsr === "75.1%" && summaryImport.ips === "不适用" && /未提供目标人群/.test(summaryImport.ipsNote) && summaryImport.intent === "不适用" && /未提供购买意向/.test(summaryImport.intentNote), JSON.stringify(summaryImport));
  add("summary workbook first renders source-backed all-network heat comparison", summaryImport.surfaceTitle === "全网声量及互动量对比" && summaryImport.selectableModels.length === summaryModels.length && summaryImport.selectedModels.length === summaryModels.length && summaryImport.heatRows.length === summaryModels.length && /^奥迪E7X.*23\.6万.*217\.0万/.test(summaryImport.heatRows[0] || "") && summaryImport.addOptions.length === 1, JSON.stringify(summaryImport));
  add("summary cockpit keeps product fixed and removes system counters", summaryImport.ownModel === "奥迪E7X" && summaryImport.ownLocked && summaryImport.competitorModels.length === summaryModels.length - 1 && !summaryImport.competitorModels.includes("奥迪E7X") && summaryImport.summaryCardsHidden, JSON.stringify(summaryImport));
  add("summary cockpit uses decision language and explains independent scales", summaryImport.productPointName === "当前可用产品点" && summaryImport.scaleNote === "声量与互动量按各自独立尺度展示，不可直接比较绝对柱长。", JSON.stringify(summaryImport));
  add("summary workbook keeps the global brand library separate from imported comparison models", summaryImport.topBrands.length > 10 && summaryImport.topBrands.includes("奥迪") && summaryImport.topBrands.includes("智己") && summaryImport.selectableModels.length === summaryModels.length, JSON.stringify(summaryImport));
  add("summary workbook renders real attribute NSR without emotion quadrants", summaryImport.attributeRows === 3 && summaryImport.attributeValues.length === 15 && summaryImport.attributeValues.every(value => /^-?\d+(?:\.\d)?%$/.test(value)) && summaryImport.quadrants === 0, JSON.stringify(summaryImport));
  const allNetworkAppearance = summaryImport.attributeRowData.find(row => row.label === "外观");
  add("summary attribute NSR compares selected models within one source platform", summaryImport.attributePlatformOptions.join("|") === "全网|垂媒车主口碑|抖音" && summaryImport.attributeSelectedPlatform === "全网" && summaryImport.attributeHeaders.join("|") === "产品点|奥迪E7X|小米YU7|Model Y|问界M7|奥迪Q6L e-tron" && allNetworkAppearance?.values.join("|") === "72.3%|72.7%|56.1%|83.8%|94.4%", JSON.stringify(summaryImport));
  add("summary cockpit separates overall platform NSR from attribute NSR", summaryImport.nsrTitle === "车型整体平台 NSR 对比" && summaryImport.nsrPlatformOptions.join("|") === "全网|垂媒车主口碑|抖音|小红书|微博|B站|视频号" && summaryImport.nsrRows.length === summaryModels.length && summaryImport.nsrRows[0]?.model === "奥迪E7X" && summaryImport.nsrRows[0]?.value === "75.1%" && summaryImport.nsrRows[0]?.role === "own", JSON.stringify(summaryImport));
  const exteriorOpportunity = summaryImport.opportunityBubbles.find(item => item.label === "外观");
  add("summary opportunity map uses source-backed attribute NSR instead of equalized sample shares", /本品NSR 77\.0%/.test(exteriorOpportunity?.title || "") && /竞品均值 78\.1%/.test(exteriorOpportunity?.title || "") && /Gap \+1\.1pp/.test(exteriorOpportunity?.title || "") && /属性 NSR/.test(summaryImport.opportunitySummary) && summaryImport.opportunityPlacement?.gap > 0 && summaryImport.opportunityPlacement.gap <= 48 && summaryImport.opportunityPlacement.alignedRight, JSON.stringify({ exteriorOpportunity, summary: summaryImport.opportunitySummary, placement: summaryImport.opportunityPlacement }));

  const attributePlatformCount = await page.locator("#summary-attribute-platform").count();
  let douyinAttributes = { selected: "", overallSelected: "", appearance: [] };
  if (attributePlatformCount === 1) {
    await page.locator("#summary-attribute-platform").selectOption("抖音");
    douyinAttributes = await page.evaluate(() => ({
      selected: document.querySelector("#summary-attribute-platform")?.value || "",
      overallSelected: document.querySelector("#summary-nsr-platform")?.value || "",
      appearance: [...document.querySelectorAll(".summary-attribute-row")].find(node => node.querySelector(".summary-attribute-label b")?.textContent.trim() === "外观")
        ? [...[...document.querySelectorAll(".summary-attribute-row")].find(node => node.querySelector(".summary-attribute-label b")?.textContent.trim() === "外观").querySelectorAll(".summary-attribute-value")].map(node => node.textContent.trim())
        : []
    }));
  }
  add("attribute platform selection refreshes only the attribute comparison", attributePlatformCount === 1 && douyinAttributes.selected === "抖音" && douyinAttributes.overallSelected === "全网" && douyinAttributes.appearance.join("|") === "76.1%|72.7%|46.7%|83.8%|92.0%", JSON.stringify(douyinAttributes));
  if (attributePlatformCount === 1) await page.locator("#summary-attribute-platform").selectOption("全网");

  await page.locator("#summary-nsr-platform").selectOption("B站");
  const bSiteNsr = await page.evaluate(() => ({
    values: [...document.querySelectorAll(".summary-nsr-row")].map(node => ({ model: node.querySelector("b")?.textContent.trim(), value: node.querySelector("strong")?.textContent.trim(), left: node.querySelector("em")?.style.getPropertyValue("--nsr-left"), size: node.querySelector("em")?.style.getPropertyValue("--nsr-size"), color: node.querySelector("em") ? getComputedStyle(node.querySelector("em")).backgroundColor : "" })),
    selected: document.querySelector("#summary-nsr-platform")?.value || ""
  }));
  const bSiteXiaomi = bSiteNsr.values.find(row => row.model === "小米YU7"), bSiteAudi = bSiteNsr.values.find(row => row.model === "奥迪E7X");
  add("platform NSR uses a fixed minus-100 to 100 scale with role colors", bSiteNsr.selected === "B站" && bSiteXiaomi?.value === "-19.6%" && parseFloat(bSiteXiaomi.left) < 50 && bSiteXiaomi.color === "rgb(230, 160, 170)" && bSiteAudi?.value === "66.7%" && bSiteAudi.left === "50.0000%" && bSiteAudi.color === "rgb(156, 207, 227)", JSON.stringify(bSiteNsr));

  await page.locator('[data-summary-nsr-model="小米YU7"]').click();
  const nsrBubble = await page.evaluate(() => ({
    title: document.querySelector(".summary-nsr-popover header b")?.textContent.replace(/\s+/g, " ").trim() || "",
    groups: [...document.querySelectorAll(".summary-nsr-popover .summary-platform-group")].map(node => ({
      platform: node.querySelector(".summary-platform-name")?.textContent.trim() || "",
      series: [...node.querySelectorAll(".summary-platform-series>div")].map(series => ({ text: series.querySelector("small")?.textContent.trim() || "", left: series.querySelector("em")?.style.getPropertyValue("--nsr-left"), color: series.querySelector("em") ? getComputedStyle(series.querySelector("em")).backgroundColor : "" }))
    }))
  }));
  const nsrBsite = nsrBubble.groups.find(group => group.platform === "B站");
  add("overall NSR bubble compares every platform against the fixed product", /小米YU7 vs 奥迪E7X/.test(nsrBubble.title) && nsrBubble.groups.length === 7 && nsrBubble.groups.every(group => group.series.length === 2) && parseFloat(nsrBsite?.series[0]?.left) < 50 && nsrBsite?.series[0]?.color === "rgb(230, 160, 170)" && nsrBsite?.series[1]?.text === "本品 · 奥迪E7X" && nsrBsite?.series[1]?.color === "rgb(156, 207, 227)", JSON.stringify(nsrBubble));
  await page.locator(".summary-nsr-popover button").click();
  await page.locator("#summary-nsr-platform").selectOption("全网");

  await page.locator('[data-summary-heat-model="小米YU7"]').click();
  const platformBubble = await page.evaluate(() => {
    const close = document.querySelector(".summary-platform-popover button");
    const before = close ? getComputedStyle(close, "::before") : null;
    const after = close ? getComputedStyle(close, "::after") : null;
    return {
      title: document.querySelector(".summary-platform-popover header")?.textContent.replace(/\s+/g, " ").trim() || "",
      groups: [...document.querySelectorAll(".summary-platform-group")].map(node => ({
        platform: node.querySelector(".summary-platform-name")?.textContent.trim() || "",
        series: [...node.querySelectorAll(".summary-platform-series>div")].map(series => ({
          text: series.textContent.replace(/\s+/g, " ").trim(),
          width: series.querySelector("em")?.style.width || "",
          color: series.querySelector("em") ? getComputedStyle(series.querySelector("em")).backgroundColor : "",
          hasTrailingValue: Boolean(series.querySelector("strong"))
        }))
      })),
      closeLabel: close?.getAttribute("aria-label") || "",
      closeText: close?.textContent.trim() || "",
      closeGeometry: close && before && after ? {
        width: close.getBoundingClientRect().width,
        height: close.getBoundingClientRect().height,
        clientWidth: close.clientWidth,
        clientHeight: close.clientHeight,
        beforeLeft: parseFloat(before.left),
        beforeTop: parseFloat(before.top),
        afterLeft: parseFloat(after.left),
        afterTop: parseFloat(after.top)
      } : null
    };
  });
  const douyinGroup = platformBubble.groups.find(group => group.platform === "抖音");
  const closeCentered = platformBubble.closeGeometry && platformBubble.closeGeometry.width === platformBubble.closeGeometry.height && Math.abs(platformBubble.closeGeometry.beforeLeft - platformBubble.closeGeometry.clientWidth / 2) < .6 && Math.abs(platformBubble.closeGeometry.beforeTop - platformBubble.closeGeometry.clientHeight / 2) < .6 && Math.abs(platformBubble.closeGeometry.afterLeft - platformBubble.closeGeometry.clientWidth / 2) < .6 && Math.abs(platformBubble.closeGeometry.afterTop - platformBubble.closeGeometry.clientHeight / 2) < .6;
  add("competitor heat bubble normalizes each platform pair without trailing values", /小米YU7.*奥迪E7X.*分平台声量对比/.test(platformBubble.title) && platformBubble.groups.length === 9 && platformBubble.groups.every(group => group.series.length === 2 && group.series.every(row => !row.hasTrailingValue) && group.series.some(row => row.width === "100%")) && douyinGroup?.series.some(row => row.text === "小米YU7" && row.width === "100%" && row.color === "rgb(230, 160, 170)") && douyinGroup?.series.some(row => row.text === "本品 · 奥迪E7X" && row.width === "63.4103%" && row.color === "rgb(156, 207, 227)"), JSON.stringify(platformBubble));
  add("platform bubble close icon is geometrically centered", platformBubble.closeLabel === "关闭分平台声量气泡" && platformBubble.closeText === "" && closeCentered, JSON.stringify(platformBubble.closeGeometry));
  const headerScope = await page.evaluate(() => ({
    main: getComputedStyle(document.querySelector("main>header")).position,
    popover: getComputedStyle(document.querySelector(".summary-platform-popover header")).position,
    attribute: getComputedStyle(document.querySelector(".summary-attribute-section>header")).position
  }));
  add("only the page header is sticky", headerScope.main === "sticky" && headerScope.popover === "static" && headerScope.attribute === "static", JSON.stringify(headerScope));
  await page.locator(".summary-platform-popover button").click();
  await page.evaluate(() => document.querySelector(".summary-attribute-section")?.scrollIntoView({ block: "start" }));
  await page.waitForTimeout(80);
  const attributeTopBefore = await page.locator(".summary-attribute-section>header").evaluate(node => node.getBoundingClientRect().top);
  await page.evaluate(() => window.scrollBy(0, 120));
  await page.waitForTimeout(80);
  const attributeTopAfter = await page.locator(".summary-attribute-section>header").evaluate(node => node.getBoundingClientRect().top);
  add("attribute header scrolls with content instead of covering the page header", attributeTopBefore - attributeTopAfter > 100, JSON.stringify({ attributeTopBefore, attributeTopAfter }));
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.locator('.summary-heat-model-list input[value="小米YU7"]').uncheck();
  const lockedAfterFilter = await page.evaluate(() => ({
    ownLocked: Boolean(document.querySelector(".summary-heat-own input:checked:disabled")),
    rows: [...document.querySelectorAll(".summary-heat-row>b")].map(node => node.textContent.trim()),
    nsrRows: [...document.querySelectorAll(".summary-nsr-row>b")].map(node => node.textContent.trim())
  }));
  add("competitor filtering cannot remove the product model", lockedAfterFilter.ownLocked && lockedAfterFilter.rows.includes("奥迪E7X") && !lockedAfterFilter.rows.includes("小米YU7") && lockedAfterFilter.nsrRows.includes("奥迪E7X") && !lockedAfterFilter.nsrRows.includes("小米YU7"), JSON.stringify(lockedAfterFilter));
  await page.locator('.summary-heat-model-list input[value="小米YU7"]').check();

  await page.route("**/api/import-xlsx?filename=AUDI%20E7X.xlsx", route => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ ok: true, dataset: {
      datasetVersion: "summary_xlsx_AUDI_E7X",
      sourceNote: "测试产品评价汇总表",
      config: { project: "奥迪E7X认知诊断｜产品评价导入", brand: "奥迪", model: "奥迪E7X", competitor: "小米YU7 / Model Y" },
      platforms: { "全网": 1, "垂媒车主口碑": 1.15, "抖音": 1.35 },
      models: summaryModels,
      rows: summaryRows,
      summaryHeat,
      summaryPlatformNsr,
      summaryMetrics: { "奥迪E7X": { overallNsr: .7512874630645843 } },
      importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false }, platformNsrAvailable: true, platformNsrSources: ["全网", "垂媒车主口碑", "抖音", "小红书", "微博", "B站", "视频号"] }
    } })
  }));
  await page.evaluate(async () => {
    const brandByModel = { "小米YU7": "小米汽车", "Model Y": "特斯拉", "问界M7": "问界", "奥迪E7X": "奥迪", "奥迪Q6L e-tron": "奥迪" };
    Object.entries(brandByModel).forEach(([model, brand]) => {
      modelIdentities.items[model] = { raw_name: model, normalized_name: model, brand_name: brand, model_family: model, energy_type: "UNKNOWN", confidence: "release-gate" };
    });
    dashBrandOpen = "智己";
    dashboardPlatformFilter = "抖音";
    await importDataFile(new File([new Uint8Array([1])], "AUDI E7X.xlsx"));
  });
  const replacementContext = await page.evaluate(() => ({
    brand: document.querySelector("#dash-brand-select")?.value || "",
    model: document.querySelector("#dash-model-select")?.value || "",
    models: [...document.querySelectorAll("#dash-model-select option")].map(option => option.textContent.trim()),
    heatRows: document.querySelectorAll(".summary-heat-row").length,
    selectableModels: [document.querySelector(".summary-heat-own b")?.textContent.trim(), ...[...document.querySelectorAll(".summary-heat-model-list label span")].map(option => option.textContent.trim())].filter(Boolean)
  }));
  add("replacement import resets the dashboard while preserving the global model library", replacementContext.brand === "奥迪" && replacementContext.model === "奥迪E7X" && replacementContext.models.includes("奥迪E7X") && replacementContext.models.includes("奥迪Q6L e-tron") && replacementContext.models.includes("奥迪A3") && replacementContext.heatRows === summaryModels.length && replacementContext.selectableModels.length === summaryModels.length && !replacementContext.selectableModels.includes("奥迪A3"), JSON.stringify(replacementContext));

  await page.evaluate(() => {
    localStorage.setItem("mmnEngineState:china", JSON.stringify({
      datasetVersion: "summary_xlsx_legacy_bad_import",
      sourceNote: "已从旧版产品评价汇总表导入。",
      config: { project: "奥迪E7X认知诊断", brand: "奥迪", model: "奥迪E7X", competitor: "小米YU7", targetIdentity: "目标核心人群", budget: 800, priorityThreshold: 60, riskThreshold: 500 },
      platforms: { 抖音: 1.25 },
      rows: [["奥迪E7X", "本品", "正面", "整体口碑", "总体口碑", "兴奋", "目标核心人群", "高意向", 100, 4, 1, 4]],
      importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false } }
    }));
  });
  await page.reload({ waitUntil: "networkidle" });
  const blockedLegacy = await page.evaluate(() => ({
    nsr: document.querySelector("#kpi-nsr")?.textContent.trim() || "",
    samples: document.querySelector("#dash-samples")?.textContent.trim() || "",
    note: document.querySelector("#dashboard-data-note")?.textContent.trim() || "",
    platforms: [...document.querySelectorAll("#dashboard-platform-filter option")].map(option => option.textContent.trim())
  }));
  add("legacy summary imports are quarantined instead of rendering false metrics", blockedLegacy.nsr === "请重新导入" && blockedLegacy.samples === "旧版结果已隔离" && /已阻止旧版产品评价汇总表结果/.test(blockedLegacy.note) && !blockedLegacy.platforms.includes("正面"), JSON.stringify(blockedLegacy));

  await browser.close();

  const failed = checks.filter(item => !item.pass);
  const result = { ok: failed.length === 0 && runtimeErrors.length === 0, checks, failed, runtimeErrors };
  console.log(JSON.stringify(result, null, 2));
  if (!result.ok) process.exit(1);
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
