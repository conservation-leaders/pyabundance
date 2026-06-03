# Posterior Abundance Benchmark

Status: COMPLETED

Models:
- Poisson:
  - posterior matrix time: 0.00157333
  - summary time: 0.00601583
  - sampling time: 0.0116395
  - total abundance time: 0.0115993
  - posterior matrix shape: [500, 61]
  - row-sum max error: 3.33067e-16
- Negative-binomial:
  - posterior matrix time: 0.00400829
  - summary time: 0.00895138
  - sampling time: 0.0142005
  - total abundance time: 0.01412
  - posterior matrix shape: [500, 101]
  - row-sum max error: 2.22045e-16
- Zero-inflated Poisson:
  - posterior matrix time: 0.00273621
  - summary time: 0.00571817
  - sampling time: 0.0127894
  - total abundance time: 0.012826
  - posterior matrix shape: [500, 101]
  - row-sum max error: 3.33067e-16

Notes:
- This benchmark measures posterior abundance post-processing, not model fitting.
- Posterior abundance conditions on fitted parameters.
- Do not invent results.
