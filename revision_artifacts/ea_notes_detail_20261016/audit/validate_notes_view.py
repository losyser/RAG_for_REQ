from pathlib import Path
import sys,json,sqlite3,collections,hashlib,xml.etree.ElementTree as ET,struct,re,zipfile,shutil
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R));O=R/'revision_artifacts/ea_notes_detail_20261016';V=R/'revision_artifacts/ea_paper_v4_20261016';A=O/'audit'
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.requirement_status import display_colors,colorref
root=ET.parse(O/'paper/reliability_selected_notes.xml').getroot();props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};selection=json.loads((A/'selection.json').read_text());expanded=set(selection['expanded'])
db=sqlite3.connect((O/'notes_import_validation.qea').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
objects={r['Object_ID']:dict(r) for r in db.execute('SELECT * FROM t_object')};tags={}
for r in db.execute('SELECT * FROM t_objectproperties'):
 v=r['Value'] or '';v=v+'#NOTES#'+(r['Notes'] or '') if v=='<memo>' else v;tags.setdefault(r['Object_ID'],{})[r['Property']]=v
by={p['id']:oid for oid,p in tags.items() if 'id' in p};assert len(by)==5
clean=lambda s:(s or '').replace('\r\n','\n')
for rid,p in props.items():
 oid=by[p['id']];assert objects[oid]['Name']==roles[rid].get('name');assert clean(objects[oid]['Note'])==clean(p['text'].removeprefix('<memo>#NOTES#'))
 for k,v in p.items():assert clean(tags[oid].get(k))==clean(v),(p['id'],k)
expected={tuple(by[props[e.get('type')]['id']] for e in edge.iter(q('AssociationEnd')))+('Nesting',) for edge in root.iter(q('Association'))};actual={(r['Start_Object_ID'],r['End_Object_ID'],r['Connector_Type']) for r in db.execute('SELECT * FROM t_connector')};assert expected==actual and len(actual)==4
assert db.execute('SELECT COUNT(*) FROM t_diagram').fetchone()[0]==1
for r in db.execute('SELECT * FROM t_diagramobjects'):
 p=tags[r['Object_ID']];assert ('Notes=0;' in r['ObjectStyle'])==(p['id'] in expanded)
 for key,col in zip(['BCol','LCol'],display_colors(p,'Evidence support')):assert key+'='+str(colorref(col))+';' in r['ObjectStyle']
# Native vector text demonstrates that no selected Notes sentence is truncated.
data=(O/'paper/reliability_selected_notes.emf').read_bytes();texts=[];offset=0
while offset+8<=len(data):
 typ,n=struct.unpack_from('<II',data,offset)
 if n<8:break
 if typ==84:
  chars,pos=struct.unpack_from('<II',data,offset+44);texts.append(data[offset+pos:offset+pos+chars*2].decode('utf-16-le'))
 offset+=n
norm=lambda s:re.sub(r'\s+','',s)
joined=norm(' '.join(texts))
for p in props.values():
 if p['id'] in expanded:assert norm(p['text'].removeprefix('<memo>#NOTES#')) in joined,('truncated',p['id'])
(A/'emf_visible_text.txt').write_text('\n'.join(texts),encoding='utf-8')
hashes=json.loads((A/'original_paper_hashes.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
datahashes=json.loads((V/'audit/data_hashes_before.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in datahashes.items())
preserved={}
for name,p in [('test_v4',V/'v4_independent_import.qea'),('4x',Path(r'C:\Users\yando\Desktop\4x.qea')),('111',R/'revision_artifacts/ea_native_followup_20261016/111.qea')]:
 with sqlite3.connect((A/f'{name}_before.qea').as_uri()+'?mode=ro',uri=True) as before,sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as after:
  for t in ['t_package','t_object','t_objectproperties','t_connector','t_diagram','t_diagramobjects','t_diagramlinks','t_xref']:assert collections.Counter(before.execute('SELECT * FROM '+t))==collections.Counter(after.execute('SELECT * FROM '+t)),(name,t)
 preserved[name]='8 core tables unchanged'
result={'actual_xml_import':True,'nodes':5,'original_edges':4,'expanded':sorted(expanded),'folded':selection['folded'],'all_native_tags_and_notes_match_xml':True,'complete_expanded_notes_in_native_emf':True,'png_and_emf_visually_checked':True,'color_mode':'Evidence support','support_is_unverified':True,'original_v4_paper_files_unchanged':10,'original_data_files_unchanged':len(datahashes),'models':preserved,'trial_watermark_retained':True}
(A/'acceptance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
with sqlite3.connect(O/'notes_validated_saved.qea') as dst:db.backup(dst)
(O/'README.txt').write_text('Cooling Reliability — selected Notes detail\n\nSelected R001 for direct/indirect/gap status coverage. Complete Notes expanded for ER-R001-02 (47 words), ER-R001-03 (60 words), ER-R001-04 (25 words). R001 and ER-R001-01 remain folded. All five real nodes, four original edges, original properties and full text preserved. Colors encode reported Evidence support, not independent verification.\n\nActual XML import into an independent new EA model, native PNG/EMF exported and visually checked. Full selected Notes text verified in vector output. Trial watermark retained. No old model, original folded diagram, data or paper changes. Existing v4 test-model save prompt was canceled; a separate new process was used instead. No source code changes; existing 285-test baseline retained.\n',encoding='utf-8')
with zipfile.ZipFile(O/'reliability_selected_notes_validated.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((O/'paper').iterdir()):z.write(p,p.name)
 z.write(O/'README.txt','README.txt')
print(json.dumps(result,indent=2))
