import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const items=JSON.parse(await fs.readFile('blind_input.json','utf8'));
const rules=JSON.parse(await fs.readFile('guide.json','utf8'));
const out='outputs/01a13537-s3/01_仅此目录可发评审';
const wb=Workbook.create();
const identity=wb.worksheets.add('身份与说明');
const definitions=wb.worksheets.add('评分定义');
const scores=wb.worksheets.add('评分50');
const reader=wb.worksheets.add('完整原文');
const font='Microsoft YaHei';
function base(s,range){s.showGridLines=false;s.getRange(range).format.font={name:font,size:11,color:'#17263C'};s.getRange(range).format.verticalAlignment='top';}
function header(s,range){s.getRange(range).format.fill='#294E78';s.getRange(range).format.font={name:font,size:11,bold:true,color:'#FFFFFF'};s.getRange(range).format.rowHeight=30;}
function title(s,text,sub){s.getRange('A2').values=[[text]];s.getRange('A2').format.font={name:font,size:15,bold:true};s.getRange('A2').format.rowHeight=30;s.getRange('A3').values=[[sub]];s.getRange('A3').format.rowHeight=26;}
base(identity,'A1:B22');identity.getRange('A1:A22').format.columnWidth=38;identity.getRange('B1:B22').format.columnWidth=100;
title(identity,'S3 数值候选独立评分','先阅读评分定义；两位评审各自另存，不共享首判。');
header(identity,'A5:B5');identity.getRange('A5:B5').values=[['本人填写项目','填写区（初始留空）']];
const meta=['评审代号（两位须不同）','身份','相关专业与工程经验','单位或职业背景（可选）','既往接触这些输出或相关审核的情况','首判是否独立完成且未交换答案','本次记录阶段','开始时间（含时区）','完成时间（含时区）'];
identity.getRange('A6:B14').values=meta.map(x=>[x,null]);identity.getRange('A6:B14').format.rowHeight=40;identity.getRange('A6:B14').format.wrapText=true;identity.getRange('B6:B14').format.fill='#FFF2CC';
identity.getRange('B7').dataValidation={rule:{type:'list',values:['外部非作者领域评审','共同作者领域评审','其他（备注说明）']}};
identity.getRange('B11').dataValidation={rule:{type:'list',values:['是','否']}};
identity.getRange('B12').dataValidation={rule:{type:'list',values:['独立首判','讨论后修订']}};
identity.getRange('A17').values=[['填写提示']];identity.getRange('B17').values=[['原文见“完整原文”或同目录只读HTML。评分仅填“评分50”黄色区；不要修改盲ID和原文。']];
identity.getRange('A18').values=[['记录说明']];identity.getRange('B18').values=[['身份、经验、接触情况和时间请本人如实填写；不预填姓名，不自动声明外部独立性。']];
identity.getRange('A19').values=[['提交方式']];identity.getRange('B19').values=[['独立完成后另存并提交第一阶段原件。出处猜测是之后另行提供的可选材料。']];identity.getRange('A17:B19').format.wrapText=true;identity.getRange('A17:B19').format.rowHeight=52;
base(definitions,`A1:B${rules.length+5}`);definitions.getRange(`A1:A${rules.length+5}`).format.columnWidth=24;definitions.getRange(`B1:B${rules.length+5}`).format.columnWidth=105;
title(definitions,'评分定义与查证规则','未知允许保留；任何关键错误不能整条判正确。');header(definitions,'A5:B5');definitions.getRange('A5:B5').values=[['主题','定义与操作']];definitions.getRange(`A6:B${rules.length+5}`).values=rules;definitions.getRange(`A6:B${rules.length+5}`).format.wrapText=true;
for(let i=0;i<rules.length;i++)definitions.getRange(`A${i+6}:B${i+6}`).format.rowHeight=Math.max(55,Math.ceil(rules[i][1].length/48)*20+16);
base(scores,'A1:F55');[16,18,18,65,12,42].forEach((w,i)=>scores.getRangeByIndexes(0,i,55,1).format.columnWidth=w);
title(scores,'50条独立评分','按盲ID阅读完整原文；只填写黄色区。');header(scores,'A5:F5');scores.getRange('A5:F5').values=[['盲ID','数值正确性','适用性','具体依据（版本/页码/条款，或实践判断及范围）','信心1–3','备注']];scores.getRange('A5:F5').format.wrapText=true;scores.getRange('A5:F5').format.rowHeight=48;
scores.getRange('A6:F55').values=items.map(r=>[r.blind_id,null,null,null,null,null]);scores.getRange('B6:F55').format.fill='#FFF2CC';scores.getRange('A6:F55').format.rowHeight=62;scores.getRange('A6:F55').format.wrapText=true;
scores.getRange('B6:B55').dataValidation={rule:{type:'list',values:['正确','可接受','错误','无法判断']}};
scores.getRange('C6:C55').dataValidation={rule:{type:'list',values:['适用','不适用','工况不明']}};
scores.getRange('E6:E55').dataValidation={rule:{type:'list',values:['1','2','3']}};scores.freezePanes.freezeRows(5);
const rows=[];const index=[];
function add(code,label,value){const text=Array.isArray(value)?value.join('\n'):String(value??'');const chunks=text.match(/[\s\S]{1,250}/g)||[''];for(let i=0;i<chunks.length;i++)rows.push([code,label+(chunks.length>1?`（${i+1}/${chunks.length}）`:''),chunks[i]]);}
for(const item of items){index.push({blind_id:item.blind_id,row:rows.length+6});for(const [k,l] of [['original_requirement','原需求'],['shall_statement','候选要求'],['measurable_criterion','数值判据'],['applicable_condition','适用条件'],['verification_method','验证方法'],['acceptance_criteria','验收内容']])add(item.blind_id,l,item[k]);rows.push(['','','']);}
base(reader,`A1:C${rows.length+5}`);reader.getRange(`A1:A${rows.length+5}`).format.columnWidth=16;reader.getRange(`B1:B${rows.length+5}`).format.columnWidth=24;reader.getRange(`C1:C${rows.length+5}`).format.columnWidth=105;
title(reader,'完整原文阅读','Ctrl+F查盲ID；长文本分段，字符未删改。');header(reader,'A5:C5');reader.getRange('A5:C5').values=[['盲ID','字段','原文']];reader.getRange(`A6:C${rows.length+5}`).values=rows;reader.getRange(`A6:C${rows.length+5}`).format.wrapText=true;
for(let i=0;i<rows.length;i++){const text=rows[i][2];const weight=[...text].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);const lines=Math.ceil(weight/85)+(text.match(/\n/g)||[]).length;reader.getRange(`A${i+6}:C${i+6}`).format.rowHeight=text?Math.max(35,lines*19+18):16;if(rows[i][1]==='原需求'){reader.getRange(`A${i+6}:C${i+6}`).format.fill='#E5EDF6';}}
reader.freezePanes.freezeRows(5);wb.recalculate();await fs.mkdir('previews',{recursive:true});
for(const [name,range,file] of [['身份与说明','A1:B19','identity'],['评分定义','A1:B13','definitions'],['评分50','A1:F9','scores'],['完整原文','A1:C14','reader']]){const png=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(`previews/${file}.png`,new Uint8Array(await png.arrayBuffer()));}
await fs.writeFile('reader_rows.json',JSON.stringify({rows,index},null,2));
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:20},maxChars:1800});
await fs.writeFile('WORKBOOK_INSPECT.json',JSON.stringify({errors:errors.ndjson,sheets:(await wb.inspect({kind:'sheet',include:'id,name'})).ndjson},null,2));
await (await SpreadsheetFile.exportXlsx(wb)).save(`${out}/数值候选独立评分.xlsx`);console.log('Exported 50 blank cards, identity blank, complete original text.');
