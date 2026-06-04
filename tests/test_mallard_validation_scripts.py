from __future__ import annotations

import py_compile
from pathlib import Path


def test_python_mallard_validation_scripts_compile():
    for path in [
        Path("examples/validation/run_mallard_pyabundance.py"),
        Path("examples/validation/compare_mallard_results.py"),
    ]:
        py_compile.compile(str(path), doraise=True)
