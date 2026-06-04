from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "check_repo_hygiene", ROOT / "scripts" / "check_repo_hygiene.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_check_repo_hygiene = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_check_repo_hygiene)
is_forbidden_tracked_path = _check_repo_hygiene.is_forbidden_tracked_path


def test_repo_hygiene_script_passes():
    if shutil.which("git") is None:
        pytest.skip("git is not available")
    result = subprocess.run(
        [sys.executable, "scripts/check_repo_hygiene.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "passed" in result.stdout.lower()


def test_omx_state_is_forbidden_when_tracked():
    assert is_forbidden_tracked_path(".omx/metrics.json")
    assert is_forbidden_tracked_path("./.omx/state/notify-fallback-authority-state.json")
    assert is_forbidden_tracked_path(".omx/logs/turns-2026-06-03.jsonl")


def test_generated_artifact_policy_classification():
    assert is_forbidden_tracked_path("benchmark_artifacts/v1.0.0rc1/manifest.json")
    assert is_forbidden_tracked_path("data/benchmark/pcount.csv")
    assert is_forbidden_tracked_path("dist/pyabundance-1.0.0rc1.tar.gz")
    assert is_forbidden_tracked_path("coverage.xml")
    assert is_forbidden_tracked_path("htmlcov/index.html")
    assert is_forbidden_tracked_path("reports/benchmark.json")
    assert is_forbidden_tracked_path("reports/BENCHMARK_RESULTS.md")


def test_curated_files_remain_allowed():
    assert not is_forbidden_tracked_path("reports/README.md")
    assert not is_forbidden_tracked_path("benchmarks/run_py_benchmark.py")
    assert not is_forbidden_tracked_path("docs/benchmarks/BENCHMARKS.md")
    assert not is_forbidden_tracked_path("python/pyabundance/__init__.py")
