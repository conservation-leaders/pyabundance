# pcount Parameter Mapping

`pyabundance.pcount_mapping` contains experimental, pcount-specific helpers for
inspecting how a fitted `PCountResult` parameter vector maps to pyabundance
process names, shared-core parameter blocks, link functions, and common
pcount/unmarked-style terminology.

These helpers are descriptive only. They do **not** change likelihood formulas,
Rust likelihood hot paths, fitting, prediction, simulation, bootstrap, or model
selection behavior.

## Usage

```python
from pyabundance.pcount_mapping import pcount_parameter_mapping

mapping = pcount_parameter_mapping(fit)
table = mapping.table
summary = mapping.summary()
```

For a Poisson pcount fit, the table includes rows for:

| Process | Link | Level | Coefficient source | Meaning |
| --- | --- | --- | --- | --- |
| `lambda` | `log` | `site` | `result.beta` | abundance state / lambda coefficients |
| `p` | `logit` | `observation` | `result.detection` / `result.alpha` | detection probability coefficients |

Negative-binomial fits add a global `r` block with coefficient `log_r`, a `log`
link, and transformed value `result.r`. ZIP fits add a global `psi` block with
coefficient `logit_psi`, a `logit` link, and transformed value `result.psi`.

## Table contents

The table is one row per fitted coefficient and includes columns such as:

- parameter-vector index;
- parameter name and fitted design column;
- pyabundance process and block names;
- block start/stop positions;
- link and process level;
- coefficient estimate;
- transformed name/value for mixture-specific extras;
- abundance and detection formulas when available;
- fitted model metadata such as mixture and `K`;
- public pcount/unmarked-style terminology.

`pcount_parameter_mapping_table(fit)` returns the table directly, and
`pcount_parameter_map(fit)` is a conservative alias for
`pcount_parameter_mapping(fit)`.

## Scope and clean-room notes

The helpers accept `PCountResult` objects and raise a clear `TypeError` for
unsupported objects. They validate that `parameter_blocks` exactly cover the
parameter vector without gaps or overlap.

The unmarked-style terminology is public-facing vocabulary only. It is not based
on inspecting, copying, translating, or paraphrasing GPL source code. The default
CI path does not require R, `unmarked`, external datasets, or downloads.

These names are intentionally not exported from top-level `pyabundance.__all__`.
