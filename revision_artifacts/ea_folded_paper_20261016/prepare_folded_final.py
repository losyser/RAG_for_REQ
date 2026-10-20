from pathlib import Path
import sys,json,hashlib
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');sys.path.insert(0,str(R))
from cooling_rag_mg.ea_presentation import presentation_xml,fresh_ids
from cooling_rag_mg.ea_ui_export import native_exporter
O=R/'revision_artifacts/ea_folded_paper_20261016';a=(R/'revision_artifacts/ea_structure_native_final_20261016/ea_native_sel_structure.xml').read_text(encoding='utf-8')
cases=[('folded_all',None,()),('paper_overview',['OR008','OR008.1','OR008.5','OR008.8'],()),('detail_b',['OR008','OR008.1'],['OR008','OR008.1']),('detail_c',['OR008','OR008.8'],['OR008','OR008.8'])]
manifest=[]
for case,visible,expanded in cases:
 b=presentation_xml(a,native_exporter().GRADE_STYLE,visible_ids=visible,expanded_ids=expanded,name='REQ_'+case)
 b,m=fresh_ids(b);b=b.replace(' 01_Requirements','Presentation_'+case)
 p=O/(case+'.xml');assert not p.exists();p.write_text(b,encoding='utf-8')
 (O/(case+'_guid_map.json')).write_text(json.dumps(m,indent=2))
 manifest.append({'case':case,'visible':visible or 'all 23','expanded':expanded,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Created four new independent packages')
