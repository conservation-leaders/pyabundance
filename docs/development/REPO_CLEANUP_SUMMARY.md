# Repository cleanup summary

Date: 2026-06-04
Branch: repo-cleanup-before-external-alpha

What changed:
- generated artifacts removed from git tracking;
- `.gitignore` expanded for build, coverage, cache, benchmark, and report outputs;
- README simplified for external users;
- `pyproject.toml` URLs corrected to `conservation-leaders/pyabundance`;
- generated reports removed from tracked root `reports/`;
- benchmark artifacts ignored and documented as CI/release assets;
- repo hygiene check added;
- docs navigation simplified;
- benchmark and hygiene docs added under `docs/`.

Generated artifacts policy:
- reports generated locally are ignored;
- benchmark artifacts are uploaded by CI, not committed;
- release docs live in `docs/release/`;
- curated benchmark docs live in `docs/benchmarks/`.

Validation:
- cargo test: passed (10 Rust tests)
- cargo clippy: passed
- ruff: format check and lint passed
- mypy: passed
- pytest: passed (74 tests)
- coverage: passed (84.20%, threshold 80%)
- docs build: passed (`mkdocs build --strict`)
- repo hygiene check: passed

Known remaining cleanup TODOs:
- run TestPyPI publish workflow in GitHub after cleanup PR merges;
- run cross-platform wheel matrix in GitHub Actions;
- keep future generated reports out of git.
