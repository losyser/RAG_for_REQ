"""Read-only historical checks and unlabelled preparation. No experiment imports or calls."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('local_review_server', HERE / 'server.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
BASELINE = '74ee5651974dccc0468367396ebc2179cced3e25'
FROZEN = 'b5ed0ca6eedf82d9f88f35652510669996a39677'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def by_id(rows, key):
    result = {r[key]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate source IDs')
    return result

def pairs(items):
    result = {tuple(x) for x in items}
    if len(result) != len(items):
        raise ValueError('Duplicate prediction pairs')
    return result

def source_library(package):
    result = {k: package[k] for k in ('components', 'intents', 'taxonomy', 'sources')}
    result.update(format='mapping-review-source-library-v1', not_an_assignment=True,
                  purpose='Unlabelled reference only; not a requirement to review all 60 sources')
    result['version'] = review.digest(result)
    return result

def prepare(project, snapshot, output):
    if output.exists():
        raise FileExistsError('Refusing to overwrite existing preparation directory')
    rels = {
        'predictions': 'data/search_results/exp_v4/e1_predictions.json',
        'pool': 'data/search_results/exp_v4/e1_pool.csv',
        'v3': 'data/search_results/exp_v3/rag_v3_results.json',
        'v4': 'data/search_results/exp_v4/rag_v4_results.json',
        'source': 'data/processed/original_requirements_v2.jsonl',
        'kb': 'data/processed/evidence_units_v3_audited.jsonl',
        'taxonomy': 'cooling_rag_mg/evidence_taxonomy.py',
        'analyzer': 'cooling_rag_mg/requirement_analyzer.py',
        'config': 'cooling_rag_mg/config.py',
        'stage1_script': 'scripts/54_run_pipelines_v3.py',
        'v4_script': 'scripts/77_run_v4_rag.py',
        'refill_script': 'scripts/107_fill_truncated_sets.py',
        'rerun_script': 'scripts/96_rerun_postaudit.py',
        'log': 'logs/rerun_postaudit_20261015_0129.log',
    }
    paths = {k: project / v for k, v in rels.items()}
    predictions = read_json(paths['predictions'])
    v3 = by_id(read_json(paths['v3'])['result_sets'], 'source_requirement_id')
    v4 = by_id(read_json(paths['v4'])['result_sets'], 'source_requirement_id')
    sources = by_id([json.loads(line) for line in paths['source'].read_text(encoding='utf8').splitlines() if line.strip()], 'requirement_id')
    kb = {json.loads(line)['id'] for line in paths['kb'].read_text(encoding='utf8').splitlines() if line.strip()}
    ids = sorted(sources)
    if len(ids) != 60 or set(v3) != set(ids) or set(v4) != set(ids):
        raise ValueError('Unexpected source frame')
    if set(predictions) != {'deepseek', 'qwen', 'bm25', 'embed'}:
        raise ValueError('Unexpected method set')
    if any(set(method) != set(ids) for method in predictions.values()):
        raise ValueError('Incomplete prediction source frame')
    package = review.build_assignment(project, ','.join(ids), 'reference-library-only', 'pilot')
    pool_sources = {s['id']: s for s in package['sources']}
    logged = {}
    current = None
    log_text = paths['log'].read_text(encoding='utf8')
    initial_output_match = re.search(r'^总 shall 数:\s*(\d+)\s*$', log_text, re.MULTILINE)
    if initial_output_match is None or int(initial_output_match[1]) != 409:
        raise ValueError('Unexpected initial v4 output count in historical log')
    for line in log_text.splitlines():
        match = re.match(r'^\[\s*\d+/60\]\s*(OR\d+):', line)
        if match:
            current = match[1]
            if current in logged:
                raise ValueError('Repeated source header in mapping log')
            logged[current] = []
        match = re.match(r'^\s*\(([a-z_]+)\s*×\s*([a-z_]+)\)', line)
        if match:
            if current is None:
                raise ValueError('Mapping pair before source header')
            logged[current].append((match[1], match[2]))
    if set(logged) != set(ids):
        raise ValueError('Incomplete historical log mapping')
    per_source = []
    for sid in ids:
        archived = pairs([p.split('×') for p in v3[sid]['_pairs_used']])
        predicted = {method: pairs(data[sid]) for method, data in predictions.items()}
        merged = set().union(*predicted.values())
        pool = {(p['component'], p['intent']) for p in pool_sources[sid]['candidates']}
        evidence = {eid for er in v3[sid]['engineering_requirements'] for eid in er.get('evidence_ids', []) if eid in kb}
        timings = {k: v3[sid]['_timing'][k] == v4[sid]['_timing'][k] for k in ('stage1_s', 'retrieval_s', 'selection_s')}
        checks = {
            'deepseek_equals_archived_v3': predicted['deepseek'] == archived,
            'log_equals_archived_v3': pairs(logged[sid]) == archived,
            'pool_equals_four_method_union': pool == merged,
            'pool_source_text_equals_original': pool_sources[sid]['text'] == sources[sid]['requirement_text'],
            'v4_evidence_equals_filtered_v3_citation_union': set(v4[sid]['_evidence_values']) == evidence,
            'v4_evidence_count_matches': v4[sid]['_n_evidence'] == len(evidence),
            'v4_has_no_pairs_used': '_pairs_used' not in v4[sid],
            **{'timing_equal_' + k: v for k, v in timings.items()},
        }
        per_source.append({'source_id': sid, 'checks': checks, 'candidate_count': len(pool),
                           'mapping_count': len(archived), 'method_counts': {k:len(v) for k,v in predicted.items()},
                           'v4_evidence_count': len(evidence), 'v4_output_count': len(v4[sid]['engineering_requirements']),
                           'refilled': '_refilled_max_tokens' in v4[sid]})
    if not all(all(row['checks'].values()) for row in per_source):
        raise ValueError('Historical per-source verification failed')
    files = []
    for key, rel in rels.items():
        row = {'role': key, 'path': rel, 'sha256': sha(paths[key])}
        # Log may be untracked; no claim of frozen-byte equality for it.
        if key != 'log':
            frozen_bytes = subprocess.check_output(['git', '-C', str(snapshot), 'show', FROZEN + ':project/' + rel])
            row['frozen_sha256'] = hashlib.sha256(frozen_bytes).hexdigest()
            row['equals_frozen'] = row['sha256'] == row['frozen_sha256']
            if not row['equals_frozen']:
                raise ValueError('Frozen input mismatch: ' + rel)
        files.append(row)
    counts = {sid: len(pool_sources[sid]['candidates']) for sid in ids}
    median = statistics.median(counts.values())
    pilot_ids = [next(sid for sid in ids if counts[sid] == median), next(sid for sid in ids if counts[sid] == max(counts.values()))]
    if pilot_ids != ['OR002', 'OR001']:
        raise ValueError('Pilot workload rule changed; review protocol before generating')
    pilot = review.build_assignment(project, ','.join(pilot_ids), 'S2-calibration-v1-exclude-formal', 'pilot')
    total = sum(row['v4_output_count'] for row in per_source)
    if total != 513 or sum(counts.values()) != 570:
        raise ValueError('Unexpected frozen output or candidate count')
    report = {
        'status': 'verified-historical-upstream-only; no accuracy score or new model run',
        'preparation_baseline': BASELINE, 'paper_frozen_commit': FROZEN,
        'source_count': len(ids), 'candidate_count': sum(counts.values()), 'mapping_count': sum(len(x) for x in logged.values()),
        'taxonomy': {'components': len(package['components']), 'declared_intent_labels': 45,
                     'display_intent_labels': len(package['intents']),
                     'labels_from_original_line_comments': {k:v for k,v in package['intents'].items() if v.startswith('[原目录')},
                     'legal_pairs': sum(len(v) for v in package['taxonomy'].values())},
        'v4_initial_logged_output_count': int(initial_output_match[1]),
        'v4_final_output_count': total, 'refilled_sources': [r['source_id'] for r in per_source if r['refilled']],
        'pilot_ids': pilot_ids, 'pilot_selection': 'Lexicographic first at median and maximum candidate count; purposive timing only; excluded from formal scoring',
        'formal_sample_selected': False, 'expert_answers_created': False,
        'files': files, 'per_source': per_source,
        'limitations': ['v4 does not save _pairs_used; upstream reuse is evidenced by source code, logged pairs, evidence unions and copied timings.',
                       'Historical run logged 409 initial v4 outputs; script 107 refill explains current 513. This is not a new 513-output Stage 1 run.',
                       'Raw historical model responses/resolved provider model revision are not retained; API alias alone does not establish exact remote model reproducibility.',
                       'No gold, precision, recall, F1 or formal random sample is produced. Existing full-workbook scorer is not a validated four-state/subsample scorer.']}
    output.mkdir(parents=True)
    expert = output / 'expert_packet'; expert.mkdir()
    coordinator = output / 'coordinator'; coordinator.mkdir()
    for name in ('RULES_ZH.md', 'RULES_EN_DRAFT.md', 'START_HERE_ZH.md'):
        shutil.copy2(HERE / 'material_templates' / name, expert / name)
    shutil.copy2(HERE / 'material_templates/LIMITED_SOURCE_PROTOCOL_DRAFT.md', coordinator / 'LIMITED_SOURCE_PROTOCOL_DRAFT.md')
    def write_json(path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    write_json(expert / 'calibration_2_sources.pilot.json', pilot)
    write_json(coordinator / 'source_library_unlabelled.json', source_library(package))
    write_json(coordinator / 'UPSTREAM_VERIFICATION.json', report)
    with (expert / 'calibration_timing_blank.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['reviewer_code', 'source_id', 'total_minutes', 'completed_yes_no', 'interruption_minutes', 'questions'])
        for sid in pilot_ids: writer.writerow(['', sid, '', '', '', ''])
    (coordinator / 'UPSTREAM_PROVENANCE.md').write_text('''# 历史上游映射溯源（本轮只读验证）

结论：现存 DeepSeek 映射是 v4 实际复用的历史 Stage 1 上游，配对保存在 v3 文件中。可以对这个历史映射做后续补充评价；不能称为本轮重跑 v4 的性能，也不能在独立参考集尚缺时声称准确率或 F1。

## 已逐源核验

- 60/60 源：e1_predictions 中 DeepSeek 配对、v3 的 _pairs_used 与历史日志配对完全一致，共 250 对。
- 60/60 源：v4 的 _evidence_values 键等于 v3 生成结果引用的 evidence_ids 并集（限冻结 KB 内）；stage1_s/retrieval_s/selection_s 三项分别完全一致。
- 60/60 源：候选池等于 DeepSeek、Qwen、BM25、embedding 四方法预测并集，共570对；源文本与原始中文一致。完整 taxonomy 为21组件、183合法配对。原说明字典45项，但合法配对还引用14个字典缺失的意图ID；任务包从原文件行注释补充显示说明，合计59个显示条目，不更改任何合法配对或原始分类文件。
- scripts/77_run_v4_rag.py 直接读取 v3，复用其证据并复制上游计时，没有重新调用映射器。v4 未保存 _pairs_used 不等于它没有可追溯的历史上游。
- 初始日志记录409条 v4 输出；scripts/107_fill_truncated_sets.py 保留上游证据/计时并补生成空集合，当前513条，补生成源为 OR001、OR003、OR010、OR011、OR013、OR032。未将初始409条日志冒称为513条运行。
- JSON 列出的13个输入/脚本均与论文冻结提交 b5ed0ca 对应 project/ 文件逐字节一致；日志单独记录 SHA256，不宣称其包含于冻结提交。

## 可复核证据与边界

UPSTREAM_VERIFICATION.json 保存每个文件哈希、冻结版本哈希及60源逐项布尔检查、候选/预测数量和补生成标记。准备前检查点为74ee565。本次脚本只读 JSON/CSV/日志、静态解析 taxonomy 和读取 Git 对象；不导入项目实验模块、不运行模型。

历史原始模型响应及服务端实际模型修订未保存，不能仅凭 API 别名保证远程模型复现。两源试做 OR002/OR001 仅依候选工作量选取，用来测时并排除正式计分。没有正式抽样、没有专家答案、没有新增评分。

专家材料与协调者溯源分目录保存。专家任务包无方法身份或逐方法预测；四方法合并候选仍有提示效应，因此先锁定独立首轮判断再显示候选，并进行完整目录查漏。旧工作簿评分脚本尚不能直接承担本工具四态/有限源评分。
''', encoding='utf8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.project, args.snapshot, args.output)
    print(json.dumps({'output': str(args.output), 'sources_verified': len(result['per_source']), 'formal_sample_selected': False}))
