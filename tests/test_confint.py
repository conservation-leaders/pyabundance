from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip


def test_confint_contains_estimates_for_poisson():
    rng = np.random.default_rng(14)
    X = np.column_stack([np.ones(45), rng.normal(size=45)])
    W = np.ones((45, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.3], seed=15)
    fit = pcount(y, X, W, K=35, se=True)

    ci = fit.confint()
    assert set(["parameter", "estimate", "lower", "upper"]).issubset(ci.columns)
    finite = np.isfinite(ci[["estimate", "lower", "upper"]].to_numpy()).all(axis=1)
    assert np.all(ci.loc[finite, "lower"] <= ci.loc[finite, "estimate"])
    assert np.all(ci.loc[finite, "estimate"] <= ci.loc[finite, "upper"])


def test_transformed_params_for_negbin_and_zip():
    rng = np.random.default_rng(16)
    X = np.column_stack([np.ones(60), rng.normal(size=60)])
    W = np.ones((60, 3, 1), dtype=np.float64)

    y_nb = simulate_pcount_negbin(X, W, beta=[0.2, 0.1], detection=[-0.4], r=1.8, seed=17)
    nb = pcount(y_nb, X, W, K=50, mixture="negative_binomial", se=True)
    nb_trans = nb.transformed_params()
    assert "r" in set(nb_trans["parameter"])
    assert float(nb_trans.loc[nb_trans["parameter"] == "r", "estimate"].iloc[0]) > 0

    y_zip = simulate_pcount_zip(X, W, beta=[0.2, 0.1], detection=[-0.4], psi=0.2, seed=18)
    zip_fit = pcount(y_zip, X, W, K=50, mixture="zero_inflated_poisson", se=True)
    zip_trans = zip_fit.transformed_params()
    psi = float(zip_trans.loc[zip_trans["parameter"] == "psi", "estimate"].iloc[0])
    assert 0.0 < psi < 1.0
