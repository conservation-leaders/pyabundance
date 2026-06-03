from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip


def _design(seed: int = 24):
    rng = np.random.default_rng(seed)
    X = np.column_stack([np.ones(35), rng.normal(size=35)])
    W = np.ones((35, 3, 1), dtype=np.float64)
    return X, W


def _check_fit(fit):
    diag = fit.diagnostics()
    for key in ["success", "message", "nfev", "loglik", "aic", "mixture", "residual_sse"]:
        assert key in diag
    assert fit.fitted_counts().shape == fit.y.shape
    assert fit.residuals().shape == fit.y.shape
    assert np.isfinite(fit.sse())


def test_diagnostics_for_all_mixtures_and_missing_residuals():
    X, W = _design()
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.3], seed=25)
    y[0, 0] = np.nan
    poisson = pcount(y, X, W, K=30, se=True)
    assert np.isnan(poisson.residuals()[0, 0])
    _check_fit(poisson)

    y_nb = simulate_pcount_negbin(X, W, beta=[0.1, 0.2], detection=[-0.3], r=1.5, seed=26)
    _check_fit(pcount(y_nb, X, W, K=40, mixture="negative_binomial"))

    y_zip = simulate_pcount_zip(X, W, beta=[0.1, 0.2], detection=[-0.3], psi=0.2, seed=27)
    _check_fit(pcount(y_zip, X, W, K=40, mixture="zero_inflated_poisson"))
