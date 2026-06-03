from __future__ import annotations

from pyabundance import aic_table, load_example_pcount, pcount_df

example = load_example_pcount("poisson", n_sites=120, seed=20260606)

fit_p = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula=example.abundance_formula,
    detection_formula=example.detection_formula,
    mixture="poisson",
    K=example.K,
)
fit_nb = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula=example.abundance_formula,
    detection_formula=example.detection_formula,
    mixture="negative_binomial",
    K=100,
)
fit_zip = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula=example.abundance_formula,
    detection_formula=example.detection_formula,
    mixture="zero_inflated_poisson",
    K=100,
)

print(aic_table({"poisson": fit_p, "negative_binomial": fit_nb, "zip": fit_zip}))
