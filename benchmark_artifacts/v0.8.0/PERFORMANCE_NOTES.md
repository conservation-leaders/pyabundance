# Performance Notes

## What was profiled

- Full Python `pcount(..., method="BFGS")` fit on the synthetic 500-site, 3-visit, K=60 dataset.
- Direct Rust-backed Poisson N-mixture likelihood through `_core.PCountPoissonProblem.loglik`.
- One Python cProfile fit, written separately to `reports/profile_py_fit.txt`.
- Optional black-box R `unmarked::pcount` comparison when R/unmarked is available.

## What changed

- Added `_core.PCountPoissonProblem(y, X, W, K)` to validate and cache fixed problem data once.
- Precomputed count validity, missing-observation structures, site maximum observed counts,
  and log-factorials from 0..K.
- Updated Python `pcount()` to reuse the cached problem object for optimizer objective calls.
- Reduced repeated per-site allocation and count parsing in the hot Rust likelihood path.
- Added optimizer method, function evaluation count, iteration count, success, and message
  reporting.
- Added direct likelihood benchmarking and a short cProfile report.

## Before/after benchmark table

| Run | Python+Rust median fit time | R median fit time | Python nfev | Direct likelihood median |
| --- | ---: | ---: | ---: | ---: |
| v0.1 pre-flight local run | 1.45702 s | 0.509 s | not available | not available |
| v0.1.1 current local run | 0.0623701 s | 0.554 s | 96 | 0.619938 ms |

## Is R still faster?

R still faster: no.

## Bottleneck assessment

Bottleneck appears dominated by optimizer likelihood calls: nfev × direct likelihood median ≈ 0.0595s (95.4% of median fit time).

## Next performance candidates

- Add analytic gradients or a more efficient finite-difference strategy to reduce optimizer
  evaluations.
- Reuse mutable work buffers across repeated likelihood calls if the PyO3 problem object grows an
  interior workspace.
- Add Rayon site-wise parallel likelihood after serial correctness remains stable.
- Benchmark alternative optimizers and convergence tolerances on multiple synthetic datasets.

No benchmark numbers in this file are invented; unavailable values are marked as not available.
