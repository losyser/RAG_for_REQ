import hashlib, json, pathlib, shutil, subprocess
root = pathlib.Path(r'D:\cooling_rag_multigranular\cooling_rag_multigranular')
dest = pathlib.Path(r'D:\cooling_rag_multigranular\local_git_baselines\before_expert_mapping_ui_20261017')
if dest.exists():
    raise SystemExit('Snapshot destination already exists; refusing overwrite')
tracked = subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
paths = {root / p for p in tracked if p}
for directory in ('cooling_rag_mg','scripts','tests','ui','docs'):
    paths.update((root / directory).rglob('*.py'))
    paths.update((root / directory).rglob('*.md'))
paths.add(root / 'data/search_results/exp_v4/e1_pool.csv')
paths.add(root / 'revision_artifacts/audit_20261015/stage1_prediction_provenance.json')
dest.mkdir(parents=True)
manifest = []
for p in sorted(paths):
    rel = p.relative_to(root)
    if not p.is_file() or any(x in str(rel).lower() for x in ('.env','expert_key','private','__pycache__')):
        continue
    target = dest / 'project' / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(target.read_bytes()).hexdigest()
    manifest.append({'path':rel.as_posix(),'sha256':digest})
(dest/'BASELINE.json').write_text(json.dumps({'scope':'Tracked working files plus source/tests/docs and mapping input; excludes credentials/private keys. Not a full disk backup. Original Git index unchanged.','original_head':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD']).decode().strip(),'files':manifest},indent=2),encoding='utf-8')
subprocess.run(['git','init',str(dest)],check=True)
subprocess.run(['git','-C',str(dest),'add','--all'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['git','-C',str(dest),'-c','user.name=Local Review Snapshot','-c','user.email=local-snapshot@localhost','commit','-m','baseline: preserve working project before local expert mapping UI'],check=True,stdout=subprocess.DEVNULL)
print(json.dumps({'snapshot':str(dest),'file_count':len(manifest),'commit':subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD']).decode().strip()}))
