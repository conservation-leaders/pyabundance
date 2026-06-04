from __future__ import annotations

import pandas as pd
import pytest
from pyabundance import build_pcount_matrices, load_example_pcount, pcount_df


def test_visit_labels_auto_infers_obs_labels_that_differ_from_count_cols():
    data = load_example_pcount("poisson", n_sites=6)
    matrices = build_pcount_matrices(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
    )
    assert matrices.visit_labels == ["v1", "v2", "v3"]
    assert matrices.visit_label_source == "auto_obs_data"
    assert "Inferred visit_labels" in (matrices.visit_label_message or "")

    fit = pcount_df(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K="auto",
    )
    assert fit.visit_labels == ["v1", "v2", "v3"]
    assert fit.visit_label_source == "auto_obs_data"


def test_explicit_visit_labels_still_work():
    data = load_example_pcount("poisson", n_sites=6)
    matrices = build_pcount_matrices(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        visit_labels=["v1", "v2", "v3"],
        count_cols=data.count_cols,
        detection_formula="~ visit - 1",
    )
    assert matrices.visit_label_source == "explicit"


def test_visit_labels_auto_rejects_non_categorical_different_visit_labels():
    site_data = pd.DataFrame(
        {
            "site_id": ["s1", "s2"],
            "y1": [0, 1],
            "y2": [1, 0],
            "y3": [2, 1],
        }
    )
    obs_data = pd.DataFrame(
        [
            {"site_id": "s1", "visit": "v2"},
            {"site_id": "s1", "visit": "v1"},
            {"site_id": "s1", "visit": "v3"},
            {"site_id": "s2", "visit": "v2"},
            {"site_id": "s2", "visit": "v1"},
            {"site_id": "s2", "visit": "v3"},
        ]
    )
    with pytest.raises(ValueError, match="cannot be safely auto-inferred"):
        build_pcount_matrices(
            site_data=site_data,
            obs_data=obs_data,
            site_id_col="site_id",
            count_cols=["y1", "y2", "y3"],
            detection_formula="~ visit - 1",
        )


def test_visit_labels_auto_uses_count_cols_when_obs_labels_match():
    site_data = pd.DataFrame(
        {
            "site_id": ["s1", "s2"],
            "y1": [0, 1],
            "y2": [1, 0],
            "y3": [2, 1],
        }
    )
    obs_data = pd.DataFrame(
        [
            {"site_id": "s1", "visit": "y2"},
            {"site_id": "s1", "visit": "y1"},
            {"site_id": "s1", "visit": "y3"},
            {"site_id": "s2", "visit": "y2"},
            {"site_id": "s2", "visit": "y1"},
            {"site_id": "s2", "visit": "y3"},
        ]
    )
    matrices = build_pcount_matrices(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2", "y3"],
        detection_formula="~ visit - 1",
    )
    assert matrices.visit_labels == ["y1", "y2", "y3"]
    assert matrices.visit_label_source == "count_cols"


def test_visit_labels_auto_preserves_ordered_categorical_order():
    site_data = pd.DataFrame(
        {
            "site_id": ["s1", "s2"],
            "y1": [0, 1],
            "y2": [1, 0],
            "y10": [2, 1],
        }
    )
    obs_data = pd.DataFrame(
        [
            {"site_id": "s1", "visit": "v1"},
            {"site_id": "s1", "visit": "v2"},
            {"site_id": "s1", "visit": "v10"},
            {"site_id": "s2", "visit": "v1"},
            {"site_id": "s2", "visit": "v2"},
            {"site_id": "s2", "visit": "v10"},
        ]
    )
    obs_data["visit"] = pd.Categorical(
        obs_data["visit"], categories=["v1", "v10", "v2"], ordered=True
    )
    matrices = build_pcount_matrices(
        site_data=site_data,
        obs_data=obs_data,
        site_id_col="site_id",
        count_cols=["y1", "y2", "y10"],
        detection_formula="~ visit - 1",
    )
    assert matrices.visit_labels == ["v1", "v10", "v2"]


def test_visit_label_count_mismatch_has_beginner_message():
    data = load_example_pcount("poisson", n_sites=3)
    bad = data.obs_data[data.obs_data["visit"] != "v3"].copy()
    with pytest.raises(ValueError, match="Pass explicit visit_labels"):
        build_pcount_matrices(
            site_data=data.site_data,
            obs_data=bad,
            site_id_col="site_id",
            count_cols=data.count_cols,
            detection_formula="~ visit - 1",
        )


def test_duplicate_and_missing_site_visit_rows_raise():
    data = load_example_pcount("poisson", n_sites=3)
    dup = pd.concat([data.obs_data, data.obs_data.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="one row per site"):
        build_pcount_matrices(
            site_data=data.site_data,
            obs_data=dup,
            site_id_col="site_id",
            count_cols=data.count_cols,
        )

    missing = data.obs_data.iloc[:-1]
    with pytest.raises(ValueError, match="missing required site"):
        build_pcount_matrices(
            site_data=data.site_data,
            obs_data=missing,
            site_id_col="site_id",
            count_cols=data.count_cols,
            visit_labels=["v1", "v2", "v3"],
        )
