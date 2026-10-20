from pathlib import Path
import sqlite3,shutil,hashlib,json
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular');O=R/'revision_artifacts/ea_paper_v3_20261016';O.mkdir(exist_ok=False)
with sqlite3.connect((R/'revision_artifacts/ea_native_followup_20261016/111.qea').as_uri()+'?mode=ro',uri=True) as a,sqlite3.connect(O/'111_before_v3.qea') as b:a.backup(b);assert b.execute('pragma integrity_check').fetchone()[0]=='ok'
for name in ['cooling_rag_mg/ea_paper_figures.py','cooling_rag_mg/ea_status_view.py','ui/pages/engineering.py','tests/test_ea_english_paper.py']:
 p=O/'code_before'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
(O/'data_hashes_before.json').write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'data').rglob('*') if p.is_file() and p.suffix in ['.xml','.json','.jsonl']},indent=2))
print(O)
