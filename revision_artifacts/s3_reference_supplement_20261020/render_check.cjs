const {chromium}=require('C:/Users/yando/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('url');const path=require('path');const fs=require('fs');
(async()=>{const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1365,height:1000}});
await page.route('**/*',r=>r.request().url().startsWith('file:')?r.continue():r.abort());
const root=path.join(__dirname,'01_中性查证资料');const out=path.join(__dirname,'02_工作记录_不发评审','visual_checks');fs.mkdirSync(out,{recursive:true});
const results=[];
for(const [name,file,anchor] of [['entry','阅读入口.html',''],['model','阅读入口.html','K849074'],['gap','阅读入口.html','K452269'],['catalog','来源与页码索引.html','doc19']]){
await page.goto(pathToFileURL(path.join(root,file)).href+(anchor?'#'+anchor:''));
await page.screenshot({path:path.join(out,name+'.png')});
results.push({name,title:await page.title(),horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
}
if(results.some(r=>r.horizontalOverflow))throw Error('Horizontal overflow');fs.writeFileSync(path.join(out,'browser_checks.json'),JSON.stringify(results,null,2));await browser.close();console.log(JSON.stringify(results));})();
