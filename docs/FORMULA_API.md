# Formula API

pyabundance has two pcount APIs:

```python
pcount(y, X, W, ...)
pcount_df(site_data=..., count_cols=..., abundance_formula=..., detection_formula=...)
```

Use `pcount()` when you already have NumPy design matrices and want the lowest-overhead path. Use
`pcount_df()` for a pandas-first workflow with Formulaic fixed-effect formulas.

## Basic example

```python
from pyabundance import pcount_df

fit = pcount_df(
    site_data=df,
    count_cols=["y1", "y2", "y3"],
    abundance_formula="~ forest",
    detection_formula="~ visit - 1",
    mixture="poisson",
    K=60,
)
print(fit.summary())
```

`count_cols` defines the visit order. If `visit_labels` is not supplied, the count-column names are
also used as visit labels.

## Observation covariates

For observation-level covariates, pass long-format `obs_data`. In v0.4, explicit site IDs are
required when `obs_data` is supplied.

```python
fit = pcount_df(
    site_data=site_df,
    obs_data=obs_df,
    site_id_col="site_id",
    visit_col="visit",
    count_cols=["v1", "v2", "v3"],
    abundance_formula="~ forest + elevation",
    detection_formula="~ wind + observer",
    mixture="negative_binomial",
    K=100,
)
```

`obs_data` must contain exactly one row per site × visit. Rows may be out of order; pyabundance sorts
them internally to match the site order in `site_data` and the visit order in `count_cols` or
`visit_labels`.

## ZIP example

```python
fit = pcount_df(
    site_data=df,
    count_cols=["y1", "y2", "y3"],
    abundance_formula="~ x",
    detection_formula="~ visit - 1",
    mixture="zero_inflated_poisson",
    K=100,
)
print(fit.psi)
```

ZIP models can be weakly identified because low detection, low abundance, and structural zeros can all
produce many observed zeros. Inspect convergence and compare against Poisson and NB alternatives.

## Building matrices without fitting

```python
from pyabundance import build_pcount_matrices

matrices = build_pcount_matrices(
    site_data=df,
    count_cols=["y1", "y2", "y3"],
    abundance_formula="~ x",
    detection_formula="~ visit - 1",
)
print(matrices.X.shape, matrices.W.shape)
print(matrices.abundance_column_names)
print(matrices.detection_column_names)
```

## Current limitations

- no response-side formulas;
- no random effects;
- no offsets;
- no smooths or splines;
- no dynamic/open N-mixture models;
- no spatial models;
- formulas are used only to build fixed-effect design matrices.

Unsupported formula features raise `ValueError` with a v0.4 limitation message.

## Uncertainty

The DataFrame API supports the same uncertainty options as the matrix API:

```python
fit = pcount_df(
    site_data=df,
    count_cols=["y1", "y2", "y3"],
    abundance_formula="~ x",
    detection_formula="~ visit - 1",
    mixture="poisson",
    K=60,
    se=True,
    cov_method="bfgs",
)
print(fit.coef_table())
```

Formulaic coefficient names are preserved in `summary()` and `coef_table()`.


## RC2 guided workflow note

`analyze_pcount()` is the easiest entry point for common pcount analyses. `K="auto"` resolves a conservative integration limit once before fitting. `visit_labels="auto"` can infer observation visit labels when count columns and visit labels use different names.
