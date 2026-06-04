# API freeze summary

The public API is frozen for external-alpha review unless reviewer feedback identifies a blocker.

Stable release-candidate APIs:

- `pcount`
- `pcount_df`
- `build_pcount_matrices`
- pcount mixture aliases for Poisson, negative-binomial, and zero-inflated Poisson
- `PCountResult` core summaries, predictions, diagnostics, uncertainty, posterior abundance, and reporting methods
- `aic_table` and `compare_models`
- dataset loaders and simulation helpers

Experimental formatting:

- exact markdown report formatting;
- bootstrap result table formatting.

Internal APIs:

- `pyabundance._core`;
- Rust/PyO3 problem-object internals.

`_core` is intentionally not exported through `pyabundance.__all__`.
