# GitHub Actions stabilization

## Issue fixed

- Previous issue: `maturin develop` was called in GitHub Actions without a virtualenv.
- Current issue: `tests/test_release_engineering.py` still expected `benchmark_artifacts/README.md` after repository cleanup.

## Root cause

`benchmark_artifacts/` is now generated and ignored after repository cleanup, but the release-engineering test still expected a tracked file under that directory.

## Fix

- Removed `benchmark_artifacts/README.md` from required tracked files.
- Added cleanup-policy assertions for `reports/README.md`, repository hygiene docs, benchmark docs, artifact preservation script, benchmark upload workflow, and the repo hygiene script.
- Confirmed generated artifacts remain untracked.
- Kept benchmark scripts and artifact-upload workflows tracked.

## Validation

- repo hygiene: passed.
- GitHub Actions policy check: passed.
- cargo fmt: passed.
- cargo test: passed, 10 Rust tests.
- cargo clippy: passed.
- ruff format/check: passed.
- mypy: passed.
- pytest: passed, 80 tests.
- coverage: passed, 84.20% against 80% threshold.
- docs: `mkdocs build --strict` passed.
- benchmark generation smoke: passed; generated outputs remained ignored/untracked.

## Decision

The cleanup policy is correct. Generated benchmark artifacts should not be re-tracked. CI is ready to rerun across Python 3.11, 3.12, and 3.13.
