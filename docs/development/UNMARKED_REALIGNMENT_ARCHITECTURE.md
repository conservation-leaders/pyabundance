# Unmarked feature realignment: architecture review and delivery plan

**Status:** proposed architecture

**Review date:** 2026-08-17

**Behavioral reference:** `unmarked` 1.5.1 public API

**Repository baseline:** `pyabundance` 1.0.0rc2

## Executive decision

The requested scope is a new model platform, not an incremental extension of the
current `pcount` path.

Today the repository has one substantive vertical slice: Python prepares pcount
matrices, SciPy optimizes, one of three Rust pcount problems evaluates the
likelihood, and `PCountResult` implements pcount-specific post-fit behavior. The
experimental `pyabundance.core` package adds useful metadata and facades, but it
does not drive fitting and is deliberately outside the stable public API.

The recommended realignment is to:

1. preserve the existing pcount API through a compatibility adapter;
2. replace the shallow shared-core facades with three deep modules: a validated
   survey-frame layer, an executable model compiler, and a model-generic fit and
   inference layer;
3. keep one numerical source of truth in Rust for likelihoods, latent-state
   posteriors, fitted means, and simulation;
4. keep data-frame/formula handling, SciPy optimization orchestration, labeled
   results, model lists, and bootstrap scheduling in Python initially;
5. prove the architecture with `pcount` and `occu` before implementing `colext`,
   `occuMulti`, and `occuComm`; and
6. treat parity as a pinned, clean-room behavioral contract with reviewed
   black-box fixtures, not as source translation.

This architecture has a real seam: every requested model needs the same small
set of compiled-model capabilities, and every requested generic method consumes
those capabilities. Adding one more metadata registry or another pcount-shaped
result class would not create that leverage.

## Scope and evidence

This review covers the exact requested surface:

- models: `pcount`, `occu`, `occuMulti`, `occuComm`, `colext`;
- derived analysis: `richness`;
- frames: `unmarkedFrame`, `unmarkedFramePCount`, `unmarkedFrameOccu`,
  `unmarkedFrameOccuMulti`, `unmarkedFrameOccuComm`;
- generic operations: `predict`, `fitted`, `ranef`, `parboot`, `fitList`,
  coefficient methods, and confidence-interval methods.

The companion [feature contract](UNMARKED_FEATURE_CONTRACT.md) records the
public behavior and mathematical requirements found in CRAN documentation,
official vignettes, the published package paper, and permitted black-box calls.
No upstream implementation source was inspected for this review.

Repository evidence came from the Rust crates, Python package, stubs, tests,
specifications, validation artifacts, workflows, release documents, and a local
verification run. The principal evidence locations are:

- Rust exports: `crates/ecoabundance-core/src/lib.rs:1-23`;
- PyO3 registration: `crates/ecoabundance-py/src/lib.rs:3-28`;
- stable Python exports: `python/pyabundance/__init__.py:3-46`;
- experimental frames and result protocols:
  `python/pyabundance/core/frames.py:16-228` and
  `python/pyabundance/core/results.py:12-39`;
- current pcount fitter: `python/pyabundance/pcount.py:127-284`;
- current pcount result: `python/pyabundance/result.py:44`;
- current architecture boundary and non-goals:
  `docs/development/SHARED_CORE_ARCHITECTURE.md:3-16,251-264`;
- clean-room rules: `specs/clean_room_policy.md:3-12` and
  `specs/r_parity_protocol.md:3-16`.

### Product-boundary assumption

This plan assumes the existing product boundary remains intact: pyabundance is
a public Python library backed by a reusable but internal Rust numerical crate.
“Rust and Python” therefore means that numerical capabilities are implemented
and tested in `ecoabundance-core`, exposed through PyO3, and presented through
the Python API.

If a separately consumable, stable Rust library is also a product requirement,
the scope is larger. It would need public Rust frame/builders, an optimizer and
fit-result API, labeled post-fit outputs, standalone documentation/examples,
serialization decisions, and independent Rust semver commitments. Those are not
assumed in the phases below; the typed Rust kernels remain usable and testable,
but Python owns the end-user statistical workflow.

## Current architecture

The stable execution path is:

```text
pandas / arrays / two separate formulas
                 |
                 v
       PCountMatrices (Python)
                 |
                 v
       pcount() + SciPy minimize
                 |
                 v
  one of 3 PyO3 pcount problem classes
                 |
                 v
   duplicated Rust P / NB / ZIP kernels
                 |
                 v
          PCountResult (Python)
```

### What is already strong

- Poisson, negative-binomial, and zero-inflated Poisson pcount likelihoods exist
  in Rust.
- Python has a usable pcount fitting, prediction, covariance, posterior abundance,
  simulation, bootstrap, reporting, and model-comparison workflow.
- Cached native problem objects avoid reconstructing all pcount data on every
  objective call.
- Formulaic, NumPy, pandas, SciPy, maturin, PyO3, typing, linting, wheel builds,
  and documentation infrastructure are in place.
- Independent slow Python likelihood calculations cover one small case for each
  pcount mixture. These are the strongest current numerical correctness tests.
- `ModelSpec`, `ProcessSpec`, and `ParameterBlock` provide useful vocabulary for
  an eventual common result contract.

### What only looks shared

- `ModelFrame` stores arrays and tables but does not enforce ecological response
  types, covariate alignment, axes, missingness semantics, or immutable identity
  (`python/pyabundance/core/frames.py:16-40`).
- `FramePCount` stores already-compiled `y`, `X`, and `W`; its documentation
  explicitly says it is not a fitting object
  (`python/pyabundance/core/frames.py:59-66`).
- `ModelSpec` is reconstructed from `PCountResult` after fitting instead of
  compiling and driving the fit (`python/pyabundance/result.py:190-244`).
- the generic `predict` registry has one pcount handler and is not public
  (`python/pyabundance/core/predict.py:10-143`);
- `FitList.predict()` chooses one model instead of producing model-averaged
  prediction (`python/pyabundance/core/fitlist.py:87-115`);
- the nominally generic model-selection path reads pcount fields such as
  `mixture`, `K`, `X`, and `W` (`python/pyabundance/model_selection.py:55-127`).

The result is a shallow interface: calling code sees shared names, but failures
and family-specific decisions still leak through pcount branches. The current
shared-core stages were intentionally scoped as adapters and facades rather than
new model families, as documented in
`docs/development/SHARED_CORE_ARCHITECTURE.md`.

## Requested-feature readiness

| Requested feature | Current readiness | Required implementation ownership |
| --- | --- | --- |
| `pcount` | Substantive P/NB/ZIP implementation; not full reference contract | Refactor shared Rust kernel and compiled fit path; add frame-driven Python adapter, missing options, stricter validation, and parity fixtures |
| `occu` | Absent | Python frame/compiler/result plus Rust binary-occupancy kernel, posterior, fitted values, and simulator |
| `occuMulti` | Absent | Python multispecies frame/formula/prediction API plus Rust bitset state-space likelihood, posterior, simulation, and penalty support |
| `occuComm` | Absent | Python community/species-covariate API plus Rust hierarchical occupancy and Gaussian random-effect integration |
| `richness` | Absent | Python derived-result API over an `occuComm` latent-posterior sampler; Rust supplies occupancy probabilities/samples |
| `colext` | Absent | Additional dynamic frame, four-process compiler, Rust forward/backward HMM, posterior trajectories, simulation, and results |
| `ranef` | Pcount-only summary alias | Rust latent posterior per family plus one labeled Python posterior object and sampling/summary methods |
| `unmarkedFrame` | Experimental storage class only | Public validated base survey frame, axes, masks, covariate alignment, snapshot identity, and coercion rules |
| `unmarkedFramePCount` | Experimental compiled-array adapter only | Raw count survey frame connected to the compiler and pcount fit |
| `unmarkedFrameOccu` | Absent | Raw binary survey frame and validation |
| `unmarkedFrameOccuMulti` | Absent | Normalized site x visit x species frame, species order, and `maxOrder` metadata |
| `unmarkedFrameOccuComm` | Absent | Site x visit x species frame plus species-covariate broadcasting and labels |
| `predict` | Experimental pcount-only dispatcher | Public process-aware generic; stored design schema; family-specific prediction strategies and fit-list averaging |
| `parboot` | Pcount-only and restricted | Generic simulate/refit recipe, callable vector statistics, mask preservation, reproducible parallel scheduling, and failure accounting |
| `fitted` | Pcount method only | Generic response-shaped values with explicit family semantics and labeled multispecies output |
| `fitList` | Experimental thin wrapper | Immutable comparable-fit collection, exact data identity checks, generic AIC table, model averaging, and unconditional uncertainty |
| coefficient methods | Pcount tables/alias only | Generic named coefficient selection by process/block, fixed/random distinction, and stable ordering |
| confidence-interval methods | Pcount Wald/link only | Generic normal and profile intervals, parameter selection, transformations, and clear distinction from posterior intervals |

No requested feature currently has full interface-and-behavior parity. Even
`pcount` is a strong numerical subset rather than the named reference contract:
it accepts compiled arrays, defaults to `se=False`, has no engine/thread or
random-effect path, and does not fit from a public survey frame.

## Findings, ordered by architectural impact

### 1. The narrowed list is not dependency-closed

At least four unlisted capabilities are mandatory:

- `colext` needs the equivalent of `unmarkedMultFrame`: primary periods,
  secondary visits, and yearly site covariates. A `DynamicOccuFrame` is therefore
  enabling scope, even if an R-compatible constructor name is not exported.
- `richness` needs posterior occupancy sampling. A private or public
  `posterior_samples` capability must exist before richness can be correct.
- `occuComm` needs access to random-effect terms and standard deviations for a
  useful fit object, even if exact `randomTerms` and `sigma` aliases are deferred.
- every `parboot` path needs model-specific simulation and a stored, reproducible
  refit recipe.

Penalized `occuMulti` also depends on bootstrap covariance. Dynamic occupancy is
more useful if projected and smoothed occupancy trajectories are retained.

### 2. Frames must be raw, validated domain objects

The current `FramePCount` is a compiled matrix bundle. Treating it as the base
for four more frame classes would mix three concerns: raw survey data, formula
encoding, and native memory layout.

The frame module should own the stable ecological facts:

- named site, visit, species, and primary-period axes;
- response dtype and value rules: non-negative integral counts or binary values;
- missing-observation masks and all-missing site rules;
- explicit observation-to-response mapping equivalent to `obsToY`, rather than
  assuming one observation row/process for every response cell;
- site, observation, yearly-site, and species covariate alignment;
- site-major conversion from wide matrices and long data;
- an immutable snapshot and deterministic data fingerprint.

It should not own design matrices or a native likelihood object. Those belong to
the compiler and Rust engine respectively. A frozen dataclass is not sufficient:
NumPy buffers and pandas objects remain mutable unless defensively copied and/or
made read-only. Fingerprints are trustworthy only when the referenced snapshot
cannot change underneath a result.

### 3. Formula compilation must become fitted state

Formula parsing is currently duplicated between `formula.py` and
`core/formulas.py`, and prediction reconstructs designs from strings and column
checks. That discards categorical levels, contrasts, transforms, and exact NA
behavior.

One compiler should transform `(frame, model declaration)` into an immutable
`PreparedModel` containing:

- trained Formulaic model specifications for every process;
- contiguous response/design arrays and masks;
- parameter layout and stable coefficient names;
- process links, axis mappings, and prediction reconstruction rules;
- the frame fingerprint and post-NA response fingerprint; and
- family options such as mixture, `K`, known occupancy, `maxOrder`, or penalty.

The parameter layout must cover the fitted vector exactly once. The present
`ParameterBlock` checks overlap but permits gaps
(`python/pyabundance/core/specs.py:122`); coefficient selection, profiling, and
prediction need a lossless layout invariant.

The compiler should author that layout once from the fitted designs, pass it to
the native prepared problem, and receive the validated same schema in numeric
snapshots. Python results must not reconstruct offsets independently after Rust
has already interpreted the flat parameter vector.

This is the highest-leverage Python module. It localizes formula and alignment
complexity and gives profile likelihood, `parboot`, prediction, and `fitList` the
same reproducible input.

### 4. Rust has three pcount implementations where it needs one family kernel

The P, NB, and ZIP modules repeat dimensions, observation parsing, site
preprocessing, combinatorial caches, latent loops, posterior loops, and error
mapping. `PCountDims` being defined in the Poisson module and imported by the
other mixtures is evidence that the seam is misplaced.

Before adding models, factor reusable native foundations:

- checked tensor dimensions and allocation limits;
- checked dot-product widths rather than `zip`-truncating unequal vectors;
- response/missing-mask preprocessing;
- numerically stable links, PMFs, log-sum-exp, and probability validation;
- shared count-mixture marginalization parameterized by the latent distribution;
- structured errors shared by core and PyO3;
- standardized result buffers for fitted values, posterior probabilities, and
  simulation.

Current edge behavior makes this a correctness prerequisite, not cosmetic
cleanup: non-finite detection designs can reach Rust and return `NaN`; extreme
ZIP logits can fail after rounding to exactly zero or one; and some products and
`K`-dependent allocations are unchecked. The compatibility contract must also
decide and lock whether `K == max(y)` is accepted: the current implementation
does, while public `unmarked` 1.5.1 behavior requires `K > max(y)`.
All-missing sites also need a contract: the current finite pcount sum can make
them contribute truncated-prior mass instead of no information.

### 5. Cross-cutting methods need capabilities, not family `if` cascades

The common internal model contract should be deliberately small:

```text
evaluate(theta)          -> objective and optional score/Hessian
fitted(theta)            -> response-axis expected values
latent_posterior(theta)  -> probabilities plus latent-state metadata
simulate(theta, seed)    -> response with the original structural mask
```

Prediction from new data also needs a compiler-created native problem or a
family prediction plan; it should not require Rust to understand pandas or
Formulaic. Profile intervals can reuse `evaluate` with a constrained parameter.

This is a justified abstraction because five model adapters, posterior methods,
bootstrap, and profiling all consume it. SciPy optimization should remain an
internal implementation detail until a second optimizer exists; introducing a
public optimizer interface now would add breadth without leverage.

### 6. `PCountResult` is the current change bottleneck

`PCountResult` holds parameters, raw arrays, optimizer diagnostics, covariance,
model metadata, coefficient tables, prediction, fitted values, posterior
abundance, reporting hooks, and bootstrap-related behavior
(`python/pyabundance/result.py:44` onward). Adding occupancy branches here would
turn one large class into the dispatch system for the entire library.

Create a common immutable fit core with:

- `PreparedModel`, native problem, parameters, objective, covariance, and status;
- a serializable fit recipe;
- generic AIC, log-likelihood, coefficient, covariance, and interval access;
- typed family result views for family-specific quantities.

Keep `PCountResult` as a compatibility wrapper/view during the transition.

### 7. High-dimensional models change numerical requirements

The current optimizer calls Rust once per scalar objective evaluation and may
use a finite-difference Hessian. That is acceptable for small pcount fits but is
unlikely to be adequate for:

- `occuMulti`, whose latent state has `2^S` configurations and whose natural
  parameter count grows combinatorially; and
- `occuComm`, which adds species-level Gaussian effects and an inner integration
  or approximation problem.

The engine interface should allow analytic or automatically differentiated
scores and Hessians without requiring them in the first `occu` slice. Before
committing to `occuComm`, write an architecture decision record and numerical
spike comparing clean-room marginalization choices such as Laplace or adaptive
quadrature. The public documents do not fully specify that numerical choice, so
black-box conformance and independent statistical validation are essential.

### 8. Existing validation demonstrates regression, not requested parity

The local baseline passes:

- 258 Python tests with 86.04% aggregate Python coverage;
- 10 Rust core tests; the PyO3 crate has zero Rust tests;
- Cargo formatting/clippy, Ruff, mypy, strict MkDocs, repository hygiene, and
  workflow-policy checks.

However:

- the checked-in pcount validation fixtures were generated by pyabundance itself
  (`docs/validation/PCOUNT_VALIDATION_FIXTURES.md:13-21`), so they are regression
  goldens rather than independent parity evidence;
- the R workflow is manual and all R/comparison commands tolerate failure with
  `|| true` (`.github/workflows/benchmarks.yml:48-66`);
- the R package version is discovered at runtime rather than pinned;
- native stub/runtime checking is not a gate and currently reports 43 mismatches;
- wheel smoke tests exercise only Poisson pcount.

The new architecture must be accompanied by a new evidence architecture.

### 9. The realignment supersedes current release governance

The public API is frozen for RC2 (`docs/release/API_FREEZE.md:1-20`), while the
shared-core document explicitly excludes occupancy, dynamic models, generic
bootstrap, and new likelihoods. The requested work must therefore begin with a
versioned roadmap decision: preserve RC2 as the pcount compatibility baseline,
formally supersede its non-goals, and define whether the realigned API targets a
new release candidate or the next major/minor development line.

## Target architecture

```text
Public Python model/frame API
  pcount | occu | colext | occu_multi | occu_comm
                         |
                         v
Deep survey-frame module ----------------------------------+
  response + axes + covariates + masks + fingerprint       |
                         |                                  |
                         v                                  |
Deep model compiler                                        |
  Formulaic schemas + designs + parameter layout           |
  -> immutable PreparedModel                               |
                         |                                  |
                         v                                  |
Fit coordinator (Python, SciPy initially)                   |
                         |                                  |
                         v                                  |
One PyO3 compiled-problem boundary                          |
                         |                                  |
                         v                                  |
Typed Rust kernels                                          |
  count mixture | binary occupancy | 2-state HMM            |
  bitset joint state | community random effects             |
                         |                                  |
                         v                                  |
Immutable common FitResult + typed family views <-----------+
                         |
                         v
Generic inference
  predict | fitted | ranef | parboot | coef | confint | FitList
                         |
                         v
Labeled Python outputs
  PredictionResult | FittedValues | LatentPosterior | BootstrapResult
```

### Module ownership

| Module | Owns | Must not own |
| --- | --- | --- |
| Python survey frames | Raw response, covariates, axes, masks, validation, fingerprint | Formulas, coefficient order, likelihoods |
| Python model compiler | Formula schemas, transformed designs, parameter layout, family options, prediction reconstruction | Optimization policy, numerical likelihood loops |
| Python fit coordinator | Starts, SciPy invocation, covariance policy, warnings, immutable fit recipe | Family-specific statistical formulas |
| Rust model engine | Likelihood, stable probability calculations, latent posterior, fitted means, simulation, optional derivatives | pandas/Formulaic objects, presentation labels |
| PyO3 boundary | Checked conversion, GIL release, structured error mapping, NumPy result buffers | Duplicated family math or independent validation rules |
| Python results/inference | Labels, transforms, intervals, model averaging, bootstrap scheduling, tabular views | Reimplementation of native latent loops |

### Proposed internal interfaces

Names are illustrative; behavior and ownership matter more than exact spelling.

```python
@dataclass(frozen=True)
class PreparedModel:
    frame: SurveyFrame
    spec: ModelSpec
    parameter_layout: ParameterLayout
    designs: Mapping[str, DesignMatrix]
    design_schemas: Mapping[str, FormulaSchema]
    data_signature: str
    family_options: Mapping[str, object]

@dataclass(frozen=True)
class FitRecipe:
    prepared_model: PreparedModel
    starts: NDArray[np.float64]
    optimizer: OptimizerSettings
    covariance: CovarianceSettings

class FitResult:
    recipe: FitRecipe
    params: NDArray[np.float64]
    covariance: NDArray[np.float64] | None
    diagnostics: FitDiagnostics
    native_problem: CompiledProblem
```

The Python-visible native object can be one `CompiledProblem` backed by a Rust
enum, instead of one copy-pasted PyO3 class per mixture and family. Typed Rust
problem structs should remain directly testable inside `ecoabundance-core`.

The result data types should preserve axes instead of returning ambiguous nested
lists:

- `PredictionResult`: estimate, standard error, lower/upper interval, process,
  scale, and row labels;
- `FittedValues`: response-shaped array plus site/visit/species/period axes;
- `LatentPosterior`: probability tensor, latent-state labels, axes, summaries,
  and seeded sampling;
- `BootstrapResult`: observed statistic vector, replicate matrix, failures,
  seeds, and metadata.

Simple immutable NumPy/pandas-backed types are sufficient. A new labeled-array
dependency is not required unless concrete output complexity justifies it.

## Rust work by family

### Shared numerical foundation

1. Extract dimensions, validated tensor layouts, masks, allocation guards, links,
   stable transforms, and structured errors from the pcount modules.
2. Collapse P/NB/ZIP into one count-marginalization engine with a latent-mixture
   strategy; preserve the existing exported wrappers temporarily.
3. Move NB and ZIP simulation into Rust so every pcount capability uses the same
   distribution definitions.
4. Standardize contiguous array outputs and release the GIL around expensive
   work. Return shaped NumPy arrays directly instead of constructing nested
   Python lists that are immediately converted back.
5. Add optional evaluation flags or methods for score/Hessian support without
   making derivatives mandatory for the first slice.
6. Avoid retaining duplicate raw arrays, parsed arrays, Python result arrays,
   and native copies when one immutable owner plus views is sufficient.
7. Establish one thread-budget policy so inner site parallelism and outer
   bootstrap workers cannot silently oversubscribe CPUs.

### `occu`

- binary response and missing-occasion preprocessing;
- logit and complementary-log-log occupancy links;
- known-occupied conditioning;
- stable closed-form marginal likelihood;
- site-level two-state posterior, expected fitted detection values, and simulator;
- fixed-parameter reference tests including all-zero histories.

This is the smallest second family and the proof that the compiled-model seam is
real.

### `colext`

- two-state, log-space/scaled forward likelihood over primary periods;
- forward-backward smoothing for latent posterior trajectories;
- four parameter processes: initial occupancy, colonization, extinction, and
  detection;
- correct transition-covariate period alignment;
- dynamic simulator and response-shaped fitted values;
- projected and smoothed trajectories retained internally, with public accessors
  decided in the API contract.

Do not enumerate `2^T` paths.

### `occuMulti`

- deterministic species order and bitmask encoding of all `2^S` states;
- natural-parameter subset design up to `maxOrder`;
- stable log-weight normalization and species-specific detection likelihoods;
- joint state posterior, marginal species posterior, co-occurrence and conditional
  probabilities;
- L2-penalized objective and bootstrap covariance path;
- simulation and hard dimension/memory limits with informative errors.

Reducing `maxOrder` reduces interaction parameters, not the `2^S` latent state
space. That distinction must be visible in validation and performance guidance.

### `occuComm`

- reuse the binary occupancy observation kernel per species;
- hierarchical community means, species deviations, and standard-deviation
  parameters for eligible state/detection terms;
- independent, documented Gaussian random-effect integration developed from a
  clean-room math specification;
- efficient inner-mode/curvature calculations and stable covariance handling;
- site-by-species latent posterior and seeded posterior sampling;
- simulation-recovery tests for community means, dispersion, and boundary cases.

This is the highest-risk family. Do not schedule its production implementation
until the integration spike establishes accuracy, runtime, gradients, and wheel
portability.

## Python work by capability

### Frames and names

Use idiomatic canonical names such as `SurveyFrame`, `PCountFrame`, `OccuFrame`,
`OccuMultiFrame`, `OccuCommFrame`, and `DynamicOccuFrame`. If source migration is
a product goal, add documented aliases for the requested R-style constructor
names. Do not reproduce R S4 internals or pretend arbitrary R objects are binary
compatible.

Normalize multispecies inputs to one internal `site x visit x species` layout,
even when users supply a species-keyed list. Preserve the input species order as
part of the frame identity.

### Model functions

- retain `pcount(...)` and add frame/formula overloads without breaking current
  matrix calls;
- add `occu(...)`, `colext(...)`, `occu_multi(...)`, and `occu_comm(...)` as the
  canonical Python names;
- optionally expose `occuMulti` and `occuComm` compatibility aliases only after
  naming and behavior policy is documented;
- make every function compile a frame to `PreparedModel` and call the same fit
  coordinator.

### `predict`

- dispatch from model/process metadata, not a mutable global registry;
- transform new data using the stored Formulaic schema;
- return a consistent labeled estimate/SE/interval object;
- support state/detection and family-specific processes;
- implement `occuMulti` joint, marginal, and conditional prediction;
- return species-keyed output for community models;
- model-average compatible `FitList` predictions with unconditional variance.

### `fitted`

Return arrays with the same ecological axes as the response, including named
species outputs where appropriate. Define whether values are marginal or
conditional in each family contract. Do not silently reproduce inconsistent
reference behavior: CRAN `unmarked` 1.5.1 appears to apply the ZIP structural-zero
factor twice in `fitted()`, while its documented generative model implies one
factor. Decide between mathematically corrected behavior and an explicit
compatibility mode, then test and document it.

### `ranef` and `richness`

`ranef` should return `LatentPosterior`, not just a summary table:

- pcount: site x abundance state `0..K`;
- occu: site x binary state;
- colext: site x primary period x binary state;
- occuMulti: joint state internally, with species-marginal views matching the
  public contract;
- occuComm: site x species x binary state.

`richness` then samples occupancy states for `occuComm`, sums across supplied
species, and returns either site means or the full sampled posterior. It does not
estimate unobserved species outside the frame.

### `parboot`

Replace the pcount branch with:

```text
simulate from fitted model
  -> restore structural/missing mask
  -> optionally refit stored FitRecipe
  -> evaluate a numeric-vector statistic
  -> record values, seeds, diagnostics, and failures
```

Use deterministic child seed streams so serial and parallel execution produce
the same replicates. Python should schedule workers; Rust should simulate each
model. Support callable statistics and `refit=False` as contract decisions.

### `FitList`

Require identical frame and post-NA response fingerprints, not merely compatible
shapes or names. Generalize AIC extraction away from pcount fields. Implement
AIC-weighted prediction with unconditional standard errors and explicit rejection
of incomparable models. Preserve input order and stable model names.

### Coefficients and confidence intervals

Use `ParameterLayout`/`ParameterBlock` as the one authority for names, ordering,
process selection, fixed/random distinction, and link transforms.

- `coef`: named numeric values by process/block, with a separate table method for
  estimates plus uncertainty;
- normal/Wald intervals: derived from covariance with explicit link or response
  scale;
- profile intervals: repeated constrained optimization from the stored fit
  recipe;
- posterior intervals: exposed as posterior summaries, not mislabeled as
  frequentist confidence intervals.

## Delivery sequence

The phases are dependency-ordered. Later family kernels can proceed in parallel
only after the compiled-model contract is stable.

| Phase | Deliverable | Exit gate |
| --- | --- | --- |
| 0. Contract and governance | Pin `unmarked` 1.5.1 behavior profile; approve clean-room specs; decide aliases, compatibility quirks, supported formula subset, standalone-Rust scope, and new release line | Every requested item is classified as exact, intentionally divergent, or deferred; RC2 non-goals formally superseded |
| 0b. Community feasibility spike | Compare independently specified random-effect integration, derivative, covariance, runtime, and portability options using a minimal occupancy model | Architecture decision records an accurate and feasible method, or `occuComm` is explicitly blocked/de-scoped before shared APIs harden around a false assumption |
| 1. Stabilize foundation | Fix native validation/overflow/extreme-link issues; refactor pcount common Rust and PyO3 utilities; add stub parity and binding tests | Existing pcount numerical/API tests unchanged; `stubtest` passes; no duplicated binding validators |
| 2. Deep frames and compiler | Raw survey frames, axes/masks/fingerprint, one formula compiler, `PreparedModel`, `FitRecipe` | Current pcount fits route through the new path and produce regression-equivalent results |
| 3. `occu` vertical slice | Occu frame, compiler adapter, Rust likelihood/posterior/simulation, typed result | Fixed-parameter, recovery, black-box, prediction, fitted, and posterior gates pass for pcount and occu |
| 4. Generic inference | Public predict/fitted/ranef/parboot/coef/confint/FitList across pcount and occu | Generic modules have no direct pcount-field coupling; serial/parallel bootstrap and model-average tests pass |
| 5. `colext` | Dynamic frame, HMM forward/backward, four processes, results | One-period reduction, posterior normalization, simulated recovery, and pinned black-box cases pass |
| 6. `occuMulti` | Multispecies frame, bitset engine, penalty, conditional prediction | Hand-enumerated two-species cases, state ordering, normalization, performance limits, and parity pass |
| 7. `occuComm` and richness | Approved random-effect engine, community fit/posterior, richness sampler | Integration spike criteria, recovery, boundary tests, richness invariants, and parity pass |
| 8. Release hardening | Full wheels/sdist smoke, docs/API manifests, strict parity regeneration, benchmarks | Tested artifacts are the published artifacts; compatibility and limitations are documented |

### Relative effort and risk

| Work package | Relative effort | Risk driver |
| --- | --- | --- |
| Foundation, frames, compiler, results | XL | Broad migration while preserving pcount behavior |
| `occu` | M | New family but closed-form likelihood |
| Generic post-fit methods | L | Shape/scale semantics across families |
| `colext` | L | Time-index alignment and forward/backward correctness |
| `occuMulti` | XL | Exponential state space and specialized predictions |
| `occuComm` + richness | XL+ | Gaussian random-effect marginalization, derivatives, recovery, runtime |
| Verification/release hardening | L, continuous | Independent oracles and cross-platform native packaging |

Effort labels are comparative, not calendar estimates. Phase 1 and 2 are not
overhead that can be skipped: without them each new family recreates validation,
formula, result, and PyO3 machinery and makes every later method more expensive.

## Clean-room implementation and parity policy

The repository is Apache-2.0 and explicitly forbids opening, copying,
translating, or paraphrasing incompatible upstream source. Therefore “migrate”
must mean independent behavioral reimplementation:

1. an independently authored mathematical and API specification is approved
   before code;
2. implementation uses that specification, public documentation, published
   equations, and original derivation;
3. R is used only through exported functions as a black-box oracle;
4. contributors record provenance and disclose incompatible source exposure;
5. reviewed fixtures record inputs, outputs, target package/version, platform,
   seed, configuration, tolerances, and provenance.

Generated diagnostic reports may remain ignored, but small reviewed black-box
goldens must be committed under a narrow policy exception. Default CI can consume
those fixtures without installing R. A scheduled or release job should regenerate
them against the pinned reference and fail when comparisons exceed thresholds.

Parity should be defined in layers:

- **mathematical parity:** likelihood and transformation identities at fixed
  parameters;
- **fit parity:** named objective, coefficients, covariance, and convergence on
  curated datasets;
- **behavioral parity:** defaults, errors, output shapes/names, missingness, and
  generic-method semantics;
- **compatibility policy:** documented corrections or deliberate exclusions when
  the reference has ambiguous, unstable, or apparently erroneous behavior.

## Verification architecture

### Per-family gates

1. Hand-computable microcases and an independently written slow enumerator.
2. Rust fixed-parameter likelihood, posterior, fitted, and simulation tests.
3. Python boundary tests for dtype, shape, contiguity, labels, covariate alignment,
   missingness, formulas, and error types.
4. Numerical stress grids: extreme predictors, all-zero histories, all-missing
   visits/sites, invalid values, degenerate dimensions, and allocation limits.
5. Multi-seed simulation recovery across identifiable and weak regimes.
6. Pinned, provenance-stamped R black-box fixtures comparing named values.
7. Representative performance and memory budgets.

Useful metamorphic reductions include:

- NB pcount approaches Poisson as size grows;
- ZIP pcount approaches Poisson as structural-zero probability approaches zero;
- one-species multispecies/community cases reduce to ordinary occupancy where
  the declared model permits;
- one-primary-period `colext` reduces to static occupancy;
- every posterior distribution sums to one;
- richness stays between zero and the number of supplied species.

### Cross-cutting gates

- exact shape, axis, name, and ordering fixtures for every
  model x `predict`/`fitted`/`ranef`/`coef`/`confint` combination;
- response/link-scale identities and transformed interval checks;
- posterior mean/mode/quantiles agree with stored probabilities;
- bootstrap reproducibility, custom-vector statistics, failed-refit accounting,
  mask preservation, and serial/parallel equivalence;
- `FitList` rejects different frame or post-NA response signatures and verifies
  model-averaged uncertainty;
- profile likelihood endpoints satisfy the target likelihood-ratio criterion;
- optimization comparisons align parameters by name and separately compare the
  objective at each solution.

### Native, packaging, and release gates

- add Rust coverage or explicit per-module test requirements;
- add PyO3 integration tests; the binding crate currently has none;
- make `_core.pyi` runtime parity (`stubtest`) a CI gate before adding bindings;
- smoke every native family in installed wheels, not only Poisson pcount;
- install and test the sdist in CI;
- test the same `abi3-py311` wheel on every declared Python version and decide
  whether Python 3.14 is supported;
- keep current platform promises explicit if Linux arm64, musllinux, or Windows
  arm64 are not added;
- publish the exact artifacts that passed model and smoke tests;
- replace subset-only public API tests with a versioned exact manifest;
- synchronize Python, Cargo, and release metadata versions.

## Alternatives considered

### Add one vertical slice per model

This would copy pcount's data validation, PyO3 classes, SciPy closure, result
methods, simulation, and bootstrap branches five times. It gives quick first
likelihoods but poor locality: any method or validation fix would touch every
family. Reject.

### Continue expanding the experimental registries and protocols

The current registry and metadata objects do not own fitting behavior. Expanding
their names would preserve a shallow abstraction in which callers still discover
family constraints at runtime. Reject as the primary architecture; reuse the
useful spec vocabulary inside the compiled-model design.

### Reimplement numerical models in both Python and Rust

This doubles correctness and parity work and invites divergence between fit,
simulation, posterior, and bootstrap behavior. Keep slow independent Python
references only as tests. Reject for production.

### Move all optimization and formulas into Rust immediately

This would replace working SciPy and Formulaic infrastructure before model
semantics are established. It expands the native surface and packaging risk
without evidence of need for the smaller families. Defer; design the engine so
derivatives or Rust-side optimization can be added when community/multispecies
benchmarks justify it.

## Decisions required before implementation

1. **Compatibility target:** exact `unmarked` 1.5.1 behavior, an idiomatic Python
   API with compatible results, or both through an explicit compatibility mode.
2. **Naming:** canonical snake_case/classes only, or R-style aliases such as
   `occuMulti` and `unmarkedFramePCount`.
3. **Formula subset:** fixed effects first versus random-effect syntax in the first
   public release. `occuComm` cannot be complete without its hierarchical random
   effects even if general random effects elsewhere are staged.
4. **ZIP fitted quirk:** corrected generative expectation versus opt-in exact
   reference compatibility.
5. **`occuComm` integration:** approve a clean-room numerical method after the
   dedicated spike; do not infer it from upstream source.
6. **Derivative strategy:** hand-derived/automatic differentiation/native
   optimization based on measured family benchmarks.
7. **Scope closure:** whether dynamic projected/smoothed accessors and community
   random-effect summaries are public in the same milestone.
8. **Release line:** how the new surface supersedes the RC2 API freeze while
   preserving current pcount users.

## Definition of done for the realignment

The requested scope is supported only when:

- every requested public name or documented Python equivalent is exported,
  typed, documented, and included in an exact API manifest;
- all model functions consume validated frames through one compiler and fit
  coordinator;
- all production likelihood, posterior, fitted, and simulation math has one Rust
  implementation;
- generic operations work without pcount-specific branches and preserve labeled
  ecological axes;
- the required hidden dependencies are implemented;
- approved clean-room specs and locked independent fixtures exist for every
  family and method contract;
- numerical, recovery, stress, parity, performance, PyO3, wheel, and sdist gates
  pass; and
- pcount compatibility behavior and every intentional reference divergence are
  documented in the release notes.

Until those conditions hold, individual names should be described as partial or
experimental rather than as unmarked-compatible.

## Primary public references

- [CRAN `unmarked` 1.5.1 reference manual](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html)
- [Official `unmarked` reference site](https://ecoverseR.github.io/unmarked/reference/)
- [Fiske and Chandler, 2011, *unmarked: An R Package for Fitting Hierarchical Models of Wildlife Occurrence and Abundance*](https://www.jstatsoft.org/article/view/v043i10)
