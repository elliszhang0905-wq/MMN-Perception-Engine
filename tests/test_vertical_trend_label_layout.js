const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const source = app.match(/function trendPointLabelY\([^\n]+/);

assert.ok(source, "trend chart should expose collision-aware point label placement");
const trendPointLabelY = new Function(`${source[0]}; return trendPointLabelY;`)();
const segmentSource = app.match(/function trendLineSegments\([^\n]+/);
assert.ok(segmentSource, "trend chart should split lines around missing periods");
const trendLineSegments = new Function(`${segmentSource[0]}; return trendLineSegments;`)();
const gapSource = app.match(/function trendGapConnectorMarkup\([^\n]+/);
assert.ok(gapSource, "trend chart should expose honest connectors across missing periods");
const trendGapConnectorMarkup = new Function(`${gapSource[0]}; return trendGapConnectorMarkup;`)();
const axisSource = app.match(/function trendXAxisLabelIndexes\([^\n]+/);
assert.ok(axisSource, "trend chart should limit x-axis label density");
const trendXAxisLabelIndexes = new Function(`${axisSource[0]}; return trendXAxisLabelIndexes;`)();

const upper = { y: 42 };
const lower = { y: 64 };
assert.equal(trendPointLabelY(upper, lower, "neg"), 33, "upper point label should move above the line");
assert.equal(trendPointLabelY(lower, upper, "pos"), 82, "lower point label should move below the line");
assert.equal(trendPointLabelY({ y: 100 }, { y: 100 }, "pos"), 91, "coincident positive label stays above");
assert.equal(trendPointLabelY({ y: 100 }, { y: 100 }, "neg"), 118, "coincident negative label stays below");
assert.match(app, /trendPointLabelY\(p,neg\[index\],"pos"\)/);
assert.match(app, /trendPointLabelY\(p,pos\[index\],"neg"\)/);
assert.deepEqual(trendLineSegments([{ x: 1 }, null, { x: 3 }, { x: 4 }]), [[{ x: 1 }], [{ x: 3 }, { x: 4 }]]);
assert.doesNotMatch(app, /arr\.filter\(Boolean\)\.map\(p=>`\$\{p\.x\},\$\{p\.y\}`\)/, "missing periods must not be joined by a continuous line");
assert.match(trendGapConnectorMarkup([{ x: 1, y: 2 }, null, { x: 3, y: 4 }], "pos-line"), /class="pos-line gap-line"/, "missing periods should be bridged with a visibly dashed connector");
assert.equal(trendGapConnectorMarkup([{ x: 1, y: 2 }, { x: 3, y: 4 }], "pos-line"), "", "consecutive observations should keep the normal solid line");
assert.deepEqual(trendXAxisLabelIndexes(Array.from({ length: 17 }), 6), [0, 3, 6, 10, 13, 16], "dense axes should render only evenly spaced key labels");
assert.deepEqual(trendXAxisLabelIndexes(Array.from({ length: 4 }), 6), [0, 1, 2, 3], "short axes should keep every label");
assert.match(app, /虚线跨越无记录周期/, "chart legend should explain dashed gap connectors");

console.log("vertical trend label layout: ok");
