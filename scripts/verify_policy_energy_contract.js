let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (error) {
  if (error?.code !== "MODULE_NOT_FOUND") throw error;
  ({ chromium } = require("playwright-core"));
}

const fs = require("fs");
const path = require("path");

const baseUrl = process.env.MMN_URL || "http://localhost:8765/";
const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const username = process.env.MMN_USERNAME || "";
const password = process.env.MMN_PASSWORD || "";
const outputDir = process.env.MMN_ACCEPTANCE_OUTPUT || "output/playwright";
const targetRegion = process.env.MMN_POLICY_REGION || "上海";
const expectedVersion = process.env.MMN_EXPECTED_VERSION || "beta-1.03-20260731-policy-demo-ready-1";
const viewports = [
  { width: 1440, height: 1000 },
  { width: 390, height: 844 },
];

async function authenticate(page) {
  const login = page.locator("#cloud-login-screen");
  await page.waitForFunction(() => {
    const screen = document.querySelector("#cloud-login-screen");
    return !screen || screen.hidden || document.body.classList.contains("cloud-auth-required");
  });
  if (!(await login.isVisible())) return;
  if (!username || !password) throw new Error("Set MMN_USERNAME and MMN_PASSWORD for authenticated acceptance.");
  await page.locator('#cloud-login-form input[name="username"]').fill(username);
  await page.locator('#cloud-login-form input[name="password"]').fill(password);
  await page.locator("#cloud-login-form button[type=submit]").click();
  await login.waitFor({ state: "hidden", timeout: 30000 });
}

async function verifyViewport(browser, viewport) {
  const page = await browser.newPage({ viewport });
  const runtimeErrors = [];
  const failedResponses = [];
  page.on("pageerror", error => runtimeErrors.push(String(error.message || error)));
  page.on("console", message => {
    if (message.type() === "error") runtimeErrors.push(message.text());
  });
  page.on("response", response => {
    if (response.status() >= 400 && response.url().startsWith(baseUrl)) {
      failedResponses.push(`${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });
  await page.route("**/api/policy-intelligence/analyze", route => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      strategyValidation: {
        status: "insufficient_evidence",
        reasons: ["生产验收仅核对规则测算，不运行交叉复核"],
      },
    }),
  }));
  await page.route("**/api/project-state", route => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ ok: true, snapshot_id: "acceptance-no-write" }),
  }));

  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => localStorage.setItem("mmnEngineEdition", "china"));
  await page.reload({ waitUntil: "domcontentloaded" });
  await authenticate(page);
  const health = await page.evaluate(async () => {
    const response = await fetch("/api/health");
    return response.json();
  });
  if (health.versionCode !== expectedVersion) {
    throw new Error(`Wrong local runtime: expected ${expectedVersion}, received ${health.versionCode || "unknown"}`);
  }
  await page.locator("#dashboard").waitFor({ state: "visible", timeout: 30000 });
  await page.waitForTimeout(500);
  await page.locator('#nav button[data-page="policyintelligence"]').click();
  const moduleAvailable = await page.evaluate(() => typeof window.PolicyIntelligenceModule?.load === "function");
  if (!moduleAvailable) {
    throw new Error(`PolicyIntelligenceModule unavailable: ${JSON.stringify({ runtimeErrors, failedResponses })}`);
  }
  const responsePromise = page.waitForResponse(response =>
    response.url().includes("/api/policy-intelligence/dashboard")
      && response.request().method() === "GET"
      && response.status() === 200,
    { timeout: 30000 },
  );
  await page.evaluate(region => window.PolicyIntelligenceModule.select("智己LS6", region), targetRegion);
  await page.waitForFunction(() =>
    document.querySelector("#policy-controls") || document.querySelector(".policy-error"),
  );
  const policyError = await page.locator(".policy-error").textContent().catch(() => "");
  if (policyError) throw new Error(`Policy page load failed: ${policyError.replace(/\s+/g, " ").trim()}`);
  const form = page.locator("#policy-controls");
  await form.waitFor({ state: "visible", timeout: 30000 });
  const response = await responsePromise;
  const payload = await response.json();
  await page.waitForFunction(region => {
    const impact = document.querySelector(".policy-impact");
    return impact?.textContent?.includes(`智己LS6在${region}`);
  }, targetRegion, { timeout: 30000 });

  const ui = await page.evaluate(() => {
    const root = document.querySelector("#policy-intelligence-root");
    const impact = document.querySelector(".policy-impact");
    const own = document.querySelector(".policy-comparison-table article.own");
    return {
      model: document.querySelector('#policy-controls select[name="model"]')?.value,
      region: document.querySelector('#policy-controls select[name="region"]')?.value,
      scenario: document.querySelector('#policy-controls select[name="scenario"]')?.value,
      impactText: impact?.textContent?.replace(/\s+/g, " ").trim(),
      ownText: own?.textContent?.replace(/\s+/g, " ").trim(),
      overflow: Math.max(0, (root?.scrollWidth || 0) - (root?.clientWidth || 0)),
    };
  });
  const impact = payload.vehicleImpact || {};
  const summary = payload.summary || {};
  const result = {
    viewport: viewport.width,
    ui,
    api: {
      runtimeVersion: health.versionCode,
      evidenceStatus: impact.evidenceStatus,
      verifiedPolicyCount: impact.verifiedPolicyCount,
      conditionalBenefit: impact.conditionalBenefit,
      postPolicyPrice: impact.postPolicyPrice,
      scenarioConditionalBenefit: summary.scenarioConditionalBenefit,
      analysisRequestSuppressed: true,
      projectSnapshotWritesSuppressed: true,
    },
    runtimeErrors,
    failedResponses,
  };

    const valid = ui.model === "智己LS6"
    && ui.region === targetRegion
    && ui.scenario === "置换更新"
    && ui.impactText?.includes("¥23,403")
    && ui.ownText?.includes("¥166,497")
    && ui.overflow === 0
    && Number(impact.verifiedPolicyCount) === 2
    && Number(summary.scenarioConditionalBenefit) === 23403
    && runtimeErrors.length === 0
    && failedResponses.length === 0;
  fs.mkdirSync(outputDir, { recursive: true });
  await page.screenshot({
    path: path.join(outputDir, `prod-policy-energy-${viewport.width}.png`),
    fullPage: true,
  });
  await page.close();
  return { ...result, valid };
}

async function main() {
  const browser = await chromium.launch({ headless: true, executablePath: chromePath });
  try {
    const results = [];
    for (const viewport of viewports) results.push(await verifyViewport(browser, viewport));
    console.log(JSON.stringify({ results }, null, 2));
    if (results.some(result => !result.valid)) process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
