# Performance architecture

pyabundance separates high-level Python orchestration from Rust numerical kernels. The product goal is to make abundance analysis pleasant in Python without moving likelihood hot paths out of Rust.

- Rust owns hot likelihood kernels.
- Python owns formula handling, guided workflows, validation, reporting, and deterministic explanations.
- Cached Rust problem objects prevent repeated validation/setup inside optimizer objectives.
- Rust precomputes reusable quantities such as log-factorials and site maxima.
- PyO3 objects use contiguous owned buffers for batch model-level calls.
- Likelihood calculations use stable log-space arithmetic.
- The Python/Rust boundary is crossed at the model/problem level, not once per site or visit.
- Python code must not loop over latent abundance states in likelihood hot paths.
- `K="auto"` is selected once before fitting.
- `analyze_pcount()` orchestrates existing fitted models; it does not replace Rust-backed fitting or define a new statistical model.

The guided interface is allowed to add Python-side convenience, warnings, model comparison, and report generation. It should not change validated likelihood formulas or broaden performance claims beyond local benchmark wording.

Future performance candidates include reusable Rust work buffers, analytic gradients, Rayon over sites for large datasets, criterion benchmarks, and memory allocation profiling. These should be benchmark-driven and must not change validated likelihood formulas unintentionally.
