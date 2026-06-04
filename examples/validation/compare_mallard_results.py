from __future__ import annotations

from pathlib import Path


def main() -> None:
    results_dir = Path("results/mallard")
    r_path = results_dir / "unmarked_results.csv"
    py_path = results_dir / "pyabundance_results.csv"
    missing = [str(path) for path in [r_path, py_path] if not path.exists()]
    if missing:
        raise SystemExit("Missing Mallard result files: " + ", ".join(missing))
    print("Compare logLik/AIC/runtime columns from R and Python result CSVs.")


if __name__ == "__main__":
    main()
