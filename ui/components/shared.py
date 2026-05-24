# -*- coding: utf-8 -*-
"""Shared HTML helper functions used across pages."""
from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from ui.state import SUPPORT_LABELS, SUPPORT_CLASS, ENGINEERING_STATUS_LABELS, ENGINEERING_STATUS_CLASS


def status_pill_html(label: str, value: str, tone: str = "neutral") -> str:
    tone_class = "" if tone == "neutral" else f" {tone}"
    return f'<span class="status-pill{tone_class}">{escape(label)}<strong>{escape(value)}</strong></span>'


def render_status_pill(label: str, value: str, tone: str = "neutral") -> None:
    st.markdown(status_pill_html(label, value, tone), unsafe_allow_html=True)


def render_workspace_header(title: str, caption: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="page-hero">
            <div class="page-kicker">{escape(kicker)}</div>
            <div class="page-title">{escape(title)}</div>
            <div class="page-subtitle">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, caption: str = "", kicker: str = "") -> None:
    kicker_html = f'<div class="section-kicker">{escape(kicker)}</div>' if kicker else ""
    caption_html = f'<div class="section-caption">{escape(caption)}</div>' if caption else ""
    st.markdown(
        f"""
        <div class="section-header">
            {kicker_html}
            <div class="section-title">{escape(title)}</div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_html(support_type: str) -> str:
    cls = SUPPORT_CLASS.get(support_type, "badge-na")
    label = SUPPORT_LABELS.get(support_type, support_type or "未审查")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def engineering_badge_html(status: str) -> str:
    cls = ENGINEERING_STATUS_CLASS.get(status, "badge-confirm")
    label = ENGINEERING_STATUS_LABELS.get(status, status or "未标注")
    return f'<span class="badge {cls}">{escape(label)}</span>'


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def format_score(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "无"
    return f"{number:.3f}"


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "待估计"
    seconds = max(0, int(round(seconds)))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}小时{minutes}分{sec}秒"
    if minutes:
        return f"{minutes}分{sec}秒"
    return f"{sec}秒"
