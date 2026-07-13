const { chromium } = require("playwright");

const cdpUrl = process.argv[2] || "http://127.0.0.1:9225";
const sourceUrl = "https://creator.douyin.com/creator-micro/creative-guidance";
const responsePath = "/web/api/creator/material/center/billboard/";
const views = [
  { key: "videos", label: "热门视频", billboardType: "1" },
  { key: "topics", label: "热门话题", billboardType: "3" },
];
const ranges = [
  { key: "24h", label: "24小时" },
  { key: "7d", label: "7天" },
  { key: "30d", label: "30天" },
];

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function visibleEntries(locator) {
  const rows = [];
  for (let index = 0; index < await locator.count(); index += 1) {
    const item = locator.nth(index);
    if (await item.isVisible().catch(() => false)) {
      rows.push({ item, box: await item.boundingBox().catch(() => null) });
    }
  }
  return rows.filter(row => row.box);
}

async function clickVisibleText(page, text, predicate = () => true) {
  const rows = await visibleEntries(page.getByText(text, { exact: true }));
  const row = rows.find(candidate => predicate(candidate.box)) || rows[0];
  if (!row) throw new Error(`页面中没有找到“${text}”`);
  await row.item.click({ force: true });
  return row.box;
}

const TIME_LABELS = new Set(ranges.map(range => range.label));

async function activeTimeSelector(page) {
  const candidates = await visibleEntries(page.locator('[aria-haspopup="true"][data-popupid]'));
  for (const candidate of candidates) {
    const label = (await candidate.item.innerText().catch(() => "")).trim();
    if (TIME_LABELS.has(label)) return { ...candidate, label };
  }
  return null;
}

async function chooseTime(page, label) {
  let lastCurrent = "";
  for (let attempt = 0; attempt < 3; attempt += 1) {
    const current = await activeTimeSelector(page);
    if (!current) throw new Error("没有找到时间维度选择器");
    lastCurrent = current.label;
    if (current.label === label) return false;
    if (attempt === 0) {
      await current.item.click({ force: true });
    } else if (attempt === 1) {
      await page.mouse.click(current.box.x + current.box.width / 2, current.box.y + current.box.height / 2);
    } else {
      await current.item.focus();
      await page.keyboard.press("ArrowDown");
    }
    const option = page.getByRole("menuitem", { name: label, exact: true });
    try {
      await option.waitFor({ state: "visible", timeout: 3000 });
      await option.click({ force: true });
      await delay(450);
      return true;
    } catch (_) {
      await page.keyboard.press("Escape").catch(() => {});
      await delay(350);
    }
  }
  throw new Error(`时间维度“${label}”未能展开（当前为“${lastCurrent || "未知"}”）；请重新打开采集器窗口后重试`);
}

async function selectTime(page, label, billboardType) {
  const current = await activeTimeSelector(page);
  if (!current) throw new Error("没有找到时间维度选择器");
  if (current.label === label) {
    const pivot = ranges.find(range => range.label !== label);
    if (!pivot) throw new Error("没有可用于切换时间维度的备选项");
    await chooseTime(page, pivot.label);
  }
  const responsePromise = page.waitForResponse(response => {
    if (!response.url().includes(responsePath)) return false;
    const url = new URL(response.url());
    return url.searchParams.get("billboard_type") === billboardType && url.searchParams.get("billboard_tag") === "335";
  }, { timeout: 30000 });
  await chooseTime(page, label);
  return responsePromise;
}

async function main() {
  const browser = await chromium.connectOverCDP(cdpUrl);
  const context = browser.contexts()[0];
  if (!context) throw new Error("没有连接到抖音采集器浏览器");
  let page = context.pages().find(item => item.url().includes("creator.douyin.com"));
  if (!page) page = await context.newPage();
  if (!page.url().includes("creator.douyin.com/creator-micro/creative-guidance")) {
    await page.goto(sourceUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
  }
  await page.bringToFront();
  const rankingEntry = page.getByText("热门视频", { exact: true }).first();
  try {
    await rankingEntry.waitFor({ state: "visible", timeout: 60000 });
  } catch (_error) {
    // The creator-center shell can remain blank briefly after QR verification.
    // Reload once before treating the session as unavailable.
    await page.goto(sourceUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
    await rankingEntry.waitFor({ state: "visible", timeout: 60000 }).catch(() => {
      throw new Error("抖音创作者中心在120秒内未加载出榜单；请确认已登录，并在采集器窗口中能看到“热门视频”后重试");
    });
  }
  process.stdout.write(`${JSON.stringify({ type: "login_verified" })}\n`);

  for (const view of views) {
    await clickVisibleText(page, view.label, box => box.y < 280);
    await delay(500);
    await clickVisibleText(page, "汽车", box => box.y < 460);
    await delay(500);
    for (const range of ranges) {
      const response = await selectTime(page, range.label, view.billboardType);
      const payload = await response.json();
      if (Number(payload.status_code || 0) !== 0) {
        throw new Error(payload.status_message || payload.status_msg || `抖音榜单接口返回 ${payload.status_code}`);
      }
      const snapshot = {
        view: view.key,
        range: range.key,
        capturedAt: new Date().toISOString(),
        sourceUrl,
        items: Array.isArray(payload.item_list) ? payload.item_list : [],
      };
      process.stdout.write(`${JSON.stringify({ type: "snapshot", snapshot })}\n`);
      await delay(350);
    }
  }
  process.stdout.write(`${JSON.stringify({ type: "complete", count: 6 })}\n`);
  process.exit(0);
}

main().catch(error => {
  process.stderr.write(`${error && error.stack ? error.stack : error}\n`);
  process.exit(1);
});
