from __future__ import annotations

import numpy as np
import pandas as pd
import pyabundance
import pytest
from pyabundance import PCountMatrices, build_pcount_matrices, pcount_df
from pyabundance.core import FramePCount


def _simple_arrays():
    y = np.asarray([[1.0, 0.0], [2.0, 1.0], [0.0, 1.0]])
    X = np.asarray([[1.0, 0.2], [1.0, 0.4], [1.0, 0.6]])
    W = np.ones((3, 2, 1), dtype=np.float64)
    return y, X, W


def _simple_data():
    site_data = pd.DataFrame(
        {
            "site_id": ["s1", "s2", "s3"],
            "y1": [1, 2, 0],
            "y2": [0, 1, 1],
            "forest": [0.2, 0.4, 0.6],
        }
    )
    obs_data = pd.DataFrame(
        [
            {"site_id": "s1", "visit": "v1", "wind": 0.1},
            {"site_id": "s1", "visit": "v2", "wind": 0.2},
            {"site_id": "s2", "visit": "v1", "wind": 0.3},
            {"site_id": "s2", "visit": "v2", "wind": 0.4},
            {"site_id": "s3", "visit": "v1", "wind": 0.5},
            {"site_id": "s3", "visit": "v2", "wind": 0.6},
        ]
    )
    return site_data, obs_data


def test_frame_pcount_from_matrices_valid_arrays_preserves_metadata():
    y, X, W = _simple_arrays()
    site_data = pd.DataFrame({"forest": [0.2, 0.4, 0.6]})
    obs_data = pd.DataFrame({"wind": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]})

    frame = FramePCount.from_matrices(
        y=y,
        X=X,
        W=W,
        site_ids=["s1", "s2", "s3"],
        visit_labels=["v1", "v2"],
        abundance_column_names=["Intercept", "forest"],
        detection_column_names=["Intercept"],
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ 1",
        site_data=site_data,
        obs_data=obs_data,
        visit_label_source="explicit",
        visit_label_message="provided by test",
        metadata={"stage": 2},
    )

    np.testing.assert_allclose(frame.y, y)
    np.testing.assert_allclose(frame.X, X)
    np.testing.assert_allclose(frame.W, W)
    assert frame.site_data is site_data
    assert frame.obs_data is obs_data
    assert frame.site_ids == ("s1", "s2", "s3")
    assert frame.visit_labels == ("v1", "v2")
    assert frame.abundance_column_names == ("Intercept", "forest")
    assert frame.detection_column_names == ("Intercept",)
    assert frame.count_cols == ("y1", "y2")
    assert frame.abundance_formula == "~ forest"
    assert frame.detection_formula == "~ 1"
    assert frame.visit_label_source == "explicit"
    assert frame.visit_label_message == "provided by test"
    assert frame.metadata["stage"] == 2


def test_frame_pcount_from_pcount_matrices_and_to_frame_interop():
    site_data, obs_data = _simple_data()
    matrices = build_pcount_matrices(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ wind",
        visit_labels=["v1", "v2"],
    )

    frame = FramePCount.from_pcount_matrices(matrices)
    frame_from_method = matrices.to_frame()

    assert isinstance(matrices, PCountMatrices)
    assert isinstance(frame_from_method, FramePCount)
    np.testing.assert_allclose(frame.y, matrices.y)
    np.testing.assert_allclose(frame.X, matrices.X)
    np.testing.assert_allclose(frame.W, matrices.W)
    assert frame.site_ids == tuple(matrices.site_ids)
    assert frame.visit_labels == tuple(matrices.visit_labels)
    assert frame.abundance_column_names == tuple(matrices.abundance_column_names)
    assert frame.detection_column_names == tuple(matrices.detection_column_names)
    assert frame.count_cols == tuple(matrices.count_cols)
    assert frame.abundance_formula == "~ forest"
    assert frame.detection_formula == "~ wind"
    assert frame.site_data is matrices.site_data_used
    assert frame.obs_data is matrices.obs_data_used
    assert frame.visit_label_source == "explicit"


def test_frame_pcount_data_info():
    y, X, W = _simple_arrays()
    frame = FramePCount.from_matrices(y, X, W)
    assert frame.n_sites == 3
    assert frame.n_visits == 2
    assert frame.n_abundance_params == 2
    assert frame.n_detection_params == 1
    assert frame.response_shape == (3, 2)
    assert frame.data_info == {
        "n_sites": 3,
        "n_visits": 2,
        "n_abundance_params": 2,
        "n_detection_params": 1,
    }


def test_frame_pcount_invalid_y_shape_raises():
    _, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="y must have 2 dimensions"):
        FramePCount.from_matrices(y=[1.0, 2.0], X=X, W=W)


def test_frame_pcount_invalid_x_shape_raises():
    y, _, W = _simple_arrays()
    with pytest.raises(ValueError, match="X must have 2 dimensions"):
        FramePCount.from_matrices(y=y, X=[1.0, 2.0, 3.0], W=W)


def test_frame_pcount_invalid_w_shape_raises():
    y, X, _ = _simple_arrays()
    with pytest.raises(ValueError, match="W must have 3 dimensions"):
        FramePCount.from_matrices(y=y, X=X, W=np.ones((3, 2)))


def test_frame_pcount_mismatched_site_count_raises():
    y, _, W = _simple_arrays()
    with pytest.raises(ValueError, match="same number of sites"):
        FramePCount.from_matrices(y=y, X=np.ones((2, 2)), W=W)


def test_frame_pcount_mismatched_visit_count_raises():
    y, X, _ = _simple_arrays()
    with pytest.raises(ValueError, match="same number of visits"):
        FramePCount.from_matrices(y=y, X=X, W=np.ones((3, 3, 1)))


def test_frame_pcount_mismatched_site_ids_length_raises():
    y, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="site_ids"):
        FramePCount.from_matrices(y=y, X=X, W=W, site_ids=["s1", "s2"])


def test_frame_pcount_mismatched_visit_labels_length_raises():
    y, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="visit_labels"):
        FramePCount.from_matrices(y=y, X=X, W=W, visit_labels=["v1"])


def test_frame_pcount_mismatched_count_cols_length_raises():
    y, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="count_cols"):
        FramePCount.from_matrices(y=y, X=X, W=W, count_cols=["y1"])


def test_frame_pcount_mismatched_abundance_column_names_length_raises():
    y, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="abundance_column_names"):
        FramePCount.from_matrices(y=y, X=X, W=W, abundance_column_names=["Intercept"])


def test_frame_pcount_mismatched_detection_column_names_length_raises():
    y, X, W = _simple_arrays()
    with pytest.raises(ValueError, match="detection_column_names"):
        FramePCount.from_matrices(
            y=y,
            X=X,
            W=W,
            detection_column_names=["Intercept", "wind"],
        )


def test_existing_pcount_df_workflow_still_works_unchanged():
    site_data, obs_data = _simple_data()
    fit = pcount_df(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ wind",
        visit_labels=["v1", "v2"],
        K=20,
    )
    assert fit.from_dataframe is True
    assert fit.site_ids == ["s1", "s2", "s3"]
    assert fit.visit_labels == ["v1", "v2"]
    assert fit.data_info == {
        "n_sites": 3,
        "n_visits": 2,
        "n_abundance_params": 2,
        "n_detection_params": 2,
    }


def test_build_pcount_matrices_still_returns_pcount_matrices():
    site_data, obs_data = _simple_data()
    matrices = build_pcount_matrices(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ wind",
        visit_labels=["v1", "v2"],
    )
    assert type(matrices) is PCountMatrices


def test_frame_pcount_exported_from_core_only_not_top_level_all():
    assert FramePCount is not None
    assert "FramePCount" not in pyabundance.__all__


def test_pcount_matrices_to_frame_mapping_preserves_available_metadata():
    site_data, obs_data = _simple_data()
    matrices = build_pcount_matrices(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2"],
        abundance_formula="~ forest",
        detection_formula="~ wind",
        visit_labels=["v1", "v2"],
    )
    frame = matrices.to_frame()

    expected = {
        "y": matrices.y,
        "X": matrices.X,
        "W": matrices.W,
        "site_data": matrices.site_data_used,
        "obs_data": matrices.obs_data_used,
        "site_ids": tuple(matrices.site_ids),
        "visit_labels": tuple(matrices.visit_labels),
        "abundance_column_names": tuple(matrices.abundance_column_names),
        "detection_column_names": tuple(matrices.detection_column_names),
        "count_cols": tuple(matrices.count_cols),
        "abundance_formula": "~ forest",
        "detection_formula": "~ wind",
        "visit_label_source": matrices.visit_label_source,
        "visit_label_message": matrices.visit_label_message,
    }
    for attr, value in expected.items():
        if attr in {"y", "X", "W"}:
            np.testing.assert_allclose(getattr(frame, attr), value)
        elif attr in {"site_data", "obs_data"}:
            assert getattr(frame, attr) is value
        else:
            assert getattr(frame, attr) == value
