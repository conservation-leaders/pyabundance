# Dependency Audit for v1.0.0-rc1

Status: PARTIAL

Rust:
- cargo tree: completed locally
- cargo audit: not run; `cargo-audit` is not installed in this environment

Python:
- pip list: completed locally
- pip-audit: not run; `pip-audit` is not installed in this environment

Findings:
- No new runtime dependency was added for rc1.
- Runtime Python dependencies remain `numpy`, `scipy`, `pandas`, and `formulaic`.
- Release/docs/test tools remain optional dependencies only.
- Rust dependencies are captured in `Cargo.lock`.
- Rust package metadata is present for workspace crates.

Maintainer follow-up:
- Optional: install and run `cargo audit`.
- Optional: install and run `pip-audit`.
