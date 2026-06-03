import numpy as np
from pyabundance import pcount, simulate_pcount_negbin


def test_negbin_fit_on_synthetic_data():
    rng = np.random.default_rng(202604)
    n_sites = 250
    n_visits = 3
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    beta = np.array([0.3, 0.35])
    detection = np.array([-0.25])
    y = simulate_pcount_negbin(X, W, beta, detection, r=2.0, seed=202605)
    fit = pcount(
        y,
        X,
        W,
        K=90,
        mixture="negative_binomial",
        start=np.array([0.0, 0.0, 0.0, 0.0]),
        method="BFGS",
    )
    assert fit.success, fit.message
    assert np.isfinite(fit.loglik)
    assert fit.params.shape == (4,)
    assert fit.r is not None and fit.r > 0.0
    assert fit.log_r is not None
    assert abs(fit.aic - (2 * 4 - 2 * fit.loglik)) < 1.0e-12
    assert "r:" in fit.summary()
