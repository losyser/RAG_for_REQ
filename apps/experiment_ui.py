# -*- coding: utf-8 -*-
"""
Experiment comparison and metrics analysis UI pages.
Imported by requirement_collection_ui.py.
"""
from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]

GROUP_LABELS = {
    "G1": "G1 Direct LLM",
    "G2": "G2 Flat RAG",
    "G3": "G3 Multi-RAG",
    "G4": "G4 Proposed",
    "A1": "A1 w/o QualityGate",
    "A2": "A2 w/o ProfileScore",
}

GROUP_DESCRIPTIONS = {
    "G1": "无检索，仅凭领域知识直接生成",
    "G2": "单粒度 evidence_units 检索，无质量门",
    "G3": "多粒度检索（本文方法），无质量门",
    "G4": "多粒度检索 + 质量门 + SysML 输出（完整方案）",
    "A1": "消融：G4 去掉质量门",
    "A2": "消融：G4 去掉 Profile Scoring",
}

GROUP_WITH_QG = {"G4", "A2"}

STATUS_ICON = {
    "verified_by_direct_evidence": "🟢 直接证据支撑",
    "need_confirmation": "🟡 待确认",
    "supported_by_indirect_evidence": "🟠 间接证据支撑",
    "evidence_gap": "🔴 证据缺口",
    "no_evidence_baseline": "⚫ 无证据基线",
}

METRIC_META = [
    ("m1", "M1 无证据率", "↓", "evidence_ids 为空条数 / 总条数"),
    ("m2", "M2 质量门通过率", "↑", "overall_passed / 总条数（仅 G4/A2）"),
    ("m3", "M3 过度推理率", "↓", "过度推理检查失败条数 / 总条数"),
    ("m4", "M4 可验证率", "↑", "可验证检查通过条数 / 总条数"),
    ("m5", "M5 MBSE 完整率", "↑", "SysML 必填字段全满足条数 / 总条数"),
]

ENGINEERING_STATUS_LABELS = {
    "verified_by_direct_evidence": "直接证据支撑",
    "supported_by_indirect_evidence": "间接证据支撑",
    "evidence_gap": "证据缺口",
    "need_confirmation": "需确认",
    "no_evidence_baseline": "无证据基线",
}

ENGINEERING_STATUS_CLASS = {
    "verified_by_direct_evidence": "badge-direct",
    "supported_by_indirect_evidence": "badge-indirect",
    "evidence_gap": "badge-na",
    "need_confirmation": "badge-confirm",
    "no_evidence_baseline": "badge-background",
}


# ─────────────────────────────────────────────
# Cached data loaders
# ─────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def _load_eu_cache(processed_dir: str) -> dict[str, dict]:
    path = Path(processed_dir) / "evidence_units.jsonl"
    result: dict[str, dict] = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    result[obj.get("id", "")] = obj
                except Exception:
                    pass
    return result


@st.cache_resource(show_spinner=False)
def _load_test_req_cache(processed_dir: str) -> dict[str, dict]:
    path = Path(processed_dir) / "test_requirements.jsonl"
    result: dict[str, dict] = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    result[obj["requirement_id"]] = obj
                except Exception:
                    pass
    return result


# ─────────────────────────────────────────────
# Reused HTML helpers (duplicated from main UI to keep module self-contained)
# ─────────────────────────────────────────────

def _badge(status: str) -> str:
    cls = ENGINEERING_STATUS_CLASS.get(status, "badge-confirm")
    label = ENGINEERING_STATUS_LABELS.get(status, status or "未标注")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def _pill(label: str, value: str, tone: str = "neutral") -> str:
    tone_class = f" {tone}" if tone != "neutral" else ""
    return f'<span class="status-pill{tone_class}">{escape(label)}<strong>{escape(value)}</strong></span>'


def _fmt_pct(v: float) -> str:
    if math.isnan(v):
        return "N/A"
    return f"{v * 100:.1f}%"


# ─────────────────────────────────────────────
# Group metric summary cards
# ─────────────────────────────────────────────

def _group_metric_cards(group: str, result_sets: list[dict]) -> None:
    from cooling_rag_mg.experiment_runner import compute_metrics
    metrics_rows = compute_metrics({group: result_sets})
    if not metrics_rows:
        return
    row = metrics_rows[0]
    cols = st.columns(6)
    cards = [
        ("需求集数", str(row["n_sets"]), "neutral"),
        ("需求条数", str(row["n_reqs"]), "neutral"),
        ("M1 无证据率", _fmt_pct(row["m1"]), "danger" if row["m1"] > 0.2 else "success"),
        ("M3 过度推理率", _fmt_pct(row["m3"]), "danger" if row["m3"] > 0.1 else "success"),
        ("M4 可验证率", _fmt_pct(row["m4"]), "success" if row["m4"] > 0.85 else "warning"),
        ("M5 MBSE 完整率", _fmt_pct(row["m5"]), "success" if row["m5"] > 0.7 else "warning"),
    ]
    if group in GROUP_WITH_QG and not math.isnan(row["m2"]):
        cards[2] = ("M2 质量门通过率", _fmt_pct(row["m2"]), "success" if row["m2"] > 0.6 else "warning")

    for col, (label, value, tone) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="summary-card">'
                f'<div class="summary-label">{escape(label)}</div>'
                f'<div class="summary-value">{escape(value)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
# Quality gate summary
# ─────────────────────────────────────────────

def _render_quality_gate_summary(result_sets: list[dict]) -> None:
    rows = []
    for rs in result_sets:
        for er in rs.get("engineering_requirements") or []:
            qgr = er.get("quality_gate_report")
            if not qgr:
                continue
            check_summary = {c["dimension"]: ("✅" if c["passed"] else "❌") for c in qgr.get("checks", [])}
            rows.append({
                "ID": er.get("id", ""),
                "主题": er.get("topic", ""),
                "overall": "✅ PASS" if qgr.get("overall_passed") else "❌ FAIL",
                "分数": f"{qgr.get('score', 0):.2f}",
                "证据充分性": check_summary.get("evidence_sufficiency", "—"),
                "可验证性": check_summary.get("verifiability", "—"),
                "过度推理": check_summary.get("over_inference", "—"),
                "歧义性": check_summary.get("ambiguity", "—"),
                "MBSE完整性": check_summary.get("mbse_completeness", "—"),
            })
    if not rows:
        st.info("未找到质量门报告数据。")
        return

    total = len(rows)
    passed = sum(1 for r in rows if "PASS" in r["overall"])
    st.markdown(
        f'<div class="status-strip" style="margin-bottom:10px">'
        f'{_pill("总计", str(total))}'
        f'{_pill("通过", str(passed), "success")}'
        f'{_pill("未通过", str(total - passed), "danger")}'
        f'{_pill("通过率", f"{passed/total:.1%}" if total else "—", "success" if total and passed/total > 0.6 else "warning")}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# SysML diagram (adapted from main UI)
# ─────────────────────────────────────────────

def _build_req_tree(items: list[dict], parent_id: str) -> list[dict]:
    result = []
    for item in items:
        if item.get("parent_id") == parent_id:
            node = dict(item)
            node["_children"] = _build_req_tree(items, node.get("id", ""))
            result.append(node)
    return result


def _sysml_block_html(item: dict, depth: int = 0) -> str:
    status = item.get("support_status", "")
    status_class = {
        "verified_by_direct_evidence": "sysml-direct",
        "supported_by_indirect_evidence": "sysml-indirect",
        "evidence_gap": "sysml-gap",
        "need_confirmation": "sysml-confirm",
    }.get(status, "sysml-unknown")
    badge_class = ENGINEERING_STATUS_CLASS.get(status, "badge-na")
    status_label = ENGINEERING_STATUS_LABELS.get(status, status)
    req_id = escape(str(item.get("id", "") or ""))
    topic = escape(str(item.get("topic", "") or ""))
    shall_raw = str(item.get("shall_statement", "") or "")
    shall_display = escape(shall_raw[:130] + ("…" if len(shall_raw) > 130 else ""))
    verif = escape(str(item.get("verification_method", "") or ""))
    ev_list = [str(x) for x in (item.get("evidence_ids") or [])]
    evidence = escape(", ".join(ev_list) if ev_list else "—")
    depth_class = "sysml-l1" if depth == 0 else "sysml-l2"
    children_html = ""
    children = item.get("_children", [])
    if children:
        inner = "".join(_sysml_block_html(c, depth + 1) for c in children)
        children_html = f'<div class="sysml-children">{inner}</div>'
    return (
        f'<div class="sysml-block {status_class} {depth_class}">'
        f'<div class="sysml-stereotype">«requirement»</div>'
        f'<div class="sysml-block-name">{topic}</div>'
        f'<div class="sysml-block-body">'
        f'<div class="sysml-attr"><span class="sysml-attr-label">id : </span>{req_id}</div>'
        f'<div class="sysml-attr"><span class="sysml-attr-label">text : </span>'
        f'<span class="sysml-text-val">{shall_display}</span></div>'
        f'<div class="sysml-meta">'
        f'<span class="badge {badge_class}">{escape(status_label)}</span>'
        f'<span class="sysml-verif-chip">{verif}</span>'
        f'<div class="sysml-evidence-line">证据：{evidence}</div>'
        f'</div></div>{children_html}</div>'
    )


def _render_exp_sysml_diagram(result_sets: list[dict]) -> None:
    if not result_sets:
        st.info("没有可展示的工程化需求。")
        return
    for rs in result_sets:
        set_id = rs.get("requirement_set_id", "")
        source_id = rs.get("source_requirement_id", "")
        stakeholder = rs.get("stakeholder", "")
        summary = rs.get("professional_summary", "")
        items = rs.get("engineering_requirements") or []
        roots = _build_req_tree(items, set_id)
        reached: set[str] = set()
        def _collect(nodes: list) -> None:
            for n in nodes:
                reached.add(n.get("id", ""))
                _collect(n.get("_children", []))
        _collect(roots)
        for item in items:
            if item.get("id", "") not in reached:
                node = dict(item)
                node["_children"] = []
                roots.append(node)
        blocks_html = "".join(_sysml_block_html(r, 0) for r in roots)
        st.markdown(
            f'<div class="sysml-diagram-section">'
            f'<div class="sysml-set-header">'
            f'<span class="sysml-set-id">{escape(set_id)}</span>'
            f'<span class="sysml-set-src">来源 {escape(source_id)} ｜ {escape(stakeholder)}</span>'
            f'</div>'
            f'<div class="sysml-set-summary">{escape(summary)}</div>'
            f'<div class="sysml-blocks-wrap">{blocks_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_exp_sysml_table(result_sets: list[dict]) -> None:
    rows = []
    for rs in result_sets:
        for item in rs.get("engineering_requirements") or []:
            rows.append({
                "需求集": rs.get("requirement_set_id", ""),
                "来源": rs.get("source_requirement_id", ""),
                "ID": item.get("id", ""),
                "层级": item.get("level", ""),
                "类型": item.get("requirement_type", ""),
                "主题": item.get("topic", ""),
                "shall 语句": item.get("shall_statement", ""),
                "验证方式": item.get("verification_method", ""),
                "支撑状态": ENGINEERING_STATUS_LABELS.get(item.get("support_status", ""), item.get("support_status", "")),
                "证据数": len(item.get("evidence_ids") or []),
            })
    if not rows:
        st.info("没有需求数据。")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def _render_exp_gap_table(result_sets: list[dict]) -> None:
    rows = []
    for rs in result_sets:
        for gap in rs.get("evidence_gaps") or []:
            if not isinstance(gap, dict):
                gap = {"description": str(gap)}
            rows.append({
                "需求集": rs.get("requirement_set_id", ""),
                "关联需求": gap.get("related_requirement_id", ""),
                "缺口类型": gap.get("gap_type", ""),
                "描述": gap.get("description", ""),
                "建议补充": gap.get("suggested_document_update", ""),
            })
    if not rows:
        st.success("无单独列出的证据缺口。")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ─────────────────────────────────────────────
# Per-group tab
# ─────────────────────────────────────────────

def _render_group_tab(group: str, result_sets: list[dict]) -> None:
    st.markdown(
        f'<div class="section-caption" style="margin-bottom:10px">'
        f'{escape(GROUP_DESCRIPTIONS.get(group, ""))}</div>',
        unsafe_allow_html=True,
    )
    _group_metric_cards(group, result_sets)

    sub_labels = ["需求图", "需求表", "证据缺口"]
    if group in GROUP_WITH_QG:
        sub_labels.append("质量门报告")

    sub_tabs = st.tabs(sub_labels)
    with sub_tabs[0]:
        _render_exp_sysml_diagram(result_sets)
    with sub_tabs[1]:
        _render_exp_sysml_table(result_sets)
    with sub_tabs[2]:
        _render_exp_gap_table(result_sets)
    if group in GROUP_WITH_QG and len(sub_tabs) > 3:
        with sub_tabs[3]:
            _render_quality_gate_summary(result_sets)


# ─────────────────────────────────────────────
# Experiment workspace
# ─────────────────────────────────────────────

def render_experiment_workspace(cfg: Any) -> None:
    from cooling_rag_mg.experiment_runner import (
        run_g1, run_g2, run_pipeline_group,
    )

    st.markdown(
        '<div class="page-hero">'
        '<div class="page-kicker">EXPERIMENT COMPARISON</div>'
        '<div class="page-title">实验对比平台</div>'
        '<div class="page-subtitle">'
        '选择实验组并运行；结果以 SysML 需求图、需求表、证据缺口和质量门报告分组展示。'
        '使用检索工作台中当前启用的需求作为输入。'
        '</div></div>',
        unsafe_allow_html=True,
    )

    exp_results: dict[str, list] = st.session_state.setdefault("exp_results", {})

    col_ctrl, col_main = st.columns([1, 3])

    # ── 左列：控制面板 ──
    with col_ctrl:
        st.markdown('<div class="section-title" style="margin-bottom:8px">选择实验组</div>', unsafe_allow_html=True)
        selected_groups = []
        for g in ALL_GROUPS:
            default = g in {"G1", "G2", "G3", "G4"}
            checked = st.checkbox(GROUP_LABELS[g], value=default, key=f"exp_chk_{g}")
            if checked:
                selected_groups.append(g)

        st.markdown("---")
        top_k = st.number_input("Top-K", min_value=1, max_value=10, value=4, step=1, key="exp_top_k")
        st.markdown('<div class="section-caption">每个子需求最多保留的证据条数</div>', unsafe_allow_html=True)
        st.markdown("")

        run_disabled = bool(st.session_state.get("exp_running")) or not selected_groups
        run_clicked = st.button(
            "▶ 运行选中实验组",
            type="primary",
            use_container_width=True,
            disabled=run_disabled,
        )
        clear_clicked = st.button("清空实验结果", use_container_width=True, disabled=bool(st.session_state.get("exp_running")))


    # ── 运行逻辑 ──
    if clear_clicked:
        st.session_state.exp_results = {}
        st.session_state.pop("exp_metrics", None)
        st.session_state.pop("exp_m6_template", None)
        st.session_state.pop("m6_judgements", None)
        st.rerun()

    if run_clicked and selected_groups:
        from cooling_rag_mg.experiment_runner import compute_metrics
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from apps.requirement_collection_ui import normalize_df  # type: ignore

        reqs = normalize_df(st.session_state.requirements_df)
        if not reqs:
            st.warning("检索工作台中没有启用的需求，请先添加需求。")
        else:
            st.session_state.exp_running = True
            with col_main:
                progress_bar = st.progress(0, text="准备运行实验")
                status_box = st.empty()

            total_groups = len(selected_groups)
            for gi, group in enumerate(selected_groups):
                st.session_state.exp_current_group = group
                progress_bar.progress(gi / total_groups, text=f"运行 {group}（{gi+1}/{total_groups}）")
                status_box.info(f"正在运行 {GROUP_LABELS[group]}：{GROUP_DESCRIPTIONS[group]}")

                try:
                    def _prog(done: int, total: int, msg: str) -> None:
                        frac = gi / total_groups + (done / max(total, 1)) / total_groups
                        progress_bar.progress(min(frac, 0.99), text=f"{GROUP_LABELS[group]} — {msg}")

                    if group == "G1":
                        result = run_g1(reqs, cfg, on_progress=_prog)
                    elif group == "G2":
                        result = run_g2(reqs, cfg, top_k=int(top_k), on_progress=_prog)
                    elif group == "G3":
                        result = run_pipeline_group(
                            "G3", reqs, cfg,
                            with_quality_gate=False, with_profile_scoring=True,
                            top_k=int(top_k), on_progress=_prog,
                        )
                    elif group == "G4":
                        result = run_pipeline_group(
                            "G4", reqs, cfg,
                            with_quality_gate=True, with_profile_scoring=True,
                            top_k=int(top_k), on_progress=_prog,
                        )
                    elif group == "A1":
                        result = run_pipeline_group(
                            "A1", reqs, cfg,
                            with_quality_gate=False, with_profile_scoring=True,
                            top_k=int(top_k), on_progress=_prog,
                        )
                    else:  # A2
                        result = run_pipeline_group(
                            "A2", reqs, cfg,
                            with_quality_gate=True, with_profile_scoring=False,
                            top_k=int(top_k), on_progress=_prog,
                        )
                    exp_results[group] = result
                except Exception as exc:
                    status_box.error(f"{group} 运行失败：{exc}")

            # Compute metrics
            st.session_state.exp_metrics = compute_metrics(exp_results)
            st.session_state.exp_running = False
            st.session_state.pop("exp_current_group", None)
            progress_bar.progress(100, text="全部实验组运行完成")
            status_box.success(f"完成 {len(exp_results)} 个实验组，可在「指标分析」页查看汇总指标。")
            st.rerun()

    # ── 右列：结果展示 ──
    with col_main:
        if not exp_results:
            st.markdown(
                '<div class="run-panel">'
                '<div class="run-title">尚未运行实验</div>'
                '<div class="run-detail">在左侧选择实验组，点击「运行选中实验组」后结果将在此处展示。'
                '输入需求来自检索工作台的需求表（当前启用行）。</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            return

        available = [g for g in ALL_GROUPS if g in exp_results]
        tab_labels = [GROUP_LABELS[g] for g in available]
        tabs = st.tabs(tab_labels)
        for tab, group in zip(tabs, available):
            with tab:
                _render_group_tab(group, exp_results[group])


# ─────────────────────────────────────────────
# Metrics charts
# ─────────────────────────────────────────────

def _render_metrics_table(metrics: list[dict]) -> None:
    if not metrics:
        return

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

    def _highlight(frame: pd.DataFrame) -> pd.DataFrame:
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

    # LaTeX download
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


def _render_bar_charts(metrics: list[dict]) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("需要安装 plotly：pip install plotly")
        return

    groups = [GROUP_LABELS.get(r["group"], r["group"]) for r in metrics]
    accent = "#2563eb"
    palette = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"]

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
        # Invert ↓ metrics so higher = better on radar
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
            # positive delta means G4 > A1
            # For ↑ metrics: G4 > A1 is good; for ↓ metrics: G4 < A1 is good → delta < 0 is good
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
        st.dataframe(pd.DataFrame(diff_rows), hide_index=True, use_container_width=True)

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
        st.dataframe(pd.DataFrame(diff_rows), hide_index=True, use_container_width=True)

    if not g4:
        st.info("消融分析需要 G4 结果。请先运行 G4 实验组。")


# ─────────────────────────────────────────────
# M6 human review
# ─────────────────────────────────────────────

def _render_m6_card(
    item: dict,
    eu_cache: dict,
    test_req_cache: dict,
    prev_src_id: list,  # mutable 1-element list to track current source group
) -> bool:
    """Render one M6 review card. Returns True if this item has evidence_ids."""
    req_id = item["requirement_id"]
    eids = item.get("evidence_ids") or []
    status = item.get("support_status", "")
    shall = item.get("shall_statement", "")
    set_id = item.get("source_set_id", "")

    # source_set_id is "ER-R001"; strip "ER-" to get original requirement id "R001"
    src_id = item.get("source_set_id", "").replace("ER-", "", 1)
    if not src_id:
        import re
        src_id = re.sub(r"-\d+$", "", req_id.replace("ER-", "", 1))

    if src_id != prev_src_id[0]:
        prev_src_id[0] = src_id
        orig = test_req_cache.get(src_id, {})
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
        choice = st.radio(
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
    from ui.state import normalize_df as _normalize_df
    test_req_cache: dict = dict(_load_test_req_cache(processed_dir))
    for row in _normalize_df(st.session_state.get("requirements_df")):
        rid = row.get("requirement_id", "")
        if rid and rid not in test_req_cache:
            test_req_cache[rid] = row

    if not st.session_state.get("exp_m6_template"):
        st.session_state.exp_m6_template = generate_m6_template(g4_results, n=20)

    template: list[dict] = st.session_state.exp_m6_template or []
    if not template:
        from cooling_rag_mg.experiment_runner import flatten_requirements
        n_sets = len(g4_results)
        n_reqs = len(flatten_requirements(g4_results))
        st.warning(
            f"G4 结果中未找到工程化需求（{n_sets} 个需求集，展开后 {n_reqs} 条需求）。"
        )
        if n_reqs == 0:
            st.info("engineering_requirements 全部为空。最可能的原因：LLM 调用成功但证据全部被判定为 background/not_applicable，导致 fallback 路径下无支撑证据，跳过了需求生成。请检查 evidence_judge 输出，或临时将 USE_EVIDENCE_JUDGE=0 后重新运行 G4。")
        return
    items_with_eids = [it for it in template if it.get("evidence_ids")]

    # Compute current score from widget state
    judged_correct = 0
    judged_total = 0
    for it in items_with_eids:
        rid = it["requirement_id"]
        val = st.session_state.get(f"m6_radio_{rid}")
        if val is not None:
            judged_total += 1
            if "✅" in val:
                judged_correct += 1

    # Top status bar
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
        _render_m6_card(item, eu_cache, test_req_cache, prev_src)

    st.markdown("---")
    # Save button
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

        # Find latest experiment batch dir
        batches = sorted(cfg.paths.search_results_dir.glob("batch_*/experiment"))
        if batches:
            save_path = batches[-1] / "M6_sampling_template.json"
            save_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success(f"已保存 → {save_path}")
        # Also offer download
        st.download_button(
            "下载 M6_sampling_template.json",
            data=json.dumps(out, ensure_ascii=False, indent=2),
            file_name="M6_sampling_template.json",
            mime="application/json",
        )


# ─────────────────────────────────────────────
# Metrics workspace
# ─────────────────────────────────────────────

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
