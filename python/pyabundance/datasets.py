"""Dataset helpers for pyabundance examples and benchmarks."""

from __future__ import annotations

from pathlib import Path


def benchmark_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "benchmark"
