# Shared Core Architecture

The shared core is an experimental foundation for model families that are not yet part of the stable `pyabundance` API. It gives pcount, and future families such as occupancy or distance-sampling models, a common vocabulary without changing the pcount-centered rc2 surface.

## Current state

The existing pcount workflow remains the stable public surface. Functions and classes such as `pcount`, `pcount_df`, `build_pcount_matrices`, `PCountMatrices`, and `PCountResult` keep their current behavior.

Stage 1 adds adapter properties to `PCountResult`:

- `parameter_blocks`
- `model_spec`

These properties expose shared metadata over the existing fit result. They do not alter fitting, likelihood evaluation, summaries, AIC, predictions, bootstrap behavior, reports, or formula handling.

The new subpackage is importable as `pyabundance.core`, but it is intentionally not exported from top-level `pyabundance.__all__` in this stage.

Stage 2 adds an experimental `FramePCount` adapter in `pyabundance.core`.
`FramePCount` carries pcount response/design arrays and related labels using
the shared-core frame vocabulary. It does not replace `PCountMatrices`; the
stable pcount APIs remain `pcount`, `pcount_df`, and `build_pcount_matrices`.
Stage 2 prepares the frame layer for later shared process formulas and
prediction dispatch without adding a new fitting path.

Stage 3 adds an experimental process-formula builder in `pyabundance.core`.
It builds fixed-effect design matrices from `ProcessSpec` metadata and pandas
data using the shared process vocabulary. This is foundation work for future
shared prediction/newdata APIs, but Stage 3 does not implement prediction
dispatch, pcount formula newdata prediction, occupancy, distance-sampling,
dynamic models, or any new ecological model family.

Stage 4 adds an experimental generic prediction dispatch layer in
`pyabundance.core`. The shared `predict(result, type=...)` function dispatches
by shared-core result metadata and prediction type, then delegates pcount
requests to existing `PCountResult` prediction methods. It is intentionally
small: it does not add new prediction math, does not replace pcount-specific
methods, and supports existing-data pcount predictions only.

## Core concepts

### `ProcessSpec`

`ProcessSpec` describes one model process: its name, formula, link function, process level, design columns, and optional metadata. It is metadata only, not a fitting object.

### `ModelSpec`

`ModelSpec` groups the processes for a fitted model family. It records the model name, response name, process mapping, parameter blocks, and optional metadata.

### `ParameterBlock`

`ParameterBlock` describes a contiguous slice of a coefficient vector. Blocks include the block name, start/stop indices, link function, column names, and the process they belong to.

### `ModelFrame`

`ModelFrame` is a small generic container for a response array and optional site/observation data. It is not a pcount-specific frame and does not replace `PCountMatrices`.

### `FramePCount`

`FramePCount` is an experimental pcount-specific adapter for existing
matrix/DataFrame workflows. It exposes the pcount response matrix `y`, the
abundance design matrix `X`, the detection design tensor `W`, optional
site/observation data, site and visit labels, design column names, formula
strings when provided, visit-label provenance, and small metadata. It validates
only basic pcount frame consistency and is metadata/data-shape plumbing, not a
model fitting path.

### `ProcessDesign`

`ProcessDesign` is an experimental fixed-effect design matrix for one process.
It records the process name, process level, link, normalized RHS formula, a
contiguous `float64` matrix, formulaic column names, and optional metadata.
`build_process_design` builds one design from a `ProcessSpec` and a pandas
`DataFrame`; `build_process_designs` builds a mapping of designs from process
specs and data keyed by process level, such as `site` and `observation`.

The Stage 3 builder intentionally supports only fixed-effect RHS formulas:
examples include `~ x`, `~ visit - 1`, `~ x:visit`, and `~ x * visit`. It does
not support response-side formulas, random effects, offsets, splines, dot
expansion, prediction dispatch, or formula-less global processes such as
negative-binomial `r` and ZIP `psi` when a design is explicitly requested.

### `FitResultProtocol`

`FitResultProtocol` describes the shared result surface expected from fitted models: parameters, log-likelihood, status, AIC, model metadata, coefficient tables, and covariance access.

### `LikelihoodProblemProtocol`

`LikelihoodProblemProtocol` is the minimal likelihood-problem surface: an object with `loglik(theta) -> float`.

### `predict(result, type=...)`

`predict` is an experimental shared-core dispatch function. It identifies a
fitted result through `result.model_spec.model` when available, chooses a
registered handler for that model family, and delegates the request to existing
model-specific prediction methods. The initial Stage 4 handler supports pcount
results only.

Supported pcount prediction types are:

| `type` | Delegated pcount method |
| --- | --- |
| `"lambda"` | `PCountResult.predict_lambda()` |
| `"abundance"` | `PCountResult.predict_abundance()` |
| `"p"` | `PCountResult.predict_detection()` |
| `"det"` | `PCountResult.predict_detection()` |
| `"detection"` | `PCountResult.predict_detection()` |
| `"fitted"` | `PCountResult.fitted_counts()` |

`PCountResult.predict(type=...)` is a convenience method that delegates to the
same shared-core dispatch. The existing pcount methods remain the stable API:
`predict_lambda`, `predict_abundance`, `predict_detection`, `fitted_counts`,
and the DataFrame helper methods are not removed or renamed.

Formula/newdata prediction is not implemented in Stage 4. Requests using
`newdata`, `new_site_data`, or `new_obs_data` are rejected with a clear "not
implemented yet" error until a later stage adds pcount formula newdata support.

Shared-core spec objects are intended to be stable metadata snapshots for fitted results.
They defensively copy and freeze mapping metadata at construction time, including model
process mappings. This is a shallow freeze only; nested objects inside metadata are not
recursively frozen.

## pcount mapping

The pcount adapter maps existing pcount metadata into shared-core concepts:

| Existing pcount concept | Shared-core concept |
| --- | --- |
| `abundance_formula` | `lambda` process with `log` link at `site` level |
| `detection_formula` | `p` process with `logit` link at `observation` level |
| abundance coefficient columns | `lambda` `ParameterBlock` |
| detection coefficient columns | `p` `ParameterBlock` |
| negative-binomial `log_r` | `r` global process and one-parameter block with `log` link |
| ZIP `logit_psi` | `psi` global process and one-parameter block with `logit` link |

`PCountResult.model_spec.metadata` includes the mixture, truncation value `K`, whether the fit came from the DataFrame API, and the response dimensions.

`FramePCount` uses the same vocabulary for pcount design data: abundance
formulas describe the `lambda` process with a `log` link at the site level, and
detection formulas describe the `p` process with a `logit` link at the
observation level. Negative-binomial `log_r` remains the `r` global process with
a `log` link, and ZIP `logit_psi` remains the `psi` global process with a
`logit` link.

## Intentional non-goals for this stage

This stage intentionally does not add or implement:

- a new ecological model family;
- occupancy (`occu`);
- formula/newdata prediction;
- generic fit-list/model-selection containers;
- new likelihoods;
- changes to Rust likelihood formulas or hot paths;
- changes to the stable pcount public API.

## Next stages

Planned follow-up work can build on this metadata layer with:

1. shared pcount formula/newdata prediction built on process designs;
2. a shared `FitList`/model comparison foundation;
3. validation fixtures for cross-family parity checks;
4. future model families such as `occu` once the shared foundation is proven.
