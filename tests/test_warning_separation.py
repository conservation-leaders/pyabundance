from __future__ import annotations

import numpy as np
from pyabundance import load_example_pcount, pcount
from pyabundance.uncertainty import covariance_diagnostics


def _warnings_text(fit) -> tuple[str, str]:
    model = " ".join(fit.warnings or [])
    covariance = " ".join((fit.covariance_diagnostics or {}).get("warnings", []))
    return model, covariance


def test_auto_k_warning_is_model_only():
    data = load_example_pcount("poisson", n_sites=12)
    fit = pcount(data.y, data.X, data.W, K="auto", se=False)
    model_warnings, covariance_warnings = _warnings_text(fit)
    assert "Auto-selected K" in model_warnings
    assert "Auto-selected K" not in covariance_warnings


def test_zip_identifiability_warning_is_model_only():
    data = load_example_pcount("poisson", n_sites=12)
    fit = pcount(data.y, data.X, data.W, K="auto", mixture="zero_inflated_poisson", se=False)
    model_warnings, covariance_warnings = _warnings_text(fit)
    assert "ZIP identifiability" in model_warnings
    assert "ZIP identifiability" not in covariance_warnings


def test_se_false_cov_method_none_has_no_covariance_unavailable_warning():
    data = load_example_pcount("poisson", n_sites=12)
    fit = pcount(data.y, data.X, data.W, K="auto", se=False)
    covariance_warnings = " ".join((fit.covariance_diagnostics or {}).get("warnings", []))
    assert fit.cov_method == "none"
    assert "covariance is unavailable" not in covariance_warnings


def test_covariance_specific_warnings_remain_covariance_diagnostics():
    diagnostics = covariance_diagnostics(
        np.array([[1.0, 0.0], [0.0, -1.0]]),
        method="finite_difference",
        warnings=["hessian is not positive definite"],
    )
    warnings = " ".join(diagnostics["warnings"])
    assert "hessian is not positive definite" in warnings
    assert "covariance is not positive definite" in warnings
