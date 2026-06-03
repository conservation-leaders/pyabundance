import numpy as np
import pandas as pd
from pyabundance import build_pcount_matrices, pcount, pcount_df, simulate_pcount_zip


def test_pcount_df_zip_matches_matrix_api():
    rng = np.random.default_rng(301)
    n_sites = 110
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.ones((n_sites, 3, 1))
    y = simulate_pcount_zip(X, W, [0.4, 0.2], [-0.1], psi=0.2, seed=302)
    df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "x": x})
    matrices = build_pcount_matrices(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ 1",
    )
    start = np.array([0.0, 0.0, 0.0, np.log(0.2 / 0.8)])
    fit_df = pcount_df(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ 1",
        mixture="zero_inflated_poisson",
        K=80,
        start=start,
    )
    fit_matrix = pcount(
        matrices.y, matrices.X, matrices.W, K=80, mixture="zero_inflated_poisson", start=start
    )
    assert abs(fit_df.loglik - fit_matrix.loglik) < 1.0e-8
    np.testing.assert_allclose(fit_df.params, fit_matrix.params, atol=1.0e-6)
    assert fit_df.psi is not None and 0.0 < fit_df.psi < 1.0
    assert "psi:" in fit_df.summary()
