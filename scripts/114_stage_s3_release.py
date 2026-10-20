# scripts/114_stage_s3_release.py
"""Stage the S3 blind expert review as a Zenodo addendum (S3_expert_review.zip).

Contents: blank workbook and reader as sent, frozen protocol/sample/contract files, analysis
code, the reviewer's returned workbook (identity fields reduced to role and background),
the analysis copy, the result JSON and the paper macros. frozen_inputs/ duplicates files of
the main archive, so only their SHA-256 values are kept. Local paths are replaced and a
privacy scan blocks the build on any remaining user path or e-mail address.
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
S3 = ROOT / "revision_artifacts/s3_paired_review50_20261019"
DESK = Path("/mnt/c/Users/yando/Desktop/S3数值独立盲评50条_20261019_1610")
OUT = ROOT.parent / "release_staging_v3_20261019/S3_expert_review"
ZIP = OUT.with_suffix(".zip")
COORD = "02_协调者_勿发评审"
COORD_FILES = ["ANALYSIS_FREEZE.json", "CANDIDATE_POOL_FROZEN.json", "DISPLAY_CORRECTION.json", "DISPLAY_DIFFS.json",
               "INPUT_MANIFEST.json", "PROTOCOL_FROZEN.json", "SAMPLE_FROZEN.json", "SAMPLING.json",
               "VALIDATION_REPORT.json", "WORKBOOK_CONTRACT.json", "分析使用说明.txt"]
CODE = ["analyze.py", "prepare.py", "test_review.py", "verify.py", "finalize.py", "correct_display.py",
        "freeze_display_v2.py", "build_workbook.mjs", "render_html.mjs", "guide.json", "blind_input.json",
        "reader_rows.json", "prepare_reviewer1_copy.py", "run_reviewer1.py"]
PATH_SUBS = [(re.compile(r"/mnt/[cd]/[^\s\"']*?(?=(?:S3数值|cooling_rag_multigranular|revision_artifacts)[^\s\"']*)"), "<local>/"),
             (re.compile(r"[A-Za-z]:\\\\?Users\\\\?[^\\\s\"']+"), "<home>"),
             (re.compile(r"/home/[^/\s\"']+"), "<home>")]
BLOCK = [re.compile(p) for p in (r"/mnt/[cd]/", r"[A-Za-z]:\\\\?Users", r"/home/\w", r"yando",
                                  r"[\w.+-]+@[\w-]+\.[\w.]+")]
sha = lambda b: hashlib.sha256(b).hexdigest()


def scrub(text: str) -> str:
    for rx, rep in PATH_SUBS:
        text = rx.sub(rep, text)
    return text


def put(rel: str, data: bytes, manifest: dict) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if rel.endswith((".json", ".txt", ".py", ".mjs", ".md", ".html")):
        data = scrub(data.decode("utf-8")).encode("utf-8")
    p.write_bytes(data)
    manifest[rel] = sha(data)


def reviewer_workbook(src: Path) -> bytes:
    """Keep ratings verbatim; identity sheet reduced to reviewer code, role and background."""
    wb = openpyxl.load_workbook(src)
    ws = wb["身份与说明"]
    keep = {6: "评审员1", 7: "外部非作者领域评审", 8: "轮机工程", 9: "外部公司工程师；专业硕士研究生",
            10: "无", 11: "是", 12: "独立首判"}
    for r, v in keep.items():
        ws.cell(r, 2).value = v
    # document properties carry local account names of whoever last saved the file; cleared
    wb.properties.creator = None
    wb.properties.lastModifiedBy = None
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    manifest: dict = {}
    send = DESK / "01_仅此目录可发评审"
    blank = S3 / "outputs/01a13537-s3/01_仅此目录可发评审"
    for f in sorted(blank.iterdir()):
        put(f"01_materials_sent_to_reviewer/{f.name}", f.read_bytes(), manifest)
    for f in COORD_FILES:
        put(f"02_frozen_protocol/{f}", (S3 / COORD / f).read_bytes(), manifest)
    fi = {p.name: sha(p.read_bytes()) for p in sorted((S3 / COORD / "frozen_inputs").iterdir())}
    put("02_frozen_protocol/frozen_inputs_sha256.json",
        json.dumps({"note": "Identical copies of these files are in RAG_for_REQ_data.zip (kb, inputs, main arms).",
                    "sha256": fi}, ensure_ascii=False, indent=2).encode(), manifest)
    for f in CODE:
        put(f"03_analysis_code/{f}", (S3 / f).read_bytes(), manifest)
    put("04_returned_ratings/reviewer1_first_pass.xlsx", reviewer_workbook(send / "评审表修改版.xlsx"), manifest)
    put("04_returned_ratings/reviewer1_earlier_save_basis_empty.xlsx",
        reviewer_workbook(send / "数值候选独立评分.xlsx"), manifest)
    for f in ("reviewer1_first_pass.json", "reviewer1_provenance.json"):
        put(f"05_results/{f}", (S3 / "review_results" / f).read_bytes(), manifest)
    put("05_results/s3_numbers.json", (ROOT / "data/search_results/exp_v4/s3_expert/s3_numbers.json").read_bytes(), manifest)
    readme = """S3 blind expert review of paired numeric candidates (manuscript 4762284, Section 2.5.5 / Table 13)

01  Blank workbook, read-only HTML and instructions exactly as sent to the reviewer.
02  Frozen candidate pool, sample (blind_id -> arm, source, row), display diffs, workbook contract,
    protocol and analysis freeze (hashes), all fixed before the workbook was sent.
03  Analysis code. analyze.py is the frozen analysis; run_reviewer1.py runs it waiving only the
    unrecorded start/end time fields; prepare_reviewer1_copy.py makes the analysis copy.
04  Returned ratings. reviewer1_first_pass.xlsx is the analysed workbook; the earlier save has an
    empty basis column and differs in one label (K288080), revised by the reviewer on re-check before
    unblinding. Identity fields are reduced to role and background and document properties
    (local account names) are cleared; ratings, basis and notes are verbatim. SHA-256 of the
    returned originals are listed in 05_results/reviewer1_provenance.json.
05  Result JSON (frozen summaries), coordinator provenance log and paper macros.
Reviewer: one marine engineer from an external company, enrolled in a professional master's
programme, not an author, no prior exposure; AI search used only to locate documents. The reviewer
did not receive the coordinator-assembled reference packet. No inter-rater agreement.
"""
    put("README.txt", readme.encode(), manifest)
    put("MANIFEST_sha256.json", json.dumps(manifest, ensure_ascii=False, indent=2).encode(), {})
    hits = []
    for p in OUT.rglob("*"):
        if p.is_file() and p.suffix in (".json", ".txt", ".py", ".mjs", ".html", ".md"):
            t = p.read_text(encoding="utf-8", errors="ignore")
            hits += [f"{p.relative_to(OUT)}: {rx.pattern}" for rx in BLOCK if rx.search(t)]
    if hits:
        raise SystemExit("privacy scan failed:\n" + "\n".join(hits))
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(OUT.parent))
    print(len(manifest), "files", ZIP.stat().st_size, "bytes", ZIP)


if __name__ == "__main__":
    main()
