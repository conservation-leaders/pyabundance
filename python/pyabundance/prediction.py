from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from formulaic import Formula
from numpy.typing import NDArray

from pyabundance.core.formulas import build_process_design

_INTERNAL_SITE_INDEX = "__pyabundance_site_index__"
_PredictionType = Literal["lambda", "abundance", "p", "detection", "fitted"]


def predict_pcount_formula_newdata(
    result: Any,
    prediction_type: _PredictionType,
    *,
    newdata: Any = None,
    new_site_data: Any = None,
    new_obs_data: Any = None,
    site_id_col: str | None = None,
    visit_col: str = "visit",
    visit_labels: list[Any] | tuple[Any, ...] | str | None = None,
    se: bool = False,
    interval: bool = False,
    level: float = 0.95,
    as_dataframe: bool = False,
) -> NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame:
    """Predict a pcount result on formula-based new site/observation data."""

    if prediction_type in {"lambda", "abundance"}:
        _require_formula_metadata(result, process="lambda")
    elif prediction_type in {"p", "detection"}:
        _require_formula_metadata(result, process="p")
    else:
        _require_formula_metadata(result, process="lambda")
        _require_formula_metadata(result, process="p")
    if prediction_type in {"lambda", "abundance"} and new_obs_data is not None:
        raise ValueError("new_obs_data is only supported for detection and fitted predictions")

    site_df = _resolve_new_site_data(newdata=newdata, new_site_data=new_site_data)
    resolved_site_id_col, site_ids = _resolve_site_ids(site_df, site_id_col)

    if prediction_type in {"lambda", "abundance"}:
        x_new = build_abundance_design(result, site_df)
        out = result.predict_lambda(X=x_new, se=se, interval=interval, level=level)
        return _lambda_output(out, site_ids=site_ids, as_dataframe=as_dataframe)

    if prediction_type in {"p", "detection"}:
        w_new, visits = build_detection_design(
            result,
            site_df,
            new_obs_data=new_obs_data,
            site_id_col=resolved_site_id_col,
            site_ids=site_ids,
            visit_col=visit_col,
            visit_labels=visit_labels,
        )
        out = result.predict_detection(W=w_new, se=se, interval=interval, level=level)
        return _detection_output(
            out, site_ids=site_ids, visit_labels=visits, as_dataframe=as_dataframe
        )

    if se or interval:
        raise ValueError(
            "standard errors and intervals are not supported for fitted newdata predictions"
        )
    x_new = build_abundance_design(result, site_df)
    w_new, visits = build_detection_design(
        result,
        site_df,
        new_obs_data=new_obs_data,
        site_id_col=resolved_site_id_col,
        site_ids=site_ids,
        visit_col=visit_col,
        visit_labels=visit_labels,
    )
    lam = np.asarray(result.predict_lambda(X=x_new), dtype=np.float64)
    if getattr(result, "mixture", None) == "zero_inflated_poisson":
        lam = lam * (1.0 - float(getattr(result, "psi", 0.0) or 0.0))
    p = np.asarray(result.predict_detection(W=w_new), dtype=np.float64)
    fitted = lam[:, None] * p
    if as_dataframe:
        return _fitted_dataframe(fitted, site_ids=site_ids, visit_labels=visits)
    return fitted


def build_abundance_design(result: Any, site_data: pd.DataFrame) -> NDArray[np.float64]:
    """Build and validate a newdata abundance design matrix for a pcount result."""

    _require_formula_metadata(result, process="lambda")
    spec = result.model_spec.process("lambda")
    _check_missing_covariates(spec.formula, site_data, "new_site_data", "abundance_formula")
    design = build_process_design(spec, site_data)
    expected = _expected_columns(result, "abundance", spec.columns)
    _validate_design_columns(
        process="abundance",
        actual=design.columns,
        expected=expected,
    )
    return design.matrix


def build_detection_design(
    result: Any,
    site_data: pd.DataFrame,
    *,
    new_obs_data: Any = None,
    site_id_col: str | None,
    site_ids: list[Any],
    visit_col: str,
    visit_labels: list[Any] | tuple[Any, ...] | str | None,
) -> tuple[NDArray[np.float64], list[Any]]:
    """Build and validate a newdata detection design tensor for a pcount result."""

    _require_formula_metadata(result, process="p")
    visits = _resolve_visit_labels(result, visit_labels)
    if new_obs_data is None:
        obs_df = _default_obs_data(
            site_data,
            site_ids=site_ids,
            site_id_col=site_id_col,
            visit_col=visit_col,
            visit_labels=visits,
        )
    else:
        obs_df = _provided_obs_data(
            site_data,
            new_obs_data,
            site_ids=site_ids,
            site_id_col=site_id_col,
            visit_col=visit_col,
            visit_labels=visits,
        )
    obs_df[visit_col] = pd.Categorical(obs_df[visit_col], categories=visits, ordered=True)
    spec = result.model_spec.process("p")
    _check_missing_covariates(spec.formula, obs_df, "new_obs_data", "detection_formula")
    design = build_process_design(spec, obs_df)
    expected = _expected_columns(result, "detection", spec.columns)
    _validate_design_columns(
        process="detection",
        actual=design.columns,
        expected=expected,
    )

    n_sites = len(site_ids)
    n_visits = len(visits)
    if design.matrix.shape[0] != n_sites * n_visits:
        raise ValueError("detection newdata must contain one row per site × visit")
    w_new = design.matrix.reshape(n_sites, n_visits, design.matrix.shape[1])
    return np.ascontiguousarray(w_new, dtype=np.float64), visits


def _resolve_new_site_data(*, newdata: Any, new_site_data: Any) -> pd.DataFrame:
    if newdata is not None and new_site_data is not None:
        raise ValueError("pass only one of newdata or new_site_data")
    value = new_site_data if new_site_data is not None else newdata
    if not isinstance(value, pd.DataFrame):
        raise ValueError(
            "new_site_data must be a pandas DataFrame for formula newdata prediction"
        )
    return value.reset_index(drop=True).copy()


def _resolve_site_ids(
    site_data: pd.DataFrame, site_id_col: str | None
) -> tuple[str | None, list[Any]]:
    resolved = site_id_col
    if resolved is None and "site_id" in site_data.columns:
        resolved = "site_id"
    if resolved is None:
        return None, list(range(len(site_data)))
    if resolved not in site_data.columns:
        raise ValueError(f"new_site_data must contain site_id_col {resolved!r}")
    site_ids = site_data[resolved].tolist()
    if len(set(site_ids)) != len(site_ids):
        raise ValueError(f"new_site_data site_id_col {resolved!r} must contain unique values")
    return resolved, site_ids


def _require_formula_metadata(result: Any, *, process: str) -> None:
    spec = getattr(result, "model_spec", None)
    processes = getattr(spec, "processes", {})
    process_spec = processes.get(process) if hasattr(processes, "get") else None
    if process_spec is None or getattr(process_spec, "formula", None) is None:
        raise ValueError(
            "formula metadata is required for pcount formula newdata prediction; "
            "fit with pcount_df for formula prediction, or use matrix X/W prediction methods"
        )


def _expected_columns(result: Any, kind: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
    attr = f"{kind}_column_names"
    names = getattr(result, attr, None)
    if names:
        return tuple(str(name) for name in names)
    return tuple(fallback)


def _validate_design_columns(
    *, process: str, actual: tuple[str, ...], expected: tuple[str, ...]
) -> None:
    if actual == expected:
        return
    missing = [name for name in expected if name not in actual]
    extra = [name for name in actual if name not in expected]
    details = []
    if missing:
        details.append(f"missing fitted columns: {missing}")
    if extra:
        details.append(f"unexpected newdata columns: {extra}")
    detail = "; ".join(details) if details else f"expected {expected}, got {actual}"
    raise ValueError(f"{process} design columns do not match fitted columns: {detail}")


def _check_missing_covariates(
    formula: str | None, data: pd.DataFrame, data_name: str, formula_name: str
) -> None:
    if formula is None:
        return
    try:
        required = {str(var) for var in Formula(formula).required_variables}
    except Exception:
        return
    missing = sorted(var for var in required if var not in data.columns)
    if missing:
        raise ValueError(f"{data_name} is missing covariates required by {formula_name}: {missing}")


def _resolve_visit_labels(
    result: Any, visit_labels: list[Any] | tuple[Any, ...] | str | None
) -> list[Any]:
    if visit_labels is not None and visit_labels != "auto":
        if isinstance(visit_labels, str) or not hasattr(visit_labels, "__iter__"):
            raise ValueError("visit_labels must be a non-empty list-like object")
        out = list(visit_labels)
        if not out:
            raise ValueError("visit_labels must be non-empty")
        return out
    fitted = getattr(result, "visit_labels", None)
    if fitted is None:
        raise ValueError(
            "visit_labels are required for detection newdata prediction when fit.visit_labels "
            "are unavailable"
        )
    out = list(fitted)
    if not out:
        raise ValueError("visit_labels must be non-empty")
    return out


def _default_obs_data(
    site_data: pd.DataFrame,
    *,
    site_ids: list[Any],
    site_id_col: str | None,
    visit_col: str,
    visit_labels: list[Any],
) -> pd.DataFrame:
    site_covs = site_data.reset_index(drop=True).copy()
    rows = []
    for site_index, site_id in enumerate(site_ids):
        base = site_covs.iloc[site_index].to_dict()
        base[_INTERNAL_SITE_INDEX] = site_index
        if site_id_col is not None:
            base[site_id_col] = site_id
        for visit in visit_labels:
            row = dict(base)
            row[visit_col] = visit
            rows.append(row)
    return pd.DataFrame(rows)


def _provided_obs_data(
    site_data: pd.DataFrame,
    obs_data: Any,
    *,
    site_ids: list[Any],
    site_id_col: str | None,
    visit_col: str,
    visit_labels: list[Any],
) -> pd.DataFrame:
    if not isinstance(obs_data, pd.DataFrame):
        raise ValueError("new_obs_data must be a pandas DataFrame")
    if site_id_col is None:
        raise ValueError(
            "site_id_col is required when new_obs_data is provided unless "
            "new_site_data contains a 'site_id' column"
        )
    if site_id_col not in site_data.columns:
        raise ValueError(f"new_site_data must contain site_id_col {site_id_col!r}")
    if site_id_col not in obs_data.columns:
        raise ValueError(f"new_obs_data must contain site_id_col {site_id_col!r}")
    if visit_col not in obs_data.columns:
        raise ValueError(f"new_obs_data must contain visit_col {visit_col!r}")
    if obs_data.duplicated([site_id_col, visit_col]).any():
        raise ValueError("new_obs_data must contain at most one row per site × visit")

    obs = obs_data.copy()
    unknown_sites = sorted(set(obs[site_id_col]) - set(site_ids))
    unknown_visits = sorted(set(obs[visit_col]) - set(visit_labels))
    if unknown_sites:
        raise ValueError(f"new_obs_data contains unknown sites: {unknown_sites}")
    if unknown_visits:
        raise ValueError(f"new_obs_data contains unknown visits: {unknown_visits}")

    expected = pd.MultiIndex.from_product([site_ids, visit_labels], names=[site_id_col, visit_col])
    obs_indexed = obs.set_index([site_id_col, visit_col])
    missing = expected.difference(obs_indexed.index)
    if len(missing):
        raise ValueError(f"new_obs_data is missing required site×visit rows: {list(missing)[:5]}")
    obs = obs_indexed.loc[expected].reset_index()

    site_order = {site_id: i for i, site_id in enumerate(site_ids)}
    obs[_INTERNAL_SITE_INDEX] = obs[site_id_col].map(site_order).astype(int)
    site_covs = site_data.reset_index(drop=True).copy()
    site_covs[_INTERNAL_SITE_INDEX] = range(len(site_covs))
    merge_cols = [
        col for col in site_covs.columns if col not in obs.columns or col == _INTERNAL_SITE_INDEX
    ]
    merged = obs.merge(site_covs[merge_cols], on=_INTERNAL_SITE_INDEX, how="left")
    visit_order = {visit: j for j, visit in enumerate(visit_labels)}
    merged["__visit_order__"] = merged[visit_col].map(visit_order).astype(int)
    merged = merged.sort_values([_INTERNAL_SITE_INDEX, "__visit_order__"]).drop(
        columns="__visit_order__"
    )
    return merged.reset_index(drop=True)


def _lambda_output(
    out: NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame,
    *,
    site_ids: list[Any],
    as_dataframe: bool,
) -> NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame:
    if not as_dataframe:
        return out
    if isinstance(out, pd.DataFrame):
        df = out.copy()
        if "site_id" not in df.columns:
            df.insert(0, "site_id", site_ids)
        else:
            df["site_id"] = site_ids
        return df
    if isinstance(out, dict):
        data: dict[str, Any] = {"site_id": site_ids}
        for key in ["estimate", "se", "lower", "upper"]:
            if key in out:
                data[key] = out[key]
        return pd.DataFrame(data)
    values = np.asarray(out, dtype=np.float64)
    return pd.DataFrame({"site_id": site_ids, "estimate": values})


def _detection_output(
    out: NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame,
    *,
    site_ids: list[Any],
    visit_labels: list[Any],
    as_dataframe: bool,
) -> NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame:
    if not as_dataframe:
        return out
    if isinstance(out, dict):
        return _array_dict_to_detection_dataframe(out, site_ids, visit_labels)
    if isinstance(out, pd.DataFrame):
        df = out.copy()
        rows = _site_visit_rows(site_ids, visit_labels)
        df["site_id"] = [row["site_id"] for row in rows]
        df["visit"] = [row["visit"] for row in rows]
        return df
    return _array_dict_to_detection_dataframe(
        {"estimate": np.asarray(out, dtype=np.float64)}, site_ids, visit_labels
    )


def _array_dict_to_detection_dataframe(
    values: dict[str, NDArray[np.float64]], site_ids: list[Any], visit_labels: list[Any]
) -> pd.DataFrame:
    rows = []
    for i, site_id in enumerate(site_ids):
        for j, visit in enumerate(visit_labels):
            row: dict[str, Any] = {"site_id": site_id, "visit": visit}
            for key in ["estimate", "se", "lower", "upper"]:
                if key in values:
                    row[key] = float(values[key][i, j])
            rows.append(row)
    return pd.DataFrame(rows)


def _fitted_dataframe(
    fitted: NDArray[np.float64], *, site_ids: list[Any], visit_labels: list[Any]
) -> pd.DataFrame:
    rows = []
    for i, site_id in enumerate(site_ids):
        for j, visit in enumerate(visit_labels):
            rows.append({"site_id": site_id, "visit": visit, "fitted": float(fitted[i, j])})
    return pd.DataFrame(rows)


def _site_visit_rows(site_ids: list[Any], visit_labels: list[Any]) -> list[dict[str, Any]]:
    return [
        {"site_id": site_id, "visit": visit}
        for site_id in site_ids
        for visit in visit_labels
    ]
