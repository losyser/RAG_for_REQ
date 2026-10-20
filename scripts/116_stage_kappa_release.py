# scripts/116_stage_kappa_release.py
"""Stage the blind taxonomy-label review (R1-4.2) as a Zenodo addendum (taxonomy_kappa_review.zip).

Contents: blank workbook as sent, frozen protocol and key, build/analysis code and tests, the
reviewer's first submission (document properties cleared; labels verbatim), the frozen result
and the paper macros. Later re-entries made after preliminary results were shared are not
analysed; only their SHA-256 values are listed.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "revision_artifacts/kappa_taxonomy_review_20261020"
OUT = ROOT.parent / "release_staging_v3_20261019/taxonomy_kappa_review"
ZIP = OUT.with_suffix(".zip")
BLOCK = [re.compile(p) for p in (r"/mnt/[cd]/", r"[A-Za-z]:\\\\?Users", r"/home/\w", r"yando", r"严冬三",
                                  r"[\w.+-]+@[\w-]+\.[\w.]+")]
sha = lambda b: hashlib.sha256(b).hexdigest()


def clean_wb(path: Path) -> bytes:
    wb = openpyxl.load_workbook(path)
    wb.properties.creator = None
    wb.properties.lastModifiedBy = None
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    files = {
        "01_sent_to_reviewer/证据单元分类标注50.xlsx": (K / "delivery/01_发给评审/证据单元分类标注50.xlsx").read_bytes(),
        "02_frozen/PROTOCOL_FROZEN.json": (K / "delivery/02_协调者_勿发/PROTOCOL_FROZEN.json").read_bytes(),
        "02_frozen/SAMPLE_KEY.json": (K / "delivery/02_协调者_勿发/SAMPLE_KEY.json").read_bytes(),
        "03_code/build.py": (K / "build.py").read_bytes(),
        "03_code/analyze.py": (K / "analyze.py").read_bytes(),
        "03_code/test_kappa.py": (K / "test_kappa.py").read_bytes(),
        "04_returned/reviewer_first_submission.xlsx": clean_wb(K / "review_results/raw/reviewer1_returned.xlsx"),
        "05_results/reviewer1.json": (K / "review_results/reviewer1.json").read_bytes(),
        "05_results/kappa_numbers.json": (ROOT / "data/search_results/exp_v4/kappa/kappa_numbers.json").read_bytes(),
    }
    later = {p.name: sha(p.read_bytes()) for p in sorted((K / "review_results/raw").glob("*.xlsx"))
             if p.name != "reviewer1_returned.xlsx"}
    files["05_results/NOT_ANALYSED_later_entries_sha256.json"] = json.dumps(
        {"note": "Re-entries made after preliminary results were shared with the corresponding author; "
                 "not independent first passes and not analysed. Retained by the authors.",
         "first_submission_sha256": sha((K / "review_results/raw/reviewer1_returned.xlsx").read_bytes()),
         "later_entries_sha256": later}, ensure_ascii=False, indent=2).encode()
    files["README.txt"] = """Blind taxonomy-label review (manuscript 4762284, Section 2.2, reply R1-4.2)

50 evidence units drawn at random (seed 20261020) from the 1,208-unit audited KB. One marine
engineer from an external marine-engineering company, not an author, assigned one component and
one aspect per unit without seeing the KB labels; curator notes restating the label were removed
from the displayed text. Sample, key and analysis were frozen before the workbook was sent.
Result (first submission): component kappa 0.52 [0.35, 0.68], aspect kappa 0.29 [0.16, 0.41],
pair agreement 18%. Re-run: python 03_code/analyze.py 04_returned/reviewer_first_submission.xlsx
(place 02_frozen as delivery/02_协调者_勿发 next to analyze.py).
""".encode()
    manifest = {}
    for rel, data in files.items():
        p = OUT / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); manifest[rel] = sha(data)
    (OUT / "MANIFEST_sha256.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    hits = []
    for p in OUT.rglob("*"):
        if p.is_file():
            blobs = [p.read_bytes()]
            if p.suffix == ".xlsx":
                with zipfile.ZipFile(p) as z:
                    blobs = [z.read(n) for n in z.namelist()]
            for b in blobs:
                t = b.decode("utf-8", errors="ignore")
                hits += [f"{p.relative_to(OUT)}: {rx.pattern}" for rx in BLOCK if rx.search(t)]
    if hits:
        raise SystemExit("privacy scan failed:\n" + "\n".join(sorted(set(hits))))
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT.parent))
    print(len(manifest) + 1, "files", ZIP.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
