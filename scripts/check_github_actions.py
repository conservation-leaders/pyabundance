from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

WORKFLOW_DIR = Path(".github/workflows")
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

    return violations


def check_workflows(workflow_dir: Path = WORKFLOW_DIR) -> list[Violation]:
    if not workflow_dir.exists():
        return [Violation(workflow_dir, "workflow directory does not exist")]
    violations: list[Violation] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        violations.extend(check_workflow_text(path, path.read_text()))
    for path in sorted(workflow_dir.glob("*.yaml")):
        violations.extend(check_workflow_text(path, path.read_text()))
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
