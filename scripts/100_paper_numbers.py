# scripts/100_paper_numbers.py
"""从各结果文件汇总论文中出现的全部数字，写入 exp_v4/paper_numbers.json。
可选文件（E1/E2/E3/E5/E7/E8/盲评）存在才读，缺失则写 null，不会报错。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import valid_citation_ids

E4 = ROOT / "data/search_results/exp_v4"
KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0.0, c - h) * 100, 1), round(min(1.0, c + h) * 100, 1))


def _pct(k, n):
    return None if n == 0 else round(k / n * 100, 1)


def grade_summary(d: dict, kb: dict) -> dict:
    ers = [e for rs in d.get("result_sets", []) for e in rs.get("engineering_requirements", [])]
    n = len(ers)
    g = Counter(e.get("_grade") for e in ers)
    vids = [valid_citation_ids(e.get("evidence_citations", []), kb) for e in ers]
    out = {"n_shalls": n, "n_sets": len(d.get("result_sets", []))}
    for k in "ABCX":
        out[f"grade_{k}"] = g.get(k, 0)
        out[f"grade_{k}_pct"] = _pct(g.get(k, 0), n)
    out["grade_AB_pct"] = _pct(g.get("A", 0) + g.get("B", 0), n)
    out["grade_X_ci"] = wilson(g.get("X", 0), n)
    out["citation_rate_pct"] = _pct(sum(1 for v in vids if v), n)
    out["l1_citation_rate_pct"] = _pct(sum(1 for v in vids if any(kb[i]["kb_tier"] == "L1" for i in v)), n)
    out["multi_source_pct"] = _pct(sum(1 for v in vids if len(v) >= 2), n)
    return out


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    kb = {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}
    N = {"kb": {"n_units": len(kb), "tiers": dict(Counter(u["kb_tier"] for u in kb.values())),
                "n_sources": len({(u.get("metadata") or {}).get("source_document") for u in kb.values()}),
                "audit": _load(ROOT / "data/processed/kb_audit/kb_audit_summary.json")}}
    for key, fn in [("rag", "rag_v4_results.json"), ("norag", "norag_v4_results.json"),
                    ("random", "ablation_random_retrieval_results.json"),
                    ("rag_qwen", "rag_v4_qwen_results.json"), ("norag_qwen", "norag_v4_qwen_results.json")]:
        d = _load(E4 / fn)
        N[key] = grade_summary(d, kb) if d else None
    rag = _load(E4 / "rag_v4_results.json") or {"result_sets": []}
    tim = [rs.get("_timing", {}) for rs in rag["result_sets"]]
    N["timing_s_mean"] = {k: (round(sum(t.get(k, 0) for t in tim) / len(tim), 2) if tim else None)
                          for k in ("stage1_s", "retrieval_s", "selection_s", "extraction_s", "generation_s")}
    for key, fn in [("grade_c", "grade_c_analysis.json"), ("posthoc", "norag_kb_verification.json"),
                    ("paired_conflict", "paired_conflict_analysis.json"),
                    ("credibility", "credibility_v4/eval_v3.json"),
                    ("regrade_preaudit", "regrade_preaudit_with_v3kb.json"),
                    ("e1_stage1", "e1_stage1_scores.json"), ("expert", "expert_scores.json"),
                    ("e3_sensitivity", "sensitivity/summary.json"), ("e5_leakage", "e5_leakage.json"),
                    ("routing", "routing_report.json"), ("stage3_subset", "stage3_accuracy_subset.json")]:
        d = _load(E4 / fn)
        N[key] = (d.get("summary", d) if isinstance(d, dict) else d) if d is not None else None
    (E4 / "paper_numbers.json").write_text(json.dumps(N, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: N[k] for k in ("kb", "rag", "norag", "random")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
