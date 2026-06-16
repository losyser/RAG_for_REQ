# -*- coding: utf-8 -*-
"""
Shall 正确性核查界面（Streamlit）

运行：
  streamlit run scripts/shall_review_ui.py --server.port 8505

功能：
  - 从 rag_v4_results.json 分层抽样 30 条 shall（A×10 / B×10 / C×10）
  - 每条显示：源需求 / shall文本 / measurable_criterion / 引用证据原文
  - 人工标注：正确 / 错误 / 部分正确
  - 结果保存到 data/search_results/exp_v4/shall_review_results.json
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RAG_FILE    = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OR_JSONL    = ROOT / "data/processed/original_requirements_v2.jsonl"
EU_JSONL    = ROOT / "data/processed/evidence_units_v2.jsonl"
RESULT_FILE = ROOT / "data/search_results/exp_v4/shall_review_results.json"
SAMPLE_FILE = ROOT / "data/search_results/exp_v4/shall_review_sample.json"

SEED = 42
QUOTA = {"A": 10, "B": 10, "C": 10}

# ── 数据层 ────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_or_map() -> dict[str, str]:
    m: dict[str, str] = {}
    with open(OR_JSONL, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            m[r["requirement_id"]] = r.get("requirement_text", "")
    return m


@st.cache_data(show_spinner=False)
def load_eu_map() -> dict[str, str]:
    m: dict[str, str] = {}
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            eu = json.loads(line)
            m[eu["id"]] = eu.get("text", "")
    return m


@st.cache_data(show_spinner=False)
def load_sample() -> list[dict]:
    if SAMPLE_FILE.exists():
        with open(SAMPLE_FILE, encoding="utf-8") as f:
            return json.load(f)

    with open(RAG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    or_map = load_or_map()

    buckets: dict[str, list[dict]] = {"A": [], "B": [], "C": []}
    for rs in data["result_sets"]:
        or_id   = rs.get("source_requirement_id", "")
        or_text = or_map.get(or_id, "")
        for er in rs.get("engineering_requirements", []):
            g = er.get("_grade", "")
            if g not in buckets:
                continue
            buckets[g].append({
                "uid":        f"{or_id}__{er.get('shall_statement','')[:30]}",
                "or_id":      or_id,
                "or_text":    or_text,
                "shall":      er.get("shall_statement", ""),
                "criterion":  er.get("measurable_criterion", ""),
                "condition":  er.get("applicable_condition", ""),
                "verification": er.get("verification_method", ""),
                "grade":      g,
                "citations":  er.get("evidence_citations", []),
            })

    rng = random.Random(SEED)
    sample: list[dict] = []
    for g, n in QUOTA.items():
        pool = buckets[g]
        picked = rng.sample(pool, min(n, len(pool)))
        sample.extend(picked)

    # stable unique ID
    for i, item in enumerate(sample):
        item["seq"] = i

    SAMPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)

    load_sample.clear()
    return sample


def load_results() -> dict[str, dict]:
    if RESULT_FILE.exists():
        with open(RESULT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: dict[str, dict]):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def compute_stats(sample: list[dict], results: dict) -> dict:
    reviewed = [it for it in sample if it["uid"] in results]
    by_grade: dict[str, dict] = {}
    for it in reviewed:
        g = it["grade"]
        r = results[it["uid"]]["verdict"]
        if g not in by_grade:
            by_grade[g] = {"correct": 0, "partial": 0, "wrong": 0}
        by_grade[g][r] = by_grade[g].get(r, 0) + 1
    total_correct = sum(v["correct"] for v in by_grade.values())
    total_partial = sum(v.get("partial", 0) for v in by_grade.values())
    total_reviewed = len(reviewed)
    return {
        "reviewed":       total_reviewed,
        "total":          len(sample),
        "total_correct":  total_correct,
        "total_partial":  total_partial,
        "by_grade":       by_grade,
        "accuracy":       (total_correct + 0.5 * total_partial) / total_reviewed if total_reviewed else None,
    }


# ── 页面 ─────────────────────────────────────────────────────

st.set_page_config(page_title="Shall 正确性核查", layout="wide")

if "idx" not in st.session_state:
    st.session_state.idx = 0

sample   = load_sample()
eu_map   = load_eu_map()
results  = load_results()
stats    = compute_stats(sample, results)
n_total  = len(sample)

# ── 侧边栏 ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 核查进度")
    st.progress(stats["reviewed"] / stats["total"])
    st.markdown(f"**{stats['reviewed']} / {stats['total']}** 已完成")

    if stats["accuracy"] is not None:
        st.markdown("---")
        st.markdown("#### 实时准确率")
        st.metric("综合准确率", f"{stats['accuracy']*100:.1f}%",
                  help="正确计1分，部分正确计0.5分")
        st.caption("按 Grade 分布：")
        for g, v in stats["by_grade"].items():
            total_g = sum(v.values())
            correct_g = v.get("correct", 0) + 0.5 * v.get("partial", 0)
            st.caption(f"  Grade {g}: {correct_g:.0f}/{total_g} 正确")

    st.markdown("---")
    st.markdown("### 跳转")
    jump = st.number_input("第N条", min_value=1, max_value=n_total,
                           value=st.session_state.idx + 1, step=1)
    if st.button("跳转"):
        st.session_state.idx = jump - 1
        st.rerun()

    unreviewed = [i for i, it in enumerate(sample) if it["uid"] not in results]
    if unreviewed:
        if st.button(f"⏭ 下一条未核查（第{unreviewed[0]+1}条）"):
            st.session_state.idx = unreviewed[0]
            st.rerun()

# ── 主区域 ───────────────────────────────────────────────────

idx  = min(st.session_state.idx, n_total - 1)
item = sample[idx]
uid  = item["uid"]
g    = item["grade"]
existing = results.get(uid, {})

grade_icon = {"A": "🔴", "B": "🟡", "C": "🟢"}.get(g, "⚪")
done_mark  = "✅" if uid in results else "○"

st.markdown(f"## {done_mark} [{idx+1}/{n_total}]　{grade_icon} Grade {g}　·　{item['or_id']}")

# 源需求
st.markdown("**源需求（OR）：**")
st.info(item["or_text"])

col_shall, col_evidence = st.columns([1, 1])

with col_shall:
    st.markdown("**生成的 Shall：**")
    st.markdown(
        f'<div style="background:#f0f4ff;padding:12px;border-radius:6px;'
        f'font-size:14px;line-height:1.8;white-space:pre-wrap;">'
        f'{item["shall"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Measurable Criterion：**")
    st.code(item["criterion"] or "(无)")

    if item.get("condition"):
        st.caption(f"适用条件：{item['condition']}")
    if item.get("verification"):
        st.caption(f"验证方法：{item['verification']}")

with col_evidence:
    st.markdown("**引用证据：**")
    cits = item["citations"]
    if not cits:
        st.warning("无引用证据")
    for c in cits:
        kb_id  = c.get("kb_id", "")
        tier   = c.get("tier", "?")
        source = c.get("source", "")[:60]
        clause = c.get("has_clause", "")
        eu_text = eu_map.get(kb_id, "（原文未找到）")[:300]

        tier_color = {"L1": "#ff4b4b", "L2": "#ffa500", "L3": "#21c354"}.get(tier, "#888")
        st.markdown(
            f'<span style="background:{tier_color};color:white;padding:2px 6px;'
            f'border-radius:3px;font-size:12px;">{tier}</span> '
            f'<code style="font-size:11px;">{kb_id}</code> {source}',
            unsafe_allow_html=True,
        )
        if clause:
            st.caption(f"条款摘录：{clause}")
        with st.expander("查看完整EU原文"):
            st.text(eu_text)

# ── 标注区 ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("#### 核查标注")
st.caption("判断标准：该shall的核心内容（要求 + 适用条件 + 数值标准）是否有充分的证据支撑、在工程上是否合理？")

verdict_options = ["correct", "partial", "wrong"]
verdict_labels  = {"correct": "✅ 正确", "partial": "⚠️ 部分正确", "wrong": "❌ 错误/幻觉"}

bc1, bc2, bc3, bc4, bc5 = st.columns([1, 1.2, 1, 1, 3])

with bc1:
    if st.button("✅ 正确 →下一条", type="primary", key="btn_correct"):
        results[uid] = {"verdict": "correct", "note": "", "grade": g}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc2:
    if st.button("⚠️ 部分正确 →", key="btn_partial"):
        results[uid] = {"verdict": "partial", "note": "", "grade": g}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc3:
    if st.button("❌ 错误", key="btn_wrong"):
        results[uid] = {"verdict": "wrong", "note": "", "grade": g}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc4:
    if st.button("跳过 →", key="btn_skip"):
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

# 备注
note_key = f"note_{uid}"
note = st.text_input("备注（可选，记录错误原因等）",
                     value=existing.get("note", ""), key=note_key)
if note and note != existing.get("note", ""):
    if uid in results:
        results[uid]["note"] = note
        save_results(results)

# 上/下翻页
st.markdown("---")
nc1, nc2, _ = st.columns([1, 1, 5])
with nc1:
    if st.button("← 上一条", disabled=(idx == 0)):
        st.session_state.idx = idx - 1
        st.rerun()
with nc2:
    if st.button("下一条 →", disabled=(idx == n_total - 1)):
        st.session_state.idx = idx + 1
        st.rerun()

# ── 完成汇总 ─────────────────────────────────────────────────

if stats["reviewed"] == stats["total"]:
    st.markdown("---")
    st.success("🎉 全部30条核查完成！")
    st.markdown("## 最终准确率")
    c1, c2, c3 = st.columns(3)
    c1.metric("综合准确率", f"{stats['accuracy']*100:.1f}%" if stats['accuracy'] else "N/A")
    c2.metric("完全正确数", stats["total_correct"])
    c3.metric("部分正确数", stats["total_partial"])

    st.markdown("#### 按 Grade 分布")
    for g_key in ["A", "B", "C"]:
        v = stats["by_grade"].get(g_key, {})
        if v:
            total_g = sum(v.values())
            st.write(f"**Grade {g_key}**: 正确 {v.get('correct',0)} / 部分 {v.get('partial',0)} / 错误 {v.get('wrong',0)} (共{total_g}条)")
