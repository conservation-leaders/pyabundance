from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]


PYTHON = sys.executable
ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    Check("Git diff hygiene", ("git", "diff", "--check", "HEAD")),
    Check("Rust format", ("cargo", "fmt", "--all", "--", "--check")),
    Check("Rust tests", ("cargo", "test", "--workspace")),
    Check(
        "Rust clippy",
        (
            "cargo",
            "clippy",
            "--workspace",
            "--all-targets",
            "--all-features",
            "--",
            "-D",
            "warnings",
        ),
    ),
    Check(
        "Native extension editable build",
        (PYTHON, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", "."),
    ),
    Check("Ruff format", (PYTHON, "-m", "ruff", "format", "--check", ".")),
    Check("Ruff lint", (PYTHON, "-m", "ruff", "check", ".")),
    Check("Mypy", (PYTHON, "-m", "mypy", "python/pyabundance")),
    Check(
        "Python tests and coverage",
        (
            PYTHON,
            "-m",
            "pytest",
            "--cov=pyabundance",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=80",
        ),
    ),
    Check("PyO3 stub parity", (PYTHON, "-m", "mypy.stubtest", "pyabundance._core")),
    Check("Strict documentation build", (PYTHON, "-m", "mkdocs", "build", "--strict")),
    Check("Repository hygiene", (PYTHON, "scripts/check_repo_hygiene.py")),
    Check("GitHub Actions policy", (PYTHON, "scripts/check_github_actions.py")),
)

Runner = Callable[[tuple[str, ...]], subprocess.CompletedProcess[str]]


def _run(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        part for part in (str(Path(PYTHON).parent), environment.get("PATH")) if part
    )
    return subprocess.run(command, check=False, cwd=ROOT, env=environment, text=True)


def run_checks(checks: Sequence[Check], *, runner: Runner = _run) -> int:
    for check in checks:
        print(f"\n==> {check.name}", flush=True)
        result = runner(check.command)
        if result.returncode != 0:
            print(f"FAILED: {check.name}", file=sys.stderr)
            return result.returncode
    print("\nAll repository checks passed.")
    return 0


def main() -> None:
    raise SystemExit(run_checks(CHECKS))


if __name__ == "__main__":
    main()
