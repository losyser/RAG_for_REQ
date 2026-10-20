"""Run the frozen analyze.py logic on reviewer 1, tolerating only the unrecorded time fields.

analyze.py itself is unchanged (its hash is checked by ANALYSIS_FREEZE). The only
deviation: start/end time issues are waived and listed under protocol_deviations.
Every other validation issue still blocks.
"""
import importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('analyze', HERE / 'analyze.py')
an = importlib.util.module_from_spec(spec); spec.loader.exec_module(an)

WAIVABLE = ('身份/过程字段未填:start_time', '身份/过程字段未填:end_time', 'start_time:', 'end_time:')


def main():
    wbk = HERE / 'review_results/reviewer1_first_pass_analysis_copy.xlsx'
    out = HERE / 'review_results/reviewer1_first_pass.json'
    if out.exists():
        raise SystemExit('result exists; refusing overwrite')
    freeze = an.read(an.COORD / 'ANALYSIS_FREEZE.json')
    for name, h in freeze['files'].items():
        if an.sha(HERE / name) != h:
            raise SystemExit('Frozen analysis/input changed: ' + name)
    sample = an.read(an.COORD / 'SAMPLE_FROZEN.json')
    expected = an.read(an.COORD / 'WORKBOOK_CONTRACT.json')
    v = an.validate(wbk, expected, sample)
    waived = [i for i in v['issues'] if i.startswith(WAIVABLE)]
    blocking = [i for i in v['issues'] if i not in waived]
    if blocking:
        print(json.dumps({'status': 'blocked', 'issues': blocking}, ensure_ascii=False, indent=2)); return 2
    if waived:  # validate() withholds ratings when any issue exists; re-read them with the same rules
        import openpyxl
        ws = openpyxl.load_workbook(wbk, read_only=True)['评分50']
        by = {r['blind_id']: r for r in sample}; ratings = []
        for i in range(6, 56):
            code, c, a, basis, conf, note = [an.norm(ws.cell(i, j).value) for j in range(1, 7)]
            ratings.append({'blind_id': code, 'source_id': by[code]['source_id'], 'arm': by[code]['arm'],
                            'correctness': c, 'applicability': a, 'basis': basis, 'confidence': conf, 'note': note})
        v['ratings'] = ratings
    result = {'status': 'complete_first_pass_forms',
              'external_non_author_present': v['metadata']['role'] == '外部非作者领域评审',
              'protocol_deviations': waived,
              'reviewers': [{'metadata': v['metadata'], 'input_sha256': v['input_sha256'],
                             'raw_ratings': v['ratings'], 'summary': an.summarize(v['ratings'])}],
              'agreement': None,
              'remaining_limit': 'Single reviewer; no inter-rater agreement. Identity relayed by corresponding author, not independently authenticated.'}
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf8')
    p, s = result['reviewers'][0]['summary']['primary'], result['reviewers'][0]['summary']['secondary']
    print(json.dumps({'deviations': waived, 'primary_diff': p['source_equal_difference'], 'boot': p['source_bootstrap_percentile_interval'],
                      'bounds': p['unknown_assignment_bounds'], 'sign': p['sign_test'], 'secondary_diff': s['source_equal_difference'],
                      'secondary_boot': s['source_bootstrap_percentile_interval'], 'item': p['item_descriptive']}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
