# pyabundance 1.0.0rc1 Release Notes

`1.0.0rc1` is a release-candidate / external-alpha release. It does not add a new ecological model family and does not intentionally change validated likelihood formulas.

## Focus

- Python package version `1.0.0rc1`.
- Cargo workspace version `1.0.0-rc.1`, the Cargo-compatible spelling of the same release candidate.
- Final API freeze review for the first pcount modelling family.
- TestPyPI rehearsal workflow and install matrix documentation.
- Local wheel and sdist validation.
- Final R black-box parity refresh.
- External alpha reviewer packet and feedback template.
- GitHub release draft for maintainers.

## Major features already included

- Poisson, negative-binomial, and zero-inflated Poisson single-season pcount-style N-mixture models.
- Matrix API and pandas/Formulaic API.
- Uncertainty outputs, confidence intervals, bootstrap, diagnostics, model selection, reporting, posterior abundance / ranef-like summaries, and posterior predictive checks.

## Limitations

This is not a final stable v1.0 release. Current limitations include no open/dynamic N-mixture models, no distance sampling, no spatial models, no random effects, and no full Bayesian posterior parameter uncertainty.

## Clean-room statement

No R/GPL source code was copied, inspected, translated, or paraphrased. R/unmarked is used only as a black-box comparison target.
