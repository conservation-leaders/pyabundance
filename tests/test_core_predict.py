from __future__ import annotations

import numpy as np
import pandas as pd
import pyabundance
import pytest
from pyabundance import pcount
from pyabundance.core import predict, register_predictor


def _matrix_fit():
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


def test_generic_predict_dispatches_pcount_matrix_fit_existing_data_types():
    fit = _matrix_fit()

    np.testing.assert_allclose(predict(fit, type="lambda"), fit.predict_lambda())
    np.testing.assert_allclose(predict(fit, type="abundance"), fit.predict_abundance())
    np.testing.assert_allclose(predict(fit, type="p"), fit.predict_detection())
    np.testing.assert_allclose(predict(fit, type="det"), predict(fit, type="p"))
    np.testing.assert_allclose(predict(fit, type="det"), fit.predict_detection())
    np.testing.assert_allclose(predict(fit, type="detection"), fit.predict_detection())
    np.testing.assert_allclose(predict(fit, type="fitted"), fit.fitted_counts())


def test_pcount_result_predict_method_delegates_to_generic_dispatch():
    fit = _matrix_fit()

    np.testing.assert_allclose(fit.predict(type="lambda"), predict(fit, type="lambda"))
    np.testing.assert_allclose(fit.predict(type="p"), predict(fit, type="p"))
    np.testing.assert_allclose(fit.predict(type="det"), fit.predict_detection())
    np.testing.assert_allclose(fit.predict(type="fitted"), predict(fit, type="fitted"))


def test_pcount_dispatch_aliases_match_existing_methods():
    fit = _matrix_fit()

    np.testing.assert_allclose(predict(fit, type="lambda"), fit.predict_lambda())
    np.testing.assert_allclose(predict(fit, type="abundance"), fit.predict_abundance())
    np.testing.assert_allclose(predict(fit, type="p"), fit.predict_detection())
    np.testing.assert_allclose(predict(fit, type="det"), fit.predict_detection())
    np.testing.assert_allclose(predict(fit, type="detection"), fit.predict_detection())


def test_pcount_dispatch_can_forward_existing_method_options():
    fit = _matrix_fit()

    abundance = predict(fit, type="lambda", as_dataframe=True)
    detection = predict(fit, type="detection", as_dataframe=True)

    assert isinstance(abundance, pd.DataFrame)
    assert list(abundance.columns) == ["estimate"]
    assert isinstance(detection, pd.DataFrame)
    assert {"site_id", "visit", "estimate"}.issubset(detection.columns)


def test_unsupported_prediction_type_has_clear_error():
    fit = _matrix_fit()

    with pytest.raises(ValueError, match="unsupported prediction type 'psi'") as exc_info:
        predict(fit, type="psi")

    assert "det" in str(exc_info.value)


def test_unsupported_result_object_has_clear_error():
    with pytest.raises(TypeError, match="unsupported result object"):
        predict(object(), type="lambda")


def test_matrix_fit_newdata_prediction_requests_require_formula_metadata():
    fit = _matrix_fit()

    for name in ["newdata", "new_site_data", "new_obs_data"]:
        with pytest.raises(ValueError, match="formula metadata is required"):
            predict(fit, type="lambda", **{name: object()})


def test_matrix_design_prediction_requests_can_route_without_newdata():
    fit = _matrix_fit()

    np.testing.assert_allclose(predict(fit, type="lambda", X=fit.X.copy()), fit.predict_lambda())
    np.testing.assert_allclose(
        predict(fit, type="detection", W=fit.W.copy()), fit.predict_detection()
    )


def test_existing_pcount_prediction_methods_still_work_unchanged():
    fit = _matrix_fit()

    assert fit.predict_lambda().shape == (fit.y.shape[0],)
    assert fit.predict_abundance().shape == (fit.y.shape[0],)
    assert fit.predict_detection().shape == fit.y.shape
    assert fit.fitted_counts().shape == fit.y.shape


def test_existing_dataframe_prediction_helpers_still_work_unchanged():
    fit = _matrix_fit()

    abundance = fit.abundance_dataframe()
    detection = fit.detection_dataframe()
    fitted = fit.fitted_counts_dataframe()
    residuals = fit.residuals_dataframe()

    assert list(abundance.columns) == ["estimate"]
    assert {"site_id", "visit", "estimate"}.issubset(detection.columns)
    assert {"observed", "fitted", "raw_residual", "pearson_residual", "missing"}.issubset(
        fitted.columns
    )
    assert {"site_id", "visit", "residual"}.issubset(residuals.columns)


def test_generic_predict_names_are_core_only_not_top_level_all():
    assert predict is not None
    assert register_predictor is not None
    assert "predict" not in pyabundance.__all__
    assert "register_predictor" not in pyabundance.__all__
