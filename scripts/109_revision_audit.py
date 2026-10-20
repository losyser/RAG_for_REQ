"""Offline reproducible audit; does not invoke API clients or modify historical outputs."""
import argparse, csv, hashlib, importlib.util, json, sys
from pathlib import Path
from collections import Counter, defaultdict
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from cooling_rag_mg.grade_classifier import classify_grade
from cooling_rag_mg.review_routing import derivation_assessment, review_route, conflict_flag
from cooling_rag_mg.revision_audit import strict_numeric_label, validate_expert_rows, validate_prediction_pool, successful_variant
E=ROOT/'data/search_results/exp_v4'
ARMS={'rag':'rag_v4_results.json','norag':'norag_v4_results.json','random':'ablation_random_retrieval_results.json','rag_qwen':'rag_v4_qwen_results.json','norag_qwen':'norag_v4_qwen_results.json'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_script(name):
    spec=importlib.util.spec_from_file_location('audit_'+name,ROOT/'scripts'/name)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    def write(n,v): (out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    from cooling_rag_mg.revision_audit import verify_frozen_arm_inputs
    baseline_path=out/'baseline_manifest.json'
    if not baseline_path.is_file():
        raise ValueError('Independent audit directory must contain the verified baseline_manifest.json')
    source_errors=verify_frozen_arm_inputs(ROOT,ARMS,read(baseline_path))
    if source_errors: raise ValueError('; '.join(source_errors))
    kb={u['id']:u for u in map(json.loads,(ROOT/'data/processed/evidence_units_v3_audited.jsonl').read_text(encoding='utf-8').splitlines())}
    pn=load_script('100_paper_numbers.py'); old=read(E/'paper_numbers.json'); historical=read(E/'routing_report.json')
    routes={}; consistency={}; fingerprints=defaultdict(list); statements={}
    for arm,fn in ARMS.items():
        p=E/fn; data=read(p); rows=[]; ids=[]; texts={}
        for rs in data['result_sets']:
            sid=rs['source_requirement_id']; ids.append(sid)
            for k,er in enumerate(rs.get('engineering_requirements',[]),1):
                g=classify_grade(er.get('measurable_criterion'),er.get('evidence_citations',[]),kb)
                e=dict(er,_grade=g); d=derivation_assessment(e,kb); route,reason=review_route(e,kb,rs.get('_evidence_values') or {})
                stmt=er.get('shall_statement',''); crit=er.get('measurable_criterion') or ''
                combined=f'{stmt}（测量判据：{crit}）' if crit else stmt
                texts.setdefault((sid,combined),[]).append(f'{sid}.{k}')
                rows.append({'arm':arm,'id':f'{sid}.{k}','source_id':sid,'stored_grade':er.get('_grade'),'grade_v2':g,'criterion':crit,'assessment':d,'route':route,'route_reason':reason,'conflict':conflict_flag(e,kb,rs.get('_evidence_values') or {})})
        counts=Counter(r['route'] for r in rows); deriv=Counter(r['assessment']['legacy_type'] for r in rows)
        grades=Counter(r['grade_v2'] for r in rows)
        assert sum(counts.values())==sum(deriv.values())==sum(grades.values())==len(rows)
        if len(ids)!=len(set(ids)): raise ValueError(arm+': duplicate sources')
        fingerprint=sha(p); fingerprints[fingerprint].append(arm)
        routes[arm]={'source_file':fn,'sha256':fingerprint,'source_arm_label':data.get('arm'),'set_arm_labels':dict(Counter(str(r.get('_arm')) for r in data['result_sets'])),'n_sets':len(ids),'denominator_all_requirements':len(rows),'routes':dict(counts),'legacy_derivation_categories':dict(deriv),'classification_v2':dict(Counter(r['assessment']['classification'] for r in rows)),'grades_v2':dict(grades),'unknown_grades':sum(r['stored_grade'] not in 'ABCX' if isinstance(r['stored_grade'],str) else True for r in rows),'rows':rows}
        summary=json.loads(json.dumps(pn.grade_summary(data,kb)))
        consistency[arm]={'actual':summary,'historical_registry':old.get(arm),'differences':{k:{'historical':old.get(arm,{}).get(k),'recomputed_v2':v} for k,v in summary.items() if old.get(arm,{}).get(k)!=v},'historical_routing_total':sum(historical.get(arm,{}).get('routes',{}).values()) if arm in historical else None,'stored_grade_mismatches':sum(r['stored_grade']!=r['grade_v2'] for r in rows)}
        statements[arm]=texts
    duplicate_files=[v for v in fingerprints.values() if len(v)>1]
    write('routing_v2.json',{'version':'routing-v2','definition':'Token matches and rule candidates only; no semantic or mathematical verification','cross_arm_identical_files':duplicate_files,'arms':routes})
    write('registry_comparison.json',consistency)
    post=read(E/'norag_kb_verification.json'); details=[]
    for i,r in enumerate(post['details']):
        arm={'rag_v3':'rag','no_rag':'norag'}.get(r['arm'])
        if arm is None: raise ValueError('Unknown posthoc arm '+r['arm'])
        matches=statements[arm].get((r['sid'],r['stmt']),[])
        label=strict_numeric_label(r['verdicts'],r.get('llm_raw',''))
        details.append({'row':i,'arm':arm,'source_id':r['sid'],'matching_final_ids':matches,'legacy_label':r['label'],'strict_reported_label':label,'strict_complete_sentence_support':'not_established_without_extraction_coverage_validation','reported_numeric_verdicts':{k:len(v) for k,v in r['verdicts'].items()},'raw':r.get('llm_raw'),'numbers':r.get('numbers')})
    poststats={}
    for arm in ('rag','norag'):
        rs=[r for r in details if r['arm']==arm]; ns=Counter()
        for r in rs: ns.update(r['reported_numeric_verdicts'])
        poststats[arm]={'selected_sentence_denominator':len(rs),'legacy_labels':dict(Counter(r['legacy_label'] for r in rs)),'strict_reported_labels':dict(Counter(r['strict_reported_label'] for r in rs)),'numeric_verdict_denominator':sum(ns.values()),'numeric_verdict_counts':dict(ns),'unmatched_to_final':sum(not r['matching_final_ids'] for r in rs),'ambiguous_final_matches':sum(len(r['matching_final_ids'])>1 for r in rs)}
    write('posthoc_v2.json',{'version':'strict-reported-v2','source_sha256':sha(E/'norag_kb_verification.json'),'legacy_summary':post['summary'],'summary':poststats,'rows':details})
    cred=read(E/'credibility_v4/eval_v3.json'); h=cred['h_hard']; hh={}
    for arm in ('rag','no-rag'):
        rs=[r for r in h['per_claim_rows'] if r['_arm']==arm]; c=Counter(r['verdict'] for r in rs)
        hh[arm]={'claim_denominator':len(rs),'counts':dict(c),'unknown_verdicts':sum(n for v,n in c.items() if v not in ('support','contradict','not_found')),'micro_contradiction_rate':c['contradict']/len(rs) if rs else None,'source_denominators':dict(Counter(r['source_requirement_id'] for r in rs))}
    write('hhard_audit.json',{'unit':'LLM-extracted claim from shall_statement only; measurable_criterion excluded by script59','legacy_macro_paired_test':h['wilcoxon'],'micro_separately_recomputed':hh,'limitation':'Historical not_found conflates API/parse failure with absent evidence; raw passage and failure status were not retained. Cannot recover these distinctions offline.','blind_quality_unchanged':cred['blind_quality']['aggregate']})
    from openpyxl import load_workbook
    scorer=load_script('98_score_expert_workbook.py'); wb=load_workbook(ROOT/'data/expert_round2/expert_workbook.xlsx',read_only=True)
    key=read(ROOT/'data/expert_round2/expert_key.json'); sheets={k:scorer._sheet(wb,n) for k,n in [('S1','S1_tagging'),('S2','S2_pairs'),('S3','S3_values'),('S4','S4_extraction')]}
    preds=read(E/'e1_predictions.json'); errors=validate_expert_rows(sheets,key); poolerrors=validate_prediction_pool(preds,key['S2'])
    # Check S3 sample remains tied to the current arm by exact statement+criterion.
    sample=[]
    for r in sheets['S3']:
        k=key['S3'][str(r['item'])]; arm={'RAG':'rag','no-RAG':'norag'}[k['arm']]
        stmt=r['shall_statement']; crit=r.get('measurable_criterion') or ''; combined=f'{stmt}（测量判据：{crit}）' if crit else stmt
        sample.append({'item':r['item'],**k,'matching_final_ids':statements[arm].get((k['sid'],combined),[])})
    write('expert_readiness_PRIVATE.json',{'counts':{k:len(v) for k,v in sheets.items()},'scoring_blocked':bool(errors or poolerrors),'annotation_errors':errors,'prediction_pool_errors':poolerrors,'S3_sample_matches':sample,'S3_arm_counts':dict(Counter(r['arm'] for r in sample)),'scores':None})
    # Public packet includes no key or arm mapping and never changes the workbook.
    public=out/'expert_packet'; public.mkdir(exist_ok=True)
    import shutil
    shutil.copyfile(ROOT/'data/expert_round2/expert_workbook.xlsx',public/'expert_workbook.xlsx')
    with (public/'sample_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['section','item','row_content_sha256'])
        for section,rs in sheets.items():
            for r in rs: w.writerow([section,r['item'],hashlib.sha256(json.dumps({str(k):v for k,v in r.items()},ensure_ascii=False,sort_keys=True).encode()).hexdigest()])
    sens=read(E/'sensitivity/summary.json'); variants={}
    for v in sens['e2e']:
        p=E/'rag_v4_results.json' if v=='default' else E/'sensitivity'/f'{v}_results.json'
        d=read(p); ok,reasons=successful_variant(d)
        expected=set(statements['rag']); source_ids={rs['source_requirement_id'] for rs in d['result_sets']}
        coverage=source_ids=={r['source_id'] for r in routes['rag']['rows']}
        variants[v]={'sha256':sha(p),'accepted':ok and coverage,'reasons':reasons,'source_coverage_complete':coverage,'actual_summary_v2':pn.grade_summary(d,kb),'historical_summary':sens['e2e'][v]}
    write('sensitivity_audit.json',{'boundary_scope':'25 condition-numeric sentences; boundary analysis only, not end-to-end window/overlap experiment','rrf_k0':'rank-fusion smoothing constant, not candidate pool size','boundary':sens['boundary'],'variants':variants,'failed_trunc_1200_in_summary':'trunc_1200' in sens['e2e'],'historical_failed_artifact':'absent at baseline; prior ledger documents HTTP402 deletion; no reconstructed result','historical_tokens_and_memory':'unknown unless explicit run record; no inferred settings'})
    print(json.dumps({'arms':{k:v['denominator_all_requirements'] for k,v in routes.items()},'posthoc':poststats,'expert_annotation_errors':len(errors),'prediction_pool_errors':poolerrors,'registry_differences':{k:v['differences'] for k,v in consistency.items()}},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
