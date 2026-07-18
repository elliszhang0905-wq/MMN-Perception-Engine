const { chromium } = require("playwright");

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
