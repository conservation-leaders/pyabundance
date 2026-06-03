from __future__ import annotations

import cProfile
import io
import pstats
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
    from pyabundance import pcount

    y, X, W = build_designs()
    profiler = cProfile.Profile()
    profiler.enable()
    fit = pcount(y, X, W, K=60, start=np.zeros(5), method="BFGS", se=False)
    profiler.disable()

    stream = io.StringIO()
    stream.write("pyabundance Python fit profile\n")
    stream.write(f"success: {fit.success}\n")
    stream.write(f"message: {fit.message}\n")
    stream.write(f"logLik: {fit.loglik}\n")
    stream.write(f"method: {fit.method}\n")
    stream.write(f"nfev: {fit.nfev}\n")
    stream.write(f"nit: {fit.nit}\n\n")
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumtime")
    stats.print_stats(30)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "profile_py_fit.txt").write_text(stream.getvalue())


if __name__ == "__main__":
    main()
