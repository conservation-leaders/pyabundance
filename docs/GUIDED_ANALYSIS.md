# Guided pcount analysis

`analyze_pcount()` is the beginner-friendly entry point for common single-season pcount-style N-mixture workflows. It builds formula matrices once, resolves `K="auto"`, fits candidate Poisson, negative-binomial, and zero-inflated Poisson models, compares successful fits by AIC, stores failures instead of stopping the whole workflow, and produces deterministic explanations and markdown reports.

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

Use `pcount_df()` when you want one explicit formula model. Use `pcount()` when you already have `y`, `X`, and `W` matrices and want full control. The `_core` extension is internal and not part of the stable public API.

`explain()` is rule-based text, not AI-generated interpretation. It reports the lowest-AIC model, flags overdispersion or ZIP identifiability cautions when relevant, and reminds users that posterior abundance summaries condition on fitted parameters.
