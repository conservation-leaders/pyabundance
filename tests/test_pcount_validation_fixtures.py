from __future__ import annotations

import math

import numpy as np
import pytest
from pyabundance import _core, pcount
from pyabundance.core import FitList, predict
from pyabundance.pcount import pcount_loglik, pcount_negbin_loglik, pcount_zip_loglik

from tests.helpers.pcount_validation import fixture_names, load_pcount_validation_fixture

_LOG_LIK_FUNCTIONS = {
    "poisson": pcount_loglik,
    "negative_binomial": pcount_negbin_loglik,
    "zero_inflated_poisson": pcount_zip_loglik,
}
_PROBLEM_CLASSES = {
    "poisson": _core.PCountPoissonProblem,
    "negative_binomial": _core.PCountNegBinProblem,
    "zero_inflated_poisson": _core.PCountZIPProblem,
}


@pytest.mark.parametrize("name", fixture_names())
def test_pcount_validation_fixture_schema(name: str):
    fixture = load_pcount_validation_fixture(name)

    assert fixture.path.name == f"{name}.json"
    assert fixture.name.startswith("synthetic_small_")
    assert fixture.K == 7
    assert fixture.y.shape == (3, 3)
    assert fixture.X.shape == (3, 2)
    assert fixture.W.shape == (3, 3, 2)
    assert fixture.theta.ndim == 1
    assert np.isnan(fixture.y[1, 1])
    assert "clean-room" in fixture.provenance.lower()


@pytest.mark.parametrize("name", fixture_names())
def test_pcount_validation_fixture_function_loglik(name: str):
    fixture = load_pcount_validation_fixture(name)
    got = _LOG_LIK_FUNCTIONS[fixture.mixture](
        fixture.y,
        fixture.X,
        fixture.W,
        fixture.theta,
        fixture.K,
    )

    assert math.isclose(
        got,
        fixture.expected_loglik,
        abs_tol=fixture.absolute_tolerance,
        rel_tol=fixture.relative_tolerance,
    )


@pytest.mark.parametrize("name", fixture_names())
def test_pcount_validation_fixture_problem_object_loglik_matches_function(name: str):
    fixture = load_pcount_validation_fixture(name)
    function_loglik = _LOG_LIK_FUNCTIONS[fixture.mixture](
        fixture.y,
        fixture.X,
        fixture.W,
        fixture.theta,
        fixture.K,
    )
    problem = _PROBLEM_CLASSES[fixture.mixture](fixture.y, fixture.X, fixture.W, fixture.K)

    assert problem.n_sites == fixture.y.shape[0]
    assert problem.n_visits == fixture.y.shape[1]
    assert problem.K == fixture.K
    assert math.isclose(
        problem.loglik(fixture.theta),
        function_loglik,
        abs_tol=fixture.absolute_tolerance,
        rel_tol=fixture.relative_tolerance,
    )


def test_pcount_validation_fixture_fitted_result_shared_core_surfaces():
    fixture = load_pcount_validation_fixture("poisson")
    fit = pcount(
        fixture.y,
        fixture.X,
        fixture.W,
        K=fixture.K,
        mixture=fixture.mixture,
        start=fixture.theta,
        method="BFGS",
    )

    assert fit.success
    assert fit.model_spec.model == "pcount"
    assert fit.model_spec.response == "count"
    assert fit.model_spec.metadata["mixture"] == "poisson"
    assert fit.model_spec.metadata["K"] == fixture.K
    assert fit.model_spec.metadata["n_sites"] == fixture.y.shape[0]
    assert fit.model_spec.metadata["n_visits"] == fixture.y.shape[1]
    assert [block.name for block in fit.parameter_blocks] == ["lambda", "p"]
    assert [(block.start, block.stop) for block in fit.parameter_blocks] == [(0, 2), (2, 4)]

    np.testing.assert_allclose(predict(fit, type="lambda"), fit.predict_lambda())
    np.testing.assert_allclose(fit.predict(type="det"), fit.predict_detection())

    fits = FitList({"fixture_poisson": fit})
    assert fits.names == ("fixture_poisson",)
    assert fits.best_model is fit
    np.testing.assert_allclose(fits.predict(type="fitted"), fit.fitted_counts())
