from __future__ import annotations

from pyabundance import load_example_pcount, pcount_df


def test_posterior_abundance_dataframes_include_site_ids():
    data = load_example_pcount("poisson", n_sites=30, seed=213)
    fit = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        site_id_col="site_id",
        K=data.K,
    )

    summary = fit.posterior_abundance_dataframe()
    assert "site_id" in summary.columns
    assert {"posterior_mean", "lower", "upper"}.issubset(summary.columns)

    long = fit.posterior_abundance_dataframe(long=True)
    assert {"site_index", "site_id", "N", "probability"}.issubset(long.columns)
    assert long.shape[0] == 30 * (data.K + 1)

    abundance = fit.abundance_dataframe(include_posterior=True)
    assert {"predicted_lambda", "posterior_mean_N", "posterior_lower"}.issubset(abundance.columns)
