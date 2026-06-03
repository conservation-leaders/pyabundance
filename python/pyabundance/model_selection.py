from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def _as_named_fits(fits: Iterable[Any] | dict[str, Any]) -> list[tuple[str, Any]]:
    if isinstance(fits, dict):
        return [(str(name), fit) for name, fit in fits.items()]
    out = []
    for idx, fit in enumerate(fits):
        label = getattr(fit, "label", None) or f"model_{idx + 1}"
        if getattr(fit, "from_dataframe", False) and getattr(fit, "mixture", None):
            label = f"{fit.mixture}_{idx + 1}"
        out.append((str(label), fit))
    if not out:
        raise ValueError("at least one fitted model is required")
    return out


def aic_table(fits: Iterable[Any] | dict[str, Any], *, sort: bool = True) -> pd.DataFrame:
    """Build an AIC model-selection table from fitted pyabundance models."""
    rows = []
    for name, fit in _as_named_fits(fits):
        rows.append(
            {
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
        )
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


def compare_models(fits: Iterable[Any] | dict[str, Any], *, sort: bool = True) -> ModelComparison:
    """Compare fitted pyabundance models with an AIC table and markdown summary."""

    named = _as_named_fits(fits)
    table = aic_table(dict(named), sort=sort)
    return ModelComparison(table=table, models=dict(named))


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    columns = [str(col) for col in df.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in df.columns) + " |")
    return "\n".join(lines)
