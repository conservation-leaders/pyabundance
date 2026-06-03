from __future__ import annotations

import pyabundance
from pyabundance import PCountResult


def test_rc1_expected_public_names_importable():
    expected = {
        "pcount",
        "pcount_df",
        "build_pcount_matrices",
        "PCountResult",
        "parametric_bootstrap",
        "aic_table",
        "compare_models",
        "load_example_pcount",
        "list_example_datasets",
        "model_report",
        "report_markdown",
        "export_model_report",
        "simulate_pcount",
        "simulate_pcount_negbin",
        "simulate_pcount_zip",
    }
    assert expected.issubset(set(pyabundance.__all__))
    for name in expected:
        assert getattr(pyabundance, name) is not None


def test_core_not_exported_by_star_contract():
    namespace: dict[str, object] = {}
    exec("from pyabundance import *", namespace)
    assert "_core" not in namespace
    assert "_core" not in pyabundance.__all__


def test_rc1_version():
    assert pyabundance.__version__ == "1.0.0rc1"


def test_major_public_functions_have_docstrings():
    for name in [
        "pcount",
        "pcount_df",
        "build_pcount_matrices",
        "aic_table",
        "compare_models",
        "load_example_pcount",
        "model_report",
    ]:
        assert getattr(pyabundance, name).__doc__, name


def test_important_result_methods_exist():
    expected_methods = [
        "summary",
        "coef_table",
        "confint",
        "transformed_params",
        "predict_lambda",
        "predict_detection",
        "fitted_counts",
        "residuals",
        "sse",
        "parametric_bootstrap",
        "prediction_interval",
        "diagnostics",
        "posterior_abundance",
        "ranef",
        "posterior_abundance_dataframe",
        "posterior_abundance_samples",
        "posterior_abundance_summary",
        "total_abundance_posterior",
        "posterior_predictive_counts",
        "posterior_predictive_check",
        "to_report",
        "to_markdown",
    ]
    for method in expected_methods:
        assert hasattr(PCountResult, method), method
