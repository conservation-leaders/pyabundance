# Repository instructions

## Project guardrails

Before changing implementation code or tests, read `CONTRIBUTING.md` and
`docs/CONTRIBUTOR_ONBOARDING.md`. Their clean-room rule is binding.

## Agent skills

### Issue tracker

Issues, specifications, and Wayfinder maps are tracked in Linear on the Engineering (`ENG`) team.
GitHub remains the code-review and CI surface, not a duplicate project tracker. See
`docs/agents/issue-tracker.md` before reading or writing tracker state.

### Triage labels

Triage uses Matt Pocock's five canonical label roles. See `docs/agents/triage-labels.md` for
the repository mapping and label prerequisite.

### Domain docs

This is a single-context repository: use root `CONTEXT.md` and `docs/adr/` when they exist.
See `docs/agents/domain.md`.

### Unmarked realignment delivery

Before planning or implementing any realignment ticket, read
`docs/agents/unmarked-delivery.md`. Implementation sessions run `python scripts/check_all.py`
before claiming a clean baseline and again before handoff. Planning and tracker-only sessions use
the latest green `main` CI unless they change repository files.
