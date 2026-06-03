from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT = REPORTS / "BENCHMARK_SUMMARY.md"


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


def row(model: str, py_path: str, r_path: str) -> str:
    py = load(REPORTS / py_path)
    r = load(REPORTS / r_path)
    py_seconds = py.get("median_seconds") if py and py.get("status") == "completed" else None
    py_loglik = py.get("logLik") if py and py.get("status") == "completed" else None
    r_seconds = r.get("median_seconds") if r and r.get("status") == "completed" else None
    r_loglik = r.get("logLik") if r and r.get("status") == "completed" else None
    speed_ratio = float(r_seconds) / float(py_seconds) if py_seconds and r_seconds else None
    loglik_diff = abs(float(py_loglik) - float(r_loglik)) if py_loglik and r_loglik else None
    status = "COMPLETED" if py_seconds is not None and r_seconds is not None else "PARTIAL"
    if py is None and r is None:
        status = "NOT RUN"
    return (
        f"| {model} | {fmt(py_seconds)} | {fmt(r_seconds)} | {fmt(speed_ratio)} | "
        f"{fmt(loglik_diff)} | {status} |"
    )


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    text = "# Benchmark Summary\n\n"
    text += (
        "| Model | Python+Rust median | R unmarked median | "
        "speed ratio R/Python | logLik difference | status |\n"
    )
    text += "|---|---:|---:|---:|---:|---|\n"
    text += row("Poisson N-mixture", "py_benchmark.json", "r_benchmark.json") + "\n"
    text += row("Negative-binomial N-mixture", "py_nb_benchmark.json", "r_nb_benchmark.json") + "\n"
    text += (
        row("Zero-inflated Poisson N-mixture", "py_zip_benchmark.json", "r_zip_benchmark.json")
        + "\n"
    )
    OUT.write_text(text)


if __name__ == "__main__":
    main()
