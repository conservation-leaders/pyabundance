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


def test_visit_label_count_mismatch_has_beginner_message():
    data = load_example_pcount("poisson", n_sites=3)
    bad = data.obs_data[data.obs_data["visit"] != "v3"].copy()
    with pytest.raises(ValueError, match="pass visit_labels=.*or use visit_labels='auto'"):
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
