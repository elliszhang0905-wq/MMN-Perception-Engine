const { chromium } = require("playwright");

const baseUrl = process.env.MMN_URL || "http://localhost:8765/";
const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function seedSummaryState() {
  const models = ["奥迪E7X", "小米YU7", "奥迪Q6L e-tron"];
  const sources = ["全网", "垂媒车主口碑", "抖音"];
  const rows = [];
  const add = (model, source, label, nsr, impact = 4) => rows.push([
    model, model === "奥迪E7X" ? "本品" : "竞品", source, "产品评价", label,
    nsr >= 0 ? "认可" : "失望", "未知", "无", 100, impact, 1, 1, "汇总NSR评分", "release-gate", nsr,
  ]);
  sources.forEach(source => {
    add("奥迪E7X", source, "空间", .78, 5);
    add("奥迪E7X", source, "质量", source === "抖音" ? -.3 : .12, 4);
    add("小米YU7", source, "用户服务", -.42, 5);
    add("小米YU7", source, "空间", .31, 5);
  });
  add("奥迪Q6L e-tron", "全网", "安全", .74, 5);
  add("奥迪Q6L e-tron", "抖音", "安全", .68, 5);
  add("奥迪E7X", "全网", "安全", .44, 5);
  add("奥迪E7X", "抖音", "安全", .32, 5);
  add("奥迪E7X", "全网", "用车成本", .2, 4);
  add("小米YU7", "全网", "用车成本", .3, 4);
  return {
    datasetVersion: "summary_xlsx_data_first_gate",
    sourceNote: "数据优先机会地图发布门禁样本",
    config: { project: "奥迪E7X产品评价导入", brand: "奥迪", model: "奥迪E7X", competitor: "小米YU7 / 奥迪Q6L e-tron", targetIdentity: "", budget: 800, priorityThreshold: 60, riskThreshold: 500 },
    platforms: Object.fromEntries(sources.map(source => [source, 1])),
    models,
    rows,
    summaryHeat: Object.fromEntries(models.map(model => [model, { volume: 1000, interaction: 2000, platformVolume: { "全网": 1000 } }])),
    summaryPlatformNsr: {},
    summaryMetrics: { "奥迪E7X": { overallNsr: .6 } },
    importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false }, attributeNsrSources: sources, platformNsrSources: sources, message: "发布门禁样本" },
  };
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const runtimeErrors = [];
  const checks = [];
  const add = (name, pass, detail = "") => checks.push({ name, pass: Boolean(pass), detail });
  page.on("pageerror", error => runtimeErrors.push(String(error.message || error)));
  page.on("console", message => { if (message.type() === "error") runtimeErrors.push(message.text()); });

  try {
    // The cockpit intentionally starts background API work (including model-backed modules).
    // Waiting for networkidle makes the release gate depend on those unrelated request durations.
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#dashboard");
    await page.evaluate(state => {
      localStorage.setItem("mmnEngineEdition", "china");
      localStorage.setItem("mmnEngineState:china", JSON.stringify(state));
    }, seedSummaryState());
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForSelector("#dashboard");
    await page.waitForTimeout(300);

    const initial = await page.evaluate(() => ({
      legacyControls: Boolean(document.querySelector("#map-filters, #map-limit, #opportunity-evidence-workbench")),
      summary: document.querySelector("#map-summary")?.textContent.trim() || "",
      models: [...document.querySelectorAll("[data-nsr-map-model]")].map(node => node.textContent.trim()),
      topCompetitors: document.querySelector("#dash-competitor")?.textContent.trim() || "",
      statuses: [...document.querySelectorAll("#opportunity-map .bubble")].map(node => node.className),
      labels: [...document.querySelectorAll("#opportunity-map .bubble span")].map(node => node.textContent.trim()),
      benchmarkLabels: [...document.querySelectorAll("#opportunity-map .bubble small")].map(node => node.textContent.trim()),
      mapBubbles: document.querySelectorAll("#opportunity-map .bubble").length,
    }));
    add("data-first map removes official verification controls", !initial.legacyControls, JSON.stringify(initial));
    add("data-first map declares imported NSR as its only basis", /导入的 .*属性 NSR/.test(initial.summary) && /蓝色仅提示数据缺口/.test(initial.summary) && !/官网|双模型|人工确认/.test(initial.summary), initial.summary);
    add("top competitors follow the imported comparison models", initial.models.length > 0 && initial.topCompetitors === initial.models.join(" / "), initial.topCompetitors);
    add("map renders one own-model bubble per attribute with benchmark semantics", initial.statuses.length > 0 && initial.statuses.every(value => /\bbubble\b/.test(value) && /\b(asset|chance|risk|pending)\b/.test(value)) && new Set(initial.labels).size === initial.labels.length && initial.labels.length === initial.mapBubbles && initial.benchmarkLabels.length === initial.mapBubbles && initial.benchmarkLabels.every(value => /本品领先|对标|待补竞品/.test(value)), JSON.stringify(initial));

    await page.getByRole("button", { name: "奥迪Q6L e-tron", exact: true }).click();
    const toggled = await page.evaluate(() => ({
      selected: document.querySelector('[data-nsr-map-model="奥迪Q6L e-tron"]')?.getAttribute("aria-pressed"),
      q6Labels: [...document.querySelectorAll("#opportunity-map .bubble")].filter(node => node.textContent.includes("Q6L")).length,
      total: document.querySelectorAll("#opportunity-map .bubble").length,
    }));
    add("model multi-select updates benchmark labels without duplicating attributes", toggled.selected === "false" && toggled.q6Labels === 0 && toggled.total === initial.mapBubbles, JSON.stringify(toggled));
    await page.getByRole("button", { name: "奥迪Q6L e-tron", exact: true }).click();

    await page.locator("#opportunity-map .bubble").first().click();
    const detailOpened = await page.locator(".nsr-map-detail").count();
    await page.locator("[data-nsr-map-close]").click();
    const detailClosed = await page.locator(".nsr-map-detail").count();
    add("attribute ranking bubble closes when the close button is pressed", detailOpened === 1 && detailClosed === 0, JSON.stringify({ detailOpened, detailClosed }));

    const layout = await page.evaluate(() => {
      const map = document.querySelector("#opportunity-map")?.getBoundingClientRect();
      const bubbles = [...document.querySelectorAll("#opportunity-map .bubble")].map(node => node.getBoundingClientRect());
      const overlap = (left, right) => Math.min(left.right, right.right) - Math.max(left.left, right.left) > 3 && Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top) > 3;
      return {
        map: map ? { width: map.width, height: map.height } : null,
        inside: Boolean(map) && bubbles.every(bubble => bubble.left >= map.left - 1 && bubble.right <= map.right + 1 && bubble.top >= map.top - 1 && bubble.bottom <= map.bottom + 1),
        overlaps: bubbles.reduce((total, bubble, index) => total + bubbles.slice(index + 1).filter(other => overlap(bubble, other)).length, 0),
      };
    });
    add("map keeps labels inside the plotting area without overlap", layout.map?.width >= 520 && layout.map?.height >= 360 && layout.inside && layout.overlaps === 0, JSON.stringify(layout));

    const socialNav = await page.evaluate(() => ({
      parent: Boolean(document.querySelector('.cockpit-nav [data-page="dashboard"]')),
      child: Boolean(document.querySelector('.cockpit-nav [data-page="socialtrends"]')),
      nested: document.querySelector('.cockpit-nav [data-page="socialtrends"]')?.closest("details")?.classList.contains("cockpit-nav") || false,
      keyLeak: /TIKHUB_API_KEY\s*=\s*[^\s<]+/.test(document.documentElement.innerHTML),
    }));
    add("cockpit remains clickable parent with social trend child and no key leak", socialNav.parent && socialNav.child && socialNav.nested && !socialNav.keyLeak, JSON.stringify(socialNav));
    let socialRequest = {};
    await page.route("**/api/social-trends/jobs", async route => {
      socialRequest = route.request().postDataJSON();
      const ownEvidence={platform:"douyin",platformLabel:"抖音",normalizedModel:"智己L6",text:"智己L6 智能座舱体验",author:"汽车媒体",sourceUrl:"https://www.douyin.com/video/1",matrixContent:true,heat:78,sentiment:"positive",metrics:{likes:1200,comments:80,shares:35,collects:120,views:52000},evidence:{contentHash:"1234567890abcdef"}};
      const competitorEvidence={platform:"weibo",platformLabel:"微博",normalizedModel:"小米YU7",text:"小米YU7 城市体验",author:"电车观察",sourceUrl:"https://weibo.com/detail/2",matrixContent:false,heat:66,sentiment:"positive",metrics:{likes:820,comments:50,shares:20,collects:0,views:0},evidence:{contentHash:"abcdef1234567890"}};
      const result={keyword:"智己L6",statusHint:"已形成可识别热度",confidence:.8,confidenceLabel:"高",snapshot:{id:"gate-snapshot"},items:[{id:"e1",sentiment:"positive"}],platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78,positive:1,negative:0,share:100}],platformShare:[{platform:"douyin",label:"抖音",contentCount:1,heat:78,positive:1,negative:0,share:100}],timeline:[{date:"2026-07-11",heat:78,contentCount:1,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78}]}],timelineUndated:{contentCount:0,heat:0,platforms:[]},hotWords:[{word:"智能座舱",count:3}],ownModelRanking:[{model:"智己L6",heat:78}],modelHeatRanking:[{model:"智己L6",heat:78},{model:"小米YU7",heat:66}],modelComparisons:[{model:"智己L6",role:"own",heat:78,contentCount:1,positiveRate:100,riskCount:0,confidence:.8,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78}],hotWords:[{word:"智能座舱"}]},{model:"小米YU7",role:"competitor",heat:66,contentCount:1,positiveRate:100,riskCount:0,confidence:.8,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:66}],hotWords:[{word:"城市体验"}]}],positiveCompetitorsTop5:[{model:"小米YU7",positiveHeat:66,positiveCount:3,confidence:.8}],contentRanking:[ownEvidence],comparisonEvidence:[ownEvidence,competitorEvidence],creatorRanking:[{author:"汽车媒体",platform:"douyin",heat:78,matrixContent:true}],matrixSummary:{creatorCount:1},commentInsights:{total:12,positive:9,negative:1},contentClusters:[{topic:"智能座舱",contentCount:3,heat:78}],riskTopics:[],hotLists:[{platform:"douyin",platformLabel:"抖音",items:["智能汽车"]}],historyComparison:{available:false,delta:{}},methodology:{heat:"可复算热度口径"},qa:{dualModel:{status:"aligned"},strategyOutput:"基于双模型一致证据形成策略结论"}};
      result.items=[ownEvidence,{platform:"xiaohongshu",platformLabel:"小红书",normalizedModel:"智己L6",text:"智己L6 车机偶发卡顿体验",author:"真实车主小林",sourceUrl:"https://www.xiaohongshu.com/explore/risk-1",heat:43.5,sentiment:"negative"}];
      await route.fulfill({status:202,contentType:"application/json",body:JSON.stringify({ok:true,job:{jobId:"gate-snapshot",status:"completed",stage:"completed",progress:100,result}})});
    });
    await page.route("**/api/social-trends/collect", async route => {
      socialRequest = route.request().postDataJSON();
      const ownEvidence={platform:"douyin",platformLabel:"抖音",normalizedModel:"智己L6",text:"智己L6 智能座舱体验",author:"汽车媒体",sourceUrl:"https://www.douyin.com/video/1",matrixContent:true,heat:78,sentiment:"positive",metrics:{likes:1200,comments:80,shares:35,collects:120,views:52000},evidence:{contentHash:"1234567890abcdef"}};
      const competitorEvidence={platform:"weibo",platformLabel:"微博",normalizedModel:"小米YU7",text:"小米YU7 城市体验",author:"电车观察",sourceUrl:"https://weibo.com/detail/2",matrixContent:false,heat:66,sentiment:"positive",metrics:{likes:820,comments:50,shares:20,collects:0,views:0},evidence:{contentHash:"abcdef1234567890"}};
      await route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({ok:true,result:{keyword:"智己L6",statusHint:"已形成可识别热度",confidence:.8,confidenceLabel:"高",snapshot:{id:"gate-snapshot"},items:[{id:"e1",sentiment:"positive"}],platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78,positive:1,negative:0,share:100}],platformShare:[{platform:"douyin",label:"抖音",contentCount:1,heat:78,positive:1,negative:0,share:100}],timeline:[{date:"2026-07-11",heat:78,contentCount:1,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78}]}],timelineUndated:{contentCount:0,heat:0,platforms:[]},hotWords:[{word:"智能座舱",count:3}],ownModelRanking:[{model:"智己L6",heat:78}],modelHeatRanking:[{model:"智己L6",heat:78},{model:"小米YU7",heat:66}],modelComparisons:[{model:"智己L6",role:"own",heat:78,contentCount:1,positiveRate:100,riskCount:0,confidence:.8,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:78}],hotWords:[{word:"智能座舱"}]},{model:"小米YU7",role:"competitor",heat:66,contentCount:1,positiveRate:100,riskCount:0,confidence:.8,platforms:[{platform:"douyin",label:"抖音",contentCount:1,heat:66}],hotWords:[{word:"城市体验"}]}],positiveCompetitorsTop5:[{model:"小米YU7",positiveHeat:66,positiveCount:3,confidence:.8}],contentRanking:[ownEvidence],comparisonEvidence:[ownEvidence,competitorEvidence],creatorRanking:[{author:"汽车媒体",platform:"douyin",heat:78,matrixContent:true}],matrixSummary:{creatorCount:1},commentInsights:{total:12,positive:9,negative:1},contentClusters:[{topic:"智能座舱",contentCount:3,heat:78}],riskTopics:[],hotLists:[{platform:"douyin",platformLabel:"抖音",items:["智能汽车"]}],historyComparison:{available:false,delta:{}},methodology:{heat:"可复算热度口径"},qa:{dualModel:{status:"aligned"},strategyOutput:"基于双模型一致证据形成策略结论"}}})});
    });
    await page.locator('#nav button[data-page="socialtrends"]').click();
    await page.locator("#social-trend-keyword").fill("智己L6");
    const initialCompetitors = await page.locator("#social-trend-competitors button").count();
    if (initialCompetitors < 3) {
      const brandSelect = page.locator("#social-trend-competitor-brand");
      const preferredBrand = brandSelect.locator('option[value="小米汽车"]');
      const brandValue = await preferredBrand.count() ? "小米汽车" : await brandSelect.locator('option:not([value=""])').first().getAttribute("value");
      await brandSelect.selectOption(brandValue);
      const modelSelect = page.locator("#social-trend-competitor-add");
      const preferredModel = modelSelect.locator('option[value="小米YU7"]');
      const modelValue = await preferredModel.count() ? "小米YU7" : await modelSelect.locator('option:not([value=""])').first().getAttribute("value");
      await modelSelect.selectOption(modelValue);
    }
    await page.locator("#social-trend-run").click();
    await page.waitForSelector(".social-ranking tbody tr");
    const socialSurface = await page.evaluate(() => ({active:document.querySelector("#socialtrends")?.classList.contains("active"),status:document.querySelector("#social-trend-status")?.textContent||"",rows:document.querySelectorAll(".social-ranking tbody tr").length,source:document.querySelector(".social-ranking a")?.getAttribute("href")||"",kpis:document.querySelectorAll(".social-kpi-grid article").length,boards:document.querySelectorAll(".social-board-grid .panel").length,comparisonModels:document.querySelectorAll(".social-model-comparison").length,evidenceModels:[...document.querySelectorAll(".social-model-tag")].map(x=>x.textContent),rawMetrics:document.querySelectorAll(".social-raw-metrics").length,segments:document.querySelectorAll(".social-segment-row button").length,logos:document.querySelectorAll(".platform-logo,.social-platform-badge i").length,progress:document.querySelector('#socialtrends [role="progressbar"]')?.getAttribute("aria-valuenow"),competitors:document.querySelectorAll("#social-trend-competitors button").length,competitorBoard:document.querySelector(".social-bar-list.competitors")?.textContent||"",importLabel:document.querySelector("#social-trend-import")?.textContent,thresholds:["douyin","xiaohongshu","weibo"].map(x=>Number(document.querySelector(`#social-threshold-${x}`)?.value)),keyCopy:/密钥|API Key|后端/.test(document.querySelector("#socialtrends")?.textContent||"")}));
    await page.screenshot({path:"output/playwright/social-trend-dashboard.png",fullPage:true});
    await page.locator(".social-bar-list.competitors").screenshot({path:"output/playwright/social-positive-benchmark.png"});
    const benchmarkSurface=await page.evaluate(()=>({model:document.querySelector(".social-own-benchmark b")?.textContent||"",heat:document.querySelector(".social-own-benchmark>em")?.textContent||"",firstCompetitorRank:document.querySelector(".social-own-benchmark+li>b>i")?.textContent||""}));
    await page.locator(".social-risk-trigger").click();
    await page.waitForSelector(".social-risk-popover:not([hidden])");
    const riskSurface=await page.evaluate(()=>({expanded:document.querySelector(".social-risk-trigger")?.getAttribute("aria-expanded"),title:document.querySelector(".social-risk-popover li b")?.textContent||"",source:document.querySelector(".social-risk-popover li a")?.getAttribute("href")||""}));
    await page.locator(".social-risk-trigger").screenshot({path:"output/playwright/social-risk-popover.png"});
    await page.screenshot({path:"output/playwright/social-risk-popover-full.png",fullPage:true});
    await page.locator("[data-social-risk-close]").click();
    add("social trend center renders full dashboard progress and evidence drill-down", socialSurface.active && /分析完成/.test(socialSurface.status) && socialSurface.progress === "100" && socialSurface.segments === 9 && socialSurface.logos >= 4 && socialSurface.kpis === 4 && socialSurface.boards === 4 && socialSurface.rows >= 1 && /douyin/.test(socialSurface.source) && !socialSurface.keyCopy, JSON.stringify(socialSurface));
    add("social trend competitor picker uses the model library and submits at most three models", socialSurface.competitors > 0 && socialSurface.competitors <= 3 && socialRequest.competitors?.length === socialSurface.competitors && socialRequest.competitors.length <= 3 && /小米YU7/.test(socialSurface.competitorBoard), JSON.stringify({socialSurface,socialRequest}));
    add("positive competitor board exposes own-model benchmark on the same scale", /智己L6/.test(benchmarkSurface.model) && benchmarkSurface.heat === "78" && benchmarkSurface.firstCompetitorRank === "1", JSON.stringify(benchmarkSurface));
    add("risk KPI opens exact negative content with a source link", riskSurface.expanded === "true" && /车机偶发卡顿/.test(riskSurface.title) && /xiaohongshu/.test(riskSurface.source), JSON.stringify(riskSurface));
    await page.locator('[data-social-time="custom"]').click();
    await page.locator("#social-start-date").fill("2026-07-01");
    await page.locator("#social-end-date").fill("2026-07-07");
    await page.locator("#social-trend-run").click();
    await page.waitForFunction(() => document.querySelector('#socialtrends [role="progressbar"]')?.getAttribute("aria-valuenow") === "100");
    add("social trend custom dates are submitted exactly through the background job", socialRequest.timeRange === "custom" && socialRequest.startDate === "2026-07-01" && socialRequest.endDate === "2026-07-07", JSON.stringify(socialRequest));
    add("social trend import uses exact button label and default platform thresholds", socialSurface.importLabel === "导入数据" && JSON.stringify(socialSurface.thresholds) === JSON.stringify([8000,500,500]), JSON.stringify({label:socialSurface.importLabel,thresholds:socialSurface.thresholds}));
    add("selected competitors appear in comparison metrics", socialSurface.comparisonModels === 2 && /小米YU7/.test(socialSurface.competitorBoard), JSON.stringify(socialSurface));
    await page.locator('[data-social-evidence-scope="competitor"]').click();
    const competitorEvidenceView = await page.evaluate(() => ({models:[...document.querySelectorAll(".social-model-tag")].map(x=>x.textContent),rows:document.querySelectorAll(".social-ranking tbody tr").length,platformButtons:document.querySelectorAll("[data-social-evidence-platform]").length}));
    add("evidence title filters switch from own model to competitor ranking", competitorEvidenceView.rows === 1 && competitorEvidenceView.models.every(x=>/小米YU7/.test(x)) && competitorEvidenceView.platformButtons === 2, JSON.stringify(competitorEvidenceView));
    await page.locator('[data-social-evidence-scope="all"]').click();
    await page.locator('[data-social-result-model="小米YU7"]').click();
    const filteredComparison = await page.evaluate(() => ({models:document.querySelectorAll(".social-model-comparison").length,rows:document.querySelectorAll(".social-ranking tbody tr").length,ownActive:document.querySelector('[data-social-result-model="智己L6"]')?.classList.contains("active")}));
    add("result model tags filter comparison charts and evidence while own model stays selected", filteredComparison.models === 1 && filteredComparison.rows === 1 && filteredComparison.ownActive, JSON.stringify(filteredComparison));
    await page.locator('[data-social-result-model="小米YU7"]').click();
    await page.route("**/api/social-trends/import?**", route => route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({ok:true,result:{keyword:"智己L6",statusHint:"未形成高热度",confidence:.5,confidenceLabel:"中",items:[],platforms:[{platform:"douyin",label:"抖音",contentCount:0,heat:0,positive:0,negative:0,share:0}],platformShare:[{platform:"douyin",label:"抖音",contentCount:0,heat:0,positive:0,negative:0,share:0}],timeline:[],timelineUndated:{contentCount:0,heat:0,platforms:[]},hotWords:[],ownModelRanking:[{model:"智己L6",heat:0,contentCount:0}],modelHeatRanking:[{model:"智己L6",heat:0,contentCount:0}],modelComparisons:[{model:"智己L6",role:"own",heat:0,contentCount:0,positiveRate:0,riskCount:0,confidence:.5,platforms:[],hotWords:[]}],comparisonEvidence:[],positiveCompetitorsTop5:[],contentRanking:[],creatorRanking:[],matrixSummary:{creatorCount:0},commentInsights:{total:0,positive:0,negative:0},contentClusters:[],riskTopics:[],hotLists:[],historyComparison:{available:false,delta:{}},admission:{inputCount:4,admittedCount:2,rejectedCount:2,duplicateCount:0,thresholds:{douyin:8000,xiaohongshu:500,weibo:500}},qa:{dualModel:{status:"insufficient_evidence"},strategyOutput:"证据不足"}}})}));
    await page.locator("#social-trend-import-file").setInputFiles({name:"社媒助手.csv",mimeType:"text/csv",buffer:Buffer.from("平台,标题,点赞数\\n抖音,智己L6,9000")});
    await page.waitForSelector(".social-import-summary");
    const importSurface=await page.evaluate(()=>({label:document.querySelector("#social-trend-import")?.textContent,summary:document.querySelector(".social-import-summary")?.textContent||"",thresholds:["douyin","xiaohongshu","weibo"].map(x=>Number(document.querySelector(`#social-threshold-${x}`)?.value))}));
    add("social assistant file import renders admission summary with default thresholds",importSurface.label==="导入数据"&&/导入记录4/.test(importSurface.summary)&&/有效入池2/.test(importSurface.summary)&&JSON.stringify(importSurface.thresholds)===JSON.stringify([8000,500,500]),JSON.stringify(importSurface));
    await page.unroute("**/api/social-trends/import?**");
    await page.unroute("**/api/social-trends/jobs");
  } finally {
    await browser.close();
  }

  const failed = checks.filter(check => !check.pass);
  console.log(JSON.stringify({ checks, failed, runtimeErrors }, null, 2));
  if (failed.length || runtimeErrors.length) process.exitCode = 1;
}

main().catch(error => { console.error(error); process.exitCode = 1; });
