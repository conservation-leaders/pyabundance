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
PY_FIT = REPORTS / "py_zip_benchmark.json"
TRUE_PARAMS = DATA / "pcount_zip_true_params.json"


def build_designs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = pd.read_csv(DATA / "pcount_zip_counts.csv")
    covs = pd.read_csv(DATA / "pcount_zip_site_covs.csv")
    y = counts[["y1", "y2", "y3"]].to_numpy(dtype=np.float64)
    x = covs["x"].to_numpy(dtype=np.float64)
    X = np.column_stack([np.ones(x.size), x]).astype(np.float64)
    W = np.zeros((x.size, 3, 3), dtype=np.float64)
    for visit in range(3):
        W[:, visit, visit] = 1.0
    return y, X, W


def load_theta() -> tuple[np.ndarray, str]:
    if PY_FIT.exists():
        fit = json.loads(PY_FIT.read_text())
        if fit.get("status") == "completed" and fit.get("params"):
            return np.asarray(fit["params"], dtype=np.float64), "fitted"
    truth = json.loads(TRUE_PARAMS.read_text())
    theta = np.asarray(
        truth["beta"] + truth["detection_logits"] + [truth["logit_psi"]], dtype=np.float64
    )
    return theta, "true"


def main() -> None:
    from pyabundance import __rust_version__, __version__, _core

    y, X, W = build_designs()
    theta, theta_source = load_theta()
    problem = _core.PCountZIPProblem(y, X, W, 100)
    repetitions = 1000
    warmups = 20
    for _ in range(warmups):
        problem.loglik(theta)
    timings = []
    loglik = float("nan")
    for _ in range(repetitions):
        t0 = time.perf_counter_ns()
        loglik = float(problem.loglik(theta))
        timings.append(time.perf_counter_ns() - t0)
    median_ns = float(np.median(timings))
    payload = {
        "status": "completed",
        "repetitions": repetitions,
        "warmups": warmups,
        "theta_source": theta_source,
        "theta": theta.tolist(),
        "logLik": loglik,
        "median_seconds": median_ns / 1_000_000_000.0,
        "median_nanoseconds": median_ns,
        "median_microseconds": median_ns / 1_000.0,
        "median_milliseconds": median_ns / 1_000_000.0,
        "python_version": sys.version.replace("\n", " "),
        "pyabundance_version": __version__,
        "rust_package_version": __rust_version__,
        "platform": platform.platform(),
        "dataset": {"n_sites": int(y.shape[0]), "n_visits": int(y.shape[1]), "K": 100},
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "py_zip_loglik_benchmark.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
