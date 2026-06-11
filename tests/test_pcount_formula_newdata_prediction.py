from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pyabundance import build_pcount_matrices, pcount, pcount_df
from pyabundance.core import build_process_design, predict

COUNT_COLS = ["y1", "y2", "y3"]
VISITS = ["v1", "v2", "v3"]


def _site_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site_id": [f"s{i}" for i in range(1, 9)],
            "y1": [0, 1, 2, 1, 3, 0, 2, 1],
            "y2": [1, 1, 1, 2, 2, 0, 1, 1],
            "y3": [0, 2, 1, 1, 3, 1, 2, 0],
            "forest": [0.0, 0.2, 0.4, 0.1, 0.8, 0.3, 0.6, 0.5],
        }
    )


def _obs_data(site_ids: list[str]) -> pd.DataFrame:
    rows = []
    for i, site_id in enumerate(site_ids):
        for j, visit in enumerate(VISITS):
            rows.append(
                {
                    "site_id": site_id,
                    "visit": visit,
                    "wind": 0.1 + 0.05 * i + 0.2 * j,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def formula_fit():
    site = _site_data()
    return pcount_df(
        site_data=site,
        obs_data=_obs_data(site["site_id"].tolist()),
        site_id_col="site_id",
        visit_col="visit",
        visit_labels=VISITS,
        count_cols=COUNT_COLS,
        abundance_formula="~ forest",
        detection_formula="~ wind + visit",
        K=25,
        method="BFGS",
    )


@pytest.fixture
def new_site_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "site_id": ["n1", "n2", "n3"],
            "forest": [0.15, 0.45, 0.9],
        }
    )


@pytest.fixture
def new_obs_data(new_site_data: pd.DataFrame) -> pd.DataFrame:
    return _obs_data(new_site_data["site_id"].tolist())


def _manual_new_matrices(new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame):
    site_with_counts = new_site_data.copy()
    for count_col in COUNT_COLS:
        site_with_counts[count_col] = 0
    return build_pcount_matrices(
        site_data=site_with_counts,
        obs_data=new_obs_data,
        site_id_col="site_id",
        visit_col="visit",
        visit_labels=VISITS,
        count_cols=COUNT_COLS,
        abundance_formula="~ forest",
        detection_formula="~ wind + visit",
    )


def test_lambda_new_site_data_matches_manual_formula_matrix(
    formula_fit, new_site_data: pd.DataFrame
):
    design = build_process_design(formula_fit.model_spec.process("lambda"), new_site_data)
    manual = formula_fit.predict_lambda(X=design.matrix)

    actual = formula_fit.predict(type="lambda", new_site_data=new_site_data)
    abundance = formula_fit.predict(type="abundance", new_site_data=new_site_data)

    np.testing.assert_allclose(actual, manual)
    np.testing.assert_allclose(abundance, manual)
    assert actual.shape == (len(new_site_data),)


def test_detection_newdata_matches_manual_w_prediction(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    matrices = _manual_new_matrices(new_site_data, new_obs_data)
    manual = formula_fit.predict_detection(W=matrices.W)

    actual = formula_fit.predict(
        type="detection",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
    )
    alias = formula_fit.predict(type="p", new_site_data=new_site_data, new_obs_data=new_obs_data)

    np.testing.assert_allclose(actual, manual)
    np.testing.assert_allclose(alias, manual)
    assert actual.shape == (len(new_site_data), len(VISITS))


def test_det_alias_newdata_matches_detection(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    detection = formula_fit.predict(
        type="detection",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
    )
    det = formula_fit.predict(type="det", new_site_data=new_site_data, new_obs_data=new_obs_data)
    core_det = predict(
        formula_fit,
        type="det",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
    )

    np.testing.assert_allclose(det, detection)
    np.testing.assert_allclose(core_det, detection)


def test_fitted_newdata_matches_latent_mean_times_detection(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    matrices = _manual_new_matrices(new_site_data, new_obs_data)
    expected = formula_fit.predict_lambda(X=matrices.X)[:, None] * formula_fit.predict_detection(
        W=matrices.W
    )

    actual = formula_fit.predict(
        type="fitted",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
    )

    np.testing.assert_allclose(actual, expected)
    assert actual.shape == (len(new_site_data), len(VISITS))


def test_default_observation_rows_are_generated_from_new_site_data(formula_fit):
    site = pd.DataFrame(
        {
            "site_id": ["n1", "n2"],
            "forest": [0.2, 0.7],
            "wind": [0.4, 0.9],
        }
    )
    manual_site = site.copy()
    for count_col in COUNT_COLS:
        manual_site[count_col] = 0
    matrices = build_pcount_matrices(
        site_data=manual_site,
        site_id_col="site_id",
        visit_labels=VISITS,
        count_cols=COUNT_COLS,
        abundance_formula="~ forest",
        detection_formula="~ wind + visit",
    )

    actual = formula_fit.predict(type="detection", new_site_data=site)

    np.testing.assert_allclose(actual, formula_fit.predict_detection(W=matrices.W))


def test_newdata_prediction_dataframe_outputs(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    abundance = predict(formula_fit, type="lambda", new_site_data=new_site_data, as_dataframe=True)
    detection = predict(
        formula_fit,
        type="detection",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
        as_dataframe=True,
    )

    assert list(abundance.columns) == ["site_id", "estimate"]
    assert abundance["site_id"].tolist() == ["n1", "n2", "n3"]
    assert {"site_id", "visit", "estimate"}.issubset(detection.columns)
    assert detection.shape[0] == len(new_site_data) * len(VISITS)


def test_core_predict_and_fit_predict_dispatch_newdata(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    via_core = predict(
        formula_fit,
        type="fitted",
        newdata=new_site_data,
        new_obs_data=new_obs_data,
    )
    via_method = formula_fit.predict(
        type="fitted",
        new_site_data=new_site_data,
        new_obs_data=new_obs_data,
    )

    np.testing.assert_allclose(via_core, via_method)


def test_core_predict_rejects_formula_newdata_with_matrix_design_kwargs(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    with pytest.raises(ValueError) as x_exc_info:
        predict(
            formula_fit,
            type="lambda",
            new_site_data=new_site_data,
            X=np.ones((len(new_site_data), formula_fit.n_abundance_params), dtype=np.float64),
        )

    x_message = str(x_exc_info.value)
    assert "combining formula newdata" in x_message
    assert "matrix design kwargs" in x_message
    assert "X" in x_message

    with pytest.raises(ValueError) as w_exc_info:
        predict(
            formula_fit,
            type="p",
            new_site_data=new_site_data,
            new_obs_data=new_obs_data,
            W=np.ones(
                (len(new_site_data), len(VISITS), formula_fit.n_detection_params),
                dtype=np.float64,
            ),
        )

    w_message = str(w_exc_info.value)
    assert "combining formula newdata" in w_message
    assert "matrix design kwargs" in w_message
    assert "W" in w_message


def test_fit_predict_rejects_formula_newdata_with_matrix_design_kwargs(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    with pytest.raises(ValueError) as x_exc_info:
        formula_fit.predict(
            type="lambda",
            new_site_data=new_site_data,
            X=np.ones((len(new_site_data), formula_fit.n_abundance_params), dtype=np.float64),
        )

    x_message = str(x_exc_info.value)
    assert "combining formula newdata" in x_message
    assert "matrix design kwargs" in x_message
    assert "X" in x_message

    with pytest.raises(ValueError) as w_exc_info:
        formula_fit.predict(
            type="p",
            new_site_data=new_site_data,
            new_obs_data=new_obs_data,
            W=np.ones(
                (len(new_site_data), len(VISITS), formula_fit.n_detection_params),
                dtype=np.float64,
            ),
        )

    w_message = str(w_exc_info.value)
    assert "combining formula newdata" in w_message
    assert "matrix design kwargs" in w_message
    assert "W" in w_message


def test_matrix_fit_newdata_request_requires_formula_metadata(new_site_data: pd.DataFrame):
    y = np.ones((3, 2), dtype=np.float64)
    x = np.ones((3, 1), dtype=np.float64)
    w = np.ones((3, 2, 1), dtype=np.float64)
    fit = pcount(y, x, w, K=5)

    with pytest.raises(ValueError, match="formula metadata is required"):
        predict(fit, type="lambda", new_site_data=new_site_data)


def test_missing_covariate_raises_clear_error(formula_fit):
    with pytest.raises(ValueError, match="missing covariates.*forest"):
        formula_fit.predict(type="lambda", new_site_data=pd.DataFrame({"site_id": ["n1"]}))


def test_mismatched_design_columns_raise_clear_error(formula_fit, new_site_data: pd.DataFrame):
    obs = _obs_data(new_site_data["site_id"].tolist())
    obs = obs[obs["visit"] == "v1"].copy()

    with pytest.raises(ValueError, match="detection design columns do not match fitted columns"):
        formula_fit.predict(
            type="detection",
            new_site_data=new_site_data,
            new_obs_data=obs,
            visit_labels=["v1"],
        )


def test_missing_observation_rows_raise_clear_error(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    bad_obs = new_obs_data.iloc[:-1].copy()

    with pytest.raises(ValueError, match="missing required site×visit rows"):
        formula_fit.predict(
            type="detection",
            new_site_data=new_site_data,
            new_obs_data=bad_obs,
        )


def test_duplicate_observation_rows_raise_clear_error(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    duplicate_obs = pd.concat([new_obs_data, new_obs_data.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="one row per site × visit"):
        formula_fit.predict(
            type="p",
            new_site_data=new_site_data,
            new_obs_data=duplicate_obs,
        )


def test_unknown_observation_sites_raise_clear_error(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    bad_obs = new_obs_data.copy()
    bad_obs.loc[0, "site_id"] = "unknown-site"

    with pytest.raises(ValueError, match="unknown sites"):
        formula_fit.predict(
            type="detection",
            new_site_data=new_site_data,
            new_obs_data=bad_obs,
        )


def test_unknown_observation_visits_raise_clear_error(
    formula_fit, new_site_data: pd.DataFrame, new_obs_data: pd.DataFrame
):
    bad_obs = new_obs_data.copy()
    bad_obs.loc[0, "visit"] = "unknown-visit"

    with pytest.raises(ValueError, match="unknown visits"):
        formula_fit.predict(
            type="detection",
            new_site_data=new_site_data,
            new_obs_data=bad_obs,
        )
