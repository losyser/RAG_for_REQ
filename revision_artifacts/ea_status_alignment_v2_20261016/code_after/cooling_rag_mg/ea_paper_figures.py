"""Offline English EA presentation packages with lossless source provenance."""
import hashlib
import io
import json
import re
import uuid
import zipfile
import xml.etree.ElementTree as ET
from .ea_structure import q, properties
from .ea_presentation import presentation_xml, fresh_ids, serialize
from .ea_ui_export import native_exporter

def mapping_template(xml):
    root=ET.fromstring(xml); props=properties(root)
    rows={props[e.get('xmi.id')]['id']: {
        'original_name':e.get('name'),
        'original_text':props[e.get('xmi.id')]['text'].removeprefix('<memo>#NOTES#'),
        'english_title':e.get('name'),
        'english_text':props[e.get('xmi.id')]['text'].removeprefix('<memo>#NOTES#'),
        'translation_reviewed':False,
    } for e in root.iter(q('ClassifierRole'))}
    return {'requirements':rows,'figures':[], 'instructions':
        'Provide concise English titles (max 48 characters), complete English text, and 3-4 figures with name, ids (3-5 each), rationale. Unchanged English text needs no translation approval. Review any translation before setting translation_reviewed=true.'}

def paper_bundle(xml, mapping):
    if isinstance(xml,bytes):xml=xml.decode('utf-8')
    root=ET.fromstring(xml);props=properties(root);content=root.find('XMI.content')
    roles=list(root.iter(q('ClassifierRole'))); ids={props[e.get('xmi.id')]['id'] for e in roles}
    rows=mapping['requirements'];figures=mapping['figures']
    if set(rows)!=ids:raise ValueError('Mapping IDs must exactly match the current full model')
    if not 3<=len(figures)<=4:raise ValueError('Provide 3-4 representative figures')
    names=set()
    for f in figures:
        if not re.fullmatch('[a-z][a-z0-9_]*',f['name']) or f['name'] in names:raise ValueError('Unique lowercase figure names required')
        names.add(f['name'])
        if not 3<=len(f['ids'])<=5 or len(set(f['ids']))!=len(f['ids']) or not set(f['ids'])<=ids:raise ValueError('Each figure needs 3-5 distinct existing IDs')
        if not f.get('rationale'):raise ValueError('Selection rationale required')
    source_hash=hashlib.sha256(xml.encode()).hexdigest();provenance=[]
    def add(rid,key,value):
        ET.SubElement(content,q('TaggedValue'),{'tag':key,'xmi.id':'EAID_'+str(uuid.uuid4()).upper().replace('-','_'),'modelElement':rid,'value':value})
    for e in roles:
        rid=e.get('xmi.id');p=props[rid];bid=p['id'];row=rows[bid];text=p['text'].removeprefix('<memo>#NOTES#')
        if row['original_name']!=e.get('name') or row['original_text']!=text:raise ValueError('Stale original content: '+bid)
        title=row['english_title'];english=row['english_text']
        if not title.strip() or len(title)>48 or title==bid or re.search(r'[\u3400-\u9fff]',title+english):raise ValueError('Concise English title and English text required: '+bid)
        if english!=text:
            if not row.get('translation_reviewed'):raise ValueError('Human-reviewed translation required: '+bid)
            # Reject changed numbers and literal placeholders; semantic review remains explicit.
            for pattern in (r'\d+(?:\.\d+)?',r'\{\{?TBD\|.*?\}\}?'):
                if re.findall(pattern,text)!=re.findall(pattern,english):raise ValueError('Translation changed protected numbers/placeholders: '+bid)
            if not re.search(r'[\u3400-\u9fff]',text):raise ValueError('Existing English normative text must remain verbatim: '+bid)
        for key,value in {'paper_original_name':e.get('name'),'paper_original_text':'<memo>#NOTES#'+text,'paper_source_guid':rid,'paper_source_sha256':source_hash}.items():
            if key in p:raise ValueError('Export from the original model, not an existing paper package')
            add(rid,key,value)
        e.set('name',title)
        for tv in content.findall(q('TaggedValue')):
            if tv.get('modelElement')==rid and tv.get('tag')=='text':tv.set('value','<memo>#NOTES#'+english)
        provenance.append({'id':bid,'source_guid':rid,**row})
    names_by_guid={e.get('xmi.id'):e.get('name') for e in roles}
    for edge in root.iter(q('Association')):
        ends=list(edge.iter(q('AssociationEnd')))
        for key,end in zip(('ea_sourceName','ea_targetName'),ends):
            for tv in edge.iter(q('TaggedValue')):
                if tv.get('tag')==key:tv.set('value',names_by_guid[end.get('type')])
    source=serialize(root);files={};manifest={'source_sha256':source_hash,'requirements':provenance,'figures':figures,'packages':[]}
    for f in [{'name':'english_full','ids':None,'rationale':'Complete engineering model; not a main-text figure.'}]+figures:
        output=presentation_xml(source,native_exporter().GRADE_STYLE,visible_ids=f['ids'],name='REQ_'+f['name'])
        view=ET.fromstring(output)
        source_roles={e.get('xmi.id') for e in roles if props[e.get('xmi.id')].get('grade','_src') in ('_src','source')}
        for obj in view.iter(q('DiagramElement')):
            if obj.get('subject') in source_roles:
                geometry=obj.get('geometry','')
                left=int(re.search(r'Left=(\d+)',geometry).group(1))
                obj.set('geometry',geometry.replace('Left='+str(left)+';','Left='+str(left+60)+';'))
        if f['ids'] and all(props[r]['id'] in f['ids'] for r in source_roles) and len(f['ids'])==len(source_roles):
            # Independent source scopes fit a single row; no artificial links.
            index=0
            for obj in view.iter(q('DiagramElement')):
                if obj.get('subject') in source_roles:
                    left=20+200*index;index+=1
                    obj.set('geometry',f'Left={left};Top=20;Right={left+180};Bottom=96;')
                elif obj.get('subject') not in names_by_guid:
                    obj.set('geometry',f'Left=20;Top=126;Right={20+200*len(source_roles)-20};Bottom=181;')
        # Reserve the top band for EA's native diagram-frame caption.
        for obj in view.iter(q('DiagramElement')):
            geometry=obj.get('geometry','')
            if 'Top=' in geometry:
                geometry=re.sub(r'(Top|Bottom)=(\d+);',lambda m:m[1]+'='+str(int(m[2])+40)+';',geometry)
            else:
                geometry=re.sub(r'Path=([^;]*);',lambda m:'Path='+re.sub(r'(-?\d+):(-?\d+)\$',lambda p:p[1]+':'+str(int(p[2])-40)+'$',m[1])+';',geometry)
            obj.set('geometry',geometry)
        # EA renders its native frame; an explicit Package object obscures nodes.
        output=serialize(view)
        status_mode=next((p.get('coloring_mode') for p in props.values() if p.get('coloring_mode')),None)
        if status_mode:
            from .ea_status_view import status_view
            output=status_view(output,status_mode)
        output,guid_map=fresh_ids(output)
        # fresh_ids rewrites references globally; provenance must point backwards.
        view=ET.fromstring(output)
        original_guids={guid_map[e.get('xmi.id')]:e.get('xmi.id') for e in roles}
        for tv in view.iter(q('TaggedValue')):
            if tv.get('tag')=='paper_source_guid':tv.set('value',original_guids[tv.get('modelElement')])
        output=serialize(view)
        files[f['name']+'.xml']=output.encode('utf-8')
        files[f['name']+'_guid_map.json']=json.dumps(guid_map,indent=2).encode()
        manifest['packages'].append({'name':f['name'],'visible_ids':f['ids'] or sorted(ids),'sha256':hashlib.sha256(files[f['name']+'.xml']).hexdigest()})
    files['selection_translation_map.json']=json.dumps(mapping,ensure_ascii=False,indent=2).encode('utf-8')
    files['provenance.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    files['README.txt']=b'All XML packages retain the complete model. Only diagram selection changes. Names are concise English titles; id and full text remain independent. Notes are hidden by default. Source names/text/GUIDs and original metadata are retained. Gray=source; blue=B; orange=C where present. Grades are rule classifications, not probabilities. No paid translation API. Import a fresh package into a separate EA test repository; export PNG/EMF using licensed EA for journal artwork. Selection is illustrative, not statistically representative. Human review is required for translations; numeric checks cannot prove unit or modality equivalence.\n'
    return files

def paper_zip(xml,mapping):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in paper_bundle(xml,mapping).items():z.writestr(name,data)
    return output.getvalue()
