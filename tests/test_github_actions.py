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

VALID_MINIMAL_CI = """
jobs:
  full-check:
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Run full repository check
        shell: bash
        run: python scripts/check_all.py
  compatibility:
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - name: Type check supported Python version
        shell: bash
        run: python -m mypy --python-version "${{ matrix.python-version }}" python/pyabundance
      - name: Run tests
        shell: bash
        run: python -m pytest -q
  merge-gate:
    name: Merge gate
    if: always()
    needs: [full-check, compatibility]
    runs-on: ubuntu-latest
    steps:
      - name: Require every CI job to pass
        shell: bash
        env:
          FULL_CHECK_RESULT: ${{ needs.full-check.result }}
          COMPATIBILITY_RESULT: ${{ needs.compatibility.result }}
        run: |
          test "$FULL_CHECK_RESULT" = "success"
          test "$COMPATIBILITY_RESULT" = "success"
"""


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


def test_ci_merge_gate_rejects_continue_on_error() -> None:
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
        runs-on: ubuntu-latest
        steps:
          - name: Require every CI job to pass
            continue-on-error: true
            env:
              FULL_CHECK_RESULT: ${{ needs.full-check.result }}
              COMPATIBILITY_RESULT: ${{ needs.compatibility.result }}
            run: |
              test "$FULL_CHECK_RESULT" = "success"
              test "$COMPATIBILITY_RESULT" = "success"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("canonical unconditional assertion step" in item.message for item in violations)


def test_ci_merge_gate_rejects_conditional_assertion_step() -> None:
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
        runs-on: ubuntu-latest
        steps:
          - name: Require every CI job to pass
            if: success()
            env:
              FULL_CHECK_RESULT: ${{ needs.full-check.result }}
              COMPATIBILITY_RESULT: ${{ needs.compatibility.result }}
            run: |
              test "$FULL_CHECK_RESULT" = "success"
              test "$COMPATIBILITY_RESULT" = "success"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("canonical unconditional assertion step" in item.message for item in violations)


def test_ci_merge_gate_rejects_failure_masking_shell() -> None:
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
        runs-on: ubuntu-latest
        steps:
          - name: Require every CI job to pass
            shell: bash {0} || true
            env:
              FULL_CHECK_RESULT: ${{ needs.full-check.result }}
              COMPATIBILITY_RESULT: ${{ needs.compatibility.result }}
            run: |
              test "$FULL_CHECK_RESULT" = "success"
              test "$COMPATIBILITY_RESULT" = "success"
    """

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("fail-fast Bash shell" in item.message for item in violations)


def test_ci_rejects_conditional_full_check_step() -> None:
    text = VALID_MINIMAL_CI.replace(
        "        shell: bash\n        run: python scripts/check_all.py",
        "        if: false\n        shell: bash\n        run: python scripts/check_all.py",
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("unconditional full-check step" in item.message for item in violations)


def test_ci_rejects_continue_on_error_full_check_step() -> None:
    text = VALID_MINIMAL_CI.replace(
        "        shell: bash\n        run: python scripts/check_all.py",
        "        continue-on-error: true\n"
        "        shell: bash\n"
        "        run: python scripts/check_all.py",
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("unconditional full-check step" in item.message for item in violations)


def test_ci_rejects_failure_masking_compatibility_job() -> None:
    text = VALID_MINIMAL_CI.replace(
        "  compatibility:\n    strategy:",
        "  compatibility:\n    continue-on-error: true\n    strategy:",
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("compatibility job must not mask failures" in item.message for item in violations)


def test_ci_requires_compatibility_typecheck_and_tests() -> None:
    text = VALID_MINIMAL_CI.replace(
        '        run: python -m mypy --python-version "${{ matrix.python-version }}" '
        "python/pyabundance",
        '        run: "true"',
    ).replace("        run: python -m pytest -q", '        run: "true"')

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("compatibility job must run mypy and pytest" in item.message for item in violations)


def test_ci_requires_setup_for_each_compatibility_interpreter() -> None:
    text = VALID_MINIMAL_CI.replace(
        "          python-version: ${{ matrix.python-version }}",
        '          python-version: "3.11"',
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("configure each matrix interpreter" in item.message for item in violations)


def test_ci_requires_python_311_for_full_check() -> None:
    text = VALID_MINIMAL_CI.replace(
        '          python-version: "3.11"',
        '          python-version: "3.12"',
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("configure Python 3.11" in item.message for item in violations)


def test_ci_rejects_test_control_environment_overrides() -> None:
    text = VALID_MINIMAL_CI.replace(
        "  compatibility:\n    strategy:",
        "  compatibility:\n    env:\n      PYTEST_ADDOPTS: --collect-only\n    strategy:",
    )

    violations = check_workflow_text(Path("ci.yml"), text)

    assert any("test-control environment" in item.message for item in violations)


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
