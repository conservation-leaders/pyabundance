from __future__ import annotations

import numpy as np
import pytest
from pyabundance import PCountAnalysis, analyze_pcount, load_example_pcount


def test_analyze_pcount_fits_candidates_and_selects_best():
    data = load_example_pcount("poisson", n_sites=25)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K="auto",
        se=False,
    )
    assert isinstance(analysis, PCountAnalysis)
    assert {"poisson", "negative_binomial", "zero_inflated_poisson"}.issubset(analysis.fits)
    assert analysis.best_model_name in analysis.fits
    assert np.isclose(analysis.table["AIC_weight"].sum(), 1.0)
    assert analysis.visit_labels == ["v1", "v2", "v3"]


def test_analyze_pcount_failed_model_handling_with_too_small_k():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ visit - 1",
        K=0,
        se=False,
    )
    assert analysis.failed
    assert not analysis.fits
    assert analysis.best_model_name is None


def test_analyze_pcount_single_start_vector_allowed_for_one_mixture():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ 1",
        mixtures=("poisson",),
        K="auto",
        start=np.zeros(2),
        se=False,
    )
    assert set(analysis.fits) == {"poisson"}


def test_analyze_pcount_single_string_mixture_is_one_candidate():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ 1",
        mixtures="poisson",
        K="auto",
        se=False,
    )
    assert set(analysis.fits) == {"poisson"}
    assert analysis.best_model_name == "poisson" or analysis.best_model_name in analysis.fits


def test_analyze_pcount_single_string_mixture_alias_is_canonicalized():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ 1",
        mixtures="P",
        K="auto",
        se=False,
    )
    assert set(analysis.fits) == {"poisson"}
    assert analysis.model("poisson").mixture == "poisson"


def test_analyze_pcount_single_start_vector_rejected_for_multiple_mixtures():
    data = load_example_pcount("poisson", n_sites=12)
    with pytest.raises(ValueError, match="one start vector for multiple mixtures"):
        analyze_pcount(
            site_data=data.site_data,
            obs_data=data.obs_data,
            site_id_col="site_id",
            count_cols=data.count_cols,
            abundance_formula="~ 1",
            detection_formula="~ 1",
            mixtures=("poisson", "negative_binomial"),
            K="auto",
            start=np.zeros(2),
            se=False,
        )


def test_analyze_pcount_start_dict_accepts_aliases_and_missing_keys():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ 1",
        mixtures=("poisson", "negative_binomial", "zero_inflated_poisson"),
        K="auto",
        start={"P": np.zeros(2), "NB": np.zeros(3)},
        se=False,
    )
    assert {"poisson", "negative_binomial", "zero_inflated_poisson"}.issubset(
        set(analysis.fits) | set(analysis.failed)
    )
