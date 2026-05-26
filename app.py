# -*- coding: utf-8 -*-
"""Single Streamlit entry point for the cooling-water RAG system."""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=r".*Accessing `__path__`.*")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from cooling_rag_mg.config import get_config
from ui.state import init_state
from ui.styles import inject_css
from ui.sidebar import render_nav_sidebar
from ui.pages.retrieval import render_retrieval_workspace
from ui.pages.results import render_retrieval_results_workspace
from ui.pages.engineering import render_engineering_workspace
from ui.pages.experiment import render_experiment_workspace
from ui.pages.metrics import render_metrics_workspace
from ui.pages.evidence_manager import render_evidence_manager


def main() -> None:
    st.set_page_config(
        page_title="多粒度需求证据检索",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    inject_css()
    cfg = get_config()
    render_nav_sidebar(cfg)

    active = st.session_state.get("active_workspace", "retrieval_workspace")
    if active == "retrieval_workspace":
        render_retrieval_workspace(cfg)
    elif active == "retrieval_results":
        render_retrieval_results_workspace()
    elif active == "engineering_workspace":
        render_engineering_workspace(cfg)
    elif active == "experiment_comparison":
        render_experiment_workspace(cfg)
    elif active == "metrics_analysis":
        render_metrics_workspace(cfg)
    elif active == "evidence_manager":
        render_evidence_manager()
    else:
        st.session_state.active_workspace = "retrieval_workspace"
        render_retrieval_workspace(cfg)


if __name__ == "__main__":
    import streamlit.runtime
    if streamlit.runtime.exists():
        main()
    else:
        import subprocess
        sys.exit(subprocess.run(
            [sys.executable, "-m", "streamlit", "run", __file__] + sys.argv[1:]
        ).returncode)
