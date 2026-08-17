from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

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


def _workflow_job_block(text: str, job_id: str) -> str | None:
    normalized = textwrap.dedent(text)
    job_pattern = re.compile(rf"^  {re.escape(job_id)}:\s*(?:#.*)?$", re.MULTILINE)
    match = job_pattern.search(normalized)
    if match is None:
        return None
    next_job = re.search(
        r"^  [A-Za-z0-9_-]+:\s*(?:#.*)?$",
        normalized[match.end() :],
        re.MULTILINE,
    )
    end = match.end() + next_job.start() if next_job is not None else len(normalized)
    return normalized[match.start() : end]


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
        full_check_job = _workflow_job_block(text, "full-check") or ""
        merge_gate_job = _workflow_job_block(text, "merge-gate") or ""
        active_lines = {
            line.strip()
            for line in merge_gate_job.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        if "python scripts/check_all.py" not in full_check_job:
            violations.append(
                Violation(path, "CI must run the repository-owned full check command")
            )
        merge_gate_markers = ("name: Merge gate", "if: always()")
        if not merge_gate_job or not all(marker in merge_gate_job for marker in merge_gate_markers):
            violations.append(
                Violation(path, "CI must expose a stable aggregate check named Merge gate")
            )
        if not re.search(
            r"needs:\s*\[\s*full-check\s*,\s*compatibility\s*\]",
            merge_gate_job,
        ):
            violations.append(
                Violation(path, "Merge gate must depend on full-check and compatibility jobs")
            )
        result_markers = ("needs.full-check.result", "needs.compatibility.result")
        if not all(marker in merge_gate_job for marker in result_markers):
            violations.append(Violation(path, "Merge gate must evaluate all dependency results"))
        success_assertions = {
            'test "$FULL_CHECK_RESULT" = "success"',
            'test "$COMPATIBILITY_RESULT" = "success"',
        }
        if not success_assertions.issubset(active_lines):
            violations.append(Violation(path, "Merge gate must assert every dependency succeeded"))

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
