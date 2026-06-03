from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "benchmark"
REPORTS = ROOT / "reports"


def _design(prefix: str = "pcount") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    counts = pd.read_csv(DATA / f"{prefix}_counts.csv")
    covs = pd.read_csv(DATA / f"{prefix}_site_covs.csv")
    y = counts[["y1", "y2", "y3"]].to_numpy(dtype=np.float64)
    x = covs["x"].to_numpy(dtype=np.float64)
    X = np.column_stack([np.ones(x.size), x]).astype(np.float64)
    W = np.zeros((x.size, 3, 3), dtype=np.float64)
    for visit in range(3):
        W[:, visit, visit] = 1.0
    return y, X, W


def _time(callable_obj):
    t0 = time.perf_counter()
    value = callable_obj()
    return value, time.perf_counter() - t0


def _run_model(name: str, prefix: str, mixture: str, k: int, start_len: int) -> dict[str, Any]:
    from pyabundance import pcount

    y, X, W = _design(prefix)
    start = np.zeros(start_len, dtype=np.float64)
    if mixture == "zero_inflated_poisson":
        start[-1] = np.log(0.2 / 0.8)
    fit = pcount(y, X, W, K=k, mixture=mixture, start=start)
    posterior, matrix_seconds = _time(fit.posterior_abundance)
    summary, summary_seconds = _time(fit.posterior_abundance_summary)
    samples, sampling_seconds = _time(lambda: fit.posterior_abundance_samples(nsim=1000, seed=1))
    total, total_seconds = _time(lambda: fit.total_abundance_posterior(nsim=1000, seed=1))
    return {
        "model": name,
        "status": "completed",
        "posterior_matrix_seconds": matrix_seconds,
        "summary_seconds": summary_seconds,
        "sampling_seconds": sampling_seconds,
        "total_abundance_seconds": total_seconds,
        "posterior_matrix_shape": list(posterior.shape),
        "row_sum_max_error": float(np.max(np.abs(posterior.sum(axis=1) - 1.0))),
        "summary_rows": int(summary.shape[0]),
        "samples_shape": list(samples.shape),
        "total_mean": total.mean,
        "total_lower": total.lower,
        "total_upper": total.upper,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = {
        "poisson": _run_model("Poisson", "pcount", "poisson", 60, 5),
        "negative_binomial": _run_model(
            "Negative-binomial", "pcount_nb", "negative_binomial", 100, 6
        ),
        "zero_inflated_poisson": _run_model(
            "Zero-inflated Poisson", "pcount_zip", "zero_inflated_poisson", 100, 6
        ),
    }
    payload = {"status": "completed", "models": results}
    (REPORTS / "posterior_abundance_benchmark.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    lines = ["# Posterior Abundance Benchmark", "", "Status: COMPLETED", "", "Models:"]
    for key, label in [
        ("poisson", "Poisson"),
        ("negative_binomial", "Negative-binomial"),
        ("zero_inflated_poisson", "Zero-inflated Poisson"),
    ]:
        item = results[key]
        lines.extend(
            [
                f"- {label}:",
                f"  - posterior matrix time: {_fmt(item['posterior_matrix_seconds'])}",
                f"  - summary time: {_fmt(item['summary_seconds'])}",
                f"  - sampling time: {_fmt(item['sampling_seconds'])}",
                f"  - total abundance time: {_fmt(item['total_abundance_seconds'])}",
                f"  - posterior matrix shape: {item['posterior_matrix_shape']}",
                f"  - row-sum max error: {_fmt(item['row_sum_max_error'])}",
            ]
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- This benchmark measures posterior abundance post-processing, not model fitting.",
            "- Posterior abundance conditions on fitted parameters.",
            "- Do not invent results.",
        ]
    )
    (REPORTS / "POSTERIOR_ABUNDANCE_BENCHMARK.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
