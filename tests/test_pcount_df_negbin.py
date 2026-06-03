import numpy as np
import pandas as pd
from pyabundance import build_pcount_matrices, pcount, pcount_df, simulate_pcount_negbin


def test_pcount_df_negbin_matches_matrix_api():
    rng = np.random.default_rng(201)
    n_sites = 100
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, 3, 1))
    y = simulate_pcount_negbin(X, W, [0.3, 0.25], [-0.2], r=1.8, seed=202)
    df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "x": x})
    matrices = build_pcount_matrices(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ 1",
    )
    start = np.zeros(4)
    fit_df = pcount_df(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ 1",
        mixture="negative_binomial",
        K=80,
        start=start,
    )
    fit_matrix = pcount(
        matrices.y, matrices.X, matrices.W, K=80, mixture="negative_binomial", start=start
    )
    assert abs(fit_df.loglik - fit_matrix.loglik) < 1.0e-8
    np.testing.assert_allclose(fit_df.params, fit_matrix.params, atol=1.0e-6)
    assert fit_df.r is not None and fit_df.r > 0
    assert "r:" in fit_df.summary()
