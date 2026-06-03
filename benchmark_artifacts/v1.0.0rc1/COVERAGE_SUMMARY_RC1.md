# Coverage Summary for v1.0.0-rc1

Status: COMPLETED

Coverage:
- percentage: 84.20%
- threshold: 80%
- status: passed

Low coverage modules:
- `python/pyabundance/model_selection.py`: 67%
- `python/pyabundance/bootstrap.py`: 74%
- `python/pyabundance/uncertainty.py`: 75%

Notes:
- Command: `pytest --cov=pyabundance --cov-report=term-missing --cov-report=xml --cov-fail-under=80`.
- `coverage.xml` was generated locally.
