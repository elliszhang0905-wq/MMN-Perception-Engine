const { chromium } = require("playwright");
const fs = require("fs");

const chromePath = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const baseUrl = process.env.MMN_URL || "http://127.0.0.1:8765/";

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on("pageerror", e => errors.push(String(e.message || e)));
  page.on("console", msg => {
    if (["error", "warning"].includes(msg.type())) errors.push(`${msg.type()}: ${msg.text()}`);
  });

  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
  await page.reload({ waitUntil: "networkidle" });

  const checks = [];
  const add = (name, pass, detail = undefined) => checks.push({ name, pass: Boolean(pass), detail });

  const logoBox = await page.locator(".brand-logo").boundingBox();
  const sideBox = await page.locator(".sidebar").boundingBox();
  const noteBox = await page.locator(".side-note").boundingBox();
  add("logo stays inside sidebar", logoBox && sideBox && logoBox.width <= 190 && logoBox.height <= 112 && logoBox.x >= sideBox.x && logoBox.y >= sideBox.y && logoBox.x + logoBox.width <= sideBox.x + sideBox.width, { logoBox, sideBox });
  add("side note stays fully visible", noteBox && sideBox && noteBox.y >= sideBox.y && noteBox.y + noteBox.height <= sideBox.y + sideBox.height, { noteBox, sideBox });
  add("china edition uses cn logo", await page.locator(".brand-logo").getAttribute("src").then(src => src.includes("mmn-logo-cn-line-cropped")).catch(() => false));
  add("edition switch defaults to china", await page.locator(".edition-switch").evaluate(el => el.querySelector('[data-edition="china"]')?.classList.contains("active")).catch(() => false));
  add("china edition chrome renders", await page.locator("#edition-eyebrow").innerText().then(t => t.includes("CHINA AUTO")).catch(() => false));
  add("header action buttons removed", await page.locator("#account-button,#reset-demo,#export-gamma,#export-pptx,#export-report").count().then(n => n === 0));
  add("china sales marquee renders", await page.locator("#sales-marquee").isVisible().catch(() => false));
  await page.waitForFunction(() => /销量|懂车帝|Top/.test(document.querySelector("#sales-marquee-track")?.innerText || ""), null, { timeout: 15000 }).catch(() => {});
  add("sales marquee has sales copy", await page.locator("#sales-marquee-track").innerText().then(t => t.includes("销量") || t.includes("懂车帝") || t.includes("Top")).catch(() => false));

  const pages = ["dashboard", "data", "cognition", "vertical", "videos", "actions", "knowhow", "strategykb", "learning", "architecture", "workspace", "config"];
  for (const pageName of pages) {
    await page.locator(`#nav button[data-page="${pageName}"]`).click();
    add(`nav opens ${pageName}`, await page.locator(`#${pageName}.page.active`).count() === 1);
  }

  await page.locator('#nav button[data-page="dashboard"]').click();
  add("dashboard import bar visible", await page.locator(".dashboard-import").isVisible());
  add("dashboard embeds data center", await page.locator("#dashboard-data-table tbody tr").count().then(n => n > 0));
  add("dashboard embeds cognition diagnosis", await page.locator("#dashboard-cognition-table tbody tr").count().then(n => n > 0));
  let dashboardChooserOk = false;
  const dashboardChooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { dashboardChooserOk = true; }).catch(() => {});
  await page.locator('.dashboard-import [data-file-target="xlsx-file"]').click();
  await dashboardChooser;
  add("dashboard import opens file chooser", dashboardChooserOk);

  await page.locator('#nav button[data-page="vertical"]').click();
  const verticalImport = page.locator('[data-file-target="vertical-xlsx-file"]');
  const importStyle = await verticalImport.evaluate(el => ({
    color: getComputedStyle(el).color,
    bg: getComputedStyle(el).backgroundImage || getComputedStyle(el).backgroundColor,
    rect: el.getBoundingClientRect().toJSON()
  }));
  add("vertical import button visible", importStyle.rect.width >= 50 && importStyle.rect.height >= 36 && importStyle.color !== "rgba(0, 0, 0, 0)", importStyle);
  let fileChooserOk = false;
  const chooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { fileChooserOk = true; }).catch(() => {});
  await verticalImport.click();
  await chooser;
  add("vertical import opens file chooser", fileChooserOk);
  const verticalSample = "/Users/ellis/Downloads/jp5_20260609210005316742.xlsx";
  if (fs.existsSync(verticalSample)) {
    const importResult = await page.evaluate(async ({ name, bytes }) => {
      const res = await fetch(`/api/import-vertical-xlsx?filename=${encodeURIComponent(name)}`, {
        method: "POST",
        body: new Uint8Array(bytes)
      });
      return res.json();
    }, { name: "jp5_20260609210005316742.xlsx", bytes: Array.from(fs.readFileSync(verticalSample)) });
    const shares = (importResult.dataset?.items || []).map(x => Number(x.share)).filter(Number.isFinite);
    const maxShare = Math.max(0, ...shares);
    const badShareText = shares.some(v => {
      const rendered = `${(v > 1 ? v : v * 100).toFixed(1)}%`;
      return Number(rendered.replace("%", "")) > 100;
    });
    add("vertical share values are normalized", importResult.ok && maxShare <= 1 && !badShareText, { maxShare, count: shares.length });
  }

  await page.locator('#nav button[data-page="videos"]').click();
  add("content asset subnav visible in china", await page.locator("#content-subnav").evaluate(el => !el.hidden).catch(() => false));
  await page.waitForFunction(() => /已识别Chrome采集插件|未识别插件/.test(document.querySelector("#social-plugin-status")?.innerText || ""), null, { timeout: 10000 }).catch(() => {});
  add("social plugin bridge panel renders", await page.locator("#social-plugin-panel").innerText().then(t => t.includes("采集插件") && t.includes("抖音采集") && t.includes("小红书采集")).catch(() => false));
  await page.locator('[data-content-view="douyinCreators"]').click();
  add("douyin creator library opens", await page.locator("#creator-library-title").innerText().then(t => t.includes("抖音达人库")).catch(() => false));
  add("douyin creator cards render", await page.locator(".creator-card").count().then(n => n >= 3));
  await page.locator('[data-content-view="xhsCreators"]').click();
  add("xiaohongshu creator library opens", await page.locator("#creator-library-title").innerText().then(t => t.includes("小红书达人库")).catch(() => false));
  add("creator recommendation flow renders", await page.locator("#creator-planner-flow div").count().then(n => n >= 6));
  await page.locator('[data-content-view="assets"]').click();

  await page.locator('#nav button[data-page="data"]').click();
  add("data center has model buttons", await page.locator("#data-model-filter button").count().then(n => n >= 2));
  add("data center has traffic buttons", await page.locator("#data-traffic-filter button").count().then(n => n >= 4));
  add("data center visual panels render", await page.locator(".data-bars .data-bar").count().then(n => n >= 4));
  add("data center traffic chart renders", await page.locator("#data-traffic-chart .data-bar").count().then(n => n > 0));
  await page.locator("#data-emotion-chart .data-bar").first().click();
  add("emotion drill opens", await page.locator("#data-drill-dialog[open]").count().then(n => n === 1));
  add("emotion drill includes planning", await page.locator("#data-drill-body").innerText().then(t => t.includes("下一步营销规划") && t.includes("按平台拆")).catch(() => false));
  add("emotion drill includes knowhow rag and word cloud", await page.locator("#data-drill-body").innerText().then(t => t.includes("Know-how") && t.includes("RAG引用依据") && t.includes("词云分类")).catch(() => false));
  add("emotion drill has one MMN strategy button", await page.locator("[data-strategy-engine]").count().then(n => n === 1));
  add("emotion drill hides model brand buttons", await page.locator("[data-strategy-engine]").innerText().then(t => t.includes("MMN策略") && !t.includes("千问") && !t.includes("ChatGPT")));
  await page.locator("#data-drill-close").click();
  await page.locator('#data-traffic-filter [data-traffic-type="自然声量"]').click();
  add("data center traffic filter works", await page.locator("#data-table tbody tr").count().then(n => n > 0));
  await page.locator('#data-traffic-filter [data-traffic-type="all"]').click();
  const firstModelButton = page.locator('#data-model-filter button:not(.active)').first();
  if (await firstModelButton.count()) {
    await firstModelButton.click();
    add("data center model filter works", await page.locator("#data-table tbody tr").count().then(n => n > 0));
  }
  let dataChooserOk = false;
  const dataChooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { dataChooserOk = true; }).catch(() => {});
  await page.locator('#data [data-file-target="xlsx-file"]').click();
  await dataChooser;
  add("main data import opens file chooser", dataChooserOk);

  await page.locator("#add-row").click();
  add("add row dialog opens", await page.locator("#row-dialog[open]").count() === 1);
  await page.keyboard.press("Escape");

  await page.locator('#nav button[data-page="strategykb"]').click();
  await page.locator("#strategy-kb-input").fill("价格焦虑处理方法：当小红书自然声量中用户认为价格贵、权益不清晰时，优先用真实车主账本、总拥有成本、同级配置对比来降低焦虑。适用平台：小红书、抖音。适用阶段：上市期、口碑修复期。");
  await page.locator("#import-strategy-kb").click();
  await page.locator("#import-rag-seed").click();
  await page.waitForTimeout(500);
  add("MMN RAG training package imports", await page.locator("#strategy-kb-count").innerText().then(t => Number(t.replace(/\D/g, "")) >= 83).catch(() => false));
  add("RAG knowledge map renders clusters", await page.locator(".kb-cluster").count().then(n => n >= 4));
  add("RAG knowledge map sits below console", await page.locator("#strategykb").evaluate(() => {
    const results = document.querySelector("#rag-results")?.getBoundingClientRect();
    const map = document.querySelector("#strategy-kb-map")?.getBoundingClientRect();
    return results && map && map.top > results.bottom;
  }).catch(() => false));
  await page.locator(".kb-cluster").filter({ hasText: "智己" }).first().click().catch(async() => page.locator(".kb-cluster").first().click());
  add("knowledge cluster click triggers pulse", await page.locator(".kb-cluster.active").evaluate(el => el.classList.contains("focus-pulse")).catch(() => false));
  add("RAG cluster drill renders details", await page.locator(".kb-cluster-detail").innerText().then(t => t.includes("条知识") && t.includes("巡检这个气泡")).catch(() => false));
  await page.locator("[data-kb-query]").first().click();
  await page.waitForTimeout(300);
  add("RAG cluster inspection stays collapsed", await page.locator("#rag-results .rag-card").count().then(n => n === 0));
  await page.locator("#rag-results-toggle").click();
  add("RAG cluster can expand inspection", await page.locator("#rag-results .rag-card").count().then(n => n > 0));
  await page.locator("#rag-query").fill("智己LS8 最大传播问题 下一阶段怎么打");
  add("RAG console uses fast and deep strategy CTAs", await page.locator("#run-rag-search").innerText().then(t => t.includes("MMN快速策略")).catch(() => false) && await page.locator("#run-rag-deep-strategy").innerText().then(t => t.includes("MMN深度策略")).catch(() => false));
  await page.locator("#run-rag-search").click();
  await page.waitForSelector(".mmn-ai-bubble:not(.loading)", { timeout: 30000 }).catch(() => {});
  add("MMN fast strategy returns chat bubble", await page.locator("#rag-results").innerText().then(t => t.includes("MMN快速策略") && t.includes("该策略由MMN营销引擎输出")).catch(() => false));
  await page.locator("#rag-results-toggle").click();
  add("RAG recalls imported MMN corpus", await page.locator("#rag-results").innerText().then(t => t.includes("智己LS8") && t.includes("MMN-AUTO")).catch(() => false));
  await page.locator("#rag-query").fill("小红书 价格 焦虑");
  await page.locator("#run-rag-search").click();
  await page.waitForSelector(".mmn-ai-bubble:not(.loading)", { timeout: 30000 }).catch(() => {});
  await page.locator("#rag-results-toggle").click();
  add("rag search returns references", await page.locator("#rag-results .rag-card").count().then(n => n > 0));
  let kbChooserOk = false;
  const kbChooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { kbChooserOk = true; }).catch(() => {});
  await page.locator('[data-file-target="strategy-kb-file"]').click();
  await kbChooser;
  add("strategy knowledge upload opens file chooser", kbChooserOk);

  const loginData = await page.evaluate(async () => {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ org: "演示客户", name: "QA", email: "qa@mmn.local" })
    });
    return res.json();
  });
  await page.evaluate(session => localStorage.setItem("mmnCommercialSession", JSON.stringify(session)), loginData.session);
  await page.reload({ waitUntil: "networkidle" });
  await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
  await page.locator('#nav button[data-page="workspace"]').click();
  add("workspace renders hierarchy", await page.locator("#workspace-tree").innerText().then(t => t.includes("集团") || t.includes("演示客户")).catch(() => false));
  add("workspace shows china MMN router", await page.locator("#model-router").innerText().then(t => t.includes("MMN多模态") && t.includes("本土化RAG") && t.includes("本土规则")).catch(() => false));
  await page.locator('[data-edition="global"]').click();
  add("edition switch opens global", await page.locator(".edition-switch").evaluate(el => el.querySelector('[data-edition="global"]')?.classList.contains("active")).catch(() => false));
  add("global edition chrome renders", await page.locator("#edition-eyebrow").innerText().then(t => t.includes("GLOBAL AUTO")).catch(() => false));
  add("global edition keeps original logo", await page.locator(".brand-logo").getAttribute("src").then(src => src.includes("mmn-logo-reverse-cropped")).catch(() => false));
  add("global edition uses isolated project dataset", await page.locator("#dash-project").innerText().then(t => t.includes("Thailand") && !t.includes("智己LS8")).catch(() => false));
  await page.locator('#nav button[data-page="videos"]').click();
  add("global edition hides domestic creator subnav", await page.locator("#content-subnav").evaluate(el => el.hidden).catch(() => false));
  await page.waitForFunction(() => /Thailand Market|Thailand Registration/.test(document.querySelector("#sales-marquee-track")?.innerText || ""), null, { timeout: 10000 }).catch(() => {});
  add("global sales marquee renders thailand market data", await page.locator("#sales-marquee-track").innerText().then(t => t.includes("Thailand Market") && t.includes("Thailand Registration")).catch(() => false));
  add("workspace shows global router", await page.locator("#model-router").innerText().then(t => t.includes("OpenAI") && t.includes("TikTok") && t.includes("多语言RAG")).catch(() => false));
  await page.locator('[data-edition="china"]').click();
  add("china edition restores isolated domestic dataset", await page.locator("#dash-project").innerText().then(t => !t.includes("Thailand")).catch(() => false));
  await page.locator('#nav button[data-page="architecture"]').click();
  add("architecture opens china foundation", await page.locator("#architecture").innerText().then(t => t.includes("国内版数据源") && t.includes("MMN多模态") && t.includes("本土化RAG")).catch(() => false));
  await page.locator('[data-edition="global"]').click();
  add("architecture switches global foundation", await page.locator("#architecture").innerText().then(t => t.includes("出海版数据源") && t.includes("TikTok") && t.includes("OpenAI")).catch(() => false));
  await page.locator('[data-edition="china"]').click();
  await page.locator('#nav button[data-page="workspace"]').click();
  add("workspace has snapshot button", await page.locator("#sync-project-state").isVisible());
  await page.locator("#sync-project-state").click();
  await page.waitForTimeout(600);
  add("workspace snapshot persists", await page.locator("#workspace-snapshots-count").innerText().then(t => Number(t.replace(/,/g, "")) >= 1).catch(() => false));

  const failed = checks.filter(x => !x.pass);
  await browser.close();

  const result = { ok: failed.length === 0 && errors.length === 0, checks, failed, errors };
  console.log(JSON.stringify(result, null, 2));
  if (!result.ok) process.exit(1);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
