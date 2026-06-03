# External Alpha Review Guide

This guide helps early ecological modelling reviewers try pyabundance without reading internal implementation details.

## Installation options

### From wheel artifact

Download a wheel from a GitHub Actions artifact, then run:

```bash
python -m pip install pyabundance-*.whl
python scripts/smoke_test_installed.py --expected-version 1.0.0rc1
```

### From TestPyPI

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pyabundance==1.0.0rc1
```

### From source

```bash
python -m pip install -e '.[dev]'
maturin develop --release
pytest -q
```

## 15-minute smoke tutorial

```python
from pyabundance import compare_models, load_example_pcount, pcount_df

data = load_example_pcount("poisson", n_sites=80, seed=20260612)
poisson = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula="~ visit - 1",
    mixture="poisson",
    K=data.K,
    se=True,
)
nb = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula="~ visit - 1",
    mixture="negative_binomial",
    K=100,
)
print(compare_models({"P": poisson, "NB": nb}).summary())
print(poisson.coef_table())
print(poisson.ranef().head())
print(poisson.to_markdown(include_posterior_abundance=True))
```

## Reviewer questions

- Is the API understandable?
- Are formulas intuitive for ecologists coming from R?
- Are summaries clear and not overconfident?
- Are uncertainty warnings clear?
- Are posterior abundance outputs understandable?
- Are docs sufficient to start without maintainer help?
- What blocks real ecological use?

## Issue types

Use the issue templates for bugs, docs, features, and statistical concerns.

## Clean-room reminder

Do not paste GPL source code, translated source snippets, or package internals from other projects into issues or pull requests. Describe equations, public behavior, or black-box outputs instead.
