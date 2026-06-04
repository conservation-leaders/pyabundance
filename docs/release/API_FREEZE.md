# API freeze summary

The public API is frozen for the 1.0.0rc2 external-alpha review unless reviewer feedback identifies a blocker.

Stable release-candidate APIs:

- `pcount`
- `pcount_df`
- `build_pcount_matrices`
- `analyze_pcount`
- `PCountAnalysis`
- `suggest_K`
- `KSuggestion`
- pcount mixture aliases for Poisson, negative-binomial, and zero-inflated Poisson
- `PCountResult` core summaries, predictions, diagnostics, uncertainty, posterior abundance, and reporting methods
- `PCountResult.coef_table(as_dataframe=True)` and `PCountResult.coef_table(as_dataframe=False)`
- `aic_table` and `compare_models`
- `aic_table(..., names=[...])` for iterable model inputs
- `compare_models(..., names=[...])` for iterable model inputs
- dataset loaders and simulation helpers

Backwards-compatible RC2 additions:

- `K="auto"` in `pcount`, `pcount_df`, and `analyze_pcount`;
- safer `visit_labels="auto"` behavior:
  - no `obs_data`: count columns define visit labels;
  - `obs_data` labels matching `count_cols`: count columns define visit labels;
  - differing `obs_data` labels: auto-inference requires an ordered pandas Categorical, otherwise pass explicit `visit_labels`.

Experimental formatting details:

- exact markdown report formatting;
- exact deterministic explanation prose;
- exact warning wording/order;
- bootstrap result table formatting;
- `PCountAnalysis` report section layout.

Internal APIs:

- `pyabundance._core`;
- Rust/PyO3 problem-object internals.

`_core` is intentionally not exported through `pyabundance.__all__`.
