# Guided pcount analysis

`analyze_pcount()` is the beginner-friendly entry point for common single-season pcount-style N-mixture workflows. It is designed for applied ecology users who want a Python-first path without giving up transparent model objects or the lower-level APIs.

pyabundance modernizes pcount-style abundance analysis by combining:

- Python data workflows with pandas and Formulaic;
- Rust likelihood kernels for hot numerical paths;
- validation against R/unmarked as a black-box comparison target;
- a guided interface for routine analysis;
- power-user matrix controls through `pcount()`.

The guided workflow is orchestration over the same fitted models, not a different statistical model.

```python
from pyabundance import analyze_pcount, load_example_pcount

data = load_example_pcount("poisson")
analysis = analyze_pcount(
    site_data=data.site_data,
    obs_data=data.obs_data,
    site_id_col="site_id",
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    K="auto",
)

print(analysis.summary())
print(analysis.explain())
analysis.export_report("abundance_report.md")
```

## What the guided workflow does

- builds count, abundance, and detection matrices once;
- safely infers differing observation visit labels only when the visit column is an ordered pandas Categorical;
- resolves `K="auto"` once before fitting;
- fits candidate Poisson, negative-binomial, and zero-inflated Poisson models;
- compares successful fits by AIC;
- keeps failed candidate details instead of crashing the whole analysis;
- records warnings and deterministic explanation text;
- exports concise markdown reports.

`explain()` is rule-based text, not AI-generated interpretation. It reports the lowest-AIC model, flags overdispersion or ZIP identifiability cautions when relevant, and reminds users that posterior abundance summaries condition on fitted parameters.

## Visit label safety

When `obs_data` is provided, `visit_labels="auto"` is conservative. If observation visit labels match `count_cols`, count columns define the order. If observation visit labels differ from `count_cols`, auto-inference requires `obs_data[visit_col]` to be an ordered pandas Categorical. Otherwise pass explicit `visit_labels` in the order matching `count_cols`. This avoids silently pairing count columns with observation covariates in the wrong visit order.

## Escape hatches

Use `pcount_df()` when you want one explicit formula model. Use `pcount()` when you already have `y`, `X`, and `W` matrices and want full control over `K`, starts, optimizer, covariance method, and outputs. The `_core` extension is internal and not part of the stable public API.
