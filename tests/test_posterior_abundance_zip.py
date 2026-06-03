from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount_zip


def test_zip_posterior_zero_mass_for_zero_and_positive_sites():
    rng = np.random.default_rng(205)
    X = np.column_stack([np.ones(60), rng.normal(size=60)])
    W = np.ones((60, 3, 1), dtype=np.float64)
    y = simulate_pcount_zip(X, W, beta=[0.2, 0.1], detection=[-0.3], psi=0.35, seed=206)
    y[0, :] = 0.0
    fit = pcount(y, X, W, K=45, mixture="zero_inflated_poisson")

    probs = fit.posterior_abundance()
    assert np.allclose(probs.sum(axis=1), 1.0, atol=1e-10)
    assert probs[0, 0] > 0.0
    positive_sites = np.where(np.nanmax(y, axis=1) > 0)[0]
    assert positive_sites.size > 0
    assert np.allclose(probs[positive_sites, 0], 0.0, atol=1e-14)
    assert 0.0 < fit.psi < 1.0
