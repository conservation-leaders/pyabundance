# Mallard validation against R unmarked

This walkthrough compares pyabundance with `unmarked::mallard` as a black-box validation target. Do not copy Mallard data into the package source; export it locally from R if licensing and your local installation permit it.

## Inputs and outputs

- Source data: `unmarked::mallard`.
- Local exported data directory: `data/mallard/` (git ignored).
- Local result directory: `results/mallard/` (git ignored).

## Workflow

```bash
Rscript examples/validation/export_mallard_from_unmarked.R
Rscript examples/validation/run_mallard_unmarked.R
python examples/validation/run_mallard_pyabundance.py
python examples/validation/compare_mallard_results.py
```

Complete-case filtering is used so both tools fit the same site and observation rows. R is used only as a black-box comparison target.

## Internal local result example

In internal Mallard testing, pyabundance closely matched R unmarked:

- Poisson logLik difference: `6.85e-09`
- Negative-binomial logLik difference: `3.96e-05`
- Local speed ratio R/Python: Poisson `12.08`, NB `5.92`

These results are from one local machine and one dataset. They are not universal performance claims.
