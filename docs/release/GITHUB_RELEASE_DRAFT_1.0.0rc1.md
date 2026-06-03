# pyabundance v1.0.0-rc1

pyabundance `1.0.0rc1` is a release candidate / external alpha for a clean-room Rust + Python ecological abundance modelling library.

This is **not** the final stable v1.0 release. It is intended for external installation, documentation, API, and statistical workflow review.

## Install from TestPyPI

After maintainers run the TestPyPI publishing workflow:

```bash
python -m pip install --upgrade pip
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pyabundance==1.0.0rc1
python scripts/smoke_test_installed.py --expected-version 1.0.0rc1
```

## Install from wheel artifact

Download the wheel artifact from GitHub Actions and run:

```bash
python -m pip install pyabundance-1.0.0rc1-*.whl
python scripts/smoke_test_installed.py --expected-version 1.0.0rc1
```

## Major features

- Single-season pcount-style N-mixture models:
  - Poisson;
  - negative-binomial;
  - zero-inflated Poisson.
- High-performance Rust likelihood core with PyO3 bindings.
- Matrix API and pandas/Formulaic API.
- Standard errors, confidence intervals, transformed parameters, prediction intervals, bootstrap, residual diagnostics, model comparison, reporting helpers, and posterior abundance / ranef-like outputs.

## Current limitations

- no open/dynamic N-mixture models;
- no distance sampling;
- no spatial models;
- no random effects;
- empirical-Bayes abundance intervals condition on fitted parameters;
- asymptotic SEs can be unreliable with weak data;
- local synthetic benchmarks are not general performance claims.

## Clean-room statement

This project does not copy, inspect, translate, paraphrase, or mechanically port R/C/C++/TMB/Stan source code from GPL packages. R/unmarked is used only as a black-box validation and benchmark target.

## Reviewer request

Please try the external alpha guide and file issues using the templates. Do not paste GPL source code into issues or PRs.

Recommended reviewer docs:

- `docs/release/EXTERNAL_ALPHA_REVIEW.md`
- `docs/release/REVIEWER_FEEDBACK_TEMPLATE.md`
- `docs/LIMITATIONS.md`
- `reports/RC1_READINESS_AUDIT.md`
- `reports/R_PARITY_REFRESH_RC1.md`
- `reports/WHEEL_MATRIX_STATUS_RC1.md`

## Known partials / not-run items

- Live TestPyPI publishing may remain not run until maintainers configure Trusted Publishing.
- Cross-platform wheel matrix is the GitHub Actions source of truth; local validation covers only the local platform.
- Optional dependency security tools may be partial if `cargo-audit` or `pip-audit` are not installed locally.
