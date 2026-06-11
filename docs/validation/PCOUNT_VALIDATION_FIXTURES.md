# pcount validation fixtures

Stage 6 adds a small deterministic fixture harness for pcount likelihood validation. The fixtures live under `tests/fixtures/pcount_validation/` and are intentionally test-only: they are not a stable public validation API and are not exported from top-level `pyabundance.__all__`.

## What is covered

The checked-in synthetic fixtures cover:

- Poisson pcount;
- negative-binomial pcount;
- zero-inflated Poisson pcount.

Each fixture records the fixture name, mixture, truncation value `K`, `y`/`X`/`W` shapes, the response/design arrays, one parameter vector, the expected pyabundance log-likelihood, numeric tolerances, and a clean-room provenance note. The loader in `tests/helpers/pcount_validation.py` validates this schema before tests use the arrays.

The default test suite checks the fixture schema, the public Python log-likelihood helper for each mixture, and the corresponding Rust-backed problem-object `loglik(theta)` method. A lightweight fitted Poisson check also verifies that `PCountResult.model_spec`, `parameter_blocks`, generic `predict`, and `FitList` remain compatible with the existing pcount result surface.

## Clean-room and CI policy

The fixtures are synthetic and reviewable. Their expected values were computed from pyabundance public Python/Rust APIs. Do not inspect, copy, translate, or paraphrase GPL source code when extending them.

Default CI does not require R, `unmarked`, external datasets, or external downloads. Optional R/`unmarked` comparisons are manual black-box checks only: use public package behavior and fitted outputs, not source code internals.

Generated validation outputs must remain local and uncommitted. Do not commit reports, benchmark output, coverage output, wheels, Mallard data, Mallard results, or ad hoc R/pyabundance comparison outputs.
