# pyabundance 0.8.0 Release Notes

v0.8.0 is a release-engineering and contributor-readiness release. It does not add a new ecological likelihood family and does not change validated pcount likelihood formulas.

## Highlights

- API reference documentation scaffold using MkDocs and mkdocstrings.
- Runnable tutorial scripts for pcount fitting, uncertainty, model comparison, and posterior abundance.
- CI hardening for Rust fmt/test/clippy, Python tests, ruff, mypy, and coverage.
- Maturin wheel-building workflow and clean-venv wheel smoke test.
- Package metadata audit and optional dependency groups.
- Benchmark artifact preservation script and release checklist.

## Public API stability

The following v0.7 APIs are preserved:

- `pcount(...)`
- `pcount_df(...)`
- `build_pcount_matrices(...)`
- `aic_table(...)`
- `compare_models(...)`
- `load_example_pcount(...)`
- posterior abundance / ranef-like methods
- uncertainty methods
- reporting/export methods

## Clean-room status

No R/GPL source code was copied, inspected, translated, or paraphrased. R remains a black-box validation target only.
