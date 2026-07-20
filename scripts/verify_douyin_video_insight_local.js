const { chromium } = require("playwright");

const baseUrl = process.argv[2] || "http://127.0.0.1:8765/";
const target = "一路熟悉，一路新";

async function verify(viewport) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport });
  const consoleErrors = [];
  const failedRequests = [];
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("requestfailed", request => failedRequests.push(`${request.method()} ${request.url()}`));
  await page.goto(baseUrl, { waitUntil: "networkidle", timeout: 60000 });
  const expand = page.getByRole("button", { name: /展开完整榜单/ }).first();
  if (await expand.isVisible().catch(() => false)) await expand.click();
  const row = page.locator(".douyin-hot-row").filter({ hasText: target }).first();
  await row.waitFor({ state: "visible", timeout: 30000 });
  const toggle = row.getByRole("button", { name: /查看完整洞察|收起/ });
  if ((await toggle.textContent()).includes("查看")) await toggle.click();
  await row.locator(".douyin-video-insight-detail").waitFor({ state: "visible" });
  const text = await row.innerText();
  const pageMetrics = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  const required = ["完整证据", "视频本体", "人工复核入口", "MMN独立分析 1 · 已完成",
                    "MMN独立分析 2 · 已完成", "MMN独立分析 3 · 已完成"];
  const forbidden = ["HTTP 400", "非公网媒体地址", "JSON 对象", "partial", "limited", "V:"];
  const result = {
    viewport, required: Object.fromEntries(required.map(value => [value, text.includes(value)])),
    forbidden: forbidden.filter(value => text.includes(value)),
    overflow: pageMetrics.scrollWidth > pageMetrics.innerWidth + 1,
    consoleErrors, failedRequests: failedRequests.filter(url => url.includes("127.0.0.1:8765")),
  };
  await page.screenshot({ path: `output/playwright/douyin-video-insight-${viewport.width}.png`, fullPage: false });
  await browser.close();
  if (Object.values(result.required).some(value => !value) || result.forbidden.length || result.overflow
      || result.consoleErrors.length || result.failedRequests.length) {
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
