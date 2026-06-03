# Formula API Overhead Benchmark

Status: COMPLETED

Dataset:
- n_sites: 500
- n_visits: 3
- K: 60
- repetitions: 3

Correctness:
- matrix API logLik: -1351.31
- formula API logLik: -1351.31
- absolute logLik difference: 0
- max coefficient absolute difference: 0

Performance:
- matrix API median fit time: 0.0609172
- formula API median fit time: 0.0676367
- formula overhead: 0.0067195
- formula/matrix ratio: 1.11031

Notes:
- This measures convenience-layer overhead, not Rust likelihood speed.
- Matrix API remains the lowest-overhead path.
- Do not invent results.
