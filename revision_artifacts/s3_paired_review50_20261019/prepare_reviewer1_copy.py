"""Make an analysis copy of reviewer 1's returned workbook (原件不改).

Coordinator actions, all recorded in review_results/reviewer1_provenance.json:
  1. Clear accidental '136' fill in blank separator rows of 完整原文 (contract cells only).
  2. Fill identity fields with values relayed by the corresponding author on 2026-10-20.
  3. Start/end time were not recorded; left blank (handled as a declared deviation by
     run_reviewer1.py, not invented).
"""
import hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
import openpyxl

HERE = Path(__file__).resolve().parent
SRC = Path('/mnt/c/Users/yando/Desktop/S3数值独立盲评50条_20261019_1610/01_仅此目录可发评审/评审表修改版.xlsx')
OUT_DIR = HERE / 'review_results'
DST = OUT_DIR / 'reviewer1_first_pass_analysis_copy.xlsx'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

IDENTITY = {  # row -> value, relayed by the corresponding author
    7: '外部非作者领域评审',
    8: '轮机工程',
    9: '外部公司工程人员（表中原填写：专业硕士研究生）',
    10: '无',
    11: '是',
    12: '独立首判',
}


def strip_dimension(path):
    """openpyxl adds <dimension>; the returned original has none, and the frozen
    contract compares read-only max_row/max_column (None). Remove it to match."""
    import re, zipfile
    tmp = path.with_suffix('.tmp')
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith('xl/worksheets/sheet'):
                data = re.sub(rb'<dimension [^>]*/>', b'', data)
            zout.writestr(item, data)
    tmp.replace(path)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    if DST.exists():
        raise SystemExit('analysis copy exists; refusing overwrite')
    contract = json.loads((HERE / '02_协调者_勿发评审/WORKBOOK_CONTRACT.json').read_text(encoding='utf8'))
    expected = contract['完整原文']['cells']
    shutil.copy2(SRC, DST)
    wb = openpyxl.load_workbook(DST)
    ws = wb['完整原文']
    cleared = []
    for row in ws.iter_rows():
        for c in row:
            if c.coordinate not in expected and c.value not in (None, ''):
                if str(c.value) != '136':
                    raise SystemExit(f'unexpected non-contract content {c.coordinate}={c.value!r}')
                cleared.append(c.coordinate)
                c.value = None
    ids = wb['身份与说明']
    before = {r: ids.cell(r, 2).value for r in IDENTITY}
    for r, v in IDENTITY.items():
        ids.cell(r, 2).value = v
    wb.save(DST)
    strip_dimension(DST)
    prov = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_workbook': str(SRC), 'source_sha256': sha(SRC),
        'analysis_copy': DST.name, 'analysis_copy_sha256': sha(DST),
        'ratings_sheet_changed': False,
        'cleared_separator_cells_value_136': cleared,
        'identity_before': before, 'identity_after': IDENTITY,
        'identity_source': 'Relayed by corresponding author 2026-10-20: external company expert, marine engineering, no prior exposure, independent first pass.',
        'self_revision': 'Reviewer revised K288080 from 正确 to 无法判断 on own re-check before any unblinding (earlier file 数值候选独立评分.xlsx, basis column empty, kept unchanged).',
        'earlier_file_sha256': sha(SRC.with_name('数值候选独立评分.xlsx')),
        'time_fields': 'not recorded; left blank by decision of corresponding author',
    }
    (OUT_DIR / 'reviewer1_provenance.json').write_text(json.dumps(prov, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: prov[k] for k in ['source_sha256', 'analysis_copy_sha256']}, indent=2), len(cleared), 'cells cleared')


if __name__ == '__main__':
    main()
