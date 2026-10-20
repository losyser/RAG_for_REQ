"""Opt-in offline q-format-v2 diagnostics; NEVER assigns legacy A/B or semantic support."""
import re
VERSION = 'q-format-v2-20261019'
TBD = re.compile(r'\{\{?\s*TBD\s*\||\bTBD\b|无法确定|待确定', re.I)
UNKNOWN = re.compile(r'未知|未记录|未确定|不明确|unknown', re.I)
NUMBER = re.compile(r'\d+(?:\.\d+)?\s*(?:°C|℃|°F|MPa|kPa|bar|%|ppm|dGH|mg/L|L/min|mm|kW|rpm|秒|小时)',re.I)

def classify(row, kb_ids, selected_ids, *, evidence_required=True):
    if not isinstance(row,dict):
        return {'version':VERSION,'class':'invalid_row','q_format':'not_applicable','semantic_support':'not_assessed','applicability':'not_assessed'}
    raw=row.get('measurable_criterion'); text=raw.strip() if isinstance(raw,str) else ''
    q_candidate='[Q]' in text; prefix=text.startswith('[Q]')
    condition=row.get('applicable_condition')
    cond=condition.strip() if isinstance(condition,str) else ''
    cites=row.get('evidence_citations'); errors=[]
    if q_candidate:
        if not prefix: errors.append('prefix_not_at_start')
        if prefix and not text[3:].strip(): errors.append('empty_q_body')
        if TBD.search(text): errors.append('mixed_q_tbd')
        if not cond: errors.append('condition_missing')
        if not isinstance(cites,list) or not cites: errors.append('citations_missing_or_invalid')
        else:
            for c in cites:
                if not isinstance(c,dict) or not isinstance(c.get('kb_id'),str): errors.append('invalid_citation_schema')
                elif c['kb_id'] not in kb_ids: errors.append('citation_not_in_kb')
                elif c['kb_id'] not in selected_ids: errors.append('citation_not_in_context')
        if evidence_required and not selected_ids: errors.append('empty_context_requires_tbd')
        kind='q_candidate'
    elif TBD.search(text): kind='tbd_or_mixed_candidate'
    elif NUMBER.search(text): kind='numeric_candidate'
    elif text: kind='unmarked_nonnumeric_candidate'
    else: kind='missing_criterion'
    return {'version':VERSION,'class':kind,'q_format':('fail' if errors else 'pass') if q_candidate else 'not_applicable',
            'format_errors':sorted(set(errors)),'semantic_support':'not_assessed',
            'applicability':'unknown' if not cond or UNKNOWN.search(cond) else 'not_assessed',
            'requires_semantic_checks':['verifiability','faithful_quote_or_paraphrase','no_new_inference_or_synthesis','object_parameter_operator_scope_alignment','source_reliability_separate'],
            'legacy_grade_action':'unchanged_not_promoted'}
