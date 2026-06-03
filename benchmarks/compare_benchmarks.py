from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PY_JSON = REPORTS / "py_benchmark.json"
R_JSON = REPORTS / "r_benchmark.json"
LOGLIK_JSON = REPORTS / "py_loglik_benchmark.json"
PY_PREFLIGHT_JSON = REPORTS / "py_benchmark_v0.1_preflight.json"
OUT = REPORTS / "BENCHMARK_RESULTS.md"
PERF_NOTES = REPORTS / "PERFORMANCE_NOTES.md"
TRUE_JSON = ROOT / "data" / "benchmark" / "pcount_true_params.json"


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


def rust_version() -> str:
    try:
        return subprocess.check_output(["rustc", "--version"], text=True).strip()
    except Exception:
        return "not available"


def bottleneck_note(py: dict[str, Any] | None, loglik: dict[str, Any] | None) -> str:
    if not py or py.get("status") != "completed":
        return "Python full-fit benchmark did not complete, so bottleneck was not assessed."
    if not loglik or loglik.get("status") != "completed":
        return "Direct likelihood benchmark did not complete, so bottleneck was not assessed."
    nfev = py.get("nfev")
    fit_seconds = py.get("median_seconds")
    loglik_ms = loglik.get("median_milliseconds")
    if not nfev or fit_seconds is None or loglik_ms is None:
        return "Missing nfev or direct likelihood timing, so bottleneck was not assessed."
    implied = float(nfev) * float(loglik_ms) / 1000.0
    share = implied / float(fit_seconds) if fit_seconds else None
    if share is not None and share > 0.75:
        return (
            "Bottleneck appears dominated by optimizer likelihood calls: "
            f"nfev × direct likelihood median ≈ {implied:.3g}s "
            f"({share:.1%} of median fit time)."
        )
    return (
        "Bottleneck appears mixed between optimizer orchestration and likelihood calls: "
        f"nfev × direct likelihood median ≈ {implied:.3g}s."
    )


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    py = load(PY_JSON)
    r = load(R_JSON)
    loglik = load(LOGLIK_JSON)
    preflight = load(PY_PREFLIGHT_JSON)
    truth = load(TRUE_JSON) or {}
    dataset = (py or {}).get("dataset") or (r or {}).get("dataset") or truth

    status = "NOT RUN"
    notes = [
        "This is a simple end-to-end fit benchmark, not a comprehensive benchmark.",
        "Optimizer implementations and convergence paths may differ.",
    ]
    py_loglik = r_loglik = abs_loglik_diff = max_coef_diff = None
    py_seconds = r_seconds = speed_ratio = None
    py_nfev = py_nit = None
    py_method = py_message = None
    direct_loglik_ms = direct_loglik_us = None
    parity_status = "not assessed"
    r_env = "not available"
    unmarked_env = "not available"

    if py is None:
        notes.append("Python benchmark was not run; reports/py_benchmark.json is missing.")
    elif py.get("status") != "completed":
        notes.append(f"Python benchmark did not complete: {py.get('message', 'no message')}")
    else:
        status = "PARTIAL"
        py_loglik = py.get("logLik")
        py_seconds = py.get("median_seconds")
        py_nfev = py.get("nfev")
        py_nit = py.get("nit")
        py_method = py.get("method")
        py_message = py.get("message")
        if not py.get("success", False):
            notes.append(f"Python optimizer reported non-success: {py.get('message')}")

    if loglik is None:
        notes.append("Python direct likelihood benchmark was not run.")
    elif loglik.get("status") == "completed":
        direct_loglik_ms = loglik.get("median_milliseconds")
        direct_loglik_us = loglik.get("median_microseconds")
    else:
        notes.append(
            f"Python direct likelihood benchmark did not complete: {loglik.get('message')}"
        )

    if r is None:
        notes.append("R benchmark was not run; reports/r_benchmark.json is missing.")
    elif r.get("status") != "completed":
        notes.append(f"R comparison was not run: {r.get('message', 'no message')}")
        r_env = r.get("R_version", r_env)
    else:
        r_env = r.get("R_version", r_env)
        unmarked_env = r.get("unmarked_version", unmarked_env)
        r_loglik = r.get("logLik")
        r_seconds = r.get("median_seconds")
        if py_loglik is not None:
            status = "COMPLETED"
            abs_loglik_diff = abs(float(py_loglik) - float(r_loglik))
            py_params = py.get("params", [])
            r_params = r.get("coefficients", [])
            if len(py_params) == len(r_params):
                max_coef_diff = max(
                    abs(float(a) - float(b)) for a, b in zip(py_params, r_params, strict=True)
                )
            if py_seconds and r_seconds:
                speed_ratio = float(r_seconds) / float(py_seconds)
            parity_status = (
                "close"
                if abs_loglik_diff < 1.0e-5 and (max_coef_diff is None or max_coef_diff < 1.0e-4)
                else "differs"
            )

    if r is None or (r and r.get("status") != "completed"):
        notes.append(
            "R was unavailable, unmarked could not be installed, or the R benchmark was "
            "skipped/failed; no R parity numbers are invented."
        )
    notes.append(bottleneck_note(py, loglik))

    text = f"""Benchmark Results
Status: {status}
Dataset:
\t•\tn_sites: {fmt(dataset.get("n_sites"))}
\t•\tn_visits: {fmt(dataset.get("n_visits"))}
\t•\tK: {fmt(dataset.get("K"))}
\t•\trepetitions: {fmt(dataset.get("repetitions", 3 if py else None))}
Correctness:
\t•\tPython logLik: {fmt(py_loglik)}
\t•\tR unmarked logLik: {fmt(r_loglik)}
\t•\tabsolute logLik difference: {fmt(abs_loglik_diff)}
\t•\tmax coefficient absolute difference: {fmt(max_coef_diff)}
\t•\tparity status: {parity_status}
Performance:
\t•\tPython full fit median time: {fmt(py_seconds)}
\t•\tR full fit median time: {fmt(r_seconds)}
\t•\tspeed ratio R/Python: {fmt(speed_ratio)}
\t•\tPython optimizer method: {fmt(py_method)}
\t•\tPython function evaluations: {fmt(py_nfev)}
\t•\tPython optimizer iterations: {fmt(py_nit)}
\t•\tPython optimizer message: {fmt(py_message)}
\t•\tPython direct likelihood median time: {fmt(direct_loglik_ms)} ms ({fmt(direct_loglik_us)} µs)
Environment:
\t•\tOS: {platform.platform()}
\t•\tCPU if available: {platform.processor() or platform.machine() or "not available"}
\t•\tPython: {(py or {}).get("python_version", "not available")}
\t•\tRust: {rust_version()}
\t•\tR: {r_env}
\t•\tunmarked: {unmarked_env}
Notes:
"""
    for note in notes:
        text += f"\t•\t{note}\n"
    OUT.write_text(text)

    before = preflight.get("median_seconds") if preflight else None
    after = py_seconds
    before_label = "v0.1 pre-flight local run" if before is not None else "not available"
    after_label = "v0.1.1 current local run" if after is not None else "not available"
    if py_seconds is not None and r_seconds is not None:
        r_faster = "yes" if r_seconds < py_seconds else "no"
    else:
        r_faster = "not assessed"
    preflight_r = load(REPORTS / "r_benchmark_v0.1_preflight.json") or {}
    preflight_r_seconds = preflight_r.get("median_seconds")
    before_row = (
        f"| {before_label} | {fmt(before)} s | {fmt(preflight_r_seconds)} s | "
        f"{fmt((preflight or {}).get('nfev'))} | not available |"
    )
    after_row = (
        f"| {after_label} | {fmt(after)} s | {fmt(r_seconds)} s | "
        f"{fmt(py_nfev)} | {fmt(direct_loglik_ms)} ms |"
    )

    perf = f"""# Performance Notes

## What was profiled

- Full Python `pcount(..., method="BFGS")` fit on the synthetic 500-site, 3-visit, K=60 dataset.
- Direct Rust-backed Poisson N-mixture likelihood through `_core.PCountPoissonProblem.loglik`.
- One Python cProfile fit, written separately to `reports/profile_py_fit.txt`.
- Optional black-box R `unmarked::pcount` comparison when R/unmarked is available.

## What changed

- Added `_core.PCountPoissonProblem(y, X, W, K)` to validate and cache fixed problem data once.
- Precomputed count validity, missing-observation structures, site maximum observed counts,
  and log-factorials from 0..K.
- Updated Python `pcount()` to reuse the cached problem object for optimizer objective calls.
- Reduced repeated per-site allocation and count parsing in the hot Rust likelihood path.
- Added optimizer method, function evaluation count, iteration count, success, and message
  reporting.
- Added direct likelihood benchmarking and a short cProfile report.

## Before/after benchmark table

| Run | Python+Rust median fit time | R median fit time | Python nfev | Direct likelihood median |
| --- | ---: | ---: | ---: | ---: |
{before_row}
{after_row}

## Is R still faster?

R still faster: {r_faster}.

## Bottleneck assessment

{bottleneck_note(py, loglik)}

## Next performance candidates

- Add analytic gradients or a more efficient finite-difference strategy to reduce optimizer
  evaluations.
- Reuse mutable work buffers across repeated likelihood calls if the PyO3 problem object grows an
  interior workspace.
- Add Rayon site-wise parallel likelihood after serial correctness remains stable.
- Benchmark alternative optimizers and convergence tolerances on multiple synthetic datasets.

No benchmark numbers in this file are invented; unavailable values are marked as not available.
"""
    PERF_NOTES.write_text(perf)


if __name__ == "__main__":
    main()
