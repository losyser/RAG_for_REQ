"""Local allowlisted S3 archive; no network or model calls."""
import json, hashlib, shutil, html, re, subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parents[1]; R=ROOT/'revision_artifacts'
F=R/'s3_paired_review50_20261019'; C=F/'02_协调者_勿发评审'
P=R/'s3_posthoc_exploratory_20261020'
A=H/'S3_50_完整实验归档_20261020'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def dump(p,d):put(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
origins={}
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    assert sha(src)==sha(dst);origins[str(dst.relative_to(A))]=str(src)
def render(md):
    blocks=[];table=False;code=False
    def inline(s):
        s=html.escape(s)
        s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s)
        return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    for line in md.splitlines():
        if line.startswith('```'):
            blocks.append('</pre>' if code else '<pre>');code=not code;continue
        if code:blocks.append(html.escape(line)+'\n');continue
        if line.startswith('|'):
            if re.match(r'^\|[\s:|-]+\|$',line):continue
            if not table:blocks.append('<div class="scroll"><table>');table=True
            blocks.append('<tr>'+''.join('<td>'+inline(x.strip())+'</td>' for x in line.strip('|').split('|'))+'</tr>');continue
        if table:blocks.append('</table></div>');table=False
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));blocks.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>')
        elif line.strip():blocks.append('<p>'+inline(line)+'</p>')
    if table:blocks.append('</table></div>')
    return '<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>S3 完整实验归档</title><style>body{font:17px/1.8 system-ui,"Microsoft YaHei";max-width:1100px;margin:40px auto;padding:0 24px;color:#203046;background:#f7f9fc}h1,h2,h3{line-height:1.4;color:#163d65}h2{border-top:2px solid #ccd9e5;padding-top:24px}p{overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;background:white}td{padding:10px;border:1px solid #d6dfe8;vertical-align:top}tr:first-child{font-weight:bold;background:#e5eef8}.scroll{overflow-x:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e9eef4;padding:16px}a{color:#075f9d}code{font-size:.88em}</style><body>'+''.join(blocks)+'</body></html>'

def main():
    A.mkdir(exist_ok=True)
    rp=A/'02_协调者_勿发评审/复现项目/revision_artifacts'
    freeze=read(C/'ANALYSIS_FREEZE.json')
    for rel,digest in freeze['files'].items():
        assert sha(F/rel)==digest,rel
        copy(F/rel,rp/F.name/rel)
    copy(C/'ANALYSIS_FREEZE.json',rp/F.name/'02_协调者_勿发评审/ANALYSIS_FREEZE.json')
    for name in ['prepare.py','DELIVERY_REPORT.md']:
        copy(F/name,rp/F.name/name)
    expert=F/'outputs/01a13537-s3/01_仅此目录可发评审'
    for p in expert.iterdir():
        if p.is_file():copy(p,A/'01_可发评审_原始材料'/p.name)
    for name in ['s3_return_technical_cleanup_20261020','s3_posthoc_exploratory_20261020']:
        source=R/name
        for p in source.rglob('*'):
            rel=p.relative_to(source)
            if p.is_file() and not any(x in rel.parts for x in ['private_tests','__pycache__','previews']) and p.suffix in ['.py','.json','.md','.csv','.xlsx','.txt'] and not p.name.startswith(('GIT_STATUS','PROTECTED_')):
                copy(p,rp/name/rel)
    for version,folder in [('v1','s3_return_analysis_20261020'),('v2','s3_return_analysis_20261020_v2'),('v3','s3_return_analysis_20261020_v3')]:
        for p in (R/folder/'raw').glob('*.xlsx'):copy(p,A/'02_协调者_勿发评审/原始返表'/version/p.name)
        for p in (R/folder).iterdir():
            if p.is_file() and p.suffix in ['.json','.md','.txt'] and not p.name.startswith(('PROTECTED','GIT_STATUS')):
                copy(p,A/'02_协调者_勿发评审/版本与审计'/version/p.name)
    ref=R/'s3_reference_supplement_20261020'
    for folder in ['02_工作记录_不发评审','04_修订记录_v2_不发评审']:
        for p in (ref/folder).glob('*.json'):
            if not p.name.startswith(('PROTECTED','GIT_STATUS')):copy(p,A/'03_资料来源索引/程序与修订记录'/folder/p.name)
    catalog=read(ref/'03_中性查证资料_v2/来源与版本清单.json')
    source_md='# 原版资料索引（PDF 不随包）\n\n此包只供本地研究归档，不是公开发布包。25 个文件、24 个独立 PDF；保留官方 URL、版本、哈希和原始本地位置。迁移电脑后本地链接可能失效，官方链接也可能变更；索引不保证资料支持候选数值。\n'
    for i,x in enumerate(catalog,1):
        local=(ref/'03_中性查证资料_v2'/x['file']).resolve()
        assert sha(local)==x['sha256']
        x['external_original_local_path']=str(local)
        source_md+=f"\n## {i}. {x['title']}\n\n版本：{x.get('version','')}；出版者：{x.get('publisher','')}；页数：{x.get('pages','')}。\n\n适用范围：{x.get('scope','')}\n\n[官方来源或出版者入口]({x.get('url','')})；[本机原版 PDF]({local.as_uri()})。\n\n本地路径：`{local}`\n\nSHA256：`{x['sha256']}`\n\n链接限制：{x.get('local_url_limit','') or '见来源记录；未重新联网验证。'}\n"
    dump(A/'03_资料来源索引/原版资料索引.json',catalog)
    put(A/'03_资料来源索引/原版资料索引.md',source_md)
    put(A/'03_资料来源索引/原版资料索引.html',render(source_md))
    result=read(P/'delivery/EXPLORATORY_RESULT.json')
    samples={x['blind_id']:x for x in read(C/'SAMPLE_FROZEN.json')}
    report=(H/'REPORT_SOURCE.md').read_text(encoding='utf-8')
    nature={'K783304':'未找到统一强制依据；证据不足，不等于已经证明参数错误。','K522557':'适用性和试验对象未确认；背景条文不足以直接反证全部数值。','K849074':'评审指出表格分隔符被误读为负号；其余温区仍需逐项核验。','K997682':'进水设计值与出水报警/降额混用，含不匹配判断及待核对部分。','K189805':'排气温度/流量容差套用于冷却系统，属于对象错配。','K204711':'评审指出预热表格中的连接符被误读为 −100°C。','K814606':'approximately 0.5 bar 被写成 ≤0.5 bar，近似值变成硬上限。','K797131':'≤1秒缺少依据；手动确认/复位要求与报警消音、视觉保持规则存在混淆。','K445671':'持续超过1秒被改成1秒内响应，并从泄漏要求偏移到温度条件。'}
    report+='\n## 7. 九条“错误”标签的逐条追溯\n\n下列保留评审最终标签，性质说明仅区分“明确冲突主张”与“支持证据不足”，不重新评分、不将每条均称为已证伪。候选原字段完整列出，数字相同不等于语义支持。\n'
    cases=[]
    for row in result['raw_ratings']:
        if row['blind_id'] not in nature:continue
        s=samples[row['blind_id']];cases.append({'sample':s,'review':row,'diagnostic_nature':nature[row['blind_id']]})
        report+=f"\n### {row['blind_id']} · {row['arm']} · {s['source_id']} · 原结果行 {s['row_1based']}\n\n原需求：{s['original_requirement']}\n\n候选内容：\n\n```json\n{json.dumps(s['candidate'],ensure_ascii=False,indent=2)}\n```\n\n评审依据（原文）：{row['basis']}\n\n评审备注（原文）：{row['note']}\n\n判断性质：{nature[row['blind_id']]}\n\n适用性标签：{row['applicability']}；置信度：{row['confidence']}。\n"
    assert len(cases)==9
    dump(A/'02_协调者_勿发评审/九条错误标签追溯.json',cases)
    report+='\n'+(H/'REPORT_END.md').read_text(encoding='utf-8')
    put(A/'总报告.md',report);put(A/'总报告.html',render(report));put(H/'总报告.md',report)
    entry='# S3 · 50 条数值候选完整实验归档\n\n归档日期：2026-10-20。协调者内部资料；包含解盲映射与评分，不能整包发送评审或公开发布。\n\n[阅读完整实验报告](总报告.html)\n\n[原版资料索引（PDF 不随包）](03_资料来源索引/原版资料索引.html)\n\n[复现说明](04_复现与文件索引/复现说明.md)\n\n[文件索引](04_复现与文件索引/文件索引.html)\n\n`01_可发评审_原始材料` 仅保留原始空白表、原文阅读页与说明。其余目录、总报告和此入口均属于协调者内部资料。\n\n状态：报告内容已汇总；打包与复现的最终结果请查看 `04_复现与文件索引/VERIFICATION.json`。没有该文件时不得视为已完成全部核验。\n'
    put(A/'00_开始阅读.html',render(entry))
    deps='Python 3.11.15\nopenpyxl==3.1.5\n标准库：json, csv, hashlib, pathlib, random, math, statistics, zipfile, unittest 等。\n无需模型 API、密钥、联网或重新生成候选。\n'
    put(A/'04_复现与文件索引/依赖说明.txt',deps)
    commands='''# 本地复现

在解压后的 `02_协调者_勿发评审/复现项目` 目录中使用 Python 3.11 与 openpyxl 3.1.5：

```powershell
python -B revision_artifacts/s3_posthoc_exploratory_20261020/explore.py --out revision_artifacts/s3_posthoc_exploratory_20261020/private_tests/replay
python -B -m unittest discover -s revision_artifacts/s3_posthoc_exploratory_20261020 -p test_acceptance.py
```

输出路径必须尚不存在。生成 JSON 应与归档 delivery/EXPLORATORY_RESULT.json 完全相等；不调用 API。原始冻结 analyze.py 的流程验收仍会拒绝缺失身份/时间信息，这是保留的限制，并非此包缺陷。探索性入口是显式事后修订。

冻结的输入、候选池、样本、抽样种子、原始行号、分类器、协议和原分析脚本均在 s3_paired_review50_20261019/02_协调者_勿发评审。prepare.py 和工作簿生成脚本为历史方法记录，包含原项目路径依赖；不要用它们覆盖已冻结样本。此包支持评分统计与验收测试的离线重放，不宣称能重建当时模型输出或搜索服务结果。

SHA256SUMS.json 覆盖除其自身以外的文件；ZIP 的 SHA256 另在交付侧记录。正式提交号见最终交付说明；包内 GIT_HISTORY.txt 记录构建前历史，避免自指哈希。
'''
    put(A/'04_复现与文件索引/复现说明.md',commands)
    history=subprocess.check_output(['git','log','-25','--format=%h %aI %s'],cwd=ROOT).decode('utf-8')
    put(A/'04_复现与文件索引/GIT_HISTORY.txt',history)
    dump(H/'COPY_ORIGINS.json',origins)
    print(str(A/'00_开始阅读.html'))
if __name__=='__main__':main()
