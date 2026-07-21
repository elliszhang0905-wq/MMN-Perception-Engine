(function(root,factory){
 const api=factory();
 if(typeof module!=="undefined"&&module.exports)module.exports=api;
 if(root)root.MmnLegacyProductEvaluation=api;
})(typeof window!=="undefined"?window:globalThis,function(){
 const POSITIVE_EMOTIONS=new Set(["兴奋","惊喜","期待","信任","认可","自豪"]);
 const NEGATIVE_EMOTIONS=new Set(["怀疑","焦虑","嘲讽","失望","愤怒","后悔"]);
 const LEGACY_NOTE="属性层级 NSR 已拆分为正/负两类聚合行";

 function count(value){
  const number=Number(value);
  return Number.isFinite(number)&&number>0?number:0;
 }
 function score(bucket){
  const denominator=bucket.positive+bucket.negative;
  return denominator?(bucket.positive-bucket.negative)/denominator:null;
 }
 function bucketFor(map,key){
  if(!map.has(key))map.set(key,{positive:0,negative:0});
  return map.get(key);
 }
 function addEmotion(bucket,emotion,value){
  if(POSITIVE_EMOTIONS.has(emotion))bucket.positive+=value;
  else if(NEGATIVE_EMOTIONS.has(emotion))bucket.negative+=value;
 }
 function key(parts){return JSON.stringify(parts)}

 function normalizeLegacyAttributeNsrDataset(dataset){
  if(!dataset||!Array.isArray(dataset.rows))return dataset;
  const sourceNote=String(dataset.sourceNote||dataset.note||"");
  if(!sourceNote.includes(LEGACY_NOTE))return dataset;
  if(dataset.rows.some(row=>Number.isFinite(Number(row?.[14]))))return dataset;

  const attributeBuckets=new Map(),platformBuckets=new Map(),modelBuckets=new Map();
  const models=[],sources=[];
  const seenModels=new Set(),seenSources=new Set();
  for(const row of dataset.rows){
   const model=String(row?.[0]||"").trim(),source=String(row?.[2]||"").trim(),label=String(row?.[4]||"").trim(),emotion=String(row?.[5]||"").trim(),samples=count(row?.[8]);
   if(!model||!source||!label||!samples||(!POSITIVE_EMOTIONS.has(emotion)&&!NEGATIVE_EMOTIONS.has(emotion)))continue;
   if(!seenModels.has(model)){seenModels.add(model);models.push(model)}
   if(!seenSources.has(source)){seenSources.add(source);sources.push(source)}
   addEmotion(bucketFor(attributeBuckets,key([model,source,label])),emotion,samples);
   addEmotion(bucketFor(platformBuckets,key([model,source])),emotion,samples);
   addEmotion(bucketFor(modelBuckets,key([model])),emotion,samples);
  }

  const rows=dataset.rows.map(row=>{
   const model=String(row?.[0]||"").trim(),source=String(row?.[2]||"").trim(),label=String(row?.[4]||"").trim();
   const nsr=score(attributeBuckets.get(key([model,source,label]))||{positive:0,negative:0});
   if(nsr===null)return[...row];
   const normalized=[...row];
   normalized[12]=normalized[12]||"正负样本聚合NSR";
   normalized[13]=normalized[13]||`确定性计算｜${source}｜${label}`;
   normalized[14]=Number(nsr.toFixed(8));
   return normalized;
  });

  const summaryHeat={},summaryPlatformNsr={},summaryMetrics={};
  for(const model of models){
   const platformVolume={};
   for(const source of sources){
    const platformBucket=platformBuckets.get(key([model,source]));
    if(!platformBucket)continue;
    platformVolume[source]=platformBucket.positive+platformBucket.negative;
   }
   const overallBucket=modelBuckets.get(key([model]))||{positive:0,negative:0},overallNsr=score(overallBucket);
   summaryHeat[model]={volume:overallBucket.positive+overallBucket.negative,interaction:null,platformVolume};
   summaryPlatformNsr[model]={};
   if(overallNsr!==null)summaryPlatformNsr[model]["全网"]=Number(overallNsr.toFixed(8));
   for(const source of sources){
    const platformNsr=score(platformBuckets.get(key([model,source]))||{positive:0,negative:0});
    if(platformNsr!==null)summaryPlatformNsr[model][source]=Number(platformNsr.toFixed(8));
   }
   summaryMetrics[model]={overallNsr:overallNsr===null?null:Number(overallNsr.toFixed(8))};
  }

  const ownModel=String(dataset.productEvaluationSourceModel||dataset.config?.model||"").trim();
  return{
   ...dataset,
   datasetVersion:dataset.datasetVersion||dataset.version||"legacy_product_evaluation_normalized",
   sourceNote:`${sourceNote}；属性与整体NSR已按（正面-负面）/（正面+负面）确定性计算。`,
   rows,
   models,
   summaryHeat,
   summaryPlatformNsr,
   summaryMetrics,
   summaryAttributeBenchmark:dataset.summaryAttributeBenchmark||{},
   importQuality:{
    ...(dataset.importQuality||{}),
    kind:"PRODUCT_EVALUATION_SUMMARY",
    timeRange:dataset.importQuality?.timeRange||"2026.5.1 — 2026.6.4",
    metricCoverage:{nsr:true,ips:false,intent:false,risk:false},
    attributeVolumeAvailable:true,
    platformVolumeAvailable:true,
    platformNsrAvailable:true,
    platformNsrSources:["全网",...sources],
    attributeNsrSources:sources,
    interactionAvailable:false,
    volumeMetricLabel:"有效样本",
    attributeNsrDerivedFromSentimentCounts:true,
    message:"源数据提供车型、平台、属性及正负情绪有效样本；属性NSR与整体NSR按源表公式确定性计算。源表未提供互动量、购买意向和风险量级，相关指标不推断。"
   },
   sourceRowCount:dataset.sourceRowCount||dataset.rows.length,
   aggregatedRowCount:rows.length,
   replace:true,
   productEvaluationSourceModel:ownModel,
   productEvaluationBoundModel:ownModel
  };
 }

 return{normalizeLegacyAttributeNsrDataset};
});
