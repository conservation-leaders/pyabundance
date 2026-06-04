from __future__ import annotations

import json
import time
from pathlib import Path

from pyabundance import (
    analyze_pcount,
    compare_models,
    load_example_pcount,
    pcount,
    pcount_df,
    suggest_K,
)


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


def main() -> None:
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    data = load_example_pcount("poisson", n_sites=80)
    K = int(suggest_K(data.y))

    matrix_fit, matrix_time = timed(lambda: pcount(data.y, data.X, data.W, K=K))
    df_fit, df_time = timed(
        lambda: pcount_df(
            site_data=data.site_data,
            obs_data=data.obs_data,
            site_id_col="site_id",
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            K=K,
        )
    )
    _, k_time = timed(lambda: suggest_K(data.y))
    analysis, analysis_time = timed(
        lambda: analyze_pcount(
            site_data=data.site_data,
            obs_data=data.obs_data,
            site_id_col="site_id",
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            K="auto",
            se=False,
        )
    )
    _, compare_time = timed(lambda: compare_models([matrix_fit, df_fit], names=["matrix", "df"]))
    report_path = reports / "RC2_UX_BENCHMARK_report.md"
    _, report_time = timed(lambda: analysis.export_report(report_path))

    payload = {
        "status": "COMPLETED",
        "dataset": {"n_sites": len(data.site_data), "n_visits": len(data.count_cols), "K": K},
        "runtime_seconds": {
            "matrix_pcount_poisson": matrix_time,
            "pcount_df_poisson": df_time,
            "analyze_pcount_poisson_nb_zip": analysis_time,
            "K_auto_overhead": k_time,
            "compare_models_names": compare_time,
            "report_export": report_time,
        },
        "notes": [
            "This benchmark measures orchestration overhead.",
            "Likelihood kernels remain Rust-backed.",
            "Local benchmark results are not universal performance claims.",
        ],
    }
    (reports / "rc2_ux_benchmark.json").write_text(json.dumps(payload, indent=2) + "\n")
    md = [
        "# RC2 UX Benchmark",
        "",
        "Status: COMPLETED",
        "",
        "Dataset:",
        f"- n_sites: {payload['dataset']['n_sites']}",
        f"- n_visits: {payload['dataset']['n_visits']}",
        f"- K: {payload['dataset']['K']}",
        "",
        "Runtime:",
    ]
    for key, value in payload["runtime_seconds"].items():
        md.append(f"- {key}: {value:.6f} s")
    md.extend(["", "Notes:", *[f"- {note}" for note in payload["notes"]]])
    (reports / "RC2_UX_BENCHMARK.md").write_text("\n".join(md) + "\n")
    print("Wrote reports/RC2_UX_BENCHMARK.md and reports/rc2_ux_benchmark.json")


if __name__ == "__main__":
    main()
