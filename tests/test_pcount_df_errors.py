import numpy as np
import pandas as pd
import pytest
from pyabundance import build_pcount_matrices


def base_df():
    return pd.DataFrame(
        {
            "site_id": ["s1", "s2"],
            "y1": [0, 1],
            "y2": [1, 0],
            "y3": [0, 2],
            "x": [0.1, 0.2],
        }
    )


def test_missing_count_column_raises():
    with pytest.raises(ValueError, match="missing count columns"):
        build_pcount_matrices(site_data=base_df(), count_cols=["y1", "y2", "missing"])


def test_non_integer_count_raises():
    df = base_df().astype({"y1": float})
    df.loc[0, "y1"] = 1.5
    with pytest.raises(ValueError, match="non-negative integers"):
        build_pcount_matrices(site_data=df, count_cols=["y1", "y2", "y3"])


def test_missing_formula_covariate_raises():
    with pytest.raises(ValueError, match="failed to build abundance"):
        build_pcount_matrices(
            site_data=base_df(), count_cols=["y1", "y2", "y3"], abundance_formula="~ missing"
        )


def test_missing_formula_covariate_value_raises():
    df = base_df()
    df.loc[0, "x"] = np.nan
    with pytest.raises(ValueError, match="failed to build abundance"):
        build_pcount_matrices(site_data=df, count_cols=["y1", "y2", "y3"], abundance_formula="~ x")


def test_drop_missing_sites_drops_formula_covariates_only():
    df = base_df()
    df["unused"] = [np.nan, 1.0]
    df.loc[0, "x"] = np.nan
    matrices = build_pcount_matrices(
        site_data=df,
        count_cols=["y1", "y2", "y3"],
        abundance_formula="~ x",
        site_id_col="site_id",
        drop_missing_sites=True,
    )
    assert matrices.y.shape == (1, 3)
    assert matrices.site_ids == ["s2"]


def test_obs_data_requires_site_id_col():
    obs = pd.DataFrame({"site_id": ["s1"], "visit": ["y1"], "wind": [0.1]})
    with pytest.raises(ValueError, match="site_id_col is required"):
        build_pcount_matrices(site_data=base_df(), count_cols=["y1", "y2", "y3"], obs_data=obs)


def test_obs_data_missing_site_id_col_raises():
    obs = pd.DataFrame({"visit": ["y1"], "wind": [0.1]})
    with pytest.raises(ValueError, match="site_id_col"):
        build_pcount_matrices(
            site_data=base_df(),
            count_cols=["y1", "y2", "y3"],
            obs_data=obs,
            site_id_col="site_id",
        )


def test_obs_data_missing_visit_col_raises():
    obs = pd.DataFrame({"site_id": ["s1"], "wind": [0.1]})
    with pytest.raises(ValueError, match="visit_col"):
        build_pcount_matrices(
            site_data=base_df(),
            count_cols=["y1", "y2", "y3"],
            obs_data=obs,
            site_id_col="site_id",
        )


def test_obs_data_missing_site_visit_row_raises():
    obs = pd.DataFrame(
        {
            "site_id": ["s1", "s1", "s1", "s2", "s2"],
            "visit": ["y1", "y2", "y3", "y1", "y2"],
            "wind": np.arange(5),
        }
    )
    with pytest.raises(ValueError, match="missing required site"):
        build_pcount_matrices(
            site_data=base_df(),
            count_cols=["y1", "y2", "y3"],
            obs_data=obs,
            site_id_col="site_id",
            detection_formula="~ wind",
        )


def test_unsupported_formula_feature_raises():
    with pytest.raises(ValueError, match="unsupported formula feature"):
        build_pcount_matrices(
            site_data=base_df(),
            count_cols=["y1", "y2", "y3"],
            abundance_formula="~ x | site_id",
        )
