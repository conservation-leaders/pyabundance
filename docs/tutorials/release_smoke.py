"""Small release smoke script used by contributors after installing a wheel."""

from __future__ import annotations

from pyabundance import compare_models, load_example_pcount, pcount_df


def main() -> None:
    data = load_example_pcount("poisson", n_sites=60, seed=20260609)
    fit = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K=data.K,
        se=True,
    )
    comparison = compare_models({"poisson": fit})
    assert comparison.best_model.success
    assert fit.posterior_abundance().shape[0] == 60
    print(comparison.summary())


if __name__ == "__main__":
    main()
