from __future__ import annotations

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


def test_release_docs_and_workflows_exist():
    required = [
        "CHANGELOG.md",
        "mkdocs.yml",
        "docs/api/pcount.md",
        "docs/tutorials/pcount_end_to_end.py",
        "docs/release/RELEASE_CHECKLIST.md",
        "docs/CONTRIBUTOR_ONBOARDING.md",
        ".github/workflows/ci.yml",
        ".github/workflows/wheels.yml",
        "scripts/smoke_test_wheel.py",
        "scripts/preserve_benchmark_artifacts.py",
        "benchmark_artifacts/README.md",
    ]
    for path in required:
        assert (ROOT / path).exists(), path


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
