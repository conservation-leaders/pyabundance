from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from pyabundance import __version__, load_example_pcount, pcount_df

ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_and_optional_dependency_groups():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pyproject["project"]["version"] == __version__ == "1.0.0rc1"
    assert "urls" in pyproject["project"]
    extras = pyproject["project"]["optional-dependencies"]
    for group in ["dev", "docs", "test", "benchmark", "release"]:
        assert group in extras
    assert pyproject["tool"]["maturin"]["module-name"] == "pyabundance._core"
    assert "mypy" in pyproject["tool"]
    assert "coverage" in pyproject["tool"]


def test_release_docs_workflows_and_cleanup_policy_files_exist():
    required = [
        "CHANGELOG.md",
        "mkdocs.yml",
        "docs/api/pcount.md",
        "docs/tutorials/pcount_end_to_end.py",
        "docs/release/RELEASE_CHECKLIST.md",
        "docs/CONTRIBUTOR_ONBOARDING.md",
        "docs/benchmarks/BENCHMARKS.md",
        "docs/benchmarks/LOCAL_BENCHMARK_CAVEAT.md",
        "docs/development/REPOSITORY_HYGIENE.md",
        "docs/development/REPO_CLEANUP_SUMMARY.md",
        "reports/README.md",
        ".github/workflows/ci.yml",
        ".github/workflows/wheels.yml",
        ".github/workflows/benchmarks.yml",
        "scripts/smoke_test_wheel.py",
        "scripts/preserve_benchmark_artifacts.py",
        "scripts/check_repo_hygiene.py",
    ]
    for path in required:
        assert (ROOT / path).exists(), path


def test_generated_artifact_policy_is_not_to_track_generated_outputs():
    assert (ROOT / "reports/README.md").exists()
    assert (ROOT / "scripts/check_repo_hygiene.py").exists()
    assert (ROOT / "scripts/preserve_benchmark_artifacts.py").exists()
    assert (ROOT / "docs/development/REPOSITORY_HYGIENE.md").exists()
    assert (ROOT / "docs/benchmarks/BENCHMARKS.md").exists()
    assert (ROOT / ".github/workflows/benchmarks.yml").exists()

    result = subprocess.run(
        ["git", "ls-files", "reports", "benchmark_artifacts", "data/benchmark", "dist"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert "reports/README.md" in tracked
    assert "benchmark_artifacts/README.md" not in tracked
    assert not any(path.startswith("benchmark_artifacts/") for path in tracked)
    assert not any(path.startswith("data/benchmark/") for path in tracked)
    assert not any(path.startswith("dist/") for path in tracked)


def test_repo_hygiene_script_passes_release_policy():
    if not (ROOT / ".git").exists():
        return
    subprocess.run(
        [sys.executable, "scripts/check_repo_hygiene.py"],
        cwd=ROOT,
        check=True,
    )


def test_release_smoke_dataset_fit():
    data = load_example_pcount("poisson", n_sites=20, seed=20260610)
    fit = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K=data.K,
    )
    assert fit.success
    assert fit.posterior_abundance().shape == (20, data.K + 1)
