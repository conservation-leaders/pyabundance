# Posterior Abundance Benchmark

Status: COMPLETED

Models:
- Poisson:
  - posterior matrix time: 0.00156492
  - summary time: 0.00437817
  - sampling time: 0.0115934
  - total abundance time: 0.0115308
  - posterior matrix shape: [500, 61]
  - row-sum max error: 3.33067e-16
- Negative-binomial:
  - posterior matrix time: 0.00414646
  - summary time: 0.00696354
  - sampling time: 0.0141902
  - total abundance time: 0.0144631
  - posterior matrix shape: [500, 101]
  - row-sum max error: 2.22045e-16
- Zero-inflated Poisson:
  - posterior matrix time: 0.00277104
  - summary time: 0.0058785
  - sampling time: 0.012776
  - total abundance time: 0.0128229
  - posterior matrix shape: [500, 101]
  - row-sum max error: 3.33067e-16

Notes:
- This benchmark measures posterior abundance post-processing, not model fitting.
- Posterior abundance conditions on fitted parameters.
- Do not invent results.
