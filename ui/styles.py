# -*- coding: utf-8 -*-
"""Global CSS for the Streamlit app."""
from __future__ import annotations

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f6f8fb;
            --panel: #ffffff;
            --panel-soft: #f9fbfd;
            --line: #dbe3ea;
            --line-strong: #c8d4df;
            --text: #1f2937;
            --muted: #64748b;
            --accent: #2563eb;
            --accent-soft: #eff6ff;
            --success: #15803d;
            --success-bg: #ecfdf3;
            --warning: #a16207;
            --warning-bg: #fffbeb;
            --danger: #b91c1c;
            --danger-bg: #fef2f2;
            --shadow: 0 10px 26px rgba(15, 23, 42, 0.07);
        }
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        .block-container {
            max-width: 1320px;
            padding-top: 1.15rem;
            padding-bottom: 2rem;
        }
        section[data-testid="stSidebar"] {
            width: 15rem !important;
            min-width: 15rem !important;
            background: #ffffff;
            border-right: 1px solid var(--line);
            box-shadow: 8px 0 22px rgba(15, 23, 42, 0.04);
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding: 1rem 0.85rem 1.25rem;
        }
        .nav-brand {
            padding: 4px 2px 12px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--line);
        }
        .nav-brand-title {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 760;
            line-height: 1.35;
        }
        .nav-brand-caption {
            color: var(--muted);
            font-size: 0.76rem;
            line-height: 1.55;
            margin-top: 5px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            display: grid;
            gap: 7px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 9px 10px;
            background: #ffffff;
            color: var(--text);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            border-color: #93c5fd;
            background: var(--accent-soft);
            box-shadow: inset 3px 0 0 var(--accent);
        }
        h1, h2, h3,
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3 {
            color: var(--text);
            letter-spacing: 0;
        }
        div[data-testid="stMarkdownContainer"] p {
            line-height: 1.65;
        }
        .page-hero {
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 18px 20px 16px;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff, #f8fbff);
            box-shadow: var(--shadow);
        }
        .page-kicker {
            color: var(--accent);
            font-size: 0.74rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .page-title {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 780;
            line-height: 1.2;
            margin-bottom: 7px;
        }
        .page-subtitle {
            color: var(--muted);
            max-width: 940px;
            font-size: 0.94rem;
            line-height: 1.65;
            margin-bottom: 12px;
        }
        .section-header {
            margin: 18px 0 10px;
        }
        .section-kicker {
            color: var(--accent);
            font-size: 0.72rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        .section-title {
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 760;
            line-height: 1.35;
            margin-bottom: 3px;
        }
        .section-caption, .workflow-note, .muted {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            align-items: center;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 4px 10px;
            background: #ffffff;
            color: var(--muted);
            font-size: 0.8rem;
            font-weight: 650;
        }
        .status-pill strong {
            color: var(--text);
            font-weight: 760;
        }
        .status-pill.success {
            color: var(--success);
            background: var(--success-bg);
            border-color: #bbf7d0;
        }
        .status-pill.warning {
            color: var(--warning);
            background: var(--warning-bg);
            border-color: #fde68a;
        }
        .status-pill.danger {
            color: var(--danger);
            background: var(--danger-bg);
            border-color: #fecaca;
        }
        div[data-testid="stMetric"] {
            background: transparent;
            border: 0;
            padding: 0.1rem 0;
        }
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.8rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 720;
        }
        div[data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: var(--panel);
            box-shadow: none;
            overflow: hidden;
        }
        div[data-testid="stExpander"] details summary {
            background: var(--panel-soft);
            min-height: 42px;
        }
        div[data-testid="stTabs"] button {
            color: var(--muted);
            font-weight: 650;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
            background: var(--panel);
        }
        div[data-testid="stAlert"] {
            border-radius: 10px;
            border: 1px solid var(--line);
        }
        div[data-testid="stCodeBlock"] {
            border-radius: 10px;
            border: 1px solid var(--line);
        }
        .stButton > button {
            border-radius: 9px;
            min-height: 2.55rem;
            font-weight: 700;
            border: 1px solid var(--line-strong);
            box-shadow: none;
            background: #ffffff;
            color: var(--text);
        }
        .stButton > button[kind="primary"] {
            background: var(--accent);
            border-color: var(--accent);
            color: #ffffff;
        }
        .stButton > button:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
        .stButton > button[kind="primary"]:hover {
            background: #1d4ed8;
            border-color: #1d4ed8;
            color: #ffffff;
        }
        div[data-testid="stProgress"] > div > div > div > div {
            background: var(--accent);
        }
        .summary-card, .progress-card, .compact-req-card, .evidence-card {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--panel);
            box-shadow: var(--shadow);
        }
        .summary-card {
            padding: 12px 14px;
            min-height: 72px;
        }
        .summary-label {
            color: var(--muted);
            font-size: 0.8rem;
            margin-bottom: 4px;
        }
        .summary-value {
            color: var(--text);
            font-size: 1.36rem;
            font-weight: 760;
            line-height: 1.2;
        }
        .progress-card {
            padding: 12px 14px;
            margin-top: 6px;
            box-shadow: none;
        }
        .evidence-card {
            border-left: 3px solid #93c5fd;
            padding: 11px 13px;
            margin: 9px 0;
            box-shadow: none;
        }
        .evidence-title {
            color: var(--text);
            font-weight: 740;
            line-height: 1.55;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 0.76rem;
            font-weight: 700;
            margin-right: 6px;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .badge-direct { color: var(--success); background: var(--success-bg); border-color: #bbf7d0; }
        .badge-indirect { color: var(--warning); background: var(--warning-bg); border-color: #fde68a; }
        .badge-background { color: #475569; background: #f1f5f9; border-color: #cbd5e1; }
        .badge-na { color: var(--danger); background: var(--danger-bg); border-color: #fecaca; }
        .badge-confirm { color: #334155; background: #eef2ff; border-color: #c7d2fe; }
        .query-box {
            border-left: 3px solid #93c5fd;
            padding: 9px 11px;
            background: var(--accent-soft);
            border-radius: 8px;
            white-space: pre-wrap;
            font-size: 0.88rem;
            color: var(--text);
            line-height: 1.65;
        }
        .compact-req-card {
            padding: 12px 14px;
            margin: 10px 0;
        }
        .compact-req-head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            border-bottom: 1px solid var(--line);
            padding-bottom: 9px;
            margin-bottom: 8px;
        }
        .compact-req-title {
            color: var(--text);
            font-weight: 780;
            font-size: 1rem;
        }
        .compact-sub {
            border-left: 2px solid #93c5fd;
            padding: 7px 0 7px 11px;
            margin: 7px 0;
            background: #f8fbff;
        }
        .compact-sub-title {
            color: var(--text);
            font-weight: 730;
            margin-bottom: 3px;
        }
        .evidence-chip {
            display: inline-block;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 2px 8px;
            margin: 3px 4px 3px 0;
            color: var(--text);
            background: var(--accent-soft);
            font-size: 0.76rem;
        }
        .run-panel {
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 12px 14px;
            background: #ffffff;
            box-shadow: var(--shadow);
            margin: 8px 0 12px;
        }
        .run-title {
            color: var(--text);
            font-weight: 760;
            margin-bottom: 4px;
        }
        .run-detail {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.6;
        }
        .sysml-canvas {
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
            margin: 12px 0 18px;
            overflow-x: auto;
            overflow-y: hidden;
        }
        .sysml-diagram-section { margin: 10px 0 22px; }
        .sysml-set-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 3px; }
        .sysml-set-id { font-weight: 780; font-size: 1.0rem; color: var(--text); }
        .sysml-set-src { color: var(--muted); font-size: 0.84rem; }
        .sysml-set-summary { color: var(--muted); font-size: 0.83rem; margin-bottom: 10px; line-height: 1.5; }
        .sysml-blocks-wrap {
            display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;
        }
        .sysml-block {
            border: 2px solid #94a3b8; border-top-width: 4px; border-radius: 8px;
            background: #ffffff; min-width: 200px; max-width: 310px;
            flex: 1 1 220px; overflow: hidden; font-size: 0.82rem;
        }
        .sysml-block.sysml-direct   { border-top-color: #15803d; border-color: #86efac; }
        .sysml-block.sysml-indirect { border-top-color: #b45309; border-color: #fcd34d; }
        .sysml-block.sysml-gap      { border-top-color: #b91c1c; border-color: #fca5a5; background: #fff8f8; }
        .sysml-block.sysml-confirm  { border-top-color: #4338ca; border-color: #c7d2fe; background: #f8f8ff; }
        .sysml-block.sysml-unknown  { border-top-color: #94a3b8; }
        .sysml-stereotype {
            font-size: 0.70rem; color: #64748b; font-style: italic;
            text-align: center; padding: 5px 8px 0; letter-spacing: 0.04em;
        }
        .sysml-block-name {
            font-weight: 760; color: var(--text); text-align: center;
            padding: 3px 8px 5px; font-size: 0.87rem; line-height: 1.4;
            border-bottom: 1.5px solid #e2e8f0;
        }
        .sysml-block-body { padding: 8px 10px; }
        .sysml-attr { margin: 3px 0; line-height: 1.55; color: var(--text); }
        .sysml-attr-label { color: #94a3b8; font-style: italic; font-size: 0.72rem; }
        .sysml-text-val { color: #334155; font-size: 0.79rem; }
        .sysml-meta { margin-top: 7px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
        .sysml-verif-chip {
            font-size: 0.69rem; color: #475569; background: #f1f5f9;
            border: 1px solid #e2e8f0; border-radius: 999px; padding: 1px 7px;
        }
        .sysml-evidence-line { width: 100%; color: #94a3b8; font-size: 0.70rem; margin-top: 3px; }
        .sysml-children {
            border-top: 1.5px dashed #e2e8f0; background: #f9fbfd;
            padding: 8px; display: flex; flex-wrap: wrap; gap: 7px;
        }
        .sysml-block.sysml-l2 {
            min-width: 160px; max-width: 270px; flex: 1 1 170px;
            border-top-width: 3px; font-size: 0.79rem;
        }
        .sysml-block.sysml-l2 .sysml-block-name { font-size: 0.82rem; font-weight: 740; }
        @media (max-width: 760px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .page-title { font-size: 1.35rem; }
            .compact-req-head { display: block; }
            .sysml-blocks-wrap { flex-direction: column; }
            .sysml-block, .sysml-block.sysml-l2 { max-width: 100%; min-width: unset; flex: 1 1 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
