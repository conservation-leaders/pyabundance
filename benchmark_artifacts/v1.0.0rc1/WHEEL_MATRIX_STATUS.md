# Wheel Matrix Status

Status: PARTIAL

Targets:
- linux x86_64: configured in CI, not run locally
- macOS x86_64: configured in CI, not run locally
- macOS arm64: COMPLETED locally (macOS-26.5.1-arm64-arm-64bit-Mach-O)
- Windows x86_64: configured in CI, not run locally

Smoke tests:
- import pyabundance: passed locally
- load bundled dataset: passed locally
- pcount_df tiny fit: passed locally
- posterior_abundance: passed locally
- compare_models: passed locally

Artifacts:
- wheels: `pyabundance-0.9.0-cp311-abi3-macosx_11_0_arm64.whl`
- sdist: `pyabundance-0.9.0.tar.gz`

Notes:
- Local machine can only validate the local platform wheel.
- CI is the source of truth for cross-platform matrix.
- Do not invent results.
