# TestPyPI Install Matrix

Status: NOT RUN

Targets:
- Linux x86_64: configured in workflow, not run locally
- macOS x86_64: configured in workflow, not run locally
- macOS arm64: configured in workflow, not run locally
- Windows x86_64: configured in workflow, not run locally

Install command:
- `python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyabundance==1.0.0rc1`

Smoke test:
- `python scripts/smoke_test_installed.py --expected-version 1.0.0rc1`

Notes:
- Live TestPyPI install requires the TestPyPI publish workflow to run first.
- CI is the source of truth for the cross-platform install matrix.
