from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _find_wheel(path: Path) -> Path:
    if path.is_dir():
        wheels = sorted(path.glob("*.whl"))
        if not wheels:
            raise SystemExit(f"no wheel files found in {path}")
        return wheels[0]
    if path.suffix != ".whl":
        raise SystemExit(f"expected a .whl file or directory, got {path}")
    return path


def _install_wheel(path: Path) -> None:
    wheel = _find_wheel(path)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--force-reinstall", str(wheel)],
        check=True,
    )


def _smoke(expected_version: str | None = None) -> None:
    from pyabundance import (
        __version__,
        compare_models,
        load_example_pcount,
        pcount_df,
    )

    if expected_version is not None and __version__ != expected_version:
        raise AssertionError(f"expected pyabundance {expected_version}, got {__version__}")
    data = load_example_pcount("poisson", n_sites=25, seed=20260608)
    fit1 = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula=data.abundance_formula,
        detection_formula=data.detection_formula,
        K=data.K,
    )
    fit2 = pcount_df(
        site_data=data.site_data,
        count_cols=data.count_cols,
        abundance_formula="~ 1",
        detection_formula=data.detection_formula,
        K=data.K,
    )
    assert fit1.success, fit1.message
    assert fit1.posterior_abundance().shape == (25, data.K + 1)
    assert fit1.ranef().shape[0] == 25
    comparison = compare_models({"covariate": fit1, "intercept": fit2})
    assert comparison.table.shape[0] == 2
    print(f"pyabundance {__version__} wheel smoke test passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install and smoke-test a built pyabundance wheel."
    )
    parser.add_argument("path", nargs="?", default=None, help="Wheel file or dist directory")
    parser.add_argument(
        "--from-installed",
        action="store_true",
        help="Do not install a wheel; smoke-test the already installed package.",
    )
    parser.add_argument("--expected-version", default=None)
    args = parser.parse_args()
    if not args.from_installed:
        if args.path is None:
            # Backward-compatible mode for CI jobs that already installed the wheel.
            args.from_installed = True
        else:
            _install_wheel(Path(args.path))
    _smoke(args.expected_version)


if __name__ == "__main__":
    main()
