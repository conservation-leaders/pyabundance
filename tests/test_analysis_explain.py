from __future__ import annotations

from pyabundance import analyze_pcount, load_example_pcount


def test_analysis_explain_is_deterministic_and_cautious():
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
    first = analysis.explain()
    second = analysis.explain()
    assert first == second
    assert analysis.best_model_name in first
    assert "ZIP models can be weakly identified" in first
    assert "Posterior abundance summaries condition on fitted parameters" in first
    assert "Inspect" in first
