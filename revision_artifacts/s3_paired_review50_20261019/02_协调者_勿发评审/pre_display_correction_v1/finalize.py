"""Freeze derived analysis artifacts once, without changing the frozen sample/protocol."""
import csv,json,shutil
from datetime import datetime,timezone
from pathlib import Path
import analyze as a
H=a.HERE;C=a.COORD;E=H/'outputs/01a13537-s3/01_仅此目录可发评审'
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    freeze=C/'ANALYSIS_FREEZE.json'
    if freeze.exists():raise SystemExit('Already frozen; refusing overwrite')
    inspection=E/'数值候选独立评分.xlsx.inspect.ndjson'
    if inspection.exists():shutil.move(str(inspection),str(C/'artifact_export.inspect.ndjson'))
    dump(C/'WORKBOOK_CONTRACT.json',a.contract(E/'数值候选独立评分.xlsx'))
    stage2=C/'03_首判提交后才可发';stage2.mkdir(exist_ok=True)
    with (stage2/'可选出处猜测.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['盲ID','猜测来源（RAG/noRAG/无法判断）','理由（可选）'])
        writer.writerows([r['blind_id'],'',''] for r in a.read(C/'SAMPLE_FROZEN.json'))
    (stage2/'发放限制.txt').write_text('仅在该评审提交独立第一阶段评分原文件之后，才可另行提供此可选猜测表。\n不要发送协调者映射、候选池或抽样文件。不得用猜测修改首判；首判原件须单独保留。\n',encoding='utf8')
    (C/'分析使用说明.txt').write_text('本目录含解盲信息，勿发评审。当前只有空白模板，无真实评分结果。\n'
      '每位评审单独从同一空白模板另存；保留提交原件并计算SHA256，不覆盖。至少一位外部非作者领域评审仍待落实；共同作者须单列。\n'
      '时间须含时区，例如2026-10-20T09:00:00+08:00（示例，不是默认填写值）。先进行非样本定义校准，再估计工时。\n'
      '在本任务根目录，用安装openpyxl的Python运行：\n'
      'python -E -B analyze.py "首判甲.xlsx" --out review_results/甲_首次.json\n'
      'python -E -B analyze.py "首判甲.xlsx" "首判乙.xlsx" --out review_results/双评审_首次.json\n'
      '结果只能写入新文件；空表、不完整表、原文/盲ID变动、公式、非独立首判均阻塞。身份声明只能核查完整性，不能自动证明真实性。具体依据仅检查非空，内容充分性须人工核查。\n'
      '主指标为20源等权配对的正确且适用率差；次指标允许可接受。条目率仅描述；未知保留并给反向极端界限。源bootstrap仅探索性；符号检验无效能或等效性主张。\n'
      '两份完整独立首判且不同评审代号才计算一致性/kappa；讨论后共识不得混入。可选出处猜测材料仅在首判提交后另发。\n'
      '只省略非技术元数据，技术型号/典型/示例措辞不改，无法保证完全盲法。当前没有完备中立证据包；评审同等独立查原文，必要时保留未知。\n',encoding='utf8')
    files=[H/n for n in ['analyze.py','test_review.py','build_workbook.mjs','render_html.mjs','blind_input.json','guide.json','reader_rows.json']]
    files += [p for p in C.rglob('*') if p.is_file() and p.name not in ['ANALYSIS_FREEZE.json','VALIDATION_REPORT.json']]
    files += [p for p in E.rglob('*') if p.is_file()]
    dump(freeze,{'version':'S3-analysis-v1','frozen_before_ratings_utc':datetime.now(timezone.utc).isoformat(),'real_ratings_present':False,'files':{p.relative_to(H).as_posix():a.sha(p) for p in sorted(files)}})
    print('Frozen analysis and blank expert materials; no human results computed.')
if __name__=='__main__':main()
