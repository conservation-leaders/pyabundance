# pyabundance

pyabundance is an open-source Python library for ecological abundance modelling with a high-performance Rust numerical core.

## Current v0.1 scope

v0.1 scaffolds a clean-room implementation of the single-season Poisson N-mixture / pcount-style repeated-count abundance model:

- matrix-first Python API;
- Rust likelihood engine;
- PyO3 extension imported as `pyabundance._core`;
- SciPy BFGS fitting orchestration;
- synthetic benchmark data and optional R `unmarked::pcount` parity benchmark.

It is **not yet a full replacement for `unmarked`**. Formula interfaces, additional mixtures, standard errors, bootstrap helpers, and more model families are roadmap items.

## Clean-room statement

This project does not copy, translate, or paraphrase GPL R/C++/TMB/Stan source code. The implementation is based on independent mathematical specifications, public documentation, published equations, and black-box output comparisons. R `unmarked` may be used only as a validation/benchmark target.

## Install from source

```bash
python -m venv .venv
. .venv/bin/activate || source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install maturin numpy scipy pandas pytest pytest-benchmark ruff mypy
maturin develop --release
```

## Minimal example

```python
import numpy as np
from pyabundance import pcount, simulate_pcount

rng = np.random.default_rng(1)
n_sites, n_visits = 100, 3
x = rng.normal(size=n_sites)
X = np.column_stack([np.ones(n_sites), x])
W = np.ones((n_sites, n_visits, 1))

beta = np.array([0.2, 0.5])
alpha = np.array([-0.3])
y = simulate_pcount(X, W, beta, alpha, seed=2)

fit = pcount(y, X, W, K=50)
print(fit.summary())
print(fit.predict_lambda()[:5])
```

## Run tests

```bash
cargo fmt --all -- --check
cargo test
cargo clippy --all-targets --all-features -- -D warnings
pytest -q
```

## Run the R parity benchmark

```bash
python benchmarks/generate_pcount_dataset.py
python benchmarks/run_py_benchmark.py
Rscript benchmarks/run_r_unmarked_benchmark.R || true
python benchmarks/compare_benchmarks.py
cat reports/BENCHMARK_RESULTS.md
```

The R step is optional. If R or `unmarked` is unavailable, the comparison report records a `PARTIAL` or `NOT RUN` status and does not invent values.
