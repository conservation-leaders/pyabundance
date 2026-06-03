import numpy as np
from pyabundance import pcount, simulate_pcount


def test_pcount_fit_converges_on_synthetic_data():
    rng = np.random.default_rng(42)
    n_sites = 120
    n_visits = 3
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    beta = np.array([0.2, 0.4])
    alpha = np.array([-0.2])
    y = simulate_pcount(X, W, beta, alpha, seed=123)
    fit = pcount(y, X, W, K=40, start=np.zeros(3), method="BFGS")
    assert fit.success, fit.message
    assert np.isfinite(fit.loglik)
    assert fit.params.shape == (3,)
