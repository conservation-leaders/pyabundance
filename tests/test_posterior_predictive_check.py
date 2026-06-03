from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_posterior_predictive_check_statistics():
    X = np.ones((22, 1), dtype=np.float64)
    W = np.ones((22, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=212)
    fit = pcount(y, X, W, K=25)

    for statistic in ["sse", "total_count", "zero_count", "max_count"]:
        out = fit.posterior_predictive_check(statistic=statistic, nsim=10, seed=4)
        assert {"observed", "simulated", "p_value", "statistic", "nsim"}.issubset(out)
        assert out["statistic"] == statistic
        assert out["simulated"].shape == (10,)
        assert 0.0 <= out["p_value"] <= 1.0
