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

check_toolchain_file = check_github_actions.check_toolchain_file
check_workflow_text = check_github_actions.check_workflow_text
check_workflows = check_github_actions.check_workflows


def test_current_github_actions_workflows_pass_policy() -> None:
    assert check_workflows() == []


def test_ci_requires_a_stable_merge_gate() -> None:
    text = """
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - run: pytest
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("Merge gate" in violation.message for violation in violations)


def test_ci_merge_gate_must_depend_on_all_test_jobs() -> None:
    text = """
    jobs:
      full-check:
        steps:
          - run: python scripts/check_all.py
      compatibility:
        steps:
          - run: pytest
      merge-gate:
        name: Merge gate
        if: always()
        needs: [full-check]
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("full-check and compatibility" in violation.message for violation in violations)


def test_ci_merge_gate_must_consume_every_dependency_result() -> None:
    text = """
    jobs:
      full-check:
        steps:
          - run: python scripts/check_all.py
      compatibility:
        steps:
          - run: pytest
      merge-gate:
        name: Merge gate
        if: always()
        needs: [full-check, compatibility]
        steps:
          - run: "true"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("dependency results" in violation.message for violation in violations)


def test_ci_merge_gate_rejects_result_markers_without_success_assertions() -> None:
    text = """
    jobs:
      full-check:
        steps:
          - run: python scripts/check_all.py
      compatibility:
        steps:
          - run: pytest
      merge-gate:
        name: Merge gate
        if: always()
        needs: [full-check, compatibility]
        # needs.full-check.result needs.compatibility.result
        steps:
          - run: "true"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("assert every dependency succeeded" in violation.message for violation in violations)


def test_ci_merge_gate_does_not_borrow_assertions_from_another_job() -> None:
    text = """
    jobs:
      full-check:
        steps:
          - run: python scripts/check_all.py
          - run: |
              test "$FULL_CHECK_RESULT" = "success"
              test "$COMPATIBILITY_RESULT" = "success"
      compatibility:
        steps:
          - run: pytest
      merge-gate:
        name: Merge gate
        if: always()
        needs: [full-check, compatibility]
        env:
          FULL_CHECK_RESULT: ${{ needs.full-check.result }}
          COMPATIBILITY_RESULT: ${{ needs.compatibility.result }}
        steps:
          - run: "true"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("assert every dependency succeeded" in violation.message for violation in violations)


def test_detects_stale_macos_13_runner_label() -> None:
    violations = check_workflow_text(Path("wheels.yml"), "runs-on: macos-13\n")
    assert any("macos-13" in violation.message for violation in violations)


def test_detects_non_exact_rust_toolchain_action() -> None:
    violations = check_workflow_text(
        Path("ci.yml"), "steps:\n  - uses: dtolnay/rust-toolchain@1.83\n"
    )
    assert any("1.83.0" in violation.message for violation in violations)


def test_detects_maturin_develop_in_workflow() -> None:
    violations = check_workflow_text(Path("ci.yml"), "steps:\n  - run: maturin develop\n")
    assert any("maturin develop" in violation.message for violation in violations)


def test_detects_deprecated_upload_artifact_action() -> None:
    violations = check_workflow_text(
        Path("wheels.yml"), "steps:\n  - uses: actions/upload-artifact@v3\n"
    )
    assert any("upload-artifact@v4" in violation.message for violation in violations)


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


def test_wheel_workflow_requires_full_platform_matrix() -> None:
    text = """
    runs-on: ubuntu-latest
    os: macos-15-intel
    os: windows-latest
    args: --release --out dist --compatibility pypi
    manylinux: "2014"
    """
    violations = check_workflow_text(Path("wheels.yml"), text)
    assert any("macOS arm64" in violation.message for violation in violations)


def test_rust_toolchain_file_requires_exact_minimal_profile(tmp_path: Path) -> None:
    toolchain = tmp_path / "rust-toolchain.toml"
    toolchain.write_text('[toolchain]\nchannel = "1.83"\ncomponents = ["rustfmt", "clippy"]\n')
    violations = check_toolchain_file(toolchain)
    assert any("1.83.0" in violation.message for violation in violations)
    assert any("profile" in violation.message for violation in violations)
    assert any("components" in violation.message for violation in violations)
