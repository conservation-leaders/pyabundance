# Uncertainty Benchmark

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 60

Runtime:
- fit without SE: 0.0612081
- fit with BFGS covariance: 0.0610278
- fit with finite-difference covariance: 0.0926443
- parametric bootstrap nsim: 20
- parametric bootstrap time: 1.06766

Outputs:
- covariance method: finite_difference
- covariance status: available
- number of parameters: 5
- finite SE count: 5
- warnings: none

Notes:
- This benchmark measures uncertainty overhead, not raw likelihood speed.
- Bootstrap runtime scales approximately with nsim and refit cost.
- Do not invent results.
