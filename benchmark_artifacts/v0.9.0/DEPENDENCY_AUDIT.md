# Dependency Audit

Status: PARTIAL

Rust:
- cargo tree: completed locally
- cargo audit: not run; `cargo-audit` is not installed in this environment

Python:
- pip list: completed locally
- pip-audit: not run; `pip-audit` is not installed in this environment

Findings:
- No new runtime dependency was added for v0.9.
- Runtime Python dependencies remain `numpy`, `scipy`, `pandas`, and `formulaic`.
- Release/docs/test tools are optional dependencies only.
- Rust dependencies are captured in `Cargo.lock`, which is included intentionally for reproducible PyO3 builds.
- Rust crate package metadata was added for the workspace crates.

Notes:
- Optional audit tools are not runtime dependencies.
- A future release workflow can add non-blocking `cargo audit` and `pip-audit` jobs.
