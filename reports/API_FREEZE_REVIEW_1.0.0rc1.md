# API Freeze Review for v1.0.0rc1

Status: COMPLETED

Stable for rc1:
- `pcount`
- `pcount_df`
- `build_pcount_matrices`
- `PCountResult` core properties and methods
- pcount mixture aliases (`poisson`, `P`, `negative_binomial`, `negbin`, `NB`, `zero_inflated_poisson`, `zip`, `ZIP`)
- uncertainty methods
- posterior abundance / ranef-like methods
- model selection functions
- reporting/export functions
- dataset loaders

Experimental / may change before final v1.0:
- exact markdown/table formatting
- bootstrap result formatting

Internal:
- `pyabundance._core`
- Rust/PyO3 problem-object internals

Checks:
- `_core` is not exported through `pyabundance.__all__`.
- public API freeze tests exist in `tests/test_public_api_freeze.py`.
- public functions have docstrings.
- public functions are typed where practical.
- current limitations are documented in `docs/LIMITATIONS.md`.
