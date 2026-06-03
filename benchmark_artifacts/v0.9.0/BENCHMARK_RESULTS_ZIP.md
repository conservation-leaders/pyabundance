# Zero-Inflated Poisson Benchmark Results

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 100
- repetitions: 3

Correctness:
- Python logLik: -1211.05
- R unmarked logLik: -1211.05
- absolute logLik difference: 3.01475e-09
- coefficient comparison: not forced; raw Python/R vectors recorded because ZIP psi naming may differ
- psi comparison: Python logit_psi=-1.21673, psi=0.228513; R zero-inflation parameterization not assumed from coefficient order
- parity status: close

Performance:
- Python+Rust median fit time: 0.189355
- R unmarked median fit time: 1.052
- speed ratio R/Python: 5.55569
- Python function evaluations: 126
- Python iterations: 13
- direct ZIP likelihood median: 1.49633 ms
- nfev × direct likelihood median: 0.188538 s
- percentage of fit time explained by likelihood calls: 99.5684%

Environment:
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
- Python: 3.14.5 (main, May 10 2026, 10:21:34) [Clang 21.0.0 (clang-2100.0.123.102)]
- Rust: rustc 1.83.0 (90b35a623 2024-11-26)
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1

Notes:
- This is a simple end-to-end benchmark, not a comprehensive performance study.
- Optimizer paths may differ.
- ZIP models can be more weakly identified than Poisson or NB models.
- Low detection, low abundance, and structural zeros can all produce many observed zero counts.
- Local benchmark speedups are not general performance claims.
- Do not invent results.
- Raw Python params: [0.2906998066542672, 0.5056986994438573, -0.7065327034619705, -0.20241078766454892, 0.4673331487499947, -1.2167261667973384]
- Raw R coefficients: [0.2907057236469966, 0.5056977286891191, -0.7065354177630662, -0.20241499259694418, 0.4673273460034151, -1.2167003449842988]
- Raw R coefficient names: ['lam(Int)', 'lam(x)', 'p(visitv1)', 'p(visitv2)', 'p(visitv3)', 'psi(psi)']
