"""Versioned status projection; never creates semantic evidence relationships."""
import json,uuid,xml.etree.ElementTree as ET
from .ea_structure import q,properties
from .ea_presentation import serialize
from .ea_compact import merge_style
from .requirement_status import normalize_status,display_colors,colorref

def status_view(xml,mode='Rule grade',*,batch_id='',source_path=''):
    if isinstance(xml,bytes):xml=xml.decode('utf-8')
    root=ET.fromstring(xml);before=properties(root);content=root.find('XMI.content');states={}
    def put(rid,key,value):
        found=next((t for t in content.findall(q('TaggedValue')) if t.get('modelElement')==rid and t.get('tag')==key),None)
        if found is None:found=ET.SubElement(content,q('TaggedValue'),{'tag':key,'xmi.id':'EAID_'+str(uuid.uuid4()).upper().replace('-','_'),'modelElement':rid})
        found.set('value',str(value))
    for role in root.iter(q('ClassifierRole')):
        rid=role.get('xmi.id');p=before[rid];source='grade' not in p
        record=dict(p)
        if p.get('ui_original_json') and not source:
            record.update(json.loads(p['ui_original_json'].removeprefix('<memo>#NOTES#')));record['grade']=p['grade']
        state=normalize_status(record,source=source);states[rid]=state
        if p.get('rule_grade_origin'):state['rule_grade_origin']=p['rule_grade_origin']
        for key,value in state.items():put(rid,key,value)
        put(rid,'coloring_mode',mode)
        if batch_id:put(rid,'status_batch_id',batch_id)
        if source_path:put(rid,'status_source_path',source_path)
    for diagram in root.iter(q('Diagram')):
        visible=[]
        for obj in diagram.iter(q('DiagramElement')):
            rid=obj.get('subject')
            if rid in states:
                visible.append(rid);bg,border=display_colors(states[rid],mode);obj.set('style',merge_style(obj.get('style',''),{'BCol':colorref(bg),'LCol':colorref(border)}))
        label='Coloring by '+mode+'. '
        if mode=='Rule grade':label+='Grades are criterion/citation rules, not semantic support.'
        else:label+='Reported support is unverified; missing status = Not assessed.'
        keys=sorted({states[r]['rule_grade'] if mode=='Rule grade' else states[r]['evidence_support_label'] for r in visible})
        legend=label+'\n'+', '.join(keys)+'. Nesting = grouping.'
        subjects={o.get('subject') for o in diagram.iter(q('DiagramElement'))}
        for note in root.iter(q('Comment')):
            if note.get('xmi.id') in subjects:
                for t in note.iter(q('TaggedValue')):
                    if t.get('tag')=='documentation':t.set('value',legend)
        hidden=sorted({k for p in properties(root).values() for k in p if k!='id'})
        for t in diagram.iter(q('TaggedValue')):
            if t.get('tag')=='styleex':t.set('value',merge_style(t.get('value',''),{'SUPTAG':','.join(hidden),'ShowNotes':0,'ShowTags':1}))
    return serialize(root)
