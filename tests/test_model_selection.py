from __future__ import annotations

import numpy as np
from pyabundance import aic_table, compare_models, pcount, simulate_pcount


def test_aic_table_and_compare_models_rank_models():
    rng = np.random.default_rng(101)
    X1 = np.ones((45, 1), dtype=np.float64)
    x = rng.normal(size=45)
    X2 = np.column_stack([np.ones(45), x])
    W = np.ones((45, 3, 1), dtype=np.float64)
    y = simulate_pcount(X2, W, beta=[0.2, 0.4], alpha=[-0.3], seed=102)

    null = pcount(y, X1, W, K=40)
    covariate = pcount(y, X2, W, K=40)

    table = aic_table({"null": null, "covariate": covariate})
    assert list(table["rank"]) == [1, 2]
    assert set(["model", "AIC", "delta_AIC", "AIC_weight"]).issubset(table.columns)
    assert np.isclose(table["AIC_weight"].sum(), 1.0)

    comparison = compare_models({"null": null, "covariate": covariate})
    assert comparison.best_model_name in {"null", "covariate"}
    assert "AIC_weight" in comparison.summary()
