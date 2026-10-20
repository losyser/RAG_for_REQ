from pathlib import Path
import sqlite3,json,xml.etree.ElementTree as E
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');O=R/'revision_artifacts/ea_paper_v3_20261016';old=R/'revision_artifacts/ea_status_alignment_v2_20261016'
a=sqlite3.connect((old/'111_before_status_v2.qea').as_uri()+'?mode=ro',uri=True);stages=[]
for name in ['status_v2_cn98_rule','status_v2_cn98_support','status_v2_en23_rule','status_v2_en23_support']:
 root=E.fromstring((old/('native_'+name)/'diagrams.xml').read_text(encoding='utf-8-sig'));changed=[]
 for r in root.iter('Row'):
  did=int(r.findtext('Diagram_ID'));row=a.execute('select StyleEx from t_diagram where Diagram_ID=?',(did,)).fetchone()
  if row and row[0]!=(r.findtext('StyleEx') or ''):changed.append(did)
 stages.append({'stage':name,'old_diagrams_style_differing_from_backup':changed})
(O/'audit/prior_save_investigation.json').write_text(json.dumps({'stages':stages,'conclusion':'Differences already present after first ImportPackageXMI readback; cache/auto-save association, exact user-edit versus EA automatic source cannot be attributed retrospectively. V3 avoids ImportPackageXMI/SaveAllDiagrams and verifies all old rows unchanged.'},indent=2));print(stages)
