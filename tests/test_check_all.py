from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from subprocess import CompletedProcess

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_all.py"
SPEC = importlib.util.spec_from_file_location("check_all", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
check_all = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_all
SPEC.loader.exec_module(check_all)


def test_full_check_covers_every_gate() -> None:
    names = {check.name for check in check_all.CHECKS}

    assert names == {
        "Git diff hygiene",
        "Rust format",
        "Rust tests",
        "Rust clippy",
        "Native extension editable build",
        "Ruff format",
        "Ruff lint",
        "Mypy",
        "Python tests and coverage",
        "PyO3 stub parity",
        "Strict documentation build",
        "Repository hygiene",
        "GitHub Actions policy",
    }

    check_names = [check.name for check in check_all.CHECKS]
    assert check_names.index("Native extension editable build") < check_names.index(
        "Python tests and coverage"
    )
    assert check_names.index("Native extension editable build") < check_names.index(
        "PyO3 stub parity"
    )

    commands = {check.name: check.command for check in check_all.CHECKS}
    assert commands["Native extension editable build"] == (
        check_all.PYTHON,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--no-build-isolation",
        "-e",
        ".",
    )
    assert commands["PyO3 stub parity"] == (
        check_all.PYTHON,
        "-m",
        "mypy.stubtest",
        "pyabundance._core",
    )
    assert commands["Strict documentation build"] == (
        check_all.PYTHON,
        "-m",
        "mkdocs",
        "build",
        "--strict",
    )
    coverage_command = commands["Python tests and coverage"]
    assert "--cov=pyabundance" in coverage_command
    assert "--cov-fail-under=80" in coverage_command


def test_full_check_stops_after_first_failure() -> None:
    calls: list[tuple[str, ...]] = []

    def failing_runner(command: tuple[str, ...]) -> CompletedProcess[str]:
        calls.append(command)
        return CompletedProcess(command, returncode=1)

    result = check_all.run_checks(check_all.CHECKS, runner=failing_runner)

    assert result == 1
    assert calls == [check_all.CHECKS[0].command]


def test_command_runner_exposes_selected_python_environment_tools(monkeypatch) -> None:
    captured_environment: dict[str, str] = {}

    def fake_subprocess_run(command, **kwargs):
        captured_environment.update(kwargs["env"])
        return CompletedProcess(command, returncode=0)

    monkeypatch.setattr(check_all.subprocess, "run", fake_subprocess_run)

    check_all._run(("example-tool",))

    assert captured_environment["PATH"].split(os.pathsep)[0] == str(Path(check_all.PYTHON).parent)
