'use strict';
const $ = id => document.getElementById(id);
const labels = {unanswered:'未答', relevant:'相关', irrelevant:'不相关', uncertain:'不确定'};
const phaseLabels = {practice:'练习',pilot:'试做校准（不计正式分数）',formal:'正式'};
let task = null, token = null, dirty = false, saving = null, timer = null, generation = 0, busy = false;
let newNonce = null, pendingBackup = null;
const entry = new URLSearchParams(location.search);
const formalSlot = entry.get('formal')==='1' && ['A','B'].includes(entry.get('reviewer')) ? entry.get('reviewer') : null;
const storageKey = 'mapping-review-active-v1'+(formalSlot?':formal-'+formalSlot:'');
let preloadedFormal = null;
const formalReady = formalSlot ? fetch('/formal_assignment.json').then(async r=>{if(!r.ok)throw new Error('正式包加载失败');preloadedFormal=await r.json();if(preloadedFormal.kind!=='formal')throw new Error('正式包类型不符');}).catch(error=>{message(error.message,true);}) : Promise.resolve();
function message(value, error=false) { $('message').textContent=value; $('message').className=error?'error':''; }
function nonce() { return Array.from(crypto.getRandomValues(new Uint8Array(16)), v=>v.toString(16).padStart(2,'0')).join(''); }
function setBusy(value) { busy=value; $('workspace').inert=value; }
function recoveryRequest(backup) {
  const key='mapping-review-recovery-'+backup.sha256;
  let id=sessionStorage.getItem(key);
  if(!id){id=nonce();sessionStorage.setItem(key,id);}
  return {key,id};
}
async function api(path, body, blob=false) {
  const controller = new AbortController(), timeout = setTimeout(()=>controller.abort(), 12000);
  try {
    const response = await fetch('/api/'+path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body), signal:controller.signal});
    if (!response.ok) { const result=await response.json(); const error=new Error(result.error || '请求失败'); error.code=result.code; throw error; }
    return blob ? await response.blob() : await response.json();
  } catch(error) { if(error.name==='AbortError') throw new Error('本机服务未响应。记录仍在页面，请导出待保存副本后恢复。'); throw error; }
  finally { clearTimeout(timeout); }
}
function persist() {
  if (!task) return;
  try { localStorage.setItem(storageKey,JSON.stringify({task,token,dirty})); }
  catch { message('浏览器恢复缓存不可用，请立即保存并导出备份。',true); }
}
function changed() { dirty=true; generation++; persist(); status(); clearTimeout(timer); timer=setTimeout(()=>save().catch(()=>{}),700); }
function sourceComplete(a){return a.first_pass_done&&a.coverage_reviewed&&!Object.values(a.candidates).includes('unanswered')&&(task.package.kind!=='formal'||(a.review_details?.complete==='yes'&&a.review_details?.total_minutes!==null&&a.review_details?.exposure==='after_first_pass'));}
function status() {
  if (!task) return;
  $('saveState').textContent=saving?'正在保存…':dirty?'有待保存修改':'已保存到本机 · '+task.updated_at.replace('T',' ').replace('Z',' UTC');
  $('draftBtn').hidden=!dirty;
  const answers=Object.values(task.answers);
  const done=answers.filter(sourceComplete).length;
  const uncertain=answers.reduce((n,a)=>n+Object.values(a.candidates).filter(v=>v==='uncertain').length+a.missing_pairs.filter(p=>p.verdict==='uncertain').length,0);
  $('progress').textContent=`源需求审核 ${done} / ${answers.length} · 不确定配对 ${uncertain}（需保留或后续裁定）`;
  document.querySelectorAll('[data-source-id]').forEach(b=>{
    const a=task.answers[b.dataset.sourceId],done=sourceComplete(a);
    b.textContent=b.dataset.sourceId+(done?' · 已审核':' · 待审核');
  });
  const a=currentAnswer();
  $('sourceStatus').textContent=!a.first_pass_done?'先完成独立首判':!a.coverage_reviewed?'尚未确认完整 taxonomy 查漏':Object.values(a.candidates).includes('unanswered')?'仍有候选未答':!sourceComplete(a)?'请补齐正式阶段、耗时和完成声明':'本条记录齐全；不确定仍待解决，尚不等于gold';
}
async function save() {
  clearTimeout(timer);
  if (!task) return true;
  if (saving) { await saving; if(dirty) return save(); return true; }
  if (!dirty) return true;
  const startGeneration=generation, taskId=task.id;
  const body={id:task.id,token,revision:task.revision,answers:structuredClone(task.answers),current_index:task.current_index};
  saving=(async()=>{
    try {
      const result=await api('save',body);
      if(task && task.id===taskId) {
        task.revision=result.task.revision; task.updated_at=result.task.updated_at;
        if(generation===startGeneration) dirty=false;
        persist();
      }
    } catch(error) { message('保存未完成：'+error.message,true); throw error; }
  })();
  status();
  try { await saving; } finally { saving=null; status(); }
  if (dirty && generation!==startGeneration) return save();
  return true;
}
function confirmAction(title, description, yes='确认') {
  return new Promise(resolve=>{
    $('confirmTitle').textContent=title; $('confirmText').textContent=description; $('confirmYes').textContent=yes;
    const dialog=$('confirmDialog');
    const finish=value=>{dialog.close();dialog.oncancel=null;resolve(value);};
    $('confirmYes').onclick=()=>finish(true); $('confirmNo').onclick=()=>finish(false);
    dialog.oncancel=event=>{event.preventDefault();finish(false);}; dialog.showModal();
  });
}
async function protectSwitch() {
  if(!dirty && !saving) return true;
  if(!await confirmAction('先保存当前审查？','切换前将保存当前修改；保存失败时保留当前页面。','保存并继续')) return false;
  try {await save(); return true;} catch{return false;}
}
function activate(result) {
  task=result.task;token=result.token;dirty=false;generation=0;persist();render();
  message(task.package.kind==='practice'?'当前为隔离练习，所有答案仅用于工具试用，不进入论文研究数据。':task.package.kind==='pilot'?'当前为真实源需求试做校准，不进入正式评分。请记录每条完整审核耗时和规则疑问。':'独立审查已打开，请保留中文原始判断。');
}
function source(){return task.package.sources[task.current_index];}
function currentAnswer(){return task.answers[source().id];}
function button(label, callback, className='') {const b=document.createElement('button');b.textContent=label;b.className=className;b.onclick=callback;return b;}
function pairName(pair) {return task.package.components[pair.component]+' / '+task.package.intents[pair.intent];}
function renderPairs(target, pairs, removable) {
  $(target).replaceChildren();
  if(!pairs.length){const p=document.createElement('p');p.className='hint';p.textContent='暂无配对记录。';$(target).append(p);return;}
  pairs.forEach((pair,index)=>{
    const row=document.createElement('div');row.className='pairItem';const content=document.createElement('div');
    const name=document.createElement('strong');name.textContent=pairName(pair);const note=document.createElement('p');note.textContent=labels[pair.verdict]+(pair.note?' · '+pair.note:'');content.append(name,note);row.append(content);
    if(removable)row.append(button('移除',async()=>{if(await confirmAction('移除此配对？','仅移除当前未锁定的配对记录。')){pairs.splice(index,1);changed();render();}}));
    $(target).append(row);
  });
}
function render(){
  $('welcome').hidden=!!task;$('workspace').hidden=!task;
  ['saveBtn','backupBtn','csvBtn','leaveBtn'].forEach(id=>$(id).disabled=!task);
  if(!task)return;
  const p=task.package,a=currentAnswer(),s=source();
  $('taskLabel').textContent=phaseLabels[p.kind]+' · '+task.reviewer+' · '+p.title;
  $('taskMeta').textContent=`任务 ${task.id.slice(0,12)} · 数据版本 ${p.version.slice(0,12)} · 原记录语言：中文`;
  $('sourcePosition').textContent=`源需求 ${task.current_index+1} / ${p.sources.length}`;
  $('sourceId').textContent=s.id;$('sourceText').textContent=s.text;
  $('sourceList').replaceChildren();p.sources.forEach((s,i)=>{
    const a=task.answers[s.id],done=sourceComplete(a);
    const sourceButton=button(s.id+(done?' · 已审核':' · 待审核'),()=>navigate(i),i===task.current_index?'active':'');
    sourceButton.dataset.sourceId=s.id;$('sourceList').append(sourceButton);
  });
  $('firstPass').hidden=a.first_pass_done;$('candidateSection').hidden=!a.first_pass_done;$('coverageLabel').hidden=!a.first_pass_done;
  $('taxonomyTitle').textContent=a.first_pass_done?'3 · 完整分类目录查漏':'完整分类目录 · 添加首判配对';
  renderPairs('initialPairs',a.initial_pairs,!a.first_pass_done);renderPairs('lockedInitial',a.initial_pairs,false);renderPairs('missingPairs',a.missing_pairs,true);
  $('candidates').replaceChildren();
  if(a.first_pass_done)s.candidates.forEach(pair=>{
    const row=document.createElement('div');row.className='candidate';const name=document.createElement('div');name.className='pairName';name.textContent=pairName(pair);
    const code=document.createElement('span');code.className='code';code.textContent=pair.id;name.append(code);
    const choices=document.createElement('div');choices.className='choices';choices.setAttribute('role','group');choices.setAttribute('aria-label',pairName(pair));
    Object.entries(labels).forEach(([value,label])=>{const b=button(label,()=>{a.candidates[pair.id]=value;changed();render();},a.candidates[pair.id]===value?'selected':'');b.dataset.value=value;b.setAttribute('aria-pressed',String(a.candidates[pair.id]===value));choices.append(b);});
    row.append(name,choices);$('candidates').append(row);
  });
  const previousComponent=$('component').value;
  $('component').replaceChildren();Object.entries(p.components).forEach(([id,name])=>{$('component').add(new Option(name,id));});
  if(p.components[previousComponent])$('component').value=previousComponent;
  renderIntents();
  $('taxonomySummary').textContent=`展开完整 taxonomy：${Object.keys(p.components).length} 个部件、${Object.keys(p.intents).length} 个方面`;
  $('taxonomyAll').replaceChildren();
  Object.entries(p.components).forEach(([c,name])=>{const line=document.createElement('p');const title=document.createElement('b');title.textContent=name+'：';line.append(title,document.createTextNode(p.taxonomy[c].map(i=>p.intents[i]).join('；')));$('taxonomyAll').append(line);});
  $('coverage').checked=a.coverage_reviewed;$('note').value=a.note;
  $('formalDetails').hidden=p.kind!=='formal';
  if(p.kind==='formal'){const d=a.review_details??={exposure:a.first_pass_done?'uncertain':'not_viewed',first_pass_at:'',first_candidate_at:'',total_minutes:null,interruption_minutes:null,complete:'unanswered',questions:''};
    $('reviewExposure').value=d.exposure;$('reviewComplete').value=d.complete;$('reviewMinutes').value=d.total_minutes??'';$('reviewInterrupt').value=d.interruption_minutes??'';$('reviewQuestions').value=d.questions;
    $('reviewFirstTime').value=d.first_pass_at;$('reviewCandidateTime').value=d.first_candidate_at;
    $('reviewTimes').textContent='首判确认：'+(d.first_pass_at||'未确认')+'；首次显示候选：'+(d.first_candidate_at||'未显示');}
  $('prevBtn').disabled=task.current_index===0;$('nextBtn').disabled=task.current_index===p.sources.length-1;status();
}
function renderIntents(){const prev=$('intent').value;$('intent').replaceChildren();task.package.taxonomy[$('component').value].forEach(i=>$('intent').add(new Option(task.package.intents[i],i)));if(task.package.taxonomy[$('component').value].includes(prev))$('intent').value=prev;}
function navigate(index){task.current_index=index;changed();render();window.scrollTo({top:0,behavior:'smooth'});}
async function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
function canonical(value){if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';return JSON.stringify(value);}
async function exportDraft(){
  const copy=structuredClone(task);copy.revision++;
  const backup={format:'mapping-review-backup-v1',task:copy,token};
  backup.sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(backup)))),v=>v.toString(16).padStart(2,'0')).join('');
  await download(new Blob([JSON.stringify(backup,null,2)],{type:'application/json'}),`待保存副本_${task.id.slice(0,12)}.review.json`);
  message('已导出待保存副本。它包含页面修改；如有版本冲突，请恢复为新副本，勿覆盖原记录。');
}
$('newBtn').onclick=async()=>{if(busy||!await protectSwitch())return;newNonce=nonce();$('newForm').reset();$('assignmentLabel').hidden=true;$('newError').textContent='';await formalReady;$('loadedAssignment').hidden=!preloadedFormal;if(preloadedFormal){$('taskKind').value='formal';$('reviewer').value='专家'+formalSlot;}$('newDialog').showModal();};
$('cancelNew').onclick=()=>{if(!busy)$('newDialog').close();};
$('newDialog').oncancel=e=>{if(busy)e.preventDefault();};
$('taskKind').onchange=()=>{$('assignmentLabel').hidden=$('taskKind').value==='practice'||($('taskKind').value==='formal'&&!!preloadedFormal);$('loadedAssignment').hidden=!($('taskKind').value==='formal'&&preloadedFormal);};
$('newForm').onsubmit=async event=>{
  event.preventDefault();if(busy)return;setBusy(true);$('createBtn').disabled=true;$('cancelNew').disabled=true;
  try{
    const kind=$('taskKind').value;let packageData=null;
    if(kind==='formal'&&preloadedFormal){packageData=preloadedFormal;}else if(kind!=='practice'){const file=$('assignmentFile').files[0];if(!file)throw new Error('请选择协调者提供的对应任务包。');if(file.size>4000000)throw new Error('任务包过大。');packageData=JSON.parse(await file.text());if(packageData.kind!==kind)throw new Error('任务包类型与所选类型不符，不能将试做或源库标为正式。');}
    const result=await api('new',{kind,reviewer:$('reviewer').value.trim(),package:packageData,request_id:newNonce});activate(result);$('newDialog').close();
  }catch(error){$('newError').textContent='创建失败：'+error.message;}finally{setBusy(false);$('createBtn').disabled=false;$('cancelNew').disabled=false;}
};
$('saveBtn').onclick=async()=>{try{await save();message('当前审查已保存到本机。建议同时导出备份。');}catch{}};
$('openBtn').onclick=async()=>{if(busy||!await protectSwitch())return;$('openFile').value='';$('openFile').click();};
$('openFile').onchange=async()=>{
  const file=$('openFile').files[0];if(!file||busy)return;setBusy(true);
  try{if(file.size>4000000)throw new Error('备份文件过大。');pendingBackup=JSON.parse(await file.text());let result;
    try{result=await api('open',{backup:pendingBackup});}
    catch(error){
      if(!['record_missing','record_corrupt','backup_newer'].includes(error.code))throw error;
      if(!await confirmAction('恢复为独立副本？',error.message+' 原文件不会被覆盖。','恢复副本'))return;
      const recovery=recoveryRequest(pendingBackup);
      result=await api('open',{backup:pendingBackup,restore:true,request_id:recovery.id});
      sessionStorage.removeItem(recovery.key);
    }
    activate(result);
  }catch(error){message('打开失败：'+error.message+' 当前审查保持不变。',true);}finally{setBusy(false);pendingBackup=null;}
};
$('backupBtn').onclick=async()=>{try{await save();const backup=await api('export',{id:task.id,token});await download(new Blob([JSON.stringify(backup,null,2)],{type:'application/json'}),`${task.package.kind}_${task.id.slice(0,12)}_r${task.revision}.review.json`);message('备份已下载，包含本位专家的原始记录。请妥善保管。');}catch(error){message(error.message,true);}};
$('csvBtn').onclick=async()=>{try{await save();await download(await api('export',{id:task.id,token,format:'csv'},true),`${task.package.kind}_${task.id.slice(0,12)}_r${task.revision}.csv`);message('CSV 已导出；包含候选判断、补漏、首判和中文备注。可恢复原记录请使用 JSON 备份。');}catch(error){message(error.message,true);}};
$('leaveBtn').onclick=async()=>{if(busy||!await protectSwitch())return;if(!await confirmAction('离开本位专家的审查？','请先导出备份。离开后清除浏览器恢复入口，本机保存文件保留；下一位专家可新建自己的任务。','离开'))return;clearTimeout(timer);localStorage.removeItem(storageKey);task=null;token=null;dirty=false;$('draftBtn').hidden=true;render();message('已离开审查。请用自己的备份打开旧任务，或为下一位专家新建任务。');};
$('component').onchange=renderIntents;
$('addPair').onclick=()=>{const a=currentAnswer(),c=$('component').value,i=$('intent').value,target=a.first_pass_done?a.missing_pairs:a.initial_pairs;const id=c+':'+i;if(target.some(p=>p.component===c&&p.intent===i)||(a.first_pass_done&&Object.hasOwn(a.candidates,id))){message('此配对已存在，请在原位置判断；没有添加重复记录。',true);return;}target.push({component:c,intent:i,verdict:$('pairVerdict').value,note:$('pairNote').value});$('pairNote').value='';changed();render();message('配对已添加。');};
$('unlockBtn').onclick=async()=>{if(busy)return;setBusy(true);try{if(!await confirmAction('锁定独立首判并显示候选？','首判记录将保留且不可回写，候选判断与后续补漏另行记录。','锁定并显示'))return;currentAnswer().first_pass_done=true;if(task.package.kind==='formal'){const d=currentAnswer().review_details,now=new Date().toISOString();d.first_pass_at=now;d.first_candidate_at=now;if(d.exposure==='not_viewed')d.exposure='after_first_pass';}changed();await save();render();}catch{render();}finally{setBusy(false);}};
$('coverage').onchange=()=>{currentAnswer().coverage_reviewed=$('coverage').checked;changed();status();};
$('note').oninput=()=>{currentAnswer().note=$('note').value;changed();};
for(const [id,key] of [['reviewExposure','exposure'],['reviewComplete','complete'],['reviewQuestions','questions'],['reviewFirstTime','first_pass_at'],['reviewCandidateTime','first_candidate_at']])$(id).oninput=()=>{currentAnswer().review_details[key]=$(id).value;changed();};
for(const [id,key] of [['reviewMinutes','total_minutes'],['reviewInterrupt','interruption_minutes']])$(id).oninput=()=>{currentAnswer().review_details[key]=$(id).value===''?null:Number($(id).value);changed();};
$('prevBtn').onclick=()=>navigate(task.current_index-1);$('nextBtn').onclick=()=>navigate(task.current_index+1);
$('draftBtn').onclick=exportDraft;
window.addEventListener('beforeunload',event=>{if(dirty||saving){persist();event.preventDefault();event.returnValue='';}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&dirty){persist();save().catch(()=>{});}});
(async()=>{
  try{
    const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(!saved)return;
    const result=await api('get',{id:saved.task.id,token:saved.token});
    activate({task:result.task,token:saved.token});
    if(saved.dirty){
      if(saved.task.revision===result.task.revision){task.answers=saved.task.answers;task.current_index=saved.task.current_index;changed();render();message('已恢复关闭前的待保存修改，正在保存。');}
      else{task=saved.task;token=saved.token;dirty=true;persist();render();message('检测到版本冲突，保留关闭前的页面副本。请先导出待保存副本，再重新打开已保存记录。',true);}
    }else message('已恢复上次审查，继续你的独立评阅。');
  }catch(error){
    try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(saved?.task){task=saved.task;token=saved.token;dirty=true;render();}}catch{}
    message('自动恢复未完成：'+error.message+' 可导出待保存副本，或打开 JSON 备份。',true);
  }
})();
