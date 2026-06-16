# -*- coding: utf-8 -*-
"""
Stage 2.5 值提取准确率审核界面（Streamlit）

运行：
  streamlit run scripts/stage25_review_ui.py --server.port 8503
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_FILE   = ROOT / "data/search_results/exp_v4/stage25_sample_data.json"
RESULT_FILE = ROOT / "data/search_results/exp_v4/stage25_review_results.json"
EU_JSONL    = ROOT / "data/processed/evidence_units_v2.jsonl"

TIER_QUOTA = {"L1": 8, "L2": 18, "L3": 24}
SEED = 42
_NUM_ROUGH = re.compile(r"\d+\.?\d*")

# ── 数据层 ──────────────────────────────────────────────────

def load_eus() -> dict[str, list[dict]]:
    by_tier: dict[str, list[dict]] = {"L1": [], "L2": [], "L3": []}
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            eu = json.loads(line)
            t = eu.get("kb_tier", "")
            if t in by_tier:
                by_tier[t].append(eu)
    return by_tier


def stratified_sample(by_tier: dict, quota: dict, seed: int) -> list[dict]:
    rng = random.Random(seed)
    sample = []
    for tier, n in quota.items():
        pool = by_tier.get(tier, [])
        numeric  = [eu for eu in pool if _NUM_ROUGH.search(eu.get("text", ""))]
        non_num  = [eu for eu in pool if not _NUM_ROUGH.search(eu.get("text", ""))]
        n_num    = min(round(n * 0.6), len(numeric))
        n_non    = n - n_num
        picked   = rng.sample(numeric, n_num) + rng.sample(non_num, min(n_non, len(non_num)))
        if len(picked) < n:
            remaining = [eu for eu in numeric if eu not in picked]
            picked += rng.sample(remaining, min(n - len(picked), len(remaining)))
        rng.shuffle(picked)
        sample.extend(picked[:n])
    return sample


@st.cache_data(show_spinner=False)
def load_sample_data() -> list[dict]:
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_sample_data(data: list[dict]):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_results() -> dict[str, dict]:
    if RESULT_FILE.exists():
        with open(RESULT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results: dict[str, dict]):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def compute_stats(sample_data: list[dict], review_results: dict) -> dict:
    total_extracted = total_correct = total_missed = reviewed = 0
    for item in sample_data:
        eu_id = item["eu_id"]
        if eu_id not in review_results:
            continue
        r = review_results[eu_id]
        total_extracted += len(item["extracted_values"])
        total_correct   += r.get("correct_count", 0)
        total_missed    += r.get("missed_count", 0)
        reviewed += 1
    return {
        "reviewed": reviewed,
        "total": len(sample_data),
        "total_extracted": total_extracted,
        "total_correct": total_correct,
        "total_missed": total_missed,
        "precision": total_correct / total_extracted if total_extracted > 0 else None,
        "recall": total_correct / (total_correct + total_missed) if (total_correct + total_missed) > 0 else None,
    }


def highlight_numbers(text: str) -> str:
    _PAT = re.compile(
        r"(\d+\.?\d*\s*(?:°C|℃|MPa|bar\b|kPa|L/min|m³/h|mm\b|%|秒|分钟|s\b|min\b|rpm\b|kW\b|m/s|N\b))"
    )
    return _PAT.sub(r"**\1**", text)


# ── 页面配置 ─────────────────────────────────────────────────

st.set_page_config(page_title="Stage 2.5 审核", layout="wide")

# session_state 初始化
if "idx" not in st.session_state:
    st.session_state.idx = 0

# ── Step 0: 提取（首次）─────────────────────────────────────

sample_data = load_sample_data()

if not sample_data:
    st.title("Stage 2.5 值提取准确率审核")
    st.info("尚未生成抽样数据，点击下方按钮对50条EU运行DeepSeek提取（约2-3分钟）。")
    if st.button("▶ 开始提取（调用API）", type="primary"):
        with st.spinner("加载EU并抽样..."):
            by_tier = load_eus()
            sample  = stratified_sample(by_tier, TIER_QUOTA, SEED)

        from cooling_rag_mg.config import DeepSeekConfig
        from cooling_rag_mg.kb_value_extractor import extract_values_from_evidence
        cfg    = DeepSeekConfig()
        client = cfg.make_client()
        model  = cfg.model

        results  = []
        progress = st.progress(0, text="提取中...")
        for i, eu in enumerate(sample):
            values = extract_values_from_evidence(eu.get("text", ""), client, model)
            results.append({
                "eu_id": eu.get("id", "?"),
                "tier": eu.get("kb_tier", "?"),
                "source_document": eu.get("source_document", "?"),
                "text": eu.get("text", ""),
                "extracted_values": values,
            })
            progress.progress((i + 1) / len(sample), text=f"提取中 {i+1}/{len(sample)}...")

        save_sample_data(results)
        load_sample_data.clear()
        st.success(f"完成！共 {len(results)} 条。")
        st.rerun()
    st.stop()

# ── Step 1: 审核界面 ─────────────────────────────────────────

review_results = load_results()
stats = compute_stats(sample_data, review_results)
n_total = len(sample_data)

# 边界保护
if st.session_state.idx >= n_total:
    st.session_state.idx = n_total - 1

idx  = st.session_state.idx
item = sample_data[idx]
eu_id  = item["eu_id"]
tier   = item["tier"]
source = item["source_document"]
text   = item["text"]
values = item["extracted_values"]
existing = review_results.get(eu_id, {})

# ── 侧边栏 ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 审核进度")
    st.progress(stats["reviewed"] / stats["total"])
    st.markdown(f"**{stats['reviewed']} / {stats['total']}** 已完成")

    if stats["precision"] is not None:
        st.markdown("---")
        st.markdown("#### 实时统计（已审条目）")
        st.metric("Precision（精确率）", f"{stats['precision']*100:.1f}%")
        if stats["recall"] is not None:
            st.metric("Recall（召回率）", f"{stats['recall']*100:.1f}%")
        st.caption(
            f"提取总数: {stats['total_extracted']}  \n"
            f"正确: {stats['total_correct']}  漏检: {stats['total_missed']}"
        )

    st.markdown("---")
    st.markdown("### 快速跳转")

    def go_to(i: int):
        st.session_state.idx = max(0, min(i, n_total - 1))

    jump = st.number_input("跳到第N条（1-50）", min_value=1, max_value=n_total,
                           value=idx + 1, step=1, key="jump_input")
    if st.button("跳转", key="btn_jump"):
        go_to(jump - 1)
        st.rerun()

    # 跳到第一条未审核
    unreviewed = [i for i, it in enumerate(sample_data) if it["eu_id"] not in review_results]
    if unreviewed:
        if st.button(f"⏭ 第一条未审核（第{unreviewed[0]+1}条）"):
            go_to(unreviewed[0])
            st.rerun()

# ── 主区域 ───────────────────────────────────────────────────

tier_icon = {"L1": "🔴", "L2": "🟡", "L3": "🟢"}.get(tier, "⚪")
done_mark = "✅" if eu_id in review_results else "○"
st.markdown(f"## {done_mark}  [{idx+1} / {n_total}]　{tier_icon} **{tier}**　·　{source}")
st.caption(f"EU ID: `{eu_id}`")

col_text, col_values = st.columns([3, 2])

with col_text:
    st.markdown("**原文**")
    st.markdown(
        f'<div style="background:#f8f9fa;padding:14px;border-radius:6px;'
        f'font-size:14px;line-height:1.8;white-space:pre-wrap;">'
        f'{highlight_numbers(text)}</div>',
        unsafe_allow_html=True,
    )

with col_values:
    st.markdown("**提取结果**")
    if values:
        for v in values:
            op  = v.get("operator", "")
            vt  = v.get("value_text", "")
            u   = v.get("unit", "")
            lbl = f"{op} {vt}  ({u})" if op else f"{vt}  ({u})"
            st.code(lbl.strip())
        st.markdown(f"共提取 **{len(values)}** 个")
    else:
        st.info("未提取到任何数值")

# ── 标注区 ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("#### 标注")

rc1, rc2, rc3 = st.columns(3)
with rc1:
    correct = st.number_input(
        "✅ 正确数（提取的值中存在于原文的）",
        min_value=0, max_value=max(len(values), 1),
        value=existing.get("correct_count", 0),
        key=f"correct_{eu_id}",
    )
with rc2:
    missed = st.number_input(
        "🔍 漏检数（原文有但未提取到的）",
        min_value=0, max_value=20,
        value=existing.get("missed_count", 0),
        key=f"missed_{eu_id}",
    )
with rc3:
    notes = st.text_input(
        "备注（可选）",
        value=existing.get("notes", ""),
        key=f"notes_{eu_id}",
    )

bc1, bc2, bc3, bc4 = st.columns([1, 1.2, 1, 3])

with bc1:
    if st.button("💾 保存", type="primary", key="btn_save"):
        review_results[eu_id] = {
            "correct_count": int(correct),
            "missed_count": int(missed),
            "notes": notes,
            "n_extracted": len(values),
        }
        save_results(review_results)
        st.toast("已保存 ✓")

with bc2:
    if st.button("⚡ 全部正确 →下一条", key="btn_allcorrect"):
        review_results[eu_id] = {
            "correct_count": len(values),
            "missed_count": 0,
            "notes": "",
            "n_extracted": len(values),
        }
        save_results(review_results)
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

with bc3:
    if st.button("跳过 →下一条", key="btn_skip"):
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

# ── 上下翻页 ─────────────────────────────────────────────────

st.markdown("---")
nc1, nc2, _ = st.columns([1, 1, 5])
with nc1:
    if st.button("← 上一条", key="btn_prev", disabled=(idx == 0)):
        st.session_state.idx = idx - 1
        st.rerun()
with nc2:
    if st.button("下一条 →", key="btn_next", disabled=(idx == n_total - 1)):
        st.session_state.idx = idx + 1
        st.rerun()

# ── 完成统计 ─────────────────────────────────────────────────

if stats["reviewed"] == stats["total"]:
    st.markdown("---")
    st.success("🎉 全部50条审核完成！")
    st.markdown("## 最终统计")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precision", f"{stats['precision']*100:.1f}%" if stats['precision'] is not None else "N/A",
              help="正确提取数 / 总提取数")
    c2.metric("Recall",    f"{stats['recall']*100:.1f}%"    if stats['recall']    is not None else "N/A",
              help="正确提取数 / (正确提取数 + 漏检数)")
    c3.metric("总提取数", stats["total_extracted"])
    c4.metric("漏检总数", stats["total_missed"])
