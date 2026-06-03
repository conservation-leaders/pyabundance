# R Parity Refresh for v1.0.0-rc1

Status: COMPLETED

Poisson:
- logLik difference: 1.59162e-09
- coefficient difference: max absolute coefficient difference 4.12509e-06
- status: COMPLETED

Negative-binomial:
- logLik difference: 4.05334e-07
- coefficient difference: see detailed NB report; coefficient comparison is name/order cautious
- status: COMPLETED

Zero-inflated Poisson:
- logLik difference: 3.01475e-09
- coefficient difference: see detailed ZIP report; coefficient comparison is name/order cautious
- status: COMPLETED

Standard errors:
- max absolute SE difference: 0.00127149
- max relative SE difference: 0.0213298
- status: COMPLETED

Ranef/posterior abundance:
- max posterior mean difference: 1.20093e-05
- max posterior mode difference: 0
- status: COMPLETED

Environment:
- Python: 3.14.5
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O

Notes:
- R was used only as a black-box comparison target.
- Do not treat local synthetic benchmarks as universal performance claims.
- Detailed black-box reports remain in `reports/BENCHMARK_RESULTS*.md`, `reports/SE_COMPARISON_R.md`, and `reports/RANEF_COMPARISON_R.md`.
