# GitHub Actions

pyabundance is a mixed Rust/Python package built with maturin. GitHub Actions must distinguish local development installs from release builds.

## Install/build policy

- Local developers may run `maturin develop --release` inside an activated virtual environment.
- GitHub Actions CI, docs, and benchmark jobs should not call `maturin develop`.
- CI/test/docs/benchmark workflows use `python -m pip install -e '.[...]'`, which invokes the maturin PEP 660 backend under `setup-python` without requiring `VIRTUAL_ENV`.
- Wheel and publish workflows use `maturin build`, not editable installs.
- Wheel smoke tests install built wheels with pip and then run installed-package smoke tests.
- TestPyPI install workflows install from TestPyPI only and do not build locally.

## Workflows

### `ci.yml`

Purpose: default Python/Rust quality gate for pushes and pull requests.

Install method: `python -m pip install -e '.[dev,docs,release]'`.

Checks: Rust formatting, Rust tests, clippy, Ruff format/lint, mypy, pytest, coverage on Python 3.11, repository hygiene, and GitHub Actions policy.

### `docs.yml`

Purpose: strict MkDocs build and optional GitHub Pages deployment.

Install method: `python -m pip install -e '.[docs]'`.

### `wheels.yml`

Purpose: manual/PR wheel matrix build and smoke test.

Build method: `PyO3/maturin-action@v1` with `maturin build --release --out dist --compatibility pypi`.

Artifacts: platform wheels and optional smoke-test status artifacts.

### `publish-testpypi.yml`

Purpose: manual TestPyPI rehearsal using Trusted Publishing.

Build method: maturin-action for Linux/macOS/Windows wheels plus `maturin sdist` for source distribution.

Secrets: none. Maintainers must configure TestPyPI Trusted Publishing for this workflow.

### `publish-pypi.yml`

Purpose: guarded maintainer-only real PyPI publishing draft.

Build method: maturin-action for Linux/macOS/Windows wheels plus `maturin sdist`.

Secrets: none. Uses PyPI Trusted Publishing and the protected `pypi-release` environment.

### `testpypi-install.yml`

Purpose: cross-platform installation from TestPyPI after rehearsal publish.

Install method: `pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyabundance==...`.

This workflow must not build pyabundance locally.

### `benchmarks.yml`

Purpose: manual Python benchmark and optional R black-box parity run.

Install method: `python -m pip install -e '.[dev,benchmark]'`.

Artifacts: generated `reports/`, `benchmark_artifacts/`, and benchmark data are uploaded by CI and remain ignored by git.

## Sanity check

Run before editing workflow files:

```bash
python scripts/check_github_actions.py
```

The check fails if workflows use `maturin develop`, old action versions, upload-artifact v3, token-based PyPI credentials, or local builds in the TestPyPI install workflow.
