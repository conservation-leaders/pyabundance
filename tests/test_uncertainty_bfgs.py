from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_bfgs_uncertainty_outputs_have_expected_shapes():
    rng = np.random.default_rng(10)
    X = np.column_stack([np.ones(50), rng.normal(size=50)])
    W = np.ones((50, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.3], alpha=[-0.4], seed=11)

    fit = pcount(y, X, W, K=35, se=True, cov_method="bfgs")

    assert fit.covariance is not None
    assert fit.covariance.shape == (3, 3)
    assert fit.standard_errors is not None
    assert fit.standard_errors.shape == (3,)
    table = fit.coef_table()
    assert set(["parameter", "estimate", "std.error", "lower", "upper"]).issubset(table.columns)
    assert fit.param_names == ["abundance[0]", "abundance[1]", "detection[0]"]
    assert isinstance(fit.covariance_diagnostics["warnings"], list)
