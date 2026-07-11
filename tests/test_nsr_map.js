const assert = require("node:assert/strict");
const { buildDataFirstNsrMap, rankNsrLabel } = require("../nsr-map.js");

const sources = ["全网", "垂媒车主口碑", "抖音"];
const rows = [
  { model: "奥迪 E7X", label: "空间", source: "全网", nsr: 0.72, impact: 4 },
  { model: "奥迪 E7X", label: "空间", source: "垂媒车主口碑", nsr: 0.68, impact: 4 },
  { model: "奥迪 E7X", label: "空间", source: "抖音", nsr: 0.75, impact: 4 },
  { model: "问界 M7", label: "空间", source: "全网", nsr: 0.84, impact: 4 },
  { model: "问界 M7", label: "空间", source: "垂媒车主口碑", nsr: 0.80, impact: 4 },
  { model: "问界 M7", label: "空间", source: "抖音", nsr: 0.86, impact: 4 },
  { model: "小米 YU7", label: "用户服务", source: "全网", nsr: -0.51, impact: 4 },
  { model: "小米 YU7", label: "用户服务", source: "垂媒车主口碑", nsr: -0.50, impact: 4 },
  { model: "小米 YU7", label: "用户服务", source: "抖音", nsr: -0.87, impact: 4 },
  { model: "奥迪 E7X", label: "智能座舱", source: "全网", nsr: 0.68, impact: 5 },
  { model: "奥迪 E7X", label: "智能座舱", source: "垂媒车主口碑", nsr: 0.13, impact: 5 },
  { model: "奥迪 E7X", label: "智能座舱", source: "抖音", nsr: 0.81, impact: 5 },
  { model: "奥迪 Q6L e-tron", label: "配置", source: "全网", nsr: 1, impact: 4 },
  { model: "奥迪 Q6L e-tron", label: "配置", source: "抖音", nsr: 1, impact: 4 },
  { model: "小米 YU7", label: "安全", source: "全网", nsr: 0.4, impact: 4 },
];

const result = buildDataFirstNsrMap({
  rows,
  ownModel: "奥迪 E7X",
  selectedModels: ["奥迪 E7X", "问界 M7", "小米 YU7", "奥迪 Q6L e-tron"],
  expectedSources: sources,
});

assert.equal(result.basis, "imported_nsr_only");
assert.deepEqual(result.expectedSources, sources);
assert.equal(result.summary.strength, 2);
assert.equal(result.summary.neutral, 2);
assert.equal(result.summary.risk, 1);
assert.equal(result.summary.data_missing, 6);

const byKey = new Map(result.items.map(item => [`${item.model}:${item.label}`, item]));
assert.equal(byKey.get("奥迪 E7X:空间").status, "strength");
assert.equal(byKey.get("问界 M7:空间").status, "strength");
assert.ok(byKey.get("问界 M7:空间").gap > 0, "竞品强于本品时应落在地图右侧");
assert.equal(byKey.get("小米 YU7:用户服务").status, "risk");
assert.equal(byKey.get("奥迪 E7X:智能座舱").status, "neutral");
assert.equal(byKey.get("奥迪 Q6L e-tron:配置").status, "neutral");
assert.equal(byKey.get("奥迪 Q6L e-tron:配置").coverageCount, 2);
assert.equal(byKey.get("奥迪 Q6L e-tron:配置").coverageLabel, "2/3来源，可参与排名");
assert.deepEqual(byKey.get("奥迪 Q6L e-tron:配置").missingSources, ["垂媒车主口碑"]);
assert.equal(byKey.get("小米 YU7:安全").status, "data_missing");
assert.equal(byKey.get("小米 YU7:安全").coverageLabel, "1/3来源，不参与排名");

const spaceRanking = rankNsrLabel(result, "空间");
assert.deepEqual(spaceRanking.map(item => item.model), ["问界 M7", "奥迪 E7X", "奥迪 Q6L e-tron", "小米 YU7"]);
assert.deepEqual(spaceRanking.map(item => item.rank), [1, 2, null, null]);
assert.equal(spaceRanking.find(item => item.isOwn)?.rank, 2);
assert.equal(spaceRanking.find(item => item.isOwn)?.rankTotal, 2);

const missingResult = buildDataFirstNsrMap({
  rows: [
    { model: "奥迪 E7X", label: "安全", source: "全网", nsr: 0, impact: 4 },
    { model: "小米 YU7", label: "安全", source: "全网", nsr: null, impact: 4 },
    { model: "小米 YU7", label: "安全", source: "垂媒车主口碑", nsr: "", impact: 4 },
  ],
  ownModel: "奥迪 E7X",
  selectedModels: ["小米 YU7"],
  expectedSources: sources,
});
const missingRanking = rankNsrLabel(missingResult, "安全");
assert.equal(missingRanking.find(item => item.model === "奥迪 E7X")?.nsr, 0, "真实 0 必须保留");
assert.equal(missingRanking.find(item => item.model === "小米 YU7")?.status, "data_missing");
assert.equal(missingRanking.find(item => item.model === "小米 YU7")?.coverageCount, 0);
assert.equal(missingRanking.find(item => item.model === "小米 YU7")?.rank, null);

console.log("nsr data-first map: ok");
