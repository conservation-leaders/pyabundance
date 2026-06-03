import numpy as np
import pandas as pd
from pyabundance import pcount_df, simulate_pcount


def test_result_summary_contains_formulas_and_named_coefficients():
    rng = np.random.default_rng(401)
    n_sites = 80
    forest = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), forest])
    W = np.zeros((n_sites, 3, 3))
    for visit in range(3):
        W[:, visit, visit] = 1.0
    y = simulate_pcount(X, W, [0.1, 0.3], [-0.5, -0.1, 0.2], seed=402)
    df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "forest": forest})
    fit = pcount_df(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K=50,
        start=np.zeros(5),
    )
    summary = fit.summary()
    assert "abundance formula: ~ forest" in summary
    assert "detection formula: ~ visit - 1" in summary
    assert "forest" in summary
    assert "visit[y1]" in summary
    assert "poisson" in summary
    assert "K: 50" in summary
    assert "AIC" in summary
    assert "logLik" in summary
    assert repr(fit).startswith("PCountResult")
