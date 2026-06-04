from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_github_actions.py"
SPEC = importlib.util.spec_from_file_location("check_github_actions", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
check_github_actions = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_github_actions
SPEC.loader.exec_module(check_github_actions)

check_workflow_text = check_github_actions.check_workflow_text
check_workflows = check_github_actions.check_workflows


def test_current_github_actions_workflows_pass_policy() -> None:
    assert check_workflows() == []


def test_detects_maturin_develop_in_workflow() -> None:
    violations = check_workflow_text(Path("ci.yml"), "steps:\n  - run: maturin develop\n")
    assert any("maturin develop" in violation.message for violation in violations)


def test_detects_testpypi_local_build() -> None:
    violations = check_workflow_text(
        Path("testpypi-install.yml"), "steps:\n  - run: maturin build --release\n"
    )
    assert any("must install published artifacts" in violation.message for violation in violations)


def test_detects_publish_token_credentials() -> None:
    violations = check_workflow_text(
        Path("publish-pypi.yml"), "env:\n  PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}\n"
    )
    assert any("Trusted Publishing" in violation.message for violation in violations)
