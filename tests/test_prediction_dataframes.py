from __future__ import annotations

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_prediction_and_residual_dataframes_have_metadata():
    rng = np.random.default_rng(105)
    X = np.column_stack([np.ones(20), rng.normal(size=20)])
    W = np.ones((20, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.5], seed=106)
    y[0, 0] = np.nan
    site_ids = [f"s{i}" for i in range(20)]
    visits = ["a", "b", "c"]
    fit = pcount(y, X, W, K=25, se=True, site_ids=site_ids, visit_labels=visits)

    abundance = fit.abundance_dataframe(se=True, interval=True)
    assert list(abundance.columns) == ["site_id", "estimate", "se", "lower", "upper"]
    assert abundance.loc[0, "site_id"] == "s0"

    detection = fit.detection_dataframe(se=True, interval=True)
    assert {"site_id", "visit", "estimate", "se", "lower", "upper"}.issubset(detection.columns)
    assert detection.shape[0] == 60

    fitted = fit.fitted_counts_dataframe()
    assert {"observed", "fitted", "raw_residual", "pearson_residual", "missing"}.issubset(
        fitted.columns
    )
    assert bool(fitted.loc[0, "missing"])

    residuals = fit.residuals_dataframe(kind="raw")
    assert residuals.shape[0] == 60
