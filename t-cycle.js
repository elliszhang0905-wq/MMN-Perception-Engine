(function(root,factory){
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 if(root)root.MmnTCycle=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 const DAY_MS=86400000;
 const phases=[
  {key:"preheat",label:"上市预热",range:"T-45～T-22",start:-45,end:-22,goal:"建立产品初始认知与上市期待"},
  {key:"presale",label:"首发/预售",range:"T-21～T-1",start:-21,end:-1,goal:"完成卖点蓄水与预售意向转化"},
  {key:"launch",label:"正式上市",range:"T0",start:0,end:0,goal:"发布价格权益并集中引爆声量"},
  {key:"amplify",label:"热度放大",range:"T+1～T+30",start:1,end:30,goal:"放大大定、评测与用户订单证据"},
  {key:"conversion",label:"销售转化",range:"T+31～T+90",start:31,end:90,goal:"验证卖点认知与真实选择的匹配"},
  {key:"validation",label:"销售验证",range:"T+91～T+120",start:91,end:120,goal:"复盘销量、交付、口碑与战胜战败"},
  {key:"alwayson",label:"常态经营",range:"T+121起",start:121,end:null,goal:"进入常态内容与产品经营"}
 ];
 function parseIsoDate(value){
  const match=String(value||"").trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if(!match)return null;
  const date=new Date(Date.UTC(Number(match[1]),Number(match[2])-1,Number(match[3])));
  return Number.isNaN(date.getTime())?null:date;
 }
 function formatIsoDate(date){return date instanceof Date&&!Number.isNaN(date.getTime())?date.toISOString().slice(0,10):""}
 function addDays(value,days){const date=parseIsoDate(value);if(!date)return"";date.setUTCDate(date.getUTCDate()+Number(days||0));return formatIsoDate(date)}
 function dayOffset(t0Date,assessmentDate){const t0=parseIsoDate(t0Date),assessment=parseIsoDate(assessmentDate);return t0&&assessment?Math.round((assessment-t0)/DAY_MS):null}
 function phaseForOffset(offset){if(!Number.isFinite(offset))return null;return phases.find(phase=>offset>=phase.start&&(phase.end===null||offset<=phase.end))||phases[0]}
 function tLabel(offset){if(!Number.isFinite(offset))return"待设置";return offset===0?"T0":`T${offset>0?"+":""}${offset}`}
 function phaseDates(t0Date,phase){if(!phase)return{start:"",end:""};return{start:addDays(t0Date,phase.start),end:phase.end===null?"":addDays(t0Date,phase.end)}}
 return{DAY_MS,phases,parseIsoDate,formatIsoDate,addDays,dayOffset,phaseForOffset,tLabel,phaseDates};
});
