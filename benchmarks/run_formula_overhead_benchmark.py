from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DATA = ROOT / "data" / "benchmark"


def build_inputs() -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    counts = pd.read_csv(DATA / "pcount_counts.csv")
    covs = pd.read_csv(DATA / "pcount_site_covs.csv")
    site_data = pd.DataFrame(
        {
            "y1": counts["y1"].to_numpy(),
            "y2": counts["y2"].to_numpy(),
            "y3": counts["y3"].to_numpy(),
            "x": covs["x"].to_numpy(),
        }
    )
    y = counts[["y1", "y2", "y3"]].to_numpy(dtype=np.float64)
    x = covs["x"].to_numpy(dtype=np.float64)
    X = np.column_stack([np.ones(x.size), x]).astype(np.float64)
    W = np.zeros((x.size, 3, 3), dtype=np.float64)
    for visit in range(3):
        W[:, visit, visit] = 1.0
    return y, X, W, site_data


def main() -> None:
    from pyabundance import __version__, pcount, pcount_df

    y, X, W, site_data = build_inputs()
    start = np.zeros(5, dtype=np.float64)
    matrix_seconds: list[float] = []
    formula_seconds: list[float] = []
    matrix_fits = []
    formula_fits = []
    for _ in range(3):
        t0 = time.perf_counter()
        matrix_fits.append(pcount(y, X, W, K=60, start=start, method="BFGS"))
        matrix_seconds.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        formula_fits.append(
            pcount_df(
                site_data=site_data,
                count_cols=["y1", "y2", "y3"],
                abundance_formula="~ x",
                detection_formula="~ visit - 1",
                K=60,
                start=start,
                method="BFGS",
            )
        )
        formula_seconds.append(time.perf_counter() - t0)

    matrix_fit = matrix_fits[-1]
    formula_fit = formula_fits[-1]
    matrix_median = float(np.median(matrix_seconds))
    formula_median = float(np.median(formula_seconds))
    loglik_diff = abs(float(matrix_fit.loglik) - float(formula_fit.loglik))
    coef_diff = float(np.max(np.abs(matrix_fit.params - formula_fit.params)))
    payload = {
        "status": "completed",
        "matrix_seconds": matrix_seconds,
        "formula_seconds": formula_seconds,
        "matrix_median_seconds": matrix_median,
        "formula_median_seconds": formula_median,
        "formula_overhead_seconds": formula_median - matrix_median,
        "formula_matrix_ratio": formula_median / matrix_median,
        "matrix_logLik": float(matrix_fit.loglik),
        "formula_logLik": float(formula_fit.loglik),
        "absolute_logLik_difference": loglik_diff,
        "max_coefficient_absolute_difference": coef_diff,
        "python_version": sys.version.replace("\n", " "),
        "pyabundance_version": __version__,
        "platform": platform.platform(),
        "dataset": {
            "n_sites": int(y.shape[0]),
            "n_visits": int(y.shape[1]),
            "K": 60,
            "repetitions": 3,
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "formula_overhead_benchmark.json").write_text(json.dumps(payload, indent=2) + "\n")
    report = f"""# Formula API Overhead Benchmark

Status: COMPLETED

Dataset:
- n_sites: {y.shape[0]}
- n_visits: {y.shape[1]}
- K: 60
- repetitions: 3

Correctness:
- matrix API logLik: {matrix_fit.loglik:.6g}
- formula API logLik: {formula_fit.loglik:.6g}
- absolute logLik difference: {loglik_diff:.6g}
- max coefficient absolute difference: {coef_diff:.6g}

Performance:
- matrix API median fit time: {matrix_median:.6g}
- formula API median fit time: {formula_median:.6g}
- formula overhead: {formula_median - matrix_median:.6g}
- formula/matrix ratio: {formula_median / matrix_median:.6g}

Notes:
- This measures convenience-layer overhead, not Rust likelihood speed.
- Matrix API remains the lowest-overhead path.
- Do not invent results.
"""
    (REPORTS / "FORMULA_OVERHEAD_BENCHMARK.md").write_text(report)


if __name__ == "__main__":
    main()
