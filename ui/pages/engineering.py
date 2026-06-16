# -*- coding: utf-8 -*-
"""Engineering requirements generation page."""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from cooling_rag_mg.engineering_requirement_agent import (
    generate_engineering_requirements,
    save_engineering_requirements,
)
from cooling_rag_mg.sysml_exporter import export_payload_bytes
from ui.state import ENGINEERING_STATUS_LABELS, normalize_df
from ui.components.shared import (
    render_workspace_header,
    engineering_badge_html,
)


def _build_req_tree(items: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    result = []
    for item in items:
        if item.get("parent_id") == parent_id:
            node = dict(item)
            node["_children"] = _build_req_tree(items, node.get("id", ""))
            result.append(node)
    return result


def _sysml_block_html(item: dict[str, Any], depth: int = 0) -> str:
    from ui.state import ENGINEERING_STATUS_CLASS
    status = item.get("support_status", "")
    status_class = {
        "verified_by_direct_evidence": "sysml-direct",
        "supported_by_indirect_evidence": "sysml-indirect",
        "evidence_gap": "sysml-gap",
        "need_confirmation": "sysml-confirm",
    }.get(status, "sysml-unknown")
    status_label = ENGINEERING_STATUS_LABELS.get(status, status)
    badge_class = ENGINEERING_STATUS_CLASS.get(status, "badge-na")
    req_id = escape(str(item.get("id", "") or ""))
    topic = escape(str(item.get("topic", "") or ""))
    shall_raw = str(item.get("shall_statement", "") or "")
    shall_display = escape(shall_raw[:130] + ("…" if len(shall_raw) > 130 else ""))
    verif = escape(str(item.get("verification_method", "") or ""))
    ev_list = [str(x) for x in (item.get("evidence_ids") or [])]
    evidence = escape(", ".join(ev_list) if ev_list else "—")
    depth_class = "sysml-l1" if depth == 0 else "sysml-l2"
    children = item.get("_children", [])
    children_html = ""
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
        f'</div></div>'
        f'{children_html}'
        f'</div>'
    )


def render_engineering_requirement_overview(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    total_items = sum(len(x.get("engineering_requirements", []) or []) for x in req_sets)
    direct_items = sum(
        1
        for req_set in req_sets
        for item in req_set.get("engineering_requirements", []) or []
        if item.get("support_status") == "verified_by_direct_evidence"
    )
    gap_items = sum(
        1
        for req_set in req_sets
        for item in req_set.get("engineering_requirements", []) or []
        if item.get("support_status") == "evidence_gap"
    )
    cols = st.columns(3)
    for col, label, value, caption in [
        (cols[0], "需求集", len(req_sets), ""),
        (cols[1], "工程需求", total_items, ""),
        (cols[2], "证据缺口", gap_items, f"直接证据支撑 {direct_items} 条"),
    ]:
        with col:
            extra = f'<div class="muted">{escape(caption)}</div>' if caption else ""
            st.markdown(
                f'<div class="summary-card">'
                f'<div class="summary-label">{escape(label)}</div>'
                f'<div class="summary-value">{value}</div>'
                f'{extra}</div>',
                unsafe_allow_html=True,
            )


def render_sysml_requirement_table(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    rows = []
    for req_set in req_sets:
        for item in req_set.get("engineering_requirements", []) or []:
            rows.append({
                "需求集": req_set.get("requirement_set_id", ""),
                "来源需求": req_set.get("source_requirement_id", ""),
                "ID": item.get("id", ""),
                "父级": item.get("parent_id", ""),
                "层级": item.get("level", ""),
                "类型": item.get("requirement_type", ""),
                "主题": item.get("topic", ""),
                "工程化需求": item.get("shall_statement", ""),
                "验证方式": item.get("verification_method", ""),
                "支撑状态": ENGINEERING_STATUS_LABELS.get(item.get("support_status", ""), item.get("support_status", "")),
                "证据": ", ".join([str(x) for x in item.get("evidence_ids", []) or []]),
            })
    if not rows:
        st.info("没有可展示的工程化需求表。")
        return
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    for req_set in req_sets:
        set_id = req_set.get("requirement_set_id", "")
        source_id = req_set.get("source_requirement_id", "")
        with st.expander(f"{set_id}｜来源 {source_id}｜完整验收判据与风险", expanded=False):
            st.markdown(f"**工程化摘要**  {req_set.get('professional_summary', '')}")
            for item in req_set.get("engineering_requirements", []) or []:
                st.markdown(
                    f'<div class="evidence-card">'
                    f'<div class="evidence-title">{engineering_badge_html(item.get("support_status", ""))}'
                    f'{escape(str(item.get("id", "") or ""))}｜{escape(str(item.get("topic", "") or ""))}</div>'
                    f'<div>{escape(str(item.get("shall_statement", "") or ""))}</div>'
                    f'<div class="muted">验证方式：{escape(str(item.get("verification_method", "") or ""))}｜'
                    f'证据：{escape(", ".join([str(x) for x in item.get("evidence_ids", []) or []]) or "无")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                criteria = item.get("acceptance_criteria", []) or []
                if criteria:
                    st.markdown("**验收判据**")
                    for criterion in criteria:
                        st.write(f"- {criterion}")
                st.markdown("**未满足风险**")
                st.write(item.get("risk_if_unmet", "无"))


def render_sysml_requirement_diagram(payload: dict[str, Any]) -> None:
    req_sets = payload.get("requirement_sets", []) or []
    if not req_sets:
        st.info("没有可展示的工程化需求。")
        return
    for req_set in req_sets:
        set_id = req_set.get("requirement_set_id", "")
        source_id = req_set.get("source_requirement_id", "")
        stakeholder = req_set.get("stakeholder", "")
        summary = req_set.get("professional_summary", "")
        items = req_set.get("engineering_requirements", []) or []
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
        with st.expander(f"{set_id} — 完整验收判据与风险", expanded=False):
            for item in items:
                st.markdown(
                    f'<div class="evidence-card">'
                    f'<div class="evidence-title">'
                    f'{engineering_badge_html(item.get("support_status", ""))}'
                    f'{escape(str(item.get("id", "") or ""))} ｜ {escape(str(item.get("topic", "") or ""))}'
                    f'</div>'
                    f'<div>{escape(str(item.get("shall_statement", "") or ""))}</div>'
                    f'<div class="muted">验证方式：{escape(str(item.get("verification_method", "") or ""))} ｜ '
                    f'证据：{escape(", ".join([str(x) for x in item.get("evidence_ids", []) or []]) or "无")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                criteria = item.get("acceptance_criteria", []) or []
                if criteria:
                    st.markdown("**验收判据**")
                    for c in criteria:
                        st.write(f"- {c}")
                risk = item.get("risk_if_unmet", "")
                if risk:
                    st.markdown("**未满足风险**")
                    st.write(risk)


def render_engineering_workspace(cfg: Any) -> None:
    render_workspace_header(
        "工程化需求",
        "基于原始需求和有支撑证据生成工程化需求，以 SysML 需求图方式呈现层级结构与支撑状态。",
        "SysML Requirement",
    )
    has_results = st.session_state.results is not None
    control_col, note_col = st.columns([1.1, 4])
    with control_col:
        generate_clicked = st.button(
            "生成工程化需求",
            type="primary",
            width="stretch",
            disabled=(not has_results) or bool(st.session_state.is_generating),
        )
    with note_col:
        if has_results:
            st.markdown('<div class="workflow-note">已检测到检索结果，可以调用工程化需求智能体。生成过程结束后会自动刷新。</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="workflow-note">请先完成检索。没有检索结果时不能生成工程化需求。</div>', unsafe_allow_html=True)

    if generate_clicked:
        current_requirements = normalize_df(st.session_state.requirements_df)
        if not cfg.deepseek.enabled:
            st.error("DeepSeek 未配置，无法运行工程化需求智能体。")
        elif not current_requirements:
            st.warning("没有启用的原始需求。")
        elif not st.session_state.results:
            st.warning("没有检索结果。请先运行检索。")
        else:
            st.session_state.is_generating = True
            try:
                with st.spinner("正在通过 LangGraph 调用 DeepSeek 生成工程化需求。"):
                    engineering_payload = generate_engineering_requirements(current_requirements, st.session_state.results)
                    if st.session_state.last_output:
                        retrieval_dir = Path(st.session_state.last_output).parent
                        out_path = save_engineering_requirements(retrieval_dir, engineering_payload)
                    else:
                        out_path = save_engineering_requirements(cfg.paths.search_results_dir, engineering_payload)
                    st.session_state.engineering_requirements = engineering_payload
                    st.session_state.last_engineering_output = str(out_path)
                st.success(f"工程化需求已生成：{out_path}")
            finally:
                st.session_state.is_generating = False
            st.rerun()

    if st.session_state.last_engineering_output:
        st.success("最近工程化需求输出已保存。")
        with st.expander("查看输出路径", expanded=False):
            st.code(st.session_state.last_engineering_output, language="text")

    payload = st.session_state.engineering_requirements
    if not payload:
        st.info("尚未生成工程化需求。点击上方按钮后可在需求图中查看层级结构和支撑状态。")
        return
    render_engineering_requirement_overview(payload)

    # ── Export row ──────────────────────────────────────────────────────────
    export_col, _ = st.columns([1.1, 4])
    with export_col:
        try:
            xml_bytes = export_payload_bytes(payload)
            st.download_button(
                label="导出 SysML XML",
                data=xml_bytes,
                file_name="requirements_sysml.xml",
                mime="application/xml",
                width="stretch",
            )
        except Exception as _exc:
            st.error(f"SysML XML 导出失败：{_exc}")

    diagram_tab, table_tab, gap_tab, raw_tab = st.tabs(["需求图", "SysML 需求表", "证据缺口", "原始 JSON"])
    with diagram_tab:
        render_sysml_requirement_diagram(payload)
    with table_tab:
        render_sysml_requirement_table(payload)
    with gap_tab:
        gaps = []
        for req_set in payload.get("requirement_sets", []) or []:
            for gap in req_set.get("evidence_gaps", []) or []:
                gaps.append({
                    "需求集": req_set.get("requirement_set_id", ""),
                    "related_requirement_id": gap.get("related_requirement_id", ""),
                    "gap_type": gap.get("gap_type", ""),
                    "description": gap.get("description", ""),
                    "suggested_document_update": gap.get("suggested_document_update", ""),
                })
        if gaps:
            st.dataframe(pd.DataFrame(gaps), width="stretch", hide_index=True)
        else:
            st.success("没有单独列出的证据缺口。")
    with raw_tab:
        st.json(payload)
