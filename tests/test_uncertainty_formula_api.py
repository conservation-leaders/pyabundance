from __future__ import annotations

import numpy as np
import pandas as pd
from pyabundance import pcount_df, simulate_pcount


def test_formula_api_preserves_names_with_uncertainty():
    rng = np.random.default_rng(28)
    n_sites = 50
    x = rng.normal(size=n_sites)
    X = np.column_stack([np.ones(n_sites), x])
    W = np.zeros((n_sites, 3, 3), dtype=np.float64)
    for visit in range(3):
        W[:, visit, visit] = 1.0
    y = simulate_pcount(X, W, beta=[0.2, 0.4], alpha=[-0.8, -0.2, 0.3], seed=29)
    df = pd.DataFrame({"y1": y[:, 0], "y2": y[:, 1], "y3": y[:, 2], "x": x})

    fit = pcount_df(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        detection_formula="~ visit - 1",
        K=45,
        se=True,
    )

    table = fit.coef_table()
    assert "x" in set(table["parameter"])
    assert any("visit" in name for name in table["parameter"])
    summary = fit.summary()
    assert "std.error" in summary
    assert "abundance formula: ~ x" in summary
    assert fit.predict_lambda(se=True, interval=True)["estimate"].shape == (n_sites,)
