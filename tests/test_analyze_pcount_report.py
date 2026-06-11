from __future__ import annotations

import json

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
    assert text.count("## AIC table") == 1
    assert "AIC table:" not in text
    assert text.count("## Warnings") <= 1
    assert analysis.K_info is not None
    assert text.count(analysis.K_info.message) == 1
    for heading in [
        "## Summary",
        "## Candidate models",
        "## Explanation",
        "## K selection",
        "## AIC table",
        "## Best model",
    ]:
        assert heading in text


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


def test_analyze_pcount_json_serializes_k_info_structurally(tmp_path):
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
    payload = json.loads(analysis.to_json())
    assert payload["K_info"]["K"] == analysis.K
    assert payload["K_info"]["max_observed"] >= 0
    assert "Auto-selected K" in payload["K_info"]["message"]

    path = tmp_path / "analysis.json"
    analysis.to_json(path)
    file_payload = json.loads(path.read_text(encoding="utf-8"))
    assert file_payload["K_info"] == payload["K_info"]


def test_analyze_pcount_json_serializes_explicit_k_info_as_none():
    data = load_example_pcount("poisson", n_sites=12)
    analysis = analyze_pcount(
        site_data=data.site_data,
        obs_data=data.obs_data,
        site_id_col="site_id",
        count_cols=data.count_cols,
        abundance_formula="~ forest",
        detection_formula="~ visit - 1",
        K=60,
        se=False,
        mixtures=("poisson",),
    )
    payload = json.loads(analysis.to_json())
    assert payload["K_info"] is None
