import pandas as pd
import pytest
from pyabundance import build_pcount_matrices


def site_df():
    return pd.DataFrame(
        {
            "site_id": ["s1", "s2"],
            "y1": [0, 1],
            "y2": [1, 0],
            "y3": [0, 2],
            "forest": [0.2, 0.8],
        }
    )


def obs_df(out_of_order: bool = True):
    rows = [
        {"site_id": "s1", "visit": "v1", "wind": 0.1},
        {"site_id": "s1", "visit": "v2", "wind": 0.2},
        {"site_id": "s1", "visit": "v3", "wind": 0.3},
        {"site_id": "s2", "visit": "v1", "wind": 0.4},
        {"site_id": "s2", "visit": "v2", "wind": 0.5},
        {"site_id": "s2", "visit": "v3", "wind": 0.6},
    ]
    if out_of_order:
        rows = [rows[3], rows[0], rows[5], rows[2], rows[4], rows[1]]
    return pd.DataFrame(rows)


def test_formula_obs_covariates_sorted_internally():
    matrices = build_pcount_matrices(
        site_data=site_df(),
        obs_data=obs_df(),
        site_id_col="site_id",
        visit_col="visit",
        visit_labels=["v1", "v2", "v3"],
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ forest",
        detection_formula="~ wind + visit",
    )
    assert matrices.W.shape[0:2] == (2, 3)
    assert "wind" in matrices.detection_column_names
    assert "visit[T.v2]" in matrices.detection_column_names
    assert list(matrices.obs_data_used["site_id"][:3]) == ["s1", "s1", "s1"]
    assert list(matrices.obs_data_used["visit"][:3].astype(str)) == ["v1", "v2", "v3"]


def test_formula_obs_covariates_missing_row_raises():
    bad = obs_df().iloc[:-1].copy()
    with pytest.raises(ValueError, match="missing required site"):
        build_pcount_matrices(
            site_data=site_df(),
            obs_data=bad,
            site_id_col="site_id",
            visit_labels=["v1", "v2", "v3"],
            count_cols=["y1", "y2", "y3"],
            abundance_formula="~ forest",
            detection_formula="~ wind + visit",
        )
