# -*- coding: utf-8 -*-
"""
盲法数值正确性人工评审界面（Streamlit）—— 第二位专家用

目的：对 50 条"含数值的 shall"（RAG 25 + no-RAG 25，已打乱、隐去臂别与引用）
     纯凭工程判断每条数值是否正确，得到独立于单专家 Grade X spot-check 的
     "RAG vs no-RAG 人工盲评数值正确率"证据（补 M2 缺口）。

⚠️ 盲法：界面**不显示**该条属于哪个臂、有无引用、检索到什么证据。
   评审者只看 shall + 数值判据，凭工程经验判断。臂别还原在评完之后由
   scripts 用隐藏映射 blind_correctness_key.json 完成。

运行（任选其一）：
  双击  blind_review.bat
  或    streamlit run scripts/blind_correctness_review_ui.py --server.port 8508

每次点击即时存盘到：
  data/search_results/exp_v4/blind_correctness_results.json   （主存档，按 uid）
  data/search_results/exp_v4/blind_correctness_review.csv     （同步回填 verdict 列）
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXP = ROOT / "data" / "search_results" / "exp_v4"
CSV_FILE = EXP / "blind_correctness_review.csv"
RESULT_FILE = EXP / "blind_correctness_results.json"
VERDICT_COL = "verdict (correct/approx/wrong/unknown)"

VERDICTS = {
    "correct": "✅ 正确",
    "approx":  "⚠️ 近似正确",
    "wrong":   "❌ 明显错误",
    "unknown": "❓ 无法判断",
}

# ── 数据层 ────────────────────────────────────────────────────


@st.cache_data(show_spinner=False)
def load_sample() -> list[dict]:
    with CSV_FILE.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for i, r in enumerate(rows):
        r["_seq"] = i
    return rows


def load_results() -> dict[str, dict]:
    if RESULT_FILE.exists():
        return json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    return {}


def save_results(results: dict[str, dict], sample: list[dict]):
    RESULT_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    # 同步把 verdict 回填进 CSV（保持原列、原顺序）
    fieldnames = [k for k in sample[0].keys() if not k.startswith("_")]
    with CSV_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in sample:
            out = {k: r.get(k, "") for k in fieldnames}
            res = results.get(r["uid"])
            if res:
                out[VERDICT_COL] = res.get("verdict", "")
                out["note"] = res.get("note", "")
            w.writerow(out)


def counts_of(sample, results) -> dict[str, int]:
    c = {k: 0 for k in VERDICTS}
    for item in sample:
        res = results.get(item["uid"])
        if res and res.get("verdict") in c:
            c[res["verdict"]] += 1
    return c


# ── 页面 ─────────────────────────────────────────────────────

st.set_page_config(page_title="盲法数值正确性评审", layout="wide")

if "idx" not in st.session_state:
    st.session_state.idx = 0

sample = load_sample()
results = load_results()
n_total = len(sample)
counts = counts_of(sample, results)
reviewed = sum(counts.values())

# ── 侧边栏 ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 评审进度")
    st.progress(reviewed / n_total if n_total else 0)
    st.markdown(f"**{reviewed} / {n_total}** 已完成")

    st.markdown("---")
    st.markdown("#### 实时统计（已评）")
    st.caption(
        f"✅ 正确: {counts['correct']}　"
        f"⚠️ 近似: {counts['approx']}　"
        f"❌ 错误: {counts['wrong']}　"
        f"❓ 不确定: {counts['unknown']}"
    )
    st.caption("（不显示 RAG / no-RAG 分组——盲法。臂别还原在评完后进行。）")

    st.markdown("---")
    st.markdown(
        "**判断标准**（只看 shall + 数值判据，凭工程经验判断该**数值**对不对）\n\n"
        "- ✅ **正确**：与规范 / 行业惯例吻合\n"
        "- ⚠️ **近似正确**：大致对，±20% 以内\n"
        "- ❌ **明显错误**：明显偏离惯例 / 像捏造\n"
        "- ❓ **无法判断**：超出你的把握\n\n"
        "⚠️ **不要**去猜这条有没有引用 / 是哪个系统生成的——"
        "顺序已打乱、来源已隐去，凭工程判断即可。"
    )

    st.markdown("---")
    jump = st.number_input("跳到第 N 条", min_value=1, max_value=n_total,
                           value=st.session_state.idx + 1, step=1)
    if st.button("跳转"):
        st.session_state.idx = jump - 1
        st.rerun()

    unreviewed = [i for i, it in enumerate(sample) if it["uid"] not in results]
    if unreviewed and st.button(f"⏭ 下一条未评（第 {unreviewed[0]+1} 条）"):
        st.session_state.idx = unreviewed[0]
        st.rerun()

# ── 主区域 ───────────────────────────────────────────────────

idx = min(st.session_state.idx, n_total - 1)
item = sample[idx]
uid = item["uid"]
existing = results.get(uid, {})

done_mark = "✅" if uid in results else "○"
cur = existing.get("verdict")
cur_label = VERDICTS.get(cur, "未评") if cur else "未评"
st.markdown(f"## {done_mark} [{idx+1}/{n_total}]　当前判定：{cur_label}")
st.caption("盲样：以下 shall 可能来自任一系统，已隐去来源与引用。请判断其**数值**是否工程上正确。")

st.markdown("**Shall 语句：**")
st.markdown(
    f'<div style="background:#f5f7ff;padding:14px;border-radius:6px;'
    f'border-left:4px solid #3366cc;font-size:16px;line-height:1.9;'
    f'white-space:pre-wrap;">{item["shall_statement"]}</div>',
    unsafe_allow_html=True,
)

st.markdown("**可测量判据（含待判断的数值）：**")
st.code(item["measurable_criterion"] or "(无)", language=None)

# ── 标注区 ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("#### 评审标注（点击后自动存盘并跳下一条）")

cols = st.columns(len(VERDICTS) + 1)
for col, (key, label) in zip(cols, VERDICTS.items()):
    with col:
        if st.button(f"{label} →", key=f"btn_{key}",
                     type="primary" if key == "correct" else "secondary"):
            results[uid] = {"verdict": key, "note": existing.get("note", "")}
            save_results(results, sample)
            st.session_state.idx = min(idx + 1, n_total - 1)
            st.rerun()
with cols[-1]:
    if st.button("跳过 →", key="btn_skip"):
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

note = st.text_input("备注（可选：记录判断依据 / 参考数值）",
                     value=existing.get("note", ""), key=f"note_{uid}")
if note != existing.get("note", "") and uid in results:
    results[uid]["note"] = note
    save_results(results, sample)

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

# ── 完成提示 ─────────────────────────────────────────────────

if reviewed == n_total:
    st.markdown("---")
    st.success("🎉 全部 50 条评审完成！请把这件事告诉负责人，"
               "由其用隐藏映射还原 RAG / no-RAG 并计算两臂正确率。")
    st.caption(
        f"总体分布（未分臂）：✅{counts['correct']}　⚠️{counts['approx']}　"
        f"❌{counts['wrong']}　❓{counts['unknown']}"
    )
    st.caption(f"存档：{RESULT_FILE.name} + {CSV_FILE.name}（verdict 列已回填）")
