const { chromium } = require("playwright");

const baseUrl = process.argv[2] || "http://127.0.0.1:8765/";
const baseOrigin = new URL(baseUrl).origin;
const target = process.env.MMN_VIDEO_TARGET || "一路熟悉，一路新";
const username = process.env.MMN_USERNAME || "";
const password = process.env.MMN_PASSWORD || "";
const startIfMissing = process.env.MMN_VIDEO_START_IF_MISSING === "1";
const forceAnalysis = process.env.MMN_VIDEO_FORCE === "1";

async function ensureAuthenticated(page) {
  const loginScreen = page.locator("#cloud-login-screen");
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await page.waitForFunction(() => {
      const screen = document.querySelector("#cloud-login-screen");
      return !screen || screen.hidden || document.body.classList.contains("cloud-auth-required");
    });
    if (await loginScreen.isVisible().catch(() => false)) {
      if (!username || !password) throw new Error("Cloud login requires MMN_USERNAME and MMN_PASSWORD.");
      await page.locator('#cloud-login-form input[name="username"]').fill(username);
      await page.locator('#cloud-login-form input[name="password"]').fill(password);
      await page.locator("#cloud-login-form button[type=submit]").click();
      await loginScreen.waitFor({ state: "hidden", timeout: 30000 });
    }
    await page.waitForTimeout(750);
    if (!(await loginScreen.isVisible().catch(() => false))) return;
  }
  throw new Error("Cloud login did not remain active.");
}

async function verify(viewport) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  const failedRequests = [];
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("requestfailed", request => failedRequests.push(`${request.method()} ${request.url()}`));
  await page.goto(baseUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
  await page.reload({ waitUntil: "domcontentloaded" });
  await ensureAuthenticated(page);
  const dashboardNav = page.locator('#nav button[data-page="dashboard"]');
  if (await dashboardNav.isVisible().catch(() => false)) await dashboardNav.click();
  await ensureAuthenticated(page);
  const managementMode = page.locator('[data-domestic-mode="management"]');
  if (await managementMode.isVisible().catch(() => false)) await managementMode.click();
  await page.waitForSelector("#douyin-hot-module-mount .douyin-hot-panel", { timeout: 60000 });
  consoleErrors.length = 0;
  failedRequests.length = 0;
  const expand = page.getByRole("button", { name: /展开完整榜单/ }).first();
  if (await expand.isVisible().catch(() => false)) await expand.click();
  const row = target === "__first__"
    ? page.locator(".douyin-hot-row").first()
    : page.locator(".douyin-hot-row").filter({ hasText: target }).first();
  await row.waitFor({ state: "visible", timeout: 30000 });
  let toggle = row.getByRole("button", { name: /查看完整洞察|收起/ });
  if (forceAnalysis) {
    await row.getByRole("button", { name: "重新分析", exact: true }).click();
    await row.getByRole("button", { name: /分析中/ }).waitFor({ state: "visible", timeout: 30000 });
    await row.getByRole("button", { name: /重新分析/ }).waitFor({ state: "visible", timeout: 900000 });
    toggle = row.getByRole("button", { name: /查看完整洞察|收起/ });
  } else if (!(await toggle.isVisible().catch(() => false))) {
    if (!startIfMissing) throw new Error(`Target has no persisted insight: ${target}`);
    await row.getByRole("button", { name: "生成洞察", exact: true }).click();
    await row.getByText(/排队|解析|提取|转写|构建|分析|质检/).first().waitFor({ state: "visible", timeout: 30000 });
    await row.getByRole("button", { name: /重新分析/ }).waitFor({ state: "visible", timeout: 900000 });
    toggle = row.getByRole("button", { name: /查看完整洞察|收起/ });
  }
  if ((await toggle.textContent()).includes("查看")) await toggle.click();
  await row.locator(".douyin-video-insight-detail").waitFor({ state: "visible" });
  await row.getByRole("button", { name: "收起", exact: true }).click();
  await row.locator(".douyin-video-insight-detail").waitFor({ state: "hidden" });
  await row.screenshot({ path: `output/playwright/douyin-video-insight-collapsed-${viewport.width}.png` });
  await row.getByRole("button", { name: "查看完整洞察", exact: true }).click();
  await row.locator(".douyin-video-insight-detail").waitFor({ state: "visible" });
  const fontSizes = await row.evaluate(root => ({
    summary: Number.parseFloat(getComputedStyle(root.querySelector(".douyin-video-insight-summary p")).fontSize),
    sectionTitle: Number.parseFloat(getComputedStyle(root.querySelector(".douyin-video-insight-detail section > b")).fontSize),
    body: Number.parseFloat(getComputedStyle(root.querySelector(".douyin-video-insight-detail p")).fontSize),
    action: Number.parseFloat(getComputedStyle(root.querySelector(".douyin-video-insight-actions button")).fontSize),
  }));
  await row.screenshot({ path: `output/playwright/douyin-video-insight-expanded-${viewport.width}.png` });
  const text = await row.innerText();
  const pageMetrics = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  const required = ["视频本体", "MMN独立分析 1", "MMN独立分析 2", "MMN独立分析 3"];
  const forbidden = ["HTTP 400", "非公网媒体地址", "JSON 对象", "partial", "limited", "V:"];
  const result = {
    viewport, target, status: (await row.locator(".douyin-video-insight-summary span").first().textContent()).trim(), fontSizes,
    required: Object.fromEntries(required.map(value => [value, text.includes(value)])),
    forbidden: forbidden.filter(value => text.includes(value)),
    overflow: pageMetrics.scrollWidth > pageMetrics.innerWidth + 1,
    consoleErrors, failedRequests: failedRequests.filter(url => url.includes(baseOrigin)),
  };
  await page.screenshot({ path: `output/playwright/douyin-video-insight-${viewport.width}.png`, fullPage: false });
  await browser.close();
  if (Object.values(result.required).some(value => !value) || result.forbidden.length || result.overflow
      || result.consoleErrors.length || result.failedRequests.length
      || result.fontSizes.summary < 12 || result.fontSizes.sectionTitle < 11
      || result.fontSizes.body < 11 || result.fontSizes.action < 10) {
    throw new Error(JSON.stringify(result));
  }
  return result;
}

(async () => {
  const results = [];
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    results.push(await verify(viewport));
  }
  process.stdout.write(JSON.stringify(results, null, 2));
})().catch(error => {
  process.stderr.write(`${error.stack || error}\n`);
  process.exit(1);
});
