from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _read_r_meta(path: Path) -> dict[str, Any]:
    row = pd.read_csv(path).iloc[0].to_dict()
    return row


def _read_py_meta(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _summary_row(label: str, r_meta: dict[str, Any], py_meta: dict[str, Any]) -> dict[str, Any]:
    r_loglik = float(r_meta["logLik"])
    py_loglik = float(py_meta["logLik"])
    r_aic = float(r_meta["AIC"])
    py_aic = float(py_meta["AIC"])
    r_seconds = float(r_meta["runtime_seconds"])
    py_seconds = float(py_meta["runtime_seconds"])
    return {
        "model": label,
        "r_logLik": r_loglik,
        "py_logLik": py_loglik,
        "abs_logLik_diff": abs(r_loglik - py_loglik),
        "r_AIC": r_aic,
        "py_AIC": py_aic,
        "abs_AIC_diff": abs(r_aic - py_aic),
        "r_runtime_seconds": r_seconds,
        "py_runtime_seconds": py_seconds,
        "local_speed_ratio_r_over_python": r_seconds / py_seconds if py_seconds > 0 else None,
    }


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(col) for col in df.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)


def main() -> None:
    results_dir = Path("results/mallard")
    required = {
        "r_poisson": results_dir / "r_poisson_meta.csv",
        "r_nb": results_dir / "r_nb_meta.csv",
        "py_poisson": results_dir / "py_poisson_meta.json",
        "py_nb": results_dir / "py_nb_meta.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise SystemExit("Missing Mallard result files: " + ", ".join(missing))

    rows = [
        _summary_row(
            "poisson", _read_r_meta(required["r_poisson"]), _read_py_meta(required["py_poisson"])
        ),
        _summary_row(
            "negative_binomial",
            _read_r_meta(required["r_nb"]),
            _read_py_meta(required["py_nb"]),
        ),
    ]
    summary = pd.DataFrame(rows)
    summary_path = results_dir / "mallard_py_vs_r_summary.csv"
    summary.to_csv(summary_path, index=False)

    markdown_lines = [
        "# Mallard pyabundance vs R/unmarked validation summary",
        "",
        "R/unmarked was used only as a black-box comparison target.",
        "Runtime ratios are local benchmarks and are not universal performance claims.",
        "",
        _dataframe_to_markdown(summary),
        "",
    ]
    md_path = results_dir / "mallard_validation_summary.md"
    md_path.write_text("\n".join(markdown_lines), encoding="utf-8")
    print(summary.to_string(index=False))
    print("Wrote", summary_path)
    print("Wrote", md_path)


if __name__ == "__main__":
    main()
