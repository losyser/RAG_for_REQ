from pathlib import Path
import sqlite3,json,hashlib
R=Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
src=R/'revision_artifacts/ea_native_followup_20261016/111.qea'
out=R/'revision_artifacts/ea_english_small_figures_20261016/native_acceptance_111';out.mkdir(exist_ok=False)
dst=out/'111_before_english_import.qea'
with sqlite3.connect(src.as_uri()+'?mode=ro',uri=True) as live,sqlite3.connect(dst) as backup:
 live.backup(backup)
 assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 tables={r[0]:backup.execute('SELECT COUNT(*) FROM "'+r[0]+'"').fetchone()[0] for r in backup.execute("SELECT name FROM sqlite_master WHERE type='table'")}
info={'original':str(src),'backup':str(dst),'sqlite_integrity':'ok','backup_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'table_counts':tables}
(out/'backup_record.json').write_text(json.dumps(info,indent=2));print(dst)
