# External alpha execution status

Version: 1.0.0rc2

## Status

Overall: LOCAL RC2 IMPLEMENTATION VALIDATED; REMOTE RELEASE GATES NOT RUN

RC2 is a UX-hardening candidate. It adds guided pcount analysis, `K="auto"`, smarter visit-label handling, DataFrame-friendly coefficient output, deterministic explanations, Mallard validation documentation, and performance architecture documentation. It adds no new ecological model family and makes no intentional likelihood formula changes.

## Gate 1 — Local preflight

Status: PASSED

- repo hygiene: PASSED.
- GitHub Actions policy check: PASSED.
- editable install: PASSED, `.venv/bin/python -m pip install -e '.[dev,docs,release]'` installed `pyabundance==1.0.0rc2`.
- Rust toolchain: PASSED, active toolchain 1.83.0 from `rust-toolchain.toml`.
- cargo fmt: PASSED.
- cargo test: PASSED, 10 Rust tests.
- cargo clippy: PASSED.
- ruff format: PASSED.
- ruff check: PASSED.
- mypy: PASSED.
- pytest: PASSED, 107 tests.
- coverage: PASSED, 84.86% against 80% threshold.
- mkdocs: PASSED, strict build; MkDocs Material emitted a non-failing upstream warning.
- tutorial smoke: PASSED for `guided_pcount_analysis.py`, `release_smoke.py`, `pcount_end_to_end.py`, and `external_alpha_smoke.py`.
- RC2 UX benchmark: PASSED, generated ignored local reports.
- generated artifacts: ignored/untracked.

## Gate 1b — GitHub CI on main

Status: NOT RUN FOR RC2

Run after opening and merging the RC2 PR.

## Gate 2 — Wheel matrix

Status: NOT RUN FOR RC2

Run after GitHub CI passes.

## Gate 3 — TestPyPI publish

Status: NOT RUN FOR RC2

Publish `pyabundance==1.0.0rc2` to TestPyPI only after CI and wheel matrix pass. Do not overwrite rc1 and do not publish real PyPI during RC2 validation.

## Gate 4 — TestPyPI install matrix

Status: NOT RUN FOR RC2

Blocked until Gate 3 publishes `pyabundance==1.0.0rc2` to TestPyPI.

## Gate 5 — External alpha review

Status: PREPARED, NOT STARTED

Ask reviewers to try `analyze_pcount`, `pcount_df`, `K="auto"`, `compare_models` with dict keys and `names=[...]`, report export, posterior abundance, uncertainty outputs, and optional Mallard validation if they know R/unmarked.

## Notes

- No new ecological model family was added.
- No validated likelihood formulas were intentionally changed.
- Rust likelihood hot paths remain Rust-backed.
- Performance claims remain local and benchmark-specific.
- Clean-room policy remains active; R/unmarked is only a black-box comparison target.
