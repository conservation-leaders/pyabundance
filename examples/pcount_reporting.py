from __future__ import annotations

from pathlib import Path

from pyabundance import load_example_pcount, pcount_df

example = load_example_pcount("poisson", n_sites=100, seed=20260607)
fit = pcount_df(
    site_data=example.site_data,
    count_cols=example.count_cols,
    abundance_formula=example.abundance_formula,
    detection_formula=example.detection_formula,
    K=example.K,
    se=True,
)

print(fit.abundance_dataframe(se=True, interval=True).head())
print(fit.fitted_counts_dataframe().head())

out_dir = Path("reports/examples")
fit.export_summary(out_dir / "pcount_report.md")
fit.export_summary(out_dir / "pcount_report.json")
fit.export_summary(out_dir / "pcount_coefficients.csv")
