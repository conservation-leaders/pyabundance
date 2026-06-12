from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pyabundance import analyze_pcount, load_example_pcount, pcount, pcount_df, suggest_K
from pyabundance.k_selection import (
    KSuggestion,
    PCountKSensitivityResult,
    pcount_k_sensitivity,
)


def test_suggest_k_ignores_missing_and_returns_info():
    info = suggest_K([[1, np.nan, 8]], return_info=True)
    assert isinstance(info, KSuggestion)
    assert info.max_observed == 8
    assert info.K >= 58
    assert "Auto-selected K" in info.message


def test_suggest_k_rejects_non_integer_counts():
    with pytest.raises(ValueError, match="non-negative integers"):
        suggest_K(pd.DataFrame({"y1": [1.5]}))


def test_pcount_k_auto_sets_integer_result_and_warning():
    data = load_example_pcount("poisson", n_sites=20)
    fit = pcount(data.y, data.X, data.W, K="auto")
    assert isinstance(fit.K, int)
    assert fit.K >= int(np.nanmax(data.y))
    assert any("Auto-selected K" in warning for warning in (fit.warnings or []))


def test_pcount_df_and_analyze_pcount_k_auto():
    data = load_example_pcount("poisson", n_sites=20)
    fit = pcount_df(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest + elevation",
        detection_formula="~ visit - 1",
        K="auto",
    )
    assert isinstance(fit.K, int)
    assert any("Auto-selected K" in warning for warning in (fit.warnings or []))

    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest + elevation",
        detection_formula="~ visit - 1",
        K="auto",
        se=False,
    )
    assert isinstance(analysis.K, int)
    assert analysis.K_info is not None
    assert any("Auto-selected K" in warning for warning in analysis.warnings)


def _small_poisson_fit():
    data = load_example_pcount("poisson", n_sites=10)
    max_count = int(np.nanmax(data.y))
    fit = pcount(data.y, data.X, data.W, K=max_count + 5)
    return data, fit, max_count


def test_pcount_k_sensitivity_refits_and_orders_candidates():
    _, fit, max_count = _small_poisson_fit()
    result = pcount_k_sensitivity(fit, Ks=[max_count + 7, max_count + 3, max_count + 5])

    assert isinstance(result, PCountKSensitivityResult)
    assert result.reference_fit is fit
    assert result.table["K"].tolist() == [max_count + 3, max_count + 5, max_count + 7]
    assert set(result.fits) == set(result.table["K"].tolist())
    assert all(isinstance(refit, type(fit)) for refit in result.fits.values())
    assert result.best_K in result.fits
    assert result.best_fit is result.fits[result.best_K]


def test_pcount_k_sensitivity_table_columns_and_aic_delta():
    _, fit, max_count = _small_poisson_fit()
    result = pcount_k_sensitivity(fit, min_K=max_count + 2, max_K=max_count + 6, step=2)

    expected_columns = {
        "K",
        "logLik",
        "AIC",
        "delta_AIC",
        "n_params",
        "success",
        "message",
        "nfev",
        "nit",
        "max_abs_param_delta",
    }
    assert expected_columns.issubset(result.table.columns)
    assert result.table["K"].tolist() == [max_count + 2, max_count + 4, max_count + 6]
    aics = np.array([result.fits[int(K)].aic for K in result.table["K"]])
    assert np.allclose(result.table["AIC"], aics)
    assert np.allclose(result.table["delta_AIC"], aics - np.min(aics))
    assert result.table["n_params"].tolist() == [fit.params.size] * 3


def test_pcount_k_sensitivity_does_not_mutate_original_fit():
    _, fit, max_count = _small_poisson_fit()
    original_params = fit.params.copy()
    original_k = fit.K
    original_message = fit.message

    result = pcount_k_sensitivity(fit, Ks=[max_count + 3, max_count + 4])

    assert fit.K == original_k
    assert fit.message == original_message
    assert np.array_equal(fit.params, original_params)
    assert result.reference_fit is fit


def test_pcount_k_sensitivity_rejects_k_below_observed_maximum():
    _, fit, max_count = _small_poisson_fit()

    with pytest.raises(ValueError, match="max observed count"):
        pcount_k_sensitivity(fit, Ks=[max_count - 1, max_count + 2])


def test_pcount_k_sensitivity_rejects_empty_and_duplicate_k_lists():
    _, fit, max_count = _small_poisson_fit()

    with pytest.raises(ValueError, match="at least one"):
        pcount_k_sensitivity(fit, Ks=[])
    with pytest.raises(ValueError, match="duplicate K values"):
        pcount_k_sensitivity(fit, Ks=[max_count + 2, max_count + 3, max_count + 2])


def test_pcount_k_sensitivity_rejects_non_pcount_object():
    with pytest.raises(TypeError, match="PCountResult"):
        pcount_k_sensitivity(object(), Ks=[10])  # type: ignore[arg-type]


def test_pcount_k_sensitivity_preserves_formula_metadata_in_refits():
    data = load_example_pcount("poisson", n_sites=12)
    fit = pcount_df(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest + elevation",
        detection_formula="~ visit - 1",
        K=int(np.nanmax(data.y)) + 5,
    )

    result = pcount_k_sensitivity(fit, Ks=[fit.K, fit.K + 2])

    for refit in result.fits.values():
        assert refit.from_dataframe is True
        assert refit.abundance_formula == fit.abundance_formula
        assert refit.detection_formula == fit.detection_formula
        assert refit.abundance_column_names == fit.abundance_column_names
        assert refit.detection_column_names == fit.detection_column_names
        assert refit.site_ids == fit.site_ids
        assert refit.visit_labels == fit.visit_labels
        assert refit.data_info == fit.data_info


def test_pcount_k_sensitivity_not_added_to_top_level_all():
    import pyabundance

    assert "pcount_k_sensitivity" not in pyabundance.__all__
    assert "PCountKSensitivityResult" not in pyabundance.__all__
