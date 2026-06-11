# GitHub release draft: pyabundance 1.0.0rc2

pyabundance `1.0.0rc2` is a release candidate / external-alpha UX-hardening release for the clean-room Rust + Python ecological abundance modelling library.

## Highlights

- Guided `analyze_pcount()` workflow.
- `K="auto"` / `suggest_K()`.
- smarter visit-label inference for count columns such as `y1/y2/y3` with observation visits `v1/v2/v3`.
- `compare_models(names=[...])` convenience.
- `coef_table(as_dataframe=True)` support.
- deterministic explanations and report export.
- Mallard validation walkthrough.
- performance architecture guardrail docs.

No new ecological model family is included. No validated likelihood formula changes are intended.

## TestPyPI smoke

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyabundance==1.0.0rc2
python scripts/smoke_test_installed.py --expected-version 1.0.0rc2
```
