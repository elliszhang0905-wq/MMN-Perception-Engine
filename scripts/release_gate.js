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
  add("dashboard uses cache-busted app bundle", /app\.js\?v=/.test(dashboard.appVersion), dashboard.appVersion);

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

  const assetVisualization = await page.evaluate(() => ({
    rows: document.querySelectorAll("#asset-chart .asset-benchmark-row").length,
    bars: document.querySelectorAll("#asset-chart .asset-benchmark-bar").length,
    markers: document.querySelectorAll("#asset-chart .asset-benchmark-marker").length,
    benchmarkLabels: [...document.querySelectorAll("#asset-chart .asset-benchmark-label small")].filter(node => /Benchmark/.test(node.textContent)).length,
    legendColors: new Set([...document.querySelectorAll("#asset-chart .asset-benchmark-legend i")].map(node => node.className)).size,
    cards: document.querySelectorAll("#asset-chart .asset-signal-card").length,
    icons: document.querySelectorAll("#asset-chart svg").length,
    firstRowText: document.querySelector("#asset-chart .asset-benchmark-row")?.textContent.trim() || ""
  }));
  add(
    "asset and liability uses tricolor horizontal bars with benchmark",
    assetVisualization.rows > 0 && assetVisualization.bars === assetVisualization.rows && assetVisualization.markers === assetVisualization.rows && assetVisualization.benchmarkLabels === assetVisualization.rows && assetVisualization.legendColors === 3 && assetVisualization.cards === 0 && assetVisualization.icons === 0 && /Benchmark/.test(assetVisualization.firstRowText),
    JSON.stringify(assetVisualization)
  );
  await page.locator("#asset-chart .asset-benchmark-row").first().click();
  const assetDialog = await page.evaluate(() => ({
    open: document.querySelector("#asset-benchmark-dialog")?.open || false,
    title: document.querySelector("#asset-benchmark-dialog-title")?.textContent.trim() || "",
    rows: document.querySelectorAll("#asset-benchmark-dialog .asset-dialog-row").length,
    ownRows: document.querySelectorAll("#asset-benchmark-dialog .asset-dialog-row.own").length,
    competitorText: document.querySelector("#asset-benchmark-dialog-body")?.textContent.trim() || ""
  }));
  add(
    "asset label opens own and competitor comparison bubble",
    assetDialog.open && assetDialog.rows > 1 && assetDialog.ownRows === 1 && /本品/.test(assetDialog.competitorText) && /竞品/.test(assetDialog.competitorText),
    JSON.stringify(assetDialog)
  );
  await page.locator("#asset-benchmark-dialog-close").click();

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
  const summaryRows = [];
  for (const model of summaryModels) {
    for (const source of ["全网", "垂媒车主口碑", "抖音"]) {
      for (const [label, nsr] of [["外观", .82], ["价格", .62], ["安全", .41]]) {
        summaryRows.push([model, model === "奥迪E7X" ? "本品" : "竞品", source, label === "价格" ? "价格权益" : "安全质量", label, nsr >= 0 ? "认可" : "失望", "未知", "无", 100, 4, 1, 4, "汇总NSR评分", "release-gate", nsr]);
      }
    }
  }
  await page.evaluate(({ summaryModels, summaryRows, summaryHeat }) => {
    localStorage.setItem("mmnEngineState:china", JSON.stringify({
      datasetVersion: "summary_xlsx_audi",
      sourceNote: "已从产品评价汇总表导入。",
      config: { project: "奥迪E7X认知诊断｜产品评价导入", brand: "奥迪", model: "奥迪E7X", competitor: "小米YU7 / Model Y / 问界M7 / 奥迪Q6L e-tron", targetIdentity: "", budget: 800, priorityThreshold: 60, riskThreshold: 500 },
      platforms: { "全网": 1, "垂媒车主口碑": 1.15, "抖音": 1.35 },
      models: summaryModels,
      rows: summaryRows,
      summaryHeat,
      summaryMetrics: { "奥迪E7X": { overallNsr: .7512874630645843 } },
      importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false }, attributeVolumeAvailable: false, message: "源表未提供目标人群、购买意向、标签声量和风险量级。" }
    }));
  }, { summaryModels, summaryRows, summaryHeat });
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
    quadrants: document.querySelectorAll("#dashboard-emotion-quadrant .emotion-quadrant-cell").length
  }));
  add("summary workbook keeps verified NSR and suppresses unsupported metrics", summaryImport.model === "奥迪E7X" && summaryImport.nsr === "75.1%" && summaryImport.ips === "不适用" && /未提供目标人群/.test(summaryImport.ipsNote) && summaryImport.intent === "不适用" && /未提供购买意向/.test(summaryImport.intentNote), JSON.stringify(summaryImport));
  add("summary workbook first renders source-backed all-network heat comparison", summaryImport.surfaceTitle === "全网声量及互动量对比" && summaryImport.selectableModels.length === summaryModels.length && summaryImport.selectedModels.length === summaryModels.length && summaryImport.heatRows.length === summaryModels.length && /^奥迪E7X.*23\.6万.*217\.0万/.test(summaryImport.heatRows[0] || "") && summaryImport.addOptions.length === 1, JSON.stringify(summaryImport));
  add("summary cockpit keeps product fixed and removes system counters", summaryImport.ownModel === "奥迪E7X" && summaryImport.ownLocked && summaryImport.competitorModels.length === summaryModels.length - 1 && !summaryImport.competitorModels.includes("奥迪E7X") && summaryImport.summaryCardsHidden, JSON.stringify(summaryImport));
  add("summary cockpit uses decision language and explains independent scales", summaryImport.productPointName === "当前可用产品点" && summaryImport.scaleNote === "声量与互动量按各自独立尺度展示，不可直接比较绝对柱长。", JSON.stringify(summaryImport));
  add("summary workbook keeps the global brand library separate from imported comparison models", summaryImport.topBrands.length > 10 && summaryImport.topBrands.includes("奥迪") && summaryImport.topBrands.includes("智己") && summaryImport.selectableModels.length === summaryModels.length, JSON.stringify(summaryImport));
  add("summary workbook renders real attribute NSR without emotion quadrants", summaryImport.attributeRows === 3 && summaryImport.attributeValues.length === 9 && summaryImport.attributeValues.every(value => /^-?\d+(?:\.\d)?%$/.test(value)) && summaryImport.quadrants === 0, JSON.stringify(summaryImport));

  await page.locator('[data-summary-heat-model="小米YU7"]').click();
  const platformBubble = await page.evaluate(() => {
    const close = document.querySelector(".summary-platform-popover button");
    const before = close ? getComputedStyle(close, "::before") : null;
    const after = close ? getComputedStyle(close, "::after") : null;
    return {
      title: document.querySelector(".summary-platform-popover header")?.textContent.replace(/\s+/g, " ").trim() || "",
      groups: [...document.querySelectorAll(".summary-platform-group")].map(node => ({
        platform: node.querySelector(".summary-platform-name")?.textContent.trim() || "",
        series: [...node.querySelectorAll(".summary-platform-series>div")].map(series => series.textContent.replace(/\s+/g, " ").trim())
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
  add("competitor heat bubble pairs each platform with the product model", /小米YU7.*奥迪E7X.*分平台声量对比/.test(platformBubble.title) && platformBubble.groups.length === 9 && platformBubble.groups.every(group => group.series.length === 2) && douyinGroup?.series.some(row => /小米YU7.*90\.2万/.test(row)) && douyinGroup?.series.some(row => /本品.*奥迪E7X.*10\.4万/.test(row)), JSON.stringify(platformBubble));
  add("platform bubble close icon is geometrically centered", platformBubble.closeLabel === "关闭分平台声量气泡" && platformBubble.closeText === "" && closeCentered, JSON.stringify(platformBubble.closeGeometry));
  await page.locator(".summary-platform-popover button").click();
  await page.locator('.summary-heat-model-list input[value="小米YU7"]').uncheck();
  const lockedAfterFilter = await page.evaluate(() => ({
    ownLocked: Boolean(document.querySelector(".summary-heat-own input:checked:disabled")),
    rows: [...document.querySelectorAll(".summary-heat-row>b")].map(node => node.textContent.trim())
  }));
  add("competitor filtering cannot remove the product model", lockedAfterFilter.ownLocked && lockedAfterFilter.rows.includes("奥迪E7X") && !lockedAfterFilter.rows.includes("小米YU7"), JSON.stringify(lockedAfterFilter));
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
      summaryMetrics: { "奥迪E7X": { overallNsr: .7512874630645843 } },
      importQuality: { kind: "PRODUCT_EVALUATION_SUMMARY", timeRange: "2026.6.1 - 2026.6.30", metricCoverage: { nsr: true, ips: false, intent: false, risk: false } }
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
