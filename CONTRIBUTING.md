# Contributing

Contributions must be original work or compatible with Apache-2.0. Do not copy, translate,
or paraphrase GPL R/C++/TMB/Stan source code. R package outputs may be used only as black-box
validation targets.

Before submitting changes, run:

```bash
cargo fmt --all
cargo test
cargo clippy --all-targets --all-features -- -D warnings
pytest -q
```
