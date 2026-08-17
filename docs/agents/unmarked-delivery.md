# Unmarked realignment delivery playbook

This playbook governs the independent Rust and Python implementation of the unmarked-compatible
feature program. It supplements the repository clean-room policy; when instructions conflict, the
clean-room policy wins.

## Non-negotiable boundaries

- Do not inspect, copy, translate, paraphrase, or derive code from incompatible upstream source or
  tests. This restriction also applies when a generic research skill would normally permit source
  inspection.
- Use public manuals, public vignettes, published mathematics, original derivations, and recorded
  black-box outputs only.
- Identify every fixture as either an independent oracle, a black-box compatibility fixture, or a
  project-generated regression fixture. Never present the last category as independent evidence.
- Keep pandas, formulas, labels, and presentation in Python. Keep prepared numeric models,
  likelihoods, latent inference, fitted values, and simulation kernels in Rust. Any exception needs
  an accepted ADR.
- Preserve released pcount behavior while foundational modules expand, migrate callers, and then
  contract legacy paths.

## Skill choreography

Use the skills in this order:

1. `/wayfinder` records unresolved decisions and evidence-gathering work. Its issues are not
   implementation slices.
2. `/to-spec` turns accepted decisions into a behavior-complete specification based on
   `specs/TEMPLATE.md`.
3. A human approves scientific compatibility choices, public API commitments, numerical-method
   choices, and promotion gates.
4. `/to-tickets` creates dependency-linked vertical slices. Do not triage the tickets it creates;
   their readiness is part of specification work.
5. A fresh context runs `/implement` for one unblocked leaf ticket only.
6. `/code-review <base-sha>` performs independent Standards and Specification reviews before the
   pull request is handed off.

Use `wayfinder:research` for public-source evidence gathering, `wayfinder:task` for bounded numeric
experiments, and `wayfinder:grilling` for decisions. Do not use the generic throwaway prototype
workflow for numerical methods whose evidence must be tested and retained.

All governing issues live in the
[pyabundance Linear project](https://linear.app/conservation-leaders/project/project-goanna-map-visualisation-and-pyabundance-e7ea0b817b0b)
on the Engineering (`ENG`) team. Versioned specifications remain under `specs/` and link their
governing Linear issue.

## Ready-ticket contract

An implementation issue is `ready-for-agent` only when it contains all of the following:

- one observable outcome and explicit non-goals;
- links to an approved specification and any governing ADR;
- the Rust/PyO3/Python seam being changed;
- exact shape, missingness, parameter-order, error, and resource-limit contracts;
- an independent oracle or a stated reason one cannot exist;
- focused acceptance tests and the required full gate;
- compatibility divergences and the chosen policy for each;
- blockers and the earlier behaviors that must remain green.

Unresolved scientific or API decisions use `ready-for-human`, not `ready-for-agent`.

## One-ticket implementation loop

1. Read `AGENTS.md`, the clean-room policy, the selected issue, linked spec, and relevant ADRs.
   Confirm from tracker metadata that the issue is unblocked and unclaimed; do not inspect code yet.
2. Claim the issue as the session's first write and record the immutable base SHA. Then read only
   the code needed for that seam.
3. Run focused baseline tests and `python scripts/check_all.py`. Stop if the baseline is red for a
   reason unrelated to the ticket.
4. Add one failing behavior test at the public or cross-language seam. Use an independent expected
   value; do not encode the implementation into the test.
5. Make the smallest complete vertical change through Rust, PyO3, Python, typing, and documentation
   that the behavior requires. Keep compatibility adapters during expand–migrate–contract work.
6. Run focused checks continuously, then the full repository gate.
7. Create a clearly named candidate commit. Run `/code-review <base-sha>` against committed work.
8. Resolve every hard Standards and Specification finding. Record a disposition for each review
   judgment, commit fixes, and repeat the full gate and review until clean.
9. Push one branch, open one pull request, and stop. A new context selects the next frontier issue
   only after this issue is merged.

The candidate commit in step 7 is deliberate: the review skill compares committed history with a
fixed point and cannot review only staged or unstaged changes. Do not squash the audit commits until
the final review is complete.

## Required gates

Every pull request must pass:

```bash
python scripts/check_all.py
```

GitHub branch protection requires the stable `Merge gate` check, resolved conversations, and an
up-to-date branch. The solo-maintainer configuration does not require a second-account approval;
the independent Standards and Specification reviews remain mandatory. Native-boundary changes also
need focused dtype, non-contiguous-array, shape, keyword-signature, and error-mapping tests.
Statistical changes need microcases with independently derived values, normalization checks,
missing/extreme cases, and locked prior-family regressions.

Human promotion decisions are required after the common seam is proven by both pcount and occu,
after generic inference is free of pcount coupling, before adopting the occuComm integration method,
and before releasing the complete compatibility surface.

## Task shapes to reject

Do not accept tasks such as “implement all unmarked features,” “build the foundation,” “write all
Rust models,” or “add all Python wrappers.” Do not combine upstream behavior research with
production implementation, numerical feasibility with a production community model, or multiple
model families in one agent context. Each ticket must leave one end-to-end capability working and
all previous capabilities green.
