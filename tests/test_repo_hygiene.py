from __future__ import annotations

import shutil
import subprocess
import sys

import pytest


def test_repo_hygiene_script_passes():
    if shutil.which("git") is None:
        pytest.skip("git is not available")
    result = subprocess.run(
        [sys.executable, "scripts/check_repo_hygiene.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "passed" in result.stdout.lower()
