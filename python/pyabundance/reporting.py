from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    return str(value)


def _unique_preserving_order(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value)
        if text not in seen:
            out.append(text)
            seen.add(text)
    return out


def model_report(fit: Any, *, include_posterior_abundance: bool = False) -> dict[str, Any]:
    """Return a JSON-serializable report dictionary for a fitted model."""
    report = {
        "model": "pcount",
        "mixture": fit.mixture,
        "K": fit.K,
        "n_sites": int(fit.X.shape[0]),
        "n_visits": int(fit.W.shape[1]),
        "n_params": int(fit.params.size),
        "logLik": float(fit.loglik),
        "AIC": float(fit.aic),
        "success": bool(fit.success),
        "message": fit.message,
        "method": fit.method,
        "nfev": fit.nfev,
        "nit": fit.nit,
        "cov_method": fit.cov_method,
        "covariance_diagnostics": fit.covariance_diagnostics,
        "warnings": fit.warnings,
        "abundance_formula": fit.abundance_formula,
        "detection_formula": fit.detection_formula,
        "coefficients": fit.coef_table(include_z=False).to_dict(orient="records"),
        "transformed_params": fit.transformed_params().to_dict(orient="records"),
        "diagnostics": fit.diagnostics(),
    }
    if include_posterior_abundance:
        total = fit.total_abundance_posterior(nsim=1000, seed=123)
        report["posterior_abundance"] = {
            "note": (
                "Posterior abundance conditions on fitted parameters and does not include "
                "full parameter uncertainty."
            ),
            "total": {
                "mean": total.mean,
                "median": total.median,
                "lower": total.lower,
                "upper": total.upper,
                "level": total.level,
                "nsim": total.nsim,
            },
            "site_summary_head": fit.posterior_abundance_summary()
            .head(10)
            .to_dict(orient="records"),
        }
    return report


def report_markdown(fit: Any, *, include_posterior_abundance: bool = False) -> str:
    coef = fit.coef_table(include_z=False)
    lines = [
        "# pyabundance model report",
        "",
        f"- mixture: {fit.mixture}",
        f"- sites: {fit.X.shape[0]}",
        f"- visits: {fit.W.shape[1]}",
        f"- K: {fit.K}",
        f"- logLik: {fit.loglik:.6g}",
        f"- AIC: {fit.aic:.6g}",
        f"- success: {fit.success}",
        f"- message: {fit.message}",
        "",
        "## Coefficients",
        "",
        _dataframe_to_markdown(coef),
    ]
    transformed = fit.transformed_params()
    if not transformed.empty:
        lines.extend(["", "## Transformed parameters", "", _dataframe_to_markdown(transformed)])
    if include_posterior_abundance:
        total = fit.total_abundance_posterior(nsim=1000, seed=123)
        site_summary = fit.posterior_abundance_summary().head(10)
        lines.extend(
            [
                "",
                "## Posterior abundance",
                "",
                total.summary(),
                "",
                "Posterior abundance conditions on fitted parameters and does not include "
                "full parameter uncertainty.",
                "",
                "First 10 site-level summaries:",
                "",
                _dataframe_to_markdown(site_summary),
            ]
        )
    warnings = _unique_preserving_order(list(fit.warnings or []))
    cov_warnings = _unique_preserving_order(
        list((fit.covariance_diagnostics or {}).get("warnings", []))
    )
    if warnings or cov_warnings:
        lines.extend(["", "## Warnings", ""])
        if warnings:
            lines.append("### Model warnings")
            lines.append("")
            lines.extend(f"- {warning}" for warning in warnings)
        unique_cov_warnings = [warning for warning in cov_warnings if warning not in warnings]
        if unique_cov_warnings:
            if warnings:
                lines.append("")
            lines.append("### Covariance warnings")
            lines.append("")
            lines.extend(f"- {warning}" for warning in unique_cov_warnings)
    return "\n".join(lines) + "\n"


def export_model_report(
    fit: Any,
    path: str | Path,
    *,
    format: str | None = None,
    include_posterior_abundance: bool = False,
) -> None:
    """Export a fitted model report as JSON, Markdown, or CSV coefficient table."""
    out = Path(path)
    fmt = (format or out.suffix.lstrip(".") or "json").lower()
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        out.write_text(
            json.dumps(
                model_report(fit, include_posterior_abundance=include_posterior_abundance),
                indent=2,
                default=_json_default,
            )
            + "\n"
        )
    elif fmt in {"md", "markdown"}:
        out.write_text(
            report_markdown(fit, include_posterior_abundance=include_posterior_abundance)
        )
    elif fmt == "csv":
        fit.coef_table(include_z=False).to_csv(out, index=False)
    else:
        raise ValueError("format must be 'json', 'markdown', or 'csv'")


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(col) for col in df.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)
