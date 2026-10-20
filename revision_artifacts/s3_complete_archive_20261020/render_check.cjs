const {chromium}=require('C:/Users/yando/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');const path=require('path');const {pathToFileURL}=require('url');
(async()=>{
const h=__dirname,a=path.join(h,'S3_50_完整实验归档_20261020'),qa=path.join(h,'qa');fs.mkdirSync(qa,{recursive:true});
const b=await chromium.launch({headless:true});const page=await b.newPage({viewport:{width:1280,height:1000}});
await page.route('**/*',r=>r.request().url().startsWith('file:')?r.continue():r.abort());
const checks=[];
for(const file of ['00_开始阅读.html','总报告.html','03_资料来源索引/原版资料索引.html']){
await page.goto(pathToFileURL(path.join(a,file)).href);
const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
if(overflow)throw Error(file+' overflow');
checks.push({file,overflow,headings:await page.locator('h1,h2,h3').count()});
await page.screenshot({path:path.join(qa,path.basename(file)+'.png')});
if(file==='总报告.html'){await page.getByRole('heading',{name:/6. 最终/}).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(qa,'statistics.png')});}
}
fs.writeFileSync(path.join(h,'RENDER_CHECK.json'),JSON.stringify(checks,null,2));await b.close();
})();
