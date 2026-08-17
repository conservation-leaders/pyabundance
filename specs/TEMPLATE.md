# Feature specification: <name>

## Status and ownership

- Status: draft | approved | implemented
- Human approver:
- Governing Linear issue URL (`ENG-…`):
- Tracker: [Engineering (`ENG`) project](https://linear.app/conservation-leaders/project/project-goanna-map-visualisation-and-pyabundance-e7ea0b817b0b)
- Related ADRs:

## Clean-room provenance

List every public manual, vignette, paper, original derivation, and black-box recording used. State
that no incompatible implementation or test source was inspected. Classify each fixture as an
independent oracle, black-box compatibility fixture, or project-generated regression fixture.

## Observable contract

Describe public call forms, return types, shapes, labels, defaults, warnings, errors, missing-data
behavior, and deterministic/RNG behavior. Include explicit non-goals.

## Statistical contract

Define the generative model, links, parameterization, latent support, likelihood, posterior target,
and assumptions. Define parameter ordering and transformation rules.

## Compatibility decisions

For each observed upstream behavior, choose exact compatibility, documented divergence, or deferred
support. Record known quirks explicitly; never reproduce a suspected defect silently.

## Prepared numeric seam

Specify what Python compiles, what PyO3 validates/converts, what Rust owns, and the typed snapshots
returned to Python. Include formula-schema retention and prediction reconstruction where relevant.

## Resource and numerical limits

Set checked dimension/allocation limits, truncation/state-space policy, extreme-parameter behavior,
precision tolerances, and performance budgets. Define typed failure behavior.

## Acceptance matrix

List independently derived microcases, black-box comparisons, regression cases, missing/extreme
inputs, derivative checks, posterior normalization, simulation reproducibility, and cross-language
boundary cases. Name the exact focused commands plus `python scripts/check_all.py`.

## Rollout

Describe expand–migrate–contract stages, compatibility adapters, deprecations, documentation, and
the human promotion gate that permits the next milestone.
