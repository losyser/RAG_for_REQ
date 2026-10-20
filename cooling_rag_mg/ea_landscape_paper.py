"""Selected, translated landscape paper views with real hierarchy and shared status colors."""
import copy,hashlib,json,re,uuid,xml.etree.ElementTree as ET
from .ea_structure import q,properties
from .ea_presentation import presentation_xml,serialize,fresh_ids
from .ea_ui_export import native_exporter
from .ea_status_view import status_view
from .ea_compact import merge_style


def _fresh(xml):
    xml,mapping=fresh_ids(xml);root=ET.fromstring(xml);reverse={v:k for k,v in mapping.items()}
    for t in root.iter(q('TaggedValue')):
        if t.get('tag')=='paper_source_guid':t.set('value',reverse.get(t.get('value'),t.get('value')))
    return serialize(root)


def _subset(root, selected):
    root=copy.deepcopy(root);props=properties(root)
    keep={r for r,p in props.items() if p.get('id') in selected}
    remove={e.get('xmi.id') for e in root.iter(q('ClassifierRole')) if e.get('xmi.id') not in keep}
    for e in root.iter(q('Association')):
        if not all(x.get('type') in keep for x in e.iter(q('AssociationEnd'))):remove.add(e.get('xmi.id'))
    for parent in root.iter():
        for e in list(parent):
            if e.get('xmi.id') in remove or e.get('modelElement') in remove or e.get('subject') in remove or e.tag==q('Comment'):parent.remove(e)
    return root


def _layout(xml, figure, mode):
    root=ET.fromstring(presentation_xml(xml,native_exporter().GRADE_STYLE,visible_ids=figure['ids'],name=figure['title']))
    root=ET.fromstring(status_view(serialize(root),mode))
    props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};by={p['id']:r for r,p in props.items() if r in roles}
    diagram=next(root.iter(q('Diagram')));elements=diagram.find(q('Diagram.element'));visible={by[i] for i in figure['ids']}
    edges={e.get('xmi.id'):list(e.iter(q('AssociationEnd'))) for e in root.iter(q('Association'))};children={r:[] for r in visible};parents={}
    for ends in edges.values():
        a,b=[e.get('type') for e in ends]
        if a in visible and b in visible:children[a].append(b);parents[b]=a
    roots=visible-set(parents)
    if roots!={by[figure['root_id']]}:raise ValueError('Figure must contain its single real root and connected descendants')
    order={by[bid]:i for i,bid in enumerate(figure['ids'])}
    for r in children:children[r].sort(key=lambda x:order[x])
    rects={};width=250;gap=24;height=100;ygap=80;leaf=0;visiting=set()
    def place(r,depth):
        nonlocal leaf
        if r in visiting:raise ValueError('Cyclic hierarchy')
        visiting.add(r)
        if children[r]:
            xs=[place(c,depth+1) for c in children[r]];center=(min(xs)+max(xs))/2
        else:center=40+width/2+leaf*(width+gap);leaf+=1
        top=60+depth*(height+ygap);rects[r]=(round(center-width/2),top,round(center+width/2),top+height)
        return center
    place(by[figure['root_id']],0)
    if len(rects)!=len(visible):raise ValueError('Missing nodes in hierarchy')
    # Center the real root over the complete horizontal span, retaining actual edges.
    rid=by[figure['root_id']];span_left=min(x[0] for x in rects.values());span_right=max(x[2] for x in rects.values());center=(span_left+span_right)/2
    rects[rid]=(round(center-width/2),60,round(center+width/2),60+height)
    for parent in root.iter():
        for e in list(parent):
            if e.tag==q('Comment'):parent.remove(e)
    for e in list(elements):
        rid=e.get('subject')
        if rid in rects:
            l,t,r,b=rects[rid];e.set('geometry',f'Left={l};Top={t};Right={r};Bottom={b};');e.set('seqno',str(order[rid]+1))
        elif rid in edges:
            a,b=[x.get('type') for x in edges[rid]];ar,br=rects[a],rects[b];ax=(ar[0]+ar[2])//2;bx=(br[0]+br[2])//2;y=-(ar[3]+br[1])//2
            e.set('geometry',f'SX=0;SY=0;EX=0;EY=0;EDGE=3;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path={ax}:{y}${bx}:{y}$;')
            e.set('style',merge_style(e.get('style',''),{'Mode':3,'TREE':'V','Hidden':0}))
        else:elements.remove(e)
    return root


def landscape_bundle(xml,mapping):
    if isinstance(xml,bytes):xml=xml.decode('utf-8')
    root=ET.fromstring(xml);props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};by={p['id']:r for r,p in props.items() if r in roles}
    figures=mapping['figures'];rows=mapping['requirements'];selected={i for f in figures for i in f['ids']}
    if not 1<=len(figures)<=4:raise ValueError('Choose 1-4 purposeful figures')
    if set(rows)!=selected or not selected<=by.keys():raise ValueError('Translation map must exactly cover selected IDs')
    mode=mapping.get('coloring_mode','Evidence support')
    source_modes={props[by[i]].get('coloring_mode') for i in selected}-{None}
    if source_modes and source_modes!={mode}:raise ValueError('Paper coloring mode must match the current UI export')
    names=set()
    for f in figures:
        if not re.fullmatch('[a-z][a-z0-9_]*',f['name']) or f['name'] in names:raise ValueError('Unique figure filenames required')
        names.add(f['name'])
        if not 4<=len(f['ids'])<=6 or len(f['ids'])!=len(set(f['ids'])) or f['root_id'] not in f['ids']:raise ValueError('Each figure needs about five nodes including its root')
        if not f.get('rationale') or re.search(r'[\u3400-\u9fff]',f['title']):raise ValueError('English title and selection rationale required')
    content=root.find('XMI.content');sha=hashlib.sha256(xml.encode()).hexdigest()
    def put(rid,k,v):
        t=next((t for t in content.findall(q('TaggedValue')) if t.get('modelElement')==rid and t.get('tag')==k),None)
        if t is None:t=ET.SubElement(content,q('TaggedValue'),{'xmi.id':'EAID_'+str(uuid.uuid4()).upper().replace('-','_'),'modelElement':rid,'tag':k})
        t.set('value',v)
    for bid,row in rows.items():
        rid=by[bid];role=roles[rid];p=props[rid];text=p['text'].removeprefix('<memo>#NOTES#');title=row['english_title'];english=row['english_text']
        if row['original_name']!=role.get('name') or row['original_text']!=text:raise ValueError('Stale mapping: '+bid)
        if not title.strip() or len(title)>48 or len(title.split())>8 or title==bid or re.search(r'\b(shall|must)\b',title,re.I) or re.search(r'[\u3400-\u9fff]',title+english):raise ValueError('Concise English title and complete English text required: '+bid)
        if re.findall(r'\d+(?:\.\d+)?',text)!=re.findall(r'\d+(?:\.\d+)?',english):raise ValueError('Translation changed numbers: '+bid)
        if english!=text and not row.get('translation_status'):raise ValueError('Translation provenance required: '+bid)
        for k,v in {'paper_original_name':role.get('name'),'paper_original_text':'<memo>#NOTES#'+text,'paper_source_guid':rid,'paper_source_sha256':sha,'paper_translation_status':row.get('translation_status','unchanged_english'),'paper_selection':'purposeful thematic/status sampling; not representative proportions'}.items():put(rid,k,v)
        role.set('name',title);put(rid,'text','<memo>#NOTES#'+english)
    # Relationship labels follow translated endpoints; types and endpoints never change.
    for edge in root.iter(q('Association')):
        ends=list(edge.iter(q('AssociationEnd')))
        for key,end in zip(['ea_sourceName','ea_targetName'],ends):
            for t in edge.iter(q('TaggedValue')):
                if t.get('tag')==key:t.set('value',roles[end.get('type')].get('name'))
    selected_root=_subset(root,selected);files={};diagrams=[]
    for f in figures:
        view=_layout(serialize(selected_root),f,mode);diagrams.append(copy.deepcopy(next(view.iter(q('Diagram')))))
        split=_subset(view,set(f['ids']));next(split.iter(q('Package'))).set('name',f['title']);result=_fresh(serialize(split))
        files[f['name']+'.xml']=result.encode('utf-8')
    # One package, one shared requirement population, all selected diagrams: one import.
    combined=_layout(serialize(selected_root),figures[0],mode);parent=next(e for e in combined.iter() if any(c.tag==q('Diagram') for c in e))
    for d in list(parent):
        if d.tag==q('Diagram'):parent.remove(d)
    for d in diagrams:
        d.set('xmi.id','EAID_'+str(uuid.uuid4()).upper().replace('-','_'));parent.append(d)
    next(combined.iter(q('Package'))).set('name','Paper v4 - Evidence Support')
    result=_fresh(serialize(combined));files['paper_v4_combined.xml']=result.encode('utf-8')
    files['audit/selection_translation_map.json']=json.dumps(mapping,ensure_ascii=False,indent=2).encode('utf-8')
    files['audit/provenance.json']=json.dumps({'source_sha256':sha,'selected_ids':sorted(selected),'full_source_count':len(by),'coloring_mode':mode,'relationship_semantics':'Original hierarchy, Nesting grouping only','translation_review':'Assistant translation; domain review remains pending','sampling':'Purposeful themes and status coverage, not population proportions'},indent=2).encode()
    return files
