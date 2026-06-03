import numpy as np
from pyabundance import pcount, simulate_pcount


def test_simulation_recovery_broad_tolerance():
    rng = np.random.default_rng(2026)
    n_sites = 350
    n_visits = 4
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    true_params = np.array([0.5, 0.35, -0.3])
    y = simulate_pcount(X, W, true_params[:2], true_params[2:], seed=2027)
    fit = pcount(y, X, W, K=70, start=np.zeros(3), method="BFGS")
    assert fit.success, fit.message
    assert np.all(np.abs(fit.params - true_params) < 0.65)
