import json,hashlib,html
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter
from sample_v6 import select
HERE=Path(__file__).resolve().parent;WORK=HERE.parent
RUN=WORK/'authorized_remaining330_20261019'
OUT=HERE/'outputs'/'01a13537-v6'
BLIND=OUT/'01_盲审材料';PRIVATE=OUT/'02_仅协调者_勿发盲审者'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def main():
    BLIND.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(exist_ok=True)
    for folder,manifest in [(WORK,WORK/'ARTIFACT_HASHES_FINAL.json'),(RUN,RUN/'FINAL_ARTIFACT_HASHES.json'),(WORK/'authorized_resume_20261019',RUN/'PREVIOUS_ARTIFACT_HASHES.json')]:
        for name,digest in read(manifest).items():assert sha(folder/name)==digest,(folder,name)
    pre=read(WORK/'RUN_PREFLIGHT.json')
    for field in ['protected_hashes','frozen_hashes']:
        for name,digest in pre[field].items():assert sha(Path(name))==digest,name
    allrows=read(RUN/'terminal_results/REVIEW_DIAGNOSTICS_441.json');valid=[r for r in allrows if r['review_status']=='completed'];invalid=[r for r in allrows if r['review_status']!='completed']
    assert len(allrows)==441 and len(valid)==440 and len(invalid)==1
    old=read(WORK/'authorized_resume_20261019/sampling_policy_v5.json')
    policy={**old,'version':'postrun-440-valid-v6-20261019','required_population':440,'approval_basis':'Explicit delegated post-run amendment: sample30 from440 valid reviews and append1 separate missing-review diagnostic task. No API calls.','timing_disclosure':'Amended after all440 valid results were revealed. Not preregistered. Prior v5 required441 valid; one permanently quarantined ID mismatch made that gate unreachable without changing response validity.','created_at_utc':datetime.now(timezone.utc).isoformat(),'interpretation':'Fixed deterministic hash ordering; n_h/N_h and N_h/n_h are nominal inclusion fractions and weights under a hash-as-random interpretation, not randomization guarantees. Population amendment occurred after all440 valid outcomes were observed; cannot remove post-run selection or missingness bias.','old_population_gate':441,'new_population_gate':440,'excluded_invalid_id':invalid[0]['review_id'],'exception_in_machine_agreement_denominator':False,'original_total_coverage':{'candidates':441,'valid':440,'invalid':1,'unsent':0}}
    selected,strata=select(valid,[r['review_id'] for r in valid],policy)
    repeated,_=select(list(reversed(valid)),[r['review_id'] for r in valid],policy)
    assert [r['review_id'] for r in selected]==[r['review_id'] for r in repeated]
    assert len(selected)==30 and len({r['review_id'] for r in selected})==30 and sum(s['population'] for s in strata)==440 and sum(s['selected'] for s in strata)==30
    assert all(s['selected']==0 for s in strata if not s['population'])
    mapping={'direct':'直接支持','partial':'部分支持','contradicted':'相矛盾','insufficient':'证据不足','uncertain':'不确定'}
    normalized=[]
    for r in valid:
        raw=read(WORK/r['response_file']);j=json.loads(raw['response']['choices'][0]['message']['content']);assert j==r['machine_judgment'] and j['review_id']==r['review_id']
        normalized.append({'review_id':r['review_id'],'raw_support':j['support'],'normalized_support':j['support'],'display_zh':mapping[j['support']],'anchor_quality':r['anchor_quality'],'applicability':j['applicability']})
    packets={p['review_id']:p for p in read(WORK/'QWEN_BLIND_PACKETS.json')}
    order=sorted(selected,key=lambda r:hashlib.sha256(('blind-order-v6|'+r['review_id']).encode()).hexdigest())
    blind=[];key=[]
    for i,r in enumerate(order+invalid,1):
        rid=r['review_id'];code=f'H{i:02d}' if i<=30 else 'X01';p=packets[rid]
        blind.append({'code':code,'task_type':'机器评审抽查' if i<=30 else '缺失诊断（不计入30条一致率）','source_requirement':p['source_requirement'],'candidate':p['candidate'],'cited_evidence':p['cited_evidence'],'citation_checks':p['citation_checks'],'evidence_policy':p['evidence_policy']})
        key.append({'code':code,**r,'included_in_machine_agreement':i<=30})
    save(PRIVATE/'协议修订_v6.json',policy);save(PRIVATE/'分层总体_配额_名义概率权重.json',strata);save(PRIVATE/'本地解盲键_含机器标签.json',key);save(PRIVATE/'440原标签与中文映射核验.json',normalized)
    save(HERE/'blind_input.json',blind)
    rules=[
      ['工作量','共31项：H01–H30用于机器评审抽查，X01为独立缺失诊断，不进入30条机器评审一致率计算。所有人工判断初始留空；不要代填。'],
      ['修订披露','本材料按结果揭晓后的v6协议从440条有效评审抽30。原441全部有效门槛因1条ID异常修订。并非预注册抽样，不是总体无偏准确率估计。'],
      ['操作','先在原文阅读或离线HTML按编号阅读，再到评分30或异常核对填写黄色单元格。请勿打开协调者目录。'],
      ['证据范围','展示的是当时实际提供的引用摘录，不是完整文献。本交付不再截断；未提供的片段外信息视为未知。相同数字不等于同一语义支持。'],
      ['支持：直接支持','全部实质性判据均能由给定证据支撑，对象、行为、范围、单位和比较运算符一致，无新增推导。'],
      ['支持：部分支持','至少一部分得到支持，但仍有实质性内容未被证据覆盖。不得与直接支持合并成正确率。'],
      ['支持：相矛盾','给定证据与至少一项实质性判据明确冲突。请注明冲突的证据编号和具体文字。'],
      ['支持：证据不足','现有引用为空、缺失或无法建立足够支持，且没有明确反证。不是自动判为错误。'],
      ['支持：不确定','材料歧义或判断能力限制，无法在上述类别中作可靠决定。请说明不确定原因。'],
      ['适用条件','明确符合：机型/工况有明确匹配；明确不符：有明确冲突；一般规则有依据：证据确为可泛化规则且有依据；未知：机型、工况或范围缺失。证据支持与工程适用性分别判断。'],
      ['可验证性','可检验：可用明确方法和可观察结果核验；不可检验：验收目标/方法无法落实；不确定：信息不足。非数值判据也可能可检验。'],
      ['忠实性（补充）','原文摘录／忠实转述／新增推导或综合／无依据／不确定。核对引用能否逐字定位，但字面存在不自动等于语义支持。'],
      ['备注','记录所依据的证据编号、关键条件和理由。部分支持、相矛盾、证据不足、不确定或适用性未知时尤其应说明。原需求相关性问题也写入备注。'],
      ['保存与交付','Excel另存为新的.xlsx并使用Ctrl+S保存，关闭再打开核对已填内容。返回完整.xlsx，不只截图或CSV。HTML只读，不记录或保存评分。'],
      ['盲化边界','已去除生成组、机器判断、抽样层和内部ID。来源名称、层级和写作风格仍可能提供策略线索，不称完全盲法。'],
      ['缺失诊断','X01只作独立人工核对，评分同规则；不得补成有效机器结果。其原始ID异常响应仍隔离保留，人工结论不替代机器标签。'],
    ]
    save(HERE/'rules.json',rules)
    esc=html.escape
    nav=' '.join(f'<a href="#{b["code"]}">{b["code"]}</a>' for b in blind)
    cards=[]
    for b in blind:
        c=b['candidate'];parts=[f'<article id="{b["code"]}"><h2>{b["code"]} · {esc(b["task_type"])}</h2>',f'<h3>原需求</h3><pre>{esc(b["source_requirement"])}</pre>']
        for field,label in [('shall_statement','候选条目'),('measurable_criterion','判据'),('applicable_condition','声明适用条件'),('verification_method','声明验证方法'),('acceptance_criteria','声明验收要求')]:
            v=c.get(field,'未提供');v='\n'.join(v) if isinstance(v,list) else str(v);parts.append(f'<h3>{label}</h3><pre>{esc(v)}</pre>')
        parts.append('<h3>实际引用原文（完整保留所给摘录）</h3>')
        for e in b['cited_evidence']:parts.append(f'<h4>{esc(e["evidence_id"])}</h4><pre class="quote">{esc(e["supplied_excerpt"])}</pre>')
        if not b['cited_evidence']:parts.append('<p>未提供有效引用原文。</p>')
        parts.append('<p><a href="#top">返回目录</a> · 请在Excel相同编号行评分。本页只读。</p></article>');cards.append(''.join(parts))
    content='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>31项离线盲审阅读</title><style>body{font-family:"Microsoft YaHei",Arial,sans-serif;background:#f4f6f8;color:#17263c;max-width:1080px;margin:32px auto;padding:0 22px;line-height:1.7}article,section{background:white;padding:24px;margin:24px 0;border:1px solid #d6dce4;border-radius:8px}nav a{display:inline-block;margin:4px;padding:4px 10px;background:#e4eaf2;color:#23446e}h2{border-bottom:2px solid #365b87;padding-bottom:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}.quote{border-left:4px solid #8d9fb5;padding:12px;background:#f3f6fa}a{color:#1c5697}summary{cursor:pointer;font-weight:bold}@media print{nav{display:none}article{break-before:page}}</style><body id="top"><h1>31项离线盲审阅读</h1><p>30条抽查＋1条独立缺失诊断。人工评分全部在Excel填写；此HTML不保存评分，也不联网。</p><p><a href="中文盲审评分与原文.xlsx">打开同目录评分Excel</a></p><nav>'+nav+'</nav><section><details open><summary>评分规则与保存说明</summary>'+''.join(f'<p><strong>{esc(k)}：</strong>{esc(v)}</p>' for k,v in rules)+'</details></section>'+''.join(cards)+'</body></html>'
    (BLIND/'离线阅读.html').write_text(content,encoding='utf8')
    (BLIND/'阅读与保存说明.txt').write_text('\n\n'.join(k+'：'+v for k,v in rules),encoding='utf8')
    interpretation=(RUN/'terminal_results/完整终态摘要_440有效_1异常.txt').read_text(encoding='utf8')
    interpretation+='\n\n后续v6修订：本次另获授权，在全部结果揭晓后将抽样总体改为440条有效响应。以原5标签×2臂、固定hash与轮转抽30，另附1异常项。旧门槛和旧临时材料未改。不得称预注册抽样，无法消除事后规则与缺失选择偏差。名义n_h/N_h及N_h/n_h供协调者核算，不将直接与部分支持合并为正确率。55源完整配对为有条件子集：零Q的源不作0%填补，缺失源不进入比例均值；60源计数明细均保留。\n'
    interpretation+='\n独立核验补充：semantic_new的64条原始direct中6条锚点失败，random_new的29条中7条失败，不能将64/29称为锚点通过支持数。55源条件配对排除OR002（ID异常）、OR022/OR035/OR058（semantic无Q）、OR041（random无Q）；两臂生成候选也不同。该子集等源均值差（semantic减random）：direct +0.133398，partial +0.186861，insufficient -0.320260。来源名、tier与写作风格仍可提供线索，因此只称去除显式组/模型/OR元数据，不能称完全盲法。费用12.5212804仅为模型账本，非实付。\n'
    (PRIVATE/'中文结果解读与修订理由.txt').write_text(interpretation,encoding='utf8')
    (OUT/'先读我_文件分发.txt').write_text('只向盲审者提供01_盲审材料目录。02_仅协调者_勿发盲审者含组别和机器标签，严禁随盲表发出。共31项阅读任务；30条用于机器评审抽查，1条用于缺失诊断。人工全部留空。本任务未邀请或联系专家，也未创建人工结果。',encoding='utf8')
    save(HERE/'PREPARE_CHECK.json',{'created_utc':policy['created_at_utc'],'old_hashes_unchanged':True,'population':440,'all_candidate_coverage':441,'sample':30,'exception':1,'reproducible_reversed_input':True,'raw_normalized_identity':True,'strata':strata,'new_calls':0})
    print(json.dumps({'sample':30,'exception':1,'strata':strata},ensure_ascii=False))
if __name__=='__main__':main()
