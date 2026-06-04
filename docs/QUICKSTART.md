# Quickstart

```python
from pyabundance import compare_models, load_example_pcount, pcount_df

example = load_example_pcount("poisson")

fit = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula=example.abundance_formula,
    detection_formula=example.detection_formula,
    mixture="poisson",
    K=example.K,
    se=True,
)

print(fit.summary())
print(fit.coef_table())
print(fit.ranef().head())

intercept = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula="~ 1",
    detection_formula=example.detection_formula,
    mixture="poisson",
    K=example.K,
)

print(compare_models({"covariate": fit, "intercept": intercept}).summary())
```

Use `pcount(...)` directly when you already have a count matrix, abundance design matrix, and detection design tensor.
