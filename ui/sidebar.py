# -*- coding: utf-8 -*-
"""Navigation sidebar."""
from __future__ import annotations

from typing import Any

import streamlit as st

from ui.state import WORKSPACE_LABELS
from ui.components.shared import render_status_pill, format_duration


def render_nav_sidebar(cfg: Any) -> str:
    current = st.session_state.get("active_workspace", "retrieval_workspace")
    if current not in WORKSPACE_LABELS:
        current = "retrieval_workspace"
        st.session_state.active_workspace = current

    with st.sidebar:
        st.markdown(
            """
            <div class="nav-brand">
                <div class="nav-brand-title">冷却水系统 RAG</div>
                <div class="nav-brand-caption">需求检索、证据审查和工程化需求生成</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _core_keys = ["retrieval_workspace", "retrieval_results", "engineering_workspace"]
        _exp_keys  = ["experiment_comparison", "metrics_analysis"]
        _mgmt_keys = ["evidence_manager"]

        for workspace_key in _core_keys:
            selected = workspace_key == current
            button_type = "primary" if selected else "secondary"
            if st.button(WORKSPACE_LABELS[workspace_key], key=f"nav_{workspace_key}", type=button_type, width="stretch"):
                st.session_state.active_workspace = workspace_key
                st.rerun()

        st.markdown('<hr style="margin:10px 0;border-color:#e2e8f0">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:#94a3b8;font-weight:660;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px">实验与评估</div>', unsafe_allow_html=True)

        for workspace_key in _exp_keys:
            selected = workspace_key == current
            button_type = "primary" if selected else "secondary"
            if st.button(WORKSPACE_LABELS[workspace_key], key=f"nav_{workspace_key}", type=button_type, width="stretch"):
                st.session_state.active_workspace = workspace_key
                st.rerun()

        st.markdown('<hr style="margin:10px 0;border-color:#e2e8f0">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.72rem;color:#94a3b8;font-weight:660;letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px">数据管理</div>', unsafe_allow_html=True)

        for workspace_key in _mgmt_keys:
            selected = workspace_key == current
            button_type = "primary" if selected else "secondary"
            if st.button(WORKSPACE_LABELS[workspace_key], key=f"nav_{workspace_key}", type=button_type, width="stretch"):
                st.session_state.active_workspace = workspace_key
                st.rerun()

        has_results = st.session_state.results is not None
        has_engineering = st.session_state.engineering_requirements is not None

        st.markdown('<div class="nav-meta">', unsafe_allow_html=True)
        render_status_pill("DeepSeek", "已配置" if cfg.deepseek.enabled else "未配置", "success" if cfg.deepseek.enabled else "danger")
        render_status_pill("检索", "已有结果" if has_results else "待运行", "success" if has_results else "warning")
        render_status_pill("工程化", "已生成" if has_engineering else "待生成", "success" if has_engineering else "warning")
        if st.session_state.last_runtime is not None:
            render_status_pill("耗时", format_duration(st.session_state.last_runtime), "neutral")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("运行路径", expanded=False):
            st.caption("检索输出目录")
            st.code(str(cfg.paths.search_results_dir), language="text")
            if st.session_state.last_output:
                st.caption("最近检索输出")
                st.code(st.session_state.last_output, language="text")
            if st.session_state.last_engineering_output:
                st.caption("最近工程化输出")
                st.code(st.session_state.last_engineering_output, language="text")

    return st.session_state.get("active_workspace", current)
