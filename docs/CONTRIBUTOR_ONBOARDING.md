# Contributor Onboarding

Welcome to pyabundance. This project is a clean-room implementation of ecological abundance models with a Rust numerical core and Python user API.

## Clean-room rule

Do not copy, inspect, translate, paraphrase, or mechanically port GPL R/C/C++/TMB/Stan source code from `unmarked` or any GPL package. R outputs may be used only as black-box validation targets.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate || source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
maturin develop --release
```

## Standard validation

```bash
cargo fmt --all -- --check
cargo test
cargo clippy --all-targets --all-features -- -D warnings
ruff check .
mypy
pytest -q
```

## Project layout

- `crates/ecoabundance-core`: Rust numerical engine.
- `crates/ecoabundance-py`: PyO3 bindings.
- `python/pyabundance`: public Python API.
- `tests`: Python regression tests.
- `benchmarks`: repeatable local benchmark scripts.
- `specs`: clean-room mathematical and validation specifications.
- `docs`: user and contributor documentation.

## Contribution style

- Keep likelihood changes small, tested, and documented.
- Prefer public equations and independently derived implementations.
- Add Python tests for user-visible behavior.
- Add Rust tests for pure numerical helpers.
- Do not make broad performance claims from local benchmarks.
