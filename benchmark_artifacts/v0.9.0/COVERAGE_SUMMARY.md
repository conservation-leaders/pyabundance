# Coverage Summary

Status: COMPLETED

Current coverage:
- line coverage: 84.20%
- threshold: 80%
- status: passed

Low-coverage modules:
- `python/pyabundance/model_selection.py`: 67%
- `python/pyabundance/bootstrap.py`: 74%
- `python/pyabundance/uncertainty.py`: 75%

Notes:
- The threshold is intentionally conservative for the external-alpha phase and can be raised after reviewer feedback and additional tests.
- Coverage command: `pytest --cov=pyabundance --cov-report=term-missing --cov-report=xml --cov-fail-under=80`.
- `coverage.xml` was generated locally.
