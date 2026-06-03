from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test an already installed pyabundance package."
    )
    parser.add_argument("--expected-version", default=None)
    args = parser.parse_args()
    from pyabundance import (
        __version__,
        compare_models,
        load_example_pcount,
        model_report,
        pcount_df,
        report_markdown,
    )

    if args.expected_version and __version__ != args.expected_version:
        raise AssertionError(f"expected pyabundance {args.expected_version}, got {__version__}")
    data = load_example_pcount("poisson", n_sites=20, seed=20260609)
    fit_a = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K=data.K,
    )
    fit_b = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula=data.detection_formula,
        K=data.K,
    )
    assert fit_a.success, fit_a.message
    assert fit_a.posterior_abundance().shape == (20, data.K + 1)
    report = model_report(fit_a)
    assert report["mixture"] == "poisson"
    assert "# pyabundance model report" in report_markdown(fit_a)
    assert compare_models({"x": fit_a, "intercept": fit_b}).table.shape[0] == 2
    print(f"pyabundance {__version__} installed-package smoke test passed")


if __name__ == "__main__":
    main()
