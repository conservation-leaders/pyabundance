# Shared Core Architecture

The shared core is an experimental foundation for model families that are not yet part of the stable `pyabundance` API. It gives pcount, and future families such as occupancy or distance-sampling models, a common vocabulary without changing the pcount-centered rc2 surface.

## Current state

The existing pcount workflow remains the stable public surface. Functions and classes such as `pcount`, `pcount_df`, `build_pcount_matrices`, `PCountMatrices`, and `PCountResult` keep their current behavior.

Stage 1 adds adapter properties to `PCountResult`:

- `parameter_blocks`
- `model_spec`

These properties expose shared metadata over the existing fit result. They do not alter fitting, likelihood evaluation, summaries, AIC, predictions, bootstrap behavior, reports, or formula handling.

The new subpackage is importable as `pyabundance.core`, but it is intentionally not exported from top-level `pyabundance.__all__` in this stage.

## Core concepts

### `ProcessSpec`

`ProcessSpec` describes one model process: its name, formula, link function, process level, design columns, and optional metadata. It is metadata only, not a fitting object.

### `ModelSpec`

`ModelSpec` groups the processes for a fitted model family. It records the model name, response name, process mapping, parameter blocks, and optional metadata.

### `ParameterBlock`

`ParameterBlock` describes a contiguous slice of a coefficient vector. Blocks include the block name, start/stop indices, link function, column names, and the process they belong to.

### `ModelFrame`

`ModelFrame` is a small generic container for a response array and optional site/observation data. It is not a pcount-specific frame and does not replace `PCountMatrices`.

### `FitResultProtocol`

`FitResultProtocol` describes the shared result surface expected from fitted models: parameters, log-likelihood, status, AIC, model metadata, coefficient tables, and covariance access.

### `LikelihoodProblemProtocol`

`LikelihoodProblemProtocol` is the minimal likelihood-problem surface: an object with `loglik(theta) -> float`.

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

## Intentional non-goals for this stage

This stage intentionally does not add or implement:

- a new ecological model family;
- occupancy (`occu`);
- `FramePCount`;
- generic prediction dispatch;
- generic fit-list/model-selection containers;
- new likelihoods;
- changes to Rust likelihood formulas or hot paths;
- changes to the stable pcount public API.

## Next stages

Planned follow-up work can build on this metadata layer with:

1. `FramePCount` as a pcount-specific frame adapter;
2. a process-formula builder that can be reused by multiple model families;
3. generic `predict(type=...)` dispatch;
4. a shared `FitList`/model comparison foundation;
5. validation fixtures for cross-family parity checks;
6. future model families such as `occu` once the shared foundation is proven.
