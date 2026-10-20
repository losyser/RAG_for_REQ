# scripts/98_score_expert_workbook.py
"""对专家工作簿评分。
用法：PY scripts/98_score_expert_workbook.py <filled.xlsx> [<second_annotator.xlsx>] --coverage-confirmed --out-dir <new-directory>
输出：指定独立新目录中的 expert_scores.json 和 e1_stage1_scores.json；不覆盖历史结果。
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "data/search_results/exp_v4"
KEY = ROOT / "data/expert_round2/expert_key.json"


def score_kappa(a: list, b: list, valid: set | None = None) -> dict:
    from sklearn.metrics import cohen_kappa_score
    pairs = [(x, y) for x, y in zip(a, b) if x and y and (valid is None or (x in valid and y in valid))]
    if len(pairs) < 2:
        return {"kappa": None, "agreement_pct": None, "n_used": len(pairs), "n_skipped": len(a) - len(pairs)}
    xs, ys = zip(*pairs)
    k = cohen_kappa_score(xs, ys)
    return {"kappa": round(float(k), 3) if __import__("math").isfinite(k) else None, "agreement_pct": round(sum(x == y for x, y in pairs) / len(pairs) * 100, 1),
            "n_used": len(pairs), "n_skipped": len(a) - len(pairs)}


def prf(pred: dict, gold: dict) -> dict:
    if set(pred) != set(gold):
        raise ValueError("Prediction/gold source coverage differs; refusing partial scoring")
    tp = sum(len(pred.get(r, set()) & g) for r, g in gold.items())
    np_ = sum(len(pred.get(r, set())) for r in gold)
    ng = sum(len(g) for g in gold.values())
    p = tp / np_ if np_ else None
    rc = tp / ng if ng else None
    f = (2 * p * rc / (p + rc)) if p is not None and rc is not None and p + rc else (0.0 if np_ and ng else None)
    r1 = lambda v: None if v is None else round(v * 100, 1)
    return {"precision": r1(p), "recall": r1(rc), "f1": r1(f), "tp": tp, "n_pred": np_, "n_gold": ng}


def bootstrap_f1(pred: dict, gold: dict, n: int = 1000, seed: int = 42):
    rng = random.Random(seed); ids = sorted(gold); vals = []
    for _ in range(n):
        s = [rng.choice(ids) for _ in ids]
        g = {f"{i}_{k}": gold[r] for k, r in enumerate(s) for i in [r]}
        p = {f"{i}_{k}": pred.get(r, set()) for k, r in enumerate(s) for i in [r]}
        f = prf(p, g)["f1"]
        if f is not None:
            vals.append(f)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]) if vals else (None, None)


def stage3_prf(rows: list[dict]) -> dict:
    """Stage-3 extraction accuracy from expert counts; rows lacking counts are skipped."""
    ok = [r for r in rows if isinstance(r.get("n_correct"), (int, float)) and isinstance(r.get("n_missed"), (int, float))]
    out = {"n_skipped": len(rows) - len(ok)}
    for tier in ("L1", "L2", "L3", "ALL"):
        rs = [r for r in ok if tier == "ALL" or r["tier"] == tier]
        c = sum(r["n_correct"] for r in rs); m = sum(r["n_missed"] for r in rs); x = sum(r["n_extracted"] for r in rs)
        out[tier] = {"n_units": len(rs), "precision": round(c / x * 100, 1) if x else None,
                     "recall": round(c / (c + m) * 100, 1) if c + m else None}
    return out


def _sheet(wb, name):
    ws = wb[name]; rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if r and r[0] is not None]


def main() -> None:
    import argparse
    global E4
    ap = argparse.ArgumentParser()
    ap.add_argument("workbook")
    ap.add_argument("--integrity-manifest", required=True)
    ap.add_argument("--baseline-manifest", required=True)
    ap.add_argument("second_workbook", nargs="?")
    ap.add_argument("--coverage-confirmed", action="store_true", help="Coordinator confirms annotator reviewed missing pairs for every source")
    ap.add_argument("--out-dir", required=True, help="New independent scores directory; existing results are not overwritten")
    args = ap.parse_args()
    source_exp = E4
    E4 = Path(args.out_dir).resolve()
    if E4 == source_exp.resolve() or E4.exists():
        raise SystemExit("Choose a NEW independent output directory")
    from openpyxl import load_workbook
    from scipy.stats import fisher_exact
    sys.path.insert(0, str(ROOT))
    from cooling_rag_mg.evidence_taxonomy import COMPONENTS, INTENTS, valid_pair
    from cooling_rag_mg.expert_integrity import make_contract, verify_sources, validate_workbook
    contract = json.loads(Path(args.integrity_manifest).read_text(encoding="utf-8"))
    baseline = json.loads(Path(args.baseline_manifest).read_text(encoding="utf-8"))
    integrity_errors = verify_sources(ROOT, contract, baseline)
    if integrity_errors:
        raise SystemExit("SCORING BLOCKED\n" + "\n".join(integrity_errors))
    key = json.loads(KEY.read_text(encoding="utf-8"))
    template = load_workbook(ROOT / "data/expert_round2/expert_workbook.xlsx", read_only=True)
    reconstructed = make_contract(template, key, contract["source_hashes"])
    if reconstructed != contract:
        raise SystemExit("SCORING BLOCKED: integrity manifest content differs from verified template/key")
    wb = load_workbook(args.workbook, read_only=True)
    from cooling_rag_mg.revision_audit import validate_expert_rows, validate_prediction_pool
    names = {"S1":"S1_tagging", "S2":"S2_pairs", "S3":"S3_values", "S4":"S4_extraction"}
    sheets = {k:_sheet(wb,v) for k,v in names.items() if v in wb.sheetnames}
    preds = json.loads((source_exp / "e1_predictions.json").read_text(encoding="utf-8"))
    errors = validate_workbook(wb,contract) + validate_expert_rows(sheets,key) + validate_prediction_pool(preds,key["S2"])
    if not args.coverage_confirmed:
        errors.append("S2 coverage review not confirmed; candidate pool alone is not complete gold")
    if args.second_workbook:
        wb2 = load_workbook(args.second_workbook, read_only=True)
        second = _sheet(wb2,"S1_tagging")
        errors += validate_workbook(wb2,contract,["S1"]) + validate_expert_rows({"S1":second},{"S1":key["S1"]})
    if errors:
        raise SystemExit("SCORING BLOCKED\n" + "\n".join(errors))
    E4.mkdir(parents=True)

    out: dict = {}

    s1 = _sheet(wb, "S1_tagging")
    kc = [key["S1"][str(r["item"])]["component"] for r in s1]
    ki = [key["S1"][str(r["item"])]["intent"] for r in s1]
    ec = [(r.get("component") or "").strip() for r in s1]
    ei = [(r.get("intent") or "").strip() for r in s1]
    out["E2_component"] = score_kappa(kc, ec, set(COMPONENTS))
    out["E2_intent"] = score_kappa(ki, ei, set(INTENTS))
    out["E2_pair"] = score_kappa([f"{a}|{b}" for a, b in zip(kc, ki)],
                                 [f"{a}|{b}" if a and b else "" for a, b in zip(ec, ei)])

    s2 = _sheet(wb, "S2_pairs")
    gold: dict = {}
    for r in s2:
        rid, c, i = key["S2"][str(r["item"])]
        gold.setdefault(rid, set())
        if str(r.get("relevant")).strip() == "1":
            gold[rid].add((c, i))
        for tok in str(r.get("missing_pairs") or "").split(";"):
            if ":" in tok:
                c2, i2 = [t.strip() for t in tok.split(":", 1)]
                if valid_pair(c2, i2):
                    gold[rid].add((c2, i2))
    e1 = {}
    for sysname, d in preds.items():
        pd = {rid: {tuple(p) for p in ps} for rid, ps in d.items()}
        res = prf(pd, gold)
        res["f1_ci95"] = bootstrap_f1(pd, gold)
        res["component_level"] = prf({r: {c for c, _ in v} for r, v in pd.items()},
                                     {r: {c for c, _ in v} for r, v in gold.items()})
        res["intent_level"] = prf({r: {i for _, i in v} for r, v in pd.items()},
                                  {r: {i for _, i in v} for r, v in gold.items()})
        e1[sysname] = res
    e1["n_requirements_with_gold"] = sum(1 for g in gold.values() if g)
    (E4 / "e1_stage1_scores.json").write_text(json.dumps(e1, ensure_ascii=False, indent=1), encoding="utf-8")

    s3 = _sheet(wb, "S3_values")
    tab = {"RAG": Counter(), "no-RAG": Counter()}
    for r in s3:
        v = (r.get("verdict") or "").strip()
        if v in {"correct", "approx", "wrong", "unknown"}:
            tab[key["S3"][str(r["item"])]["arm"]][v] += 1
    def fisher(pos):
        a = sum(tab["RAG"][p] for p in pos); b = sum(tab["RAG"].values()) - a
        c = sum(tab["no-RAG"][p] for p in pos); d = sum(tab["no-RAG"].values()) - c
        return round(float(fisher_exact([[a, b], [c, d]])[1]), 3)
    out["S3_blind"] = {"counts": {k: dict(v) for k, v in tab.items()},
                       "p_correct_or_approx": fisher({"correct", "approx"}),
                       "p_correct": fisher({"correct"}), "p_wrong": fisher({"wrong"})}

    if "S4_extraction" in wb.sheetnames:
        s4 = _sheet(wb, "S4_extraction")
        rows4 = [{"tier": key["S4"][str(r["item"])]["tier"], "n_extracted": key["S4"][str(r["item"])]["n_extracted"],
                  "n_correct": r.get("n_correct"), "n_missed": r.get("n_missed")} for r in s4]
        st3 = stage3_prf(rows4)
        out["S4_stage3"] = st3
        (E4 / "stage3_accuracy_subset.json").write_text(json.dumps(st3, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.second_workbook:
        wb2 = load_workbook(args.second_workbook, read_only=True)
        t_by_id = {str(r["item"]):r for r in _sheet(wb2, "S1_tagging")}
        t1 = [t_by_id[str(r["item"])] for r in s1]
        out["E2_inter_annotator_pair"] = score_kappa(
            [f"{(r.get('component') or '').strip()}|{(r.get('intent') or '').strip()}" for r in s1],
            [f"{(r.get('component') or '').strip()}|{(r.get('intent') or '').strip()}" for r in t1])
    (E4 / "expert_scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
