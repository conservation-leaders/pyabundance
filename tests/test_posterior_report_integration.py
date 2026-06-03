from __future__ import annotations

import json

import numpy as np
from pyabundance import pcount, simulate_pcount


def test_report_includes_posterior_and_excludes_internal_problem(tmp_path):
    X = np.ones((20, 1), dtype=np.float64)
    W = np.ones((20, 2, 1), dtype=np.float64)
    y = simulate_pcount(X, W, beta=[0.2], alpha=[-0.3], seed=214)
    fit = pcount(y, X, W, K=25)

    report = fit.to_report(include_posterior_abundance=True)
    assert "posterior_abundance" in report
    assert "_problem" not in json.dumps(report, default=str)

    markdown = fit.to_markdown(include_posterior_abundance=True)
    assert "Posterior abundance" in markdown
    assert "conditions on fitted parameters" in markdown

    out = tmp_path / "report.json"
    fit.export_summary(out, include_posterior_abundance=True)
    loaded = json.loads(out.read_text())
    assert "posterior_abundance" in loaded
