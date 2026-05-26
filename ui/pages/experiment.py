# -*- coding: utf-8 -*-
"""Experiment comparison workspace."""
from __future__ import annotations

import math
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from ui.state import (
    ENGINEERING_STATUS_LABELS,
    ENGINEERING_STATUS_CLASS,
    normalize_df,
)

ALL_GROUPS = ["G1", "G2", "G3", "G4", "A1", "A2"]

GROUP_LABELS = {
    "G1": "G1 Direct LLM",
    "G2": "G2 Flat RAG",
    "G3": "G3 Multi-RAG",
    "G4": "G4 Proposed",
    "A1": "A1 无质量门",
    "A2": "A2 无 Profile",
}

GROUP_DESCRIPTIONS = {
    "G1": "无检索，直接 LLM 生成（无证据注入）",
    "G2": "单粒度 RAG，仅使用 evidence_units，无质量门",
    "G3": "多粒度 RAG，全量 pipeline，无质量门",
    "G4": "多粒度 RAG + 质量门 + SysML XML（本文方案）",
    "A1": "消融：G4 去掉质量门",
    "A2": "消融：G4 去掉 Profile Scoring（纯 RRF）",
}

GROUP_WITH_QG: set[str] = {"G4", "A2"}

METRIC_META = [
    ("m1", "M1 无证据率", "↓", "有多少需求的 evidence_ids 为空"),
    ("m2", "M2 QG 通过率", "↑", "质量门 overall_passed 比例（仅 G4/A2）"),
    ("m3", "M3 过度推理率", "↓", "QG over_inference 维度失败比例"),
    ("m4", "M4 可验证率", "↑", "QG verifiability 维度通过比例"),
    ("m5", "M5 MBSE 完整率", "↑", "QG mbse_completeness 维度通过比例"),
]

STATUS_ICON = {
    "verified_by_direct_evidence": "✅ 直接证据",
    "supported_by_indirect_evidence": "🔶 间接证据",
    "evidence_gap": "❌ 证据缺口",
    "need_confirmation": "❓ 需确认",
}


def _fmt_pct(v: float) -> str:
    if math.isnan(v):
        return "N/A"
    return f"{v * 100:.1f}%"


def _badge(status: str) -> str:
    cls = ENGINEERING_STATUS_CLASS.get(status, "badge-confirm")
    label = ENGINEERING_STATUS_LABELS.get(status, status or "未标注")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def _pill(label: str, value: str, tone: str = "neutral") -> str:
    tone_class = f" {tone}" if tone != "neutral" else ""
    return f'<span class="status-pill{tone_class}">{escape(label)}<strong>{escape(value)}</strong></span>'


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


def render_experiment_workspace(cfg: Any) -> None:
    from cooling_rag_mg.experiment_runner import run_g1, run_g2, run_pipeline_group

    st.markdown(
        '<div style="padding:10px 0 6px">'
        '<span style="font-size:0.7rem;font-weight:700;letter-spacing:.1em;'
        'text-transform:uppercase;color:#2563eb">EXPERIMENT COMPARISON</span>'
        '<h2 style="margin:2px 0 4px;font-size:1.35rem;font-weight:760">实验对比平台</h2>'
        '<p style="margin:0;font-size:0.85rem;color:#64748b">'
        '选择实验组并运行；结果以需求图、需求表、证据缺口和质量门报告分组展示。'
        '</p></div>',
        unsafe_allow_html=True,
    )

    exp_results: dict[str, list] = st.session_state.setdefault("exp_results", {})
    is_running = bool(st.session_state.get("exp_running"))

    col_ctrl, col_main = st.columns([1, 3], gap="medium")

    with col_ctrl:
        st.markdown("**选择实验组**")
        selected_groups = []
        for g in ALL_GROUPS:
            default = g in {"G1", "G2", "G3", "G4"}
            if st.checkbox(GROUP_LABELS[g], value=default, key=f"exp_chk_{g}"):
                selected_groups.append(g)

        top_k = st.number_input("Top-K（每子需求最多证据数）", min_value=1, max_value=10, value=4, step=1, key="exp_top_k")

        run_clicked = st.button(
            "▶ 运行选中实验组",
            type="primary",
            use_container_width=True,
            disabled=is_running or not selected_groups,
        )
        clear_clicked = st.button("清空结果", use_container_width=True, disabled=is_running)

        if st.session_state.get("exp_last_save_dir"):
            st.caption(f"上次保存：`{st.session_state.exp_last_save_dir}`")

    if clear_clicked:
        st.session_state.exp_results = {}
        st.session_state.pop("exp_metrics", None)
        st.session_state.pop("exp_m6_template", None)
        st.session_state.pop("m6_judgements", None)
        st.rerun()

    if run_clicked and selected_groups:
        from cooling_rag_mg.experiment_runner import compute_metrics

        _staged = st.session_state.get("_staged_requirements")
        reqs = normalize_df(_staged if _staged is not None else st.session_state.requirements_df)
        if not reqs:
            st.warning("检索工作台中没有启用的需求，请先添加需求。")
            return

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
                def _prog(done: int, total: int, msg: str, _gi: int = gi, _g: str = group) -> None:
                    frac = _gi / total_groups + (done / max(total, 1)) / total_groups
                    progress_bar.progress(min(frac, 0.99), text=f"{GROUP_LABELS[_g]}（{_gi+1}/{total_groups}） — {msg}")

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
                    from cooling_rag_mg.experiment_runner import make_a1_from_g4
                    if "G4" not in exp_results:
                        # G4 not yet run — run it now so A1 shares identical retrieval
                        progress_bar.progress(gi / total_groups, text="A1 需要 G4 结果，先运行 G4…")
                        g4_result = run_pipeline_group(
                            "G4", reqs, cfg,
                            with_quality_gate=True, with_profile_scoring=True,
                            top_k=int(top_k), on_progress=_prog,
                        )
                        exp_results["G4"] = g4_result
                    result = make_a1_from_g4(exp_results["G4"])
                else:  # A2
                    result = run_pipeline_group(
                        "A2", reqs, cfg,
                        with_quality_gate=True, with_profile_scoring=False,
                        top_k=int(top_k), on_progress=_prog,
                    )
                exp_results[group] = result
            except Exception as exc:
                status_box.error(f"{group} 运行失败：{exc}")

        st.session_state.exp_running = False
        st.session_state.pop("exp_current_group", None)
        metrics = compute_metrics(exp_results)
        st.session_state.exp_metrics = metrics
        progress_bar.empty()
        status_box.empty()

        try:
            from cooling_rag_mg.experiment_runner import save_experiment_results
            exp_dir = save_experiment_results(
                exp_results,
                metrics,
                results_root=cfg.paths.search_results_dir,
                top_k=int(top_k),
                n_requirements=len(reqs),
            )
            st.session_state.exp_last_save_dir = str(exp_dir)
            st.toast(f"完成 {len(exp_results)} 个实验组，结果已保存至 {exp_dir.name}/experiment/", icon="✅")
        except Exception as exc:
            st.toast(f"完成 {len(exp_results)} 个实验组（保存失败：{exc}）", icon="⚠️")

    with col_main:
        if not exp_results:
            st.info("在左侧选择实验组，点击「运行选中实验组」后结果将在此处展示。输入需求来自检索工作台的需求表（当前启用行）。")
            return

        available = [g for g in ALL_GROUPS if g in exp_results]
        tabs = st.tabs([GROUP_LABELS[g] for g in available])
        for tab, group in zip(tabs, available):
            with tab:
                _render_group_tab(group, exp_results[group])
