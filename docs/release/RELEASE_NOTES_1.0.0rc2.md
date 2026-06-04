# pyabundance 1.0.0rc2 Release Notes

`1.0.0rc2` is a UX-hardening release candidate. It adds no new ecological model family, makes no intentional likelihood formula changes, and keeps Rust likelihood behavior focused on the existing pcount-style models.

RC2 focuses on:

- `analyze_pcount()` guided workflow and `PCountAnalysis` reports.
- `K="auto"` and `suggest_K()`.
- automatic/smarter visit label handling with clearer errors.
- `compare_models(..., names=[...])` and `aic_table(..., names=[...])`.
- `coef_table(as_dataframe=True)` and `coef_table(as_dataframe=False)`.
- deterministic `explain()` summaries.
- Mallard validation walkthrough documentation.
- performance architecture documentation and UX benchmark script.

Performance claims remain local and benchmark-specific. The guided workflow is Python orchestration over existing Rust-backed model fitting.
