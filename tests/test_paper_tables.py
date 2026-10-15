import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("pt", Path("scripts/108_paper_tables.py"))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

ARM = {"n_shalls": 10, "grade_A": 1, "grade_B": 2, "grade_C": 7, "grade_X": 0, "grade_A_pct": 10.0,
       "grade_B_pct": 20.0, "grade_C_pct": 70.0, "grade_X_pct": 0.0, "grade_AB_pct": 30.0,
       "grade_X_ci": [0.0, 27.8], "citation_rate_pct": 100.0, "l1_citation_rate_pct": 10.0, "multi_source_pct": 0.0}


def test_macros_with_missing_sections_do_not_crash():
    m = pt.build_macros({"rag": ARM})
    assert m["RagNShalls"] == 10 and m["RagGradeXPct"] == 0.0
    assert m["KappaPair"] is None and m["HhP"] is None


def test_macro_names_are_unique_and_latex_safe():
    m = pt.build_macros({"rag": ARM, "norag": ARM, "random": ARM})
    assert all(k.isalpha() for k in m)


def test_grade_table_contains_formatted_counts():
    tex = pt.table_grade({"rag": ARM, "norag": ARM})
    assert r"10.0\% (1)" in tex and r"\label{tab:grade}" in tex
