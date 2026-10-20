"""Local-only input freeze. Search input is reconstructed solely from reviewer-facing cells."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
import openpyxl
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
AUDIT=H/'02_工作记录_不发评审';PACK=H/'01_中性查证资料'
OLD=ROOT/'revision_artifacts/s3_paired_review50_20261019'
E=OLD/'outputs/01a13537-s3/01_仅此目录可发评审'
D=Path('C:/Users/yando/Desktop/S3数值独立盲评50条_20261019_1610')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf8').strip()
def main():
    assert not (AUDIT/'PREFLIGHT.json').exists(),'Do not overwrite baseline'
    AUDIT.mkdir(parents=True);PACK.mkdir();now=datetime.now(timezone.utc).isoformat()
    dirty=git('diff','--name-only').splitlines();saved=H/'private_checkpoint'
    for n in dirty:
        dest=saved/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dest)
    (saved/'worktree.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=ROOT))
    # Only reviewer-facing original columns enter the search input. No keys/arm labels read.
    wb=openpyxl.load_workbook(E/'数值候选独立评分.xlsx',read_only=True);cards={}
    for code,label,text in wb['完整原文'].iter_rows(min_row=6,values_only=True):
        if code:
            field=re.sub(r'（\d+/\d+）$','',label);cards.setdefault(code,{});cards[code][field]=cards[code].get(field,'')+(text or '')
    wb.close();assert len(cards)==50;dump(AUDIT/'REVIEWER_VISIBLE_INPUT.json',cards)
    # Baseline only hashes existing research files; does not inspect evidence keys or ratings.
    paths=list(p for p in OLD.rglob('*') if p.is_file() and not any(x in p.parts for x in ['node_modules','test_outputs','checkpoint_worktree','__pycache__']))
    paths+=list(p for p in D.rglob('*') if p.is_file())
    for base in [ROOT/'data',ROOT.parent/'resubmission_4762284_20261019/texpage_source_4762284']:
        paths+=list(p for p in base.rglob('*') if p.is_file())
    paths+=[ROOT/n for n in dirty]
    dump(AUDIT/'PROTECTED_BEFORE.json',{str(p):sha(p) for p in sorted(set(paths))})
    forms=[]
    for base in [E,D/'01_仅此目录可发评审']:
        for p in base.glob('*.xlsx'):
            w=openpyxl.load_workbook(p,read_only=True,data_only=False)
            forms.append({'path':str(p),'sha256':sha(p),'rating_nonempty':sum(w['评分50'].cell(i,j).value is not None for i in range(6,56) for j in range(2,7)),'identity_nonempty':sum(w['身份与说明'][f'B{i}'].value is not None for i in range(6,15)),'identity_values_not_read_or_disclosed':True});w.close()
    dump(AUDIT/'PREFLIGHT.json',{'utc':now,'git_head':git('rev-parse','HEAD'),'checkpoint_branch':'checkpoint/before-s3-reference-supplement-20261020','dirty_hashes':{n:sha(ROOT/n) for n in dirty},'existing_forms':forms,'existing_edit_detected':True,'existing_scored_cells_in_inspected_forms':0,'scope_limit':'Only project delivery and named desktop delivery inspected; cannot establish whether external copies were already rated. Preserve prior material condition, record supplement exposure/date and do not overwrite/regrade or mix conditions.','connection':'Official public search available; first unquoted connectivity query irrelevant, quoted official Scania query returned manual. These preflight connectivity results are not a selection rationale.','model_api_calls':0,'uploads':0})
    print('Saved baseline, user-edited workbook hashes and 50 reviewer-facing cards only.')
if __name__=='__main__':main()
