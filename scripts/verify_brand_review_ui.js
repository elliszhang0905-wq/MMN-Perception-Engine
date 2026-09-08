/* Isolated real browser/API verifier. Never seeds data or calls providers. */
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
function validateTarget({url,testRoot}={}){
 if(!url||!testRoot)throw new Error('Explicit MMN_BRAND_REVIEW_URL and MMN_BRAND_REVIEW_TEST_ROOT required');
 const target=new URL(url);
 if(target.protocol!=='http:'||!['127.0.0.1','localhost','[::1]'].includes(target.hostname)||!target.port||target.port==='8765'||target.username||target.password||target.pathname!=='/'||target.search||target.hash)throw new Error('Refusing non-isolated URL');
 const realRoot=fs.realpathSync(testRoot);
 if(!realRoot.startsWith('/private/tmp/mmn-brand-review-')&&!realRoot.startsWith('/tmp/mmn-brand-review-'))throw new Error('Refusing non-dedicated temporary data root');
 return{url:target.origin,testRoot:realRoot};
}
async function main(){
 const target=validateTarget({url:process.env.MMN_BRAND_REVIEW_URL,testRoot:process.env.MMN_BRAND_REVIEW_TEST_ROOT});
 const health=await fetch(target.url+'/api/health',{redirect:'error'}).then(r=>r.json());
 validateDatabase(target.testRoot,health.db);
 const project=process.env.MMN_BRAND_REVIEW_PROJECT_JSON?JSON.parse(process.env.MMN_BRAND_REVIEW_PROJECT_JSON):null;
 const writes=process.env.MMN_BRAND_REVIEW_WRITE_TEST==='1';
 if(writes&&(!project||!String(project.name).includes('合成')))throw new Error('Writes require an explicitly named synthetic project fixture');
 const {chromium}=require('playwright'),browser=await chromium.launch({headless:true,channel:'chrome'});
 const output=path.resolve(__dirname,'../output/playwright/brand-review-v4');fs.mkdirSync(output,{recursive:true});
 const report={target:target.url,dbIdentityMatched:true,synthetic:Boolean(project),writes,screenshots:[],errors:[],checks:[]};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>report.errors.push(e.message));
  page.on('console',entry=>{if(entry.type()==='error')report.errors.push(entry.text())});
  if(project)await page.addInitScript(p=>{if(window!==window.top)return;localStorage.setItem('mmnBrandPenetrationProject',JSON.stringify(p));localStorage.setItem('mmnEngineEdition','china')},project);
  await page.goto(target.url,{waitUntil:'domcontentloaded'});
  await page.locator('#nav button[data-page="brandpenetration"]').click();
  const frame=page.frameLocator('#brand-penetration-frame');
  await frame.locator('#brandDecisionGrid').waitFor();
  if(project)try{await frame.locator('.review-v4').first().waitFor({timeout:20000})}catch(error){report.checks.push(await page.locator('#brand-penetration-snapshot-meta').textContent());report.checks.push(await frame.locator('#brandDecisionGrid').textContent());throw error}
  assert.equal(await page.locator('#brand-penetration-frame').getAttribute('sandbox'),'allow-scripts allow-popups allow-popups-to-escape-sandbox');
  if(writes){
   await frame.locator('#projectConfig > summary').click();
   let started=page.waitForResponse(r=>r.url().endsWith('/api/social-trends/jobs')&&r.request().method()==='POST');
   await frame.locator('#runProject').click();assert.equal((await started).status(),202);
   await frame.locator('#cancelBrandReview:visible').waitFor();
   const cancelled=page.waitForResponse(r=>/\/api\/brand-reviews\/jobs\/[^/]+\/cancel$/.test(r.url()));
   await frame.locator('#cancelBrandReview').click();assert.equal((await cancelled).status(),200);
   await frame.locator('#projectStatusText').filter({hasText:'已取消'}).waitFor({timeout:20000});report.checks.push('explicit cancellation real API');
   started=page.waitForResponse(r=>r.url().endsWith('/api/social-trends/jobs')&&r.request().method()==='POST');
   await frame.locator('#runProject').click();assert.equal((await started).status(),202);
   await frame.locator('.review-v4').first().waitFor({timeout:20000});report.checks.push('start analysis real API with synthetic provider boundary');
   for(const proposal of [false,true]){
    const claim=proposal?frame.locator('.review-claim').filter({has:frame.locator('.review-proposal')}).first():frame.locator('.review-claim').first();
    await claim.locator('[data-review-claim]:enabled').click();
    await frame.locator('#reviewReason').fill('合成隔离验收：人工核对来源与限定解释。');
    const response=page.waitForResponse(r=>r.url().endsWith('/api/brand-reviews/decisions')&&r.request().method()==='POST');
    await frame.locator('#reviewSave').click();assert.equal((await response).status(),200);
    await frame.locator('#brandReviewFeedback').filter({hasText:'处理已保存'}).waitFor();
    await frame.locator('#reviewClose').click();report.checks.push(proposal?'accept canonical proposal':'acknowledge source');
   }
   for(const action of ['modify','reject']){
    await frame.locator('[data-review-claim]:enabled').first().click();
    await frame.locator('#reviewAction').selectOption(action);
    if(action==='modify')await frame.locator('#reviewEdit').fill('合成验收：此修改应保留待核对，不自动发布。');
    await frame.locator('#reviewReason').fill('合成隔离浏览器验收：核对保存及刷新，不代表真实模型结论。');
    const response=page.waitForResponse(r=>r.url().endsWith('/api/brand-reviews/decisions')&&r.request().method()==='POST');
    await frame.locator('#reviewSave').click();assert.equal((await response).status(),200);
    await frame.locator('#brandReviewFeedback').filter({hasText:'处理已保存'}).waitFor();
    await frame.locator('#reviewClose').click();
    report.checks.push(action+' real API save');
   }
   await page.reload({waitUntil:'domcontentloaded'});await page.locator('#nav button[data-page="brandpenetration"]').click();
   await frame.locator('.review-v4').first().waitFor({timeout:20000});report.checks.push('refresh real API restore');
  }
  for(const width of [1440,1280,390]){
   await page.setViewportSize({width,height:1000});
   const file=path.join(output,`w3-${project?'synthetic':'history'}-${width}.png`);await page.screenshot({path:file,fullPage:true});report.screenshots.push(file);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'parent overflow');
   const iframe=page.frames().find(f=>f.url().includes('demo-brand-weekly-radar'));assert.ok(iframe);
   assert.equal(await iframe.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'iframe overflow');
   assert.equal(await iframe.locator('button button').count(),0,'nested button');
  }
  assert.deepEqual(report.errors,[]);report.checks.push('viewport, sandbox, nesting, runtime errors');
 }finally{await browser.close();fs.writeFileSync(path.join(output,'w3-verification.json'),JSON.stringify(report,null,2))}
 console.log(JSON.stringify(report,null,2));
}
function validateDatabase(testRoot,serviceDB){
 const root=fs.realpathSync(testRoot),db=path.join(root,'commercial_demo.db'),stat=fs.lstatSync(db);
 if(!stat.isFile()||stat.isSymbolicLink()||stat.nlink!==1||path.dirname(fs.realpathSync(db))!==root)throw new Error('Refusing linked or escaped test DB');
 const inspect=directory=>{for(const entry of fs.readdirSync(directory,{withFileTypes:true})){const file=path.join(directory,entry.name);if(entry.isSymbolicLink())throw new Error('Refusing symlink in dedicated test root');if(entry.isDirectory())inspect(file)}};
 inspect(root);
 if(typeof serviceDB!=='string'||fs.lstatSync(serviceDB).isSymbolicLink()||fs.realpathSync(serviceDB)!==db)throw new Error('Service DB identity mismatch');
 return db;
}
module.exports={validateTarget,validateDatabase};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1});
