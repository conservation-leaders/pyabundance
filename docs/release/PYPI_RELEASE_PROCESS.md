# PyPI Release Process

v1.0.0rc1 is a TestPyPI/external-alpha release candidate. A real PyPI release requires explicit maintainer approval and a configured protected GitHub environment named `pypi-release`.

## Guardrails

- The `publish-pypi.yml` workflow is manual and guarded.
- It requires the workflow input `confirm_real_pypi=publish-to-pypi`.
- It uses PyPI Trusted Publishing (`id-token: write`) rather than an API token.
- The repository must not store PyPI or TestPyPI tokens.
- The workflow builds distributions with `maturin build`/`maturin sdist`; it must not call `maturin develop`.

## Before real PyPI

1. Run the full local check suite.
2. Run the wheel matrix workflow.
3. Run the TestPyPI publish workflow.
4. Install from TestPyPI on Linux, macOS, and Windows.
5. Refresh R black-box parity reports.
6. Freeze public APIs or clearly mark experimental APIs.
7. Prepare a GitHub release draft.
8. Ask maintainers to approve the `pypi-release` environment.

## Real PyPI release

Only maintainers should run the guarded workflow. If the version already exists on PyPI, bump the version and restart the release checklist; do not attempt to overwrite a published artifact.
