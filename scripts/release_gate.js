const { chromium } = require("playwright");

const baseUrl = process.env.MMN_URL || "http://127.0.0.1:8765/";
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

  const dashboardText = await page.locator(".dashboard-import").innerText();
  add("dashboard does not expose file format wording", !/Excel|CSV|模板/.test(dashboardText), dashboardText);

  const dataTableRows = await page.locator("#dashboard-data-table tbody tr").count().catch(() => 0);
  const cognitionRows = await page.locator("#dashboard-cognition-table tbody tr").count().catch(() => 0);
  add("dashboard data panel renders", dataTableRows > 0, String(dataTableRows));
  add("dashboard cognition panel renders", cognitionRows > 0, String(cognitionRows));

  await page.locator('#nav button[data-page="data"]').click();
  add("data center opens", await page.locator("#data.page.active").count() === 1);

  await page.locator('#nav button[data-page="strategykb"]').click();
  add("strategy knowledge page opens", await page.locator("#strategykb.page.active").count() === 1);
  add("strategy CTA labels use MMN", await page.locator("#run-rag-search").innerText().then(text => text.includes("MMN")).catch(() => false));

  await page.locator('#nav button[data-page="dashboard"]').click();
  let chooserOpened = false;
  const chooser = page.waitForEvent("filechooser", { timeout: 2000 }).then(() => { chooserOpened = true; }).catch(() => {});
  await page.locator(".dashboard-import [data-file-target]").click();
  await chooser;
  add("dashboard import opens file chooser", chooserOpened);

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
