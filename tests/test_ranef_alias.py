from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_ranef_alias_matches_summary_and_level_changes_interval():
    X = np.ones((25, 1), dtype=np.float64)
    W = np.ones((25, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=207)
    fit = pcount(y, X, W, K=25)

    ranef = fit.ranef(level=0.8)
    summary = fit.posterior_abundance_summary(level=0.8)
    assert ranef.equals(summary)
    wide = fit.posterior_abundance_summary(level=0.95)
    assert np.all(wide["upper"] >= ranef["upper"])
