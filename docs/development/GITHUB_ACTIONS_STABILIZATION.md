# GitHub Actions stabilization

## Issues fixed

- `maturin develop` was called in GitHub Actions without a virtualenv.
- `tests/test_release_engineering.py` expected `benchmark_artifacts/README.md` after repository cleanup.
- `wheels.yml` used the stale `macos-13` runner label for macOS x86_64 wheel jobs.

## Root causes

- `maturin develop` is a local-development command that expects an activated virtualenv; GitHub Actions `setup-python` does not create one.
- `benchmark_artifacts/` is now generated and ignored after repository cleanup, but the release-engineering test still expected a tracked file under that directory.
- The wheel matrix used an outdated macOS Intel runner label, causing jobs to wait for unavailable hosted runners.

## Fixes

- Removed `maturin develop` from GitHub Actions workflows.
- Removed `benchmark_artifacts/README.md` from required tracked files.
- Added cleanup-policy assertions for `reports/README.md`, repository hygiene docs, benchmark docs, artifact preservation script, benchmark upload workflow, and the repo hygiene script.
- Updated wheel, TestPyPI install, TestPyPI publish, and guarded PyPI publish matrices to current macOS labels.
- Strengthened `scripts/check_github_actions.py` to reject `macos-13`, deprecated action versions, token-based publishing, local builds in TestPyPI install jobs, and missing release wheel platforms.

## Wheel matrix platforms

pyabundance includes a Rust/PyO3 native extension, so wheels are platform-specific. Release-candidate wheels must be built and smoke-tested for:

- Linux x86_64
- macOS x86_64
- macOS arm64
- Windows x86_64

The package may have been developed on macOS, but Linux and Windows users need platform-specific wheels. Without Linux/Windows wheels, pip may fall back to source builds requiring Rust and native build tooling.

Current runner labels:

- Linux x86_64: `ubuntu-latest`
- macOS x86_64: `macos-15-intel`
- macOS arm64: `macos-15`
- Windows x86_64: `windows-latest`

Do not use `macos-13`.

## Validation

- repo hygiene: passed.
- GitHub Actions policy check: passed.
- ruff format/check: passed.
- pytest `tests/test_github_actions.py`: passed, 7 tests.
- pytest `tests/test_release_engineering.py`: passed, 5 tests.
- full pytest: passed, 83 tests.
- docs: `mkdocs build --strict` passed.
- generated artifacts: no tracked generated artifacts; only `reports/README.md` is tracked under generated report/artifact paths.

## Decision

CI and workflow definitions are ready to rerun. The old `macos-13` wheel-matrix run should be cancelled, and the updated wheel matrix should be run before TestPyPI publishing.
