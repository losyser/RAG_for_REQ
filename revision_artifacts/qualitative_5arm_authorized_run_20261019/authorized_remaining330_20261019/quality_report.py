"""Offline dimension-wise labels and coverage, without reinterpreting model labels."""
import json
from collections import Counter
from pathlib import Path
import resume330 as resume
t=resume.t
HERE=Path(__file__).resolve().parent
ENUMS={
    'format_judgment':{'pass','fail','uncertain'},
    'verifiability':{'verifiable','not_verifiable','uncertain'},
    'faithfulness':{'quote','faithful_paraphrase','new_inference_or_synthesis','unsupported','uncertain'},
    'support':{'direct','partial','contradicted','insufficient','uncertain'},
    'applicability':{'explicit_match','explicit_mismatch','unknown','general_rule_with_basis'},
    'source_reliability':{'supported','questionable','unknown'},
}

def summarize(records,generation):
    groups={};enum_issues=[];identity_issues=[]
    for r in records:
        if r['review_status']!='completed':continue
        j=r['machine_judgment']
        if j.get('review_id')!=r['review_id']:identity_issues.append(r['review_id'])
        for field,allowed in ENUMS.items():
            if j.get(field) not in allowed:enum_issues.append({'review_id':r['review_id'],'field':field,'value':j.get(field)})
    for group in ['semantic_old','semantic_new','random_old','random_new','norag_original']:
        candidates=[r for r in records if r['group']==group];done=[r for r in candidates if r['review_status']=='completed']
        groups[group]={
            'generation_counts':generation[group],
            'Q_candidates':len(candidates),'valid_response_count':len(done),'missing_valid_response_count':len(candidates)-len(done),
            'machine_label_counts':{field:dict(Counter(r['machine_judgment'].get(field,'missing') for r in done)) for field in ENUMS},
            'anchor_quality_counts':dict(Counter(r['anchor_quality']['status'] for r in done)),
            'direct_support_with_unknown_applicability':sum(r['machine_judgment'].get('support')=='direct' and r['machine_judgment'].get('applicability')=='unknown' for r in done),
            'direct_support_with_failed_anchor_check':sum(r['machine_judgment'].get('support')=='direct' and r['anchor_quality']['status']=='fail' for r in done),
            'no_Q_review_candidates':not candidates,
        }
    return {'groups':groups,'enum_issues':enum_issues,'identity_issues':identity_issues,'interpretation':'All machine labels retained verbatim. Anchor checks and applicability are independent flags, never overrides. Missing judgments are not uncertain/insufficient labels. Zero Q candidates in old/noRAG groups is not zero semantic quality. No human judgments inferred.'}

def main():
    out=HERE/'terminal_results'
    records=t.read(out/'REVIEW_DIAGNOSTICS_441.json')
    report=summarize(records,t.read(resume.WORK/'RESULT_SUMMARY.json')['groups'])
    # Verify saved parsed labels against the actual raw JSON response for every success.
    mismatches=[]
    for r in records:
        if r['review_status']!='completed':continue
        raw=t.read(resume.WORK/r['response_file'])
        if json.loads(raw['response']['choices'][0]['message']['content'])!=r['machine_judgment']:mismatches.append(r['review_id'])
    report['raw_json_to_saved_label_mismatches']=mismatches
    assert not mismatches and not report['identity_issues']
    t.exclusive(out/'ALL_GROUPS_LABELS_AND_QUALITY.json',report)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
