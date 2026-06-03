from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_posterior_abundance_samples_are_reproducible_and_valid():
    rng = np.random.default_rng(208)
    X = np.column_stack([np.ones(30), rng.normal(size=30)])
    W = np.ones((30, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.4], seed=209)
    fit = pcount(y, X, W, K=30)

    samples1 = fit.posterior_abundance_samples(nsim=20, seed=1)
    samples2 = fit.posterior_abundance_samples(nsim=20, seed=1)
    assert samples1.shape == (20, 30)
    assert np.array_equal(samples1, samples2)
    assert np.issubdtype(samples1.dtype, np.integer)
    max_counts = np.nanmax(y, axis=1).astype(int)
    assert np.all(samples1 >= max_counts[None, :])
