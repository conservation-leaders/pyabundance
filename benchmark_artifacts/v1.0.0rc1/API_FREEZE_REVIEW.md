# API Freeze Review

Status: COMPLETED

Scope:
- public package exports in `pyabundance.__all__`
- pcount matrix API
- DataFrame/formula API
- uncertainty/bootstrap/diagnostics methods
- posterior abundance / ranef-like methods
- model-selection and reporting helpers
- bundled dataset loaders

Findings:
- APIs safe for external alpha: `pcount`, `pcount_df`, `build_pcount_matrices`, `PCountResult`, `aic_table`, `compare_models`, dataset loaders, and reporting helpers.
- Experimental but usable: bootstrap output formatting and exact markdown/report table formatting.
- Internal: `pyabundance._core` remains an implementation detail and is not exported through `__all__`.
- Public API test coverage exists in `tests/test_public_api.py`.

Documentation:
- Detailed audit: `docs/release/API_FREEZE_REVIEW_0.9.md`.

Notes:
- v0.9 is an external-alpha freeze review, not a v1.0 compatibility promise.
