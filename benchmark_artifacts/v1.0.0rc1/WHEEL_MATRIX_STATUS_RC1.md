# Wheel Matrix Status for v1.0.0-rc1

Status: PARTIAL

Targets:
- Linux x86_64: configured in CI, not run locally
- macOS x86_64: configured in CI, not run locally
- macOS arm64: COMPLETED locally (macOS-26.5.1-arm64-arm-64bit-Mach-O)
- Windows x86_64: configured in CI, not run locally

Artifacts:
- wheels: `pyabundance-1.0.0rc1-cp311-abi3-macosx_11_0_arm64.whl`
- sdist: `pyabundance-1.0.0rc1.tar.gz`

Smoke tests:
- import pyabundance: passed locally
- version check: passed locally
- bundled dataset: passed locally
- pcount_df tiny fit: passed locally
- posterior_abundance: passed locally
- compare_models: passed locally

Notes:
- CI wheel matrix is the source of truth.
- Local machine may only validate one platform.
- Do not invent results.
