# Posterior Abundance Benchmark

Status: COMPLETED

Models:
- Poisson:
  - posterior matrix time: 0.00155108
  - summary time: 0.00436696
  - sampling time: 0.0116716
  - total abundance time: 0.0116074
  - posterior matrix shape: [500, 61]
  - row-sum max error: 3.33067e-16
- Negative-binomial:
  - posterior matrix time: 0.00403004
  - summary time: 0.00690017
  - sampling time: 0.0140924
  - total abundance time: 0.0144174
  - posterior matrix shape: [500, 101]
  - row-sum max error: 2.22045e-16
- Zero-inflated Poisson:
  - posterior matrix time: 0.00273779
  - summary time: 0.00553721
  - sampling time: 0.0127317
  - total abundance time: 0.0126885
  - posterior matrix shape: [500, 101]
  - row-sum max error: 3.33067e-16

Notes:
- This benchmark measures posterior abundance post-processing, not model fitting.
- Posterior abundance conditions on fitted parameters.
- Do not invent results.
