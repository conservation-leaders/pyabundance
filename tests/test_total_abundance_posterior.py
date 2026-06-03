from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_total_abundance_posterior_summary_and_seed():
    X = np.ones((20, 1), dtype=np.float64)
    W = np.ones((20, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=210)
    fit = pcount(y, X, W, K=25)

    total1 = fit.total_abundance_posterior(nsim=50, seed=2)
    total2 = fit.total_abundance_posterior(nsim=50, seed=2)
    assert total1.samples.shape == (50,)
    assert np.array_equal(total1.samples, total2.samples)
    assert total1.lower <= total1.median <= total1.upper
    assert "TotalAbundancePosterior" in total1.summary()
