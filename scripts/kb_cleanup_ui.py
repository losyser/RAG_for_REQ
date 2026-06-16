# -*- coding: utf-8 -*-
"""
KB 表格噪声 EU 清理界面（Streamlit）

运行：
  streamlit run scripts/kb_cleanup_ui.py --server.port 8504

功能：
  - 加载疑似表格噪声的 EU（优先显示被 v3 实验检索到的28条）
  - 点击"AI建议"让 DeepSeek 把混乱的表格文本整理为干净的工程描述
  - 人工确认/编辑后保存回 evidence_units_v2.jsonl
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EU_JSONL  = ROOT / "data/processed/evidence_units_v2.jsonl"
V3_RESULT = ROOT / "data/search_results/exp_v3/rag_v3_results.json"
DONE_FILE = ROOT / "data/search_results/exp_v4/kb_cleanup_done.json"

_TABLE_PAT = re.compile(r"(\s{3,}|\t){3,}")
_NUM_DENSE = re.compile(r"(\d[\d\s./]{0,5}){5,}")

_CLEAN_PROMPT = """\
你是船舶工程知识库整理专家。下面是一条证据单元的原始文本，来自船舶主机冷却水系统相关文档。
原文因 PDF 表格提取导致格式混乱，数字和列标题堆叠在一起，难以直接使用。

请将其整理为：
1. 以工程陈述句表达（中英文均可，保持原文语言为主）
2. 保留所有有意义的参数名称、数值、单位、适用条件
3. 去除页码、文档编号、编辑日期等非内容信息
4. 去除无语义的重复字符、空格序列
5. 如果原文含有多行参数，每行单独成句
6. 若原文确实没有有效的工程内容（纯格式垃圾），输出：[NO_CONTENT]

原始文本：
{text}

整理后输出（仅输出整理结果，不加解释）：
"""

# ── 数据加载 ─────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_all_eus() -> list[dict]:
    eus = []
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            eus.append(json.loads(line))
    return eus


@st.cache_data(show_spinner=False)
def get_used_ids() -> set[str]:
    with open(V3_RESULT, encoding="utf-8") as f:
        v3 = json.load(f)
    used = set()
    for rs in v3["result_sets"]:
        for er in rs.get("engineering_requirements", []):
            used.update(er.get("evidence_ids", []))
    return used


def get_noise_eus(all_eus: list[dict], used_ids: set[str]) -> list[dict]:
    """返回表格噪声EU列表：被检索到的排前面，未检索到的排后面。"""
    noise = [
        eu for eu in all_eus
        if _TABLE_PAT.search(eu.get("text", ""))
        or _NUM_DENSE.search(eu.get("text", "")[:200])
    ]
    used_noise   = [eu for eu in noise if eu["id"] in used_ids]
    unused_noise = [eu for eu in noise if eu["id"] not in used_ids]
    return used_noise + unused_noise


def load_done() -> dict[str, str]:
    """已完成清理的 {eu_id: cleaned_text}"""
    if DONE_FILE.exists():
        with open(DONE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_done(done: dict[str, str]):
    DONE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DONE_FILE, "w", encoding="utf-8") as f:
        json.dump(done, f, ensure_ascii=False, indent=2)


def write_back_to_jsonl(eu_id: str, new_text: str):
    """把 new_text 写回 evidence_units_v2.jsonl 中对应条目的 text 字段。"""
    lines = []
    with open(EU_JSONL, encoding="utf-8") as f:
        for line in f:
            eu = json.loads(line)
            if eu["id"] == eu_id:
                eu["text"] = new_text
                if "search_text" in eu:
                    eu["search_text"] = new_text  # 同步更新检索文本
            lines.append(json.dumps(eu, ensure_ascii=False))
    with open(EU_JSONL, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # 清除缓存使下次重新加载
    load_all_eus.clear()


def ai_clean(text: str) -> str:
    from cooling_rag_mg.config import DeepSeekConfig
    cfg = DeepSeekConfig()
    client = cfg.make_client()
    prompt = _CLEAN_PROMPT.format(text=text[:1500])
    resp = client.chat.completions.create(
        model=cfg.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,
    )
    return resp.choices[0].message.content.strip()


# ── 页面 ─────────────────────────────────────────────────────

st.set_page_config(page_title="KB 噪声清理", layout="wide")

if "idx" not in st.session_state:
    st.session_state.idx = 0
if "ai_suggestion" not in st.session_state:
    st.session_state.ai_suggestion = {}   # {eu_id: suggested_text}

all_eus  = load_all_eus()
used_ids = get_used_ids()
noise_eus = get_noise_eus(all_eus, used_ids)
done = load_done()
n_total = len(noise_eus)
n_priority = sum(1 for eu in noise_eus if eu["id"] in used_ids)

# ── 侧边栏 ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 进度")
    n_done = sum(1 for eu in noise_eus if eu["id"] in done)
    st.progress(n_done / n_total)
    st.markdown(f"**{n_done} / {n_total}** 已清理")
    st.caption(f"⚠️ 优先（被检索到）: {n_priority} 条")
    st.caption(f"低优先（未检索到）: {n_total - n_priority} 条")

    st.markdown("---")
    st.markdown("### 跳转")
    jump = st.number_input("第N条", min_value=1, max_value=n_total,
                           value=st.session_state.idx + 1, step=1)
    if st.button("跳转"):
        st.session_state.idx = jump - 1
        st.rerun()

    unfinished = [i for i, eu in enumerate(noise_eus) if eu["id"] not in done]
    if unfinished:
        if st.button(f"⏭ 下一条未完成（第{unfinished[0]+1}条）"):
            st.session_state.idx = unfinished[0]
            st.rerun()

    st.markdown("---")
    st.markdown("### 批量写回")
    st.caption(f"已清理 {len(done)} 条，点击下方写入 JSONL")
    if st.button("💾 全部写回 evidence_units_v2.jsonl", type="primary"):
        with st.spinner("写入中..."):
            for eid, new_text in done.items():
                write_back_to_jsonl(eid, new_text)
        st.success(f"已写回 {len(done)} 条！")
        st.rerun()

# ── 主区域 ───────────────────────────────────────────────────

idx = min(st.session_state.idx, n_total - 1)
eu  = noise_eus[idx]
eu_id  = eu["id"]
tier   = eu.get("kb_tier", "?")
source = eu.get("source_document", "?")
text   = eu.get("text", "")

is_priority = eu_id in used_ids
tier_icon   = {"L1": "🔴", "L2": "🟡", "L3": "🟢"}.get(tier, "⚪")
done_mark   = "✅" if eu_id in done else ("⚠️" if is_priority else "○")
priority_tag = "**[优先]**" if is_priority else ""

st.markdown(f"## {done_mark} [{idx+1}/{n_total}]　{tier_icon} {tier}　·　{source}　{priority_tag}")
st.caption(f"EU ID: `{eu_id}`")

col_orig, col_clean = st.columns(2)

with col_orig:
    st.markdown("**原始文本（只读）**")
    st.text_area("原文", value=text, height=320, disabled=True, key="orig_text",
                 label_visibility="collapsed")

with col_clean:
    st.markdown("**清理后文本**")

    # 若已有保存的清理结果，优先显示；否则显示AI建议或原文
    existing_clean = done.get(eu_id, "")
    ai_sug = st.session_state.ai_suggestion.get(eu_id, "")
    default_val = existing_clean or ai_sug or text

    cleaned = st.text_area("编辑区", value=default_val, height=320, key=f"edit_{eu_id}",
                            label_visibility="collapsed")

# ── 操作按钮 ─────────────────────────────────────────────────

bc1, bc2, bc3, bc4 = st.columns([1.2, 1, 1, 3])

with bc1:
    if st.button("🤖 AI建议清理", key="btn_ai"):
        with st.spinner("DeepSeek 整理中..."):
            try:
                sug = ai_clean(text)
                st.session_state.ai_suggestion[eu_id] = sug
                st.toast("AI建议已生成，请查看右侧编辑区")
                st.rerun()
            except Exception as e:
                st.error(f"API调用失败: {e}")

with bc2:
    if st.button("💾 保存", type="primary", key="btn_save"):
        done[eu_id] = cleaned
        save_done(done)
        st.toast("已保存（尚未写回JSONL，侧边栏统一写回）")

with bc3:
    if st.button("🗑️ 标记无内容", key="btn_nocontent",
                 help="原文无有效工程内容，标记后从JSONL中清除此EU的text"):
        done[eu_id] = "[NO_CONTENT]"
        save_done(done)
        st.toast("已标记为 NO_CONTENT")

with bc4:
    if st.button("跳过 →", key="btn_skip"):
        st.session_state.idx = min(idx + 1, n_total - 1)
        st.rerun()

st.markdown("---")
nc1, nc2 = st.columns([1, 1])
with nc1:
    if st.button("← 上一条", disabled=(idx == 0)):
        st.session_state.idx = idx - 1
        st.rerun()
with nc2:
    if st.button("下一条 →", disabled=(idx == n_total - 1)):
        st.session_state.idx = idx + 1
        st.rerun()
