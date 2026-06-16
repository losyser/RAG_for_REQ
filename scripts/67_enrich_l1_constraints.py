#!/usr/bin/env python3
"""
Script 67: L1 constraint field enrichment via DeepSeek (Step 3)

For each L1 unit in evidence_units_v2.jsonl:
  - Calls DeepSeek to extract structured constraint fields from source text
  - Only extracts what is stated in the text (authenticity-first)
  - Saves checkpoint after every unit (safe to interrupt and resume)

Checkpoint: data/processed/l1_constraints_checkpoint.jsonl
Output: updates evidence_units_v2.jsonl constraint fields in-place
"""

import json
import os
import sys
import time
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
KB_V2       = Path("data/processed/evidence_units_v2.jsonl")
CHECKPOINT  = Path("data/processed/l1_constraints_checkpoint.jsonl")

# ── Config ───────────────────────────────────────────────────────────────────
MAX_TOKENS  = 1200
TEMPERATURE = 0.0
SLEEP_SEC   = 0.5       # between API calls

SYSTEM_PROMPT = """你是一位船舶工程规范分析专家。你的任务是从规范原文中提取结构化约束信息。

核心原则：
1. 只提取原文中明确陈述的信息
2. 原文未提及的字段返回 null 或空列表 []
3. 不得推断、补充或发明原文未包含的数值、条文号或交叉引用
4. 关联条文只包含原文中显式引用的其他规范条款

输出格式：纯 JSON，不加任何解释文字"""

EXTRACTION_PROMPT = """从以下规范条目中提取结构化约束信息，输出纯 JSON。

来源文件: {source_document}
来源类型: {source_type}
主题: {topic}
条文/章节: {section}
主要组件: {primary_component}
约束意图: {primary_intent}

原文:
{text}

输出以下 JSON 结构（严格按格式，不加说明）：
{{
  "规范依据": "具体条文编号，如'第7-25条1.6款'或'Section 13.5.2'；如原文未给明确编号则 null",
  "规范版本": "版本年份，如'2021版'；原文未提及则 null",
  "强制级别": "基于原文措辞：shall/must/应/不得/必须 → '强制'；should/宜 → '推荐'；may/可 → '可选'；其他 → '参考'",
  "约束类型": "从以下选一：redundancy / alarm_protection / alarm_setpoint / parameter_limit / material_spec / inspection_test / certification / calculation / installation_req / operational_req",
  "适用对象": "原文描述的具体设备或系统（中文）",
  "核心要求": "1-2句，直接基于原文，用SHALL语句描述核心要求（中文）",
  "可接受标准": "定量判据如'≥2台'、'≤36°C'、'2×100%容量'；原文没有定量标准则 null",
  "验证方式": "从以下选一：设计审查 / 计算验证 / 图纸送审 / 工厂试验 / 码头试验 / 海试 / 目视检查 / 文件审查",
  "关联条文": ["只列原文明确引用的其他规范条文，如无则空列表 []"],
  "适用船型": ["原文明确限定的船型，如无限制则 null"],
  "_extraction_meta": {{
    "core_req_source": "stated（原文直接陈述）或 summarized（对原文概括改写）",
    "acceptance_criteria_source": "stated / absent",
    "verification_source": "stated（原文有明确说明）或 inferred（根据约束类型推断）",
    "mandatory_level_source": "stated（措辞明确）或 inferred（根据来源类型推断）"
  }}
}}"""


def load_checkpoint() -> dict:
    if not CHECKPOINT.exists():
        return {}
    done = {}
    with open(CHECKPOINT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                obj = json.loads(line)
                done[obj["unit_id"]] = obj["constraint"]
    return done


def save_checkpoint(unit_id: str, constraint: dict) -> None:
    with open(CHECKPOINT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"unit_id": unit_id, "constraint": constraint},
                            ensure_ascii=False) + "\n")


def call_deepseek(client, model: str, unit: dict) -> dict | None:
    m   = unit.get("metadata", {})
    section = m.get("section_title", "") or ""
    topic   = m.get("topic", "") or ""

    user_msg = EXTRACTION_PROMPT.format(
        source_document  = unit.get("source_document", ""),
        source_type      = unit.get("source_type", ""),
        topic            = topic,
        section          = section,
        primary_component= unit.get("primary_component", ""),
        primary_intent   = unit.get("primary_intent", ""),
        text             = unit.get("text", "")[:2000],   # cap to avoid token overflow
    )

    try:
        resp = client.chat.completions.create(
            model       = model,
            messages    = [
                {"role": "system",  "content": SYSTEM_PROMPT},
                {"role": "user",    "content": user_msg},
            ],
            max_tokens  = MAX_TOKENS,
            temperature = TEMPERATURE,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse error for {unit['unit_id']}: {e}")
        return None
    except Exception as e:
        print(f"  [ERR] API error for {unit['unit_id']}: {e}")
        return None


def merge_constraint(skeleton: dict, extracted: dict) -> dict:
    """Merge extracted fields into skeleton, keeping _extraction_meta."""
    fields = [
        "规范依据", "规范版本", "强制级别", "约束类型", "适用对象",
        "核心要求", "可接受标准", "验证方式", "关联条文", "适用船型",
    ]
    updated = dict(skeleton)
    for f in fields:
        if f in extracted:
            updated[f] = extracted[f]
    if "_extraction_meta" in extracted:
        updated["_extraction_meta"] = extracted["_extraction_meta"]
    return updated


def apply_checkpoint_to_kb(checkpoint: dict) -> None:
    """Write checkpoint results back into evidence_units_v2.jsonl."""
    with open(KB_V2, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]

    updated = 0
    for u in units:
        if u["kb_tier"] == "L1" and u["unit_id"] in checkpoint:
            u["constraint"] = checkpoint[u["unit_id"]]
            updated += 1

    with open(KB_V2, "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    print(f"[OK] Applied {updated} constraint updates -> {KB_V2}")


def main():
    # ── Setup ────────────────────────────────────────────────────────────────
    sys.path.insert(0, str(Path(".")))
    from cooling_rag_mg.config import get_config
    cfg = get_config()

    if not cfg.deepseek.enabled:
        sys.exit("[ERR] DeepSeek API key not found in environment")

    client = cfg.deepseek.make_client()
    model  = cfg.deepseek.model
    print(f"Model: {model}")

    # ── Load KB and checkpoint ───────────────────────────────────────────────
    with open(KB_V2, encoding="utf-8") as f:
        units = [json.loads(l) for l in f if l.strip()]

    l1_units = [u for u in units if u["kb_tier"] == "L1"]
    checkpoint = load_checkpoint()

    todo = [u for u in l1_units if u["unit_id"] not in checkpoint]
    print(f"L1 units: {len(l1_units)} total, {len(checkpoint)} already done, {len(todo)} remaining")
    print()

    if not todo:
        print("All L1 units already enriched. Applying to KB file...")
        apply_checkpoint_to_kb(checkpoint)
        return

    # ── Process ──────────────────────────────────────────────────────────────
    errors = 0
    for i, unit in enumerate(todo, 1):
        uid = unit["unit_id"]
        print(f"[{i}/{len(todo)}] {uid}")

        result = call_deepseek(client, model, unit)
        if result is None:
            errors += 1
            # Store the skeleton with a failure marker so we don't retry indefinitely
            failed_skeleton = dict(unit.get("constraint", {}))
            failed_skeleton["_llm_error"] = True
            save_checkpoint(uid, failed_skeleton)
            time.sleep(SLEEP_SEC * 3)
            continue

        merged = merge_constraint(unit.get("constraint", {}), result)
        save_checkpoint(uid, merged)

        # Print brief summary
        print(f"  强制级别={merged.get('强制级别')}  "
              f"核心要求={str(merged.get('核心要求',''))[:50]}...")

        time.sleep(SLEEP_SEC)

    # ── Apply all results to KB ───────────────────────────────────────────────
    print()
    final_checkpoint = load_checkpoint()
    apply_checkpoint_to_kb(final_checkpoint)

    print()
    print(f"Done. Errors: {errors}/{len(todo)}")
    if errors:
        print(f"Re-run this script to retry failed units (checkpoint preserves successes).")


if __name__ == "__main__":
    main()
