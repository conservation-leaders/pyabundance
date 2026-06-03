from __future__ import annotations

from pyabundance import compare_models, load_example_pcount, pcount_df


def main() -> None:
    data = load_example_pcount("poisson", n_sites=60, seed=20260612)
    poisson = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula="~ visit - 1",
        mixture="poisson",
        K=data.K,
        se=True,
    )
    intercept = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula="~ visit - 1",
        mixture="poisson",
        K=data.K,
    )
    comparison = compare_models({"poisson_x": poisson, "poisson_intercept": intercept})
    ranef = poisson.ranef().head()
    total = poisson.total_abundance_posterior(nsim=200, seed=123)
    print("pyabundance external alpha smoke")
    print(comparison.summary())
    print(poisson.coef_table().head())
    print(ranef)
    print(total.summary())
    print(poisson.to_markdown(include_posterior_abundance=True).splitlines()[0])


if __name__ == "__main__":
    main()
