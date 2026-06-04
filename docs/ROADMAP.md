# Roadmap

## v0.1

- Poisson N-mixture / pcount
- matrix-first API
- Rust likelihood core
- Python fit/result API
- synthetic benchmark
- optional R parity benchmark

## v0.1.1

- cached Rust-side Poisson problem object
- direct likelihood benchmark
- Python fit profiling
- optimizer function-evaluation reporting
- performance notes

## v0.2

- negative-binomial N-mixture
- cached NB problem object
- NB direct likelihood benchmark
- optional R unmarked NB parity benchmark
- benchmark summary

## v0.3

- zero-inflated Poisson N-mixture
- cached ZIP problem object
- ZIP direct likelihood benchmark
- optional R unmarked ZIP parity benchmark
- benchmark summary

## v0.4

- pandas-first pcount workflow
- Formulaic-based RHS-only fixed-effect formula interface
- named abundance and detection coefficients
- notebook-friendly summaries with model metadata
- formula overhead benchmark
- DataFrame/formula examples and documentation

## v0.5

- standard errors
- confidence intervals
- covariance diagnostics
- prediction confidence intervals
- parametric bootstrap
- prediction intervals
- residual diagnostics
- optional R SE comparison report

## v0.6

- AIC tables
- compare_models()
- model-selection and reporting utilities
- richer prediction/reporting DataFrames
- exportable summaries
- bundled synthetic example datasets
- fuller documentation examples using bundled data

## v0.7

- posterior abundance distribution / ranef-like output
- empirical Bayes summaries for latent abundance N
- site-level abundance interval summaries
- posterior abundance samples and total abundance summaries
- posterior predictive checks based on latent abundance
- optional R ranef-style black-box comparison

## v0.8

- API reference docs
- tutorial notebooks
- CI wheel-building with maturin
- type-checking hardening
- coverage reporting
- changelog/release notes
- package metadata audit
- publishing test wheels
- benchmark dashboard or saved benchmark artifacts
- contributor onboarding docs

## v0.9

- external-alpha release rehearsal
- TestPyPI Trusted Publishing workflow and install smoke workflow
- guarded real-PyPI workflow draft
- cross-platform wheel matrix validation
- docs deployment workflow
- issue and pull-request templates
- API freeze review
- dependency/security audit
- benchmark artifact preservation
- external alpha reviewer guide

## v1.0 candidate

- run TestPyPI workflow and install from TestPyPI on clean Linux/macOS/Windows
- invite 2-5 external ecological modelling reviewers
- freeze public API
- fix feedback-only issues
- final R parity refresh
- final wheel matrix
- real PyPI release approval
- GitHub release draft
- tag v1.0.0-rc1

## v1.0

- Stable public API
- documentation site
- validated examples
- R parity fixture suite
- wheels for Linux/macOS/Windows
- contribution governance


## RC2 guided workflow note

`analyze_pcount()` is the easiest entry point for common pcount analyses. `K="auto"` resolves a conservative integration limit once before fitting. `visit_labels="auto"` can infer observation visit labels when count columns and visit labels use different names.
