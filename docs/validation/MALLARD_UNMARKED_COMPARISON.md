# Mallard validation against R unmarked

This walkthrough compares pyabundance with `unmarked::mallard` as a black-box validation target. Do not copy Mallard data into the package source. The scripts export data locally from R, fit R/unmarked and pyabundance models on the same complete-case subset, and compare results.

pyabundance aims to make pcount-style abundance analysis feel natural in Python while keeping Rust likelihood kernels and preserving transparent power-user controls. The Mallard workflow checks that this Python/Rust workflow remains aligned with a familiar R/unmarked analysis.

## Prerequisites

- R with package `unmarked` installed.
- pyabundance installed in the active Python environment.
- Permission to use `unmarked::mallard` locally.

Raw Mallard data is not bundled with pyabundance.

## Inputs and outputs

- Source data: `unmarked::mallard`.
- Local exported data directory: `data/mallard/` (git ignored).
- Local result directory: `results/mallard/` (git ignored).

Expected exported files include:

- `data/mallard/site_data_for_py.csv`
- `data/mallard/obs_data_for_py.csv`
- `data/mallard/analysis_site_filter.csv`

Expected result files include:

- `results/mallard/r_poisson_meta.csv`
- `results/mallard/r_nb_meta.csv`
- `results/mallard/py_poisson_meta.json`
- `results/mallard/py_nb_meta.json`
- `results/mallard/py_model_comparison.csv`
- `results/mallard/mallard_validation_summary.md`

## Workflow

```bash
Rscript examples/validation/export_mallard_from_unmarked.R
Rscript examples/validation/run_mallard_unmarked.R
python examples/validation/run_mallard_pyabundance.py
python examples/validation/compare_mallard_results.py
```

Complete-case filtering is used so both tools fit the same site and observation rows for required site covariates (`length`, `elev`, `forest`) and observation covariates (`ivel`, `date`). R/unmarked is used only as a black-box comparison target.

The pyabundance script intentionally exercises RC2 conveniences: visit labels are inferred automatically from `obs_data`, `fit.coef_table(as_dataframe=True)` is exported, and `compare_models(..., names=[...])` is used for Python-side model comparison.

## Internal local result example

In internal Mallard testing, pyabundance closely matched R unmarked:

- Poisson logLik difference: `6.85e-09`
- Negative-binomial logLik difference: `3.96e-05`
- Local speed ratio R/Python: Poisson `12.08`, NB `5.92`

These results are from one local machine and one dataset. They are not universal performance claims. Use the scripts above to reproduce local comparisons in your environment.

## Clean-room note

Do not inspect, copy, translate, or paraphrase R/unmarked source code. The validation workflow uses public package behavior and fitted outputs only.
