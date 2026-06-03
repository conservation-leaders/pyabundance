import numpy as np
import pandas as pd
from pyabundance import build_pcount_matrices, pcount, pcount_df, simulate_pcount


def test_pcount_df_poisson_matches_matrix_api():
    rng = np.random.default_rng(101)
    n_sites = 90
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.zeros((n_sites, 3, 3))
    for visit in range(3):
        W[:, visit, visit] = 1.0
    y = simulate_pcount(X, W, [0.2, 0.4], [-0.7, -0.1, 0.3], seed=102)
    df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "x": x})
    matrices = build_pcount_matrices(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ visit - 1",
    )
    start = np.zeros(5)
    fit_df = pcount_df(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ visit - 1",
        K=50,
        start=start,
    )
    fit_matrix = pcount(matrices.y, matrices.X, matrices.W, K=50, start=start)
    assert abs(fit_df.loglik - fit_matrix.loglik) < 1.0e-8
    np.testing.assert_allclose(fit_df.params, fit_matrix.params, atol=1.0e-6)
    assert fit_df.abundance_column_names == ["Intercept", "x"]
    assert "visit[y1]" in fit_df.summary()
