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
    from pyabundance import __rust_version__, __version__, pcount

    y, X, W = build_designs()
    start = np.zeros(5, dtype=np.float64)
    seconds: list[float] = []
    fits = []
    for _ in range(3):
        t0 = time.perf_counter()
        fit = pcount(y, X, W, K=60, start=start, method="BFGS", se=False)
        seconds.append(time.perf_counter() - t0)
        fits.append(fit)
    fit = fits[-1]
    payload = {
        "status": "completed",
        "seconds": seconds,
        "median_seconds": float(np.median(seconds)),
        "logLik": float(fit.loglik),
        "params": fit.params.tolist(),
        "success": bool(fit.success),
        "message": fit.message,
        "python_version": sys.version.replace("\n", " "),
        "pyabundance_version": __version__,
        "rust_package_version": __rust_version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "dataset": {
            "n_sites": int(y.shape[0]),
            "n_visits": int(y.shape[1]),
            "K": 60,
            "repetitions": 3,
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "py_benchmark.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
