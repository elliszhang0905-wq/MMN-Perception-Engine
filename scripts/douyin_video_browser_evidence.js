const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (_error) {
  ({ chromium } = require("playwright-core"));
}

const [, , cdpUrl, sourceUrl, itemId, outputRoot] = process.argv;

const safeOutputRoot = path.resolve(outputRoot || "");
const expected = new RegExp(`^https://(?:www\\.)?douyin\\.com/video/${itemId}(?:[/?#].*)?$`);
if (!itemId || !expected.test(sourceUrl || "") || !safeOutputRoot) {
  process.stderr.write("invalid video evidence request\n");
  process.exit(2);
}

async function waitForVideo(page) {
  await page.locator("video:visible").first().waitFor({ state: "visible", timeout: 45000 });
  await page.waitForFunction(() => {
    const candidates = [...document.querySelectorAll("video")];
    return candidates.some(node => node.offsetWidth > 0 && node.offsetHeight > 0 && node.readyState >= 2 && node.duration >= 5);
  }, null, { timeout: 30000 });
  await page.waitForTimeout(1200);
  const candidates = page.locator("video");
  const index = await candidates.evaluateAll(nodes => nodes
    .map((node, i) => ({ i, duration: Number(node.duration || 0), area: node.offsetWidth * node.offsetHeight }))
    .filter(row => row.duration > 0 && row.area > 0)
    .sort((a, b) => (b.duration - a.duration) || (b.area - a.area))[0]?.i ?? -1);
  if (index < 0) throw new Error("no playable video body");
  return candidates.nth(index);
}

async function main() {
  fs.mkdirSync(safeOutputRoot, { recursive: true });
  let browser;
  let launchedBrowser = false;
  try {
    browser = await chromium.connectOverCDP(cdpUrl, { timeout: 5000 });
  } catch (_error) {
    const executablePath = process.env.MMN_DOUYIN_BROWSER_EXECUTABLE || undefined;
    browser = await chromium.launch({
      headless: true,
      executablePath,
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    });
    launchedBrowser = true;
  }
  const context = browser.contexts()[0] || await browser.newContext({
    locale: "zh-CN",
    viewport: { width: 1440, height: 1000 },
    userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  });
  const page = await context.newPage();
  const frames = [];
  try {
    await page.goto(sourceUrl, { waitUntil: "domcontentloaded", timeout: 45000 });
    const video = await waitForVideo(page);
    const state = await video.evaluate(node => ({ duration: node.duration, width: node.videoWidth, height: node.videoHeight }));
    const durationMs = Math.max(1, Math.floor(Number(state.duration || 0) * 1000));
    const fractions = durationMs < 15000 ? [0.05, 0.3, 0.6, 0.9] : [0.02, 0.18, 0.38, 0.62, 0.82, 0.96];
    for (let index = 0; index < fractions.length; index += 1) {
      const timestampMs = Math.min(durationMs - 1, Math.max(0, Math.floor(durationMs * fractions[index])));
      await video.evaluate(async (node, seconds) => {
        node.pause();
        if (Math.abs(node.currentTime - seconds) < 0.08) return;
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error("seek timeout")), 8000);
          node.addEventListener("seeked", () => { clearTimeout(timer); resolve(); }, { once: true });
          node.currentTime = seconds;
        });
      }, timestampMs / 1000);
      const target = path.join(safeOutputRoot, `frame-${String(timestampMs).padStart(8, "0")}.jpg`);
      await video.screenshot({ path: target, type: "jpeg", quality: 84 });
      frames.push({ path: target, timestampMs });
    }
    const digest = crypto.createHash("sha256");
    digest.update(itemId); digest.update(String(durationMs));
    for (const frame of frames) digest.update(fs.readFileSync(frame.path));
    process.stdout.write(JSON.stringify({
      pageAvailable: true, mediaAvailable: frames.length > 0, durationMs,
      width: state.width, height: state.height, frames,
      mediaFingerprint: digest.digest("hex"),
    }), () => process.exit(0));
  } finally {
    await page.close().catch(() => {});
    if (launchedBrowser) await browser.close().catch(() => {});
  }
}

main().catch(error => {
  process.stderr.write(`${error && error.message ? error.message : error}\n`);
  process.exit(1);
});
