# API Freeze Review for v0.9

v0.9 is an external-alpha rehearsal. The API is stable enough for review, but not yet a v1.0 compatibility promise.

| API | Stable for alpha? | Likely to change before v1.0? | Documented? | Typed? | Tested? | Status |
|---|---|---|---|---|---|---|
| `pcount` | yes | no | yes | yes | yes | public |
| `pcount_df` | yes | possibly small ergonomics changes | yes | yes | yes | public |
| `build_pcount_matrices` | yes | possibly column-name details | yes | yes | yes | public |
| `PCountResult` core properties | yes | no | yes | yes | yes | public |
| `PCountResult` uncertainty methods | yes | possibly output formatting | yes | yes | yes | public |
| `PCountResult` posterior abundance methods | yes | possibly output formatting | yes | yes | yes | public |
| `parametric_bootstrap` | experimental | yes | yes | yes | yes | experimental public |
| `aic_table` | yes | no | yes | yes | yes | public |
| `compare_models` | yes | no | yes | yes | yes | public |
| `load_example_pcount` | yes | no | yes | yes | yes | public |
| `list_example_datasets` | yes | no | yes | yes | yes | public |
| reporting helpers | yes | possibly formatting | yes | yes | yes | public |
| `_core` | no | yes | no | stub only | indirectly | internal |

## Safe for external users

Use `pcount`, `pcount_df`, `build_pcount_matrices`, result summaries/predictions, uncertainty methods, posterior abundance methods, `aic_table`, `compare_models`, dataset loaders, and reporting helpers.

## Experimental

Bootstrap interfaces and exact report/table formatting may change before v1.0 based on alpha feedback.

## Internal

`pyabundance._core` is an implementation detail. It is intentionally not exported by `from pyabundance import *`.
