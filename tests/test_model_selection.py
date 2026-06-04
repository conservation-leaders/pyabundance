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


def test_compatibility_warnings_for_different_k_and_shapes():
    X = np.ones((24, 1), dtype=np.float64)
    W = np.ones((24, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=202)
    fit_k40 = pcount(y, X, W, K=40)
    fit_k45 = pcount(y, X, W, K=45)

    table = aic_table({"k40": fit_k40, "k45": fit_k45})
    assert "warnings" in table.columns
    assert table["warnings"].str.contains("different K values").any()

    no_check = aic_table({"k40": fit_k40, "k45": fit_k45}, check_compatibility=False)
    assert not no_check["warnings"].str.contains("different K values").any()

    no_warnings_col = aic_table({"k40": fit_k40, "k45": fit_k45}, include_warnings=False)
    assert "warnings" not in no_warnings_col.columns

    fit_short = pcount(y[:-1], X[:-1], W[:-1], K=40)
    shape_table = compare_models({"full": fit_k40, "short": fit_short}).table
    assert shape_table["warnings"].str.contains("different response dimensions").any()


def test_no_compatibility_warning_for_same_data_different_mixtures():
    X = np.ones((24, 1), dtype=np.float64)
    W = np.ones((24, 3, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=303)
    poisson = pcount(y, X, W, K=40, mixture="poisson")
    nb = pcount(y, X, W, K=40, mixture="negative_binomial")

    table = aic_table({"poisson": poisson, "nb": nb})
    warnings = " ".join(table["warnings"].tolist())
    assert "different K values" not in warnings
    assert "different response dimensions" not in warnings
