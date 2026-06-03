# R Ranef / Posterior Abundance Comparison

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 60

Correctness:
- Python logLik: -1351.31
- R unmarked logLik: -1351.31
- absolute logLik difference: 1.59162e-09

Posterior abundance:
- comparison status: posterior means compared
- max absolute posterior mean difference: 1.20093e-05
- max posterior mode difference: 0
- notes: ranef extraction and summaries can differ across packages; comparison is non-strict.

Environment:
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
- Python: 3.14.5 (main, May 10 2026, 10:21:34) [Clang 21.0.0 (clang-2100.0.123.102)]
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1

Notes:
- This is a black-box comparison against unmarked ranef-style outputs.
- Posterior abundance here conditions on fitted parameters.
- Empirical-Bayes intervals do not include full parameter uncertainty.
- Do not treat this as a strict parity test if extraction methods differ.
