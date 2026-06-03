from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PY_JSON = REPORTS / "py_nb_benchmark.json"
PY_LOGLIK_JSON = REPORTS / "py_nb_loglik_benchmark.json"
R_JSON = REPORTS / "r_nb_benchmark.json"
OUT = REPORTS / "BENCHMARK_RESULTS_NB.md"


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


def coefficient_comparison(py: dict[str, Any] | None, r: dict[str, Any] | None) -> str:
    if not py or not r or r.get("status") != "completed":
        return "not assessed"
    names = r.get("coefficient_names") or []
    py_params = py.get("params") or []
    r_params = r.get("coefficients") or []
    if len(py_params) != len(r_params):
        return (
            "not name-matched; raw vectors recorded because parameter lengths differ "
            f"(Python {len(py_params)}, R {len(r_params)})"
        )
    if not names or len(names) != len(r_params):
        return "not name-matched; raw vectors recorded because R coefficient names are unavailable"
    return "not forced; raw Python/R vectors recorded because NB dispersion naming may differ"


def dispersion_comparison(py: dict[str, Any] | None, r: dict[str, Any] | None) -> str:
    if not py or not r or r.get("status") != "completed":
        return "not assessed"
    return (
        f"Python log_r={fmt(py.get('log_r'))}, r={fmt(py.get('r'))}; "
        "R dispersion parameterization not assumed from coefficient order"
    )


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    py = load(PY_JSON)
    py_ll = load(PY_LOGLIK_JSON)
    r = load(R_JSON)
    dataset = (py or {}).get("dataset") or (r or {}).get("dataset") or {}

    status = "NOT RUN"
    py_loglik = r_loglik = abs_loglik_diff = None
    py_seconds = r_seconds = speed_ratio = None
    py_nfev = py_nit = None
    direct_ms = nfev_direct = pct_fit = None
    r_env = "not available"
    unmarked_env = "not available"
    parity_status = "not assessed"
    notes = [
        "This is a simple end-to-end benchmark, not a comprehensive performance study.",
        "Optimizer paths may differ.",
        "Negative-binomial dispersion is harder to estimate than Poisson parameters.",
        "v0.1.1 showed Python+Rust faster than R unmarked on one simple local Poisson "
        "benchmark, but this is not a general performance claim.",
        "Do not invent results.",
    ]

    if py and py.get("status") == "completed":
        status = "PARTIAL"
        py_loglik = py.get("logLik")
        py_seconds = py.get("median_seconds")
        py_nfev = py.get("nfev")
        py_nit = py.get("nit")
        if not py.get("success", False):
            notes.append(f"Python optimizer reported non-success: {py.get('message')}")
    elif py:
        notes.append(f"Python NB benchmark did not complete: {py.get('message', 'no message')}")
    else:
        notes.append("Python NB benchmark was not run.")

    if py_ll and py_ll.get("status") == "completed":
        direct_ms = py_ll.get("median_milliseconds")
        if py_nfev is not None and direct_ms is not None:
            nfev_direct = float(py_nfev) * float(direct_ms) / 1000.0
            if py_seconds:
                pct_fit = 100.0 * nfev_direct / float(py_seconds)
    else:
        notes.append("Python NB direct likelihood benchmark was not run or did not complete.")

    if r and r.get("status") == "completed":
        r_loglik = r.get("logLik")
        r_seconds = r.get("median_seconds")
        r_env = r.get("R_version", r_env)
        unmarked_env = r.get("unmarked_version", unmarked_env)
        if py_loglik is not None:
            status = "COMPLETED"
            abs_loglik_diff = abs(float(py_loglik) - float(r_loglik))
            parity_status = "close" if abs_loglik_diff < 1.0e-4 else "differs"
        if py_seconds and r_seconds:
            speed_ratio = float(r_seconds) / float(py_seconds)
    elif r:
        notes.append(f"R NB benchmark was not run: {r.get('message', 'no message')}")
        r_env = r.get("R_version", r_env)
    else:
        notes.append("R NB benchmark was not run; reports/r_nb_benchmark.json is missing.")

    text = f"""# Negative-Binomial Benchmark Results

Status: {status}

Dataset:
- n_sites: {fmt(dataset.get("n_sites"))}
- n_visits: {fmt(dataset.get("n_visits"))}
- K: {fmt(dataset.get("K"))}
- repetitions: {fmt(dataset.get("repetitions", 3 if py else None))}

Correctness:
- Python logLik: {fmt(py_loglik)}
- R unmarked logLik: {fmt(r_loglik)}
- absolute logLik difference: {fmt(abs_loglik_diff)}
- coefficient comparison: {coefficient_comparison(py, r)}
- dispersion comparison: {dispersion_comparison(py, r)}
- parity status: {parity_status}

Performance:
- Python+Rust median fit time: {fmt(py_seconds)}
- R unmarked median fit time: {fmt(r_seconds)}
- speed ratio R/Python: {fmt(speed_ratio)}
- Python function evaluations: {fmt(py_nfev)}
- Python iterations: {fmt(py_nit)}
- direct NB likelihood median: {fmt(direct_ms)} ms
- nfev × direct likelihood median: {fmt(nfev_direct)} s
- percentage of fit time explained by likelihood calls: {fmt(pct_fit)}%

Environment:
- OS: {platform.platform()}
- Python: {(py or {}).get("python_version", "not available")}
- Rust: {rust_version()}
- R: {r_env}
- unmarked: {unmarked_env}

Notes:
"""
    for note in notes:
        text += f"- {note}\n"
    if py:
        text += f"- Raw Python params: {py.get('params')}\n"
    if r:
        text += f"- Raw R coefficients: {r.get('coefficients')}\n"
        text += f"- Raw R coefficient names: {r.get('coefficient_names')}\n"
    OUT.write_text(text)


if __name__ == "__main__":
    main()
