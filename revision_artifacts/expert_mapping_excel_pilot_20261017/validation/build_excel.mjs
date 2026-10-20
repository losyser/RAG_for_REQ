import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const packagePath=process.argv[2];
const outputDir=path.resolve(process.argv[3]);
const pkg=JSON.parse(await fs.readFile(packagePath,'utf8'));
if(pkg.kind!=='pilot'||pkg.sources.map(s=>s.id).join(',')!=='OR002,OR001')throw Error('Expected approved pilot only');
await fs.mkdir(outputDir,{recursive:true});
const output=path.join(outputDir,'需求映射专家试做_OR002_OR001.xlsx');
try {await fs.access(output);throw Error('Refusing to overwrite existing workbook');}catch(e){if(e.code!=='ENOENT')throw e;}
const wb=Workbook.create();
const names=['0规则与计时','1独立首判','2候选判断','3遗漏补充','4完整分类目录'];
const sheets=names.map(n=>wb.worksheets.add(n));
const [home,initial,candidates,missing,tax]=sheets;
const palette={navy:'#253D57',ink:'#172B3A',muted:'#516272',input:'#FFF3CD',pale:'#EEF3F7',warn:'#9B421B'};
function write(s,cell,rows){s.getRange(cell).write(rows);}
function base(s,range){s.showGridLines=false;s.getRange(range).format={font:{name:'Microsoft YaHei',size:11,color:palette.ink},verticalAlignment:'center',rowHeight:28};}
function title(s,text){write(s,'A2',[[text]]);s.getRange('A2').format.font={name:'Microsoft YaHei',size:16,bold:true,color:palette.navy};s.getRange('A2:F2').format.rowHeight=32;}
function header(s,range){s.getRange(range).format={fill:palette.navy,font:{name:'Microsoft YaHei',size:11,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:34,horizontalAlignment:'center'};}
function input(s,range){s.getRange(range).format.fill=palette.input;}
function list(s,range,values){s.getRange(range).dataValidation={rule:{type:'list',values}};}
function widths(s,values){values.forEach((w,i)=>s.getRangeByIndexes(0,i,1,1).format.columnWidth=w);}
function sourceBanner(s){
  write(s,'A4',[[pkg.sources[0].id,pkg.sources[0].text],[pkg.sources[1].id,pkg.sources[1].text]]);
  s.getRange('B4:F4').merge();s.getRange('B5:F5').merge();
  s.getRange('A4:F5').format={fill:palette.pale,wrapText:true,rowHeight:40};
}
// Start sheet combines clear rules, authoritative source text, stage declarations and timing.
base(home,'A1:B57');widths(home,[29,112]);title(home,'需求映射专家试做');
const rules=[
 ['用途','仅 OR002、OR001 的真实试做校准，排除正式评分。黄色格可填写，其他内容请勿更改。'],
 ['填写方式','同一位专家、同一试做任务：网页或本 Excel 二选一；不要双填。若已开始网页，请继续网页或联系协调者处理切换。'],
 ['专家代号',null],
 ['操作顺序','先做两源独立首判并保存，再查看候选页；随后判断候选、补漏，最后填写计时。首次打开候选页会同时暴露两源候选。'],
 ['独立首判','只依据原需求直接表达的含义，从完整分类目录选配对。可多选，不凑数量；不要补写“工程上应该有”的需求。'],
 ['阶段记录','在两源“首判已完成”填“是”并记完成时间，再打开候选页。之后不要改写首判原记录，纠正或新增意见记到源备注。'],
 ['Excel 的限制','所有页均可访问；Excel 无法强制锁定首判或证明盲审。请如实记录是否提前看过候选，不把工作表隐藏当作强盲法。'],
 ['判断与查漏','相关／不相关／不确定／未答分开。空白仍是未答。先通览21部件、183合法配对，补充候选之外的相关或不确定配对。'],
 ['目录说明','45个原意图说明之外，14个合法ID使用原文件行注释并标记。含义不清时记不确定和疑问，不自改目录。'],
 ['保存与回传','先另存为“原文件名_专家代号.xlsx”，Ctrl+S保存。回传整个.xlsx；保留中文原记录。不要只发截图或另存CSV。'],
 ['计时口径','每源总分钟包含首判、候选、查漏和备注；中断分钟另记。两源都完成首判再看候选，分别累计每源用时。未完成如实填写。']
];
write(home,'A4',rules);home.getRange('B4:B14').format.wrapText=true;
home.getRange('A4:A14').format.font.bold=true;
for(let r=4;r<=14;r++)home.getRange(`A${r}:B${r}`).format.rowHeight=r===6?30:48;
input(home,'B6');home.getRange('B10').format.font.color=palette.warn;
const fields=['原始需求（只读）','首判已完成','候选暴露状态','首次看候选时间（文本）','完整目录查漏已完成','本源全部审核已完成','总耗时（分钟）','中断时长（分钟）','规则疑问／停在哪一步','源中文备注／首判更正','首判完成时间（文本）'];
pkg.sources.forEach((s,index)=>{
 const start=17+index*14;
 write(home,`A${start}`,[[s.id,'本源阶段与耗时']]);header(home,`A${start}:B${start}`);
 write(home,`A${start+1}`,fields.map((f,i)=>[f,i===0?s.text:null]));
 home.getRange(`B${start+1}:B${start+11}`).format.wrapText=true;
 home.getRange(`A${start+1}:B${start+1}`).format.rowHeight=58;
 home.getRange(`A${start+9}:B${start+10}`).format.rowHeight=55;
 input(home,`B${start+2}:B${start+11}`);
 for(const offset of [2,5,6])list(home,`B${start+offset}`,['是','否']);
 list(home,`B${start+3}`,['尚未查看','首判完成后查看','首判前已查看','不确定']);
 for(const offset of [7,8]){home.getRange(`B${start+offset}`).dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};home.getRange(`B${start+offset}`).setNumberFormat('0.0');}
 for(const offset of [4,11])home.getRange(`B${start+offset}`).setNumberFormat('@');
});
write(home,'A47',[
 ['格式版本','mapping-review-excel-pilot-v1'],['模板ID','pilot-'+pkg.version.slice(0,16)],['任务包版本',pkg.version],['协议',pkg.protocol],['源文件SHA256',pkg.provenance.source_sha256],['目录SHA256',pkg.provenance.taxonomy_sha256],['任务类型','pilot'],['原始来源文件',path.basename(packagePath)]
]);home.getRange('B47:B54').format={font:{name:'Microsoft YaHei',size:10,color:palette.muted},wrapText:true};home.getRange('A47:B54').format.rowHeight=30;
home.tabColor=palette.navy;
const legal=Object.entries(pkg.taxonomy).flatMap(([c,intents])=>intents.map(i=>[c+':'+i,pkg.components[c],pkg.intents[i],c,i])).sort((a,b)=>a[0].localeCompare(b[0]));
base(tax,'A1:E187');widths(tax,[48,28,70,30,28]);title(tax,'完整分类目录：183个合法配对');
write(tax,'A3',[['只读目录。首判和补漏均可查阅。复制配对ID到对应页，或使用配对ID下拉。']]);tax.getRange('A3:E3').merge();
write(tax,'A4',[['稳定配对ID','部件中文','工程方面中文','部件ID','意图ID']]);header(tax,'A4:E4');write(tax,'A5',legal);
tax.getRange('A5:E187').format.wrapText=true;tax.getRange('A5:E187').format.rowHeight=48;
tax.freezePanes.freezeRows(4);tax.freezePanes.freezeColumns(1);
wb.names.add('ValidPairs',"='4完整分类目录'!$A$5:$A$187");
for(const [s,isInitial] of [[initial,true],[missing,false]]){
 base(s,'A1:F68');widths(s,[13,48,27,58,14,48]);title(s,isInitial?'独立首判：先完成两源，再看候选':'遗漏补充：记录候选池外配对');
 write(s,'A3',[[isInitial?'先只看原文和完整目录。每行一个配对；未发现配对可留空并在首页确认首判完成。':'仅添加未在候选页出现的合法配对。分类缺项写首页疑问，不强行归类；已有候选的意见写候选页。']]);s.getRange('A3:F3').merge();s.getRange('A3:F3').format={wrapText:true,rowHeight:42};sourceBanner(s);
 write(s,'A7',[['黄色输入：选择源ID、配对ID、判断，填写中文理由。部件／方面自动显示。可复制空行继续添加。']]);s.getRange('A7:F7').merge();
 write(s,'A8',[['源ID','稳定配对ID','部件中文（自动）','工程方面（自动）','判断','中文理由／疑问']]);header(s,'A8:F8');
 input(s,'A9:B68');input(s,'E9:F68');s.getRange('A9:F68').format={rowHeight:52,wrapText:true};
 list(s,'A9:A68',['OR002','OR001']);s.getRange('B9:B68').dataValidation={rule:{type:'list',formula1:'=ValidPairs'}};list(s,'E9:E68',['相关','不确定','未答']);
 for(let r=9;r<=68;r++)for(const [col,index] of [['C',2],['D',3]])s.getRange(`${col}${r}`).formulas=[[`=IF(B${r}="","",IFERROR(VLOOKUP(B${r},'4完整分类目录'!$A$5:$E$187,${index},FALSE),"配对ID无效，请核对目录"))`]];
 s.freezePanes.freezeRows(8);s.freezePanes.freezeColumns(2);
}
base(candidates,'A1:F34');widths(candidates,[13,48,27,58,14,48]);title(candidates,'候选判断：两源首判保存后再查看');
write(candidates,'A3',[['本页会同时暴露两源候选。请先完成两源首判，在首页记录暴露状态和时间；首判完成后不要回改首判原记录。']]);candidates.getRange('A3:F3').merge();candidates.getRange('A3:F3').format={wrapText:true,rowHeight:42,font:{color:palette.warn}};sourceBanner(candidates);
write(candidates,'A7',[['每行一个待判断配对。空白或“未答”均不当作负例。相关／不相关／不确定分别保留；理由可写在右侧。']]);candidates.getRange('A7:F7').merge();
write(candidates,'A8',[['源ID','稳定配对ID','部件中文','工程方面中文','判断','中文理由／疑问']]);header(candidates,'A8:F8');
const rows=pkg.sources.flatMap(s=>s.candidates.map(p=>[s.id,p.id,pkg.components[p.component],pkg.intents[p.intent],null,null]));write(candidates,'A9',rows);
candidates.getRange('A9:F34').format={wrapText:true,rowHeight:60};input(candidates,'E9:F34');list(candidates,'E9:E34',['相关','不相关','不确定','未答']);
candidates.getRange('E9:E34').conditionalFormats.add('containsText',{text:'不确定',format:{fill:'#FFE1C7',font:{color:'#8B3D14'}}});
candidates.freezePanes.freezeRows(8);candidates.freezePanes.freezeColumns(2);
wb.recalculate();
const check=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},summary:'Formula error scan'});
await fs.writeFile(path.join(outputDir,'artifact_inspection.json'),JSON.stringify({errorScan:check.ndjson,packageVersion:pkg.version}));
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(output);
for(let i=0;i<sheets.length;i++){
 const range=i===0?'A2:B28':i===4?'A2:E18':'A2:F14';
 const preview=await wb.render({sheetName:names[i],range,scale:1,format:'png'});
 await fs.writeFile(path.join(outputDir,`sheet_${i}.png`),new Uint8Array(await preview.arrayBuffer()));
}
console.log(JSON.stringify({output,legalPairs:legal.length,candidates:rows.length,sheets:names}));
