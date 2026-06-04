# External alpha execution status

Version: 1.0.0rc1

## Status

Overall: BLOCKED AT GATE 3

Blocker: TestPyPI Trusted Publisher is not configured for the current GitHub OIDC claims. Artifact builds pass, but TestPyPI rejects the publish token with `invalid-publisher`.

## Gate 1 — Local preflight

Status: PASSED

- branch: `external-alpha-rc1-execution`, based on clean `main` and merged back through PR #3.
- repo hygiene: PASSED.
- GitHub Actions policy check: PASSED.
- editable install: PASSED, `python -m pip install -e '.[dev,docs,release]'`.
- Rust sanity: PASSED, Rust/Cargo/rustfmt/clippy available on toolchain 1.83.0.
- cargo fmt: PASSED.
- cargo test: PASSED, 10 Rust tests.
- cargo clippy: PASSED.
- ruff format: PASSED.
- ruff check: PASSED.
- mypy: PASSED.
- pytest: PASSED, 85 tests.
- coverage: PASSED, 84.20% against 80% threshold.
- mkdocs: PASSED, strict build; MkDocs Material emitted a non-failing upstream MkDocs 2.0 warning.
- tutorial smoke: PASSED for `release_smoke.py`, `pcount_end_to_end.py`, and `external_alpha_smoke.py`.
- local wheel: PASSED, built `pyabundance-1.0.0rc1-cp311-abi3-macosx_11_0_arm64.whl` locally.
- local sdist: PASSED, built `pyabundance-1.0.0rc1.tar.gz` locally.
- twine check: PASSED.
- dist metadata check: PASSED.
- wheel smoke: PASSED.
- sdist smoke: PASSED.
- installed-package smoke: PASSED.

## Gate 1b — GitHub CI on main

Status: PASSED

- workflow: `CI`.
- run URL: https://github.com/conservation-leaders/pyabundance/actions/runs/26929744952
- Python 3.11: PASSED.
- Python 3.12: PASSED.
- Python 3.13: PASSED.
- Rust setup, editable install, cargo checks, ruff, mypy, pytest, coverage, repo hygiene, and GitHub Actions policy checks passed.

## Gate 2 — Wheel matrix

Status: PASSED

- Linux x86_64: PASSED.
- macOS x86_64: PASSED.
- macOS arm64: PASSED.
- Windows x86_64: PASSED.
- workflow: `Build and smoke-test wheels`.
- run URL: https://github.com/conservation-leaders/pyabundance/actions/runs/26930694287
- note: wheel artifacts built and smoke-tested on all release-candidate platforms.

## Gate 3 — TestPyPI publish

Status: BLOCKED

Artifact build status: PASSED

- workflow: `Publish to TestPyPI`.
- successful artifact build run with failed publish: https://github.com/conservation-leaders/pyabundance/actions/runs/26931187829
- Build TestPyPI sdist: PASSED.
- Build TestPyPI wheel Linux x86_64: PASSED.
- Build TestPyPI wheel macOS x86_64: PASSED.
- Build TestPyPI wheel macOS arm64: PASSED.
- Build TestPyPI wheel Windows x86_64: PASSED.
- Publish artifacts to TestPyPI: FAILED.

Previous workflow setup issue: FIXED

- failed run URL: https://github.com/conservation-leaders/pyabundance/actions/runs/26930840180
- failure classification: publish job used `actions/setup-python` pip cache without checkout/pyproject in that job.
- fix: PR #3 added checkout before artifact download/setup-python in publish jobs.
- PR URL: https://github.com/conservation-leaders/pyabundance/pull/3

Current publish blocker: TestPyPI Trusted Publisher configuration

- TestPyPI error: `invalid-publisher`: valid token, but no corresponding publisher was found.
- GitHub OIDC claims from the failed main-branch publish run:
  - `sub`: `repo:conservation-leaders/pyabundance:ref:refs/heads/main`
  - `repository`: `conservation-leaders/pyabundance`
  - `repository_owner`: `conservation-leaders`
  - `workflow_ref`: `conservation-leaders/pyabundance/.github/workflows/publish-testpypi.yml@refs/heads/main`
  - `job_workflow_ref`: `conservation-leaders/pyabundance/.github/workflows/publish-testpypi.yml@refs/heads/main`
  - `ref`: `refs/heads/main`
  - `environment`: `MISSING`
- required maintainer action: configure TestPyPI Trusted Publisher for project `pyabundance` using repository `conservation-leaders/pyabundance`, workflow `publish-testpypi.yml`, and no environment unless the workflow is later changed to use one.
- version published: NO.
- TestPyPI URL: PENDING.

## Gate 4 — TestPyPI install matrix

Status: NOT RUN

Blocked until Gate 3 publishes `pyabundance==1.0.0rc1` to TestPyPI.

- Linux: NOT RUN.
- macOS x86_64: NOT RUN.
- macOS arm64: NOT RUN.
- Windows: NOT RUN.

## Gate 5 — External alpha review

Status: PREPARED, NOT STARTED

- reviewer packet ready: YES.
- external alpha invitation: CREATED.
- external alpha tracker: CREATED.
- feedback triage rules: CREATED.
- reviewers invited: no; blocked until CI, wheel matrix, TestPyPI publish, and TestPyPI install matrix pass.
- feedback received: no.
- blockers found: none from reviewers yet.

## Gate 6 — v1.0.0 final readiness

Status: NOT READY

- blocker issues resolved: TestPyPI Trusted Publisher configuration remains unresolved.
- final R parity refresh: not run in this stage yet.
- final wheel matrix: Gate 2 passed for rc1, but final release will need a fresh final wheel matrix.
- maintainer approval: pending.
- ready for v1.0.0 final: no; TestPyPI publish/install and external alpha review are incomplete.

## Notes

- No new ecological model family was added during this stage.
- No validated likelihood formulas were changed.
- No public API changes were made.
- No real PyPI publish was attempted.
- Local benchmark results are not universal performance claims.
- Clean-room policy remains active.
- Generated reports, benchmark artifacts, benchmark data, `dist/`, and coverage output remain ignored/untracked.
