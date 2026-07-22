let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (error) {
  if (error?.code !== "MODULE_NOT_FOUND") throw error;
  ({ chromium } = require("playwright-core"));
}

const baseUrl = process.env.MMN_URL || "http://localhost:8765/";
const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const username = process.env.MMN_USERNAME || "";
const password = process.env.MMN_PASSWORD || "";
const viewports = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "mobile", width: 390, height: 844 },
];

const checks = [];
const runtimeErrors = [];
const failedResponses = [];
const add = (name, pass, detail = "") => checks.push({ name, pass: Boolean(pass), detail });

async function ensureAuthenticated(page) {
  const loginScreen = page.locator("#cloud-login-screen");
  await page.waitForFunction(() => {
    const screen = document.querySelector("#cloud-login-screen");
    return !screen || screen.hidden || document.body.classList.contains("cloud-auth-required");
  });
  if (!(await loginScreen.isVisible())) return;
  if (!username || !password) throw new Error("Cloud login is required; set MMN_USERNAME and MMN_PASSWORD for this gate.");
  await page.locator('#cloud-login-form input[name="username"]').fill(username);
  await page.locator('#cloud-login-form input[name="password"]').fill(password);
  await page.locator("#cloud-login-form button[type=submit]").click();
  await loginScreen.waitFor({ state: "hidden" });
}

async function auditViewport(browser, viewport) {
  const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
  page.on("pageerror", error => runtimeErrors.push(`${viewport.name}: ${String(error.message || error)}`));
  page.on("console", message => {
    if (message.type() === "error") runtimeErrors.push(`${viewport.name}: ${message.text()}`);
  });
  page.on("response", response => {
    const url = response.url();
    if (response.status() >= 400 && url.startsWith(baseUrl)) {
      failedResponses.push(`${viewport.name}: ${response.status()} ${response.request().method()} ${url}`);
    }
  });

  try {
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
    await page.reload({ waitUntil: "domcontentloaded" });
    await ensureAuthenticated(page);
    await page.waitForSelector("#dashboard");
    await page.waitForTimeout(500);

    const identityState = await page.evaluate(() => {
      const cases = ["乐道L60", "银河L6", "智己L6", "智己LS7", "L60"];
      return Object.fromEntries(cases.map(model => [model, {
        brand: brandForDisplay(model),
        family: standardIdentityFor(model)?.model_family || "",
      }]));
    });
    add(
      `${viewport.name}: brand-model ownership rules stay clean`,
      identityState["乐道L60"].brand === "乐道"
        && identityState["银河L6"].brand === "吉利银河"
        && identityState["智己L6"].brand === "智己"
        && identityState["智己LS7"].brand === "智己"
        && identityState.L60.brand === "待人工确认",
      JSON.stringify(identityState),
    );

    const navSelector = '#nav button[data-page]:not([hidden])';
    const pageIds = await page.locator(navSelector).evaluateAll(nodes => nodes.map(node => node.dataset.page));
    add(`${viewport.name}: all customer navigation entries are present`, pageIds.length === 19, JSON.stringify(pageIds));

    for (const pageId of pageIds) {
      const button = page.locator(`${navSelector}[data-page="${pageId}"]`);
      await button.evaluate(node => {
        [...node.closest("#nav").querySelectorAll("details")]
          .filter(details => details.contains(node))
          .forEach(details => { details.open = true; });
      });
      await button.scrollIntoViewIfNeeded();
      await button.click();
      await page.waitForTimeout(180);
      const state = await page.evaluate(currentPageId => {
        const expectedPageId = currentPageId === "bloggerskill" || currentPageId === "founder" ? "videos" : currentPageId;
        const activePages = [...document.querySelectorAll("main .page.active")];
        const activeNav = [...document.querySelectorAll("#nav button.active[data-page]")].map(node => node.dataset.page);
        const activePage = document.getElementById(expectedPageId);
        return {
          currentPageId,
          expectedPageId,
          activeNav,
          activePages: activePages.map(node => node.id),
          expectedActive: Boolean(activePage?.classList.contains("active")),
          contentLength: (activePage?.innerText || "").replace(/\s+/g, "").length,
          title: document.querySelector("#page-title")?.textContent.trim() || "",
          horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        };
      }, pageId);
      add(
        `${viewport.name}: ${pageId} opens one usable surface`,
        state.activeNav.length === 1
          && state.activeNav[0] === pageId
          && state.activePages.length === 1
          && state.expectedActive
          && state.contentLength >= 20
          && state.title.length > 0
          && state.horizontalOverflow <= 1,
        JSON.stringify(state),
      );
    }

    await page.locator(`${navSelector}[data-page="dashboard"]`).click();
    await page.locator('[data-domestic-mode="management"]').click();
    await page.waitForSelector("#group-dashboard-root [data-group-view]");
    const groupViews = page.locator("#group-dashboard-root [data-group-view]");
    const viewCount = await groupViews.count();
    add(`${viewport.name}: management dashboard exposes eight views`, viewCount === 8, String(viewCount));
    for (let index = 0; index < viewCount; index += 1) {
      await groupViews.nth(index).click();
      const state = await page.locator("#group-dashboard-root").evaluate((root, currentIndex) => ({
        selected: root.querySelectorAll('[data-group-view][aria-selected="true"]').length,
        visiblePanels: [...root.querySelectorAll("[data-group-panel]")].filter(panel => !panel.hidden).length,
        progress: root.querySelector("[data-group-view-progress]")?.textContent.trim() || "",
        activeTextLength: (root.querySelector("[data-group-panel]:not([hidden])")?.innerText || "").replace(/\s+/g, "").length,
        expectedProgress: `${currentIndex + 1} / 8`,
        horizontalOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        overflowNodes: [...root.querySelectorAll("[data-group-panel]:not([hidden]) *")]
          .map(node => ({ node, rect: node.getBoundingClientRect() }))
          .filter(({ rect }) => rect.right > document.documentElement.clientWidth + 1)
          .slice(0, 8)
          .map(({ node, rect }) => ({
            tag: node.tagName.toLowerCase(),
            className: typeof node.className === "string" ? node.className : "",
            right: Math.round(rect.right),
            width: Math.round(rect.width),
          })),
      }), index);
      add(
        `${viewport.name}: management view ${index + 1} is independently usable`,
        state.selected === 1
          && state.visiblePanels === 1
          && state.progress === state.expectedProgress
          && state.activeTextLength >= 20
          && state.horizontalOverflow <= 1,
        JSON.stringify(state),
      );
    }

    await groupViews.nth(2).click();
    const e7xWarning = page.locator("#group-dashboard-root [data-warning-series-id]").filter({ hasText: "奥迪E7X" }).first();
    await e7xWarning.click();
    await page.waitForFunction(() => document.querySelector("#summary-own-model")?.value === "奥迪E7X");
    const e7xLinkage = await page.evaluate(() => ({
      contextModel: state.config.model,
      datasetModels: state.models || [],
      rowModels: [...new Set((state.rows || []).map(row => row[0]))],
      ownSelector: document.querySelector("#summary-own-model")?.value || "",
      competitorConfig: state.config.competitor,
      sellingPointModel: document.querySelector("#selling-point-model-select")?.value || "",
      attributeCount: new Set((state.rows || []).filter(row => row[0] === "奥迪E7X").map(row => row[4])).size,
      attributeSources: [...new Set((state.rows || []).map(row => row[2]))],
      rowCount: (state.rows || []).length,
      platformVolumeCount: Object.keys(state.summaryHeat?.["奥迪E7X"]?.platformVolume || {}).length,
      platformNsrCount: Object.keys(state.summaryPlatformNsr?.["奥迪E7X"] || {}).length,
      sourceNote: state.sourceNote || "",
    }));
    const expectedE7xModels = ["小米YU7", "Model Y", "问界M7", "奥迪E7X", "奥迪Q6L e-tron"];
    add(
      `${viewport.name}: E7X selection binds the matching product dataset and downstream model context`,
      e7xLinkage.contextModel === "奥迪E7X"
        && e7xLinkage.ownSelector === "奥迪E7X"
        && e7xLinkage.sellingPointModel === "奥迪E7X"
        && expectedE7xModels.every(model => e7xLinkage.datasetModels.includes(model))
        && !e7xLinkage.datasetModels.includes("小米SU7")
        && expectedE7xModels.every(model => e7xLinkage.rowModels.includes(model))
        && e7xLinkage.rowCount === 207
        && e7xLinkage.attributeCount === 15
        && ["全网", "垂媒车主口碑", "抖音"].every(source => e7xLinkage.attributeSources.includes(source))
        && e7xLinkage.platformVolumeCount === 9
        && e7xLinkage.platformNsrCount === 7
        && expectedE7xModels.filter(model => model !== "奥迪E7X").every(model => e7xLinkage.competitorConfig.includes(model))
        && e7xLinkage.sourceNote.includes("AUDI E7X等5车产品评价_0710_v2.xlsx"),
      JSON.stringify(e7xLinkage),
    );

    const staleSameModelUpgrade = await page.evaluate(async () => {
      const response = await fetch("/api/group-dashboard-demo?edition=china", {
        credentials: "same-origin",
        headers: typeof authHeaders === "function" ? authHeaders() : {},
      });
      const payload = await response.json();
      state.datasetVersion = "legacy_cached_e7x";
      state.productEvaluationBoundModel = "奥迪E7X";
      state.rows = (state.rows || []).filter(row => row[0] === "奥迪E7X" && row[2] === "全网").slice(0, 15);
      state.summaryHeat = Object.fromEntries(Object.entries(state.summaryHeat || {}).map(([model, item]) => [model, { ...item, platformVolume: {} }]));
      state.summaryPlatformNsr = Object.fromEntries(Object.entries(state.summaryPlatformNsr || {}).map(([model, item]) => [model, Object.fromEntries(Object.entries(item || {}).filter(([platform]) => ["全网", "垂媒车主口碑", "抖音"].includes(platform))) ]));
      registerProductEvaluation(payload.productEvaluation);
      return {
        datasetVersion: state.datasetVersion,
        boundModel: state.productEvaluationBoundModel,
        rowCount: (state.rows || []).length,
        rowModels: [...new Set((state.rows || []).map(row => row[0]))],
        attributeSources: [...new Set((state.rows || []).map(row => row[2]))],
        platformVolumeCount: Object.keys(state.summaryHeat?.["奥迪E7X"]?.platformVolume || {}).length,
        platformNsrCount: Object.keys(state.summaryPlatformNsr?.["奥迪E7X"] || {}).length,
      };
    });
    add(
      `${viewport.name}: stale same-model browser cache upgrades to the complete server dataset`,
      staleSameModelUpgrade.datasetVersion !== "legacy_cached_e7x"
        && staleSameModelUpgrade.boundModel === "奥迪E7X"
        && staleSameModelUpgrade.rowCount === 207
        && expectedE7xModels.every(model => staleSameModelUpgrade.rowModels.includes(model))
        && ["全网", "垂媒车主口碑", "抖音"].every(source => staleSameModelUpgrade.attributeSources.includes(source))
        && staleSameModelUpgrade.platformVolumeCount === 9
        && staleSameModelUpgrade.platformNsrCount === 7,
      JSON.stringify(staleSameModelUpgrade),
    );

    const warningModels = await page.locator("#group-dashboard-root [data-warning-series-id]").evaluateAll(items => [...new Set(items.map(item => item.closest(".sales-warning-row")?.querySelector(".sales-warning-model b")?.textContent?.trim()).filter(Boolean))]);
    for (const model of warningModels) {
      await page.evaluate(target => window.MMNVehicleContext.select(target, { source: "sales-warning", notify: false }), model);
      await page.waitForFunction(target => state.config.model === target && state.productEvaluationBoundModel === target, model);
      const binding = await page.evaluate(target => {
        const unavailable = state.importQuality?.kind === "PRODUCT_EVALUATION_UNAVAILABLE";
        const supported = [...new Set([...(state.models || []), ...Object.keys(state.summaryHeat || {}), ...Object.keys(state.summaryPlatformNsr || {}), ...(state.rows || []).map(row => row[0])])];
        return {
          target,
          contextModel: state.config.model,
          boundModel: state.productEvaluationBoundModel,
          sellingPointModel: document.querySelector("#selling-point-model-select")?.value || "",
          unavailable,
          datasetModels: state.models || [],
          rowCount: (state.rows || []).length,
          summaryModelCount: Object.keys(state.summaryHeat || {}).length,
          supported,
          sourceNote: state.sourceNote || "",
        };
      }, model);
      const unavailableIsClean = !binding.unavailable
        || (binding.datasetModels.length === 1
          && binding.datasetModels[0] === model
          && binding.rowCount === 0
          && binding.summaryModelCount === 0
          && binding.sourceNote.includes(model)
          && binding.sourceNote.includes("已清除上一车型数据"));
      add(
        `${viewport.name}: ${model} never reuses the previously selected model dataset`,
        binding.contextModel === model
          && binding.boundModel === model
          && binding.sellingPointModel === model
          && binding.supported.includes(model)
          && unavailableIsClean,
        JSON.stringify(binding),
      );
    }

    await page.evaluate(() => window.MMNVehicleContext.select("奥迪E7X", { source: "sales-warning", notify: false }));
    await page.waitForFunction(() => state.config.model === "奥迪E7X" && state.productEvaluationBoundModel === "奥迪E7X");
    const restoredE7x = await page.evaluate(() => ({
      models: state.models || [],
      rowModels: [...new Set((state.rows || []).map(row => row[0]))],
      attributeCount: new Set((state.rows || []).filter(row => row[0] === "奥迪E7X").map(row => row[4])).size,
      rowCount: (state.rows || []).length,
      platformVolumeCount: Object.keys(state.summaryHeat?.["奥迪E7X"]?.platformVolume || {}).length,
      sellingPointModel: document.querySelector("#selling-point-model-select")?.value || "",
    }));
    add(
      `${viewport.name}: a registered model dataset restores after visiting models without product data`,
      restoredE7x.models.includes("奥迪E7X")
        && expectedE7xModels.every(model => restoredE7x.rowModels.includes(model))
        && restoredE7x.rowCount === 207
        && restoredE7x.attributeCount === 15
        && restoredE7x.platformVolumeCount === 9
        && restoredE7x.sellingPointModel === "奥迪E7X",
      JSON.stringify(restoredE7x),
    );

    await page.screenshot({ path: `output/playwright/all-surfaces-${viewport.width}.png`, fullPage: true });
  } finally {
    await page.close();
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  try {
    for (const viewport of viewports) await auditViewport(browser, viewport);
  } finally {
    await browser.close();
  }

  const failed = checks.filter(check => !check.pass);
  console.log(JSON.stringify({ checks, failed, runtimeErrors, failedResponses }, null, 2));
  if (failed.length || runtimeErrors.length || failedResponses.length) process.exitCode = 1;
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
