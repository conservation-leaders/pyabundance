# Local benchmark caveat

pyabundance benchmark outputs are synthetic, local, and environment-specific. They are useful for regression checks and black-box parity checks, but they are not universal performance claims.

Timing depends on:

- hardware;
- operating system;
- Python/R/Rust versions;
- BLAS/runtime libraries;
- optimizer convergence paths;
- `K` truncation choices;
- dataset structure.

R/unmarked comparisons are black-box output comparisons only. Do not inspect or copy GPL source code when validating behavior.
