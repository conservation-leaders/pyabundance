from __future__ import annotations

from pyabundance import list_example_datasets, load_example_pcount, pcount_df


def test_example_datasets_load_and_fit_poisson():
    assert set(list_example_datasets()) == {"poisson", "negative_binomial", "zip"}
    data = load_example_pcount("poisson", n_sites=40, seed=107)
    assert data.site_data.shape[0] == 40
    assert data.y.shape == (40, 3)
    assert data.X.shape[0] == 40
    fit = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K=data.K,
    )
    assert fit.success
    assert fit.from_dataframe
    assert "forest" in fit.param_names
