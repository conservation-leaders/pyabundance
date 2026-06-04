from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
from pyabundance import compare_models, export_model_report, pcount_df


def _json_default(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


def _fit_meta(fit: Any, runtime_seconds: float) -> dict[str, Any]:
    return {
        "model": fit.mixture,
        "mixture": fit.mixture,
        "logLik": float(fit.loglik),
        "AIC": float(fit.aic),
        "n_params": int(fit.params.size),
        "K": int(fit.K),
        "runtime_seconds": float(runtime_seconds),
        "success": bool(fit.success),
        "message": fit.message,
        "warnings": fit.warnings or [],
        "visit_labels": fit.visit_labels,
        "visit_label_source": fit.visit_label_source,
    }


def _timed_fit(**kwargs: Any) -> tuple[Any, float]:
    start = time.perf_counter()
    fit = pcount_df(**kwargs)
    return fit, time.perf_counter() - start


def main() -> None:
    data_dir = Path("data/mallard")
    results_dir = Path("results/mallard")
    results_dir.mkdir(parents=True, exist_ok=True)
    site_path = data_dir / "site_data_for_py.csv"
    obs_path = data_dir / "obs_data_for_py.csv"
    if not site_path.exists() or not obs_path.exists():
        raise SystemExit(
            "Mallard CSVs are missing. Run "
            "Rscript examples/validation/export_mallard_from_unmarked.R first."
        )

    site_data = pd.read_csv(site_path)
    obs_data = pd.read_csv(obs_path)
    obs_data["date2"] = obs_data["date"] ** 2
    count_cols = ["y1", "y2", "y3"]
    common = {
        "site_data": site_data,
        "obs_data": obs_data,
        "site_id_col": "site_id",
        "visit_col": "visit",
        "count_cols": count_cols,
        "K": 30,
        "se": True,
        "cov_method": "bfgs",
    }

    poisson_fit, poisson_runtime = _timed_fit(
        **common,
        abundance_formula="~ length + elev + forest",
        detection_formula="~ ivel + date + date2",
        mixture="poisson",
    )
    nb_fit, nb_runtime = _timed_fit(
        **common,
        abundance_formula="~ length + elev",
        detection_formula="~ date + date2",
        mixture="negative_binomial",
    )
    zip_fit, zip_runtime = _timed_fit(
        **common,
        abundance_formula="~ length + elev + forest",
        detection_formula="~ ivel + date + date2",
        mixture="zero_inflated_poisson",
    )

    outputs = [
        ("py_poisson", poisson_fit, poisson_runtime),
        ("py_nb", nb_fit, nb_runtime),
        ("py_zip", zip_fit, zip_runtime),
    ]
    for prefix, fit, runtime in outputs:
        (results_dir / f"{prefix}_meta.json").write_text(
            json.dumps(_fit_meta(fit, runtime), indent=2, default=_json_default) + "\n",
            encoding="utf-8",
        )
        fit.coef_table(as_dataframe=True).to_csv(results_dir / f"{prefix}_coef.csv", index=False)
        export_model_report(fit, results_dir / f"{prefix}_report.md", format="markdown")

    comparison = compare_models(
        [poisson_fit, nb_fit, zip_fit],
        names=["poisson", "negative_binomial", "zip"],
    )
    comparison.table.to_csv(results_dir / "py_model_comparison.csv", index=False)
    print("Wrote pyabundance Mallard results to", results_dir)


if __name__ == "__main__":
    main()
