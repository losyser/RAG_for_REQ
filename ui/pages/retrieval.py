# -*- coding: utf-8 -*-
"""Retrieval workspace page."""
from __future__ import annotations

import time
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from cooling_rag_mg.evidence_pack import make_batch_dir, save_pack
from cooling_rag_mg.pipeline import make_services, run_requirements_with_services
from ui.state import normalize_df
from ui.components.shared import (
    render_workspace_header,
    render_section_header,
    status_pill_html,
    badge_html,
    format_score,
    format_duration,
)


# ── Payload helpers ────────────────────────────────────────────


def empty_payload() -> dict[str, Any]:
    return {
        "requirements": [],
        "diagnostics": {
            "requirement_count": 0,
            "sub_requirement_count": 0,
            "selected_evidence_count": 0,
            "evidence_gap_count": 0,
        },
    }


def merge_payload(target: dict[str, Any], part: dict[str, Any]) -> None:
    target.setdefault("requirements", []).extend(part.get("requirements", []) or [])
    target_diag = target.setdefault("diagnostics", {})
    part_diag = part.get("diagnostics", {}) or {}
    for key in ["requirement_count", "sub_requirement_count", "selected_evidence_count", "evidence_gap_count"]:
        target_diag[key] = int(target_diag.get(key, 0) or 0) + int(part_diag.get(key, 0) or 0)


def summarize_payload(payload: dict[str, Any]) -> dict[str, int]:
    reqs = payload.get("requirements", []) or []
    sub_count = selected_count = direct_count = indirect_count = background_count = gap_count = 0
    for req in reqs:
        for sub in req.get("sub_requirements", []) or []:
            sub_count += 1
            if sub.get("evidence_gap"):
                gap_count += 1
            for ev in sub.get("selected_results", []) or []:
                selected_count += 1
                support_type = (ev.get("llm_judge", {}) or {}).get("support_type", "")
                if support_type == "direct":
                    direct_count += 1
                elif support_type == "indirect":
                    indirect_count += 1
                elif support_type == "background":
                    background_count += 1
    return {
        "requirements": len(reqs),
        "sub_requirements": sub_count,
        "selected_evidence": selected_count,
        "direct": direct_count,
        "indirect": indirect_count,
        "background": background_count,
        "gaps": gap_count,
    }


# ── Card renderers ─────────────────────────────────────────────


def render_summary_cards(payload: dict[str, Any]) -> None:
    summary = summarize_payload(payload)
    columns = st.columns(6)
    cards = [
        ("需求数", summary["requirements"]),
        ("子需求", summary["sub_requirements"]),
        ("保留证据", summary["selected_evidence"]),
        ("直接支撑", summary["direct"]),
        ("间接支撑", summary["indirect"]),
        ("证据缺口", summary["gaps"]),
    ]
    for col, (label, value) in zip(columns, cards):
        with col:
            st.markdown(
                f'<div class="summary-card">'
                f'<div class="summary-label">{escape(label)}</div>'
                f'<div class="summary-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_evidence_card(ev: dict[str, Any], idx: int) -> None:
    meta = ev.get("metadata", {}) or {}
    judge = ev.get("llm_judge", {}) or {}
    support_type = judge.get("support_type", "")
    evidence_id = str(ev.get("id", "") or "")
    topic = str(meta.get("topic", "") or "未命名证据")
    source = str(meta.get("source_document", "") or "未知来源")
    location = str(meta.get("location", "") or "未知位置")
    reason = str(judge.get("reason", "") or "无审查说明")
    text = str(ev.get("text", "") or "")

    st.markdown(
        f'<div class="evidence-card">'
        f'<div class="evidence-title">{badge_html(support_type)}{idx}. {escape(evidence_id)}｜{escape(topic)}</div>'
        f'<div class="muted">来源：{escape(source)}｜位置：{escape(location)}</div>'
        f'<div class="muted">判断理由：{escape(reason)}</div>'
        f'<div class="muted">final_score：{format_score(ev.get("final_score"))}｜rrf_score：{format_score(ev.get("rrf_score"))}｜profile_score：{format_score(ev.get("profile_score"))}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("查看原文和详细字段", expanded=False):
        st.code(text, language="text")
        left, right = st.columns(2)
        with left:
            st.markdown("**LLM Judge**")
            st.json(judge)
        with right:
            st.markdown("**Metadata**")
            st.json(meta)


def sub_support_type(sub: dict[str, Any]) -> str:
    selected = sub.get("selected_results", []) or []
    support_types = [(ev.get("llm_judge", {}) or {}).get("support_type", "") for ev in selected]
    if "direct" in support_types:
        return "direct"
    if "indirect" in support_types:
        return "indirect"
    if "background" in support_types:
        return "background"
    if sub.get("evidence_gap"):
        return "not_applicable"
    return ""


def render_compact_sub_requirement(sub: dict[str, Any]) -> None:
    selected = sub.get("selected_results", []) or []
    support_type = sub_support_type(sub)
    evidence_chips = []
    if selected:
        evidence_chips.append(f'<span class="evidence-chip">保留证据 {len(selected)} 条</span>')
    for ev in selected:
        meta = ev.get("metadata", {}) or {}
        evidence_id = escape(str(ev.get("id", "") or "未编号"))
        source = escape(str(meta.get("source_document", "") or "未知来源"))
        evidence_chips.append(f'<span class="evidence-chip">{evidence_id}｜{source}</span>')
    if not evidence_chips:
        evidence_chips.append('<span class="evidence-chip">暂无保留证据</span>')

    st.markdown(
        f'<div class="compact-sub">'
        f'<div class="compact-sub-title">'
        f'{badge_html(support_type)}'
        f'{escape(str(sub.get("sub_requirement_id", "") or ""))}｜{escape(str(sub.get("requirement_type", "") or ""))}｜{escape(str(sub.get("topic", "") or ""))}'
        f'</div>'
        f'<div class="muted">{escape(str(sub.get("text", "") or ""))}</div>'
        f'<div>{"".join(evidence_chips)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"展开详情：{sub.get('sub_requirement_id', '')}", expanded=False):
        if sub.get("evidence_gap"):
            reason = (sub.get("evidence_gap") or {}).get("reason", "")
            st.warning(f"证据缺口：{reason}")
        tabs = st.tabs(["保留证据", "检索画像", "候选证据", "调试信息"])
        with tabs[0]:
            if not selected:
                st.info("没有保留证据。")
            for idx, ev in enumerate(selected, start=1):
                render_evidence_card(ev, idx)
        with tabs[1]:
            query = sub.get("retrieval_query", "") or ""
            st.markdown("**检索 query**")
            st.markdown(f'<div class="query-box">{escape(query)}</div>', unsafe_allow_html=True)
            st.markdown("**Profile**")
            st.json(sub.get("profile", {}))
        with tabs[2]:
            candidates = sub.get("candidate_results", []) or []
            if candidates:
                table = []
                for item in candidates[:20]:
                    meta = item.get("metadata", {}) or {}
                    table.append({
                        "id": item.get("id"),
                        "topic": meta.get("topic", ""),
                        "source": meta.get("source_document", ""),
                        "score": format_score(item.get("final_score")),
                    })
                st.dataframe(pd.DataFrame(table), width="stretch", hide_index=True)
            else:
                st.info("没有候选证据。")
            with st.expander("查看 rejected_results", expanded=False):
                st.json(sub.get("rejected_results", []))
        with tabs[3]:
            st.markdown("**Stage Diagnostics**")
            st.json(sub.get("stage_diagnostics", {}))
            st.markdown("**Judge Result**")
            st.json(sub.get("judge_result", {}))


def render_compact_results(payload: dict[str, Any]) -> None:
    render_summary_cards(payload)
    requirements = payload.get("requirements", []) or []
    result_count = len(requirements)
    enabled_count = len(normalize_df(st.session_state.requirements_df))
    tone = "success" if result_count == enabled_count else "warning"
    st.markdown(
        f'<div class="status-strip">'
        f'{status_pill_html("结果需求数", str(result_count), tone)}'
        f'{status_pill_html("当前启用需求数", str(enabled_count), "neutral")}'
        f'</div>',
        unsafe_allow_html=True,
    )
    if result_count != enabled_count:
        st.warning("当前启用需求数与已保存检索结果数不一致。通常是检索后又修改了需求表；请重新运行检索以同步结果。")

    if not requirements:
        st.info("当前结果文件中没有需求结果。")
        return

    overview_rows = []
    for req in requirements:
        req_id = str(req.get("requirement_id", "") or "")
        stakeholder = str(req.get("stakeholder", "") or "")
        sub_requirements = req.get("sub_requirements", []) or []
        gap_count = sum(1 for sub in sub_requirements if sub.get("evidence_gap"))
        selected_count = sum(len(sub.get("selected_results", []) or []) for sub in sub_requirements)
        direct_count = sum(
            1
            for sub in sub_requirements
            for ev in sub.get("selected_results", []) or []
            if (ev.get("llm_judge", {}) or {}).get("support_type") == "direct"
        )
        overview_rows.append({
            "需求编号": req_id,
            "提出方": stakeholder,
            "子需求": len(sub_requirements),
            "保留证据": selected_count,
            "直接证据": direct_count,
            "证据缺口": gap_count,
        })

    render_section_header("需求概览", "这里展示本次结果中的全部原始需求；下方选择一条查看详细证据链。", "Overview")
    st.dataframe(pd.DataFrame(overview_rows), width="stretch", hide_index=True)

    options = [str(req.get("requirement_id", "") or f"REQ-{idx + 1}") for idx, req in enumerate(requirements)]
    selected_req_id = st.selectbox(
        "选择要查看的需求",
        options=options,
        format_func=lambda rid: next(
            (
                f"{rid}｜{req.get('stakeholder', '')}｜子需求 {len(req.get('sub_requirements', []) or [])}"
                for req in requirements
                if str(req.get("requirement_id", "") or "") == rid
            ),
            rid,
        ),
    )
    selected_req = next(
        (req for req in requirements if str(req.get("requirement_id", "") or "") == selected_req_id),
        requirements[0],
    )

    req_id = str(selected_req.get("requirement_id", "") or "")
    stakeholder = str(selected_req.get("stakeholder", "") or "")
    raw_text = str(selected_req.get("raw_requirement_text", "") or "")
    sub_requirements = selected_req.get("sub_requirements", []) or []
    gap_count = sum(1 for sub in sub_requirements if sub.get("evidence_gap"))
    selected_count = sum(len(sub.get("selected_results", []) or []) for sub in sub_requirements)

    render_section_header("需求详情", "默认只显示子需求、支撑状态和保留证据摘要；原文和调试字段在展开详情中。", "Detail")
    st.markdown(
        f'<div class="compact-req-card">'
        f'<div class="compact-req-head">'
        f'<div>'
        f'<div class="compact-req-title">{escape(req_id)}｜{escape(stakeholder)}</div>'
        f'<div class="muted">{escape(raw_text)}</div>'
        f'</div>'
        f'<div class="status-strip">'
        f'{status_pill_html("子需求", str(len(sub_requirements)), "neutral")}'
        f'{status_pill_html("证据", str(selected_count), "success" if selected_count else "warning")}'
        f'{status_pill_html("缺口", str(gap_count), "danger" if gap_count else "success")}'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    for sub in sub_requirements:
        render_compact_sub_requirement(sub)


# ── Progress UI ────────────────────────────────────────────────


def update_progress_ui(
    progress_bar: Any,
    status_box: Any,
    metric_box: Any,
    *,
    fraction: float,
    title: str,
    detail: str,
    completed: int,
    total: int,
    elapsed_seconds: float,
    remaining_seconds: float | None,
) -> None:
    percent = max(0, min(100, int(round(fraction * 100))))
    progress_bar.progress(percent, text=title)
    metric_box.markdown(
        f'<div class="progress-card">'
        f'<div class="summary-label">运行进度</div>'
        f'<div class="summary-value">{completed}/{total}</div>'
        f'<div class="muted">已用：{format_duration(elapsed_seconds)}｜预计剩余：{format_duration(remaining_seconds)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    status_box.info(detail)


def render_run_panel(title: str, detail: str) -> None:
    st.markdown(
        f'<div class="run-panel">'
        f'<div class="run-title">{escape(title)}</div>'
        f'<div class="run-detail">{escape(detail)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def run_with_progress(
    requirements: list[dict[str, Any]],
    *,
    cfg: Any,
    top_k: int,
    coarse_k: int,
    fine_k: int,
) -> tuple[dict[str, Any], Path, float]:
    total = len(requirements)
    start = time.perf_counter()
    progress_bar = st.progress(0, text="准备检索")
    status_box = st.empty()
    metric_box = st.empty()
    stage_box = st.empty()
    with stage_box.container():
        render_run_panel("多粒度证据检索运行中", "正在执行需求拆分、粗粒度召回、细粒度召回、工程适用性过滤与证据审查。")

    update_progress_ui(
        progress_bar, status_box, metric_box,
        fraction=0.02,
        title="加载索引和模型",
        detail="正在加载多粒度索引、BM25、FAISS 和 embedding 模型。首次运行会比较慢。",
        completed=0, total=total, elapsed_seconds=0, remaining_seconds=None,
    )

    services = make_services()
    payload = empty_payload()
    load_elapsed = time.perf_counter() - start
    update_progress_ui(
        progress_bar, status_box, metric_box,
        fraction=0.08,
        title="模型加载完成",
        detail=f"模型和索引已加载。加载耗时：{format_duration(load_elapsed)}。",
        completed=0, total=total, elapsed_seconds=load_elapsed, remaining_seconds=None,
    )

    request_times: list[float] = []
    for index, req in enumerate(requirements, start=1):
        req_id = req.get("requirement_id", f"第{index}条")
        before = time.perf_counter()
        completed_before = index - 1
        fraction_before = 0.08 + (completed_before / total) * 0.88
        avg_seconds = sum(request_times) / len(request_times) if request_times else None
        remaining_before = avg_seconds * (total - completed_before) if avg_seconds is not None else None
        update_progress_ui(
            progress_bar, status_box, metric_box,
            fraction=fraction_before,
            title=f"正在检索 {index}/{total}：{req_id}",
            detail="当前阶段包括需求拆分、粗检索、细检索、工程适用性过滤和证据审查。",
            completed=completed_before, total=total,
            elapsed_seconds=time.perf_counter() - start,
            remaining_seconds=remaining_before,
        )
        part = run_requirements_with_services(
            [req],
            services=services,
            top_k=top_k,
            coarse_k=coarse_k,
            fine_k=fine_k,
        )
        merge_payload(payload, part)
        current_elapsed = time.perf_counter() - before
        request_times.append(current_elapsed)
        completed = index
        avg_seconds = sum(request_times) / len(request_times)
        remaining = avg_seconds * (total - completed)
        fraction_after = 0.08 + (completed / total) * 0.88
        update_progress_ui(
            progress_bar, status_box, metric_box,
            fraction=fraction_after,
            title=f"已完成 {completed}/{total}：{req_id}",
            detail=f"本条耗时：{format_duration(current_elapsed)}。预计剩余时间按已完成需求的平均耗时计算。",
            completed=completed, total=total,
            elapsed_seconds=time.perf_counter() - start,
            remaining_seconds=remaining,
        )

    batch = make_batch_dir(cfg.paths.search_results_dir)
    out_path = save_pack(batch, payload)
    runtime = time.perf_counter() - start
    stage_box.empty()
    progress_bar.progress(100, text="检索完成")
    status_box.success(f"检索完成。结果已保存：{out_path}")
    metric_box.markdown(
        f'<div class="progress-card">'
        f'<div class="summary-label">运行完成</div>'
        f'<div class="summary-value">100%</div>'
        f'<div class="muted">总耗时：{format_duration(runtime)}｜输出：{out_path}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    return payload, out_path, runtime


# ── Page render ────────────────────────────────────────────────


def render_retrieval_workspace(cfg: Any) -> None:
    render_workspace_header(
        "检索工作台",
        "调整检索参数和原始需求。启动后系统会执行多粒度召回、工程适用性过滤与证据审查。",
        "Retrieval Console",
    )
    with st.expander("检索参数", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            top_k = st.number_input("每个子需求保留证据数", min_value=1, max_value=10, value=int(st.session_state.top_k), step=1, key="top_k_input")
        with cols[1]:
            coarse_k = st.number_input("大颗粒度候选数", min_value=5, max_value=50, value=int(st.session_state.coarse_k), step=1, key="coarse_k_input")
        with cols[2]:
            fine_k = st.number_input("小颗粒度候选数", min_value=10, max_value=100, value=int(st.session_state.fine_k), step=5, key="fine_k_input")
    st.session_state.top_k = int(top_k)
    st.session_state.coarse_k = int(coarse_k)
    st.session_state.fine_k = int(fine_k)

    render_section_header("原始需求", "只保留启用且需求内容非空的行进入检索。", "Input")
    edited_df = st.data_editor(
        st.session_state.requirements_df,
        key="requirements_editor",
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        column_config={
            "需求编号": st.column_config.TextColumn("需求编号", width="small"),
            "提出方": st.column_config.TextColumn("提出方", width="medium"),
            "需求内容": st.column_config.TextColumn("需求内容", width="large"),
            "启用": st.column_config.CheckboxColumn("启用", width="small"),
        },
    )
    enabled_count = len(normalize_df(pd.DataFrame(edited_df)))
    action_col, info_col, clear_col = st.columns([1.05, 3.6, 1.05])
    with action_col:
        start_clicked = st.button("开始检索", type="primary", width="stretch", disabled=bool(st.session_state.is_retrieving))
    with info_col:
        st.markdown(f'<div class="workflow-note">当前启用需求 {enabled_count} 条。检索完成后会停留在本页，避免长任务结束后强制刷新导致页面失去响应。</div>', unsafe_allow_html=True)
    with clear_col:
        clear_clicked = st.button("清空结果", width="stretch", disabled=bool(st.session_state.is_retrieving))

    if clear_clicked:
        st.session_state.results = None
        st.session_state.engineering_requirements = None
        st.session_state.last_output = ""
        st.session_state.last_engineering_output = ""
        st.session_state.last_runtime = None
        st.session_state.show_result_cta = False
        st.rerun()

    if start_clicked:
        st.session_state.requirements_df = pd.DataFrame(edited_df)
        reqs = normalize_df(edited_df)
        if not reqs:
            st.warning("没有可检索的需求。")
            return
        st.session_state.is_retrieving = True
        try:
            payload, out_path, runtime = run_with_progress(
                reqs,
                cfg=cfg,
                top_k=int(top_k),
                coarse_k=int(coarse_k),
                fine_k=int(fine_k),
            )
            st.session_state.results = payload
            st.session_state.last_output = str(out_path)
            st.session_state.last_runtime = runtime
            st.session_state.show_result_cta = True
        finally:
            st.session_state.is_retrieving = False

    if st.session_state.results and st.session_state.show_result_cta:
        st.success("检索已完成。请进入检索结果页查看全部需求概览。")
        if st.button("查看检索结果", type="primary", width="stretch"):
            st.session_state.active_workspace = "retrieval_results"
            st.session_state.show_result_cta = False
            st.rerun()
