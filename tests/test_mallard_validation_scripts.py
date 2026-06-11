from __future__ import annotations

import py_compile
from pathlib import Path


def test_python_mallard_validation_scripts_compile():
    for path in [
        Path("examples/validation/run_mallard_pyabundance.py"),
        Path("examples/validation/compare_mallard_results.py"),
    ]:
        py_compile.compile(str(path), doraise=True)


def test_mallard_validation_scripts_are_not_placeholders():
    expected_strings = {
        "examples/validation/export_mallard_from_unmarked.R": [
            "site_data_for_py.csv",
            "analysis_site_filter.csv",
            "complete.cases",
        ],
        "examples/validation/run_mallard_unmarked.R": [
            "unmarked::coef",
            "unmarked::SE",
            "unmarked::logLik",
            "stats::AIC",
            "unmarked::pcount",
            "r_poisson_meta.csv",
            "r_nb_coef.csv",
            "Fallback only for installed unmarked versions",
        ],
        "examples/validation/run_mallard_pyabundance.py": [
            "pcount_df",
            "compare_models",
            "py_model_comparison.csv",
        ],
        "examples/validation/compare_mallard_results.py": [
            "mallard_py_vs_r_summary.csv",
            "not universal performance claims",
            "black-box comparison target",
        ],
    }
    for path, strings in expected_strings.items():
        text = Path(path).read_text(encoding="utf-8")
        assert "Inspect the object above" not in text
        assert "print a message" not in text
        for expected in strings:
            assert expected in text, (path, expected)
