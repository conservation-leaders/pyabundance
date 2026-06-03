from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "benchmark"
REPORTS = ROOT / "reports"


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


def fmt(value: Any) -> str:
    if value is None:
        return "not run"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def main() -> None:
    from pyabundance import __version__, pcount

    y, X, W = build_designs()
    start = np.zeros(5, dtype=np.float64)
    REPORTS.mkdir(parents=True, exist_ok=True)

    no_se_seconds = []
    bfgs_seconds = []
    for _ in range(3):
        t0 = time.perf_counter()
        pcount(y, X, W, K=60, start=start, se=False)
        no_se_seconds.append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        bfgs_fit = pcount(y, X, W, K=60, start=start, se=True, cov_method="bfgs")
        bfgs_seconds.append(time.perf_counter() - t0)

    finite_seconds = []
    finite_fit = None
    finite_status = "completed"
    try:
        t0 = time.perf_counter()
        finite_fit = pcount(y, X, W, K=60, start=start, se=True, cov_method="finite_difference")
        finite_seconds.append(time.perf_counter() - t0)
    except Exception as exc:  # pragma: no cover - benchmark environment dependent
        finite_status = f"not_run: {exc}"

    t0 = time.perf_counter()
    bfgs_fit.parametric_bootstrap(nsim=20, statistic="sse", seed=20260603)
    bootstrap_seconds = time.perf_counter() - t0

    fit_for_outputs = finite_fit or bfgs_fit
    se = fit_for_outputs.standard_errors
    warnings = list(fit_for_outputs.warnings or [])
    warnings.extend(fit_for_outputs.covariance_diagnostics.get("warnings", []))
    payload = {
        "status": "completed",
        "fit_without_se_seconds": no_se_seconds,
        "fit_with_bfgs_seconds": bfgs_seconds,
        "fit_with_finite_difference_seconds": finite_seconds,
        "finite_difference_status": finite_status,
        "median_without_se_seconds": float(np.median(no_se_seconds)),
        "median_bfgs_seconds": float(np.median(bfgs_seconds)),
        "finite_difference_seconds": float(finite_seconds[0]) if finite_seconds else None,
        "bootstrap_nsim": 20,
        "bootstrap_seconds": float(bootstrap_seconds),
        "covariance_method": fit_for_outputs.cov_method,
        "covariance_status": fit_for_outputs.covariance_diagnostics,
        "n_params": int(fit_for_outputs.params.size),
        "finite_se_count": int(np.sum(np.isfinite(se))) if se is not None else 0,
        "max_finite_se": (
            float(np.nanmax(se)) if se is not None and np.any(np.isfinite(se)) else None
        ),
        "warnings": warnings,
        "python_version": sys.version.replace("\n", " "),
        "pyabundance_version": __version__,
        "platform": platform.platform(),
        "dataset": {"n_sites": int(y.shape[0]), "n_visits": int(y.shape[1]), "K": 60},
    }
    (REPORTS / "uncertainty_benchmark.json").write_text(json.dumps(payload, indent=2) + "\n")
    report = f"""# Uncertainty Benchmark

Status: COMPLETED

Dataset:
- n_sites: {y.shape[0]}
- n_visits: {y.shape[1]}
- K: 60

Runtime:
- fit without SE: {np.median(no_se_seconds):.6g}
- fit with BFGS covariance: {np.median(bfgs_seconds):.6g}
- fit with finite-difference covariance: {fmt(payload["finite_difference_seconds"])}
- parametric bootstrap nsim: 20
- parametric bootstrap time: {bootstrap_seconds:.6g}

Outputs:
- covariance method: {fit_for_outputs.cov_method}
- covariance status: {"available" if fit_for_outputs.has_covariance else "unavailable"}
- number of parameters: {fit_for_outputs.params.size}
- finite SE count: {payload["finite_se_count"]}
- warnings: {warnings if warnings else "none"}

Notes:
- This benchmark measures uncertainty overhead, not raw likelihood speed.
- Bootstrap runtime scales approximately with nsim and refit cost.
- Do not invent results.
"""
    (REPORTS / "UNCERTAINTY_BENCHMARK.md").write_text(report)


if __name__ == "__main__":
    main()
