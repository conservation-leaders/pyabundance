# CI Workflows

Status: COMPLETED

| Workflow | Trigger | Purpose | Secrets/environments | Artifacts | Required for PRs |
|---|---|---|---|---|---|
| `ci.yml` | push, pull_request | Rust/Python tests, lint, type check, coverage, benchmark smoke | none | coverage XML, benchmark reports | yes |
| `wheels.yml` | workflow_dispatch, selected pull_request paths | cross-platform wheel build and smoke tests | none | wheel artifacts, wheel status reports | optional |
| `publish-testpypi.yml` | workflow_dispatch | build dist and publish to TestPyPI via Trusted Publishing | TestPyPI Trusted Publisher configured externally | dist artifact | manual only |
| `publish-pypi.yml` | workflow_dispatch, tags | guarded real PyPI draft workflow | protected `pypi-release` environment and PyPI Trusted Publisher | none by default | manual/guarded only |
| `testpypi-install.yml` | workflow_dispatch | install from TestPyPI on Linux/macOS/Windows and smoke test | none | logs | manual only |
| `docs.yml` | push to main, workflow_dispatch | strict MkDocs build and optional Pages deploy | GitHub Pages environment for deploy | Pages artifact | optional |
| `benchmarks.yml` | workflow_dispatch | Python benchmarks, optional R parity, artifact upload | none; R installed only when requested | reports and benchmark artifacts | manual only |

Notes:
- No PyPI or TestPyPI API tokens are stored in the repository.
- Uploads use `actions/upload-artifact@v4`.
