const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const helperStart = app.indexOf("function dashboardCompetitionSourceCandidates(");
const helperEnd = app.indexOf("function renderDashboardCompetitorTrend(", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "competition snapshot helpers should be discoverable");
const helpers = app.slice(helperStart, helperEnd);

function row({
  platform,
  source,
  period,
  periodOrder,
  competitor,
  positiveRank,
  negativeRank,
  share,
  updatedAt,
}) {
  return {
    platform,
    source,
    period,
    periodOrder,
    ownModel: "奥迪E7X",
    competitor,
    positiveRank,
    negativeRank,
    share,
    updatedAt,
    sheet: period,
  };
}

const items = [
  row({platform: "汽车之家", source: "汽车之家周度旧文件.xlsx", period: "7.2-7.8", periodOrder: "2026-07-08", competitor: "旧竞品", positiveRank: 1, negativeRank: 2, share: .18, updatedAt: "2026-07-11T18:21:52Z"}),
  row({platform: "汽车之家", source: "汽车之家排名更新到0723.xlsx", period: "2026.07.23", periodOrder: "2026-07-23", competitor: "排名新竞品", positiveRank: 1, negativeRank: 3, share: null, updatedAt: "2026-07-23T08:04:36Z"}),
  row({platform: "懂车帝", source: "懂车帝周度更新到0722.xlsx", period: "7.9-7.15", periodOrder: "2026-07-15", competitor: "动态竞品1", positiveRank: 2, negativeRank: 5, share: .11, updatedAt: "2026-07-23T08:04:41Z"}),
  ...Array.from({length: 9}, (_, index) => row({
    platform: "懂车帝",
    source: "懂车帝周度更新到0722.xlsx",
    period: "7.16-7.22",
    periodOrder: "2026-07-22",
    competitor: `动态竞品${index + 1}`,
    positiveRank: index < 7 ? index + 1 : 8,
    negativeRank: index + 2,
    share: .2 - index * .01,
    updatedAt: "2026-07-23T08:04:41Z",
  })),
];

const context = {
  state: {config: {model: "奥迪E7X"}, models: ["奥迪E7X", "旧竞品"]},
  verticalState: {items},
  sellingPointAdvisoryState: {key: "old", loading: false, result: {status: "aligned", canEnterMarketingAction: true}, error: "", restoredKeys: new Set()},
  dashboardTopicPlanState: {loading: false, result: {id: "old-plan"}, error: ""},
  strategyReportExportState: {loading: false, result: {id: "old-package"}, error: ""},
  nullableNumber(value) {
    if (value === null || value === undefined || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  },
  console,
};
vm.runInNewContext(`${helpers}\nthis.api={dashboardCompetitionSourceCandidates,dashboardCompetitionSnapshot,dashboardLatestCompetitorRows,dashboardCompetitorSeries,invalidateCompetitionDerivedState,getDerivedState:()=>({sellingPointAdvisoryState,dashboardTopicPlanState,strategyReportExportState})};`, context);
const api = context.api;

const candidates = api.dashboardCompetitionSourceCandidates("奥迪E7X", items);
assert.equal(candidates[0].source, "汽车之家排名更新到0723.xlsx", "candidate ordering should expose the newest rank snapshot");

const snapshot = api.dashboardCompetitionSnapshot("奥迪E7X", items);
assert.equal(snapshot.platform, "懂车帝");
assert.equal(snapshot.source, "懂车帝周度更新到0722.xlsx");
assert.equal(snapshot.latestOrder, "2026-07-22");
assert.equal(snapshot.latestPeriod, "7.16-7.22");
assert.equal(snapshot.complete, true);
assert.equal(snapshot.newerRankSnapshot.source, "汽车之家排名更新到0723.xlsx");
assert.ok(snapshot.rows.every(item => item.platform === "懂车帝" && item.source === snapshot.source), "one dashboard snapshot must never mix sources or platforms");

const latest = api.dashboardLatestCompetitorRows("奥迪E7X", items);
assert.equal(latest.length, 9, "dynamic competition rows should retain the rank-eight tie");
assert.ok(latest.some(item => item.competitor === "动态竞品9"), "dynamic competitors must not be restricted to the product-evaluation model list");

const series = api.dashboardCompetitorSeries("奥迪E7X", items);
assert.equal(series.length, 9);
assert.ok(series.every(item => item.rows.every(value => value.source === snapshot.source)));
assert.ok(series.find(item => item.competitor === "动态竞品1").rows.length === 2, "trend rows should come from one source family");

const rankOnly = items.filter(item => item.source === "汽车之家排名更新到0723.xlsx");
const rankOnlySnapshot = api.dashboardCompetitionSnapshot("奥迪E7X", rankOnly);
assert.equal(rankOnlySnapshot.source, "汽车之家排名更新到0723.xlsx");
assert.equal(rankOnlySnapshot.complete, false);
assert.equal(rankOnlySnapshot.latestRows[0].share, null, "missing share must stay missing instead of borrowing an old value");

assert.equal(api.invalidateCompetitionDerivedState(snapshot.snapshotId, snapshot.snapshotId), false);
assert.equal(api.invalidateCompetitionDerivedState(snapshot.snapshotId, `${snapshot.snapshotId}|new`), true);
const invalidated = api.getDerivedState();
assert.equal(invalidated.sellingPointAdvisoryState.result.status, "stale");
assert.equal(invalidated.sellingPointAdvisoryState.result.canEnterMarketingAction, false);
assert.equal(invalidated.dashboardTopicPlanState.result, null);
assert.equal(invalidated.strategyReportExportState.result, null);

assert.match(app, /competitionSnapshotId/, "selling-point evidence should carry the competition snapshot identity");
assert.match(app, /invalidateCompetitionDerivedState\(/, "competition-dependent outputs should be invalidated after a new import");
assert.match(app, /previousCompetitionSnapshotId/, "the import flow should compare snapshots before and after hydration");
assert.match(app, /showPage\(activePageId\)/, "the import flow should preserve the user's active page");

console.log("dashboard competition snapshot: ok");
