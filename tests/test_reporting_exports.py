from __future__ import annotations

import json

import numpy as np
from pyabundance import export_model_report, model_report, pcount, simulate_pcount


def test_model_report_and_exports(tmp_path):
    rng = np.random.default_rng(103)
    X = np.column_stack([np.ones(35), rng.normal(size=35)])
    W = np.ones((35, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.1, 0.2], alpha=[-0.4], seed=104)
    fit = pcount(y, X, W, K=30, se=True)

    report = model_report(fit)
    assert report["mixture"] == "poisson"
    assert "coefficients" in report
    assert "diagnostics" in report

    json_path = tmp_path / "report.json"
    md_path = tmp_path / "report.md"
    csv_path = tmp_path / "coef.csv"
    export_model_report(fit, json_path)
    fit.export_summary(md_path)
    fit.export_summary(csv_path)

    assert json.loads(json_path.read_text())["mixture"] == "poisson"
    assert "pyabundance model report" in md_path.read_text()
    assert "parameter" in csv_path.read_text()
