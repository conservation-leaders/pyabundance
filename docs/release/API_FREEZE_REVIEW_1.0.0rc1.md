# API Freeze Review for 1.0.0rc1

The following APIs are considered stable for the release-candidate external alpha unless blocker feedback requires changes.

| API | Classification | v1.0 stability | Documented | Typed | Tested |
|---|---|---|---|---|---|
| `pcount` | public | stable | yes | yes | yes |
| `pcount_df` | public | stable | yes | yes | yes |
| `build_pcount_matrices` | public | stable | yes | yes | yes |
| mixture aliases `P`, `NB`, `ZIP` and long names | public | stable | yes | yes | yes |
| `PCountResult` core properties/methods | public | stable | yes | yes | yes |
| uncertainty methods | public | stable | yes | yes | yes |
| `parametric_bootstrap` and bootstrap result formatting | public | experimental formatting | yes | yes | yes |
| posterior abundance / `ranef` methods | public | stable | yes | yes | yes |
| `aic_table`, `compare_models` | public | stable | yes | yes | yes |
| reporting/export helpers | public | stable data, experimental formatting | yes | yes | yes |
| `load_example_pcount`, `list_example_datasets` | public | stable | yes | yes | yes |
| `pyabundance._core` | internal | may change | no public docs | stub only | indirectly |

## Internal API boundary

`pyabundance._core` and Rust/PyO3 problem-object internals are implementation details. They are not exported through `pyabundance.__all__` and are not promised as stable user APIs.

## Limitations

See `docs/LIMITATIONS.md`. The package remains scoped to single-season pcount-style N-mixture models for this release candidate.
