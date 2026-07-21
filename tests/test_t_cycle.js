const assert = require("node:assert/strict");
const cycle = require("../t-cycle.js");

const t0 = "2026-05-29";

assert.equal(cycle.dayOffset(t0, "2026-04-14"), -45);
assert.equal(cycle.dayOffset(t0, "2026-05-08"), -21);
assert.equal(cycle.dayOffset(t0, "2026-05-29"), 0);
assert.equal(cycle.dayOffset(t0, "2026-07-16"), 48);
assert.equal(cycle.phaseForOffset(-45).key, "preheat");
assert.equal(cycle.phaseForOffset(-21).key, "presale");
assert.equal(cycle.phaseForOffset(0).key, "launch");
assert.equal(cycle.phaseForOffset(48).key, "conversion");
assert.equal(cycle.addDays(t0, 90), "2026-08-27");
assert.equal(cycle.addDays(t0, 120), "2026-09-26");
assert.deepEqual(cycle.phaseDates(t0, cycle.phaseForOffset(48)), {
  start: "2026-06-29",
  end: "2026-08-27",
});
assert.equal(cycle.tLabel(-21), "T-21");
assert.equal(cycle.tLabel(0), "T0");
assert.equal(cycle.tLabel(48), "T+48");
assert.equal(cycle.parseIsoDate("2026-02-30"), null);

const boundaryExpectations = new Map([
  [-46, "preheat"], [-45, "preheat"], [-44, "preheat"], [-23, "preheat"], [-22, "preheat"],
  [-21, "presale"], [-20, "presale"], [-2, "presale"], [-1, "presale"],
  [0, "launch"], [1, "amplify"], [2, "amplify"], [29, "amplify"], [30, "amplify"],
  [31, "conversion"], [32, "conversion"], [89, "conversion"], [90, "conversion"],
  [91, "validation"], [92, "validation"], [119, "validation"], [120, "validation"],
  [121, "alwayson"], [122, "alwayson"],
]);
for (const [offset, phaseKey] of boundaryExpectations) assert.equal(cycle.phaseForOffset(offset).key, phaseKey, `offset ${offset}`);

console.log("t cycle: ok");
