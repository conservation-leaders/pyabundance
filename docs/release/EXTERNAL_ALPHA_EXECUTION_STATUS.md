# External alpha execution status

Version: 1.0.0rc1

## Status

Overall: IN PROGRESS

## Gate 1 — Local preflight

- branch: `external-alpha-rc1-execution`, reset to `origin/main` commit `20b733f`.
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
- local wheel: PASSED, built `pyabundance-1.0.0rc1-cp311-abi3-macosx_11_0_arm64.whl`.
- local sdist: PASSED, built `pyabundance-1.0.0rc1.tar.gz`.
- twine check: PASSED.
- dist metadata check: PASSED.
- wheel smoke: PASSED.
- sdist smoke: PASSED.
- installed-package smoke: PASSED.

## Gate 2 — Wheel matrix

- Linux x86_64: PASSED.
- macOS x86_64: PASSED.
- macOS arm64: PASSED.
- Windows x86_64: PASSED.
- workflow: `Build and smoke-test wheels`.
- run URL: https://github.com/conservation-leaders/pyabundance/actions/runs/26930694287

## Gate 3 — TestPyPI publish

- Trusted Publishing configured: PENDING VERIFICATION.
- publish workflow run: FAILED once due workflow setup issue, fix in progress.
- failed run URL: https://github.com/conservation-leaders/pyabundance/actions/runs/26930840180
- failure classification: publish job used `actions/setup-python` pip cache without checkout/pyproject in that job; artifact builds all passed.
- fix: add checkout before download/setup-python in publish jobs.
- version published: NOT RUN / not yet successful.
- TestPyPI URL: PENDING.

## Gate 4 — TestPyPI install matrix

- Linux: NOT RUN.
- macOS x86_64: NOT RUN.
- macOS arm64: NOT RUN.
- Windows: NOT RUN.

## Gate 5 — External alpha review

- reviewer packet ready: IN PROGRESS.
- reviewers invited: no; blocked until CI, wheel matrix, TestPyPI publish, and TestPyPI install matrix pass.
- feedback received: no.
- blockers found: none yet.

## Gate 6 — v1.0.0 final readiness

- blocker issues resolved: not assessed.
- final R parity refresh: not run in this stage yet.
- final wheel matrix: pending Gate 2.
- maintainer approval: pending.
- ready for v1.0.0 final: no; external-alpha gates are still in progress.

## Notes

- No new ecological model family is being added during RC feedback.
- No real PyPI publish is planned in this stage.
- Local benchmark results are not universal performance claims.
- Clean-room policy remains active.
- Generated reports, benchmark artifacts, benchmark data, `dist/`, and coverage output remain ignored/untracked.
