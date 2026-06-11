# Installation

pyabundance is currently prepared for external-alpha / release-candidate review.

## From source

```bash
python -m venv .venv
. .venv/bin/activate || source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
maturin develop --release
```

## From TestPyPI

After maintainers run the TestPyPI workflow:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  pyabundance==1.0.0rc2
```

## Smoke test

```bash
python scripts/smoke_test_installed.py --expected-version 1.0.0rc2
```
