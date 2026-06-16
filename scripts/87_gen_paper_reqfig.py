#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate SysML requirement diagram (TikZ) and requirement table (LaTeX)
from rag_v4_results.json for inclusion in paper_els.tex.

Outputs:
  paper/figures/fig4_req_diagram.tex   -- TikZ standalone, compile separately
  paper/tables/table_req_case.tex      -- LaTeX tabular, \input into paper
"""
from __future__ import annotations
import json
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
DATA = Path("data/search_results/exp_v4/rag_v4_results.json")
FIG_DIR  = Path("../paper/figures")
TAB_DIR  = Path("../paper/tables")

# ── case study: OR001 in English translation ───────────────────────────────────
# Source: rag_v4_results.json RS[0], translated for English-language journal
CASE = {
    "src_id": "OR-001",
    "src_text": "Engine Cooling Water System — Temperature \& Valve Control",
    "ers": [
        {
            "id": "ER-1.1",
            "grade": "A",
            "topic": "HT Jacket Water Inlet Temperature",
            "shall": r"The propulsion engine cooling system \textbf{shall} maintain the engine jacket water inlet temperature within the limits specified by the engine manufacturer.",
            "shall_short": r"Maintain jacket water inlet temp within manufacturer limits.",
            "criterion": r"70--85\,\textdegree{}C",
            "condition": "All normal operating modes",
            "verification": "Test",
            "tier": "L1",
            "source": r"IACS UR M3.1 Cooling Systems",
            "kb_id": "E-PARAM-HT-001",
        },
        {
            "id": "ER-1.2",
            "grade": "A",
            "topic": "HT Circuit Max Inlet Temperature",
            "shall": r"In the HT freshwater circuit, under the most adverse ambient conditions, the engine inlet temperature \textbf{shall not} exceed 36\,\textdegree{}C above the thermostat opening temperature.",
            "shall_short": r"Engine inlet $\leq T_{\text{therm}}+36\,\text{\textdegree{}C}$.",
            "criterion": r"$\leq T_{\mathrm{therm}} + 36\,\text{\textdegree{}C}$",
            "condition": "Most adverse ambient conditions",
            "verification": "Analysis",
            "tier": "L1",
            "source": r"DNV Rules Pt4 Ch3 Machinery",
            "kb_id": "E-DNV-COOL-001",
        },
        {
            "id": "ER-1.3",
            "grade": "C",
            "topic": "Per-Engine Temperature Control Valve",
            "shall": r"Each main engine \textbf{shall} be equipped with a dedicated temperature control valve.",
            "shall_short": r"Dedicated TCV required per engine.",
            "criterion": r"\{\{TBD $|$ qty $|$ MAN 49/60 Project Guide\}\}",
            "condition": "Multiple engines sharing one cooling circuit",
            "verification": "Inspection",
            "tier": "L2",
            "source": r"MAN 49/60 Project Guide",
            "kb_id": "E-TCV-TEMP-013",
        },
        {
            "id": "ER-1.4",
            "grade": "C",
            "topic": "HT Three-Way Mixing Valve",
            "shall": r"The HT cooling water system \textbf{shall} be fitted with an electrically actuated three-way mixing valve with a linear characteristic curve.",
            "shall_short": r"Motorised 3-way mixing valve (linear) required.",
            "criterion": r"\{\{TBD $|$ qty $|$ Everllence 49/60DF Project Guide\}\}",
            "condition": "HT cooling water system",
            "verification": "Inspection",
            "tier": "L2",
            "source": r"Everllence 49/60DF Project Guide",
            "kb_id": "E-SYS-PRESS-020",
        },
    ],
}

GRADE_COLOR = {"A": "gradeA", "B": "gradeB", "C": "gradeC", "X": "gradeX"}


# ── TikZ requirement diagram ──────────────────────────────────────────────────

def gen_diagram() -> str:
    ers = CASE["ers"]
    n = len(ers)
    # layout: source req centered, ERs spread below
    er_sep  = 4.0   # horizontal separation between ER blocks
    er_y    = -5.4  # y position of ER row

    lines: list[str] = []
    lines.append(r"""\documentclass[tikz,border=4pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{shapes.multipart,arrows.meta,positioning,fit,backgrounds}
\usepackage{xcolor}
\usepackage{textcomp}

% Grade colour palette
\definecolor{gradeA}{RGB}{34,139,34}
\definecolor{gradeC}{RGB}{204,102,0}
\definecolor{gradeAbg}{RGB}{235,255,235}
\definecolor{gradeCbg}{RGB}{255,245,225}
\definecolor{srcbg}{RGB}{230,240,255}

\tikzset{
  reqblock/.style={
    rectangle split, rectangle split parts=2,
    draw, rounded corners=2pt,
    text width=#1,
    font=\small,
    align=left,
    inner sep=4pt,
  },
  reqblock/.default=3.8cm,
  srcblock/.style={reqblock=7.2cm, fill=srcbg, draw=blue!40!black, line width=0.8pt},
  gradeAbk/.style={reqblock, fill=gradeAbg, draw=gradeA, line width=0.8pt},
  gradeCbk/.style={reqblock, fill=gradeCbg, draw=gradeC, line width=0.8pt},
  derive/.style={-{Stealth[length=6pt]}, dashed, gray!70, thick},
  gradetag/.style={font=\scriptsize\bfseries, inner sep=2pt, rounded corners=2pt},
}

\begin{document}
\begin{tikzpicture}[node distance=1.2cm]

%% ── Source requirement ────────────────────────────────────────────────""")

    # source block
    lines.append(r"""
\node[srcblock] (src) {
  \textbf{\textit{\footnotesize «requirement»}}
  \nodepart{two}
  \textbf{OR-001}\quad Engine Cooling System — Thermal Control\\[2pt]
  \textit{\footnotesize id:} OR-001\quad
  \textit{\footnotesize text:} Maintain cooling water temperature and\\
  \phantom{\textit{\footnotesize text:} }control valves per regulatory requirements.
};
""")

    # ER blocks
    total_w = (n - 1) * er_sep
    for i, er in enumerate(ers):
        x = -total_w / 2 + i * er_sep
        style = "gradeAbk" if er["grade"] == "A" else "gradeCbk"
        color = "gradeA" if er["grade"] == "A" else "gradeC"
        node_name = f"er{i+1}"
        crit = er["criterion"]
        # escape for TikZ text
        lines.append(
            r"\node[" + style + r", below=2.6cm of src, xshift=" +
            f"{x:.1f}" + r"cm] (" + node_name + r") {"
        )
        lines.append(
            r"  \textbf{\textit{\footnotesize «requirement»}}"
        )
        lines.append(r"  \nodepart{two}")
        lines.append(
            r"  \textbf{" + er["id"] + r"}\quad {\footnotesize " +
            er["topic"] + r"}\\" + "\n" +
            r"  {\footnotesize\textit{id:} " + er["id"] + r"}\\" + "\n" +
            r"  {\scriptsize " + er["shall_short"] + r"}\\" + "\n" +
            r"  {\scriptsize\textit{crit:} " + crit + r"}\\" + "\n" +
            r"  {\scriptsize\textit{tier:} " + er["tier"] + r"\ ·\ " +
            er["source"] + r"}\\" + "\n" +
            r"  \colorbox{" + color + r"}{\textcolor{white}{\textbf{\tiny Grade " +
            er["grade"] + r"}}}"
        )
        lines.append(r"};")

    # derive arrows
    for i in range(n):
        lines.append(rf"\draw[derive] (src.south) -- (er{i+1}.north);")

    # legend
    lines.append(r"""
% ── Legend ────────────────────────────────────────────────────────────────────
\begin{scope}[shift={(6.0,-2.5)}]
  \node[fill=gradeAbg, draw=gradeA, rounded corners, font=\scriptsize, inner sep=4pt]
        (lgA) {\textcolor{gradeA}{\textbf{Grade A}} — cited value (L1/L2 evidence)};
  \node[fill=gradeCbg, draw=gradeC, rounded corners, font=\scriptsize, inner sep=4pt,
        below=0.3cm of lgA]
        {\textcolor{gradeC}{\textbf{Grade C}} — explicit \texttt{\{\{TBD\}\}} deferral};
  \node[above=0.15cm of lgA, font=\scriptsize\itshape] {Provenance Grade};
\end{scope}
""")

    lines.append(r"""\end{tikzpicture}
\end{document}
""")
    return "\n".join(lines)


# ── LaTeX requirement table ───────────────────────────────────────────────────

def gen_table() -> str:
    ers = CASE["ers"]
    lines: list[str] = []
    lines.append(r"""\begin{table}[htbp]
\caption{Case-study requirement set OR-001 (\textit{Engine Cooling System Thermal Control}):
four engineering requirements derived by the RAG pipeline, graded by provenance.
Grade~A: precise value with regulatory citation.
Grade~C: explicit \texttt{\{\{TBD\}\}} deferral — evidence retrieved but no precise value in KB.}
\label{tab:req_case}
{\small
\begin{tabularx}{\textwidth}{
  >{\centering\arraybackslash}p{1.0cm}
  >{\centering\arraybackslash}p{0.8cm}
  >{\raggedright\arraybackslash}X
  >{\centering\arraybackslash}p{2.2cm}
  >{\centering\arraybackslash}p{0.6cm}
  >{\raggedright\arraybackslash}p{3.2cm}}
\toprule
\textbf{ID} & \textbf{Grade} & \textbf{Shall Statement} &
\textbf{Measurable Criterion} & \textbf{Tier} & \textbf{Source} \\
\midrule""")

    for er in ers:
        gcolor = "gradeA" if er["grade"] == "A" else "gradeC"
        lines.append(
            er["id"] + r" & " +
            r"\textcolor{" + gcolor + r"}{\textbf{" + er["grade"] + r"}} & " +
            er["shall"] + r" & " +
            er["criterion"] + r" & " +
            er["tier"] + r" & " +
            er["source"] + r" \\"
        )
        lines.append(r"[2pt]")

    lines.append(r"""\bottomrule
\end{tabularx}
}
\end{table}""")
    return "\n".join(lines)


# ── write files ───────────────────────────────────────────────────────────────

def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TAB_DIR.mkdir(parents=True, exist_ok=True)

    fig_path = FIG_DIR / "fig4_req_diagram.tex"
    fig_path.write_text(gen_diagram(), encoding="utf-8")
    print(f"Wrote {fig_path}")

    tab_path = TAB_DIR / "table_req_case.tex"
    tab_path.write_text(gen_table(), encoding="utf-8")
    print(f"Wrote {tab_path}")


if __name__ == "__main__":
    main()
