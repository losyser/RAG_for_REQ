# -*- coding: utf-8 -*-
"""Retrieval results view page."""
from __future__ import annotations

import streamlit as st

from ui.components.shared import render_workspace_header
from ui.pages.retrieval import render_compact_results


def render_retrieval_results_workspace() -> None:
    render_workspace_header(
        "检索结果",
        "结果区只呈现最直接的信息。需求原文、候选证据、拒绝结果和调试字段放入折叠详情中。",
        "Evidence View",
    )
    if not st.session_state.results:
        st.info('尚未完成检索。请先进入「检索工作台」运行检索。')
        if st.button("进入检索工作台", type="primary"):
            st.session_state.active_workspace = "retrieval_workspace"
            st.rerun()
        return
    render_compact_results(st.session_state.results)
