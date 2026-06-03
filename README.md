# pyabundance

pyabundance is an open-source Python library for ecological abundance modelling with a high-performance Rust numerical core.

## Current scope

- v0.1 implemented a clean-room single-season Poisson N-mixture / pcount-style repeated-count model.
- v0.1.1 added cached Rust-side problem objects and profiling/benchmark observability.
- v0.2 added a clean-room negative-binomial N-mixture model.
- v0.3 added a clean-room zero-inflated Poisson N-mixture model.
- v0.4 added a pandas-first Formulaic formula API, named coefficients, notebook-friendly summaries, and examples.
- v0.5 added standard errors, confidence intervals, prediction intervals, parametric bootstrap, residuals, and diagnostics.
- v0.6 added AIC model-selection tables, reporting/export helpers, richer prediction DataFrames, and bundled synthetic examples.
- v0.7 added empirical-Bayes posterior abundance / ranef-like latent abundance outputs and posterior predictive checks.
- v0.8 adds release-engineering hardening, API docs, tutorial scripts, wheel workflows, type-checking, coverage config, and release checklists.
- v0.9 adds external-alpha release rehearsal: TestPyPI Trusted Publishing workflow, guarded PyPI draft workflow, cross-platform wheel smoke workflows, docs deployment workflow, issue/PR templates, API freeze review, and release audit reports.

The matrix API remains the lowest-overhead path: users pass a count matrix `y`, abundance design matrix `X`, and detection design tensor `W`. The new `pcount_df()` API builds those matrices from pandas DataFrames and RHS-only fixed-effect formulas.

pyabundance is **not yet a full replacement for `unmarked`**. Open/dynamic N-mixture models, spatial models, random effects, release-candidate polish and external-review feedback remain roadmap items.

## Clean-room statement

This project does not copy, translate, inspect, or paraphrase GPL R/C/C++/TMB/Stan source code. The implementation is based on independent mathematical specifications, public documentation, published equations, and black-box output comparisons. R `unmarked` may be used only as a validation/benchmark target.

## Install from source

```bash
python -m venv .venv
. .venv/bin/activate || source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
maturin develop --release
```

## DataFrame/formula quick start

```python
import numpy as np
import pandas as pd
from pyabundance import pcount_df

rng = np.random.default_rng(1)
df = pd.DataFrame(
    {
        "y1": [0, 1, 2, 1, 0, 3],
        "y2": [1, 1, 1, 0, 0, 2],
        "y3": [0, 2, 1, 1, 0, 3],
        "forest": rng.normal(size=6),
    }
)

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

Observation covariates can be supplied in long format:

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

Formula support is intentionally limited in v0.4 to RHS-only fixed effects such as `"~ x"`, `"~ visit - 1"`, `"~ x:visit"`, and `"~ x * visit"`. Random effects, offsets, response-side formulas, smooths, and dynamic/open N-mixture models are not implemented.




## Posterior abundance quick start

```python
from pyabundance import load_example_pcount, pcount_df

data = load_example_pcount("poisson")
fit = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    mixture="poisson",
    K=data.K,
)

ranef = fit.ranef()
print(ranef.head())

total = fit.total_abundance_posterior(nsim=1000, seed=123)
print(total.summary())

ppc = fit.posterior_predictive_check(statistic="zero_count", nsim=100, seed=123)
print(ppc)
```

Posterior abundance distributions condition on fitted model parameters. They are empirical-Bayes / ranef-like summaries, not full Bayesian posterior inference over model parameters.

## Model selection and reporting quick start

```python
from pyabundance import aic_table, load_example_pcount, pcount_df

data = load_example_pcount("poisson")
fit_p = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    mixture="poisson",
    K=data.K,
)
fit_nb = pcount_df(
    site_data=data.site_data,
    count_cols=data.count_cols,
    abundance_formula=data.abundance_formula,
    detection_formula=data.detection_formula,
    mixture="negative_binomial",
    K=100,
)
print(aic_table({"poisson": fit_p, "negative_binomial": fit_nb}))

fit_p.export_summary("reports/example_model.md")
print(fit_p.fitted_counts_dataframe().head())
```

AIC tables are convenience summaries for comparable models fitted to the same data. They do not replace convergence checks, diagnostics, or ecological judgement.

## Uncertainty quick start

```python
fit = pcount(y, X, W, K=60, mixture="poisson", se=True, cov_method="bfgs")
print(fit.coef_table())
print(fit.confint())

lambda_ci = fit.predict_lambda(se=True, interval=True)
boot = fit.parametric_bootstrap(nsim=20, statistic="sse", seed=1)
print(boot.summary())
```

Uncertainty methods are approximate. BFGS standard errors use the optimizer inverse-Hessian approximation; finite-difference Hessians can be slow; bootstrap intervals are more computationally expensive but useful for model checking. Always inspect convergence and diagnostics.

## Matrix API examples

Poisson:

```python
import numpy as np
from pyabundance import pcount, simulate_pcount

rng = np.random.default_rng(1)
n_sites, n_visits = 100, 3
x = rng.normal(size=n_sites)
X = np.column_stack([np.ones(n_sites), x])
W = np.ones((n_sites, n_visits, 1))

y = simulate_pcount(X, W, beta=np.array([0.2, 0.5]), alpha=np.array([-0.3]), seed=2)
fit = pcount(y, X, W, K=50, mixture="poisson")
print(fit.summary())
```

Negative binomial:

```python
from pyabundance import simulate_pcount_negbin

y = simulate_pcount_negbin(X, W, beta=[0.2, 0.5], detection=[-0.3], r=1.5, seed=4)
fit = pcount(y, X, W, K=100, mixture="negative_binomial")
print(fit.r)
```

Zero-inflated Poisson:

```python
from pyabundance import simulate_pcount_zip

y = simulate_pcount_zip(X, W, beta=[0.2, 0.5], detection=[-0.3], psi=0.2, seed=5)
fit = pcount(y, X, W, K=100, mixture="zero_inflated_poisson")
print(fit.psi)
```

Supported mixture aliases:

- Poisson: `"poisson"`, `"P"`
- Negative binomial: `"negative_binomial"`, `"negbin"`, `"NB"`
- Zero-inflated Poisson: `"zero_inflated_poisson"`, `"zip"`, `"ZIP"`

ZIP models can be weakly identified because low detection, low abundance, and structural zeros can all create many observed zero counts. Inspect convergence and compare against Poisson/NB alternatives.


## Release engineering

v0.9 includes contributor-facing release rehearsal infrastructure:

- `mkdocs.yml` and `docs/api/` for API reference documentation;
- tutorial smoke scripts under `docs/tutorials/`;
- CI workflows for tests, coverage, type checking, benchmark artifact upload, and maturin wheel builds;
- `scripts/smoke_test_wheel.py` for clean wheel-install checks;
- `scripts/preserve_benchmark_artifacts.py` for saving benchmark reports;
- `CHANGELOG.md` and `docs/release/RELEASE_CHECKLIST.md`;
- guarded `publish-testpypi.yml`, `publish-pypi.yml`, `testpypi-install.yml`, `docs.yml`, and `benchmarks.yml`;
- issue/PR templates and `docs/release/EXTERNAL_ALPHA_REVIEW.md`.

Release rehearsal commands:

```bash
maturin build --release --out dist
python -m venv .wheel-test
. .wheel-test/bin/activate || source .wheel-test/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python scripts/smoke_test_wheel.py --from-installed
```

See `docs/release/TESTPYPI_REHEARSAL.md` for TestPyPI Trusted Publishing setup. Real PyPI publishing is guarded and documented in `docs/release/PYPI_RELEASE_PROCESS.md`.

## Run tests

```bash
cargo fmt --all -- --check
cargo test
cargo clippy --all-targets --all-features -- -D warnings
ruff format --check .
ruff check .
mypy python/pyabundance
pytest -q
pytest --cov=pyabundance --cov-report=term-missing --cov-report=xml --cov-fail-under=80
```

## Run benchmarks

Poisson:

```bash
python benchmarks/generate_pcount_dataset.py
python benchmarks/run_py_benchmark.py
python benchmarks/run_py_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_benchmark.R || true
python benchmarks/compare_benchmarks.py
```

Negative binomial:

```bash
python benchmarks/generate_pcount_nb_dataset.py
python benchmarks/run_py_nb_benchmark.py
python benchmarks/run_py_nb_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_nb_benchmark.R || true
python benchmarks/compare_nb_benchmarks.py
```

Zero-inflated Poisson:

```bash
python benchmarks/generate_pcount_zip_dataset.py
python benchmarks/run_py_zip_benchmark.py
python benchmarks/run_py_zip_loglik_benchmark.py
Rscript benchmarks/run_r_unmarked_zip_benchmark.R || true
python benchmarks/compare_zip_benchmarks.py
```

Formula overhead:

```bash
python benchmarks/run_formula_overhead_benchmark.py
cat reports/FORMULA_OVERHEAD_BENCHMARK.md
```

Summary:

```bash
python benchmarks/compare_benchmark_summary.py
python benchmarks/run_reporting_workflow.py
cat reports/BENCHMARK_SUMMARY.md
```

R benchmark steps are optional. If R or `unmarked` is unavailable, reports record `PARTIAL` or `NOT RUN` and do not invent values.

Local benchmarks show strong performance on simple synthetic tests. These are not general performance claims; optimizer paths, hardware, data shape, model family, and package versions can change results. The matrix API remains the most direct and lowest-overhead interface for advanced users and benchmarking.
