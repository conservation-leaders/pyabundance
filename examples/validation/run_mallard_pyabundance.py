from __future__ import annotations

from pathlib import Path


def main() -> None:
    data_dir = Path("data/mallard")
    results_dir = Path("results/mallard")
    results_dir.mkdir(parents=True, exist_ok=True)
    if not data_dir.exists():
        raise SystemExit(
            "data/mallard/ is missing. Run "
            "examples/validation/export_mallard_from_unmarked.R first."
        )
    print(
        "Load exported Mallard CSVs, fit pyabundance models, and write "
        "results/mallard/pyabundance_results.csv"
    )


if __name__ == "__main__":
    main()
