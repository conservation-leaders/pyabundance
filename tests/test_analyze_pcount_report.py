from __future__ import annotations

from pyabundance import analyze_pcount, load_example_pcount


def test_analyze_pcount_report_and_export(tmp_path):
    data = load_example_pcount("poisson", n_sites=20)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K="auto",
        se=False,
    )
    text = analysis.report()
    assert "AIC table" in text
    assert "Explanation" in text
    assert "Best model" in text
    assert "Coefficients" in text
    assert "K selection" in text
    path = tmp_path / "abundance_report.md"
    analysis.export_report(path)
    assert path.read_text().startswith("# pyabundance guided pcount analysis")
    assert "best_model_name" in analysis.to_json()


def test_analyze_pcount_report_can_include_posterior_abundance():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K="auto",
        se=False,
        mixtures=("poisson",),
    )
    text = analysis.to_markdown(include_posterior_abundance=True)
    assert "Posterior abundance" in text
    assert "condition on fitted parameters" in text
