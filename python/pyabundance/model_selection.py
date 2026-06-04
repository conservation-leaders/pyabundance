from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def _as_named_fits(
    fits: Iterable[Any] | dict[str, Any], names: Iterable[Any] | None = None
) -> list[tuple[str, Any]]:
    if isinstance(fits, dict):
        if names is not None:
            raise ValueError("names cannot be used when fits is a dict; use dict keys instead")
        return [(str(name), fit) for name, fit in fits.items()]
    fits_list = list(fits)
    if names is not None:
        name_list = [str(name) for name in names]
        if len(name_list) != len(fits_list):
            raise ValueError("names must have the same length as fits")
        if len(set(name_list)) != len(name_list):
            raise ValueError("names must be unique")
        if not fits_list:
            raise ValueError("at least one fitted model is required")
        return list(zip(name_list, fits_list, strict=True))
    out = []
    for idx, fit in enumerate(fits_list):
        label = getattr(fit, "label", None) or f"model_{idx + 1}"
        if getattr(fit, "from_dataframe", False) and getattr(fit, "mixture", None):
            label = f"{fit.mixture}_{idx + 1}"
        out.append((str(label), fit))
    if not out:
        raise ValueError("at least one fitted model is required")
    return out


def aic_table(
    fits: Iterable[Any] | dict[str, Any],
    *,
    names: Iterable[Any] | None = None,
    sort: bool = True,
    include_warnings: bool = True,
    check_compatibility: bool = True,
) -> pd.DataFrame:
    """Build an AIC model-selection table from fitted pyabundance models."""
    del check_compatibility  # reserved for future compatibility checks
    rows = []
    for name, fit in _as_named_fits(fits, names=names):
        row = {
            "model": name,
            "mixture": fit.mixture,
            "n_params": int(fit.params.size),
            "logLik": float(fit.loglik),
            "AIC": float(fit.aic),
            "K": int(fit.K),
            "success": bool(fit.success),
            "nfev": fit.nfev,
            "nit": fit.nit,
            "abundance_formula": fit.abundance_formula,
            "detection_formula": fit.detection_formula,
        }
        if include_warnings:
            row["warnings"] = "; ".join(str(w) for w in (fit.warnings or []))
        rows.append(row)
    table = pd.DataFrame(rows)
    if sort:
        table = table.sort_values("AIC", kind="mergesort").reset_index(drop=True)
    min_aic = float(table["AIC"].min())
    table["delta_AIC"] = table["AIC"] - min_aic
    rel_lik = np.exp(-0.5 * table["delta_AIC"].to_numpy(dtype=np.float64))
    denom = float(np.sum(rel_lik))
    table["AIC_weight"] = rel_lik / denom if denom > 0 else np.nan
    table["rank"] = np.arange(1, len(table) + 1)
    cols = [
        "rank",
        "model",
        "mixture",
        "n_params",
        "logLik",
        "AIC",
        "delta_AIC",
        "AIC_weight",
        "K",
        "success",
        "nfev",
        "nit",
        "abundance_formula",
        "detection_formula",
    ]
    if include_warnings:
        cols.append("warnings")
    return table[cols]


@dataclass(frozen=True)
class ModelComparison:
    table: pd.DataFrame
    models: dict[str, Any]

    @property
    def best_model_name(self) -> str:
        return str(self.table.iloc[0]["model"])

    @property
    def best_model(self) -> Any:
        return self.models[self.best_model_name]

    def summary(self) -> str:
        display = self.table[["rank", "model", "mixture", "AIC", "delta_AIC", "AIC_weight"]]
        return display.to_string(index=False)

    def to_csv(self, path: str) -> None:
        self.table.to_csv(path, index=False)

    def to_markdown(self, path: str | None = None) -> str:
        text = _dataframe_to_markdown(self.table)
        if path is not None:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text + "\n")
        return text


def compare_models(
    fits: Iterable[Any] | dict[str, Any],
    *,
    names: Iterable[Any] | None = None,
    sort: bool = True,
    include_warnings: bool = True,
    check_compatibility: bool = True,
) -> ModelComparison:
    """Compare fitted pyabundance models with an AIC table and markdown summary."""

    named = _as_named_fits(fits, names=names)
    table = aic_table(
        dict(named),
        sort=sort,
        include_warnings=include_warnings,
        check_compatibility=check_compatibility,
    )
    return ModelComparison(table=table, models=dict(named))


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(col) for col in df.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)
