"""Freeze S3 inputs and draw once. Local files only; never calls a model."""
import hashlib, html, importlib.util, json, random, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
COORD=HERE/'02_协调者_勿发评审'
EXPERT=HERE/'outputs/01a13537-s3/01_仅此目录可发评审'
SEED=202610191555
FIELDS=['shall_statement','measurable_criterion','applicable_condition','verification_method','acceptance_criteria']
LABELS=['候选要求','数值判据','适用条件','验证方法','验收内容']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda obj:hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
def dump(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8').strip()

GUIDE=[
 ['任务','独立核查50条候选中的全部实质性数值及其适用条件，不以有无引用判断对错。先阅读完整原文，再填写评分。'],
 ['填写方式','在“身份与说明”填写身份和独立评审声明；在“评分50”填写黄色单元格。两位评审各自从同一空白模板另存文件，不共享首判。'],
 ['正确','数值、单位、运算符、对象、范围与条件均有明确依据；整条所有关键数值均满足。一个关键错误不能整条判正确。'],
 ['可接受','有明确适用依据说明允许该近似、范围或工程取值，并写出允许理由；不采用统一±20%或仅凭数量级判断。'],
 ['错误','至少一项关键数值、单位、方向、对象或条件与适用依据明确冲突，注明冲突位置。'],
 ['无法判断','资料不足、来源版本不明或超出把握。不要为完成评分而猜测；不能将其自动当正确或错误。'],
 ['适用性','适用：依据范围与所声明的对象和工况一致；不适用：明确不符；工况不明：缺乏判断所需信息。不要替候选补设有利条件。'],
 ['具体依据','正确或可接受必须填写具体依据。记录文献名称、版本、页码/条款及必要解释；若仅为实践判断，明确写“实践判断：”和经验适用范围，不能伪装法规结论。'],
 ['同等查证','各条均可独立查阅原始规范/厂家完整页、表头、脚注及适用范围；不只按片段或某一数字判断。缺引用不自动错，有引用不自动对。'],
 ['参考材料限制','本包没有建立完整工程参考真值或统一完备证据包。需独立查原件；无法获得或无法确定条件时允许无法判断/工况不明，不要求强行决定。'],
 ['信心','1=低，2=中，3=高；信心不替代依据。备注可说明多参数、版本冲突或其他限制。'],
 ['独立性','先独立完成并保存首判，未提交前不交换答案。记录既往是否接触这些输出或类似审核。共同作者身份必须如实选择。'],
 ['校准与工时','正式评分前可讨论通用定义及另选的非样本案例，不提供标准答案，不用正式样本协商评分。先实测校准耗时，再估计正式工时；没有预设节时结论。'],
 ['原文与盲法','正文、例如/典型、机型、工况、单位和运算符全部保留；只不展示原始引用元数据。技术信息可能提示来源，不能承诺完全盲化。'],
 ['离线阅读','HTML是只读阅读辅助，不保存评分。所有答案只写Excel。勿修改原文、盲ID或工作表结构。'],
 ['第二阶段','完成并提交第一阶段后，协调者才可提供独立可选的出处猜测材料；不要在第一阶段推测组别或查解盲键。'],
 ['范围','本次为数值候选的限定审核，不是全系统完整性验证；不须重做此前[Q]审核。TBD或未知不算正确完成。'],
]

def main():
    if (COORD/'SAMPLE_FROZEN.json').exists():raise SystemExit('Frozen sample exists: refusing redraw/overwrite')
    COORD.mkdir(parents=True,exist_ok=True);EXPERT.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc).isoformat()
    dirty=git('diff','--name-only').splitlines()
    arch=HERE/'checkpoint_worktree';arch.mkdir(exist_ok=True)
    for n in dirty:
        p=ROOT/n
        if p.is_file():dest=arch/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    (arch/'tracked_worktree.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=ROOT))
    dump(COORD/'CHECKPOINT.json',{'utc':now,'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'checkpoint_branch':'checkpoint/before-s3-paired-review50-20261019','status':git('status','--short','--untracked-files=no'),'dirty_backup_hashes':{n:sha(ROOT/n) for n in dirty if (ROOT/n).is_file()},'backup_directory':str(arch)})
    paths=[ROOT/'data/search_results/exp_v4'/f for f in ['rag_v4_results.json','norag_v4_results.json','unified_v5/paper_numbers_unified.json']]
    paths += [ROOT/'data/processed/evidence_units_v3_audited.jsonl',ROOT/'data/processed/original_requirements_v2.jsonl',ROOT/'cooling_rag_mg/grade_classifier.py',ROOT/'scripts/110_unified_regrade.py',ROOT/'data/expert_round2/expert_workbook.xlsx',ROOT/'data/expert_round2/expert_key.json']
    final=ROOT.parent/'resubmission_4762284_20261019/texpage_source_4762284'
    paths += [p for p in final.rglob('*') if p.is_file()]
    old=read(ROOT/'revision_artifacts/qualitative_5arm_authorized_run_20261019/RUN_PREFLIGHT.json')
    paths += [Path(p) for group in ['protected_hashes','frozen_hashes'] for p in old[group]]
    protected={str(p):sha(p) for p in sorted(set(paths))}
    dump(COORD/'PROTECTED_BEFORE.json',protected)
    snap=COORD/'frozen_inputs';snap.mkdir()
    source_paths={'rag':paths[0],'norag':paths[1],'kb':ROOT/'data/processed/evidence_units_v3_audited.jsonl','requirements':ROOT/'data/processed/original_requirements_v2.jsonl','classifier':ROOT/'cooling_rag_mg/grade_classifier.py'}
    inputs={}
    for key,p in source_paths.items():
        dest=snap/(key+p.suffix);shutil.copy2(p,dest);inputs[key]={'original_path':str(p),'sha256':sha(p),'snapshot':str(dest.relative_to(HERE))}
    dump(COORD/'INPUT_MANIFEST.json',inputs)
    spec=importlib.util.spec_from_file_location('frozen_classifier',snap/'classifier.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    kb={u['id']:u for u in map(json.loads,(snap/'kb.jsonl').read_text(encoding='utf8').splitlines())}
    req={u['requirement_id']:u['requirement_text'] for u in map(json.loads,(snap/'requirements.jsonl').read_text(encoding='utf8').splitlines())}
    pools={}
    for arm,grades in [('rag',{'A','B'}),('norag',{'X'})]:
        pool=[]
        for rs in read(snap/(arm+'.json'))['result_sets']:
            for idx,raw in enumerate(rs['engineering_requirements'],1):
                grade=mod.classify_grade(raw.get('measurable_criterion'),raw.get('evidence_citations'),kb,numeric_policy='numeric-ranges-v1')
                if grade not in grades:continue
                assert not mod._TBD_PATTERN.search(str(raw.get('measurable_criterion')))
                identity={'input_sha256':inputs[arm]['sha256'],'source_id':rs['source_requirement_id'],'row_1based':idx,'candidate_sha256':digest(raw)}
                pool.append({'arm':arm,**identity,'stable_id':digest(identity),'grade':grade,'original_requirement':req[identity['source_id']],'candidate':raw})
        pools[arm]=pool
    assert [len(pools[x]) for x in ['rag','norag']]==[72,204]
    counts={a:Counter(r['source_id'] for r in rows) for a,rows in pools.items()}
    common=sorted(counts['rag'].keys()&counts['norag'].keys());eligible=[s for s in common if min(counts[a][s] for a in counts)>=2]
    assert len(common)==20 and len(eligible)==15
    supplemental=sorted(random.Random(str(SEED)+'|extra_sources').sample(eligible,5))
    selected=[]
    for sid in common:
        for arm in ['rag','norag']:
            frame=sorted([r for r in pools[arm] if r['source_id']==sid],key=lambda r:r['row_1based'])
            picks=random.Random(f'{SEED}|within|{sid}|{arm}').sample(frame,2 if sid in supplemental else 1)
            for slot,r in enumerate(picks,1):selected.append(dict(r,pair_slot=slot))
    random.Random(str(SEED)+'|display_order').shuffle(selected)
    ids=random.Random(str(SEED)+'|blind_ids').sample(range(100000,1000000),50)
    for r,n in zip(selected,ids):r['blind_id']=f'K{n}'
    assert len({r['stable_id'] for r in selected})==50
    dump(COORD/'CANDIDATE_POOL_FROZEN.json',pools)
    dump(COORD/'SAMPLE_FROZEN.json',selected)
    dump(COORD/'SAMPLING.json',{'seed':SEED,'python_version':sys.version,'algorithm':'Python random.Random with independent string-seeded streams; sorted IDs and original row order; sample without replacement; single committed draw','common_sources':common,'counts':{a:dict(c) for a,c in counts.items()},'supplement_eligible':eligible,'supplement_selected':supplemental,'total_cards':50,'source_clusters':20,'source_pairs':25,'within_source_pairing':'same source only; not guaranteed same parameter','scope':'conditional numeric-candidate pool; not all 60-source output correctness; exposed known problems not grounds for replacement','draw_utc':now})
    blind=[];diffs=[]
    for r in selected:
        display={f:r['candidate'].get(f) for f in FIELDS}
        blind.append({'blind_id':r['blind_id'],'original_requirement':r['original_requirement'],**display})
        diffs.append({'blind_id':r['blind_id'],'original':r['candidate'],'display':display,'removed_fields':[f for f in r['candidate'] if f not in FIELDS],'technical_fields_exact':all(display[f]==r['candidate'].get(f) for f in FIELDS),'text_rewrites':[],'residual_blinding_risk':'Maker/model/source wording in technical text is intentionally retained; complete blinding not assured'})
    dump(COORD/'DISPLAY_DIFFS.json',diffs)
    dump(HERE/'blind_input.json',blind);dump(HERE/'guide.json',GUIDE)
    protocol={'version':'S3-paired-50-v1','frozen_before_human_labels_utc':now,'not_preregistered_full_experiment':True,'authorization':'Delegated user approval Sentinel_b5d848a9e57c8191b3f0db13e06a362e 2026-10-19T15:55:13Z','classifier':mod.RANGE_CLASSIFIER_VERSION,'numeric_policy':'numeric-ranges-v1','candidate_pool_sha256':sha(COORD/'CANDIDATE_POOL_FROZEN.json'),'sample_sha256':sha(COORD/'SAMPLE_FROZEN.json'),'sampling_sha256':sha(COORD/'SAMPLING.json'),'display_diffs_sha256':sha(COORD/'DISPLAY_DIFFS.json'),'blind_input_sha256':sha(HERE/'blind_input.json'),'reviewer_requirement':'At least one external non-author domain reviewer; coauthor review separately labelled, not independent external validation. No reviewer secured or assessment completed by preparing this package.','target':'Every material numeric commitment in the complete displayed candidate under its stated conditions, not just one matched value. Independent full-document verification for both arms; no retrospective favorable conditions.','reference_limit':'No complete neutral engineering ground truth has been assembled; reviewers may independently consult full sources equally and record unknown. Practice judgments explicitly distinguished from document-grounded judgments.','primary':'source-equal mean of [rag(correct AND applicable)/n_rag - norag(correct AND applicable)/n_norag]; 20 source clusters','secondary':'same with (correct OR acceptable) AND applicable; item fractions secondary only','unknown':'correctness=无法判断 OR applicability=工况不明; preserve independently. If explicit wrong or not applicable, failure is established even when other axis unknown. Remaining unresolved cases create lower/upper bounds; confirmed-success rate uses all sampled rows, not deletion or imputed factual error.','bounds':'RAG-unfavorable: unresolved RAG=0,noRAG=1; favorable reverse. Report both endpoints; not confidence intervals.','ci':'source-cluster percentile bootstrap of paired confirmed-success differences, 10000 resamples with seed 202610191556, 2.5/97.5 percentiles; exploratory conditional stability interval, not population coverage guarantee; only 20 source clusters and all eligible common sources included','test':'only two-sided exact source-level sign test on nonzero primary confirmed-success differences; ties excluded from binomial count but reported; descriptive symmetry/independence assumptions; no outcome-driven test choice; not power or equivalence evidence','agreement':'only two complete first-pass independently filled valid workbooks with distinct identities and declarations: exact agreement and unweighted Cohen kappa for each nominal axis including unknown; external/coauthor identities retained; no consensus ratings. Independence is declared, not externally verified.','acceptance_rules':'Correct/acceptable need a concrete source locator/version or explicit practice-judgment basis; no uniform +/-20%; one key error prevents whole-row correct','blinding':'Only nontechnical metadata omitted; original numeric/unit/operator/qualifier/model/condition preserved exactly. Optional source guessing separate file released only after first-pass submission.','no_outcome':'No real scores exist. Empty/incomplete forms must block all outcome statistics.'}
    dump(COORD/'PROTOCOL_FROZEN.json',protocol)
    esc=html.escape
    cards=[]
    for r in blind:
        parts=[f'<article id="{r["blind_id"]}"><h2>{r["blind_id"]}</h2>']
        for f,l in [('original_requirement','原需求')]+list(zip(FIELDS,LABELS)):
            value=r[f];value='\n'.join(value) if isinstance(value,list) else str(value or '')
            parts.append(f'<h3>{l}</h3><pre>{esc(value)}</pre>')
        parts.append('</article>');cards.append(''.join(parts))
    document='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>S3数值候选独立阅读</title><style>body{max-width:980px;margin:30px auto;padding:0 22px;color:#183047;font:17px/1.7 "Microsoft YaHei",sans-serif}article{border-top:2px solid #b9c8d6;margin-top:40px;padding-top:12px}h1{font-size:28px}h2{font-size:23px}h3{font-size:17px;margin-bottom:4px}pre{white-space:pre-wrap;font:inherit;background:#f2f5f8;padding:14px;margin-top:0}a{color:#244f78}nav{line-height:2.2}</style><h1>S3数值候选独立阅读</h1><p>只读页面，不保存任何评分。请在配套Excel填写。用Ctrl+F查盲ID；正文和适用条件原样保留。先看Excel说明；不要用是否有引用判断对错。</p><nav>'+ ' · '.join(f'<a href="#{r["blind_id"]}">{r["blind_id"]}</a>' for r in blind)+'</nav>'+''.join(cards)+'</html>'
    (EXPERT/'50条原文只读阅读.html').write_text(document,encoding='utf8')
    (EXPERT/'先读我.txt').write_text('先打开《数值候选独立评分.xlsx》的“身份与说明”，再看“评分定义”。\n在“评分50”填写黄色区；原文可在“完整原文”或只读HTML按盲ID查找。HTML不保存答案。\n两位评审各自另存，以评审代号命名。不要覆盖空白模板，不交换首判，不修改原文或结构。所有身份、时间及评分均应由本人填写。\n请独立查完整原文、表头、脚注和适用条件。本包没有完整工程真值。无法确定时可选无法判断/工况不明。不得统一使用±20%。\n先做不入样本的流程校准并记录耗时，再估计工作量。无需重做此前[Q]审核。\n第一阶段提交后才可获取另行提供的可选出处猜测页。\n',encoding='utf8')
    (HERE/'README_交付说明.txt').write_text('本包仅准备S3人评材料，尚无真实评分。\n可发评审：outputs/01a13537-s3/01_仅此目录可发评审，内含评分Excel、原文HTML和先读我。\n02_协调者_勿发评审含组别、等级、原ID、抽样种子、完整来源和解盲键，不要发给评审。\n至少一位外部非作者领域评审尚需落实；共同作者复评身份单列，不冒称外部独立评审。\n抽样为20个共同数值源、每臂25条；补5对来自同样5源。它不是全60源准确率，也不保证配对条目为同参数。\n旧S3、历史实验和最终论文未改动。不因疑点或负温度重抽。\n分析前先核验原文与身份；空表一律阻塞，无真实分数。分析工具只接受完整独立首判；合议表不用于独立一致性。\n统一中立证据包和工程真值尚不完备，评审需同等独立查原件并允许未知。\n实际工时需先做非样本校准，未承诺功效或RAG获胜。\n',encoding='utf8')
    print(json.dumps({'frozen':True,'n':50,'sources':20,'supplement_sources':supplemental,'pool_sizes':{a:len(r) for a,r in pools.items()},'sample_sha256':sha(COORD/'SAMPLE_FROZEN.json')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
