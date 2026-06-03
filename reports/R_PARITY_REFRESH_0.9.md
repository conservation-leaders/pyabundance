# R Parity Refresh 0.9

Status: COMPLETED

Comparisons:
- Poisson parity: COMPLETED; logLik difference 1.59162e-09
- Negative-binomial parity: COMPLETED; logLik difference 4.05334e-07
- Zero-inflated Poisson parity: COMPLETED; logLik difference 3.01475e-09
- R SE comparison: COMPLETED; max absolute SE difference 0.00127149; max relative SE difference 0.0213298
- R ranef comparison: COMPLETED; max absolute posterior mean difference 1.20093e-05; max posterior mode difference 0

Environment:
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
- Python: 3.14.5
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1

Notes:
- R/unmarked comparisons are optional black-box validation targets.
- No R/GPL source code was copied, inspected, translated, or paraphrased.
- Detailed reports remain in `reports/BENCHMARK_RESULTS*.md`, `reports/SE_COMPARISON_R.md`, and `reports/RANEF_COMPARISON_R.md`.
