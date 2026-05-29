# scripts/41_generate_original_requirements.py
# -*- coding: utf-8 -*-
"""Phase 1 Task 1.3：用文心 ERNIE 生成高层原始干系人需求，质量校验后冻结。

多智能体分工中的「出题」角色（ERNIE），与生成者 Qwen、拆分者 DeepSeek 跨厂商。
产物 data/processed/original_requirements_v1.jsonl 为冻结数据集，两实验组共用其下游拆分。

用法：
  python scripts/41_generate_original_requirements.py --n 60
  python scripts/41_generate_original_requirements.py --n 60 --batch-size 12 --sim-threshold 0.8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.grounding import load_evidence_text_map
from cooling_rag_mg.jsonl import write_jsonl
from cooling_rag_mg.original_requirements import (
    build_generation_prompt, parse_generated, quality_check,
)

# 参考主题（可发散）——覆盖船舶主机冷却水系统的多个工程面，保证多样性
SEED_TOPICS = [
    "海水泵冗余与自动投入", "淡水冷却温度监测与高温报警", "冷却器/换热器维护可达性",
    "膨胀水箱液位与补水", "防腐与牺牲阳极", "应急冷却与失电工况",
    "管路布置与隔离阀", "传感器与控制联锁", "运行参数可验证性",
    "海水滤器堵塞监测", "低温保护与暖机", "冷却系统能效与变频",
]


def _dedupe(reqs: list[dict], sim_threshold: float) -> list[dict]:
    """组内互查：用同一字符 n-gram Jaccard 去掉近似重复，保留先到者。"""
    from cooling_rag_mg.original_requirements import _jaccard
    kept: list[dict] = []
    for r in reqs:
        t = r["requirement_text"]
        if all(_jaccard(t, k["requirement_text"]) < sim_threshold for k in kept):
            kept.append(r)
    return kept


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="目标条数（去重+质量过滤后）")
    ap.add_argument("--batch-size", type=int, default=10, help="每次 ERNIE 调用生成条数")
    ap.add_argument("--sim-threshold", type=float, default=0.8, help="KB 查重/去重阈值")
    ap.add_argument("--out", default=None, help="输出 jsonl（缺省 processed/original_requirements_v1.jsonl）")
    args = ap.parse_args()

    cfg = get_config()
    if not cfg.ernie.enabled:
        print("ERNIE 未配置 API key（.env）。"); sys.exit(1)
    client = cfg.ernie.make_client()
    kb_texts = list(load_evidence_text_map(cfg.paths.evidence_units_jsonl).values())

    collected: list[dict] = []
    attempts = 0
    max_attempts = max(8, (args.n // args.batch_size) * 3 + 4)
    while len(collected) < args.n and attempts < max_attempts:
        attempts += 1
        # 轮换主题切片，促进多样性
        topics = SEED_TOPICS[(attempts * 3) % len(SEED_TOPICS):][:6] or SEED_TOPICS[:6]
        prompt = build_generation_prompt(n=args.batch_size, seed_topics=topics)
        # 反重复后缀：避免与已生成需求雷同（提升多样性）
        if collected:
            sample = [c["requirement_text"] for c in collected[-12:]]
            prompt += "\n\n请勿与以下已有需求重复或近义改写：\n- " + "\n- ".join(sample)
        try:
            # 直连 client（不走缓存）：出题要多样性采样，缓存会让相同 prompt 返回同一批
            resp = client.chat.completions.create(
                model=cfg.ernie.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # 出题阶段要多样性，非确定
                max_tokens=3000,
                response_format={"type": "json_object"},
            )
            batch = parse_generated(resp.choices[0].message.content or "{}",
                                    start_index=1, prefix="TMP")
        except Exception as exc:
            print(f"[warn] 第 {attempts} 批生成失败：{exc}")
            continue
        collected.extend(batch)
        collected = _dedupe(collected, args.sim_threshold)
        print(f"[batch {attempts}] 累计去重后 {len(collected)} 条")

    # 重新分配稳定 ID
    for i, r in enumerate(collected, start=1):
        r["requirement_id"] = f"OR{i:03d}"

    # KB 查重，剔除疑似照抄
    report = quality_check(collected, kb_texts, sim_threshold=args.sim_threshold)
    suspect = {r["requirement_id"] for r in report if r["kb_copy_suspect"]}
    clean = [r for r in collected if r["requirement_id"] not in suspect]
    for i, r in enumerate(clean, start=1):  # 剔除后再次稳定 ID
        r["requirement_id"] = f"OR{i:03d}"

    out_path = Path(args.out) if args.out else cfg.paths.processed_dir / "original_requirements_v1.jsonl"
    write_jsonl(out_path, clean)
    max_sim = max((r["max_kb_similarity"] for r in report), default=0.0)
    print(f"\n生成 {len(collected)} 条 → KB 照抄剔除 {len(suspect)} 条 → 冻结 {len(clean)} 条")
    print(f"最大 KB 相似度 {max_sim:.3f}（阈值 {args.sim_threshold}）")
    print(f"-> {out_path}")
    if len(clean) < args.n:
        print(f"[note] 实得 {len(clean)} < 目标 {args.n}，可加大 --batch-size 或 max_attempts 重跑。")


if __name__ == "__main__":
    main()
