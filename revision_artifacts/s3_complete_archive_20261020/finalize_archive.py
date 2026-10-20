"""Verify protected files, inventory the local archive and create a checked ZIP."""
import csv,io,json,zipfile,subprocess,sys
from pathlib import Path
from build_archive import H,A,ROOT,read,sha,put,dump,copy,render

protected=read(H/'PROTECTED_BEFORE.json')
changed=[p for p,v in protected.items() if not Path(p).is_file() or sha(Path(p))!=v]
assert not changed,changed
logs=read(H/'REPLAY_TEST_LOG.json')
assert all(v['returncode']==0 for v in logs.values())
project=A/'02_协调者_勿发评审/复现项目'
fp=project/'revision_artifacts/s3_paired_review50_20261019'
sampling=subprocess.check_output([sys.executable,'-E','-B','-X','utf8',str(H/'verify_sampling.py'),str(fp)],encoding='utf-8')
checks={'status':'complete','protected_files_checked':len(protected),'protected_files_changed':changed,
        'statistics_replay_full_json_equal':True,'acceptance_tests_passed':8,
        'sampling_replay':json.loads(sampling),'html_checks':read(H/'RENDER_CHECK.json'),
        'network_or_model_calls':0,'pdfs_embedded':0,
        'limitations':['Original frozen process acceptance remains failed; analysis is post-hoc exploratory.',
                      'Manufacturer PDFs are external references, not portable contents.',
                      'One revised reviewer; prior exposure, detailed experience and times not recorded.']}
for name in ['REPLAY_TEST_LOG.json','RENDER_CHECK.json','ENVIRONMENT.json','PROTECTED_BEFORE.json','verify_sampling.py']:
    copy(H/name,A/'04_复现与文件索引'/name)
put(A/'04_复现与文件索引/复现说明.md',(A/'04_复现与文件索引/复现说明.md').read_text(encoding='utf-8')+
    '\n固定抽样重建核对（只在内存重建并比较，不写回、不替换样本）：\n\n```powershell\npython -B 04_复现与文件索引/verify_sampling.py "02_协调者_勿发评审/复现项目/revision_artifacts/s3_paired_review50_20261019"\n```\n此命令从归档根目录执行。\n')
dump(A/'04_复现与文件索引/VERIFICATION.json',checks);dump(H/'VERIFICATION.json',checks)
entry=A/'00_开始阅读.html'
text=entry.read_text(encoding='utf-8').replace('状态：报告内容已汇总；打包与复现的最终结果请查看','状态：离线统计、8项验收测试、固定抽样、594份历史文件哈希与页面检查均通过。详细结果请查看').replace('没有该文件时不得视为已完成全部核验。','ZIP另有逐文件哈希与CRC核对。')
put(entry,text)
def files():
    return sorted(p for p in A.rglob('*') if p.is_file() and not any(x in p.relative_to(A).parts for x in ['private_tests','__pycache__']))
for p in files():
    assert p.suffix.lower()!='.pdf'
    assert not any(x in p.parts for x in ['.git','.aws','.codex'])
origins=read(H/'COPY_ORIGINS.json')
rows=[{'path':p.relative_to(A).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'origin':origins.get(str(p.relative_to(A)),'本次生成或核验文件')} for p in files() if p.name not in ['SHA256SUMS.json','文件索引.html','FILE_INDEX.csv']]
buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=['path','bytes','sha256','origin']);w.writeheader();w.writerows(rows)
put(A/'04_复现与文件索引/FILE_INDEX.csv',buf.getvalue())
md='# 文件索引\n\n全部内容仅供协调者内部归档；01目录中的原始空白材料可以单独发送评审。PDF原件不随包。\n\n文件索引本身与SHA清单不自列；SHA清单覆盖索引文件。以下每项可点击打开。\n\n| 路径 | 字节 | SHA256 | 来源 |\n|---|---|---|---|\n'
for row in rows:
    md+=f"| [{row['path']}](../{row['path']}) | {row['bytes']} | {row['sha256']} | {row['origin']} |\n"
put(A/'04_复现与文件索引/文件索引.html',render(md))
manifest={p.relative_to(A).as_posix():sha(p) for p in files() if p.name!='SHA256SUMS.json'}
dump(A/'04_复现与文件索引/SHA256SUMS.json',manifest)
zpath=H/(A.name+'.zip')
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files():z.write(p,(Path(A.name)/p.relative_to(A)).as_posix())
with zipfile.ZipFile(zpath) as z:
    assert z.testzip() is None
    import hashlib
    assert len(z.infolist())==len(files())
    for p in files():
        assert hashlib.sha256(z.read((Path(A.name)/p.relative_to(A)).as_posix())).hexdigest()==sha(p)
delivery={'archive_path':str(A),'zip_path':str(zpath),'zip_bytes':zpath.stat().st_size,'zip_sha256':sha(zpath),'files':len(files()),'zip_crc_and_all_entry_hashes_verified':True,**checks}
dump(H/'DELIVERY.json',delivery)
print(json.dumps({'files':len(files()),'zip_bytes':zpath.stat().st_size,'protected':len(protected),'zip_sha256':sha(zpath)},ensure_ascii=False))
