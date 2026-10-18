"""Explicit review flags: isolate evidence before prompting and gate delivery.

No factual KB edits, semantic verification, numeric-source inference or API calls.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re

VERSION = 'evidence-quarantine-v1'
PROMPT_RULE = ('\nEvidence marked QUARANTINED is background-only, never a numeric basis. '
               'Do not recover its withheld values from memory or other fields. Use TBD for unsupported '
               'criteria. A matching number is not source attribution. Missing parameter bindings and '
               'applicability remain unknown. Review flags do not verify any unflagged evidence.\n')


def active_flags(flags: list[dict] | None) -> dict[str, dict]:
    if flags is None:
        return {}
    if not isinstance(flags, list):
        raise ValueError('review flags must be a list')
    indexed = {}
    for flag in flags:
        if not isinstance(flag, dict):
            raise ValueError('review flag must be an object')
        for key in ('review_id', 'evidence_id', 'reason', 'verification_scope'):
            if not isinstance(flag.get(key), str) or not flag[key].strip():
                raise ValueError('missing review flag field: '+key)
        if flag.get('status') not in ('quarantined', 'released'):
            raise ValueError('unknown review status')
        eid = flag['evidence_id']
        if eid in indexed:
            raise ValueError('duplicate review flag for evidence: '+eid)
        indexed[eid] = copy.deepcopy(flag)
    return {eid:flag for eid,flag in indexed.items() if flag['status']=='quarantined'}


def load_review_flags(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != VERSION:
        raise ValueError('unsupported review registry version')
    flags = data.get('flags')
    active_flags(flags)
    if flags is None:
        raise ValueError('registry requires flags')
    return flags


def mask_prompt_evidence(value, flags: list[dict] | None):
    """Replace whole flagged evidence records, including all duplicate UI groups.

    Never retain a second copy of values in summaries, parameters or metadata.
    The external registry retains the provenance; the prompt gets a safe stub.
    """
    indexed = active_flags(flags)
    if not indexed:
        return value
    def visit(node):
        if isinstance(node, list):
            return [visit(v) for v in node]
        if isinstance(node, dict):
            eid = next((node.get(k) for k in ('id','evidence_id','kb_id')
                        if isinstance(node.get(k),str) and node[k] in indexed), None)
            if eid:
                return {'id':eid, 'text':'QUARANTINED: numeric evidence withheld; background warning only; use TBD.',
                    'source_document':'quarantined source; consult the external review registry',
                    '_extracted_values':[], '_has_quantitative':False,
                    '_extraction_status':'quarantined_not_numeric_support',
                    '_context_status':'quarantined_unknown',
                    '_quarantine_review_id':indexed[eid]['review_id']}
            return {k:visit(v) for k,v in node.items()}
        return node
    return visit(value)


def _reported_ids(row: dict) -> tuple[list[str], list[str], bool]:
    citations = row.get('evidence_citations')
    ids = [c.get('kb_id') for c in citations if isinstance(c,dict) and isinstance(c.get('kb_id'),str)] if isinstance(citations,list) else []
    # Union all citation channels: a model-supplied extra schema field must not
    # hide a flagged ID in another channel or one removed by normalization.
    for key in ('_reported_evidence_ids','evidence_ids'):
        raw = row.get(key,[])
        if isinstance(raw,str):
            raw = [raw]
        ids.extend(i for i in (raw if isinstance(raw,list) else []) if isinstance(i,str) and i)
    bindings = row.get('parameter_bindings', [])
    valid = isinstance(bindings,list) and bool(bindings)
    bound = []
    for binding in bindings if isinstance(bindings,list) else []:
        if isinstance(binding,dict) and isinstance(binding.get('evidence_id'),str):
            bound.append(binding['evidence_id'])
        if not isinstance(binding,dict) or any(not isinstance(binding.get(k),str) or not binding[k].strip()
                                              for k in ('evidence_id','parameter_id','claim_field')):
            valid = False
            continue
    # Even a well-shaped model-declared binding is NOT independently verified.
    return list(dict.fromkeys(ids)), list(dict.fromkeys(bound)), valid


def gate_delivery(rows: list[dict], flags: list[dict] | None, *, report: dict | None = None, evidence_scope: list[dict] | None = None) -> list[dict]:
    """Return the canonical delivery list, with flagged/unattributed rows withheld.

    Mixed flagged/healthy citations cannot be disambiguated by equal numbers.
    Conservatively withhold the whole row; bindings can reveal additional flagged
    IDs, but cannot override a flagged citation or establish semantic support.
    """
    indexed = active_flags(flags)
    if not indexed:
        return rows
    result, withheld = [], []
    allowed = {e.get('id') for e in evidence_scope or []}
    for position,row in enumerate(rows,1):
        ids,bound_ids,binding_shape = _reported_ids(row)
        current_ids,_,_ = _reported_ids({k:v for k,v in row.items() if k!='_reported_evidence_ids'})
        usable_ids = current_ids if evidence_scope is None else [i for i in current_ids if i in allowed]
        implicated = [eid for eid in dict.fromkeys(ids+bound_ids) if eid in indexed]
        text = '\n'.join(str(row.get(k,'')) for k in ('shall_statement','measurable_criterion','acceptance_criteria'))
        # Remove placeholders before the conservative digit detector. Digits only
        # identify possible numeric content, never which source supplied it.
        text = re.sub(r'\{\{?TBD[^}]*\}\}?', '', text, flags=re.I)
        numeric = bool(re.search(r'\d',text))
        provenance = 'declared_binding_unverified' if binding_shape else 'unknown_missing_or_invalid_binding'
        reason = 'flagged_reference_or_declared_binding' if implicated else 'numeric_content_without_in_scope_citation' if numeric and not usable_ids else None
        diagnostic = {'version':VERSION, 'flagged_ids':implicated, 'reported_citation_ids':ids,
            'declared_binding_ids':bound_ids, 'numeric_provenance':provenance, 'semantic_support':'unknown',
            'applicability':'unknown', 'numeric_content_detected':numeric,
            'reference_scope':'unknown' if evidence_scope is None else 'supplied_context',
            'out_of_scope_ids':[] if evidence_scope is None else [i for i in current_ids if i not in allowed],
            'source_attribution':'not_inferred_from_matching_numbers'}
        if reason:
            withheld.append({'position':position,'row_id':row.get('id'),
                'status':'blocked_numeric' if numeric and implicated else 'needs_review',
                'reason':reason,'review_ids':[indexed[eid]['review_id'] for eid in implicated],
                'diagnostic':diagnostic,'original_row':copy.deepcopy(row)})
        else:
            kept = copy.deepcopy(row)
            kept['_quarantine_check'] = {**diagnostic,'status':'no_known_flag_not_verified'}
            if kept.get('support_status')=='verified_by_direct_evidence':
                kept.setdefault('_reported_support_status',kept['support_status'])
                kept['support_status']='need_confirmation'
            result.append(kept)
    if report is not None:
        report.update({'version':VERSION,'enabled':True,'active_review_ids':[f['review_id'] for f in indexed.values()],
            'input_rows':len(rows),'delivery_rows':len(result),'withheld':withheld,
            'background_warnings':[{'evidence_id':eid,'review_id':f['review_id'],
                'status':'quarantined','instruction':'Use TBD; not a numeric basis. See external review provenance.'}
                for eid,f in indexed.items()]})
    return result


def gate_ui_output(output: dict, flags: list[dict] | None, *, evidence_scope: list[dict] | None = None) -> dict:
    if not active_flags(flags):
        return output
    obj = copy.deepcopy(output)
    report = {}
    kept = gate_delivery(obj.get('engineering_requirements',[]),flags,report=report,evidence_scope=evidence_scope)
    removed = {r['row_id'] for r in report['withheld'] if r.get('row_id')}
    # Do not silently reparent children or keep dangling hierarchy/relationships.
    while True:
        descendants = [r for r in kept if r.get('parent_id') in removed]
        if not descendants:
            break
        for row in descendants:
            report['withheld'].append({'row_id':row.get('id'),'status':'needs_review',
                'reason':'ancestor_withheld','original_row':copy.deepcopy(row)})
            if row.get('id'):
                removed.add(row['id'])
        kept = [r for r in kept if r not in descendants]
    relationships = obj.get('relationships',[])
    dropped = [r for r in relationships if any(isinstance(v,str) and v in removed for v in r.values())]
    obj['relationships'] = [r for r in relationships if r not in dropped]
    report['withheld_relationships'] = dropped
    report['delivery_rows'] = len(kept)
    obj['engineering_requirements'] = kept
    obj['_quarantine_delivery'] = report
    obj['_delivery_status'] = 'needs_review' if report['withheld'] else 'no_known_flag_not_verified'
    if report['withheld']:
        # Model-written summaries can repeat a withheld threshold. Keep them in
        # the audit channel, not in the ordinary delivery summary/notes.
        report['withheld_context_fields'] = {k:obj.get(k) for k in
            ('professional_summary','assumptions','confirmation_items','evidence_gaps') if k in obj}
        obj['professional_summary'] = 'Quarantined evidence requires review. Withheld criteria are TBD and are not delivery requirements.'
        for key in ('assumptions','confirmation_items','evidence_gaps'):
            obj[key] = []
    return obj
