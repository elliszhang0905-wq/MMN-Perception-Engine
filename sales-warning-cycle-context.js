(function(root,factory){
 const cycle=root?.MmnTCycle||(typeof require==="function"?require("./t-cycle.js"):null),api=factory(cycle);
 if(typeof module==="object"&&module.exports)module.exports=api;
 if(root)root.MMNSalesWarningCycleContext=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(cycle){
 const clean=value=>String(value??"").trim();
 const identity=value=>clean(value).replace(/\s+/g,"").toLocaleLowerCase();
 const validDate=value=>{
  const text=clean(value),parsed=cycle?.parseIsoDate?.(text);
  return Boolean(parsed&&cycle.formatIsoDate(parsed)===text);
 };
 const recordFor=(records,item)=>records&&typeof records==="object"&&!Array.isArray(records)?records[String(item?.seriesId||"")]:null;
 const recordMatches=(record,item)=>{
  if(!record||typeof record!=="object"||Array.isArray(record))return false;
  const recordSeries=clean(record.seriesId),itemSeries=clean(item?.seriesId);
  if(recordSeries&&itemSeries&&recordSeries!==itemSeries)return false;
  const recordModel=identity(record.model),itemModel=identity(item?.model);
  return !recordModel||!itemModel||recordModel===itemModel;
 };
 const verifiedContext=(record,item,source)=>{
  if(!recordMatches(record,item)||record.status!=="verified"||!validDate(record.launchDate)||!validDate(record.assessmentDate))return null;
  const dayOffset=cycle?.dayOffset?.(record.launchDate,record.assessmentDate),phase=cycle?.phaseForOffset?.(dayOffset);
  if(!Number.isFinite(dayOffset)||!phase)return null;
  if(record.phaseKey&&record.phaseKey!==phase.key)return null;
  if(record.tLabel&&record.tLabel!==cycle.tLabel(dayOffset))return null;
  if(record.phaseRange&&record.phaseRange!==phase.range)return null;
  return{
   model:clean(item?.model||record.model),seriesId:clean(item?.seriesId||record.seriesId),
   launchDate:clean(record.launchDate),assessmentDate:clean(record.assessmentDate),dayOffset,
   tLabel:cycle.tLabel(dayOffset),phaseKey:phase.key,phaseLabel:clean(record.phaseLabel)||phase.label,
   phaseRange:phase.range,source,status:"verified",reviewedAt:clean(record.reviewedAt),
   refreshStatus:source==="sales-warning-cache"?"cached":"fresh"
  };
 };
 function adapt(item,{serverCycles={},localCycles={},databaseRecord=null}={}){
  const candidates=[
   [recordFor(serverCycles,item),"sales-warning-server"],
   [recordFor(localCycles,item),"sales-warning-cache"],
   [databaseRecord,"sales-warning-database"],
  ];
  for(const [record,source] of candidates){const context=verifiedContext(record,item,source);if(context)return context}
  const pending=candidates.find(([record])=>recordMatches(record,item)&&record&&record.status&&record.status!=="verified");
  if(pending)return{model:clean(item?.model),seriesId:clean(item?.seriesId),launchDate:"",assessmentDate:"",tLabel:"",phaseKey:"",phaseLabel:"上市日期待复核",phaseRange:"",source:pending[1],status:"pending_review",reviewedAt:clean(pending[0].reviewedAt),refreshStatus:pending[1]==="sales-warning-cache"?"cached":"fresh"};
  return{model:clean(item?.model),seriesId:clean(item?.seriesId),launchDate:"",assessmentDate:"",tLabel:"",phaseKey:"",phaseLabel:"该车型尚未设置正式上市日期",phaseRange:"",source:clean(item?.cycle)?"database-stage-only":"sales-warning",status:"missing",reviewedAt:"",refreshStatus:"fresh"};
 }
 function merge(serverCycles={},localCycles={}){
  const merged={...(localCycles&&typeof localCycles==="object"?localCycles:{})};
  Object.entries(serverCycles&&typeof serverCycles==="object"?serverCycles:{}).forEach(([key,value])=>{merged[key]=value});
  return merged;
 }
 return{adapt,merge,validDate,recordMatches};
});
