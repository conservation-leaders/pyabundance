# TestPyPI Rehearsal for v1.0.0-rc1

Status: PARTIAL

Prepared:
- publish-testpypi workflow: yes (`.github/workflows/publish-testpypi.yml`)
- Trusted Publishing configured: not verifiable locally
- dist metadata check: passed locally
- wheel build: passed locally
- sdist build: passed locally
- twine check: passed locally
- local smoke test: passed locally

Live TestPyPI:
- publish attempted: no
- publish result: not run locally
- package version: 1.0.0rc1
- install from TestPyPI: not run locally
- install platforms: not run locally
- smoke test result: local wheel/sdist/installed smoke passed; TestPyPI install not run

Notes:
- Real PyPI was not used.
- Maintainers must configure TestPyPI Trusted Publishing and run `publish-testpypi.yml` with `workflow_dispatch` in GitHub.
- After publishing, run `testpypi-install.yml` for Linux/macOS/Windows install validation.
