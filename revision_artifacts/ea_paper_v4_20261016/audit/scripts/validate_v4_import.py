from pathlib import Path
import sys,sqlite3,json,xml.etree.ElementTree as ET,zipfile,re,shutil,hashlib
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R));O=R/'revision_artifacts/ea_paper_v4_20261016';A=O/'audit'
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.requirement_status import display_colors,colorref
root=ET.parse(O/'candidate/paper_v4_combined.xml').getroot();props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};mapping=json.loads((A/'selection_translation_map.json').read_text(encoding='utf-8'))
db=sqlite3.connect((O/'v4_independent_import.qea').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
objects={r['Object_ID']:dict(r) for r in db.execute('SELECT * FROM t_object')};tags={}
for r in db.execute('SELECT * FROM t_objectproperties'):
    v=r['Value'] or '';v=v+'#NOTES#'+(r['Notes'] or '') if v=='<memo>' else v
    tags.setdefault(r['Object_ID'],{})[r['Property']]=v
by={p['id']:oid for oid,p in tags.items() if 'id' in p};assert len(by)==15
clean=lambda s:(s or '').replace('\r\n','\n')
ids={rid:by[p['id']] for rid,p in props.items()}
for rid,p in props.items():
    oid=ids[rid];obj=objects[oid];assert obj['Name']==roles[rid].get('name');assert obj['Stereotype']=='requirement'
    assert clean(obj['Note'])==clean(p['text'].removeprefix('<memo>#NOTES#'))
    for k,v in p.items():assert clean(tags[oid].get(k))==clean(v),(p['id'],k)
expected={tuple(ids[e.get('type')] for e in edge.iter(q('AssociationEnd')))+('Nesting',) for edge in root.iter(q('Association'))}
actual={(r['Start_Object_ID'],r['End_Object_ID'],r['Connector_Type']) for r in db.execute('SELECT * FROM t_connector')};assert expected==actual and len(actual)==12
diagrams=list(db.execute('SELECT * FROM t_diagram'));assert len(diagrams)==3
for d in diagrams:
    f=next(f for f in mapping['figures'] if f['title']==d['Name']);objs=list(db.execute('SELECT * FROM t_diagramobjects WHERE Diagram_ID=?',(d['Diagram_ID'],)))
    assert {tags[o['Object_ID']]['id'] for o in objs}==set(f['ids'])
    assert 'ShowNotes=0;' in d['StyleEx'] and 'text' in d['StyleEx'].split('SUPTAG=')[1].split(';')[0].split(',')
    for obj in objs:
        state=tags[obj['Object_ID']]
        for key,col in zip(['BCol','LCol'],display_colors(state,'Evidence support')):assert key+'='+str(colorref(col))+';' in obj['ObjectStyle']
    assert len(list(db.execute('SELECT * FROM t_diagramlinks WHERE DiagramID=?',(d['Diagram_ID'],))))==4
# Browser ZIP must carry the same semantic model, per-diagram layout and colors.
def semantic(data):
    r=ET.fromstring(data);ps=properties(r);rs={e.get('xmi.id'):e for e in r.iter(q('ClassifierRole'))}
    rows={p['id']:{'name':rs[rid].get('name'),**{k:v for k,v in p.items() if k not in ('paper_source_guid','paper_source_sha256','status_source_path')}} for rid,p in ps.items()}
    for row in rows.values():
        for key,value in list(row.items()):
            if key.endswith("_json"):row[key]=json.loads(value.removeprefix("<memo>#NOTES#"))
    links=sorted(tuple(ps[e.get('type')]['id'] for e in a.iter(q('AssociationEnd'))) for a in r.iter(q('Association')))
    views={d.get('name'):sorted((ps[e.get('subject')]['id'],e.get('geometry'),re.sub(r'DUID=[^;]*;', '', e.get('style',''))) for e in d.iter(q('DiagramElement')) if e.get('subject') in rs) for d in r.iter(q('Diagram'))}
    return rows,links,views
with zipfile.ZipFile(A/'browser/paper_support.zip') as z:
    for p in (O/'candidate').glob('*.xml'):assert semantic(z.read(p.name))==semantic(p.read_bytes()),p.name
result={'actual_import':True,'single_combined_import':True,'native_requirements':15,'native_original_edges':12,'native_diagrams':3,'nodes_per_diagram':[5,5,5],'all_tags_and_complete_notes_equal':True,'browser_semantics_layout_colors_equal':True,'color_mode':'Evidence support','direct_claims_independently_verified':False,'visual_png_and_emf_review':'pending'}
(A/'native_acceptance.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
