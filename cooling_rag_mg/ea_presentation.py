"""EA display views. Canonical text stays in its independent SysML memo tag.
Notes is an explicit display projection; prior documentation is retained separately.
"""
import copy, math, re, uuid, unicodedata
import xml.etree.ElementTree as ET
from .ea_structure import q, properties
from .ea_compact import merge_style

def serialize(root):
    return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')

def fresh_ids(xml):
    root=ET.fromstring(xml); mapping={}
    for e in root.iter():
        old=e.get('xmi.id')
        if old: mapping[old]=('EAPK_' if old.startswith('EAPK_') else 'EAID_')+str(uuid.uuid4()).upper().replace('-','_')
    for old,new in mapping.items():
        xml=xml.replace(old,new)
        if old.startswith('EAID_'): xml=xml.replace('{'+old[5:].replace('_','-')+'}','{'+new[5:].replace('_','-')+'}')
    return xml,mapping

def presentation_xml(xml, colors, *, visible_ids=None, expanded_ids=(), name='Requirements_Folded'):
    root=ET.fromstring(xml);before=properties(root);content=root.find('XMI.content')
    next(root.iter(q('Package'))).set('name','Presentation_'+name.removeprefix('REQ_'))
    roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))}
    ids={p['id']:r for r,p in before.items() if r in roles}
    if len(ids)!=len(roles):raise ValueError('Duplicate business IDs')
    visible=set(ids) if visible_ids is None else set(visible_ids)
    expanded=set(visible) if expanded_ids=='all' else set(expanded_ids)
    if not visible <= ids.keys() or not expanded <= visible:raise ValueError('Unknown view/expanded ID')
    for rid,role in roles.items():
        p=before[rid];full=p['text'].removeprefix('<memo>#NOTES#')
        tvs=role.find(q('ModelElement.taggedValue'))
        doc=next((t for t in tvs if t.get('tag')=='documentation'),None)
        if 'original_documentation' not in p:
            ET.SubElement(content,q('TaggedValue'),{'tag':'original_documentation','xmi.id':'EAID_'+str(uuid.uuid4()).upper().replace('-','_'),'modelElement':rid,'value':doc.get('value','') if doc is not None else ''})
        if doc is None:doc=ET.SubElement(tvs,q('TaggedValue'),{'tag':'documentation'})
        doc.set('value',full)
    props=properties(root)
    diagram=next(root.iter(q('Diagram')));diagram.set('name',name)
    tvs=diagram.find(q('ModelElement.taggedValue'))
    hidden=sorted({k for p in props.values() for k in p if k!='id'})
    for key in ['styleex','EAStyle']:
        tv=next((t for t in tvs if t.get('tag')==key),None)
        if tv is None:tv=ET.SubElement(tvs,q('TaggedValue'),{'tag':key})
        settings={'ShowNotes':0,'ShowTags':1}
        if key=='styleex':settings['SUPTAG']=','.join(hidden)
        tv.set('value',merge_style(tv.get('value',''),settings))
    elements=diagram.find(q('Diagram.element'));nodes={n.get('subject'):n for n in elements if n.get('subject') in roles and props[n.get('subject')]['id'] in visible}
    edges={e.get('xmi.id'):list(e.iter(q('AssociationEnd'))) for e in root.iter(q('Association'))}
    children={r:[] for r in nodes};parent={}
    for ends in edges.values():
        a,b=[e.get('type') for e in ends]
        if a in nodes and b in nodes:
            if b in parent:raise ValueError('Multiple layout parents')
            parent[b]=a;children[a].append(b)
    for e in list(elements):
        subject=e.get('subject')
        if subject not in nodes and not (subject in edges and all(x.get('type') in nodes for x in edges[subject])):elements.remove(e)
    width=240;gapx=64;gapy=24;rects={};visited=set()
    def height(r):
        title=roles[r].get('name','');h=76+15*max(0,math.ceil(len(title)/32)-1)
        if props[r]['id'] in expanded:
            text=props[r]['text'].removeprefix('<memo>#NOTES#')
            h+=32+17*sum(max(1,math.ceil(sum(2 if unicodedata.east_asian_width(c) in ('W','F') else 1 for c in line)/34)) for line in text.splitlines())
        return h
    def layout(r,x,y,stack):
        if r in stack:raise ValueError('Cyclic layout')
        h=height(r);cy=y
        for child in children[r]:cy=layout(child,x+width+gapx,cy,stack|{r})+gapy
        span=max(h,cy-y-gapy if children[r] else h)
        top=y+(span-h)//2;rects[r]=(x,top,x+width,top+h);visited.add(r)
        return y+span
    cursor=20
    for r in nodes:
        if r not in parent:cursor=layout(r,20,cursor,set())+40
    if visited!=set(nodes):raise ValueError('Cyclic or unplaced nodes')
    for rid,n in nodes.items():
        l,t,r,b=rects[rid];n.set('geometry',f'Left={l};Top={t};Right={r};Bottom={b};')
        grade=props[rid].get('grade','_src');bg,line=colors.get(grade,colors['_unknown'])
        style=merge_style(n.get('style',''),{'Tag':1,'RzO':2,'BCol':bg,'LCol':line,'LWth':1,'font':'Arial','fontsz':100} )
        style=re.sub(r'(?:^|;)Notes=[^;]*;',';',style)
        if props[rid]['id'] in expanded:style=merge_style(style,{'Notes':0})
        n.set('style',style)
    for n in elements:
        if n.get('subject') not in edges:continue
        a,b=[e.get('type') for e in edges[n.get('subject')]];ar,br=rects[a],rects[b]
        x=(ar[2]+br[0])//2;sy=-(ar[1]+ar[3])//2;ty=-(br[1]+br[3])//2
        n.set('geometry',f'SX=0;SY=0;EX=0;EY=0;EDGE=3;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path={x}:{sy}${x}:{ty}$;')
        style=re.sub(r'Hidden=[^;]*;','',n.get('style',''));n.set('style',merge_style(style,{'Mode':3,'TREE':'H'})+'Hidden=0;')
    # Diagram-only text legend: actual grades present in this view, never invented classes.
    present={props[r].get('grade','source') for r in nodes};labels={'source':'Gray: source','A':'Green: A','B':'Blue: B','C':'Orange: C','X':'Red: X'}
    legend=' | '.join(labels[g] for g in ['source','A','B','C','X'] if g in present)+'\nGrade = criterion/citation rule, not probability. Nesting = grouping.'
    lid='EAID_'+str(uuid.uuid4()).upper().replace('-','_')
    package=next(root.iter(q('Package')))
    note=ET.SubElement(package.find(q('Namespace.ownedElement')),q('Comment'),{'xmi.id':lid,'visibility':'public','namespace':package.get('xmi.id')})
    nt=ET.SubElement(note,q('ModelElement.taggedValue'));ET.SubElement(nt,q('TaggedValue'),{'tag':'ea_stype','value':'Text'});ET.SubElement(nt,q('TaggedValue'),{'tag':'documentation','value':legend});ET.SubElement(nt,q('TaggedValue'),{'tag':'package','value':package.get('xmi.id')})
    ET.SubElement(elements,q('DiagramElement'),{'subject':lid,'geometry':f'Left=20;Top={cursor};Right={max(r[2] for r in rects.values())};Bottom={cursor+55};','style':'DUID='+uuid.uuid4().hex[:8].upper()+';font=Arial;fontsz=100;BCol=16777215;LCol=16777215;'})
    after=properties(root)
    for r,p in before.items():
        for k,v in p.items():
            if after[r][k]!=v:raise ValueError('Property loss')
    return serialize(root)
