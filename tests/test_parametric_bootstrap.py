from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_parametric_bootstrap_reproducible_and_has_intervals():
    rng = np.random.default_rng(22)
    X = np.column_stack([np.ones(30), rng.normal(size=30)])
    W = np.ones((30, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.4], seed=23)
    fit = pcount(y, X, W, K=25)

    boot1 = fit.parametric_bootstrap(nsim=5, seed=123, statistic="sse")
    boot2 = fit.parametric_bootstrap(nsim=5, seed=123, statistic="sse")

    assert boot1.params.shape == (5, fit.params.size)
    assert boot1.success.shape == (5,)
    assert boot1.statistics is not None
    assert boot1.statistics.shape == (5,)
    assert boot1.confint().shape[0] == fit.params.size
    assert np.allclose(boot1.params, boot2.params, equal_nan=True)
    assert np.allclose(boot1.statistics, boot2.statistics, equal_nan=True)
