from pathlib import Path
import sys,json,hashlib,sqlite3,xml.etree.ElementTree as ET
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_structure import q,properties
from cooling_rag_mg.ea_presentation import serialize
from cooling_rag_mg.ea_landscape_paper import _fresh
from cooling_rag_mg.ea_compact import merge_style
V=R/'revision_artifacts/ea_paper_v4_20261016';O=R/'revision_artifacts/ea_notes_detail_20261016';O.mkdir();(O/'audit').mkdir();(O/'paper').mkdir()
source=V/'paper/paper_v4_reliability.xml';root=ET.parse(source).getroot();props=properties(root);roles={e.get('xmi.id'):e for e in root.iter(q('ClassifierRole'))};by={p['id']:rid for rid,p in props.items()};expanded={'ER-R001-02','ER-R001-03','ER-R001-04'}
next(root.iter(q('Package'))).set('name','Paper v4 - Reliability Notes Detail');diagram=next(root.iter(q('Diagram')));diagram.set('name','Cooling Reliability - Selected Notes')
rects={by['R001']:(490,60,810,160)}
for i in range(4):
    bid=f'ER-R001-0{i+1}';left=40+i*320;rects[by[bid]]=(left,240,left+290,600 if bid in expanded else 340)
edges={e.get('xmi.id'):list(e.iter(q('AssociationEnd'))) for e in root.iter(q('Association'))}
for obj in diagram.iter(q('DiagramElement')):
    rid=obj.get('subject')
    if rid in roles:
        l,t,r,b=rects[rid];obj.set('geometry',f'Left={l};Top={t};Right={r};Bottom={b};')
        if props[rid]['id'] in expanded:obj.set('style',merge_style(obj.get('style',''),{'Notes':0}))
    elif rid in edges:
        a,b=[e.get('type') for e in edges[rid]];ax=(rects[a][0]+rects[a][2])//2;bx=(rects[b][0]+rects[b][2])//2
        obj.set('geometry',f'SX=0;SY=0;EX=0;EY=0;EDGE=3;$LLB=;LLT=;LMT=;LMB=;LRT=;LRB=;IRHS=;ILHS=;Path={ax}:-200${bx}:-200$;')
assert properties(root)==props
(O/'paper/reliability_selected_notes.xml').write_text(_fresh(serialize(root)),encoding='utf-8')
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (V/'paper').iterdir()};(O/'audit/original_paper_hashes.json').write_text(json.dumps(hashes,indent=2))
for name,p in [('test_v4',V/'v4_independent_import.qea'),('4x',Path(r'C:\Users\yando\Desktop\4x.qea')),('111',R/'revision_artifacts/ea_native_followup_20261016/111.qea')]:
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(O/'audit'/f'{name}_before.qea') as dst:src.backup(dst)
(O/'audit/selection.json').write_text(json.dumps({'expanded':sorted(expanded),'folded':['R001','ER-R001-01'],'source':str(source),'reason':'R001 covers reported direct (unverified), reported indirect (unverified), and evidence gap; selected Notes are 47, 60 and 25 words.'},indent=2))
print(str(O))
