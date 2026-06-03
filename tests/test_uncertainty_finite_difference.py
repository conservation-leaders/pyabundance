from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_finite_difference_uncertainty_is_symmetric_or_diagnosed():
    rng = np.random.default_rng(12)
    X = np.column_stack([np.ones(25), rng.normal(size=25)])
    W = np.ones((25, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.5], seed=13)

    fit = pcount(y, X, W, K=25, se=True, cov_method="finite_difference")

    assert fit.covariance is None or fit.covariance.shape == (3, 3)
    if fit.covariance is not None:
        assert np.allclose(fit.covariance, fit.covariance.T, atol=1e-8)
    assert fit.standard_errors is not None
    assert fit.standard_errors.shape == (3,)
    assert np.all(np.isfinite(fit.standard_errors)) or fit.covariance_diagnostics["warnings"]
