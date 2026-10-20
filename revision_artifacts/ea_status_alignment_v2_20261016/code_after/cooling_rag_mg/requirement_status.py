"""Shared UI/EA display semantics. Reported support is never verification."""
import copy
from .grade_classifier import classify_grade

RULE_COLORS={'source':('#E8E8E8','#6E6E6E'),'A':('#C8FFC8','#228B22'),'B':('#D2E6FF','#0066CC'),'C':('#FFF5D2','#CC6600'),'X':('#FFD2D2','#B40000'),'unknown':('#F1F3F5','#868E96')}
SUPPORT={
 'reported_direct':('Reported direct (unverified)','#D8F0EC','#247A6B'),
 'reported_indirect':('Reported indirect (unverified)','#FFF3CD','#9C7400'),
 'evidence_gap':('Reported evidence gap','#FDE2E2','#B54A4A'),
 'needs_review':('Reported need for confirmation','#E8E1FA','#7655A3'),
 'not_assessed':('Not assessed','#F1F3F5','#868E96'),
 'source':('Source requirement','#E8E8E8','#6E6E6E'),
}
ALIASES={'verified_by_direct_evidence':'reported_direct','supported_by_indirect_evidence':'reported_indirect','evidence_gap':'evidence_gap','need_confirmation':'needs_review'}
def normalize_status(record, kb=None, *, source=False):
    raw=record.get('support_status')
    support='source' if source else ALIASES.get(raw,'not_assessed')
    grade='source' if source else next((record[k] for k in ('rule_grade','grade','_grade') if record.get(k) in ('A','B','C','X')),None)
    grade_origin='source' if source else 'preserved' if grade else 'computed_display_only'
    if grade is None:
        criterion=record.get('measurable_criterion',record.get('criterion','; '.join(map(str,record.get('acceptance_criteria') or []))))
        cites=record.get('evidence_citations',[{'kb_id':x} for x in record.get('evidence_ids',[])])
        grade=classify_grade(criterion,cites,kb) if kb is not None else 'unknown'
    return {'rule_grade':grade,'rule_grade_origin':grade_origin,'reported_support_status':raw or '',
            'evidence_support_state':support,'evidence_support_label':SUPPORT[support][0],
            'support_assessment_provenance':'source' if source else 'reported_unverified' if raw in ALIASES else 'not_assessed',
            'semantic_verification_state':'not_assessed',
            'verification_note':'No independent signed review is attached; model claims and legacy Direct are not verification.'}
def display_colors(state,mode):
    if mode not in ('Rule grade','Evidence support'):raise ValueError('Unknown coloring mode')
    return RULE_COLORS.get(state['rule_grade'],RULE_COLORS['unknown']) if mode=='Rule grade' else SUPPORT[state['evidence_support_state']][1:]
def colorref(hex_color):
    r,g,b=(int(hex_color[i:i+2],16) for i in (1,3,5));return r+256*g+65536*b
def display_payload(payload,kb,mode):
    result=copy.deepcopy(payload)
    for s in result.get('requirement_sets',[]):
        for e in s.get('engineering_requirements',[]):e['_display_state']=normalize_status(e,kb);e['_color_mode']=mode
    return result
