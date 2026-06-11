from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pyabundance
import pytest
from pyabundance import aic_table, compare_models, pcount
from pyabundance.core import FitList, predict


@dataclass(frozen=True)
class DummyFit:
    label: str
    loglik: float
    n_params: int = 1
    mixture: str = "poisson"
    K: int = 12
    success: bool = True
    nfev: int | None = 3
    nit: int | None = 2
    abundance_formula: str | None = "~ 1"
    detection_formula: str | None = "~ 1"
    warnings: list[str] | None = None

    @property
    def params(self) -> np.ndarray:
        return np.zeros(self.n_params, dtype=np.float64)

    @property
    def aic(self) -> float:
        return 2.0 * self.n_params - 2.0 * self.loglik

    @property
    def y(self) -> np.ndarray:
        return np.ones((2, 3), dtype=np.float64)

    @property
    def X(self) -> np.ndarray:
        return np.ones((2, 1), dtype=np.float64)

    @property
    def W(self) -> np.ndarray:
        return np.ones((2, 3, 1), dtype=np.float64)

    @property
    def site_ids(self) -> list[str]:
        return ["s1", "s2"]

    @property
    def visit_labels(self) -> list[str]:
        return ["v1", "v2", "v3"]


def _dummy_fits() -> tuple[DummyFit, DummyFit]:
    return DummyFit("worse", loglik=-8.0), DummyFit("better", loglik=-5.0)


def _pcount_fit():
    y = np.asarray(
        [
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 2.0],
            [0.0, 0.0, 1.0],
            [2.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ],
        dtype=np.float64,
    )
    n_sites, n_visits = y.shape
    X = np.ones((n_sites, 1), dtype=np.float64)
    W = np.ones((n_sites, n_visits, 1), dtype=np.float64)
    return pcount(y, X, W, K=12, method="BFGS")


def test_fitlist_constructs_from_dict_and_preserves_order():
    worse, better = _dummy_fits()

    fits = FitList({"worse": worse, "better": better})

    assert fits.names == ("worse", "better")
    assert fits.models["worse"] is worse
    assert fits.models["better"] is better
    assert len(fits) == 2
    assert list(fits) == ["worse", "better"]
    assert fits["worse"] is worse
    assert list(fits.keys()) == ["worse", "better"]
    assert list(fits.values()) == [worse, better]
    assert list(fits.items()) == [("worse", worse), ("better", better)]


def test_fitlist_constructs_from_iterable_plus_names_and_normalizes_names():
    worse, better = _dummy_fits()

    fits = FitList([worse, better], names=[1, "better"])

    assert fits.names == ("1", "better")
    assert fits[1] is worse
    assert fits["better"] is better


def test_fitlist_validation_errors():
    worse, better = _dummy_fits()

    with pytest.raises(ValueError, match="at least one fitted model"):
        FitList([])
    with pytest.raises(ValueError, match="at least one fitted model"):
        FitList({})
    with pytest.raises(ValueError, match="same length"):
        FitList([worse, better], names=["one"])
    with pytest.raises(ValueError, match="unique"):
        FitList([worse, better], names=["dup", "dup"])
    with pytest.raises(ValueError, match="unique"):
        FitList({1: worse, "1": better})
    with pytest.raises(ValueError, match="dict keys"):
        FitList({"one": worse}, names=["x"])


def test_fitlist_unknown_model_lookup_has_clear_error():
    worse, _ = _dummy_fits()
    fits = FitList({"known": worse})

    with pytest.raises(KeyError, match="unknown model name 'missing'"):
        fits["missing"]
    with pytest.raises(KeyError, match="unknown model name 'missing'"):
        fits.predict(model="missing")


def test_fitlist_aic_table_delegates_to_existing_aic_table():
    worse, better = _dummy_fits()
    model_dict = {"worse": worse, "better": better}

    actual = FitList(model_dict).aic_table(include_warnings=False)
    expected = aic_table(model_dict, include_warnings=False)

    pd.testing.assert_frame_equal(actual, expected)


def test_fitlist_compare_delegates_to_existing_compare_models():
    worse, better = _dummy_fits()
    model_dict = {"worse": worse, "better": better}

    actual = FitList(model_dict).compare(include_warnings=False)
    expected = compare_models(model_dict, include_warnings=False)

    pd.testing.assert_frame_equal(actual.table, expected.table)
    assert actual.models == expected.models
    assert actual.best_model_name == expected.best_model_name
    assert actual.best_model is expected.best_model
    assert FitList(model_dict).summary() == compare_models(model_dict).summary()


def test_fitlist_best_model_name_and_best_model_use_lowest_aic():
    worse, better = _dummy_fits()

    fits = FitList({"worse": worse, "better": better})

    assert fits.best_model_name == "better"
    assert fits.best_model is better


def test_fitlist_predict_delegates_to_generic_predict_for_selected_model():
    fit = _pcount_fit()
    fits = FitList({"selected": fit})

    np.testing.assert_allclose(
        fits.predict(type="lambda", model="selected"),
        predict(fit, type="lambda"),
    )
    np.testing.assert_allclose(fits.predict(type="det", model="selected"), predict(fit, type="det"))


def test_fitlist_predict_defaults_to_best_model():
    fit = _pcount_fit()
    fits = FitList({"best": fit})

    np.testing.assert_allclose(fits.predict(type="lambda"), predict(fit, type="lambda"))


def test_fitlist_predict_preserves_stage_4_unsupported_type_error():
    fit = _pcount_fit()
    fits = FitList({"selected": fit})

    with pytest.raises(ValueError, match="unsupported prediction type 'psi'"):
        fits.predict(type="psi", model="selected")


def test_fitlist_is_core_only_not_top_level_all():
    assert FitList is not None
    assert "FitList" not in pyabundance.__all__
