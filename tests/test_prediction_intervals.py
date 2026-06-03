from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_prediction_confidence_and_simulation_intervals():
    rng = np.random.default_rng(19)
    X = np.column_stack([np.ones(50), rng.normal(size=50)])
    W = np.ones((50, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.3], alpha=[-0.3], seed=20)
    fit = pcount(y, X, W, K=35, se=True)

    lam = fit.predict_lambda(se=True, interval=True)
    assert lam["estimate"].shape == (50,)
    assert np.all(lam["lower"] <= lam["estimate"])
    assert np.all(lam["estimate"] <= lam["upper"])

    det = fit.predict_detection(se=True, interval=True)
    assert det["estimate"].shape == (50, 3)
    assert np.all(det["lower"] <= det["estimate"])
    assert np.all(det["estimate"] <= det["upper"])

    pred = fit.prediction_interval(kind="observed_counts", nsim=10, seed=21)
    assert pred["lower"].shape == y.shape
    assert pred["median"].shape == y.shape
    assert pred["upper"].shape == y.shape
