const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const modulePath = path.join(__dirname, "..", "knowledge-workspace.js");

test("projects only trustworthy DTO fields and explicit unavailable metadata", () => {
  const {projectKnowledgeItem} = require(modulePath);
  const item = projectKnowledgeItem({id:"1",title:"<b>Title</b>",body:"<img onerror=alert(1)>",type:"case",brand:"A",module:"M",sourceLabel:null,sourceUrl:null,reviewStatus:"unavailable",validity:"unknown",version:"v1",relations:[1]});
  assert.deepEqual(item, {id:"1",title:"<b>Title</b>",body:"<img onerror=alert(1)>",type:"case",brand:"A",module:"M",sourceLabel:null,sourceUrl:null,createdAt:null,updatedAt:null,reviewStatus:"unavailable",validity:"unknown"});
  assert.equal(item.version, undefined);
  assert.equal(item.relations, undefined);
});

test("query params preserve real filters and paging", () => {
  const {buildKnowledgeWorkspaceUrl} = require(modulePath);
  assert.equal(buildKnowledgeWorkspaceUrl({edition:"global",q:"title body",type:"case",brand:"A&B",module:"launch",offset:50,limit:50}), "/api/knowledge-workspace?edition=global&q=title+body&type=case&brand=A%26B&module=launch&offset=50&limit=50");
});

test("controller clears details before search and distinguishes empty result", async () => {
  const {createKnowledgeWorkspaceController} = require(modulePath);
  const snapshots=[];
  const controller=createKnowledgeWorkspaceController({fetchJson:async()=>({ok:true,items:[],total:0,offset:0,limit:50,hasMore:false,facets:{brands:[],modules:[]}}),onChange:s=>snapshots.push(s)});
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u",edition:"china",project:"p"});
  await controller.search({q:"none"});
  assert.equal(controller.getState().status,"empty");
  assert.equal(controller.getState().selectedId,"");
  assert.ok(snapshots.some(s=>s.status==="loading"&&s.selectedId===""&&s.items.length===0));
});

test("failed loads are retryable and remain distinct from empty", async () => {
  const {createKnowledgeWorkspaceController} = require(modulePath);
  let calls=0;
  const controller=createKnowledgeWorkspaceController({fetchJson:async()=>{calls++;if(calls===1)throw new Error("offline");return {ok:true,items:[],total:0,offset:0,limit:50,hasMore:false,facets:{brands:[],modules:[]}}}});
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u",edition:"china",project:"p"});
  await controller.load();
  assert.equal(controller.getState().status,"error");
  assert.equal(controller.getState().error,"offline");
  await controller.retry();
  assert.equal(controller.getState().status,"empty");
});

test("inactive/authless contexts never GET and identity changes abort and reject stale responses", async () => {
  const {createKnowledgeWorkspaceController} = require(modulePath);
  const pending=[];
  const controller=createKnowledgeWorkspaceController({fetchJson:(url,options)=>new Promise(resolve=>pending.push({url,options,resolve}))});
  controller.setContext({active:false,authReady:true,orgId:"o",userId:"u1",edition:"china",project:"p"});
  assert.equal(pending.length,0);
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u1",edition:"china",project:"p"});
  const first=controller.load();
  assert.equal(pending.length,1);
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u2",edition:"china",project:"p"});
  assert.equal(pending[0].options.signal.aborted,true);
  assert.equal(controller.getState().items.length,0);
  pending[0].resolve({ok:true,items:[{id:"old",title:"old"}],total:1,facets:{brands:[],modules:[]}});
  await first;
  assert.equal(controller.getState().items.length,0);
});

test("new requests use no-store and auth headers without write methods", async () => {
  const {createKnowledgeWorkspaceController} = require(modulePath);
  let observed;
  const controller=createKnowledgeWorkspaceController({fetchJson:async(url,options)=>{observed={url,options};return {ok:true,items:[],total:0,facets:{brands:[],modules:[]}}},getHeaders:()=>({Authorization:"Bearer x"})});
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u",edition:"china",project:"p"});
  await controller.load();
  assert.equal(observed.options.method,"GET");
  assert.equal(observed.options.cache,"no-store");
  assert.equal(observed.options.headers.Authorization,"Bearer x");
});

test("module contains no knowledge cache or legacy strategy array coupling", () => {
  const source=fs.readFileSync(modulePath,"utf8");
  assert.doesNotMatch(source,/localStorage|sessionStorage|strategyKb|mergeStrategyKnowledge/);
});

test("original RAG page loads the isolated reader and lifecycle hooks", () => {
  const html=fs.readFileSync(path.join(__dirname,"..","index.html"),"utf8");
  const app=fs.readFileSync(path.join(__dirname,"..","app.js"),"utf8");
  const server=fs.readFileSync(path.join(__dirname,"..","server.py"),"utf8");
  assert.match(html,/knowledge-workspace\.css\?v=beta-1\.03-20260908-knowledge-workspace-s2-1/);
  assert.match(html,/id="knowledge-workspace"/);
  assert.match(html,/<span>知识阅读工作区<\/span><h2>客户级共享知识/);
  assert.match(html,/knowledge-workspace\.js\?v=beta-1\.03-20260908-knowledge-workspace-s2-1/);
  assert.match(html,/app\.js\?v=beta-1\.03-20260908-knowledge-workspace-s2-1/);
  assert.match(app,/function syncKnowledgeWorkspaceContext/);
  assert.match(app,/showPage[\s\S]*?syncKnowledgeWorkspaceContext\(\)/);
  assert.match(app,/function saveSession[\s\S]*?syncKnowledgeWorkspaceContext\(\)/);
  assert.match(app,/function setEdition[\s\S]*?syncKnowledgeWorkspaceContext\(\)/);
  assert.match(app,/strategy-kb-file[\s\S]*?invalidateKnowledgeWorkspace\(\)/);
  assert.match(app,/async function logoutSession\(\)[\s\S]*?invalidateKnowledgeWorkspace\(\)[\s\S]*?await api\("\/api\/logout"/);
  assert.match(app,/function signalAppAuthReady\(\)[\s\S]*?syncKnowledgeWorkspaceContext\(\)/);
  assert.match(server,/"knowledge-workspace\.css"/);
  assert.match(server,/"knowledge-workspace\.js"/);
});

test("projector rejects non-http source links", () => {
  const {projectKnowledgeItem}=require(modulePath);
  assert.equal(projectKnowledgeItem({sourceUrl:"javascript:alert(1)"}).sourceUrl,null);
  assert.equal(projectKnowledgeItem({sourceUrl:"https://example.com/source"}).sourceUrl,"https://example.com/source");
});

test("mobile drilldown keeps an internal scroll surface and restores focus", () => {
  const source=fs.readFileSync(modulePath,"utf8");
  const css=fs.readFileSync(path.join(__dirname,"..","knowledge-workspace.css"),"utf8");
  assert.match(source,/requestAnimationFrame[\s\S]*?\.focus\(\)/);
  assert.match(source,/listScroll=list\.scrollTop/);
  assert.match(css,/@media\(max-width:520px\)[\s\S]*?height:min\(/);
  assert.match(source,/function applyViewContext[\s\S]*?mobilePane="list"[\s\S]*?listScroll=0/);
  assert.match(source,/来源（未核验）/);
});

test("a new load removes stale clickable rows immediately", async () => {
  const {createKnowledgeWorkspaceController}=require(modulePath);
  let resolveSecond;
  const responses=[Promise.resolve({ok:true,items:[{id:"old",title:"old"}],total:1,offset:0,limit:50,facets:{brands:[],modules:[]}}),new Promise(resolve=>{resolveSecond=resolve})];
  const controller=createKnowledgeWorkspaceController({fetchJson:()=>responses.shift()});
  controller.setContext({active:true,authReady:true,orgId:"o",userId:"u",edition:"china",project:"p"});
  await controller.load();controller.select("old");
  const pending=controller.search({q:"new"});
  assert.equal(controller.getState().status,"loading");
  assert.equal(controller.getState().items.length,0);
  assert.equal(controller.getState().selectedId,"");
  resolveSecond({ok:true,items:[],total:0,offset:0,limit:50,facets:{brands:[],modules:[]}});await pending;
});
