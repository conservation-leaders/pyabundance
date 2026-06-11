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
`visit_labels`. If `obs_data` visit labels differ from `count_cols`, `visit_labels="auto"` is safe
only when `obs_data[visit_col]` is an ordered pandas Categorical. Otherwise pass explicit
`visit_labels` in the order matching `count_cols`.

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

## Predicting on new data

Formula newdata prediction is supported for fitted `pcount_df()` models. The
fit stores the abundance and detection formulas, then reuses them to build
compatible design matrices for new site and observation data.

```python
new_sites = pd.DataFrame(
    {
        "site_id": ["new-1", "new-2"],
        "forest": [0.2, 0.8],
    }
)

new_obs = pd.DataFrame(
    {
        "site_id": ["new-1", "new-1", "new-2", "new-2"],
        "visit": ["v1", "v2", "v1", "v2"],
        "wind": [0.1, 0.3, 0.2, 0.4],
    }
)

lambda_hat = fit.predict(type="lambda", new_site_data=new_sites)
p_hat = fit.predict(type="detection", new_site_data=new_sites, new_obs_data=new_obs)
fitted_counts = fit.predict(type="fitted", new_site_data=new_sites, new_obs_data=new_obs)
```

The shared-core dispatcher accepts the same arguments:

```python
from pyabundance.core import predict

predict(fit, type="lambda", new_site_data=new_sites)
predict(fit, type="p", new_site_data=new_sites, new_obs_data=new_obs)
```

`type="lambda"` and `type="abundance"` produce one row per `new_site_data` row.
`type="p"`/`"detection"` and `type="fitted"` produce an
`n_new_sites × n_visits` array. Use `as_dataframe=True` for labeled lambda and
detection outputs.

For detection prediction, `new_obs_data` is long format with one row per
site × visit. By default pyabundance uses:

- `site_id_col="site_id"` when that column is present in `new_site_data`;
- `visit_col="visit"`;
- `visit_labels=fit.visit_labels`.

You can override these with `site_id_col=...`, `visit_col=...`, and
`visit_labels=[...]`. If `new_obs_data` is omitted, pyabundance generates
default observation rows by crossing `new_site_data` with the resolved visit
labels and carrying site covariates into the observation-level formula. This is
useful when the detection formula uses `visit` and/or site-level covariates.

Matrix fits created with `pcount(y, X, W, ...)` do not have formula metadata for
newdata prediction. Continue to use matrix methods for those fits:

```python
fit.predict_lambda(X=new_X)
fit.predict_detection(W=new_W)
```

Requests for formula newdata from matrix fits raise a formula-metadata-required
error. Stage 7 does not include Stage 8 parity helpers or new model families.

## Current limitations

- no response-side formulas;
- no random effects;
- no offsets;
- no smooths or splines;
- no dynamic/open N-mixture models;
- no spatial models;
- formulas are used only to build fixed-effect design matrices and pcount
  formula newdata predictions.

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

## Guided workflow

For the beginner-friendly guided workflow, see [Guided analysis](GUIDED_ANALYSIS.md).
