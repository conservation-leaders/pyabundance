# Model Selection and Reporting

v0.6 adds applied-workflow helpers for comparing fitted pcount models, exporting summaries, and building tidy prediction tables.

## AIC tables

```python
from pyabundance import aic_table, compare_models

table = aic_table({
    "poisson": fit_p,
    "negative_binomial": fit_nb,
    "zip": fit_zip,
})
print(table)
```

The table includes log-likelihood, number of parameters, AIC, delta AIC, AIC weights, convergence status, and formula metadata when available.

`compare_models()` returns a small object with the table and the original fitted models:

```python
comparison = compare_models({"P": fit_p, "NB": fit_nb})
print(comparison.summary())
best = comparison.best_model
```

AIC weights are descriptive model-selection summaries. They are not proof that a model is true, and users should still inspect convergence, residuals, uncertainty, and ecological plausibility.

## Prediction DataFrames

Matrix-returning prediction methods still work. v0.6 adds tidy DataFrame helpers:

```python
fit.abundance_dataframe(se=True, interval=True)
fit.detection_dataframe(se=True, interval=True)
fit.fitted_counts_dataframe()
fit.residuals_dataframe(kind="pearson")
```

For formula/DataFrame fits, site IDs and visit labels are preserved when available.

## Exporting reports

```python
fit.export_summary("model_report.json")
fit.export_summary("model_report.md")
fit.export_summary("coefficients.csv")
```

Standalone helpers are also available:

```python
from pyabundance import model_report, export_model_report

report = model_report(fit)
export_model_report(fit, "model_report.md")
```

JSON exports include model metadata, coefficient tables, transformed parameters, diagnostics, convergence information, and covariance diagnostics. Markdown exports are intended for quick human-readable reports. CSV exports write the coefficient table.

## Bundled synthetic examples

```python
from pyabundance import load_example_pcount

data = load_example_pcount("poisson")
fit = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    K=data.K,
)
```

Available synthetic examples are `"poisson"`, `"negative_binomial"`, and `"zip"`. They are generated deterministically on demand and are intended for tutorials, examples, and smoke tests rather than scientific inference.

## Limitations

- AIC tables assume models are fit to comparable data.
- Model-selection helpers do not automate ecological interpretation.
- Export helpers are lightweight and intentionally dependency-free.
- Prediction helpers use stored design matrices; constructing new design matrices from new DataFrames remains a future enhancement.

## Posterior abundance note

See `docs/POSTERIOR_ABUNDANCE.md` for ranef-like latent abundance summaries and posterior predictive checks. These condition on fitted parameters and should be interpreted separately from uncertainty intervals over fitted coefficients.

## Guided workflow

For the beginner-friendly guided workflow, see [Guided analysis](GUIDED_ANALYSIS.md).
