# -*- coding: utf-8 -*-
"""Evidence database management page."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

from ui.components.shared import render_workspace_header

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _run_script(script_path: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PROJECT_ROOT),
    )
    return result.returncode, result.stdout, result.stderr


def render_evidence_manager() -> None:
    render_workspace_header(
        "证据库管理",
        "查看证据库状态、运行去重和补充脚本、重建索引。所有操作都在服务器端执行，请谨慎操作。",
        "Evidence DB",
    )

    eu_path = PROJECT_ROOT / "data" / "processed" / "evidence_units.jsonl"
    sc_path = PROJECT_ROOT / "data" / "processed" / "source_chunks.jsonl"
    eg_path = PROJECT_ROOT / "data" / "processed" / "evidence_groups.jsonl"

    # ── Status cards ──
    st.markdown("### 当前证据库状态")
    cols = st.columns(3)
    with cols[0]:
        n_eu = _count_jsonl(eu_path)
        st.markdown(
            f'<div class="summary-card">'
            f'<div class="summary-label">证据单元 (evidence_units)</div>'
            f'<div class="summary-value">{n_eu}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cols[1]:
        n_sc = _count_jsonl(sc_path)
        st.markdown(
            f'<div class="summary-card">'
            f'<div class="summary-label">来源块 (source_chunks)</div>'
            f'<div class="summary-value">{n_sc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        n_eg = _count_jsonl(eg_path)
        st.markdown(
            f'<div class="summary-card">'
            f'<div class="summary-label">证据组 (evidence_groups)</div>'
            f'<div class="summary-value">{n_eg}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── can_support coverage ──
    st.markdown("### 需求方面覆盖统计")
    if eu_path.exists():
        from collections import Counter
        aspect_counter: Counter = Counter()
        with open(eu_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    for a in obj.get("metadata", {}).get("can_support") or []:
                        aspect_counter[a] += 1
                except Exception:
                    pass
        if aspect_counter:
            import pandas as pd
            df = pd.DataFrame(
                sorted(aspect_counter.items(), key=lambda x: -x[1]),
                columns=["需求方面 (can_support)", "证据数"],
            )
            st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.warning("evidence_units.jsonl 不存在。")

    st.markdown("---")

    # ── Maintenance scripts ──
    st.markdown("### 维护操作")
    st.markdown(
        '<div class="section-caption">以下操作会修改数据文件，运行前请确认已备份。'
        '每次操作完成后刷新本页查看最新状态。</div>',
        unsafe_allow_html=True,
    )

    scripts = {
        "重建所有索引 (script 11)": PROJECT_ROOT / "scripts" / "11_build_multigranular_indexes.py",
        "修复孤立 parent_chunk_id (script 33)": PROJECT_ROOT / "scripts" / "33_add_source_chunks_for_new_units.py",
        "重新生成 evidence.docx (script 35)": PROJECT_ROOT / "scripts" / "35_export_full_evidence_docx.py",
    }

    for label, script_path in scripts.items():
        col_btn, col_status = st.columns([1, 3])
        with col_btn:
            if st.button(label, key=f"run_{script_path.stem}", use_container_width=True):
                with st.spinner(f"运行 {script_path.name}…"):
                    rc, stdout, stderr = _run_script(script_path)
                if rc == 0:
                    st.success(f"成功完成 {script_path.name}")
                else:
                    st.error(f"{script_path.name} 失败（退出码 {rc}）")
                if stdout:
                    with st.expander("标准输出", expanded=rc != 0):
                        st.code(stdout, language="text")
                if stderr:
                    with st.expander("错误输出", expanded=True):
                        st.code(stderr, language="text")

    st.markdown("---")
    st.markdown("### 原始数据文件路径")
    paths = {
        "evidence_units.jsonl": eu_path,
        "source_chunks.jsonl": sc_path,
        "evidence_groups.jsonl": eg_path,
        "evidence.docx": PROJECT_ROOT / "data" / "raw" / "evidence.docx",
        "索引目录": PROJECT_ROOT / "data" / "indexes",
    }
    for name, p in paths.items():
        exists = p.exists() if hasattr(p, "exists") else False
        icon = "✅" if exists else "❌"
        st.markdown(f"**{name}** {icon}  \n`{p}`")
