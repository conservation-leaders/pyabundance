from __future__ import annotations

import json
import time
from pathlib import Path

from pyabundance import aic_table, load_example_pcount, pcount_df

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    data = load_example_pcount("poisson", n_sites=120, seed=20260606)
    fits = {}
    seconds = {}
    model_specs = [
        ("poisson", data.K),
        ("negative_binomial", 100),
        ("zero_inflated_poisson", 100),
    ]
    for mixture, K in model_specs:
        t0 = time.perf_counter()
        fits[mixture] = pcount_df(
            site_data=data.site_data,
            count_cols=data.count_cols,
            abundance_formula=data.abundance_formula,
            detection_formula=data.detection_formula,
            mixture=mixture,
            K=K,
        )
        seconds[mixture] = time.perf_counter() - t0
    table = aic_table(fits)
    payload = {
        "status": "completed",
        "seconds": seconds,
        "aic_table": table.to_dict(orient="records"),
        "best_model": str(table.iloc[0]["model"]),
    }
    (REPORTS / "reporting_workflow.json").write_text(json.dumps(payload, indent=2) + "\n")
    report = (
        "# Reporting Workflow Check\n\nStatus: COMPLETED\n\n" + table.to_string(index=False) + "\n"
    )
    (REPORTS / "REPORTING_WORKFLOW.md").write_text(report)


if __name__ == "__main__":
    main()
