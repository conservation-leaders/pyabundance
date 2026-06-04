# Changelog

All notable changes to pyabundance are recorded here. The project follows a pragmatic pre-1.0 semantic-versioning style: minor versions may add public APIs, while patch versions should preserve behavior.

## 1.0.0rc2 - UX hardening / guided workflow

RC2 focuses on UX hardening: guided `analyze_pcount`, `K="auto"` and `suggest_K`, smarter visit-label handling, clearer visit-label errors, `compare_models(names=...)`, `coef_table(as_dataframe=True)`, deterministic explanation/report UX, Mallard validation docs, and performance architecture docs. It adds no new ecological model family and makes no intentional likelihood formula changes.

## 1.0.0rc1 - Release candidate / external alpha

- Prepared release-candidate metadata and documentation.
- Froze the public API for external alpha review.
- Refreshed R black-box parity reports.
- Prepared GitHub release draft and reviewer feedback template.
- Preserved RC1 benchmark artifacts.
- Did not add a new ecological model family or change validated likelihood formulas.

## 0.9.0 - External alpha release rehearsal

- Added guarded TestPyPI Trusted Publishing workflow and documentation.
- Added guarded draft PyPI publishing workflow for future maintainer-approved releases.
- Hardened cross-platform wheel build/smoke workflow.
- Added TestPyPI installation and docs deployment workflows.
- Added benchmark artifact workflow, issue templates, PR template, external-alpha reviewer guide, API freeze review, and release audit reports.
- Added local wheel/sdist/installed-package smoke scripts and dist metadata checks.
- Set conservative coverage threshold at 80%.
- Preserved existing modelling APIs and did not add new ecological model families.

## 0.8.0 - Release engineering and contributor hardening

- Added package metadata, optional dependency groups, mypy config, and coverage config.
- Added CI hardening with lint, type checking, coverage, benchmark artifact upload, and wheel-build workflows.
- Added API reference docs scaffold with MkDocs and mkdocstrings.
- Added tutorial scripts for end-to-end pcount workflows and release smoke checks.
- Added release checklist, release notes, and contributor onboarding docs.
- Added benchmark artifact preservation script and artifact directory.
- Preserved all v0.7 public modelling APIs.

## 0.7.0 - Posterior abundance / ranef-like outputs

- Added empirical-Bayes posterior abundance distributions for Poisson, NB, and ZIP pcount models.
- Added ranef-like summaries, posterior abundance samples, total abundance summaries, and posterior predictive checks.
- Added optional black-box R ranef comparison and posterior abundance benchmark.

## 0.6.0 - Model selection and reporting

- Added AIC tables, model comparison helpers, report exports, prediction DataFrames, and bundled synthetic examples.

## 0.5.0 - Uncertainty and diagnostics

- Added standard errors, confidence intervals, transformed parameter intervals, prediction intervals, residuals, SSE, diagnostics, parametric bootstrap, and optional R SE comparison.

## 0.4.0 - Formula/DataFrame API

- Added pandas-first Formulaic matrix construction and `pcount_df()`.

## 0.3.0 - Zero-inflated Poisson pcount

- Added clean-room zero-inflated Poisson N-mixture support.

## 0.2.0 - Negative-binomial pcount

- Added clean-room negative-binomial N-mixture support.

## 0.1.1 - Cached problem object and profiling

- Added cached Rust-side problem object and benchmark observability for Poisson pcount.

## 0.1.0 - Initial Poisson pcount

- Added clean-room Poisson N-mixture model, Rust core, PyO3 bindings, Python API, tests, and benchmark harness.
