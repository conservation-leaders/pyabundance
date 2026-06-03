import numpy as np
from pyabundance import pcount, simulate_pcount_zip


def test_zip_fit_on_synthetic_data():
    rng = np.random.default_rng(202607)
    n_sites = 260
    n_visits = 3
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    beta = np.array([0.45, 0.35])
    detection = np.array([-0.05])
    y = simulate_pcount_zip(X, W, beta, detection, psi=0.2, seed=202608)
    fit = pcount(
        y,
        X,
        W,
        K=90,
        mixture="zero_inflated_poisson",
        method="BFGS",
    )
    assert fit.success, fit.message
    assert np.isfinite(fit.loglik)
    assert fit.params.shape == (4,)
    assert fit.psi is not None and 0.0 < fit.psi < 1.0
    assert fit.logit_psi is not None
    assert fit.r is None
    assert abs(fit.aic - (2 * 4 - 2 * fit.loglik)) < 1.0e-12
    summary = fit.summary()
    assert "psi:" in summary
    assert "logit_psi" in summary
