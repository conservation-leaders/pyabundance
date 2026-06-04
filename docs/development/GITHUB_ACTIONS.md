# GitHub Actions

pyabundance is a mixed Rust/Python package built with maturin. GitHub Actions must distinguish local development installs from release builds.

## Install/build policy

- Local developers may run `maturin develop --release` inside an activated virtual environment.
- GitHub Actions CI, docs, and benchmark jobs should not call `maturin develop`.
- CI/test/docs/benchmark workflows use `python -m pip install -e '.[...]'`, which invokes the maturin PEP 660 backend under `setup-python` without requiring `VIRTUAL_ENV`.
- Wheel and publish workflows use `maturin build`, not editable installs.
- Wheel smoke tests install built wheels with pip and then run installed-package smoke tests.
- TestPyPI install workflows install from TestPyPI only and do not build locally.

## Rust toolchain policy

The project pins Rust to `1.83.0` for release-candidate builds.

In CI:

- install Rust explicitly before Python editable installs;
- use exact toolchain version `1.83.0`;
- install `rustfmt` and `clippy` through the GitHub Actions Rust setup step when those checks are run;
- run `rustup show`, `rustc --version`, `cargo --version`, `cargo fmt --version`, and `cargo clippy --version` before `pip install -e` in CI;
- do not rely on maturin to discover or install Rust during pip metadata generation.

`rust-toolchain.toml` pins the toolchain version with `profile = "minimal"` and does not install clippy/rustfmt components implicitly in CI.

Local development:

- developers may use `maturin develop` inside an activated virtual environment;
- developers may install components manually if needed:

```bash
rustup component add rustfmt clippy --toolchain 1.83.0
```

## Wheel matrix platforms

pyabundance includes a Rust/PyO3 native extension, so wheels are platform-specific. Release-candidate wheels must be built and smoke-tested for:

- Linux x86_64
- macOS x86_64
- macOS arm64
- Windows x86_64

The package may have been developed on macOS, but Linux and Windows users need platform-specific wheels. Without Linux/Windows wheels, pip may fall back to source builds requiring Rust and native build tooling.

Current runner labels:

- Linux x86_64: `ubuntu-latest`
- macOS x86_64: `macos-15-intel`
- macOS arm64: `macos-15`
- Windows x86_64: `windows-latest`

Do not use `macos-13`.

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
