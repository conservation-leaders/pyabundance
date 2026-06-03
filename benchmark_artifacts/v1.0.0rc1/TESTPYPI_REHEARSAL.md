# TestPyPI Rehearsal

Status: PARTIAL

Prepared:
- publish-testpypi workflow: yes (`.github/workflows/publish-testpypi.yml`)
- TestPyPI install workflow: yes (`.github/workflows/testpypi-install.yml`)
- Trusted Publishing docs: yes (`docs/release/TESTPYPI_REHEARSAL.md`)
- dist metadata check: passed locally
- local wheel smoke test: passed locally
- local sdist smoke test: passed locally

Live TestPyPI:
- publish attempted: no
- install from TestPyPI: no
- version: 0.9.0
- notes: This local Codex run cannot configure GitHub/TestPyPI Trusted Publishing. Maintainers must configure the TestPyPI Trusted Publisher and run `workflow_dispatch` in GitHub Actions. The workflow is designed to fail clearly if Trusted Publishing is not configured.

Next steps:
- configure Trusted Publisher if not done
- run workflow_dispatch
- inspect artifacts
- install from TestPyPI
