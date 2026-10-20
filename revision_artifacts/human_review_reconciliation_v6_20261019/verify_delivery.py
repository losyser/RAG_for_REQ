"""Re-run local calculations and verify immutable inputs; no network access."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / 'qualitative_5arm_authorized_run_20261019'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf8'))

def main():
    for script, log in [('reconcile.py', 'RECONCILE_LOG.txt'), ('test_reconcile.py', 'TEST_RESULTS.txt')]:
        result = subprocess.run([sys.executable, '-E', '-B', str(HERE/script)], capture_output=True)
        (HERE/log).write_bytes(result.stdout + result.stderr)
        assert result.returncode == 0, result.stderr
    calc = next((HERE/'results').glob('*\u8ba1\u7b97.py'))
    result = subprocess.run([sys.executable, '-E', '-B', str(calc)], capture_output=True)
    assert result.returncode == 0, result.stderr
    (HERE/'results'/'\u72ec\u7acb\u590d\u7b97\u8f93\u51fa.json').write_bytes(result.stdout)
    checks = {}
    for manifest in [WORK/'ARTIFACT_HASHES_FINAL.json', WORK/'authorized_remaining330_20261019/FINAL_ARTIFACT_HASHES.json', WORK/'postrun_review_v6_20261019/FINAL_ARTIFACT_HASHES.json']:
        entries = read(manifest)
        for name, expected in entries.items():
            assert sha(manifest.parent/name) == expected, name
        checks[str(manifest)] = len(entries)
    pre = read(WORK/'RUN_PREFLIGHT.json')
    for key in ['protected_hashes', 'frozen_hashes']:
        for name, expected in pre[key].items():
            assert sha(Path(name)) == expected, name
        checks[key] = len(pre[key])
    original = next((HERE/'original').glob('*.xlsx'))
    assert sha(original) == '7b831ce37bd6d8354f84ac4ef175dee7d0e8a20d43aafbf597d03fdec315ab91'
    report = read(HERE/'results/REPORT.json')
    assert report['remaining_author_questions'] == []
    output = {'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'original_sha256': sha(original), 'new_model_calls': 0, 'tests_passed': 4, 'remaining_author_questions': []}
    (HERE/'results/FINAL_RECHECK.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
