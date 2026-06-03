# R Standard Error Comparison

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 60

Correctness:
- Python logLik: -1351.31
- R unmarked logLik: -1351.31
- absolute logLik difference: 1.59162e-09
- coefficient comparison: max absolute coefficient difference 4.12509e-06

Standard errors:
- comparison status: compared
- max absolute SE difference: 0.00127149
- max relative SE difference: 0.0213298
- notes: BFGS inverse-Hessian SEs are approximate and not required to match R exactly.

Environment:
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
- Python: 3.14.5 (main, May 10 2026, 10:21:34) [Clang 21.0.0 (clang-2100.0.123.102)]
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1

Notes:
- This is a black-box comparison.
- SEs may differ because covariance approximations and optimizer paths differ.
- Do not treat this as a strict parity test.
