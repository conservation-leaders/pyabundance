# Release Checklist

Use this checklist for TestPyPI-style release rehearsals and future public releases.

## Pre-flight

- [ ] Confirm clean-room policy compliance.
- [ ] Confirm version in `pyproject.toml`, `Cargo.toml`, crate manifests, `CITATION.cff`, and `pyabundance.__version__`.
- [ ] Run `cargo fmt --all -- --check`.
- [ ] Run `cargo test`.
- [ ] Run `cargo clippy --all-targets --all-features -- -D warnings`.
- [ ] Run `maturin develop --release`.
- [ ] Run `ruff check .`.
- [ ] Run `mypy`.
- [ ] Run `pytest --cov=pyabundance --cov-report=term-missing`.

## Wheels

- [ ] Run `maturin build --release --out dist`.
- [ ] Create a clean virtual environment.
- [ ] Install the wheel from `dist/`.
- [ ] Run `python scripts/smoke_test_wheel.py`.
- [ ] Inspect wheel metadata with `twine check dist/*` when `twine` is installed.

## Benchmarks and reports

- [ ] Run Python benchmark scripts.
- [ ] Run optional R black-box comparisons where available.
- [ ] Run `python scripts/preserve_benchmark_artifacts.py --version <version>`.
- [ ] Confirm reports do not invent unavailable R results.

## Documentation

- [ ] Run tutorial scripts under `docs/tutorials/`.
- [ ] Build docs with `mkdocs build` when docs dependencies are installed.
- [ ] Review release notes and changelog.

## Publication rehearsal

- [ ] Upload to TestPyPI only after all checks pass.
- [ ] Install from TestPyPI in a clean environment.
- [ ] Run wheel smoke tests again.
