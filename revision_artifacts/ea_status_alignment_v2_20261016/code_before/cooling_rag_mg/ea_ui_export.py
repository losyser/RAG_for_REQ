"""Offline EA-native adapter for the UI payload; original IDs and data retained."""
import copy, importlib.util, json
from functools import lru_cache
from pathlib import Path
import xml.etree.ElementTree as ET
from .ea_presentation import presentation_xml,fresh_ids,serialize
from .ea_structure import properties,q

@lru_cache(maxsize=1)
def native_exporter():
    path=Path(__file__).resolve().parents[1]/'scripts/92_export_ea_native_xmi.py'
    spec=importlib.util.spec_from_file_location('_cooling_native_ea',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def load_kb(path):
    records=[json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    return {r.get('kb_id',r.get('evidence_id',r.get('id'))):r for r in records if r.get('kb_id',r.get('evidence_id',r.get('id')))}

def export_ea_payload_bytes(payload, *, source_requirements, kb_index, expanded=False):
    """Preserve the whole input as JSON tags; native relationships follow parent_id.
    A/B/C/X is recomputed from criteria/citations with the configured KB, never from
    support_status, quality-gate score or confidence. UI acceptance_criteria is the
    explicit adapter input when measurable_criterion is absent.
    """
    ea=native_exporter();sets=copy.deepcopy(payload.get('requirement_sets') or [])
    sources={str(r['requirement_id']):r for r in source_requirements}
    titles={};identities={};raw={};parents={};all_ids=set()
    for rs in sets:
        sid=str(rs['source_requirement_id']);source=sources.get(sid)
        if not source or not source.get('requirement_text'):raise ValueError('Missing original source text: '+sid)
        if sid in all_ids:raise ValueError('Duplicate source/requirement ID: '+sid)
        all_ids.add(sid);rs['_source_text']=source['requirement_text'];norm=sid if sid.startswith('OR') else 'OR'+sid
        identities[norm]=sid;raw[sid]={'source':source,'requirement_set':copy.deepcopy(rs)}
        titles['S_'+sid]=source.get('topic') or source.get('requirement_name') or source['requirement_text']
        for k,er in enumerate(rs.get('engineering_requirements',[]),1):
            rid=str(er.get('id') or '')
            if not rid or rid in all_ids:raise ValueError('Missing or duplicate requirement ID: '+rid)
            all_ids.add(rid);identities[f'{norm}.{k}']=rid;raw[rid]=copy.deepcopy(er)
            parent=str(er.get('parent_id') or sid)
            parents[rid]=sid if parent == str(rs.get('requirement_set_id') or sid) else parent
            if not er.get('topic'):raise ValueError('Missing requirement title: '+rid)
            titles[f'E_{sid}_{k}']=er['topic']
            er['measurable_criterion']=er.get('measurable_criterion','; '.join(map(str,er.get('acceptance_criteria') or [])))
            er['evidence_citations']=er.get('evidence_citations',[{'kb_id':x} for x in er.get('evidence_ids') or []])
    for rid,parent in parents.items():
        if parent not in all_ids:raise ValueError('Unknown parent: '+parent)
    xml=ea.build_xmi(sets,kb_index,titles,{},per_row=max(12,len(all_ids)))
    root=ET.fromstring(xml);props=properties(root);content=root.find('XMI.content');roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))}
    bybiz={identities[p['id']]:r for r,p in props.items() if r in roles}
    for tv in content:
        if tv.tag==q('TaggedValue') and tv.get('tag')=='id':tv.set('value',identities[tv.get('value')])
    def tag(key,value,rid):
        ET.SubElement(content,q('TaggedValue'),{'tag':key,'value':value,'modelElement':rid,'xmi.id':ea.new_guid()[0]})
    for biz,rid in bybiz.items():
        text = raw[biz]['shall_statement'] if biz in parents else raw[biz]['source']['requirement_text']
        for tv in content:
            if tv.tag == q('TaggedValue') and tv.get('modelElement') == rid and tv.get('tag') == 'text': tv.set('value', '<memo>#NOTES#' + text)
        tag('ui_original_json','<memo>#NOTES#'+json.dumps(raw[biz],ensure_ascii=False),rid)
        if biz in parents:
            tag('grade_input_mapping','measurable_criterion, else joined acceptance_criteria; evidence_citations, else evidence_ids',rid)
            tag('support_status',str(raw[biz].get('support_status','')),rid)
            if 'confidence' in raw[biz]: tag('reported_confidence',str(raw[biz]['confidence']),rid)
    # Preserve package-wide relationships/gaps/assumptions/confidence without loss.
    first=next(iter(bybiz.values()));tag('ui_payload_json','<memo>#NOTES#'+json.dumps(payload,ensure_ascii=False),first)
    duids={n.get('subject'):__import__('re').search(r'DUID=([^;]+)',n.get('style','')).group(1) for n in root.iter(q('DiagramElement')) if n.get('subject') in roles}
    for edge in root.iter(q('Association')):
        ends=list(edge.iter(q('AssociationEnd')));child=ends[1].get('type');biz=next(k for k,v in bybiz.items() if v==child);parent=bybiz[parents[biz]];ends[0].set('type',parent)
        for tv in edge.iter(q('TaggedValue')):
            if tv.get('tag')=='ea_sourceName':tv.set('value',roles[parent].get('name'))
        for n in root.iter(q('DiagramElement')):
            if n.get('subject')==edge.get('xmi.id'):
                n.set('style',__import__('re').sub(r'SOID=[^;]+;',f'SOID={duids[parent]};',n.get('style')))
    result=presentation_xml(serialize(root),ea.GRADE_STYLE,expanded_ids='all' if expanded else (),name='REQ_UI_Expanded' if expanded else 'REQ_UI_Folded')
    result,_=fresh_ids(result)
    return result.encode('utf-8')
