# Negative-Binomial Benchmark Results

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 100
- repetitions: 3

Correctness:
- Python logLik: -1360.88
- R unmarked logLik: -1360.88
- absolute logLik difference: 4.05334e-07
- coefficient comparison: not forced; raw Python/R vectors recorded because NB dispersion naming may differ
- dispersion comparison: Python log_r=0.373166, r=1.45233; R dispersion parameterization not assumed from coefficient order
- parity status: close

Performance:
- Python+Rust median fit time: 0.261248
- R unmarked median fit time: 1.076
- speed ratio R/Python: 4.11869
- Python function evaluations: 105
- Python iterations: 11
- direct NB likelihood median: 2.48398 ms
- nfev × direct likelihood median: 0.260818 s
- percentage of fit time explained by likelihood calls: 99.8353%

Environment:
- OS: macOS-26.5.1-arm64-arm-64bit-Mach-O
- Python: 3.14.5 (main, May 10 2026, 10:21:34) [Clang 21.0.0 (clang-2100.0.123.102)]
- Rust: rustc 1.83.0 (90b35a623 2024-11-26)
- R: R version 4.6.0 (2026-04-24)
- unmarked: 1.5.1

Notes:
- This is a simple end-to-end benchmark, not a comprehensive performance study.
- Optimizer paths may differ.
- Negative-binomial dispersion is harder to estimate than Poisson parameters.
- v0.1.1 showed Python+Rust faster than R unmarked on one simple local Poisson benchmark, but this is not a general performance claim.
- Do not invent results.
- Raw Python params: [0.23562760358677148, 0.5667422277298232, -0.9059667788364746, -0.09321352238130437, 0.4164678185366459, 0.3731663749812862]
- Raw R coefficients: [0.23567916358669505, 0.5667294471277714, -0.9060416415569363, -0.0932541708618808, 0.41638608627318724, 0.3730663144790894]
- Raw R coefficient names: ['lam(Int)', 'lam(x)', 'p(visitv1)', 'p(visitv2)', 'p(visitv3)', 'alpha(alpha)']
