const assert=require("node:assert/strict");

global.window={};
require("../data_20260608.js");
const{normalizeLegacyAttributeNsrDataset}=require("../legacy-product-evaluation.js");

const source=window.importedDataset20260608;
assert.equal(source.rows.length,656);
assert.ok(source.rows.every(row=>row.length===12),"fixture must preserve the original 12-column records");

const normalized=normalizeLegacyAttributeNsrDataset(source);
assert.notEqual(normalized,source);
assert.equal(normalized.rows.length,source.rows.length,"normalization must not add or delete business rows");
assert.ok(source.rows.every(row=>row.length===12),"normalization must not mutate the source records");
assert.ok(normalized.rows.every(row=>Number.isFinite(Number(row[14]))),"every recognized legacy row must receive deterministic attribute NSR");
assert.equal(normalized.models.length,6);
assert.equal(normalized.importQuality.kind,"PRODUCT_EVALUATION_SUMMARY");
assert.equal(normalized.importQuality.interactionAvailable,false);
assert.equal(normalized.importQuality.attributeNsrDerivedFromSentimentCounts,true);
assert.equal(normalized.productEvaluationSourceModel,"智己L6");

const row=(model,sourceName,label)=>normalized.rows.find(item=>item[0]===model&&item[2]===sourceName&&item[4]===label);
assert.equal(row("智己L6","垂媒车主口碑","价格")[14],1);
assert.equal(row("智己L6","垂媒车主口碑","空间")[14],-1);
assert.equal(row("小米SU7","垂媒车主口碑","价格")[14],Number(((29-7)/(29+7)).toFixed(8)));
assert.ok(Number.isFinite(normalized.summaryMetrics["智己L6"].overallNsr));
assert.ok(Number.isFinite(normalized.summaryPlatformNsr["智己L6"]["全网"]));
assert.equal(normalized.summaryHeat["智己L6"].interaction,null);
assert.equal(normalized.summaryHeat["智己L6"].volume,source.rows.filter(item=>item[0]==="智己L6").reduce((sum,item)=>sum+Number(item[8]||0),0));

assert.equal(normalizeLegacyAttributeNsrDataset(normalized),normalized,"normalization must be idempotent after explicit NSR exists");
const explicit={note:"普通产品评价",rows:[["奥迪E7X","本品","全网","造型设计","外观","认可","目标核心人群","无",100,3,1,4,"汇总NSR评分","来源",0.72]]};
assert.equal(normalizeLegacyAttributeNsrDataset(explicit),explicit,"explicit E7X-style NSR datasets must remain untouched");

console.log("legacy product evaluation normalization tests passed");
