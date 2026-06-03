from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_posterior_predictive_counts_shape_and_values():
    X = np.ones((18, 1), dtype=np.float64)
    W = np.ones((18, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=211)
    y[0, 0] = np.nan
    fit = pcount(y, X, W, K=25)

    sims = fit.posterior_predictive_counts(nsim=8, seed=3)
    assert sims.shape == (8, 18, 3)
    assert np.all(sims >= 0.0)
    assert np.all(np.abs(sims - np.round(sims)) < 1e-12)
