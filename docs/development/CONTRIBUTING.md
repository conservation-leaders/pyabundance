# Contributing

Start with the repository root `CONTRIBUTING.md`, then review:

- `docs/development/CLEAN_ROOM_POLICY.md`
- `docs/development/REPOSITORY_HYGIENE.md`
- `docs/LIMITATIONS.md`

Before submitting changes:

```bash
maturin develop --release
cargo test
cargo clippy --all-targets --all-features -- -D warnings
ruff format --check .
ruff check .
mypy python/pyabundance
pytest -q
python scripts/check_repo_hygiene.py
```

Do not paste GPL source code or translated source snippets into issues, docs, tests, or pull requests.
