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


def _shape_or_none(value: Any) -> tuple[int, ...] | None:
    shape = getattr(value, "shape", None)
    if shape is None:
        return None
    return tuple(int(dim) for dim in shape)


def _list_or_none(value: Any) -> list[Any] | None:
    if value is None:
        return None
    try:
        return list(value)
    except TypeError:
        return None


def _compatibility_warnings(named_fits: list[tuple[str, Any]]) -> dict[str, list[str]]:
    """Return lightweight AIC-comparison compatibility warnings by model name."""

    warnings: dict[str, list[str]] = {name: [] for name, _ in named_fits}
    if len(named_fits) <= 1:
        return warnings

    signatures: dict[str, list[tuple[str, Any]]] = {
        "K": [(name, getattr(fit, "K", None)) for name, fit in named_fits],
        "response_shape": [
            (name, _shape_or_none(getattr(fit, "y", None))) for name, fit in named_fits
        ],
        "n_sites": [
            (name, int(getattr(getattr(fit, "X", None), "shape", [0])[0]))
            if getattr(fit, "X", None) is not None
            else (name, None)
            for name, fit in named_fits
        ],
        "n_visits": [
            (name, int(getattr(getattr(fit, "W", None), "shape", [0, 0])[1]))
            if getattr(fit, "W", None) is not None
            else (name, None)
            for name, fit in named_fits
        ],
        "site_ids": [
            (name, _list_or_none(getattr(fit, "site_ids", None))) for name, fit in named_fits
        ],
        "visit_labels": [
            (name, _list_or_none(getattr(fit, "visit_labels", None))) for name, fit in named_fits
        ],
    }
    messages = {
        "K": "Models use different K values; AIC comparison may be affected by truncation choices.",
        "response_shape": (
            "Models appear to use different response dimensions; AIC comparisons are most "
            "meaningful for the same response data."
        ),
        "n_sites": (
            "Models appear to use different site counts; AIC comparisons are most meaningful "
            "for the same response data."
        ),
        "n_visits": (
            "Models appear to use different visit counts; AIC comparisons are most meaningful "
            "for the same response data."
        ),
        "site_ids": "Models have different site_ids metadata.",
        "visit_labels": "Models have different visit_labels metadata.",
    }
    for key, values in signatures.items():
        comparable = [(name, value) for name, value in values if value is not None]
        if len(comparable) <= 1:
            continue
        first_value = comparable[0][1]
        if any(value != first_value for _, value in comparable[1:]):
            for name, _ in comparable:
                warnings[name].append(messages[key])
    return warnings


def aic_table(
    fits: Iterable[Any] | dict[str, Any],
    *,
    names: Iterable[Any] | None = None,
    sort: bool = True,
    include_warnings: bool = True,
    check_compatibility: bool = True,
) -> pd.DataFrame:
    """Build an AIC model-selection table from fitted pyabundance models."""
    rows = []
    named = _as_named_fits(fits, names=names)
    compatibility = _compatibility_warnings(named) if check_compatibility else {}
    for name, fit in named:
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
            row_warnings = [str(w) for w in (fit.warnings or [])]
            row_warnings.extend(compatibility.get(name, []))
            row["warnings"] = "; ".join(row_warnings)
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
