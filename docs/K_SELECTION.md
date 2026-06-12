# K selection and sensitivity for pcount

`K` is the upper integration limit used when fitting closed-population pcount
(N-mixture) models. It must be at least as large as the largest observed count.
If `K` is too small, fitted likelihoods and downstream summaries can be
sensitive to the truncation rather than to the ecological signal.

## Suggesting a conservative K

```python
from pyabundance import suggest_K

K = suggest_K(y)
```

`suggest_K()` is a lightweight input helper. It ignores missing counts,
validates that observed counts are non-negative integers, and returns a
conservative integer based on the maximum observed count.

## Refitting across candidate K values

Stage 8A adds a pcount-specific sensitivity helper in `pyabundance.k_selection`:

```python
from pyabundance import pcount
from pyabundance.k_selection import pcount_k_sensitivity

fit = pcount(y, X, W, K=40)
sensitivity = pcount_k_sensitivity(fit, Ks=[40, 60, 80])

print(sensitivity.table)
print(sensitivity.summary())
best_refit = sensitivity.best_fit
```

The helper accepts an existing `PCountResult`, refits the same pcount
specification across candidate `K` values with the existing `pcount()` fitting
path, and returns a compact result with:

- `table`: a pandas DataFrame containing `K`, `logLik`, `AIC`, `delta_AIC`,
  `n_params`, `success`, `message`, `nfev`, `nit`, and
  `max_abs_param_delta` versus the reference fit;
- `fits`: a mapping from integer `K` to the refit `PCountResult`;
- `reference_fit`: the original fit, which is not modified;
- `best_K` and `best_fit`: lowest-AIC convenience accessors when available;
- `summary()`: a concise text summary.

Candidate values are sorted by increasing `K` for deterministic output.
Duplicate candidates and empty candidate lists are rejected. Every candidate
must be greater than or equal to the maximum observed count. As a small
convenience, candidates can also be generated with an inclusive range:

```python
sensitivity = pcount_k_sensitivity(fit, min_K=40, max_K=80, step=20)
```

By default, refits use the reference fit's optimizer method and a copy of the
reference parameter vector as the start values. Formula/DataFrame metadata,
column names, site IDs, visit labels, and data-shape metadata are preserved in
refits where available.

## Scope and non-goals

This is a pcount-specific diagnostic helper. It does not change likelihood math,
Rust likelihood formulas, or Rust likelihood hot paths. It does not add a new
ecological model family, `occu`, distance-sampling models, dynamic/open models,
parameter mapping helpers, generic simulation facades, or generic
parametric-bootstrap facades.
