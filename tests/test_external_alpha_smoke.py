from __future__ import annotations

import subprocess
import sys


def test_external_alpha_smoke_script_runs():
    result = subprocess.run(
        [sys.executable, "examples/external_alpha_smoke.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "pyabundance external alpha smoke" in result.stdout
    assert "posterior" in result.stdout.lower()
