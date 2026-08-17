# `unmarked` feature contract for the Rust/Python realignment

Status: research note

Reference release: `unmarked` 1.5.1, published 2025-09-26

Checked: 2026-08-17

## Scope and clean-room boundary

This note describes the documented behavioral contract of the requested R
features:

`pcount`, `occu`, `occuMulti`, `richness`, `occuComm`, `ranef`,
`unmarkedFrame`, `unmarkedFrameOccu`, `unmarkedFrameOccuComm`,
`unmarkedFramePCount`, `unmarkedFrameOccuMulti`, `predict`, `parboot`,
`fitted`, `fitList`, `colext`, `coef`, and `confint`.

The reference is CRAN's current `unmarked` 1.5.1 release. CRAN identifies the
package as GPL-3-or-later and as requiring compilation. This repository is an
Apache-2.0 clean-room implementation, so “port” must mean independent
implementation of documented models and observable behavior—not translation of
R, C++, TMB, or other package source. No `unmarked` source or test file was
opened for this research. Sources were limited to the rendered CRAN reference
manual, rendered CRAN vignettes, published model equations in those documents,
and public black-box calls against the installed CRAN package. See the local
[clean-room policy](CLEAN_ROOM_POLICY.md) and
[R parity protocol](https://github.com/conservation-leaders/pyabundance/blob/main/specs/r_parity_protocol.md).
The upstream package
metadata and license are recorded on the [CRAN package page](https://cran.r-project.org/package=unmarked).

This distinction is architectural: a contributor who has inspected
incompatible implementation source for one of these features should not write
that feature here without a separate clean-room specification from another
contributor.

## Main findings

1. **The requested list is not dependency-closed.** `colext` requires the
   multi-season equivalent of `unmarkedMultFrame`; `parboot` requires model
   simulation, refitting, residuals, and a default sum-of-squared-residuals
   statistic; `richness` requires `ranef` plus posterior sampling; `fitList`
   model-averaged prediction requires AIC weights; and profile confidence
   intervals require likelihood profiling. Those capabilities must exist even
   if their upstream helper names are not all public Python targets.
2. **There are four materially different latent-state engines beyond the
   existing pcount engine.** Static occupancy is a two-state mixture; dynamic
   occupancy is a two-state hidden Markov model; interacting multispecies
   occupancy enumerates `2^S` joint states; and community occupancy is a
   species-level mixed-effects model. They should share data, formula, result,
   prediction, and uncertainty infrastructure, but not one monolithic
   likelihood implementation.
3. **A same-named Python function is not necessarily upstream-compatible.** In
   particular, upstream `fitList` predicts by model averaging rather than by
   choosing the lowest-AIC model, upstream `ranef` is a complete discrete
   posterior distribution rather than only posterior summaries, and upstream
   `predict` has family-specific output shapes and uncertainty algorithms.
4. **Random effects are in scope if the functions are meant to match their
   documented contract.** `occu` and `pcount` accept lme4-style random-effects
   terms, while `occuComm` is intrinsically a species-level random-intercept and
   random-slope model. Fixed-effects-only milestones are useful, but they must
   be labeled as subsets.
5. **Formula compilation and retained design metadata are shared critical
   infrastructure.** Predictions must rebuild exactly the fitted columns,
   contrasts, factor levels, transformations, and random-effect group mappings;
   checking column names after independently recompiling a formula is not a
   sufficient compatibility guarantee.

## Model contracts

### `pcount`: closed N-mixture abundance

For site `i` and repeat visit `j`, latent abundance follows one of Poisson,
negative-binomial, or zero-inflated Poisson distributions and the observation
model is `y_ij | N_i ~ Binomial(N_i, p_ij)`. Abundance uses a log link and
detection uses a logit link. For negative binomial models the additional
dispersion parameter is called `alpha` and lower values mean more dispersion.
For ZIP models `psi` is the structural-zero probability and marginal abundance
is `lambda_i * (1 - psi)`. The likelihood sums latent abundance only through a
user-supplied upper bound `K`, which must be high enough not to affect estimates
and raises computational cost as it grows. The documented formula is a double
right-hand-side formula in **detection then abundance** order. Random effects in
the formula require the TMB engine in R, but a Rust implementation must use an
independently specified integration strategy. The returned fit has state and
detection processes plus `alpha` or `psi` where applicable. See the official
[`pcount` reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#pcount).

The finite sum is an unnormalized truncation of the latent distribution, not a
distribution renormalized to `0..K`. Public 1.5.1 behavior also requires
`K > max(y)`, even though an inclusive upper index equal to the largest observed
count is mathematically nonempty. The current project must decide whether to
keep its more permissive `K >= max(y)` validation or add strict R-compatibility;
in either case, likelihood summation and a diagnostic for inadequate upper-tail
mass should remain separate concerns. Formula order and internal parameter
order also differ: the call is detection then abundance, while fitted parameter
blocks are state, detection, then any mixture parameter.

The clean-room Rust likelihood already uses the appropriate finite mixture
shape. Full upstream behavior additionally needs:

- `state` prediction as expected latent abundance. For ZIP this is the marginal
  mean `lambda * (1 - psi)`, not the non-structural Poisson mean `lambda`;
- `det`, `alpha`, and `psi` prediction blocks on their natural scales;
- fitted counts with the response shape, using expected abundance times
  detection probability;
- an `M x (K+1)` empirical-Bayes posterior over `N` (or a larger caller-supplied
  `K`) for `ranef`; and
- random-effects formula terms and their conditional predictions if exact
  function parity is claimed.

The distinction between component `lambda` and marginal abundance is worth
preserving in the Python API, but the upstream alias `type="state"` must map to
the marginal quantity.

There is a version-specific behavioral trap: public black-box calls to
`unmarked` 1.5.1 show that ZIP `fitted()` multiplies by `(1-psi)` twice, returning
`lambda * p * (1-psi)^2`, even though the documented generative model implies
`E[y] = lambda * p * (1-psi)`. In the same release,
`predict(type="state")` returns the correct marginal mean while
`backTransform(type="state")` returns component `lambda`. This should be logged
as an upstream compatibility defect. The statistically correct expectation
should remain the default here; if exact bug-for-bug output is ever required,
put it behind an explicit, tested compatibility option rather than contaminating
the model definition.

### `occu`: single-season occupancy

The state and observation equations are

```text
z_i ~ Bernoulli(psi_i)
y_ij | z_i ~ Bernoulli(z_i * p_ij).
```

The double right-hand-side formula is again detection then state. Detection
uses a logit link. State uses a logit link by default or a complementary
log-log link when `linkPsi="cloglog"`; the latter corresponds to an underlying
Poisson intensity, with `cloglog(psi_i) = log(lambda_i)`. `knownOcc` is a set of
site row numbers whose latent state is fixed occupied. Documented engines are
C, R, and TMB, with TMB selected for random-effects formulas. The result is an
`unmarkedFitOccu`. See the official [`occu`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#occu).

An independent core implementation therefore needs a stable two-state
site-likelihood, correct handling of an all-zero detection history, a fixed
occupied path for `knownOcc`, both state links, optional random effects, and an
`M x 2` posterior for `ranef`. `fitted` is an `M x J` expected detection matrix,
and ordinary `predict(type="state"|"det")` returns estimates, standard errors,
and confidence limits.

`knownOcc` is conditioning information, not another observed detection. For a
known-occupied site the state is fixed to one and the occupancy-probability
factor is removed from that site's likelihood; its detection history still
informs `p`. Missing visits are omitted. The model assumes closure across repeat
visits, conditional independence, and no false-positive detections.

### `occuMulti`: interacting-species occupancy

For `S >= 2` potentially interacting species, each site's latent state is a
binary vector with `2^S` possible states. The state probabilities form a
multivariate Bernoulli distribution. With two species the documented natural
parameters are

```text
f1  = log(psi_10 / psi_00)
f2  = log(psi_01 / psi_00)
f12 = log((psi_11 * psi_00) / (psi_10 * psi_01)).
```

Each natural parameter has its own covariate formula. Each species has an
independent detection formula and conditional detection model. A state formula
of `"0"` or `"~0"` fixes that natural parameter to zero. `maxOrder` drops
interactions above a chosen order; by default all orders are present. Thus the
default number of state formula blocks is `2^S - 1`, and both memory and
likelihood cost are exponential in species count. The model and formula ordering
are described in the official [`occuMulti`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#occuMulti)
and [multispecies occupancy vignette](https://cran.r-project.org/web/packages/unmarked/vignettes/occuMulti.html).

The likelihood contract calls for a dedicated joint-state engine:

1. build a deterministic state-by-interaction design (`fDesign`) from species
   order and `maxOrder`;
2. evaluate every active natural-parameter linear predictor;
3. convert joint-state log weights to probabilities with a stable normalization;
4. multiply by conditional per-species/per-visit observation probabilities; and
5. sum over compatible joint states with log-sum-exp.

`penalty` adds the documented ridge term
`penalty * 0.5 * sum(theta^2)`. When it is nonzero, `boot` controls bootstrap
replicates used for the covariance matrix. The official vignette warns about
sparse data, boundary estimates, separation, and few joint detections; these
need explicit diagnostics rather than relying only on an optimizer success
flag. Penalized estimates trade lower variance for bias.

Prediction is family-specific. Without `species`, state prediction returns all
`2^S` state probabilities. With one or more species it returns marginal or
co-occurrence probability. `cond` requests probability conditional on presence,
or on absence when a species name is prefixed by `-`. Its uncertainty uses
bootstrap simulation controlled by `nsims` rather than the ordinary generic
path. Detection and fitted outputs are per-species collections. These behaviors
are illustrated in the official [prediction sections of the
vignette](https://cran.r-project.org/web/packages/unmarked/vignettes/occuMulti.html#occupancy-probabilities).

Reducing `maxOrder` reduces the number of estimated natural-parameter blocks,
but it does not remove any of the `2^S` latent occupancy states. Likewise,
`ranef` exposes species-marginal two-state posterior objects rather than one
public `2^S` joint posterior object. The core may calculate a joint posterior
internally, but the compatibility layer must reconstruct the per-species
objects and names.

### `occuComm` and `richness`: community mixed-effects occupancy

Community occupancy analyzes detection histories for many species jointly, but
unlike `occuMulti` it does not model direct species interactions. Each species
has its own occupancy and detection coefficients, drawn from shared normal
distributions. The documented example is

```text
z_is   ~ Bernoulli(psi_is)
y_ijs  ~ Bernoulli(p_ijs * z_is)
beta_0s ~ Normal(mu_beta0, sigma_beta0)
beta_1s ~ Normal(mu_beta1, sigma_beta1),
```

with analogous detection effects. `occuComm` takes the familiar detection-then-
occupancy formula and automatically creates species random intercepts and
eligible random slopes. A covariate that varies only by species does not receive
a species random slope. The function also accepts explicit lme4-style random
intercepts. It returns an `unmarkedFitOccuComm`. The model is documented in the
official [`occuComm`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#occuComm)
and [community occupancy vignette](https://cran.r-project.org/web/packages/unmarked/vignettes/occuComm.html).

This makes `occuComm` dependent on a genuine mixed-effects subsystem: random
effect design matrices, variance parameters, marginal-likelihood optimization,
conditional effect estimates, covariance, and population-level versus
conditional prediction (`re.form`). The reference manual does not specify the
numerical integration approximation closely enough to recreate it. The project
must select and publish an independent mathematical/numerical specification,
then set statistical parity tolerances using black-box results. Copying the
upstream TMB implementation is prohibited.

The regression random effects and latent-state posteriors are separate
concepts. Species coefficient deviations belong to `randomTerms`/variance
summaries, whereas `ranef` returns a species-named collection of two-state
occupancy posteriors. A result design that uses one overloaded “random effects”
field for both will be incorrect.

Ordinary prediction returns one result table per species; fitted values return
one `M x J` matrix per species. The documented model covers only species in the
input roster—there is no data augmentation for hypothetical completely
unobserved species. Consequently site richness is richness over that modeled
roster, not an estimator of an unbounded unseen community.

`richness(fit, nsims=100, posterior=FALSE)` uses `ranef` and posterior sampling.
With `posterior=FALSE` it returns a length-`M` vector of posterior-sample means;
with `TRUE` it returns the posterior draws. Because even the point estimate is
Monte Carlo based, the Rust/Python contract needs an explicit RNG object or seed
and documented reproducibility semantics. See the official [`richness`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#richness)
and the [richness example](https://cran.r-project.org/web/packages/unmarked/vignettes/occuComm.html#richness).

These are conditional empirical-Bayes draws: fitted fixed effects,
hyperparameters, and their estimation uncertainty are not jointly sampled.

### `colext`: dynamic occupancy

`colext` has four logit-linked processes: initial occupancy (`psi`),
colonization (`col`/`gamma`), extinction (`ext`/`epsilon`), and detection
(`det`/`p`). Initial occupancy is a site-level Bernoulli state. For later primary
periods the transition is equivalently

```text
Pr(z_it = 1 | z_i,t-1) = z_i,t-1 * (1 - epsilon_it)
                         + (1 - z_i,t-1) * gamma_it,
y_ijt ~ Bernoulli(z_it * p_ijt).
```

Initial occupancy may use site covariates; colonization and extinction may use
site and yearly-site covariates; detection may use site, yearly-site, and
observation covariates. The response is wide `M x (J*T)` data accompanied by
the number of primary periods. See the official [`colext`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#colext)
and the published equations and data layout in the [dynamic occupancy
vignette](https://cran.r-project.org/web/packages/unmarked/vignettes/colext.html#dynamic-occupancy-models).

For a yearly-site transition covariate at primary period `t`, the corresponding
row governs the `t -> t+1` transition; only the first `T-1` transition rows
contribute. Keeping all `T` rows in a general yearly design is convenient, but
the active transition mask must be explicit.

This is a two-state hidden Markov model, not repeated independent `occu` fits.
The Rust core needs forward likelihood evaluation, forward-backward smoothing,
projected state distributions, and time-aware prediction. `ranef` must store an
`M x 2 x T` smoothed posterior; `fitted` retains the `M x (J*T)` response shape.
The fit exposes prediction types `psi`, `col`, `ext`, and `det`, and the
documented result additionally supports smoothed and projected trajectories.

Critically, `colext(data=...)` requires an `unmarkedMultFrame`, not any of the
frame constructors in the requested list. The Python project must either add a
public dynamic frame equivalent or deliberately expose a differently named
constructor with all the same axes and validation. Omitting the data type leaves
`colext` unusable.

## Frame and data contracts

The base `unmarkedFrame` holds an `M x J` response, `M`-row site covariates, and
observation covariates supplied either as a named collection of `M x J` values
or a flat `M*J` table in site-major/observation-minor order. `obsToY` can map a
different number of observation processes to response columns. Missing values
are represented by `NA`, and site covariates are made available to observation
formulas as well. See the official [`unmarkedFrame`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFrame).

In the 1.5.1 binary the manual-documented base constructor is not exported by
the attached package; users normally construct a child frame. Python should
therefore treat this requested feature primarily as a base class/protocol unless
there is a deliberate reason to expose direct generic construction.

The requested child constructors specialize that contract:

| Constructor | Response | Additional contract |
| --- | --- | --- |
| `unmarkedFramePCount` | one `M x J` repeated-count matrix | non-missing observations are counts; consumed by `pcount` ([reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFramePCount)) |
| `unmarkedFrameOccu` | one `M x J` detection/non-detection matrix | consumed by `occu`; row identity and visit order must survive missingness ([reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFrameOccu)) |
| `unmarkedFrameOccuMulti` | ordered/named list of `S` `M x J` detection matrices | preserves species order/names and constructs the `2^S` joint-state and interaction design up to `maxOrder` ([reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFrameOccuMulti)) |
| `unmarkedFrameOccuComm` | named list of `S` `M x J` matrices or an `M x J x S` array | `speciesCovs` is a named collection whose entries may be length `S`, `M x S`, or `M x J x S` ([reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFrameOccuComm)) |

A single generic `y + site_data + obs_data` container is not enough. The shared
frame layer needs named axes and model-specific validation:

- site, visit, species, and primary-period labels;
- explicit layout conversion at the Python boundary and contiguous canonical
  arrays in Rust;
- response domain validation (`0/1/NA` versus non-negative integer/`NA`);
- preserved masks instead of silently losing alignment when covariates are
  missing;
- species covariate broadcasting rules;
- dynamic `site x primary x secondary` indexing; and
- deterministic interaction/state ordering for `occuMulti`.

The reference implementation is permissive in at least one surprising case:
the official overview demonstrates `occu` truncating response values above one
to one with a warning. Strict documented-domain validation is safer for a new
Python API; bug/coercion parity should be an explicit policy rather than an
accidental side effect. See the [official occupancy overview](https://cran.r-project.org/web/packages/unmarked/vignettes/unmarked.html).

## Cross-cutting method contracts

### `predict`

The ordinary fitted-model method accepts a process `type`, optional `newdata`,
original/link-scale selection, missing-value handling, optional appended input
data, confidence level, and random-effect inclusion. Most fits return a table
with `Predicted`, `SE`, `lower`, and `upper`. `type` is not one universal enum:
it is a process name valid for that model. See the official [`predict`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#predict).

There are three distinct dispatch paths that should remain explicit:

- ordinary model prediction, usually delta-method covariance propagation;
- `occuMulti` joint/marginal/conditional bootstrap prediction; and
- `unmarkedRanef` posterior-predictive evaluation of a caller-supplied function,
  whose output gains a final `nsims` dimension.

`predict(fitList, ...)` is a fourth path: it is model-averaged prediction, not
prediction from whichever model has the minimum AIC. Matching the method name
while selecting one model is a semantic incompatibility.

### `fitted`

`fitted` returns expected observations, usually the product of the relevant
state mean and detection probability. Its ordinary shape is the original
`M x J` or `M x (J*T)` response shape. Families with multiple species or
observation processes return named collections of matrices; `occuMulti` and
`occuComm` are in this category. See the official [`fitted`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#fitted).

The result protocol therefore cannot promise only one ndarray. It needs a
documented family-specific structured return and a consistent way to retain
site, visit, species, and time labels.

### `ranef` and posterior state objects

Despite its name, `ranef` estimates empirical-Bayes posterior distributions of
latent abundance or occupancy, not regression random-effect terms. For a
single-season abundance fit its stored posterior has shape
`sites x (K+1)`; for occupancy it has `sites x 2`; for open/dynamic models it
adds a primary-period axis. Some abundance methods accept a replacement `K`,
and multispecies methods accept `species`. The posterior can produce means or
modes, intervals, samples, and posterior-predictive derived quantities. See the
official [`ranef` reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#ranef)
and [`unmarkedRanef` class contract](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedRanef-class).

The manual explicitly warns that empirical Bayes holds fitted hyperparameters
fixed and can underestimate posterior variance; it also recommends the
posterior mean over the posterior mode for abundance. That warning belongs in
the Python documentation and result metadata.

### `parboot`

`parboot` simulates from a fitted model, refits each simulated data set, and
evaluates a user statistic whose first argument is the refitted model. A
statistic may be vector-valued. The result stores the observed vector `t0` and
an `nsim x len(t0)` matrix `t.star`. The default statistic is sum of squared
residuals. See the official [`parboot`
reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#parboot).

This implies a reusable per-family simulation registry and refit recipe, not a
pcount-only coefficient sampler. The bootstrap driver also needs deterministic
seed splitting, parallel execution, preservation of formula/frame metadata,
and an explicit policy for failed refits. The CRAN manual is internally
inconsistent about the default for `parallel` (the usage block says `FALSE`
while prose describes another default), so Python should choose and document a
clear default rather than pretending this detail is unambiguous.

### `fitList`

`fitList` stores already-fitted models for selection and model-averaged
prediction. Upstream requires both the original frame and the effective
response after missing-value removal to be identical across fits. It can name
models from object names or formulas. It supports coefficient and standard-error
extraction, model selection, and model-averaged prediction; regression
coefficient averaging is intentionally not implemented. See the official
[`fitList` reference](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#fitList)
and [`unmarkedFitList` class contract](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFitList-class).

The frame identity/effective-mask check requires a stable frame fingerprint and
retained analysis mask in every result. Model-averaged prediction requires AIC
weights, compatible prediction rows, and a published unconditional-uncertainty
formula.

### `coef` and `confint`

`coef` returns a named numeric vector and can select a process block, use
family-specific alternative names, or include conditional random-effect
coefficients with `fixedOnly=FALSE`. Although the short method page describes
`type` as state/detection, the general fit-class contract allows any process in
`names(fit)`—for example `psi`, `col`, `ext`, and `det` for `colext`, and
`alpha`/`psi` mixture blocks for pcount. See the official [`coef`
method](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#coef-methods)
and [`unmarkedFit` class](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#unmarkedFit-class).

`confint` selects parameters/processes and supports asymptotic normal intervals
or profile-likelihood intervals. Profile intervals require repeated constrained
optimization and cannot be implemented as an alias for a covariance/Wald
interval. Intervals on coefficients are on the fitted parameter scale; response-
scale intervals are prediction/back-transformation behavior. See the official
[`confint` method](https://cran.r-project.org/web/packages/unmarked/refman/unmarked.html#confint-methods).

## Dependency closure for the requested surface

| Requested feature | Required supporting capability not fully named in the request |
| --- | --- |
| All model functions | formula compiler with saved schema/transform state; optimizer; covariance; model-family result protocol; missing-data mask |
| `pcount` | Poisson/NB/ZIP distributions, finite latent summation, `K` diagnostics, optional mixed effects |
| `occu` | Bernoulli two-state mixture, logit and cloglog links, `knownOcc`, optional mixed effects |
| `occuMulti` | species/state combinatorics, interaction design, stable joint-state normalization, penalized likelihood, bootstrap covariance |
| `occuComm` | species mixed-effects engine, variance parameters, conditional effects, population/conditional prediction |
| `colext` | a dynamic/multi-season frame, HMM forward and forward-backward algorithms, transition designs, time-axis metadata |
| `ranef` | complete normalized discrete posterior object, summaries, quantiles, posterior samples, derived posterior prediction |
| `richness` | per-species occupancy posteriors, posterior sampling, RNG control, modeled-species roster |
| `predict` | family registry, retained design encoders, covariance transforms, bootstrap path, model-averaging path, structured outputs |
| `fitted` | family-specific expected-observation operation and response-shape reconstruction |
| `parboot` | `simulate`, refit/update recipe, `residuals`/default SSE, RNG stream management, failure accounting, parallel executor |
| `fitList` | frame/effective-response identity checks, AIC table/weights, model-averaged prediction and unconditional SE |
| `coef` | named parameter blocks, fixed versus conditional effects, family aliases |
| `confint` | covariance/Wald engine plus likelihood profiling and constrained refits |

## Consequences for the Rust core

The existing pcount kernels should remain deep, model-specific modules. The
shared Rust layer should provide only mechanisms that genuinely recur:

1. **Canonical labeled-shape descriptors.** Python owns user-friendly pandas
   ingestion; Rust receives validated contiguous arrays plus explicit axis
   sizes, masks, labels/indices, and design matrices. Multi-species and dynamic
   models cannot be forced into the present `sites x visits` vocabulary.
2. **Links and stable probability math.** Reuse log, logit, cloglog, log-sum-exp,
   Bernoulli/binomial mass, normalized state weights, gradients, and finite-
   value checks.
3. **A likelihood/problem trait with family-owned latent algorithms.** Pcount
   uses a truncated count sum, occu a two-state sum, colext a forward algorithm,
   occuMulti joint-state enumeration, and occuComm a separately specified
   mixed-effects objective.
4. **Optimizer and derivative boundary.** Results need objective value,
   convergence status, gradients, Hessian/covariance, evaluation counts, and
   warnings. Random effects and profile likelihood make a uniform
   finite-difference-only approach unattractive; select automatic
   differentiation or carefully derived gradients under a clean-room spec.
5. **First-class parameter blocks.** A block needs process name, link,
   coefficient names, fixed/random/global role, and tensor/design association.
   Flat vectors remain useful internally, but every public method depends on
   lossless block metadata.
6. **Posterior-state and simulation traits.** `ranef`, `richness`, and `parboot`
   require normalized latent posterior evaluation and simulation from every
   supported family. These should be family methods behind common orchestration,
   not Python reimplementations of Rust likelihood rules.
7. **Resource guards.** `K`, `2^S`, `M*J*T*S`, bootstrap count, and profile
   evaluations can all explode. Validate overflow, estimate allocation/work,
   allow cancellation, and report limits before starting.

## Consequences for the Python API

Python should own ergonomic construction, labels, formula syntax, dispatch, and
tabular presentation while leaving probability kernels and posterior
normalization in Rust.

- Add model-specific immutable frames for occupancy, interacting-species,
  community, and dynamic data. A base protocol may expose common accessors, but
  must not erase axes.
- Store a fitted design encoder—not only formula text and output column names—so
  categorical levels, contrasts, transformations such as `scale()`, interaction
  expansion, and random-effect group levels are reproduced for `newdata`.
- Decide whether the stable Python API uses separate formulas (more Pythonic) or
  also accepts the R double-RHS form. In either case provide an unambiguous
  detection/state order and preserve the R-compatible aliases at the dispatch
  layer.
- Define one common result protocol for likelihood, AIC, convergence,
  covariance, parameter blocks, frame fingerprint, analysis mask, prediction,
  fitted values, simulation, and latent posterior; return concrete family
  result classes for family-specific behavior.
- Return labeled pandas/xarray-like objects or small typed result containers for
  multispecies and time-indexed outputs. A bare ndarray or an ad hoc list loses
  too much ecological identity.
- Keep normal/profile confidence intervals and covariance/bootstrap uncertainty
  visibly distinct. Do not silently fall back from an unsupported method.
- Preserve existing explicit `lambda` versus marginal-abundance names, while
  adding upstream aliases such as `state` and `det` with documented mappings.

## Compatibility decisions and validation matrix

Before implementation, the project should write one clean-room specification
per likelihood family and decide whether “compatibility” means mathematical
equivalence, Pythonic feature equivalence, or R call/return parity. At minimum,
black-box fixtures should cover:

| Area | Required cases |
| --- | --- |
| Frames | all accepted covariate layouts; labels/order; `NA` in response/site/observation covariates; binary/count domain errors; species broadcasting; dynamic flatten/unflatten |
| Formula design | intercept/no-intercept; numeric and categorical terms; interactions; transformations retained into newdata; unseen levels; random intercept/slope syntax |
| `pcount` | P/NB/ZIP likelihoods; extra block names/scales; ZIP component versus marginal mean; several `K`; missing visits; posterior normalization |
| `occu` | detected/all-zero histories; `knownOcc`; logit/cloglog; site and visit covariates; random-effect include/exclude prediction |
| `colext` | `T=1` edge; transitions; missing whole periods; time-varying covariates; forward likelihood; smoothed posterior sums; projected recursion |
| `occuMulti` | `S=2/3`; state ordering; fixed-zero interaction; reduced `maxOrder`; marginal/co-occurrence/conditional prediction; penalty and bootstrap covariance |
| `occuComm` | automatic eligible random slopes; species-only covariate; conditional versus population prediction; species output order; richness posterior and seeded reproducibility |
| Methods | `fitted` shapes; process-specific `predict`; vector `parboot` statistic and failed refit; incompatible `fitList`; model-averaged prediction; fixed-only coefficients; normal versus profile CI |

Several details are insufficiently specified or internally inconsistent in the
manual and must be locked down with documented public black-box tests rather
than source inspection: exact random-effect integration and covariance
approximation, model-averaged unconditional SE, all missing-data retention
rules, bootstrap/refit failure behavior, and the `parboot` parallel default.

## Public black-box observations used to disambiguate the manual

The following were checked through documented public calls against locally
installed `unmarked` 1.5.1. They are observations for compatibility tests, not
implementation instructions.

- Pcount fit process names are `state, det`, with `alpha` added for NB and `psi`
  for ZIP. Coefficients for the extra blocks are on link scales; their
  predictions are on natural scales. ZIP `type="state"` returned
  `exp(eta_lambda) * (1 - psi)`. With fixed `lambda=5`, `p=0.8`, and `psi=0.3`,
  `fitted()` returned `1.96 = 5 * 0.8 * 0.7^2` instead of the documented
  expectation `2.8`; this is the ZIP compatibility defect discussed above.
- `occu` returned `M x J` fitted values and an `M x 2` latent posterior.
  Pcount returned `M x J` fitted values and an `M x (K+1)` posterior.
- `colext` exposed `psi, col, ext, det`, returned `M x (J*T)` fitted values, and
  returned an `M x 2 x T` latent posterior.
- `occuMulti` fitted values were a species-named list of `M x J` matrices. Joint
  state prediction returned matrices grouped as `Predicted/SE/lower/upper`;
  marginal and conditional requests returned ordinary four-column tables.
- `occuComm` fitted and predicted values were species-named collections.
  `richness(..., posterior=TRUE)` stored `M x 1 x nsims` draws, and changing the
  RNG seed changed `richness(..., posterior=FALSE)` for small `nsims`, confirming
  that the reported point estimates are Monte Carlo summaries.
- `fitList` rejected models fit to different frame objects and returned
  model-averaged four-column prediction tables. Its coefficient extraction was
  a model-by-union-of-coefficients table with missing terms represented as
  missing values.
- A vector-valued `parboot` statistic produced a same-length `t0` and an
  `nsim x length(t0)` `t.star` matrix.

These checks stay within the repository policy permitting `unmarked` as a
black-box behavioral/statistical reference. Future fixtures should record R,
package, platform, seed, input data, and tolerance metadata, while default CI
remains independent of R and network access.

## Recommended implementation order from the dependency graph

1. Freeze frame axes, masks, formula encoders, parameter blocks, result
   protocol, and family registries.
2. Complete pcount method parity on top of the existing likelihoods: structured
   prediction/fitted output, full posterior-state object, simulation/refit, and
   R-compatible aliases.
3. Add fixed-effects `occu`; it is the smallest new likelihood and exercises
   links, frames, prediction, posterior state, bootstrap, and fit lists.
4. Add the dynamic frame and `colext` HMM, reusing occupancy emission math and
   exercising time-indexed posterior output.
5. Add `occuMulti` with explicit exponential resource guards and bootstrap
   prediction/covariance.
6. Specify and build the mixed-effects engine, then add random terms to
   `occu`/`pcount` and implement `occuComm` plus richness.
7. Add profile likelihood, fully generic `parboot`, and model-averaged
   prediction after every family exposes simulate/refit/predict contracts.
8. Promote features only after clean-room equation tests, deterministic Rust
   unit tests, Python shape/label tests, simulation recovery, and optional
   recorded black-box parity checks pass.

This order keeps the shared core deep enough to support the full requested
surface while avoiding premature coupling between fundamentally different
latent-state algorithms.
