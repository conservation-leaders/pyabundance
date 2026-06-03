from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount_negbin


def test_negbin_posterior_abundance_is_normalized():
    rng = np.random.default_rng(203)
    X = np.column_stack([np.ones(45), rng.normal(size=45)])
    W = np.ones((45, 3, 1), dtype=np.float64)
    y = simulate_pcount_negbin(X, W, beta=[0.2, 0.2], detection=[-0.4], r=1.4, seed=204)
    fit = pcount(y, X, W, K=45, mixture="negative_binomial")

    probs = fit.posterior_abundance()
    assert probs.shape == (45, 46)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-10)
    assert np.all(np.isfinite(probs))
    assert fit.r > 0.0
    assert "posterior_sd" in fit.posterior_abundance_summary().columns
