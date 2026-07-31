const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "group-dashboard.js"), "utf8");
const domainSource = source.match(/const attributeChartDomain=[^\n]+/)?.[0];
const distributeSource = source.match(/const distributeAttributeLabelYs=[^\n]+/)?.[0];
const layoutSource = source.match(/const layoutAttributeLabels=[^\n]+/)?.[0];

assert.ok(domainSource, "attribute chart should expose a deterministic data domain");
assert.ok(distributeSource, "attribute chart should expose collision-safe label distribution");
assert.ok(layoutSource, "attribute chart should expose quadrant-scoped label layout");

const attributeChartDomain = new Function(`${domainSource}; return attributeChartDomain;`)();
const distributeAttributeLabelYs = new Function(`${distributeSource}; return distributeAttributeLabelYs;`)();
const layoutAttributeLabels = new Function(
  "distributeAttributeLabelYs",
  `${layoutSource}; return layoutAttributeLabels;`,
)(distributeAttributeLabelYs);

const attributes = [
  { attribute: "价格", ownNsr: 0.5155, deltaVsAverage: 0.279 },
  { attribute: "品牌口碑", ownNsr: 0.1067, deltaVsAverage: -0.2597 },
  { attribute: "安全", ownNsr: -0.3448, deltaVsAverage: -0.2329 },
  { attribute: "质量", ownNsr: -0.2222, deltaVsAverage: -0.0386 },
  { attribute: "配置", ownNsr: 0.8621, deltaVsAverage: 0.1376 },
  { attribute: "空间", ownNsr: 0.6667, deltaVsAverage: -0.013 },
];
const domain = attributeChartDomain(attributes);

assert.ok(domain.minX < -0.3448, "x domain should expand beyond the lowest real NSR");
assert.ok(domain.minY < -0.2597, "y domain should expand beyond the lowest real delta");
assert.equal(domain.minX, -0.45, "x domain should round outward to the nearest 0.05");
assert.equal(domain.minY, -0.3, "y domain should round outward to the nearest 0.05");
assert.equal(domain.maxY, 0.45, "positive y domain should preserve the observed high value with padding");
assert.equal(domain.maxX, 1, "normal positive NSR scale should retain the semantic upper bound");
assert.ok(domain.minX <= domain.thresholdX && domain.maxX >= domain.thresholdX);
assert.ok(domain.minY <= domain.thresholdY && domain.maxY >= domain.thresholdY);

const invalid = { attribute: "无效属性", ownNsr: null, deltaVsAverage: 0.2 };
assert.equal(attributeChartDomain([...attributes, invalid]).valid.includes(invalid), false);

const bounds = { left: 88, right: 1138, top: 48, bottom: 392 };
const zeroY =
  bounds.bottom -
  ((0 - domain.minY) / (domain.maxY - domain.minY)) *
    (bounds.bottom - bounds.top);
const thresholdX =
  bounds.left +
  ((domain.thresholdX - domain.minX) / (domain.maxX - domain.minX)) *
    (bounds.right - bounds.left);
const positioned = domain.valid.map((item, index) => ({
  item,
  index,
  x:
    bounds.left +
    ((item.ownNsr - domain.minX) / (domain.maxX - domain.minX)) *
      (bounds.right - bounds.left),
  y:
    bounds.bottom -
    ((item.deltaVsAverage - domain.minY) / (domain.maxY - domain.minY)) *
      (bounds.bottom - bounds.top),
}));
const labels = layoutAttributeLabels(positioned, {
  ...bounds,
  thresholdX,
  zeroY,
});

for (const point of positioned) {
  const label = labels.get(point.index);
  assert.ok(point.x >= bounds.left && point.x <= bounds.right);
  assert.ok(point.y >= bounds.top && point.y <= bounds.bottom);
  assert.ok(label, `missing label layout for ${point.item.attribute}`);
  assert.ok(label.x >= bounds.left && label.x <= bounds.right);
  assert.ok(label.y >= bounds.top && label.y <= bounds.bottom);
  assert.ok(label.kneeX >= bounds.left && label.kneeX <= bounds.right);
  assert.ok(label.lineEndX >= bounds.left && label.lineEndX <= bounds.right);
  if (label.quadrant === "awareness" || label.quadrant === "risk") {
    assert.ok(label.x <= thresholdX);
    assert.ok(label.kneeX <= thresholdX);
    assert.ok(label.lineEndX <= thresholdX);
  } else {
    assert.ok(label.x >= thresholdX);
    assert.ok(label.kneeX >= thresholdX);
    assert.ok(label.lineEndX >= thresholdX);
  }
  if (label.quadrant === "awareness" || label.quadrant === "asset") {
    assert.ok(label.y <= zeroY);
  } else {
    assert.ok(label.y >= zeroY);
  }
}

const crowded = Array.from({ length: 8 }, (_, index) => ({
  index,
  y: 100 + index,
}));
const distributed = distributeAttributeLabelYs(crowded, 80, 250, 31);
for (let index = 1; index < distributed.length; index++) {
  assert.ok(distributed[index].labelY > distributed[index - 1].labelY);
}
assert.ok(distributed[0].labelY >= 80);
assert.ok(distributed.at(-1).labelY <= 250);

assert.doesNotMatch(
  source,
  /lineEndX=side==="left"\?left-32:right\+34/,
  "leaders must not terminate outside the quadrant plot",
);
assert.match(source, /data-attribute-quadrant=/);
assert.match(source, /未按0代填/);

console.log("group attribute layout: ok");
