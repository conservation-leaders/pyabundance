from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_poisson_posterior_abundance_matrix_and_summary():
    rng = np.random.default_rng(201)
    X = np.column_stack([np.ones(35), rng.normal(size=35)])
    W = np.ones((35, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2, 0.3], alpha=[-0.4], seed=202)
    fit = pcount(y, X, W, K=35)

    probs = fit.posterior_abundance()
    assert probs.shape == (35, 36)
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-10)
    max_counts = np.nanmax(y, axis=1).astype(int)
    means = probs @ np.arange(36)
    assert np.all(means >= max_counts - 1e-10)
    for i, max_y in enumerate(max_counts):
        assert np.all(probs[i, :max_y] == 0.0)

    summary = fit.posterior_abundance_summary()
    expected = {"posterior_mean", "posterior_mode", "posterior_median", "lower", "upper"}
    assert expected.issubset(summary.columns)
