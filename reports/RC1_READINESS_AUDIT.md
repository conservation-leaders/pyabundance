# v1.0.0-rc1 Readiness Audit

Status: READY

Version:
- Python package version: 1.0.0rc1
- Rust workspace version: 1.0.0-rc.1
- CITATION version: 1.0.0rc1
- docs version: 1.0.0rc1 release notes and GitHub release draft present
- status: consistent; Rust uses Cargo-compatible prerelease spelling while Python uses PEP 440 spelling

Quality gates:
- tests: passed; 73 Python tests
- coverage: passed; 84.20% with threshold 80%
- mypy: passed
- ruff: format and lint passed
- docs: `mkdocs build --strict` passed
- wheel: local macOS arm64 wheel built
- sdist: built
- smoke tests: tutorial, external alpha, wheel, sdist, and installed-package smoke tests passed

Release gates:
- TestPyPI publish: workflow prepared; live publish not run locally
- TestPyPI install: workflow prepared; live install matrix not run locally
- wheel matrix: workflow prepared; local macOS arm64 validation passed
- R parity refresh: completed
- external alpha guide: ready
- GitHub release draft: ready

Known blockers:
- None for local RC1 preparation.
- Remaining external gates: run GitHub TestPyPI publish workflow, TestPyPI install matrix, and cross-platform wheel matrix in CI.

Notes:
- No new ecological model family was added.
- No validated likelihood formulas were changed intentionally.
- No R/GPL source code was copied, inspected, translated, or paraphrased.
