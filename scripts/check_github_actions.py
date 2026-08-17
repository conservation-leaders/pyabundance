from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

WORKFLOW_DIR = Path(".github/workflows")
TOOLCHAIN_FILE = Path("rust-toolchain.toml")
REQUIRED_RUST_TOOLCHAIN = "1.83.0"
REQUIRED_PLATFORM_LABELS = {
    "ubuntu-latest": "Linux x86_64",
    "macos-15-intel": "macOS x86_64",
    "macos-15": "macOS arm64",
    "windows-latest": "Windows x86_64",
}


@dataclass(frozen=True)
class Violation:
    path: Path
    message: str
    line: int | None = None

    def format(self) -> str:
        location = f"{self.path}"
        if self.line is not None:
            location += f":{self.line}"
        return f"{location}: {self.message}"


def _line_number(text: str, needle: str) -> int | None:
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return idx
    return None


def _has_exact_runner_label(text: str, label: str) -> bool:
    label_pattern = re.escape(label)
    patterns = [
        rf"runs-on:\s*{label_pattern}(?![-\w])",
        rf"os:\s*{label_pattern}(?![-\w])",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _as_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {key: item for key, item in value.items() if isinstance(key, str)}
    return {}


def _check_ci_structure(path: Path, text: str) -> list[Violation]:
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return [Violation(path, "CI workflow must be valid YAML")]

    workflow = _as_mapping(document)
    jobs = _as_mapping(workflow.get("jobs"))
    full_check = _as_mapping(jobs.get("full-check"))
    full_check_steps = full_check.get("steps")
    full_check_candidates = (
        [
            _as_mapping(step)
            for step in full_check_steps
            if _as_mapping(step).get("run") == "python scripts/check_all.py"
        ]
        if isinstance(full_check_steps, list)
        else []
    )

    violations: list[Violation] = []
    if len(full_check_candidates) != 1:
        violations.append(Violation(path, "CI must run the repository-owned full check command"))
    else:
        full_check_step = full_check_candidates[0]
        full_check_masking = (
            "if" in full_check
            or "continue-on-error" in full_check
            or "if" in full_check_step
            or "continue-on-error" in full_check_step
            or full_check_step.get("shell") != "bash"
            or "env" in full_check_step
            or "working-directory" in full_check_step
        )
        if full_check_masking:
            violations.append(
                Violation(path, "CI must use an unconditional full-check step with fail-fast Bash")
            )

    compatibility = _as_mapping(jobs.get("compatibility"))
    if "if" in compatibility or "continue-on-error" in compatibility:
        violations.append(Violation(path, "CI compatibility job must not mask failures"))

    strategy = _as_mapping(compatibility.get("strategy"))
    expected_matrix = {"python-version": ["3.12", "3.13"]}
    if strategy.get("fail-fast") is not False or strategy.get("matrix") != expected_matrix:
        violations.append(
            Violation(path, "CI compatibility job must keep the Python 3.12/3.13 matrix")
        )

    compatibility_steps = compatibility.get("steps")
    required_compatibility_commands = {
        'python -m mypy --python-version "${{ matrix.python-version }}" python/pyabundance',
        "python -m pytest -q",
    }
    valid_compatibility_commands: set[str] = set()
    if isinstance(compatibility_steps, list):
        for raw_step in compatibility_steps:
            step = _as_mapping(raw_step)
            run_command = step.get("run")
            if (
                isinstance(run_command, str)
                and run_command in required_compatibility_commands
                and step.get("shell") == "bash"
                and "if" not in step
                and "continue-on-error" not in step
                and "env" not in step
                and "working-directory" not in step
            ):
                valid_compatibility_commands.add(str(run_command))
    if valid_compatibility_commands != required_compatibility_commands:
        violations.append(
            Violation(
                path,
                "CI compatibility job must run mypy and pytest as unconditional fail-fast Bash "
                "steps",
            )
        )

    setup_python_steps = (
        [
            _as_mapping(step)
            for step in compatibility_steps
            if _as_mapping(step).get("uses") == "actions/setup-python@v5"
        ]
        if isinstance(compatibility_steps, list)
        else []
    )
    expected_python_setup = {
        "python-version": "${{ matrix.python-version }}",
        "cache": "pip",
    }
    valid_python_setup = (
        len(setup_python_steps) == 1
        and setup_python_steps[0].get("with") == expected_python_setup
        and "if" not in setup_python_steps[0]
        and "continue-on-error" not in setup_python_steps[0]
        and "env" not in setup_python_steps[0]
    )
    if not valid_python_setup:
        violations.append(
            Violation(path, "CI compatibility job must configure each matrix interpreter")
        )

    forbidden_environment = {
        "COVERAGE_PROCESS_START",
        "COVERAGE_RCFILE",
        "MYPY_CONFIG_FILE",
        "MYPYPATH",
        "PATH",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONHOME",
        "PYTHONPATH",
        "VIRTUAL_ENV",
    }
    environment_owners = [workflow, full_check, compatibility]
    for job_steps in (full_check_steps, compatibility_steps):
        if isinstance(job_steps, list):
            environment_owners.extend(_as_mapping(step) for step in job_steps)
    has_test_control_environment = any(
        forbidden_environment.intersection(_as_mapping(owner.get("env")))
        for owner in environment_owners
    )
    has_run_defaults = any("defaults" in owner for owner in (workflow, full_check, compatibility))
    if has_test_control_environment or has_run_defaults:
        violations.append(
            Violation(path, "CI test-control environment and run defaults must remain unset")
        )

    merge_gate = _as_mapping(jobs.get("merge-gate"))
    if merge_gate.get("name") != "Merge gate" or merge_gate.get("if") != "always()":
        violations.append(
            Violation(path, "CI must expose a stable aggregate check named Merge gate")
        )

    if merge_gate.get("needs") != ["full-check", "compatibility"]:
        violations.append(
            Violation(path, "Merge gate must depend on full-check and compatibility jobs")
        )

    steps = merge_gate.get("steps")
    assertion_step = _as_mapping(steps[0]) if isinstance(steps, list) and len(steps) == 1 else {}
    expected_environment = {
        "FULL_CHECK_RESULT": "${{ needs.full-check.result }}",
        "COMPATIBILITY_RESULT": "${{ needs.compatibility.result }}",
    }
    if assertion_step.get("env") != expected_environment:
        violations.append(Violation(path, "Merge gate must evaluate all dependency results"))

    run_value = assertion_step.get("run")
    run_lines = run_value.strip().splitlines() if isinstance(run_value, str) else []
    expected_assertions = [
        'test "$FULL_CHECK_RESULT" = "success"',
        'test "$COMPATIBILITY_RESULT" = "success"',
    ]
    failure_masking = (
        "if" in assertion_step
        or "continue-on-error" in assertion_step
        or "continue-on-error" in merge_gate
    )
    if run_lines != expected_assertions or failure_masking:
        violations.append(
            Violation(
                path,
                "Merge gate must use one canonical unconditional assertion step and "
                "assert every dependency succeeded",
            )
        )
    if assertion_step.get("shell") != "bash":
        violations.append(Violation(path, "Merge gate must use an explicit fail-fast Bash shell"))

    return violations


def _require_platform_labels(path: Path, text: str) -> list[Violation]:
    violations: list[Violation] = []
    for label, platform in REQUIRED_PLATFORM_LABELS.items():
        if not _has_exact_runner_label(text, label):
            violations.append(Violation(path, f"missing required {platform} runner label: {label}"))
    return violations


def check_workflow_text(path: Path, text: str) -> list[Violation]:
    """Return workflow policy violations for a workflow file."""
    violations: list[Violation] = []
    simple_forbidden = {
        "macos-13": "do not use stale macOS runner label macos-13; use macos-15-intel",
        "maturin develop": (
            "do not use maturin develop in GitHub Actions; "
            "use pip editable installs or maturin build"
        ),
        "actions/upload-artifact@v3": "use actions/upload-artifact@v4",
        "actions/download-artifact@v3": "use actions/download-artifact@v4",
        "actions/checkout@v3": "use actions/checkout@v4",
        "actions/setup-python@v4": "use actions/setup-python@v5",
    }
    for needle, message in simple_forbidden.items():
        if needle in text:
            violations.append(Violation(path, message, _line_number(text, needle)))

    rust_action_match = re.search(r"dtolnay/rust-toolchain@([^\s]+)", text)
    if rust_action_match and rust_action_match.group(1) != REQUIRED_RUST_TOOLCHAIN:
        violations.append(
            Violation(
                path,
                f"use exact Rust toolchain {REQUIRED_RUST_TOOLCHAIN} in dtolnay/rust-toolchain",
                text[: rust_action_match.start()].count("\n") + 1,
            )
        )

    token_patterns = [
        r"\bPYPI_API_TOKEN\b",
        r"\bTEST_PYPI_API_TOKEN\b",
        r"\bTWINE_PASSWORD\b",
        r"\bTWINE_USERNAME\b",
        r"\b__token__\b",
    ]
    if path.name in {"publish-testpypi.yml", "publish-pypi.yml"}:
        for pattern in token_patterns:
            match = re.search(pattern, text)
            if match:
                violations.append(
                    Violation(
                        path,
                        "publish workflows must use Trusted Publishing, not API token credentials",
                        text[: match.start()].count("\n") + 1,
                    )
                )

    if path.name == "testpypi-install.yml":
        forbidden_install_job = {
            "maturin build": (
                "TestPyPI install workflow must install published artifacts, not build locally"
            ),
            "maturin sdist": (
                "TestPyPI install workflow must install published artifacts, not build locally"
            ),
            "pip install -e": "TestPyPI install workflow must not use editable local installs",
            "python -m pip install -e": (
                "TestPyPI install workflow must not use editable local installs"
            ),
        }
        for needle, message in forbidden_install_job.items():
            if needle in text:
                violations.append(Violation(path, message, _line_number(text, needle)))
        violations.extend(_require_platform_labels(path, text))

    if path.name == "wheels.yml":
        violations.extend(_require_platform_labels(path, text))
        if "manylinux" not in text or "--compatibility pypi" not in text:
            violations.append(
                Violation(
                    path,
                    "wheel workflow must keep manylinux-compatible PyPI wheel settings",
                )
            )

    if path.name == "ci.yml":
        violations.extend(_check_ci_structure(path, text))

    return violations


def check_toolchain_file(path: Path = TOOLCHAIN_FILE) -> list[Violation]:
    if not path.exists():
        return [Violation(path, "rust-toolchain.toml does not exist")]
    text = path.read_text()
    violations: list[Violation] = []
    if f'channel = "{REQUIRED_RUST_TOOLCHAIN}"' not in text:
        violations.append(
            Violation(path, f"rust-toolchain.toml must pin channel {REQUIRED_RUST_TOOLCHAIN}")
        )
    if 'profile = "minimal"' not in text:
        violations.append(
            Violation(path, 'rust-toolchain.toml should use profile = "minimal" for CI stability')
        )
    if "components" in text:
        violations.append(
            Violation(
                path,
                "install rustfmt/clippy in workflow setup, not rust-toolchain.toml components",
            )
        )
    return violations


def check_workflows(workflow_dir: Path = WORKFLOW_DIR) -> list[Violation]:
    if not workflow_dir.exists():
        return [Violation(workflow_dir, "workflow directory does not exist")]
    violations: list[Violation] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        violations.extend(check_workflow_text(path, path.read_text()))
    for path in sorted(workflow_dir.glob("*.yaml")):
        violations.extend(check_workflow_text(path, path.read_text()))
    violations.extend(check_toolchain_file())
    return violations


def main() -> None:
    violations = check_workflows()
    if violations:
        print("GitHub Actions policy violations found:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation.format()}", file=sys.stderr)
        raise SystemExit(1)
    print("GitHub Actions check passed: workflows follow install/build policy.")


if __name__ == "__main__":
    main()
