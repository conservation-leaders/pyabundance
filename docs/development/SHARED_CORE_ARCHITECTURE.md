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

Stage 5 adds an experimental `FitList` wrapper in `pyabundance.core` for ordered
collections of already-fitted models. `FitList` is a convenience wrapper around
existing results and the existing `aic_table`/`compare_models` APIs; it is not a
replacement for those APIs. It can optionally call shared-core `predict` for one
selected model, defaulting to the current lowest-AIC model, but it does not
perform model averaging, ensemble prediction, stacking weights, refitting, or
formula/newdata prediction.

Stage 6 adds a test-only pcount validation fixture harness under
`tests/fixtures/pcount_validation/` with helper loading code in `tests/helpers/`.
The fixtures are deterministic synthetic Poisson, negative-binomial, and ZIP
pcount cases with explicit metadata, parameter vectors, expected pyabundance
log-likelihoods, tolerances, and clean-room provenance notes. They validate the
existing public Python log-likelihood helpers and Rust-backed likelihood problem
objects without changing Rust formulas, hot paths, fitting behavior, or stable
pcount APIs. Default CI does not require R, `unmarked`, external datasets, or
downloads; any R/`unmarked` comparison remains optional/manual and black-box
only. Generated validation outputs, reports, benchmark files, coverage outputs,
wheels, Mallard data, and Mallard results must not be committed.

Stage 7 adds formula-based newdata prediction for existing fitted `pcount_df`
results. It uses the formulas and process metadata stored on `PCountResult` to
build new abundance (`lambda`) and detection (`p`) design matrices, validates
that their Formulaic columns match the fitted columns, and delegates numerical
prediction to the existing matrix prediction methods. Matrix-based fits without
formula metadata continue to use existing-data prediction and direct `X`/`W`
prediction only; requesting formula newdata from such fits raises a clear
formula-metadata-required error. Stage 7 changes Python prediction plumbing only:
no Rust likelihood formulas, Rust likelihood hot paths, new ecological model
families, `occu`, dynamic/open models, K sensitivity helpers, generic simulate
facades, generic parboot facades, or Stage 8 parity helpers are included.

Stage 8A adds a small pcount-specific K sensitivity helper in
`pyabundance.k_selection`. `pcount_k_sensitivity()` accepts an existing
`PCountResult`, refits the same pcount specification across candidate K values
using the existing `pcount()` path, and summarizes log-likelihood, AIC,
delta-AIC, convergence status, optimizer counts, and a simple maximum absolute
parameter delta versus the reference fit. It preserves formula/DataFrame
metadata where available and does not mutate the original fit. Stage 8A changes
Python diagnostic plumbing only: no Rust likelihood formulas, Rust likelihood
hot paths, new ecological model families, `occu`, distance-sampling models,
dynamic/open models, parameter mapping helpers, generic simulation facades, or
generic parametric-bootstrap facades are included.

Stage 8B adds an experimental generic simulation facade in `pyabundance.core`.
`pyabundance.core.simulate(model, ...)` dispatches by model-family name and
currently supports only `model="pcount"`. The pcount handler delegates directly
to the existing stable simulation helpers: `simulate_pcount`,
`simulate_pcount_negbin`, and `simulate_pcount_zip`. It accepts the existing
pcount mixture names and aliases, uses `detection` as the preferred detection
coefficient keyword, accepts `alpha` as a compatibility alias, and passes
`seed` through unchanged. Existing pcount simulation functions remain the source
of truth for simulation math and stable user-facing APIs. Stage 8B does not add
new ecological model families, `occu`, distance-sampling models, dynamic/open
models, parameter mapping helpers, or a generic parametric-bootstrap facade.

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

### `FitList`

`FitList` is an experimental ordered container for collections of fitted model
results. It can be constructed from a mapping of names to fits or from an
iterable of fits plus optional names. Names are normalized to strings and must be
unique, and model insertion order is preserved.

The methods `FitList.aic_table(...)` and `FitList.compare(...)` delegate to the
existing `pyabundance.model_selection.aic_table` and `compare_models` functions,
so existing model-selection behavior remains the source of truth. Convenience
properties `best_model_name` and `best_model` use the default delegated AIC
table. `FitList.summary()` delegates to the existing `ModelComparison.summary()`
format.

`FitList.predict(type=..., model=...)` is intentionally narrow. It selects one
model by name, or the default `best_model` when omitted, and delegates to
`pyabundance.core.predict`. It does not aggregate predictions across models and
does not implement model averaging, refitting, stacking, ensemble prediction,
Stage 8 pcount formula newdata prediction, occupancy, distance sampling, open
population, dynamic, or other new ecological model families.

### `predict(result, type=...)`

`predict` is an experimental shared-core dispatch function. It identifies a
fitted result through `result.model_spec.model` when available, chooses a
registered handler for that model family, and delegates the request to existing
model-specific prediction methods. The current handler supports pcount results
only.

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

For formula-based pcount fits created with `pcount_df`, Stage 7 also supports
newdata prediction through `PCountResult.predict(...)` and
`pyabundance.core.predict(...)`:

- `type="lambda"` and `type="abundance"` require `new_site_data` (or
  unambiguous alias `newdata`) as a pandas `DataFrame` and return one prediction
  per new site.
- `type="p"` and `type="detection"` require `new_site_data` and either
  long-format `new_obs_data` or visit labels that allow default observation rows
  to be generated. The detection design tensor has shape
  `n_new_sites × n_visits × n_detection_params`.
- `type="fitted"` combines new latent mean predictions with new detection
  predictions using the existing fitted-count semantics. For ZIP fits, the
  latent mean uses the existing `lambda * (1 - psi)` behavior; negative-binomial
  fits use the existing latent mean.

The newdata path accepts `site_id_col`, `visit_col` (default `"visit"`), and
`visit_labels` (defaulting to `fit.visit_labels` when available). Explicit
`new_obs_data` must contain one row for every requested site × visit, no
duplicates, no unknown sites, and no unknown visits. If `new_obs_data` is
omitted, pyabundance generates observation rows by crossing the new sites with
the resolved visit labels and carrying site covariates into the observation
design. Missing covariates, unavailable formulas, missing site × visit rows, and
design-column mismatches raise `ValueError` with targeted messages.

Matrix fits without formulas do not gain formula newdata prediction. They may
continue to call the existing matrix prediction methods directly, such as
`fit.predict_lambda(X=...)` and `fit.predict_detection(W=...)`, or the generic
dispatch where the matrix argument maps unambiguously to the requested type.
Stage 7 does not add standard errors or intervals for fitted newdata products;
lambda and detection newdata use the existing `X`/`W` uncertainty support when
available.

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
- formula/newdata prediction beyond pcount fits created with `pcount_df`;
- parameter mapping helpers;
- generic K sensitivity helpers beyond the pcount-specific Stage 8A helper;
- generic parboot facades;
- model averaging, refitting, stacking, or ensemble prediction;
- new likelihoods;
- changes to Rust likelihood formulas or hot paths;
- changes to the stable pcount public API.

## Next stages

Planned follow-up work can build on this metadata layer with:

1. Stage 8 pcount parity helpers where separately approved;
2. future parameter mapping or parametric-bootstrap facades where separately approved;
3. future validation fixtures for additional shared-core surfaces where needed;
4. future model families such as `occu` once the shared foundation is proven.
