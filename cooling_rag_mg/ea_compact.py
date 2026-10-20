"""Presentation-only EA XMI transform. Engineering text/IDs/links stay intact."""
import copy
import re
import textwrap
import xml.etree.ElementTree as ET

U='omg.org/UML1.3'
def q(name): return '{'+U+'}'+name
ET.register_namespace('UML',U)
ROUTES={'OPEN_ITEM':'OPEN','ENGINEER_CONFIRM':'CONFIRM','SPOT_CHECK':'SPOT','ADJUDICATE':'REVIEW','VERIFY_OR_REJECT':'VERIFY'}
LEGEND_ID='EAID_COMPACT_LEGEND_00000000'
LEGEND='GRADE COLORS: grey=Source; green=A; blue=B; amber=C; red=X. Grade is provenance/format, not truth or EA status.\nREVIEW: OPEN=open item; CONFIRM=engineer; SPOT=spot-check; REVIEW=conflict candidate; VERIFY=verify/reject.\nNesting=source/output grouping. Full requirements and evidence remain in element properties.'

def merge_style(style,updates):
    remaining=dict(updates);parts=[]
    for part in style.split(';'):
        if not part:continue
        key=part.split('=',1)[0]
        if key in updates:
            if key in remaining: parts.append(key+'='+str(remaining.pop(key)))
        else:parts.append(part)
    parts += [key+'='+str(value) for key,value in remaining.items()]
    return ';'.join(parts)+';'

def compact_xml(xml,colors):
    root=ET.fromstring(xml);props={}
    for tv in root.iter(q('TaggedValue')):
        if tv.get('modelElement'):props.setdefault(tv.get('modelElement'),{})[tv.get('tag')]=tv.get('value','')
    roles={el.get('xmi.id'):el for el in root.iter(q('ClassifierRole'))}
    content=root.find('XMI.content');diagram=root.find('.//'+q('Diagram'));elements=diagram.find(q('Diagram.element'))
    nodes={el.get('subject'):el for el in elements if el.get('subject') in roles}
    def add_property(rid,key,value):
        # Stable property ID separate from all existing IDs.
        ET.SubElement(content,q('TaggedValue'),{'tag':key,'xmi.id':rid+'_'+key,'value':value,'modelElement':rid})
    for rid,el in roles.items():
        p=props[rid];biz=p['id'];grade=p.get('grade','_src');route=ROUTES.get(p.get('review_route'),'SOURCE')
        original=el.get('name',''); title=re.sub(r'^'+re.escape(biz)+r'\s*','',original)
        # Remove generic trailing wording and repair known legacy mid-word title truncation.
        title=re.sub(r'\s+Requiremen(?:t)?$','',title)
        title=re.sub(r'\bComplianc$','Compliance',title)
        title=re.sub(r'\bSettin$','Setting',title)
        title=re.sub(r'\bSett$','Setting',title)
        title=' '.join(title.split()[:6]) or 'Requirement'
        title_lines=textwrap.wrap(title,width=28,break_long_words=False)
        marker='SOURCE' if grade=='_src' else grade+' | '+route
        el.set('name',biz+'\n'+'\n'.join(title_lines)+'\n['+marker+']')
        add_property(rid,'display_full_name',original)
        add_property(rid,'display_title',title)
        add_property(rid,'display_notice','Presentation label only; full engineering text is the SysML text property')
        for tv in el.findall('.//'+q('TaggedValue')):
            if tv.get('tag')=='documentation':
                add_property(rid,'audit_notes_full',tv.get('value',''));tv.set('value',marker)
            if tv.get('tag')=='style':
                bg,border=colors.get(grade,colors['_unknown']);tv.set('value',merge_style(tv.get('value',''),{'BackColor':bg,'BorderColor':border,'BorderWidth':2}))
        # Color serialization keys are documented by Sparx DiagramObject.SetStyleEx.
        bg,border=colors.get(grade,colors['_unknown'])
        nodes[rid].set('style',merge_style(nodes[rid].get('style',''),{'Tag':0,'BCol':bg,'LCol':border,'LWth':2}))
    for tv in diagram.findall('./'+q('ModelElement.taggedValue')+'/'+q('TaggedValue')):
        if tv.get('tag')=='styleex':tv.set('value',merge_style(tv.get('value',''),{'ShowNotes':0}))
    dtv=diagram.find(q('ModelElement.taggedValue'))
    ET.SubElement(dtv,q('TaggedValue'),{'tag':'EAStyle','value':'ShowNotes=0;ShowTags=0;'})
    # Pack small groups side-by-side, larger groups across the complete width.
    sources=[rid for rid in roles if '.' not in props[rid]['id']]
    positions={};cursor=120;pending=None;rowheight=0
    for pid in sources:
        children=[rid for rid in roles if props[rid]['id'].startswith(props[pid]['id']+'.')]
        large=len(children)>6;cols=4 if large else 2
        if large and pending is not None:cursor+=rowheight+40;pending=None;rowheight=0
        x0=40 if pending is None else 540
        positions[pid]=(x0+(cols*240-30-220)//2,cursor,220,64)
        for k,cid in enumerate(children):positions[cid]=(x0+(k%cols)*240,cursor+110+(k//cols)*120,210,90)
        height=110+((len(children)+cols-1)//cols)*120
        if large:cursor+=height+40
        elif pending is None:pending=True;rowheight=height
        else:cursor+=max(rowheight,height)+40;pending=None;rowheight=0
    for rid,(x,y,w,h) in positions.items():nodes[rid].set('geometry',f'Left={x};Top={y};Right={x+w};Bottom={y+h};')
    maxright=max(x+w for x,y,w,h in positions.values())+30;maxbottom=max(y+h for x,y,w,h in positions.values())+30
    for el in elements:
        if 'NSL=1;' in el.get('style',''):el.set('geometry',f'Left=10;Top=10;Right={maxright};Bottom={maxbottom};')
    note=ET.SubElement(content,q('Comment'),{'xmi.id':LEGEND_ID,'name':'Compact legend','body':LEGEND})
    notevalues=ET.SubElement(note,q('ModelElement.taggedValue'))
    for tag,value in [('ea_stype','Note'),('documentation',LEGEND),('package',diagram.get('owner'))]:ET.SubElement(notevalues,q('TaggedValue'),{'tag':tag,'value':value})
    ET.SubElement(elements,q('DiagramElement'),{'geometry':f'Left=30;Top=20;Right={maxright-20};Bottom=100;','subject':LEGEND_ID,'seqno':'1000','style':'DUID=CAFE0001;UCRect=1;'})
    diagram.set('name',diagram.get('name')+'_Compact')
    return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode').replace(' />','/>')

def validate_compact(original,compact,colors):
    a,b=ET.fromstring(original),ET.fromstring(compact);errors=[]
    ar={x.get('xmi.id'):x for x in a.iter(q('ClassifierRole'))};br={x.get('xmi.id'):x for x in b.iter(q('ClassifierRole'))}
    if set(ar)!=set(br):errors.append('requirement IDs changed')
    def semantic_props(tree):return {(x.get('modelElement'),x.get('tag')):x.get('value') for x in tree.iter(q('TaggedValue')) if x.get('modelElement')}
    ap,bp=semantic_props(a),semantic_props(b)
    if any(bp.get(k)!=v for k,v in ap.items()):errors.append('original model properties changed')
    def edges(tree):return [(x.get('xmi.id'),[z.get('type') for z in x.iter(q('AssociationEnd'))]) for x in tree.iter(q('Association'))]
    if edges(a)!=edges(b):errors.append('relationship IDs/endpoints changed')
    an={x.get('subject'):x for x in a.iter(q('DiagramElement'))};bn={x.get('subject'):x for x in b.iter(q('DiagramElement'))}
    for rid,el in br.items():
        name=el.get('name','')
        if len(name)>120 or len(name.splitlines())>6 or 'TBD|' in name:errors.append(rid+': verbose label')
        for x in el.findall('.//'+q('TaggedValue')):
            if x.get('tag')=='documentation' and len(x.get('value',''))>32:errors.append(rid+': verbose notes')
        if re.search(r'DUID=([^;]+)',an[rid].get('style','')).group(1)!=re.search(r'DUID=([^;]+)',bn[rid].get('style','')).group(1):errors.append(rid+': DUID changed')
        grade=bp.get((rid,'grade'),'_src');bg,border=colors.get(grade,colors['_unknown'])
        if not all(token in bn[rid].get('style','') for token in ['Tag=0;',f'BCol={bg};',f'LCol={border};','LWth=2;']):errors.append(rid+': instance style mismatch')
    return errors
