# pyabundance

pyabundance is a clean-room Python library for ecological abundance modelling with a high-performance Rust numerical core.

## What it does

- Fits single-season pcount-style N-mixture models.
- Supports Poisson, negative-binomial, and zero-inflated Poisson mixtures.
- Provides a matrix API for direct numerical workflows.
- Provides a pandas/Formulaic API for ecological data workflows.
- Includes standard errors, confidence intervals, bootstrap tools, diagnostics, AIC model comparison, reporting helpers, and posterior abundance / ranef-like summaries.

## Current status

pyabundance is at external-alpha / release-candidate stage (`1.0.0rc1`). It is ready for reviewer installation and workflow feedback, but it is not yet a final stable v1.0 release.

Not yet implemented:

- open/dynamic N-mixture models;
- distance sampling;
- spatial models;
- random effects;
- full Bayesian posterior parameter uncertainty.

## Install

Source install:

```bash
python -m venv .venv
. .venv/bin/activate || source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
maturin develop --release
```

TestPyPI rehearsal install, after maintainers publish the release candidate:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pyabundance==1.0.0rc1
```

## Quick start

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

## Core APIs

- `pcount(...)`: matrix/tensor API.
- `pcount_df(...)`: pandas + Formulaic API.
- `build_pcount_matrices(...)`: formula-to-matrix builder.
- `compare_models(...)` and `aic_table(...)`: model comparison.
- `PCountResult`: summaries, prediction, uncertainty, diagnostics, reporting, posterior abundance, and posterior predictive checks.

## Documentation

- Formula API: `docs/FORMULA_API.md`
- Uncertainty: `docs/UNCERTAINTY.md`
- Posterior abundance: `docs/POSTERIOR_ABUNDANCE.md`
- Model selection/reporting: `docs/MODEL_SELECTION_REPORTING.md`
- Benchmarks: `docs/benchmarks/BENCHMARKS.md`
- Limitations: `docs/LIMITATIONS.md`
- External alpha review: `docs/release/EXTERNAL_ALPHA_REVIEW.md`

## Clean-room statement

This project does not copy, inspect, translate, paraphrase, or mechanically port GPL R/C/C++/TMB/Stan source code. The implementation is based on independent mathematical specifications, public documentation, published equations, and black-box output comparisons. R `unmarked` may be used only as a validation/benchmark target.

## Development

See `CONTRIBUTING.md` and `docs/development/REPOSITORY_HYGIENE.md`. Generated benchmark outputs, reports, wheels, coverage files, and local artifacts are ignored by git and can be regenerated from scripts.
