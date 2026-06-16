"""
Phase 4: 用分层KB重新运行 RAG v3 vs no-RAG 对比实验，计算合规指标。

本脚本是 Phase 4 的完整入口：
  1. 重建索引（使用 evidence_units_tiered.jsonl，过滤 L3 作为背景）
  2. 重跑 RAG v3 实验（60条原始需求）
  3. 重跑 no-RAG 基线实验
  4. 计算三项合规指标（RCR / CC / RR）

前置条件:
  - Phase 3 完成: evidence_units_tiered.jsonl 已生成
  - Phase 1 完成（可选但建议）: CCS L1 单元已追加到 evidence_units.jsonl
    如果 Phase 1 未完成，本脚本使用现有 KB 的 93 条 ship_rule 单元作为 L1

用法:
  python scripts/65_run_compliance_experiment.py
  python scripts/65_run_compliance_experiment.py --skip-run  # 只重算指标（实验已跑）
  python scripts/65_run_compliance_experiment.py --n-reqs 10 # 仅处理前10条需求（快速验证）
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DATA         = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR  = PROJECT_ROOT / "data" / "search_results"
INDEXES_DIR  = PROJECT_ROOT / "data" / "indexes"

TIERED_UNITS    = DATA / "evidence_units_tiered.jsonl"
UNITS_PATH      = DATA / "evidence_units.jsonl"
SRC_CHUNKS_PATH = DATA / "source_chunks.jsonl"

ORIG_REQS  = DATA / "original_requirements_v1.jsonl"
EXP_DIR    = RESULTS_DIR / "exp_v3_tiered"
RAG_OUT    = EXP_DIR / "rag_v3_results.json"
NORAG_OUT  = EXP_DIR / "norag_results.json"


def _rebuild_indexes_with_tiers(tiered_path: Path, units_path: Path) -> None:
    """
    用分层 KB 重建索引。
    L3 单元（纯背景）降级为 evidence_strength=background，
    不参与主要检索但保留在库中以备参考。
    """
    print("重建分层KB索引...")

    if not tiered_path.exists():
        print(f"[WARN] 未找到分层KB文件: {tiered_path}")
        print("  将使用原始 evidence_units.jsonl（未分层）")
        return

    # 读分层结果
    tiered: dict[str, dict] = {}
    with open(tiered_path, encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            tiered[u["id"]] = u

    # 读原始单元
    with open(units_path, encoding="utf-8") as f:
        units = [json.loads(l) for l in f]

    # 将分层信息写回单元
    updated = []
    n_l1 = n_l2 = n_l3 = 0
    for unit in units:
        uid = unit["id"]
        tier_info = tiered.get(uid, {})
        tier = tier_info.get("kb_tier", 3)

        # 更新单元
        unit["kb_tier"] = tier
        unit["tier_reason"] = tier_info.get("tier_reason", "")

        # L3 → 降级 evidence_strength 为 background（影响检索行为）
        if tier == 3:
            if isinstance(unit.get("metadata"), dict):
                unit["metadata"]["evidence_strength"] = "background"
            n_l3 += 1
        elif tier == 2:
            n_l2 += 1
        elif tier == 1:
            # L1 → 确保标记为 direct（规范条文）
            if isinstance(unit.get("metadata"), dict):
                if unit["metadata"].get("evidence_strength") != "direct":
                    unit["metadata"]["evidence_strength"] = "direct"
            n_l1 += 1

        updated.append(unit)

    print(f"  KB分层: L1={n_l1}, L2={n_l2}, L3={n_l3}（L3降级为background）")

    # 备份原始文件
    backup = units_path.with_suffix(".jsonl.before_tier")
    if not backup.exists():
        shutil.copy2(units_path, backup)
        print(f"  原始KB已备份: {backup.name}")

    # 写更新后的KB
    with open(units_path, "w", encoding="utf-8") as f:
        for u in updated:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"  已更新 {len(updated)} 条单元")

    # 重建索引
    print("  重建FAISS+BM25索引...")
    import subprocess
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "11_build_multigranular_indexes.py")],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.returncode == 0:
        print("  [OK] 索引重建完成")
    else:
        print(f"  [WARN] 索引重建失败: {result.stderr[-200:]}")


def _run_rag_v3(n_reqs: int | None, out_path: Path) -> None:
    """运行 RAG v3 实验（使用 req_generation_v2.generate_rag_v3）"""
    print(f"\n运行 RAG v3 实验...")

    from cooling_rag_mg.config import get_config
    from cooling_rag_mg.coverage_retrieval import aligned_retrieve
    from cooling_rag_mg.req_generation_v2 import generate_rag_v3
    from cooling_rag_mg.index_store import HybridIndexSearcher, load_index

    cfg = get_config()
    if not cfg.deepseek.enabled:
        print("需要 DeepSeek API key 运行 RAG 实验")
        return

    ds_client = cfg.deepseek.make_client()
    ds_model  = cfg.deepseek.model
    device    = getattr(cfg, "device", "cpu")

    # 加载索引
    idx_dir  = PROJECT_ROOT / "data" / "indexes" / "evidence_units"
    idx      = load_index(idx_dir)
    searcher = HybridIndexSearcher(idx, device=device)

    # 加载原始需求
    with open(ORIG_REQS, encoding="utf-8") as f:
        reqs = [json.loads(l) for l in f]
    if n_reqs:
        reqs = reqs[:n_reqs]

    result_sets = []
    for i, req in enumerate(reqs, 1):
        req_id   = req.get("requirement_id", req.get("id", f"R{i:03d}"))
        req_text = req.get("requirement_text", req.get("text", req.get("content", "")))
        print(f"  [{i}/{len(reqs)}] {req_id}: {req_text[:60]}...")

        try:
            evidence_list, pairs_used = aligned_retrieve(
                req_text, searcher, ds_client, ds_model,
            )
            print(f"    aligned_retrieve: {len(pairs_used)} 对 → {len(evidence_list)} 条证据")

            ers = generate_rag_v3(req_text, evidence_list, ds_client, ds_model)
            result_sets.append({
                "source_requirement_id": req_id,
                "engineering_requirements": ers,
            })

        except Exception as ex:
            print(f"    失败: {ex}")
            result_sets.append({
                "source_requirement_id": req_id,
                "engineering_requirements": [],
                "_error": str(ex),
            })

        if i % 10 == 0:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({"arm": "RAG_v3_tiered", "result_sets": result_sets}, f,
                          ensure_ascii=False, indent=2)
            print(f"    [checkpoint] 已保存 {i} 条")
        time.sleep(0.1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"arm": "RAG_v3_tiered", "result_sets": result_sets}, f,
                  ensure_ascii=False, indent=2)

    n_shalls = sum(len(rs.get("engineering_requirements", [])) for rs in result_sets)
    print(f"RAG v3 完成: {len(result_sets)} 源需求, {n_shalls} 个shall")


def _run_norag(n_reqs: int | None, out_path: Path) -> None:
    """运行 no-RAG 强基线（DeepSeek 直接生成，不阉割，可生成具体参数）"""
    print(f"\n运行 no-RAG 基线实验...")

    from cooling_rag_mg.config import get_config
    from cooling_rag_mg.json_utils import loads_lenient

    cfg = get_config()
    if not cfg.deepseek.enabled:
        print("[WARN] 需要 DeepSeek API key")
        return

    client = cfg.deepseek.make_client()

    _SYSTEM = """\
你是船舶主机冷却水系统的专业需求工程师。
将给定需求转化为结构化工程需求(shall语句)。
规则：
- shall_statement 用清晰工程语言书写，可根据专业知识提供具体参数和数值
- verification_method 取值: review/inspection/calculation/test
- acceptance_criteria 给出具体可接受标准（含数值）
只输出JSON: {"engineering_requirements":[{"shall_statement":"...","verification_method":"...","acceptance_criteria":"...","evidence_ids":[]}]}"""

    with open(ORIG_REQS, encoding="utf-8") as f:
        reqs = [json.loads(l) for l in f]
    if n_reqs:
        reqs = reqs[:n_reqs]

    result_sets = []
    for i, req in enumerate(reqs, 1):
        req_id   = req.get("requirement_id", req.get("id", f"R{i:03d}"))
        req_text = req.get("requirement_text", req.get("text", req.get("content", "")))
        print(f"  [{i}/{len(reqs)}] {req_id}")

        try:
            resp = client.chat.completions.create(
                model=cfg.deepseek.model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": f"需求: {req_text}"},
                ],
                temperature=0.0,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            obj = loads_lenient(raw) or {}
            ers = obj.get("engineering_requirements", [])
            result_sets.append({
                "source_requirement_id": req_id,
                "engineering_requirements": ers,
            })
        except Exception as ex:
            print(f"    [WARN] 失败: {ex}")
            result_sets.append({
                "source_requirement_id": req_id,
                "engineering_requirements": [],
                "_error": str(ex),
            })
        time.sleep(0.1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"arm": "no_RAG_tiered", "result_sets": result_sets}, f,
                  ensure_ascii=False, indent=2)

    n_shalls = sum(len(rs.get("engineering_requirements", [])) for rs in result_sets)
    print(f"no-RAG 完成: {len(result_sets)} 源需求, {n_shalls} 个shall")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-run",  action="store_true", help="跳过实验，只重算指标")
    ap.add_argument("--skip-index", action="store_true", help="跳过索引重建")
    ap.add_argument("--n-reqs", type=int, default=0, help="只处理前N条需求（0=全部）")
    args = ap.parse_args()

    n = args.n_reqs or None

    if not args.skip_run:
        # Step 1: 重建分层索引
        if not args.skip_index:
            _rebuild_indexes_with_tiers(TIERED_UNITS, UNITS_PATH)

        # Step 2: 运行 RAG v3
        _run_rag_v3(n, RAG_OUT)

        # Step 3: 运行 no-RAG
        _run_norag(n, NORAG_OUT)

    # Step 4: 计算合规指标
    print("\n计算合规指标...")
    import subprocess
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "64_compliance_metrics.py"),
            "--rag-file",   str(RAG_OUT),
            "--norag-file", str(NORAG_OUT),
        ],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        encoding="utf-8", errors="replace",
    )
    sys.stdout.buffer.write(result.stdout.encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    if result.stderr:
        sys.stdout.buffer.write(("STDERR: " + result.stderr[-500:]).encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()

    print("\n=== Phase 4 完成 ===")
    print(f"RAG结果:   {RAG_OUT}")
    print(f"no-RAG结果: {NORAG_OUT}")
    print(f"合规报告:   {RESULTS_DIR}/compliance_metrics.json")


if __name__ == "__main__":
    main()
