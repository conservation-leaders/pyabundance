# Repository hygiene

pyabundance keeps source, tests, docs, workflows, scripts, and benchmark generators in git. Generated benchmark outputs, release reports, local environments, and build products are regenerated locally or uploaded by CI.

## Keep tracked

- source code: `python/`, `crates/`
- tests: `tests/`
- benchmark scripts: `benchmarks/*.py`, `benchmarks/*.R`
- docs: `docs/`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CITATION.cff`, `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`
- workflows and templates: `.github/workflows/`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`
- scripts: `scripts/`
- small packaged datasets, if any: `python/pyabundance/data/`
- config: `pyproject.toml`, `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `mkdocs.yml`
- clean-room specs and policies: `specs/`, `docs/development/CLEAN_ROOM_POLICY.md`

## Do not track by default

- `dist/`, `build/`, `wheelhouse/`
- `target/`
- `.venv/`, `.venv*/`, `.env/`
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `__pycache__/`
- `.coverage`, `coverage.xml`, `htmlcov/`
- generated `reports/*.json`
- generated benchmark/release `reports/*.md`, except `reports/README.md`
- `benchmark_artifacts/`
- generated benchmark data under `data/benchmark/`
- temporary wheel/sdist/install smoke-test virtual environments

## Reports policy

`reports/` is a local generated-output directory. It should contain only `reports/README.md` in git. Curated release notes, benchmark explanations, and development policies belong in `docs/`.

## Benchmark artifacts policy

Benchmark scripts remain tracked. Generated benchmark outputs are ignored by git and uploaded from GitHub Actions as artifacts when needed. Release assets may include curated benchmark bundles, but those bundles should not be committed to `main`.

## Regenerating reports

Typical local commands:

```bash
python benchmarks/generate_pcount_dataset.py
python benchmarks/run_py_benchmark.py
python benchmarks/run_py_loglik_benchmark.py
python benchmarks/compare_benchmarks.py
```

Optional R black-box comparisons require R and `unmarked`:

```bash
Rscript benchmarks/run_r_unmarked_benchmark.R || true
python benchmarks/compare_benchmarks.py
```

## Hygiene check

Run before committing:

```bash
python scripts/check_repo_hygiene.py
```

The check fails if obvious generated artifacts are tracked by git.
