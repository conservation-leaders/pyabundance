"""End-to-end pcount tutorial script for documentation and smoke testing."""

from __future__ import annotations

from pyabundance import aic_table, load_example_pcount, pcount_df


def main() -> None:
    data = load_example_pcount("poisson", n_sites=120, seed=20260608)
    fits = {
        "poisson": pcount_df(
            site_data=data.site_data,
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            K=data.K,
            mixture="poisson",
            se=True,
        ),
        "negative_binomial": pcount_df(
            site_data=data.site_data,
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            K=100,
            mixture="negative_binomial",
        ),
        "zip": pcount_df(
            site_data=data.site_data,
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            K=100,
            mixture="zero_inflated_poisson",
        ),
    }
    print(aic_table(fits))
    best = fits["poisson"]
    print(best.coef_table())
    print(best.ranef().head())
    print(best.total_abundance_posterior(nsim=200, seed=1).summary())
    print(best.posterior_predictive_check(statistic="zero_count", nsim=50, seed=2))


if __name__ == "__main__":
    main()
