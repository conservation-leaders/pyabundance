from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "benchmark"
REPORTS = ROOT / "reports"


def load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def fmt(value: Any) -> str:
    if value is None:
        return "not available"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def build_designs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = pd.read_csv(DATA / "pcount_counts.csv")
    covs = pd.read_csv(DATA / "pcount_site_covs.csv")
    y = counts[["y1", "y2", "y3"]].to_numpy(dtype=np.float64)
    x = covs["x"].to_numpy(dtype=np.float64)
    X = np.column_stack([np.ones(x.size), x]).astype(np.float64)
    W = np.zeros((x.size, 3, 3), dtype=np.float64)
    for visit in range(3):
        W[:, visit, visit] = 1.0
    return y, X, W


def main() -> None:
    from pyabundance import pcount

    REPORTS.mkdir(parents=True, exist_ok=True)
    y, X, W = build_designs()
    fit = pcount(y, X, W, K=60, start=np.zeros(5))
    summary = fit.posterior_abundance_summary()
    r = load(REPORTS / "r_ranef_comparison.json")
    status = "PARTIAL"
    r_loglik = None
    loglik_diff = None
    mean_diff = None
    mode_diff = None
    comparison_status = "not assessed"
    r_env = "not available"
    unmarked = "not available"
    notes = [
        "This is a black-box comparison against unmarked ranef-style outputs.",
        "Posterior abundance here conditions on fitted parameters.",
        "Empirical-Bayes intervals do not include full parameter uncertainty.",
        "Do not treat this as a strict parity test if extraction methods differ.",
    ]
    if r is None:
        notes.append("R ranef comparison was not run; reports/r_ranef_comparison.json is missing.")
    elif r.get("status") != "completed":
        notes.append(f"R ranef comparison was {r.get('status')}: {r.get('message', 'no message')}")
        r_loglik = r.get("logLik")
        r_env = r.get("R_version", r_env)
        unmarked = r.get("unmarked_version", unmarked)
    else:
        status = "COMPLETED"
        r_loglik = float(r["logLik"])
        loglik_diff = abs(float(fit.loglik) - r_loglik)
        r_env = r.get("R_version", r_env)
        unmarked = r.get("unmarked_version", unmarked)
        r_means = np.asarray(r.get("posterior_means", []), dtype=np.float64)
        r_modes = np.asarray(r.get("posterior_modes", []), dtype=np.float64)
        py_means = summary["posterior_mean"].to_numpy(dtype=np.float64)
        py_modes = summary["posterior_mode"].to_numpy(dtype=np.float64)
        if r_means.size == py_means.size:
            mean_diff = float(np.max(np.abs(py_means - r_means)))
            comparison_status = "posterior means compared"
        if r_modes.size == py_modes.size and np.any(np.isfinite(r_modes)):
            mode_diff = float(np.nanmax(np.abs(py_modes - r_modes)))

    report = f"""# R Ranef / Posterior Abundance Comparison

Status: {status}

Dataset:
- n_sites: {y.shape[0]}
- n_visits: {y.shape[1]}
- K: 60

Correctness:
- Python logLik: {fmt(float(fit.loglik))}
- R unmarked logLik: {fmt(r_loglik)}
- absolute logLik difference: {fmt(loglik_diff)}

Posterior abundance:
- comparison status: {comparison_status}
- max absolute posterior mean difference: {fmt(mean_diff)}
- max posterior mode difference: {fmt(mode_diff)}
- notes: ranef extraction and summaries can differ across packages; comparison is non-strict.

Environment:
- OS: {platform.platform()}
- Python: {sys.version.replace(chr(10), " ")}
- R: {r_env}
- unmarked: {unmarked}

Notes:
"""
    for note in notes:
        report += f"- {note}\n"
    (REPORTS / "RANEF_COMPARISON_R.md").write_text(report)


if __name__ == "__main__":
    main()
