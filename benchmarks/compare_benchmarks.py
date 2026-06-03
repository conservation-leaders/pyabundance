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
OUT = REPORTS / "BENCHMARK_RESULTS.md"
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


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    py = load(PY_JSON)
    r = load(R_JSON)
    truth = load(TRUE_JSON) or {}
    dataset = (py or {}).get("dataset") or (r or {}).get("dataset") or truth

    status = "NOT RUN"
    notes = [
        "This is a simple end-to-end fit benchmark, not a comprehensive benchmark.",
        "Optimizer implementations and convergence paths may differ.",
    ]
    py_loglik = r_loglik = abs_loglik_diff = max_coef_diff = None
    py_seconds = r_seconds = speed_ratio = None
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
        if not py.get("success", False):
            notes.append(f"Python optimizer reported non-success: {py.get('message')}")

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
                    abs(float(a) - float(b))
                    for a, b in zip(py_params, r_params, strict=True)
                )
            if py_seconds and r_seconds:
                speed_ratio = float(r_seconds) / float(py_seconds)
            parity_status = (
                "close"
                if abs_loglik_diff < 1.0e-5
                and (max_coef_diff is None or max_coef_diff < 1.0e-4)
                else "differs"
            )

    if r is None or (r and r.get("status") != "completed"):
        notes.append(
            "R was unavailable, unmarked could not be installed, or the R benchmark was "
            "skipped/failed; no R parity numbers are invented."
        )

    text = f"""Benchmark Results
Status: {status}
Dataset:
\t•\tn_sites: {fmt(dataset.get('n_sites'))}
\t•\tn_visits: {fmt(dataset.get('n_visits'))}
\t•\tK: {fmt(dataset.get('K'))}
\t•\trepetitions: {fmt(dataset.get('repetitions', 3 if py else None))}
Correctness:
\t•\tPython logLik: {fmt(py_loglik)}
\t•\tR unmarked logLik: {fmt(r_loglik)}
\t•\tabsolute logLik difference: {fmt(abs_loglik_diff)}
\t•\tmax coefficient absolute difference: {fmt(max_coef_diff)}
\t•\tparity status: {parity_status}
Performance:
\t•\tPython+Rust median fit time: {fmt(py_seconds)}
\t•\tR unmarked median fit time: {fmt(r_seconds)}
\t•\tspeed ratio R/Python: {fmt(speed_ratio)}
Environment:
\t•\tOS: {platform.platform()}
\t•\tCPU if available: {platform.processor() or platform.machine() or 'not available'}
\t•\tPython: {(py or {}).get('python_version', 'not available')}
\t•\tRust: {rust_version()}
\t•\tR: {r_env}
\t•\tunmarked: {unmarked_env}
Notes:
"""
    for note in notes:
        text += f"\t•\t{note}\n"
    OUT.write_text(text)


if __name__ == "__main__":
    main()
