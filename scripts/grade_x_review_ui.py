# -*- coding: utf-8 -*-
"""
Grade X 幻觉值人工核查界面（Streamlit）

目的：从 no-RAG 174 条 Grade X shalls 中抽样 30 条，
     人工判断这些无溯源数值是否实际有误，为论文提供
     "Grade X 不只是无法溯源，而且确实存在大量错误值"的直接证据。

运行：
  streamlit run scripts/grade_x_review_ui.py --server.port 8506
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NORAG_FILE  = ROOT / "data/search_results/exp_v4/norag_v4_results.json"
RAG_FILE    = ROOT / "data/search_results/exp_v4/rag_v4_results.json"
OR_JSONL    = ROOT / "data/processed/original_requirements_v2.jsonl"
EU_JSONL    = ROOT / "data/processed/evidence_units_v2.jsonl"
SAMPLE_FILE = ROOT / "data/search_results/exp_v4/grade_x_review_sample.json"
RESULT_FILE = ROOT / "data/search_results/exp_v4/grade_x_review_results.json"

SAMPLE_SIZE = 30
SEED = 42

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
def load_rag_citations() -> dict[str, list[dict]]:
    """按 source_requirement_id 汇总 RAG 实验中引用的所有证据（去重）。"""
    with open(RAG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    cit_map: dict[str, list[dict]] = {}
    for rs in data["result_sets"]:
        src_id = rs["source_requirement_id"]
        seen: set[str] = set()
        cits: list[dict] = []
        for er in rs.get("engineering_requirements", []):
            for c in er.get("evidence_citations", []):
                kb_id = c.get("kb_id", "")
                if kb_id and kb_id not in seen:
                    seen.add(kb_id)
                    cits.append(c)
        cit_map[src_id] = cits
    return cit_map


@st.cache_data(show_spinner=False)
def load_sample() -> list[dict]:
    if SAMPLE_FILE.exists():
        with open(SAMPLE_FILE, encoding="utf-8") as f:
            return json.load(f)

    with open(NORAG_FILE, encoding="utf-8") as f:
        data = json.load(f)
    or_map = load_or_map()

    all_grade_x: list[dict] = []
    for rs in data["result_sets"]:
        src_id  = rs["source_requirement_id"]
        or_text = or_map.get(src_id, "")
        for er in rs.get("engineering_requirements", []):
            if er.get("_grade") != "X":
                continue
            all_grade_x.append({
                "uid":         f"{src_id}__{er.get('measurable_criterion','')[:40]}",
                "or_id":       src_id,
                "or_text":     or_text,
                "shall":       er.get("shall_statement", ""),
                "criterion":   er.get("measurable_criterion", ""),
                "condition":   er.get("applicable_condition", ""),
                "verification": er.get("verification_method", ""),
            })

    rng = random.Random(SEED)
    sample = rng.sample(all_grade_x, min(SAMPLE_SIZE, len(all_grade_x)))
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
    counts: dict[str, int] = {"correct": 0, "approx": 0, "wrong": 0, "unknown": 0, "trivial": 0}
    for item in sample:
        uid = item["uid"]
        if uid in results:
            v = results[uid].get("verdict", "unknown")
            counts[v] = counts.get(v, 0) + 1
    reviewed = sum(counts.values())
    # 真正工程参数条数（排除平凡断言）
    real_params = reviewed - counts.get("trivial", 0)
    wrong_rate = counts["wrong"] / real_params if real_params > 0 else None
    return {
        "reviewed":    reviewed,
        "total":       len(sample),
        "counts":      counts,
        "real_params": real_params,
        "wrong_rate":  wrong_rate,
    }


# ── 页面配置 ─────────────────────────────────────────────────

st.set_page_config(page_title="Grade X 幻觉核查", layout="wide")

if "idx" not in st.session_state:
    st.session_state.idx = 0

sample    = load_sample()
eu_map    = load_eu_map()
rag_cits  = load_rag_citations()
results   = load_results()
stats     = compute_stats(sample, results)
n_total   = len(sample)

# ── 侧边栏 ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 核查进度")
    st.progress(stats["reviewed"] / stats["total"])
    st.markdown(f"**{stats['reviewed']} / {stats['total']}** 已完成")

    if stats["wrong_rate"] is not None:
        st.markdown("---")
        st.markdown("#### 实时统计（已审）")
        c = stats["counts"]
        st.metric("❌ 明显错误率", f"{stats['wrong_rate']*100:.1f}%",
                  help="仅统计工程参数条目（排除平凡断言）")
        st.caption(
            f"✅ 正确: {c['correct']}  "
            f"⚠️ 近似: {c['approx']}  "
            f"❌ 错误: {c['wrong']}  "
            f"❓ 不确定: {c['unknown']}  "
            f"🔄 平凡断言: {c.get('trivial', 0)}"
        )

    st.markdown("---")
    st.markdown(
        "**判断标准**\n\n"
        "- ✅ **正确**：数值与行业规范/KB吻合\n"
        "- ⚠️ **近似正确**：数值在合理范围内但不精确（±20%以内）\n"
        "- ❌ **明显错误**：数值与行业惯例明显偏差，或明显捏造\n"
        "- ❓ **无法判断**：该领域超出个人知识范围\n"
        "- 🔄 **平凡断言**：数字本身无实质工程含义\n"
        "  （如\"100%通过\"、\">=1个\"这类计数型断言，\n"
        "  不属于温度/压力/流量等可查证的工程参数）"
    )

    st.markdown("---")
    jump = st.number_input("跳到第N条", min_value=1, max_value=n_total,
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
existing = results.get(uid, {})

done_mark = "✅" if uid in results else "○"
st.markdown(f"## {done_mark} [{idx+1}/{n_total}]　🔴 Grade X　·　{item['or_id']}")
st.caption("这是 **no-RAG** 生成的 shall，无任何引用证据。请判断其数值是否工程上合理。")

# 源需求
st.markdown("**源需求（原始输入）：**")
st.info(item["or_text"])

col_shall, col_ref = st.columns([1, 1])

with col_shall:
    st.markdown("**no-RAG 生成的 Shall（Grade X）：**")
    st.markdown(
        f'<div style="background:#fff0f0;padding:12px;border-radius:6px;'
        f'border-left:4px solid #ff4b4b;font-size:14px;line-height:1.8;'
        f'white-space:pre-wrap;">{item["shall"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**可测量准则（含无溯源数值）：**")
    st.code(item["criterion"] or "(无)", language=None)

    if item.get("condition"):
        st.caption(f"适用条件：{item['condition']}")
    if item.get("verification"):
        st.caption(f"验证方法：{item['verification']}")

with col_ref:
    st.markdown("**RAG 对同一源需求找到的 KB 证据（参考）：**")
    cits = rag_cits.get(item["or_id"], [])
    if not cits:
        st.warning("RAG 对该源需求未检索到任何证据")
    else:
        shown = 0
        for c in cits:
            kb_id  = c.get("kb_id", "")
            tier   = c.get("tier", "?")
            source = c.get("source", "")[:60]
            clause = c.get("has_clause", "")
            eu_text = eu_map.get(kb_id, "（原文未找到）")

            tier_color = {"L1": "#ff4b4b", "L2": "#ffa500", "L3": "#21c354"}.get(tier, "#888")
            st.markdown(
                f'<span style="background:{tier_color};color:white;padding:2px 6px;'
                f'border-radius:3px;font-size:12px;">{tier}</span> '
                f'<code style="font-size:11px;">{kb_id}</code>　{source}',
                unsafe_allow_html=True,
            )
            if clause:
                st.caption(f"条款摘录：{clause}")
            with st.expander("查看EU原文"):
                st.text(eu_text[:400])
            shown += 1
            if shown >= 6:
                st.caption(f"（共 {len(cits)} 条证据，仅显示前6条）")
                break

# ── 标注区 ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("#### 核查标注")

bc1, bc2, bc3, bc4, bc5, bc6 = st.columns([1.2, 1.4, 1.3, 1.2, 1.6, 1.2])

with bc1:
    if st.button("✅ 正确 →", type="primary", key="btn_correct"):
        results[uid] = {"verdict": "correct", "note": existing.get("note", "")}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc2:
    if st.button("⚠️ 近似正确 →", key="btn_approx"):
        results[uid] = {"verdict": "approx", "note": existing.get("note", "")}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc3:
    if st.button("❌ 明显错误 →", key="btn_wrong"):
        results[uid] = {"verdict": "wrong", "note": existing.get("note", "")}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc4:
    if st.button("❓ 不确定 →", key="btn_unknown"):
        results[uid] = {"verdict": "unknown", "note": existing.get("note", "")}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc5:
    if st.button("🔄 平凡断言 →", key="btn_trivial",
                 help="数字无实质工程含义（如100%通过、≥1个等计数型断言）"):
        results[uid] = {"verdict": "trivial", "note": existing.get("note", "")}
        save_results(results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc6:
    if st.button("跳过 →", key="btn_skip"):
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

note = st.text_input(
    "备注（记录错误原因、参考依据等）",
    value=existing.get("note", ""),
    key=f"note_{uid}",
)
if note != existing.get("note", ""):
    if uid in results:
        results[uid]["note"] = note
        save_results(results)

# 翻页
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
    c = stats["counts"]
    reviewed = stats["reviewed"]
    real = stats["real_params"]
    st.markdown("## 最终统计")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🔢 工程参数条数", real, help="排除平凡断言后的真实工程参数数量")
    col2.metric("❌ 明显错误率",
                f"{c['wrong']/real*100:.1f}%" if real else "N/A",
                help="仅在工程参数条目中统计")
    col3.metric("⚠️ 近似正确率",  f"{c['approx']/real*100:.1f}%" if real else "N/A")
    col4.metric("✅ 正确率",       f"{c['correct']/real*100:.1f}%" if real else "N/A")
    col5.metric("🔄 平凡断言数",   c.get("trivial", 0))

    if real > 0:
        unreliable = c['wrong'] + c['approx']
        st.info(
            f"**工程参数中，{c['wrong']/real*100:.0f}% 明显错误，"
            f"{unreliable/real*100:.0f}% 不可靠（含近似）。**\n\n"
            f"共审核 {reviewed} 条 Grade X shalls（从174条随机抽样），"
            f"其中 {c.get('trivial',0)} 条为平凡数值断言（如100%通过等），"
            f"不计入工程参数错误率。"
        )
