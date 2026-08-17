# Domain docs

How engineering skills should consume this repository's domain documentation while exploring
the codebase.

## Before exploring, read these

- `CONTEXT.md` at the repository root, when it exists.
- Relevant decisions under `docs/adr/`, when that directory exists.
- For current architecture and mathematical contracts, follow the focused sources in
  `docs/development/` and `specs/` that touch the area being changed.

Proceed silently when `CONTEXT.md` or `docs/adr/` does not exist. Do not create empty domain
docs up front. `/domain-modeling`, reached through `/grill-with-docs` and
`/improve-codebase-architecture`, creates them when terms or decisions are actually resolved.

## Layout

This is a single-context repository. Domain vocabulary spans the Rust numerical core, PyO3
bindings, and Python API.

```text
/
├── CONTEXT.md
├── docs/adr/
├── crates/
└── python/pyabundance/
```

## Use the glossary's vocabulary

When output names a domain concept—in an issue title, refactor proposal, hypothesis, or test
name—use the term defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly
avoids.

If a needed concept is absent, reconsider whether the term belongs to the project. If it does,
record the gap for `/domain-modeling`.

## Flag ADR conflicts

If proposed work contradicts an existing ADR, surface the conflict explicitly instead of
silently overriding the decision.
