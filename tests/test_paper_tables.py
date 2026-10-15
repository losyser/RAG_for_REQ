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


def test_boundary_and_preaudit_macros():
    N = {
        "e3_boundary": {
            "eu_atomic": {"split_pct": 0.0},
            "fixed_windows": [
                {"window": 128, "overlap": 0.0, "split_pct": 76.0},
                {"window": 128, "overlap": 0.2, "split_pct": 72.0},
                {"window": 256, "overlap": 0.0, "split_pct": 28.0},
                {"window": 512, "overlap": 0.0, "split_pct": 16.0},
            ],
            "pct_used_units_longer_than_prompt_limit": 65.4,
            "pct_values_beyond_prompt_limit": 24.1,
        },
        "regrade_preaudit": {"rag_v4_results.json": {
            "old": {"A": 29, "B": 81, "C": 176},
            "new_with_v3kb": {"A": 1, "B": 28, "C": 176, "X": 81}}},
    }
    m = pt.build_macros(N)
    assert m["BoundaryEUSplit"] == 0.0
    assert m["BoundaryWSmall"] == 76.0 and m["BoundaryWMid"] == 28.0 and m["BoundaryWLarge"] == 16.0
    assert m["BoundaryUnitsOverPrompt"] == 65.4 and m["BoundaryValuesBeyondPrompt"] == 24.1
    assert m["BoundaryWSmallOvPct"] == 72.0
    assert m["PreAuditRagAOld"] == 29 and m["PreAuditRagCOld"] == 176
    bd_used = {"e3_boundary": {"n_used_units": 356,
                               "eu_atomic": {"split_pct": 0.0},
                               "fixed_windows": [{"window": 128, "overlap": 0.0, "split_pct": 76.0}]},
               "regrade_preaudit": {"rag_v4_results.json": {
                   "old": {"A": 29, "B": 81, "C": 176},
                   "new_with_v3kb": {"A": 1, "B": 28, "C": 176, "X": 81}}}}
    assert pt.build_macros(bd_used)["SensUsedUnits"] == 356


def test_correctness_macros():
    N = {
        "posthoc": {"rag_v3": {"total_shalls": 140, "pct_supported": 90.0, "pct_conflict": 0.7142},
                    "no_rag": {"total_shalls": 204, "pct_supported": 4.9, "pct_conflict": 1.47}},
        "hhard": {"rag_numeric_verbatim_from_cited_unit": 9, "rag_qualitative_contradictions": 7},
        "credibility": {"blind_quality": {"aggregate": {"overall": {"R": 64, "B0": 51, "tie": 125}}},
                        "h_hard": {"wilcoxon": {"rag_mean": 0.014602860958554408,
                                                "norag_mean": 0.0009523809523809524,
                                                "p_value": 0.026157182329284684, "n_pairs": 60}}},
    }
    m = pt.build_macros(N)
    assert m["RagNumericShalls"] == 140 and m["NoRagNumericShalls"] == 204
    assert m["PosthocRagConflictPct"] == 0.7
    assert m["HhRagVerbatim"] == 9 and m["HhRagQualitative"] == 7
    assert m["BlindOverallR"] == 64 and m["BlindOverallN"] == 240
    assert round(m["HhRagPct"], 1) == 1.5 and round(m["HhNoRagPct"], 1) == 0.1


def test_stage1_pool_macro():
    m = pt.build_macros({"e1_pool_n": 570})
    assert m["StageOnePool"] == 570
    assert pt.build_macros({})["StageOnePool"] is None


def test_sensitivity_macros():
    """E3 retrieval/e2e robustness numbers exposed as macros for the main text."""
    N = {"e3_sensitivity": {
        "retrieval": {
            "default": {"jaccard_vs_default_mean": 1.0},
            "w_bm25_0.25": {"jaccard_vs_default_mean": 0.971},
            "w_bm25_0.75": {"jaccard_vs_default_mean": 0.947},
            "k0_10": {"jaccard_vs_default_mean": 1.0},
            "k0_100": {"jaccard_vs_default_mean": 1.0},
            "k_4": {"jaccard_vs_default_mean": 0.64},
            "embed_mpnet": {"jaccard_vs_default_mean": 0.788}},
        "e2e": {
            "default": {"grade_X_pct": 0.0, "grade_AB_pct": 14.4, "n_shalls": 513},
            "vector_only": {"grade_X_pct": 0.0, "grade_AB_pct": 12.3, "n_shalls": 487},
            "bm25_only": {"grade_X_pct": 0.0, "grade_AB_pct": 10.9, "n_shalls": 477},
            "embed_mpnet": {"grade_X_pct": 0.0, "grade_AB_pct": 12.9, "n_shalls": 497},
            "trunc_1200": {"grade_X_pct": 0.0, "grade_AB_pct": 15.7, "n_shalls": 108}}}}
    m = pt.build_macros(N)
    assert (m["SensJWeightLow"], m["SensJWeightHigh"]) == (0.947, 0.971)
    assert m["SensJKzero"] == 1.0
    assert m["SensJKfour"] == 0.64
    assert m["SensJMpnet"] == 0.788
    assert (m["SensABLowPct"], m["SensABHighPct"]) == (10.9, 15.7)
    assert m["SensGradeXMaxPct"] == 0.0
    assert m["SensTruncShalls"] == 108
    assert pt.build_macros({})["SensTruncShalls"] is None


def test_descriptive_table_counts_come_from_registry():
    """The source-requirement count must be read from the registry, not hardcoded."""
    N = {"rag": dict(ARM, n_sets=57), "norag": dict(ARM, n_sets=57)}
    tex = pt.table_descriptive(N)
    assert "57" in tex
    assert "60 source requirements" not in tex


def test_appendix_sensitivity_labels_have_no_stray_brace():
    """\\label sits outside \\caption here, so it must close with a single brace."""
    N = {"e3_sensitivity": {
        "retrieval": {"default": {"units_per_req_mean": 1, "l1_share_pct": 2,
                                  "numeric_unit_share_pct": 3, "jaccard_vs_default_mean": 1}},
        "e2e": {"default": {"n_shalls": 10, "grade_X_pct": 0,
                            "grade_AB_pct": 1, "citation_rate_pct": 99}}}}
    tex = pt.appendix_sensitivity(N)
    assert r"\label{tab:app_retrieval}}" not in tex
    assert r"\label{tab:app_e2e}}" not in tex
    assert r"\label{tab:app_retrieval}" in tex
    assert r"\label{tab:app_e2e}" in tex


BANNED = ("eliminate", "guarantee", "more correct", "proves that")


def test_tables_avoid_banned_wording():
    """The manuscript must not claim the constraint removes errors entirely."""
    N = {"rag": ARM, "norag": ARM, "random": ARM}
    for name in sorted(dir(pt)):
        if name.startswith("table_"):
            tex = getattr(pt, name)(N).lower()
            for word in BANNED:
                assert word not in tex, f"{name} contains banned wording: {word}"
