# Simulation API

The stable pcount simulation helpers remain the source of truth for simulation
math and user-facing compatibility:

- `pyabundance.simulate_pcount`
- `pyabundance.simulate_pcount_negbin`
- `pyabundance.simulate_pcount_zip`

Stage 8B also adds an **experimental** shared-core facade:

```python
from pyabundance.core import simulate

counts = simulate(
    "pcount",
    X=X,
    W=W,
    beta=beta,
    detection=detection,
    mixture="poisson",
    seed=123,
)
```

Only the `"pcount"` model family is supported. The facade delegates to the
existing pcount simulation functions and does not duplicate simulation math, add
new ecological model families, implement `occu`, or add distance-sampling,
open-population, or dynamic models. It also does not include parameter mapping
helpers or a generic parametric-bootstrap facade.

For pcount, `detection` is the preferred keyword for detection coefficients.
The facade also accepts `alpha` as a compatibility alias for the existing
`simulate_pcount` naming. Do not provide both in the same call.

Supported pcount mixture names and aliases are:

| Mixture | Aliases | Delegated helper |
| --- | --- | --- |
| `"poisson"` | `"P"` | `simulate_pcount` |
| `"negative_binomial"` | `"negbin"`, `"NB"` | `simulate_pcount_negbin` |
| `"zero_inflated_poisson"` | `"zip"`, `"ZIP"` | `simulate_pcount_zip` |

The experimental facade is exported from `pyabundance.core`; it is intentionally
not added to top-level `pyabundance.__all__`.
