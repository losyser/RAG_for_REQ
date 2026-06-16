"""
M6：为第二位专家准备**盲法正确性评审**样本。

设计：从 RAG 与 no-RAG 两臂各抽等量"含数值的 shall"，打乱、**隐去臂别与引用来源**，
只给专家看 shall 文本 + 数值判据，请其纯凭工程判断每个数值是否正确。
这样得到的是**人工盲评的 RAG vs no-RAG 数值正确率对比**——补上"RAG 输出本身是否正确"
这一独立人工证据(此前只评了 no-RAG 的错误)。

产出(exp_v4/):
  blind_correctness_review.csv  —— 发给专家填(verdict 列留空)
  blind_correctness_key.json    —— 隐藏映射 uid→(arm, sid)，专家评完后用于汇总

评判选项(写在 CSV 表头说明)：correct / approx / wrong / unknown
"""
from __future__ import annotations
import csv, json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "data" / "search_results" / "exp_v4"
NUM = re.compile(r"\d+\.?\d*\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b)")
N_PER_ARM = 25
SEED = 42


def numeric_shalls(path, arm):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for rs in d["result_sets"]:
        sid = rs["source_requirement_id"]
        for er in rs.get("engineering_requirements", []):
            crit = str(er.get("measurable_criterion") or "")
            shall = er.get("shall_statement", "")
            if NUM.search(crit) or NUM.search(shall):
                out.append({"arm": arm, "sid": sid, "shall": shall, "criterion": crit})
    return out


def main():
    rng = random.Random(SEED)
    rag = numeric_shalls(EXP / "rag_v4_results.json", "RAG")
    nor = numeric_shalls(EXP / "norag_v4_results.json", "no-RAG")
    rag_s = rng.sample(rag, min(N_PER_ARM, len(rag)))
    nor_s = rng.sample(nor, min(N_PER_ARM, len(nor)))
    pool = rag_s + nor_s
    rng.shuffle(pool)

    key = {}
    rows = []
    for i, item in enumerate(pool, 1):
        uid = f"R{i:03d}"
        key[uid] = {"arm": item["arm"], "sid": item["sid"]}
        rows.append({
            "uid": uid,
            "shall_statement": item["shall"],
            "measurable_criterion": item["criterion"],
            "verdict (correct/approx/wrong/unknown)": "",
            "note": "",
        })

    out_csv = EXP / "blind_correctness_review.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (EXP / "blind_correctness_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"评审样本: {out_csv}  ({len(rows)} 条; RAG {len(rag_s)} + no-RAG {len(nor_s)}, 已打乱隐去臂别)")
    print(f"隐藏映射: {EXP/'blind_correctness_key.json'}")
    print("说明：把 blind_correctness_review.csv 发给第二位专家，只填 verdict 列；")
    print("评判标准 correct=与规范/惯例吻合, approx=±20%内, wrong=明显偏离/捏造, unknown=超出把握。")


if __name__ == "__main__":
    main()
