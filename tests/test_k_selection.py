from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pyabundance import analyze_pcount, load_example_pcount, pcount, pcount_df, suggest_K
from pyabundance.k_selection import KSuggestion


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
