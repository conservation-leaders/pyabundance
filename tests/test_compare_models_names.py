from __future__ import annotations

import pytest
from pyabundance import aic_table, compare_models, load_example_pcount, pcount


def _fits():
    data = load_example_pcount("poisson", n_sites=20)
    fit1 = pcount(data.y, data.X[:, :1], data.W, K="auto")
    fit2 = pcount(data.y, data.X, data.W, K="auto")
    return fit1, fit2


def test_compare_models_names_list_and_aic_table_names():
    fit1, fit2 = _fits()
    comparison = compare_models([fit1, fit2], names=["null", "covariates"])
    assert set(comparison.models) == {"null", "covariates"}
    assert set(comparison.table["model"]) == {"null", "covariates"}
    table = aic_table([fit1, fit2], names=["null", "covariates"])
    assert set(table["model"]) == {"null", "covariates"}


def test_compare_models_names_validation():
    fit1, fit2 = _fits()
    with pytest.raises(ValueError, match="same length"):
        compare_models([fit1, fit2], names=["one"])
    with pytest.raises(ValueError, match="unique"):
        compare_models([fit1, fit2], names=["x", "x"])
    with pytest.raises(ValueError, match="dict keys"):
        compare_models({"one": fit1}, names=["x"])
