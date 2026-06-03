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
    start = np.zeros(5, dtype=np.float64)
    py_fit = pcount(y, X, W, K=60, start=start, se=True, cov_method="bfgs")
    py_payload = {
        "status": "completed",
        "logLik": float(py_fit.loglik),
        "coefficients": py_fit.params.tolist(),
        "standard_errors": py_fit.standard_errors.tolist(),
        "coefficient_names": py_fit.param_names,
        "covariance_diagnostics": py_fit.covariance_diagnostics,
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "dataset": {"n_sites": int(y.shape[0]), "n_visits": int(y.shape[1]), "K": 60},
    }
    (REPORTS / "py_se_comparison.json").write_text(json.dumps(py_payload, indent=2) + "\n")

    r = load(REPORTS / "r_se_comparison.json")
    status = "PARTIAL"
    notes = [
        "This is a black-box comparison.",
        "SEs may differ because covariance approximations and optimizer paths differ.",
        "Do not treat this as a strict parity test.",
    ]
    r_loglik = None
    loglik_diff = None
    coef_comp = "not available"
    se_status = "not assessed"
    max_abs_se = None
    max_rel_se = None
    r_env = "not available"
    unmarked = "not available"
    if r is None:
        notes.append("R SE comparison was not run; reports/r_se_comparison.json is missing.")
    elif r.get("status") != "completed":
        notes.append(f"R SE comparison was not run: {r.get('message', 'no message')}")
        r_env = r.get("R_version", r_env)
    else:
        status = "COMPLETED"
        r_env = r.get("R_version", r_env)
        unmarked = r.get("unmarked_version", unmarked)
        r_loglik = float(r["logLik"])
        loglik_diff = abs(float(py_fit.loglik) - r_loglik)
        r_coef = np.asarray(r.get("coefficients", []), dtype=np.float64)
        r_se = np.asarray(r.get("standard_errors", []), dtype=np.float64)
        if r_coef.size == py_fit.params.size:
            max_coef_diff = np.max(np.abs(py_fit.params - r_coef))
            coef_comp = f"max absolute coefficient difference {max_coef_diff:.6g}"
        if r_se.size == py_fit.params.size and np.any(np.isfinite(r_se)):
            py_se = np.asarray(py_fit.standard_errors, dtype=np.float64)
            mask = np.isfinite(py_se) & np.isfinite(r_se)
            if np.any(mask):
                max_abs_se = float(np.max(np.abs(py_se[mask] - r_se[mask])))
                denom = np.maximum(np.abs(r_se[mask]), 1.0e-12)
                max_rel_se = float(np.max(np.abs(py_se[mask] - r_se[mask]) / denom))
                se_status = "compared"
        else:
            se_status = "R standard errors unavailable"

    report = f"""# R Standard Error Comparison

Status: {status}

Dataset:
- n_sites: {y.shape[0]}
- n_visits: {y.shape[1]}
- K: 60

Correctness:
- Python logLik: {fmt(float(py_fit.loglik))}
- R unmarked logLik: {fmt(r_loglik)}
- absolute logLik difference: {fmt(loglik_diff)}
- coefficient comparison: {coef_comp}

Standard errors:
- comparison status: {se_status}
- max absolute SE difference: {fmt(max_abs_se)}
- max relative SE difference: {fmt(max_rel_se)}
- notes: BFGS inverse-Hessian SEs are approximate and not required to match R exactly.

Environment:
- OS: {platform.platform()}
- Python: {sys.version.replace(chr(10), " ")}
- R: {r_env}
- unmarked: {unmarked}

Notes:
"""
    for note in notes:
        report += f"- {note}\n"
    (REPORTS / "SE_COMPARISON_R.md").write_text(report)


if __name__ == "__main__":
    main()
