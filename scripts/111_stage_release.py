# scripts/111_stage_release.py
"""把修订版论文所依赖的数据整理成一个本地待发布目录（Zenodo 新版本候选），并做隐私扫描。

只复制、不修改源文件；不上传。输出：
  <repo>/../release_staging_v3_20261019/RAG_for_REQ_data_v3/   （目录）
  <repo>/../release_staging_v3_20261019/RAG_for_REQ_data_v3.zip
  .../RAG_for_REQ_data_v3/SHA256SUMS.txt
扫描命中本地路径、密钥或个人邮箱时以非零码退出（厂家手册原文里的公开服务邮箱列入白名单）。
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT.parent / "release_staging_v3_20261019"
PKG = STAGE / "RAG_for_REQ_data_v3"
E4 = "data/search_results/exp_v4"
HR = "revision_artifacts/human_review_consolidation_20261017/analysis"
Q5 = "revision_artifacts/qualitative_5arm_authorized_run_20261019"
PRE = "revision_artifacts/qualitative_5arm_v2_preflight_20261019"
TERM = f"{Q5}/authorized_remaining330_20261019/terminal_results"
HV6 = "revision_artifacts/human_review_reconciliation_v6_20261019/results"

# 目标子目录 -> 源文件（相对 ROOT）
FILES = {
    "kb": ["data/processed/evidence_units_v3_audited.jsonl", "data/processed/kb_audit/kb_provenance_audit.csv",
           "data/processed/kb_audit/kb_audit_summary.json", "data/processed/kb_audit/README.md"],
    "inputs": ["data/processed/original_requirements_v2.jsonl"],
    "results/main_arms": [f"{E4}/rag_v4_results.json", f"{E4}/norag_v4_results.json",
                          f"{E4}/ablation_random_retrieval_results.json", f"{E4}/ablation_random_retrieval_summary.json",
                          f"{E4}/rag_v4_qwen_results.json", f"{E4}/norag_v4_qwen_results.json"],
    "results/sensitivity": [f"{E4}/sensitivity/{n}" for n in
                            ("summary.json", "retrieval.json", "boundary.json", "vector_only_results.json",
                             "bm25_only_results.json", "embed_mpnet_results.json")],
    "results/auxiliary_checks": [f"{E4}/norag_kb_verification.json", f"{E4}/paired_conflict_analysis.json",
                                 f"{E4}/hhard_contradiction_analysis.json", f"{E4}/credibility_v4/eval_v3.json",
                                 f"{E4}/e5_leakage.json", f"{E4}/encode_latency.json"],
    "results/stage1_mapping_S2": [f"{E4}/e1_pool.csv", f"{E4}/e1_predictions.json", f"{HR}/ANNOTATIONS_LONG.csv",
                                  f"{HR}/MASKS.json", f"{HR}/RESULTS.json"],
    "numbers": [f"{E4}/unified_v5/paper_numbers_unified.json", f"{E4}/unified_v5/row_changes_vs_historical.csv",
                f"{E4}/qualitative_5arm/qual_numbers.json"],
    "five_arm_experiment/design": [f"{PRE}/{n}" for n in
                                   ("PLAN.md", "prompt_old.txt", "prompt_new_q.txt", "prompt_norag_original.txt",
                                    "QWEN_BLIND_REVIEW_PROMPT.txt", "CONTEXTS_120.json", "SOURCE_REQUIREMENTS_60.json",
                                    "SCHEDULE_300.json", "classifier_v2.py", "INPUT_MANIFEST.json")],
    "five_arm_experiment/review_inputs": [f"{Q5}/QWEN_BLIND_PACKETS.json", f"{Q5}/QWEN_BLIND_KEY_LOCAL_ONLY.json",
                                          f"{Q5}/QWEN_FROZEN_PLAN.json"],
    "five_arm_experiment/results": [f"{TERM}/{n}" for n in
                                    ("FINAL_REPORT.json", "ALL_GROUPS_LABELS_AND_QUALITY.json", "REVIEW_DIAGNOSTICS_441.json",
                                     "PAIRED_SOURCE_SUMMARY.json", "PAIRED_SOURCE_REVIEW_DIFFERENCES.json",
                                     "GENERATION_PAIRED_SOURCE_DIFFERENCES.json", "SOURCE_LEVEL_REVIEW_COUNTS.json",
                                     "INTEGRITY.json")],
    "five_arm_experiment/author_audit": [f"{HV6}/逐项人机对照.csv", f"{HV6}/REPORT.json", f"{HV6}/作者补充说明.json"],
}
# raw request/response directories of the five-arm experiment (copied whole; response headers carry no credentials)
RAW_DIRS = {"five_arm_experiment/raw_generation": f"{Q5}/generation",
            "five_arm_experiment/raw_review_phase1": f"{Q5}/review",
            "five_arm_experiment/raw_review_phase2": f"{Q5}/authorized_resume_20261019/review",
            "five_arm_experiment/raw_review_phase3": f"{Q5}/authorized_remaining330_20261019/review"}
INDEX_DIRS = {"indexes/evidence_units_bge_m3": "data/indexes/evidence_units",
              "indexes/evidence_units_mpnet": "data/indexes/evidence_units_mpnet"}
PUBLIC_MODEL_ID = {"indexes/evidence_units_bge_m3": "BAAI/bge-m3",
                   "indexes/evidence_units_mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"}

LEAK = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|yando|[CD]:[\\/](?:Users|models|cooling)|/mnt/[a-z]/|/home/\w+|sk-[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]",
                  re.IGNORECASE)
ALLOWED = {"primeserv-cph@mandieselturbo.com", "leo7-hol@mandieselturbo.com"}

README = """# RAG_for_REQ data (manuscript 4762284, Systems Engineering, revised version)

DOI: 10.5281/zenodo.23477218. Every number in the revised manuscript can be recomputed from
these files with the companion code (https://github.com/losyser/RAG_for_REQ):
`python scripts/110_unified_regrade.py` regenerates `numbers/paper_numbers_unified.json`
from `kb/` and `results/` without any model call.

## Contents
- `kb/` audited knowledge base: 1,208 evidence units (L1 111 / L2 455 / L3 642) and the
  provenance audit sheet listing the decision for each of the 1,364 pre-audit units
  (156 dropped, 55 re-tiered, one source corrected).
- `inputs/` the 60 stakeholder-style source requirements (Chinese).
- `indexes/` BM25 and dense indexes over the audited KB (BGE-M3, with the repaired
  tokenizer; multilingual mpnet for the sensitivity variant). `model_path.txt` names the
  public model to download.
- `results/main_arms/` frozen outputs of the five arms: RAG and no-RAG (DeepSeek), random-
  retrieval ablation, RAG and no-RAG (qwen-max).
- `results/sensitivity/` boundary diagnostic, retrieval-layer variants and three
  end-to-end variants (vector-only, BM25-only, mpnet).
- `results/auxiliary_checks/` post-hoc KB check, paired conflict test, H_hard analysis,
  blinded LLM pairwise evaluation, leakage check and encoding latency.
- `results/stage1_mapping_S2/` Stage-1 mapping predictions and the eight-source human
  review (reviewers anonymised as C and D; long-format labels, masks and metrics).
- `numbers/` the single registry used by the manuscript, graded with one deterministic
  classifier (`grade-v5-numeric-range-boundaries`) for every arm, the rows whose grade
  differs from the classifier used during the runs, and the five-arm experiment summary
  (`qual_numbers.json`, from `scripts/112_qualitative_experiment_numbers.py`).
- `five_arm_experiment/` the prompt experiment on qualitative criteria: design, frozen
  contexts and prompts, the 300 raw generation requests/responses, the masked second-model
  review packets with their key and all raw review responses, summary results, and the
  author audit of 30 criteria.

## Notes
- Grades describe criterion format and KB-citation metadata, not semantic correctness.
- KB text includes excerpts of public classification rules and manufacturer documents,
  used for research under their original terms; consult the originals for authoritative text.
- Licence: CC BY 4.0 for the curated data and results.
"""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def scan(root: Path) -> list[str]:
    hits = []
    for p in root.rglob("*"):
        if p.suffix.lower() not in {".json", ".jsonl", ".csv", ".md", ".txt"}:
            continue
        for m in LEAK.finditer(p.read_text(encoding="utf-8", errors="ignore")):
            if m.group(0).lower() not in ALLOWED:
                hits.append(f"{p.relative_to(root)}: {m.group(0)}")
    return hits


def main() -> int:
    if PKG.exists():
        shutil.rmtree(PKG)
    for sub, srcs in FILES.items():
        (PKG / sub).mkdir(parents=True, exist_ok=True)
        for s in srcs:
            shutil.copy2(ROOT / s, PKG / sub / Path(s).name)
    for sub, src in RAW_DIRS.items():
        shutil.copytree(ROOT / src, PKG / sub)
    for sub, src in INDEX_DIRS.items():
        shutil.copytree(ROOT / src, PKG / sub)
        (PKG / sub / "model_path.txt").write_text(PUBLIC_MODEL_ID[sub] + "\n", encoding="utf-8")
    (PKG / "README.md").write_text(README, encoding="utf-8")
    hits = scan(PKG)
    files = sorted(p for p in PKG.rglob("*") if p.is_file())
    (PKG / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(p)}  {p.relative_to(PKG).as_posix()}\n" for p in files), encoding="utf-8")
    if hits:
        print("PRIVACY SCAN FAILED:\n" + "\n".join(hits[:50]))
        return 1
    zpath = STAGE / f"{PKG.name}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PKG.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(STAGE).as_posix())
    print(f"staged {len(files) + 1} files; zip {zpath.stat().st_size / 1e6:.1f} MB; sha256 {sha(zpath)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
