import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const items=JSON.parse(await fs.readFile('blind_input.json','utf8'));
const rules=JSON.parse(await fs.readFile('rules.json','utf8'));
const out='outputs/01a13537-v6/01_盲审材料';
const wb=Workbook.create();
const guide=wb.worksheets.add('使用说明');
const scores=wb.worksheets.add('评分30');
const exception=wb.worksheets.add('异常核对');
const reader=wb.worksheets.add('原文阅读');
const font='Microsoft YaHei';
function base(s,range){s.showGridLines=false;s.getRange(range).format.font={name:font,size:11,color:'#17263C'};s.getRange(range).format.verticalAlignment='top';}
function header(s,range){s.getRange(range).format.fill='#294E78';s.getRange(range).format.font={name:font,size:11,bold:true,color:'#FFFFFF'};s.getRange(range).format.rowHeight=28;}
function title(s,text,help){s.getRange('A2').values=[[text]];s.getRange('A2').format.font={name:font,size:15,bold:true};s.getRange('A2').format.rowHeight=27;s.getRange('A3').values=[[help]];s.getRange('A3').format.rowHeight=25;}
base(guide,'A1:B24');guide.getRange('A1:A24').format.columnWidth=30;guide.getRange('B1:B24').format.columnWidth=112;
title(guide,'中文盲审 · 30条抽查＋1条缺失诊断','v6：结果揭晓后修订，非预注册抽样。人工判断留空。');
guide.getRange('A5:B5').values=[['项目','规则与操作']];header(guide,'A5:B5');guide.getRange(`A6:B${5+rules.length}`).values=rules;
guide.getRange(`A6:B${5+rules.length}`).format.wrapText=true;
for(let i=0;i<rules.length;i++){guide.getRange(`A${i+6}:B${i+6}`).format.rowHeight=Math.max(48,Math.ceil(rules[i][1].length/48)*18+14);}
const opts=[['直接支持','部分支持','相矛盾','证据不足','不确定'],['明确符合','明确不符','一般规则有依据','未知'],['可检验','不可检验','不确定'],['原文摘录','忠实转述','新增推导或综合','无依据','不确定']];
function scoreSheet(s,rows,isException){
 base(s,'A1:H40');const widths=[12,18,24,18,26,58,18,20];widths.forEach((w,i)=>s.getRangeByIndexes(0,i,40,1).format.columnWidth=w);
 title(s,isException?'独立缺失诊断 · X01':'30条抽查 · 人工评分',isException?'不计入30条机器评审一致率；不补成有效机器结果。':'先按编号阅读原文，再填写黄色栏；空白表示未作答。');
 s.getRange('A5:H5').values=[['编号','支持判断','适用条件判断','可验证性','忠实性（补充）','备注 / 证据编号 / 理由','评审者（可选）','填写日期（可选）']];header(s,'A5:H5');s.getRange('A5:H5').format.wrapText=true;s.getRange('A5:H5').format.rowHeight=44;
 s.getRange(`A6:H${5+rows.length}`).values=rows.map(r=>[r.code,null,null,null,null,null,null,null]);
 s.getRange(`A6:H${5+rows.length}`).format.rowHeight=42;s.getRange(`B6:H${5+rows.length}`).format.fill='#FFF2CC';s.getRange(`B6:H${5+rows.length}`).format.wrapText=true;
 for(let i=0;i<4;i++)s.getRangeByIndexes(5,i+1,rows.length,1).dataValidation={rule:{type:'list',values:opts[i]}};
 s.freezePanes.freezeRows(5);s.tabColor=isException?'#A77427':'#294E78';
}
scoreSheet(scores,items.slice(0,30),false);scoreSheet(exception,items.slice(30),true);
const rows=[];const index=[];
function add(code,label,text){text=String(text??'未提供');const chunks=text.match(/[\s\S]{1,350}/g)||[''];for(let i=0;i<chunks.length;i++)rows.push([code,label+(chunks.length>1?`（${i+1}/${chunks.length}）`:''),chunks[i]]);}
for(const item of items){
 index.push({code:item.code,startRow:rows.length+6});add(item.code,'任务',item.task_type);add(item.code,'原需求',item.source_requirement);
 for(const [key,label] of [['shall_statement','候选条目'],['measurable_criterion','判据'],['applicable_condition','声明适用条件'],['verification_method','声明验证方法'],['acceptance_criteria','声明验收要求']]){const value=item.candidate[key];add(item.code,label,Array.isArray(value)?value.join('\n'):value);}
 for(const cite of item.candidate.evidence_citations??[])add(item.code,'引用元信息',`${cite.kb_id} · 层级:${cite.tier??'未知'} · 来源:${cite.source??'未知'} · 有条款:${cite.has_clause?'是':'否'}`);
 for(const evidence of item.cited_evidence)add(item.code,`证据原文 ${evidence.evidence_id}`,evidence.supplied_excerpt);
 if(!item.cited_evidence.length)add(item.code,'证据原文','未提供有效引用原文。');
 add(item.code,'阅读边界','仅核对当时给出的摘录。此处不再截断，片段外条件未知。');
 rows.push(['','','']);
}
base(reader,`A1:C${rows.length+5}`);reader.getRange(`A1:A${rows.length+5}`).format.columnWidth=12;reader.getRange(`B1:B${rows.length+5}`).format.columnWidth=26;reader.getRange(`C1:C${rows.length+5}`).format.columnWidth=112;
title(reader,'31项原文阅读','Ctrl+F查找H01–H30或X01；长原文分连续段，未删除字符。');
reader.getRange('A5:C5').values=[['编号','字段','原始内容 / 实际引用摘录']];header(reader,'A5:C5');reader.getRange(`A6:C${rows.length+5}`).values=rows;reader.getRange(`A6:C${rows.length+5}`).format.wrapText=true;
for(let i=0;i<rows.length;i++){const text=rows[i][2];const weight=[...text].reduce((n,c)=>n+(c.charCodeAt(0)>255?2:1),0);const lines=Math.ceil(weight/92)+(text.match(/\n/g)||[]).length;reader.getRange(`A${i+6}:C${i+6}`).format.rowHeight=text?Math.min(360,Math.max(32,lines*17+15)):16;if(rows[i][1]==='任务'){reader.getRange(`A${i+6}:C${i+6}`).format.fill='#E5EDF6';reader.getRange(`A${i+6}:C${i+6}`).format.font.bold=true;}}
reader.freezePanes.freezeRows(5);
wb.recalculate();await fs.mkdir('previews',{recursive:true});
for(const [name,range,file] of [['使用说明','A1:B12','guide'],['评分30','A1:H11','scores'],['异常核对','A1:H7','exception'],['原文阅读','A1:C16','reader']]){
 const png=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(`previews/${file}.png`,new Uint8Array(await png.arrayBuffer()));
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:20},maxChars:1500});
await fs.writeFile('WORKBOOK_INSPECT.json',JSON.stringify({errors:errors.ndjson,sheets:(await wb.inspect({kind:'sheet',include:'id,name'})).ndjson,readerRows:rows.length},null,2));
await fs.writeFile('reader_rows.json',JSON.stringify({rows,index},null,2));
await (await SpreadsheetFile.exportXlsx(wb)).save(`${out}/中文盲审评分与原文.xlsx`);
console.log('Exported workbook; 30 blank ratings + 1 exception; reader rows:',rows.length);
