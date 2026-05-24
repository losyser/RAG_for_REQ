# -*- coding: utf-8 -*-
"""Metrics analysis page (M1-M5 charts + M6 human review)."""
from __future__ import annotations

import json
import math
from html import escape
from typing import Any

import streamlit as st

from ui.pages.experiment import (
    ALL_GROUPS,
    GROUP_LABELS,
    GROUP_WITH_QG,
    METRIC_META,
    STATUS_ICON,
    _fmt_pct,
)
from ui.state import ENGINEERING_STATUS_LABELS


# ── Cache loaders ──────────────────────────────────────────────


@st.cache_resource
def _load_eu_cache(processed_dir: str) -> dict:
    import json
    from pathlib import Path
    result = {}
    path = Path(processed_dir) / "evidence_units.jsonl"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    result[obj["id"]] = obj
                except Exception:
                    pass
    return result


@st.cache_resource
def _load_test_req_cache(processed_dir: str) -> dict:
    import json
    from pathlib import Path
    result = {}
    path = Path(processed_dir) / "test_requirements.jsonl"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    result[obj["requirement_id"]] = obj
                except Exception:
                    pass
    return result


# ── Metrics table & LaTeX ──────────────────────────────────────


def _render_metrics_table(metrics: list[dict]) -> None:
    if not metrics:
        return
    import pandas as pd

    best: dict[str, float] = {}
    for key in ["m1", "m2", "m3", "m4", "m5"]:
        vals = [r[key] for r in metrics if not math.isnan(r[key])]
        if vals:
            best[key] = min(vals) if key in ("m1", "m3") else max(vals)

    col_key_map = {
        "M1 无证据率↓": "m1",
        "M2 QG通过率↑": "m2",
        "M3 过度推理率↓": "m3",
        "M4 可验证率↑": "m4",
        "M5 MBSE完整率↑": "m5",
    }

    rows = []
    for row in metrics:
        def _cell(key: str) -> str:
            v = row[key]
            return "N/A" if math.isnan(v) else f"{v * 100:.1f}%"

        rows.append({
            "组别": GROUP_LABELS.get(row["group"], row["group"]),
            "需求集": row["n_sets"],
            "需求数": row["n_reqs"],
            "M1 无证据率↓": _cell("m1"),
            "M2 QG通过率↑": _cell("m2"),
            "M3 过度推理率↓": _cell("m3"),
            "M4 可验证率↑": _cell("m4"),
            "M5 MBSE完整率↑": _cell("m5"),
        })

    df = pd.DataFrame(rows)

    def _highlight(frame: "pd.DataFrame") -> "pd.DataFrame":
        styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
        for col, key in col_key_map.items():
            if key not in best:
                continue
            bv = best[key]
            for i, mrow in enumerate(metrics):
                v = mrow[key]
                if not math.isnan(v) and abs(v - bv) < 1e-9:
                    styles.at[i, col] = "background-color:#dcfce7;font-weight:bold;color:#15803d"
        return styles

    st.dataframe(df.style.apply(_highlight, axis=None), hide_index=True, use_container_width=True)

    latex = _build_latex_table(metrics)
    st.download_button(
        "下载 LaTeX 表格",
        data=latex,
        file_name="table_metrics.tex",
        mime="text/plain",
        use_container_width=False,
    )


def _build_latex_table(metrics: list[dict]) -> str:
    best: dict[str, float] = {}
    for key in ["m1", "m2", "m3", "m4", "m5"]:
        vals = [r[key] for r in metrics if not math.isnan(r[key])]
        if vals:
            best[key] = min(vals) if key in ("m1", "m3") else max(vals)

    def _fmt(v: float, key: str) -> str:
        if math.isnan(v):
            return r"\multicolumn{1}{c}{---}"
        pct = f"{v * 100:.1f}\\%"
        return f"\\textbf{{{pct}}}" if key in best and abs(v - best[key]) < 1e-9 else pct

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Comparison of M1--M5 metrics across experiment groups. Best values per metric are \textbf{bold}. $\downarrow$: lower is better; $\uparrow$: higher is better.}",
        r"\label{tab:metrics}",
        r"\begin{tabular}{l r r r r r r r}",
        r"\toprule",
        r"Group & $N_{\text{sets}}$ & $N_{\text{reqs}}$ & M1$\downarrow$ & M2$\uparrow$ & M3$\downarrow$ & M4$\uparrow$ & M5$\uparrow$ \\",
        r"\midrule",
    ]
    ablation_started = False
    for row in metrics:
        g = row["group"]
        if g in ("A1", "A2") and not ablation_started:
            lines.append(r"\midrule")
            ablation_started = True
        label = GROUP_LABELS.get(g, g)
        prefix = r"\textit" if g in ("A1", "A2") else r"\textbf"
        parts = [
            f"{prefix}{{{g}}} {label.split(' ', 1)[1] if ' ' in label else ''}",
            str(row["n_sets"]),
            str(row["n_reqs"]),
            _fmt(row["m1"], "m1"),
            _fmt(row["m2"], "m2"),
            _fmt(row["m3"], "m3"),
            _fmt(row["m4"], "m4"),
            _fmt(row["m5"], "m5"),
        ]
        lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


# ── Charts ─────────────────────────────────────────────────────


def _render_bar_charts(metrics: list[dict]) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("需要安装 plotly：pip install plotly")
        return

    groups = [GROUP_LABELS.get(r["group"], r["group"]) for r in metrics]
    accent = "#2563eb"

    for key, label, better, _ in METRIC_META:
        vals = [r[key] for r in metrics]
        colors = []
        valid = [v for v in vals if not math.isnan(v)]
        best_val = (min(valid) if better == "↓" else max(valid)) if valid else None
        for v in vals:
            if math.isnan(v):
                colors.append("#e2e8f0")
            elif best_val is not None and abs(v - best_val) < 1e-9:
                colors.append("#15803d")
            else:
                colors.append(accent)

        text_vals = [_fmt_pct(v) for v in vals]
        fig = go.Figure(go.Bar(
            x=groups,
            y=[v if not math.isnan(v) else 0 for v in vals],
            text=text_vals,
            textposition="outside",
            marker_color=colors,
        ))
        fig.update_layout(
            title=f"{label}（{better} 越好）",
            yaxis_tickformat=".0%",
            yaxis_range=[0, 1.15],
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=320,
            margin=dict(t=45, b=30, l=30, r=10),
            font=dict(family="Segoe UI, Microsoft YaHei, Arial", size=12),
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)


def _render_radar_chart(metrics: list[dict]) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("需要安装 plotly：pip install plotly")
        return

    axes = ["M1 无证据率(反)", "M2 QG通过率", "M3 过度推理(反)", "M4 可验证率", "M5 MBSE完整率"]
    colors = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"]
    fig = go.Figure()
    for i, row in enumerate(metrics):
        m1_inv = 1 - row["m1"] if not math.isnan(row["m1"]) else 0
        m3_inv = 1 - row["m3"] if not math.isnan(row["m3"]) else 0
        m2 = row["m2"] if not math.isnan(row["m2"]) else 0
        m4 = row["m4"] if not math.isnan(row["m4"]) else 0
        m5 = row["m5"] if not math.isnan(row["m5"]) else 0
        vals = [m1_inv, m2, m3_inv, m4, m5]
        vals_closed = vals + [vals[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=axes + [axes[0]],
            fill="toself",
            name=GROUP_LABELS.get(row["group"], row["group"]),
            line_color=colors[i % len(colors)],
            opacity=0.6,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        height=420,
        margin=dict(t=30, b=30),
        font=dict(family="Segoe UI, Microsoft YaHei, Arial", size=11),
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("↓ 指标（M1/M3）已取反：雷达图上越靠外越好。M2 对无质量门组取 0。")


def _render_ablation_analysis(metrics: list[dict]) -> None:
    rows_by_group = {r["group"]: r for r in metrics}
    g4 = rows_by_group.get("G4")
    a1 = rows_by_group.get("A1")
    a2 = rows_by_group.get("A2")

    st.markdown("### 消融分析")

    if g4 and a1:
        st.markdown("#### G4 vs A1（有 / 无质量门）")
        diff_rows = []
        for key, label, better, _ in METRIC_META:
            v4, va = g4[key], a1[key]
            if math.isnan(v4) and math.isnan(va):
                continue
            delta = (v4 - va) if not (math.isnan(v4) or math.isnan(va)) else float("nan")
            if better == "↓":
                is_good = not math.isnan(delta) and delta < 0
            else:
                is_good = not math.isnan(delta) and delta > 0
            diff_rows.append({
                "指标": label,
                "方向": better,
                "G4": _fmt_pct(v4),
                "A1": _fmt_pct(va),
                "差值(G4-A1)": f"{delta*100:+.1f}%" if not math.isnan(delta) else "N/A",
                "结论": "✅ QG有贡献" if is_good else ("➡ 差异不显著" if abs(delta) < 0.02 else "⚠ 待分析"),
            })
        st.dataframe(__import__("pandas").DataFrame(diff_rows), hide_index=True, use_container_width=True)

    if g4 and a2:
        st.markdown("#### G4 vs A2（有 / 无 Profile Scoring）")
        diff_rows = []
        for key, label, better, _ in METRIC_META:
            v4, va = g4[key], a2[key]
            if math.isnan(v4) and math.isnan(va):
                continue
            delta = (v4 - va) if not (math.isnan(v4) or math.isnan(va)) else float("nan")
            if better == "↓":
                is_good = not math.isnan(delta) and delta < 0
            else:
                is_good = not math.isnan(delta) and delta > 0
            diff_rows.append({
                "指标": label,
                "方向": better,
                "G4": _fmt_pct(v4),
                "A2": _fmt_pct(va),
                "差值(G4-A2)": f"{delta*100:+.1f}%" if not math.isnan(delta) else "N/A",
                "需求数差": f"{g4['n_reqs']} vs {a2['n_reqs']}（差 {g4['n_reqs']-a2['n_reqs']}）" if key == "m1" else "",
                "结论": "✅ Profile有贡献" if is_good else ("➡ 差异不显著" if abs(delta) < 0.02 else "⚠ 待分析"),
            })
        st.dataframe(__import__("pandas").DataFrame(diff_rows), hide_index=True, use_container_width=True)

    if not g4:
        st.info("消融分析需要 G4 结果。请先运行 G4 实验组。")


# ── M6 human review ────────────────────────────────────────────


def _render_m6_card(
    item: dict,
    eu_cache: dict,
    req_cache: dict,
    prev_src_id: list,
) -> bool:
    req_id = item["requirement_id"]
    eids = item.get("evidence_ids") or []
    status = item.get("support_status", "")
    shall = item.get("shall_statement", "")

    # source_set_id is "ER-R001"; strip "ER-" to get the original requirement id "R001"
    src_id = item.get("source_set_id", "").replace("ER-", "", 1)
    if not src_id:
        # fallback: derive from engineering req id "ER-R001-01" → "R001"
        import re
        src_id = re.sub(r"-\d+$", "", req_id.replace("ER-", "", 1))

    if src_id != prev_src_id[0]:
        prev_src_id[0] = src_id
        orig = req_cache.get(src_id, {})
        st.markdown(
            f'<div style="background:#f8fbff;border:1px solid #dbe3ea;border-radius:10px;'
            f'padding:10px 14px;margin:14px 0 6px">'
            f'<div style="font-size:0.75rem;color:#2563eb;font-weight:760;letter-spacing:.06em;'
            f'text-transform:uppercase;margin-bottom:4px">原始需求 {escape(src_id)}</div>'
            f'<div style="font-weight:760">{escape(orig.get("stakeholder",""))}</div>'
            f'<div style="color:#64748b;font-size:0.88rem;margin-top:3px">'
            f'{escape(orig.get("requirement_text","（未找到原文）"))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if not eids:
        st.markdown(
            f'<div style="border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;'
            f'margin:4px 0;background:#f9fafb;color:#94a3b8;font-size:0.85rem">'
            f'⬜ [{item["index"]:02d}] {escape(req_id)} — 无证据链接，自动跳过</div>',
            unsafe_allow_html=True,
        )
        return False

    status_icon = STATUS_ICON.get(status, status)
    st.markdown(
        f'<div style="border:1px solid #dbe3ea;border-left:3px solid #93c5fd;border-radius:10px;'
        f'padding:12px 15px;margin:6px 0;background:#fff">'
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;'
        f'border-bottom:1px solid #f1f5f9;padding-bottom:8px;margin-bottom:8px">'
        f'<div style="font-weight:760">[{item["index"]:02d}] {escape(req_id)}</div>'
        f'<div style="font-size:0.78rem;color:#64748b">{escape(status_icon)}</div>'
        f'</div>'
        f'<div style="font-size:0.82rem;color:#64748b;margin-bottom:3px">📌 Shall 语句</div>'
        f'<div style="color:#1f2937;line-height:1.6;margin-bottom:10px">{escape(shall)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"🔗 查看链接证据（{len(eids)} 条）", expanded=True):
        for eid in eids:
            unit = eu_cache.get(eid, {})
            text = unit.get("text", "未找到证据原文").replace("\n", " ").strip()
            if len(text) > 350:
                text = text[:350] + "…"
            st.markdown(
                f'<div style="border:1px solid #e2e8f0;border-radius:8px;padding:9px 12px;'
                f'margin:5px 0;background:#f9fbfd">'
                f'<div style="font-size:0.78rem;font-weight:760;color:#2563eb;margin-bottom:4px">'
                f'{escape(eid)}</div>'
                f'<div style="font-size:0.82rem;color:#475569;line-height:1.6">{escape(text)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    col_radio, col_note = st.columns([1, 2])
    with col_radio:
        st.radio(
            "判断",
            options=["✅ 正确", "❌ 错误"],
            index=None,
            key=f"m6_radio_{req_id}",
            label_visibility="collapsed",
            horizontal=True,
        )
    with col_note:
        st.text_input(
            "备注",
            placeholder="简要说明理由（可选）",
            key=f"m6_note_{req_id}",
            label_visibility="collapsed",
        )
    st.markdown("")
    return True


def _render_m6_review(cfg: Any) -> None:
    from cooling_rag_mg.experiment_runner import generate_m6_template

    g4_results = (st.session_state.get("exp_results") or {}).get("G4")
    if not g4_results:
        st.info("请先在「实验对比」页面运行 G4 实验组，M6 审核条目将自动从 G4 结果生成。")
        return

    processed_dir = str(cfg.paths.processed_dir)
    eu_cache = _load_eu_cache(processed_dir)
    # Merge: test_requirements.jsonl (OWN-01 format) + retrieval workspace reqs (R001 format)
    from ui.state import normalize_df
    req_cache: dict = dict(_load_test_req_cache(processed_dir))
    for row in normalize_df(st.session_state.get("requirements_df")):
        rid = row.get("requirement_id", "")
        if rid and rid not in req_cache:
            req_cache[rid] = row

    if not st.session_state.get("exp_m6_template"):
        st.session_state.exp_m6_template = generate_m6_template(g4_results, n=20)

    template: list[dict] = st.session_state.exp_m6_template or []
    if not template:
        from cooling_rag_mg.experiment_runner import flatten_requirements
        n_sets = len(g4_results)
        n_reqs = len(flatten_requirements(g4_results))
        st.warning(f"G4 结果中未找到工程化需求（{n_sets} 个需求集，展开后 {n_reqs} 条需求）。")
        if n_reqs == 0:
            st.info(
                "engineering_requirements 全部为空。最可能原因：LLM 调用成功但"
                "所有证据被 evidence_judge 判定为 background/not_applicable，"
                "导致 fallback 路径下无支撑证据，跳过了需求条目生成。\n\n"
                "**验证方法**：在检索工作台对同一需求做一次检索，查看证据卡片里 "
                "「LLM 判断」字段是否全是 background。\n\n"
                "**快速绕过**：在 `.env` 加 `USE_EVIDENCE_JUDGE=0` 后重启并重新运行 G4。"
            )
        return
    items_with_eids = [it for it in template if it.get("evidence_ids")]

    judged_correct = 0
    judged_total = 0
    for it in items_with_eids:
        rid = it["requirement_id"]
        val = st.session_state.get(f"m6_radio_{rid}")
        if val is not None:
            judged_total += 1
            if "✅" in val:
                judged_correct += 1

    m6_score = judged_correct / judged_total if judged_total else None
    prog_val = judged_total / max(len(items_with_eids), 1)

    st.progress(prog_val)
    cols = st.columns(4)
    cols[0].metric("已审核", f"{judged_total} / {len(items_with_eids)}")
    cols[1].metric("判断正确", str(judged_correct))
    cols[2].metric("M6 分数", f"{m6_score:.1%}" if m6_score is not None else "—")
    cols[3].metric("跳过（无链接）", str(len(template) - len(items_with_eids)))

    st.markdown("---")
    st.markdown(
        '<div class="section-caption" style="margin-bottom:12px">'
        '对每条需求，阅读 shall 语句和下方链接证据，判断证据是否合理支撑该需求。'
        '证据 ID 为空的条目自动跳过（显示为灰色）。'
        '</div>',
        unsafe_allow_html=True,
    )

    prev_src = [""]
    for item in template:
        _render_m6_card(item, eu_cache, req_cache, prev_src)

    st.markdown("---")
    if st.button("💾 保存 M6 结果到文件", type="primary"):
        out = []
        for it in template:
            rid = it["requirement_id"]
            val = st.session_state.get(f"m6_radio_{rid}")
            note = st.session_state.get(f"m6_note_{rid}", "")
            entry = dict(it)
            entry["M6_human_judgement"] = {
                "traceability_correct": (True if val and "✅" in val else (False if val else None)),
                "notes": note or "",
            }
            out.append(entry)

        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if batches:
            save_path = batches[-1] / "M6_sampling_template.json"
            save_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success(f"已保存 → {save_path}")
        st.download_button(
            "下载 M6_sampling_template.json",
            data=json.dumps(out, ensure_ascii=False, indent=2),
            file_name="M6_sampling_template.json",
            mime="application/json",
        )


# ── Page render ────────────────────────────────────────────────


def render_metrics_workspace(cfg: Any) -> None:
    st.markdown(
        '<div class="page-hero">'
        '<div class="page-kicker">METRICS ANALYSIS</div>'
        '<div class="page-title">指标分析</div>'
        '<div class="page-subtitle">'
        'M1–M5 自动计算指标汇总、图表对比，以及 M6 人工溯源审核。'
        '需要先在「实验对比」页面完成实验运行。'
        '</div></div>',
        unsafe_allow_html=True,
    )

    metrics: list[dict] | None = st.session_state.get("exp_metrics")
    if not metrics:
        st.info("尚未计算指标。请先在「实验对比」页面运行实验。")
        if st.button("前往实验对比", type="primary"):
            st.session_state.active_workspace = "experiment_comparison"
            st.rerun()
        return

    _render_metrics_table(metrics)

    tab_bar, tab_radar, tab_ablation, tab_m6 = st.tabs(
        ["📊 柱状图对比", "🕸 雷达图", "🔬 消融分析", "👤 M6 人工审核"]
    )
    with tab_bar:
        _render_bar_charts(metrics)
    with tab_radar:
        _render_radar_chart(metrics)
    with tab_ablation:
        _render_ablation_analysis(metrics)
    with tab_m6:
        _render_m6_review(cfg)
