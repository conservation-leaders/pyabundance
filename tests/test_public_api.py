from __future__ import annotations

import pyabundance


def test_expected_public_names_importable():
    expected = {
        "pcount",
        "pcount_df",
        "build_pcount_matrices",
        "PCountResult",
        "PCountAnalysis",
        "KSuggestion",
        "parametric_bootstrap",
        "aic_table",
        "compare_models",
        "analyze_pcount",
        "suggest_K",
        "load_example_pcount",
        "list_example_datasets",
        "model_report",
        "report_markdown",
    }
    assert expected.issubset(set(pyabundance.__all__))
    for name in expected:
        assert getattr(pyabundance, name) is not None


def test_core_not_exported_by_star_contract():
    assert "_core" not in pyabundance.__all__


def test_version_is_1_0_0rc2():
    assert pyabundance.__version__ == "1.0.0rc2"


def test_major_public_docstrings_exist():
    for name in [
        "pcount",
        "pcount_df",
        "build_pcount_matrices",
        "aic_table",
        "compare_models",
        "analyze_pcount",
        "suggest_K",
        "load_example_pcount",
    ]:
        obj = getattr(pyabundance, name)
        assert obj.__doc__, name
