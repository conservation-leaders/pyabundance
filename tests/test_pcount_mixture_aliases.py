import numpy as np
import pytest
from pyabundance import pcount, simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip


def designs(seed: int = 7):
    rng = np.random.default_rng(seed)
    n_sites = 80
    n_visits = 3
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    return X, W


def test_poisson_aliases_work():
    X, W = designs()
    y = simulate_pcount(X, W, np.array([0.1, 0.2]), np.array([-0.3]), seed=8)
    for mixture in ["poisson", "P"]:
        fit = pcount(y, X, W, K=40, mixture=mixture, method="BFGS")
        assert fit.mixture == "poisson"
        assert fit.params.shape == (3,)
        assert fit.r is None


def test_negbin_aliases_work():
    X, W = designs(9)
    y = simulate_pcount_negbin(X, W, np.array([0.2, 0.25]), np.array([-0.2]), 1.5, seed=10)
    for mixture in ["negative_binomial", "negbin", "NB"]:
        fit = pcount(y, X, W, K=60, mixture=mixture, method="BFGS")
        assert fit.mixture == "negative_binomial"
        assert fit.params.shape == (4,)
        assert fit.r is not None and fit.r > 0.0


def test_zip_aliases_work():
    X, W = designs(12)
    y = simulate_pcount_zip(X, W, np.array([0.25, 0.2]), np.array([-0.15]), 0.2, seed=13)
    for mixture in ["zero_inflated_poisson", "zip", "ZIP"]:
        fit = pcount(y, X, W, K=60, mixture=mixture, method="BFGS")
        assert fit.mixture == "zero_inflated_poisson"
        assert fit.params.shape == (4,)
        assert fit.psi is not None and 0.0 < fit.psi < 1.0


def test_unknown_mixture_raises_value_error():
    X, W = designs(11)
    y = np.zeros((X.shape[0], W.shape[1]), dtype=np.float64)
    with pytest.raises(ValueError, match="unknown mixture"):
        pcount(y, X, W, mixture="unknown")
