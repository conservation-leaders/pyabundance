# GitHub Actions stabilization

## Issues fixed

- `maturin develop` was called in GitHub Actions without a virtualenv.
- `tests/test_release_engineering.py` expected `benchmark_artifacts/README.md` after repository cleanup.
- `wheels.yml` used the stale `macos-13` runner label for macOS x86_64 wheel jobs.
- CI editable install failed during maturin metadata generation because Rust setup hit a clippy component conflict and Cargo was unavailable.

## Root causes

- `maturin develop` is a local-development command that expects an activated virtualenv; GitHub Actions `setup-python` does not create one.
- `benchmark_artifacts/` is now generated and ignored after repository cleanup, but the release-engineering test still expected a tracked file under that directory.
- The wheel matrix used an outdated macOS Intel runner label, causing jobs to wait for unavailable hosted runners.
- `rust-toolchain.toml` and CI both requested Rust components through non-exact `1.83` toolchain resolution, which could conflict before pip/maturin saw Cargo.

## Fixes

- Removed `maturin develop` from GitHub Actions workflows.
- Removed `benchmark_artifacts/README.md` from required tracked files.
- Added cleanup-policy assertions for `reports/README.md`, repository hygiene docs, benchmark docs, artifact preservation script, benchmark upload workflow, and the repo hygiene script.
- Updated wheel, TestPyPI install, TestPyPI publish, and guarded PyPI publish matrices to current macOS labels.
- Strengthened `scripts/check_github_actions.py` to reject `macos-13`, deprecated action versions, token-based publishing, local builds in TestPyPI install jobs, missing release wheel platforms, and non-exact Rust toolchain setup.
- Pinned `rust-toolchain.toml` to `1.83.0` with `profile = "minimal"`.
- Added a CI Rust sanity check before Python editable install.

## Rust toolchain policy

The project pins Rust to `1.83.0` for release-candidate builds.

In CI:

- install Rust explicitly before Python editable installs;
- use exact toolchain version `1.83.0`;
- install `rustfmt` and `clippy` through the GitHub Actions Rust setup step when those checks are run;
- run `rustup show`, `rustc --version`, `cargo --version`, `cargo fmt --version`, and `cargo clippy --version` before `pip install -e` in CI;
- do not rely on maturin to discover or install Rust during pip metadata generation.

`rust-toolchain.toml` pins the toolchain version with `profile = "minimal"` and does not install clippy/rustfmt components implicitly in CI.

Local development:

- developers may use `maturin develop` inside an activated virtual environment;
- developers may install components manually if needed:

```bash
rustup component add rustfmt clippy --toolchain 1.83.0
```

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

- Rust sanity: `rustup show`, `rustc --version`, `cargo --version`, `cargo fmt --version`, and `cargo clippy --version` passed locally with Rust 1.83.0 after installing local rustfmt/clippy components.
- repo hygiene: passed.
- GitHub Actions policy check: passed.
- cargo fmt: passed.
- cargo test: passed, 10 Rust tests.
- cargo clippy: passed.
- ruff format/check: passed.
- mypy: passed.
- pytest `tests/test_github_actions.py`: passed, 9 tests.
- full pytest: passed, 85 tests.
- coverage: passed, 84.20% against 80% threshold.
- docs: `mkdocs build --strict` passed.
- generated artifacts: no tracked generated artifacts; only `reports/README.md` is tracked under generated report/artifact paths.

## Decision

CI and workflow definitions are ready to rerun. Rust setup is explicit and checked before Python editable install. The old `macos-13` wheel-matrix run should be cancelled, and the updated wheel matrix should be run before TestPyPI publishing.
