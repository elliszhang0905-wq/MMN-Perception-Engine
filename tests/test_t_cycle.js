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

console.log("t cycle: ok");
