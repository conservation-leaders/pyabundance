"""Guided pcount analysis quickstart for pyabundance."""

from pyabundance import analyze_pcount, load_example_pcount


def main() -> None:
    data = load_example_pcount("poisson", n_sites=30)
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
    print(analysis.summary())
    print(analysis.explain())


if __name__ == "__main__":
    main()
