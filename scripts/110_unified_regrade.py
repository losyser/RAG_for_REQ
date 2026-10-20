# scripts/110_unified_regrade.py
"""用同一个（修复后的）确定性分级规则重评全部冻结输出，生成统一版论文数字。

覆盖五个主实验臂 + 三个端到端敏感性变体，并在 513 条 RAG 输出上重算 Grade C 构成和复核路由，
从而去掉"历史快照 409 条 / 评分版本待定"这类混用。只读冻结结果，不调用模型、不改 KB。

输出（隔离目录，不覆盖历史注册表）：
  data/search_results/exp_v4/unified_v5/paper_numbers_unified.json
  data/search_results/exp_v4/unified_v5/row_changes_vs_historical.csv
可选 --paper-dir：在该稿件目录写 revision_numbers.tex 和依赖分级的表格
（不写 table_e1 / table_blind_correct / table_stage3，它们是人工评审结果或已退出正文）。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cooling_rag_mg.grade_classifier import (CLASSIFIER_VERSION, RANGE_CLASSIFIER_VERSION, _TBD_PATTERN,
                                             classify_result_set, valid_citation_ids)
from cooling_rag_mg.review_routing import conflict_flag, derivation_type, review_route

E4 = ROOT / "data/search_results/exp_v4"
KBP = ROOT / "data/processed/evidence_units_v3_audited.jsonl"
OUT = E4 / "unified_v5"
ARMS = {"rag": "rag_v4_results.json", "norag": "norag_v4_results.json",
        "random": "ablation_random_retrieval_results.json",
        "rag_qwen": "rag_v4_qwen_results.json", "norag_qwen": "norag_v4_qwen_results.json"}
SENS = {"vector_only": "sensitivity/vector_only_results.json", "bm25_only": "sensitivity/bm25_only_results.json",
        "embed_mpnet": "sensitivity/embed_mpnet_results.json"}
# 只重写依赖分级的表；人工评审表和已退出正文的表不动
GRADE_TABLES = ("table_grade.tex", "table_ablation.tex", "table_routing.tex", "table_crossllm.tex",
                "appendix_sensitivity.tex")


def _load_module(name: str, fn: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pn = _load_module("paper_numbers", "100_paper_numbers.py")
pt = _load_module("paper_tables", "108_paper_tables.py")


def regrade(data: dict, kb: dict, policy: str) -> list[dict]:
    """返回按 (结果集, 序号) 展开的已重评 shall 列表，每条带 _sid 和 _k。"""
    rows = []
    for rs in data.get("result_sets", []):
        graded = classify_result_set(rs, kb, numeric_policy=policy)
        for k, e in enumerate(graded["engineering_requirements"]):
            rows.append({**e, "_sid": rs.get("source_requirement_id"), "_k": k})
    return rows


def summarize(rows: list[dict], kb: dict, n_sets: int) -> dict:
    n = len(rows)
    g = Counter(e["_grade"] for e in rows)
    vids = [e.get("_valid_citation_ids") or [] for e in rows]
    out = {"n_shalls": n, "n_sets": n_sets}
    for k in "ABCX":
        out[f"grade_{k}"] = g.get(k, 0)
        out[f"grade_{k}_pct"] = pn._pct(g.get(k, 0), n)
    out["grade_AB_pct"] = pn._pct(g.get("A", 0) + g.get("B", 0), n)
    out["grade_X_ci"] = pn.wilson(g.get("X", 0), n)
    out["citation_rate_pct"] = pn._pct(sum(1 for v in vids if v), n)
    out["l1_citation_rate_pct"] = pn._pct(sum(1 for v in vids if any(kb[i]["kb_tier"] == "L1" for i in v)), n)
    out["multi_source_pct"] = pn._pct(sum(1 for v in vids if len(v) >= 2), n)
    return out


def grade_c_breakdown(rows: list[dict], kb: dict) -> dict:
    """Grade C 按输出形式拆分：TBD+有效引用 / TBD+无有效引用 / 无可识别数值单位。只描述形式，不判断原因。"""
    cs = [e for e in rows if e["_grade"] == "C"]
    cnt = Counter()
    for e in cs:
        if _TBD_PATTERN.search(str(e.get("measurable_criterion") or "")):
            cnt["TBD_with_evidence" if e.get("_valid_citation_ids") else "TBD_no_evidence"] += 1
        else:
            cnt["qualitative"] += 1
    total_c = len(cs)
    return {"total_shalls": len(rows), "total_grade_c": total_c,
            "breakdown": {k: {"count": cnt.get(k, 0), "pct_of_c": pn._pct(cnt.get(k, 0), total_c)}
                          for k in ("TBD_with_evidence", "TBD_no_evidence", "qualitative")}}


def routing(data: dict, rows: list[dict], kb: dict) -> dict:
    ev = {rs.get("source_requirement_id"): rs.get("_evidence_values") or {} for rs in data.get("result_sets", [])}
    dt, rt, why, conflicts = Counter(), Counter(), Counter(), []
    for e in rows:
        vals = ev.get(e["_sid"], {})
        dt[derivation_type(e, kb)] += 1
        route, reason = review_route(e, kb, vals)
        rt[route] += 1
        why[f"{route}: {reason}"] += 1
        f = conflict_flag(e, kb, vals)
        if f:
            conflicts.append({"or": e["_sid"], "k": e["_k"], **f, "criterion": e.get("measurable_criterion")})
    return {"derivation": dict(dt), "routes": dict(rt), "route_reasons": dict(why),
            "conflicts": conflicts, "n_conflicts": len(conflicts)}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(policy: str) -> tuple[dict, list[dict]]:
    kb = {json.loads(l)["id"]: json.loads(l) for l in KBP.open(encoding="utf-8")}
    base = json.loads((E4 / "paper_numbers.json").read_text(encoding="utf-8"))
    N = dict(base)
    changes, inputs, graded = [], {}, {}
    for arm, fn in {**ARMS, **SENS}.items():
        p = E4 / fn
        d = json.loads(p.read_text(encoding="utf-8"))
        inputs[arm] = {"path": str(p.relative_to(ROOT)), "sha256": _sha(p)}
        rows = regrade(d, kb, policy)
        graded[arm] = (d, rows)
        s = summarize(rows, kb, len(d.get("result_sets", [])))
        if arm in ARMS:
            N[arm] = s
            hist = Counter(pn.classify_grade(e.get("measurable_criterion", ""), e.get("evidence_citations", []), kb)
                           for rs in d["result_sets"] for e in rs["engineering_requirements"])
            for e in rows:
                old = pn.classify_grade(e.get("measurable_criterion", ""), e.get("evidence_citations", []), kb)
                if old != e["_grade"]:
                    changes.append({"arm": arm, "id": f"{e['_sid']}.{e['_k'] + 1}", "historical_rule": old,
                                    "unified_rule": e["_grade"], "criterion": e.get("measurable_criterion")})
            s["historical_rule_counts"] = dict(hist)
        else:
            N.setdefault("e3_sensitivity", {}).setdefault("e2e", {})[arm] = s
    N["e3_sensitivity"]["e2e"]["default"] = {k: v for k, v in N["rag"].items() if k != "historical_rule_counts"}
    rag_d, rag_rows = graded["rag"]
    N["grade_c"] = grade_c_breakdown(rag_rows, kb)
    N["routing"] = {"rag": routing(rag_d, rag_rows, kb), "norag": routing(*graded["norag"], kb),
                    "random": routing(*graded["random"], kb)}
    N["routing"]["conflicts"] = N["routing"]["rag"]["conflicts"]
    N["routing"]["n_conflicts"] = N["routing"]["rag"]["n_conflicts"]
    N["unified_grading"] = {"numeric_policy": policy,
                            "classifier_version": RANGE_CLASSIFIER_VERSION if policy != "legacy" else CLASSIFIER_VERSION,
                            "kb_sha256": _sha(KBP), "inputs": inputs, "n_rows_changed_vs_historical_rule": len(changes),
                            "scope": "criterion format and KB citation metadata; not semantic support or correctness"}
    macros = dict(base.get("macros") or {})
    macros.update(pt.build_macros(N))
    N["macros"] = macros
    return N, changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="numeric-ranges-v1", choices=["legacy", "numeric-ranges-v1"])
    ap.add_argument("--paper-dir", type=Path, help="写入 revision_numbers.tex 与分级相关表格的稿件目录")
    a = ap.parse_args()
    N, changes = build(a.policy)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "paper_numbers_unified.json").write_text(json.dumps(N, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "row_changes_vs_historical.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arm", "id", "historical_rule", "unified_rule", "criterion"])
        w.writeheader()
        w.writerows(changes)
    if a.paper_dir:
        (a.paper_dir / "revision_numbers.tex").write_text(
            pn.to_macros(N["macros"]).replace("scripts/100_paper_numbers.py", "scripts/110_unified_regrade.py"),
            encoding="utf-8")
        for fname in GRADE_TABLES:
            (a.paper_dir / fname).write_text(pt.TABLES[fname](N), encoding="utf-8")
    print(json.dumps({"policy": a.policy, "rows_changed": len(changes),
                      "arms": {k: {g: N[k][f"grade_{g}"] for g in "ABCX"} for k in ARMS},
                      "grade_c": N["grade_c"], "rag_routes": N["routing"]["rag"]["routes"],
                      "rag_derivation": N["routing"]["rag"]["derivation"],
                      "rag_conflicts": N["routing"]["rag"]["n_conflicts"],
                      "e2e": {k: (v["grade_X_pct"], v["grade_AB_pct"]) for k, v in N["e3_sensitivity"]["e2e"].items()}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
