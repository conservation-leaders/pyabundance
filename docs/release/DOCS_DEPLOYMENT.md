# Documentation Deployment

Docs are built with MkDocs Material and `mkdocstrings`.

## Local docs

```bash
python -m pip install -e '.[docs]'
maturin develop --release
mkdocs serve
mkdocs build --strict
```

## GitHub Pages setup

In repository settings:

1. Enable GitHub Pages.
2. Select **GitHub Actions** as the Pages source.
3. Ensure workflows have permission to deploy Pages.
4. Run the `Docs` workflow manually for the first deployment.

## Workflow behavior

`docs.yml` builds docs on push to `main` and on manual dispatch. Manual dispatch also deploys through the official Pages artifact/deploy action. If Pages is not enabled, the build step remains useful and the deploy step will fail clearly.

## API docs

API docs are generated from the Python package under `python/` using `mkdocstrings`. The Rust/PyO3 extension must be buildable because examples and API imports expect `pyabundance._core` to exist.
