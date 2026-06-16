# scripts/52_enrich_metadata.py
"""
Phase 1 — 元数据重标注：为每条 evidence_unit 分配精确的
(primary_component, primary_intent)，对齐新 taxonomy。

处理范围（来自 metadata_audit.csv）：
  cooling_system_placeholder (344)  — 需 LLM 重新识别具体部件
  multi_need_pick            (464)  — 有多个合法对，需 LLM 择优
  taxonomy_gap               ( 24)  — 边界情况，标记待人工确认
  ok_exact                   (367)  — 已有唯一对，自动继承，不调 API

输出：
  data/processed/metadata_enriched_review.csv   ← 人工抽查用
  data/processed/metadata_enriched.jsonl        ← 合并前的完整结果

用法：
  python scripts/52_enrich_metadata.py --limit 10   # 冒烟
  python scripts/52_enrich_metadata.py              # 全量（约 800 次 API 调用）
  python scripts/52_enrich_metadata.py --resume     # 断点续跑（跳过已有结果的条目）
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.evidence_taxonomy import (
    COMPONENTS, INTENTS, TAXONOMY, all_pairs, get_intents_for, valid_pair,
)
from cooling_rag_mg.json_utils import loads_lenient

# ── 路径 ────────────────────────────────────────────────────────────────────
DATA = PROJECT_ROOT / "data" / "processed"
UNITS_PATH  = DATA / "evidence_units.jsonl"
AUDIT_PATH  = DATA / "metadata_audit.csv"
OUT_REVIEW  = DATA / "metadata_enriched_review.csv"
OUT_JSONL   = DATA / "metadata_enriched.jsonl"

# ── Taxonomy 辅助字符串（给 LLM 的说明）────────────────────────────────────

def _comp_menu() -> str:
    lines = []
    for c, desc in COMPONENTS.items():
        lines.append(f"  {c}: {desc}")
    return "\n".join(lines)

def _intent_menu(component: str) -> str:
    intents = get_intents_for(component)
    lines = []
    for i in intents:
        desc = INTENTS.get(i, "")
        lines.append(f"  {i}: {desc}")
    return "\n".join(lines) if lines else "  （该部件暂无方面列表）"

def _combos_menu(combos: list[tuple[str, str]]) -> str:
    lines = []
    for c, i in combos:
        cdesc = COMPONENTS.get(c, c)
        idesc = INTENTS.get(i, i)
        lines.append(f"  {c} × {i}  |  {cdesc} — {idesc}")
    return "\n".join(lines)

# ── Prompt 构造 ──────────────────────────────────────────────────────────────

_SYS = (
    "你是船舶主机冷却水系统需求工程专家。"
    "请根据证据文本，从给定的 taxonomy 中选择**最精确、最贴切**的"
    "（primary_component，primary_intent）组合。"
    "每条证据只选一个组合。只输出 JSON，不要任何解释。"
)

def _prompt_placeholder(text: str, source_doc: str) -> str:
    """用于 cooling_system_placeholder：从零识别部件+方面。"""
    return (
        f"证据来源文档：{source_doc}\n"
        f"证据文本：\n{text}\n\n"
        f"可选部件（选1个）：\n{_comp_menu()}\n\n"
        "从选定部件的方面列表中再选1个方面（不同部件方面不同，选定部件后我会列出可选方面，"
        "你先在JSON里给出部件，再给出方面）。\n"
        '输出JSON格式：{"primary_component":"<部件>","primary_intent":"<方面>","reason":"<一句话理由>"}'
    )

def _prompt_multi(text: str, combos: list[tuple[str, str]]) -> str:
    """用于 multi_need_pick：从候选组合中选最贴切的。"""
    return (
        f"证据文本：\n{text}\n\n"
        f"候选（部件×方面）组合如下，请选择最精确描述该证据核心内容的那一个：\n"
        f"{_combos_menu(combos)}\n\n"
        '输出JSON格式：{"primary_component":"<部件>","primary_intent":"<方面>","reason":"<一句话理由>"}'
    )

# ── LLM 调用（两步：placeholder 需先拿部件再补全方面列表）──────────────────

def _call(client, model: str, prompt: str, temperature: float = 0.0) -> dict:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYS},
            {"role": "user",   "content": prompt},
        ],
        temperature=temperature,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    return loads_lenient(raw) or {}


def _two_step_placeholder(client, model: str, text: str, source_doc: str) -> dict:
    """
    Step-1：让 LLM 先选 component（给完整部件列表）。
    Step-2：用选定的 component 补全方面列表，再让 LLM 选 intent。
    合法性兜底：若不合法则返回 fallback。
    """
    # Step-1: 选部件
    step1_prompt = (
        f"证据来源文档：{source_doc}\n"
        f"证据文本：\n{text[:600]}\n\n"
        f"请从以下部件中选出最匹配该证据核心内容的部件（选1个）：\n{_comp_menu()}\n\n"
        '只输出JSON：{"primary_component":"<部件>"}'
    )
    r1 = _call(client, model, step1_prompt)
    comp = r1.get("primary_component", "").strip()
    if comp not in COMPONENTS:
        return {"primary_component": "cooling_system",
                "primary_intent":   "system_description",
                "reason": "step1 invalid comp, fallback",
                "needs_review": True}

    # Step-2: 选方面
    step2_prompt = (
        f"证据文本：\n{text[:600]}\n\n"
        f"已确定部件：{comp}（{COMPONENTS[comp]}）\n"
        f"该部件的可选工程方面如下，请选1个最贴切的：\n{_intent_menu(comp)}\n\n"
        '只输出JSON：{"primary_intent":"<方面>","reason":"<一句话>"}'
    )
    r2 = _call(client, model, step2_prompt)
    intent = r2.get("primary_intent", "").strip()
    reason = r2.get("reason", "")

    if not valid_pair(comp, intent):
        # 取该部件第一个合法 intent 作为 fallback
        fallback_intent = get_intents_for(comp)[0] if get_intents_for(comp) else "specification"
        return {"primary_component": comp, "primary_intent": fallback_intent,
                "reason": f"step2 invalid intent '{intent}', fallback",
                "needs_review": True}

    return {"primary_component": comp, "primary_intent": intent,
            "reason": reason, "needs_review": False}


def _pick_multi(client, model: str, text: str,
                combos: list[tuple[str, str]]) -> dict:
    prompt = _prompt_multi(text[:600], combos)
    r = _call(client, model, prompt)
    comp   = r.get("primary_component", "").strip()
    intent = r.get("primary_intent", "").strip()
    reason = r.get("reason", "")

    if valid_pair(comp, intent):
        return {"primary_component": comp, "primary_intent": intent,
                "reason": reason, "needs_review": False}

    # fallback: 取第一个候选
    c0, i0 = combos[0]
    return {"primary_component": c0, "primary_intent": i0,
            "reason": f"LLM output invalid ({comp}×{intent}), fallback to first candidate",
            "needs_review": True}

# ── 主程序 ───────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="冒烟模式：只处理前 N 条非 ok_exact 的记录")
    ap.add_argument("--resume", action="store_true",
                    help="断点续跑：跳过 OUT_JSONL 里已有结果的条目")
    args = ap.parse_args()

    cfg   = get_config()
    if not cfg.deepseek.enabled:
        sys.exit("需要 DeepSeek API key（.env DEEPSEEK_API_KEY）")
    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model

    # ── 读入数据 ──
    units_by_id: dict[str, dict] = {}
    with open(UNITS_PATH, encoding="utf-8") as f:
        for line in f:
            u = json.loads(line)
            units_by_id[u["id"]] = u

    audit: dict[str, dict] = {}
    with open(AUDIT_PATH, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            audit[row["id"]] = row

    # ── 断点续跑：加载已有结果 ──
    done: dict[str, dict] = {}
    if args.resume and OUT_JSONL.exists():
        with open(OUT_JSONL, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                done[rec["id"]] = rec
        print(f"Resume: {len(done)} 条已完成，跳过。")

    # ── 解析旧 component→新 component 映射 ──
    old_comp_map = {
        'main_engine_cooling_water_system':'cooling_system',
        'cooling_water_pump':'cooling_water_pump',
        'ht_cooling_water_loop':'cooling_system',
        'lt_cooling_water_loop':'cooling_system',
        'expansion_tank':'expansion_tank','cooler':'cooler',
        'temperature_control_valve':'temperature_control_valve',
        'pipe':'pipe','sea_water_cooling_system':'cooling_system',
        'jacket_water_cooling_system':'cooling_system',
        'valve':'valve','alarm_system':'alarm_system',
        'central_cooling_system':'cooling_system',
        'temperature_sensor':'temperature_sensor',
        'control_system':'control_system','level_sensor':'level_sensor',
        'equipment_interface':'cooling_system','filter':'filter',
        'pressure_sensor':'pressure_sensor','drain_point':'pipe',
        'sensor':'temperature_sensor','technical_file':'cooling_system',
        'vent_point':'pipe','coolant':'coolant',
    }
    old_intent_map = {
        'temperature':'alarm_setpoint','pressure':'specification',
        'water_quality':'water_quality','installation':'installation',
        'control':'control_logic','composition':'corrosion_inhibitor',
        'inspection':'inspection','flow':'specification',
        'configuration':'installation','corrosion_protection':'corrosion_protection',
        'cleaning':'cleaning','reliability':'redundancy','maintenance':'maintenance',
        'capacity':'specification','redundancy':'redundancy',
        'drawing_review':'drawing_requirement','monitoring':'alarm_setpoint',
        'environmental_protection':'environmental_protection','arrangement':'installation',
        'alarm':'alarm_setpoint','function':'system_description','flushing':'cleaning',
        'calculation':'documentation','shutdown':'trip_setpoint','material':'material',
        'accessibility':'installation','pressure_test':'pressure_test',
        'parameter_limit':'alarm_setpoint','operation':'maintenance','test':'test_procedure',
        'load_reduction':'control_logic','commissioning_check':'test_procedure',
        'safety':'trip_setpoint','equipment_selection':'specification',
        'commissioning':'test_procedure','class_review':'class_approval',
        'document_completeness':'documentation','system_design':'system_description',
    }

    def get_meta(u, key):
        v = u.get(key) or u.get("metadata", {}).get(key)
        return ([v] if isinstance(v, str) else v) or []

    # ── 确定处理队列 ──
    queue = []
    auto_ok = []
    for uid, row in audit.items():
        if uid in done:
            continue
        issue = row["issue"]
        u = units_by_id.get(uid)
        if not u:
            continue

        if issue == "ok_exact":
            # 直接读唯一合法对
            combo_str = row["valid_combos"]  # e.g. "cooling_water_pump×specification"
            if "×" in combo_str:
                c, i = combo_str.split("×", 1)
                auto_ok.append({"id": uid, "primary_component": c,
                                 "primary_intent": i, "issue": issue,
                                 "reason": "auto_exact", "needs_review": False})
        else:
            queue.append((uid, issue, u, row))

    if args.limit:
        queue = queue[:args.limit]

    print(f"自动继承 ok_exact: {len(auto_ok)} 条")
    print(f"需 LLM 处理: {len(queue)} 条"
          + (f"（限制 {args.limit}）" if args.limit else ""))

    # ── 写出 ok_exact ──
    results: list[dict] = list(done.values()) + auto_ok

    # ── LLM 处理队列 ──
    n_api = 0
    n_err = 0
    for idx, (uid, issue, u, row) in enumerate(queue, 1):
        text       = u.get("text", "")
        source_doc = u.get("metadata", {}).get("source_document", "")
        old_comps  = get_meta(u, "component_objects")
        old_ints   = get_meta(u, "requirement_intents")
        new_comps  = list(dict.fromkeys(old_comp_map.get(c, "?") for c in old_comps))
        new_ints   = list(dict.fromkeys(old_intent_map.get(i, "?") for i in old_ints))
        valid_combos = [(c, i) for c in new_comps for i in new_ints if valid_pair(c, i)]

        try:
            if issue in ("cooling_system_placeholder", "taxonomy_gap"):
                res = _two_step_placeholder(client, model, text, source_doc)
            else:  # multi_need_pick
                res = _pick_multi(client, model, text, valid_combos)
            n_api += 1
        except Exception as e:
            res = {"primary_component": new_comps[0] if new_comps else "cooling_system",
                   "primary_intent":   new_ints[0] if new_ints else "system_description",
                   "reason": f"error: {e}", "needs_review": True}
            n_err += 1

        rec = {"id": uid, "issue": issue,
               "primary_component": res["primary_component"],
               "primary_intent":    res["primary_intent"],
               "reason":            res.get("reason", ""),
               "needs_review":      res.get("needs_review", False),
               "old_components": row["old_components"],
               "old_intents":    row["old_intents"],
               "text_snippet":   text[:150].replace("\n", " ")}
        results.append(rec)

        if idx % 50 == 0 or idx == len(queue):
            print(f"  [{idx}/{len(queue)}] API调用={n_api} 错误={n_err}")
            # 中间落盘（断点保护）
            _flush_jsonl(results, OUT_JSONL)

        time.sleep(0.15)  # 避免限流

    _flush_jsonl(results, OUT_JSONL)

    # ── 写 review CSV（重点看 needs_review=True 的） ──
    review_rows = [r for r in results if r.get("needs_review")]
    _write_review_csv(results, review_rows)

    # ── 汇总 ──
    from collections import Counter
    comp_dist  = Counter(r["primary_component"] for r in results)
    intent_dist = Counter(r["primary_intent"] for r in results)
    need_rev   = sum(1 for r in results if r.get("needs_review"))

    print()
    print("=" * 55)
    print("重标注完成")
    print("=" * 55)
    print(f"总记录: {len(results)}")
    print(f"需人工复查 (needs_review=True): {need_rev}")
    print()
    print("primary_component 分布 (Top 12):")
    for c, n in comp_dist.most_common(12):
        print(f"  {c:<30s} {n:4d}")
    print()
    print("primary_intent 分布 (Top 15):")
    for i, n in intent_dist.most_common(15):
        print(f"  {i:<30s} {n:4d}")
    print()
    print(f"结果文件: {OUT_JSONL}")
    print(f"复查文件: {OUT_REVIEW}（{need_rev} 条需核查）")
    print()
    print("确认无误后运行：")
    print("  python scripts/53_apply_metadata.py")


def _flush_jsonl(results: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_review_csv(all_results: list[dict], review_rows: list[dict]) -> None:
    fields = ["id", "issue", "primary_component", "primary_intent",
              "needs_review", "reason", "old_components", "old_intents",
              "text_snippet",
              "human_component", "human_intent", "human_ok"]
    with open(OUT_REVIEW, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        # 先写 needs_review 的，再写全量（方便整体查看）
        for r in review_rows:
            w.writerow({**r, "human_component": "", "human_intent": "", "human_ok": ""})
        for r in all_results:
            if not r.get("needs_review"):
                w.writerow({**r, "human_component": "", "human_intent": "", "human_ok": ""})


if __name__ == "__main__":
    main()
