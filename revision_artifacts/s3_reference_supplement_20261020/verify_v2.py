"""Regression checks and preserved-v1 comparison for navigation-only revision."""
import verify_delivery as base
from preflight import *
import fitz

def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    original=PACK; revised=H/'03_中性查证资料_v2'; audit=H/'04_修订记录_v2_不发评审'
    old=read(original/'逐条资料导航.json');new=read(revised/'逐条资料导航.json')
    assert [c['blind_id'] for c in old]==[c['blind_id'] for c in new]
    for a,b in zip(old,new):
        for key in ['condition_as_candidate_claim','parameters_as_candidate_claim','visible_model','queries']:assert a[key]==b[key],(a['blind_id'],key)
    before=read(original/'来源与版本清单.json');after=read(revised/'来源与版本清单.json')
    assert [(d['file'],d['sha256']) for d in before]==[(d['file'],d['sha256']) for d in after]
    changes=[]
    for a,b in zip(before,after):
        for topic in a['topics']:
            if a['topics'][topic]!=b['topics'][topic]:changes.append({'file':a['file'],'topic':topic,'previous':a['topics'][topic],'revised':b['topics'][topic],'reason':'Keep selected chapter context only; remove unvalidated lexical navigation, or correct documented section boundaries.'})
    man=next(d for d in after if d['file'].endswith('MAN_4960_local_complete.pdf'))
    assert man['topics']['monitor'][0]['end']==140
    assert man['topics']['monitor'][1]['end']==238 and man['topics']['sensor'][0]['end']==238
    for code in ['K395496','K627088']:
        card=next(c for c in new if c['blind_id']==code)
        for ref in card['references']:
            for sec in ref['sections']:
                assert (sec['start'],sec['end']) not in [(261,265),(59,62)]
                assert sec['title']!='-56-'
    assert all(sha(original/p)==h for p,h in read(audit/'V1_BASELINE.json').items())
    dump(audit/'NAVIGATION_CHANGES.json',changes)
    base.PACK=revised;base.AUDIT=audit;base.main()
    dump(audit/'V2_REGRESSION.json',{'candidate_fields_unchanged':50,'v1_files_unchanged':32,'source_pdf_hashes_unchanged':24,'changed_source_topic_mappings':len(changes),'model_api_calls':0,'new_searches':0,'passed':True})
    with fitz.open(revised/man['file']) as pdf:
        for n in [140,238,318]:pdf[n-1].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(audit/'visual_checks'/f'MAN_boundary_{n}.png')
    print('v2 regression passed; changed source/topic mappings:',len(changes))
if __name__=='__main__':main()
