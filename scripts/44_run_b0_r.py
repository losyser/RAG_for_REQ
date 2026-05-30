# scripts/44_run_b0_r.py
# -*- coding: utf-8 -*-
"""Phase 3 Task 3.3：据共享子需求跑 B0 与 R 两组工程需求生成。

单变量设计：两组共用 split_requirements_v1.jsonl 的同一份子需求拆分。
- B0(no-RAG)：每个子需求据子需求文本直接生成（Qwen），不检索，evidence_ids=[]。
- R(RAG)   ：每个子需求经多粒度检索(run_sub_requirement_stage)拿 selected 证据，
             据证据生成（Qwen）；无证据则弃权（不产出 shall，记入覆盖率）。
唯一差别 = 上下文有无检索证据。生成器 prompt 两组共用 system base（见 evidence_first_generator）。

产物（供 Phase 2 评估层读取）：data/search_results/main_experiment/{B0,R}_results.json

用法：
  python scripts/44_run_b0_r.py --limit 3      # 冒烟：只跑前 3 条源需求
  python scripts/44_run_b0_r.py                # 全量 60 条
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_first_generator import generate_for_sub
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.pipeline import make_services, run_sub_requirement_stage


def _sub_payload(sub: dict) -> dict:
    """把冻结子需求转成 run_sub_requirement_stage 需要的 payload（字段对齐 build_sub_payload）。"""
    return {
        "sub_requirement_id": sub.get("sub_requirement_id", ""),
        "requirement_type": sub.get("requirement_type", "other"),
        "topic": sub.get("topic", ""),
        "text": sub.get("text", ""),
        "split_method": sub.get("split_method", ""),
        "split_error": sub.get("split_error", ""),
        "source_phrase": sub.get("source_phrase", ""),
        "implication_type": sub.get("implication_type", ""),
    }


def _result_set(arm: str, src_id: str, stakeholder: str, ers: list[dict],
                n_subs: int, n_subs_out: int) -> dict:
    return {
        "source_requirement_id": src_id,
        "stakeholder": stakeholder,
        "_arm": arm,
        "engineering_requirements": ers,
        "_coverage": {"n_subs": n_subs, "n_subs_with_output": n_subs_out},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default=None, help="共享拆分 jsonl（缺省 processed/split_requirements_v1.jsonl）")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条源需求（0=全量）")
    ap.add_argument("--top-k", type=int, default=4)
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.qwen.enabled:
        print("Qwen 未配置 API key（.env）。"); sys.exit(1)

    split_path = Path(args.split) if args.split else cfg.paths.processed_dir / "split_requirements_v1.jsonl"
    if not split_path.exists():
        print(f"未找到共享拆分：{split_path}。先运行 scripts/42。"); sys.exit(1)
    sources = list(read_jsonl(split_path))
    if args.limit:
        sources = sources[: args.limit]

    qwen = cfg.qwen.make_client()
    services = make_services()  # 多粒度检索（R 用），含 DeepSeek 证据审查
    print(f"[b0/r] {len(sources)} 条源需求，Qwen 生成 + R 多粒度检索 ...")

    b0_sets, r_sets = [], []
    r_abstain = 0
    # 熔断：B0 永不该弃权，正常必产 ER；连续多个空 B0 ≈ API/计费故障，立即停，
    # 不再静默磨完一堆空结果（见 2026-05-30 Qwen 欠费教训）。
    consec_empty_b0 = 0
    CIRCUIT_BREAK = 5
    for i, src in enumerate(sources, start=1):
        src_id = src["source_requirement_id"]
        stake = src.get("stakeholder", "")
        src_text = src.get("requirement_text", "")
        subs = src.get("sub_requirements", []) or []

        b0_ers, r_ers = [], []
        r_out_subs = 0
        for sub in subs:
            # ── B0：无检索，据子需求生成 ──
            b0 = generate_for_sub(sub, evidence_ids=[], evidence_texts=[],
                                  source_requirement=src_text, arm="B0",
                                  client=qwen, model=cfg.qwen.model, temperature=cfg.qwen.temperature)
            b0_ers.extend(b0 or [])
            consec_empty_b0 = consec_empty_b0 + 1 if not b0 else 0
            if consec_empty_b0 >= CIRCUIT_BREAK:
                print(f"\n[ABORT] 连续 {CIRCUIT_BREAK} 个 B0 生成为空——疑似 API/计费故障"
                      f"（如 Qwen 欠费）。停止，不保存残缺结果。请检查 API 后重跑。")
                sys.exit(2)

            # ── R：多粒度检索 → 据证据生成 ──
            stage = run_sub_requirement_stage(
                _sub_payload(sub), services=services,
                top_k=args.top_k, coarse_k=12, fine_k=40, judge_candidate_k=25,
            )
            selected = stage.get("selected_results", []) or []
            ev_ids = [s.get("id") for s in selected if s.get("id")]
            ev_texts = [s.get("text", "") for s in selected if s.get("text")]
            r = generate_for_sub(sub, evidence_ids=ev_ids, evidence_texts=ev_texts,
                                 source_requirement=src_text, arm="R",
                                 client=qwen, model=cfg.qwen.model, temperature=cfg.qwen.temperature)
            if r is None:
                r_abstain += 1  # R 弃权（无证据）
            else:
                r_out_subs += 1
                r_ers.extend(r)

        b0_sets.append(_result_set("B0", src_id, stake, b0_ers, len(subs), len(subs)))
        r_sets.append(_result_set("R", src_id, stake, r_ers, len(subs), r_out_subs))
        print(f"  [{i}/{len(sources)}] {src_id}: B0 {len(b0_ers)} ER | R {len(r_ers)} ER "
              f"({r_out_subs}/{len(subs)} 子需求有证据)")

    out_dir = cfg.paths.search_results_dir / "main_experiment"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "B0_results.json").write_text(
        json.dumps({"arm": "B0", "result_sets": b0_sets}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "R_results.json").write_text(
        json.dumps({"arm": "R", "result_sets": r_sets}, ensure_ascii=False, indent=2), encoding="utf-8")

    n_sub = sum(len(s.get("sub_requirements", [])) for s in sources)
    r_cov = (n_sub - r_abstain) / n_sub if n_sub else 0
    print(f"\nB0: {sum(len(s['engineering_requirements']) for s in b0_sets)} ER（全 {n_sub} 子需求）")
    print(f"R : {sum(len(s['engineering_requirements']) for s in r_sets)} ER，"
          f"覆盖率 {r_cov:.1%}（{n_sub - r_abstain}/{n_sub} 子需求有证据，弃权 {r_abstain}）")
    print(f"-> {out_dir}")


if __name__ == "__main__":
    main()
