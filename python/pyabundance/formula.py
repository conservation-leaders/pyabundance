from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from formulaic import Formula, model_matrix
from numpy.typing import NDArray

from pyabundance.pcount import pcount

_INTERNAL_SITE_INDEX = "__pyabundance_site_index__"


@dataclass(frozen=True)
class PCountMatrices:
    """Design matrices and metadata produced by the DataFrame/formula API."""

    y: NDArray[np.float64]
    X: NDArray[np.float64]
    W: NDArray[np.float64]
    abundance_column_names: list[str]
    detection_column_names: list[str]
    site_ids: list[Any]
    visit_labels: list[Any]
    site_data_used: pd.DataFrame
    obs_data_used: pd.DataFrame

    @property
    def data_info(self) -> dict[str, int]:
        return {
            "n_sites": int(self.y.shape[0]),
            "n_visits": int(self.y.shape[1]),
            "n_abundance_params": int(self.X.shape[1]),
            "n_detection_params": int(self.W.shape[2]),
        }


def _validate_formula(formula: str, name: str) -> str:
    if not isinstance(formula, str) or not formula.strip():
        raise ValueError(f"{name} must be a non-empty RHS-only formula string")
    formula = formula.strip()
    if "~" not in formula:
        raise ValueError(f"{name} must be RHS-only and start with '~'")
    lhs, rhs = formula.split("~", 1)
    if lhs.strip():
        raise ValueError(f"{name} must be RHS-only; response-side formulas are not supported")
    unsupported_tokens = ["|", "offset(", "bs(", "cs(", "cr(", "s(", "."]
    for token in unsupported_tokens:
        if token in rhs:
            raise ValueError(
                f"{name} uses unsupported formula feature {token!r}; v0.4 supports "
                "fixed-effect RHS formulas such as '~ x', '~ visit - 1', '~ x:visit', "
                "and '~ x * visit'"
            )
    return formula


def _formula_variables(formula: str) -> set[str]:
    try:
        return {str(var) for var in Formula(formula).required_variables}
    except Exception:
        return set()


def _require_dataframe(value: Any, name: str) -> pd.DataFrame:
    if not isinstance(value, pd.DataFrame):
        raise ValueError(f"{name} must be a pandas DataFrame")
    return value.copy()


def _as_list(value: Any, name: str) -> list[Any]:
    if isinstance(value, str) or not hasattr(value, "__iter__"):
        raise ValueError(f"{name} must be a non-empty list-like object")
    out = list(value)
    if not out:
        raise ValueError(f"{name} must be non-empty")
    return out


def _validate_counts(site_data: pd.DataFrame, count_cols: list[Any]) -> NDArray[np.float64]:
    missing = [col for col in count_cols if col not in site_data.columns]
    if missing:
        raise ValueError(f"missing count columns in site_data: {missing}")
    y = site_data[count_cols].to_numpy(dtype=np.float64)
    observed = y[~np.isnan(y)]
    if np.any(~np.isfinite(observed)):
        raise ValueError("counts must be finite or NaN")
    if np.any(observed < 0) or np.any(np.abs(observed - np.round(observed)) > 1.0e-12):
        raise ValueError("non-missing counts must be non-negative integers")
    return np.ascontiguousarray(y, dtype=np.float64)


def _build_model_matrix(
    formula: str, data: pd.DataFrame, name: str
) -> tuple[NDArray[np.float64], list[str]]:
    try:
        matrix = model_matrix(formula, data, na_action="raise")
    except Exception as exc:
        raise ValueError(f"failed to build {name} design matrix: {exc}") from exc
    columns = [str(col) for col in matrix.columns]
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"{name} design matrix must be 2D")
    if not np.all(np.isfinite(arr)):
        raise ValueError(
            f"{name} design matrix contains missing or non-finite values; "
            "fix covariates or use drop_missing_sites=True for site-level missing covariates"
        )
    return np.ascontiguousarray(arr, dtype=np.float64), columns


def _default_obs_data(
    site_data: pd.DataFrame,
    *,
    count_cols: list[Any],
    site_ids: list[Any],
    site_id_col: str | None,
    visit_col: str,
    visit_labels: list[Any],
) -> pd.DataFrame:
    site_covs = site_data.drop(columns=count_cols, errors="ignore").reset_index(drop=True)
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
    obs_data: pd.DataFrame,
    *,
    count_cols: list[Any],
    site_id_col: str | None,
    visit_col: str,
    visit_labels: list[Any],
    site_ids: list[Any],
) -> pd.DataFrame:
    if site_id_col is None:
        raise ValueError("site_id_col is required when obs_data is provided")
    if site_id_col not in obs_data.columns:
        raise ValueError(f"obs_data must contain site_id_col {site_id_col!r}")
    if visit_col not in obs_data.columns:
        raise ValueError(f"obs_data must contain visit_col {visit_col!r}")
    if obs_data.duplicated([site_id_col, visit_col]).any():
        raise ValueError("obs_data must contain at most one row per site × visit")

    obs = obs_data.copy()
    site_order = {site_id: i for i, site_id in enumerate(site_ids)}
    visit_order = {visit: j for j, visit in enumerate(visit_labels)}
    unknown_sites = sorted(set(obs[site_id_col]) - set(site_ids))
    unknown_visits = sorted(set(obs[visit_col]) - set(visit_labels))
    if unknown_sites:
        raise ValueError(f"obs_data contains site IDs not present in site_data: {unknown_sites}")
    if unknown_visits:
        raise ValueError(
            f"obs_data contains visits not present in visit_labels/count_cols: {unknown_visits}"
        )

    expected = pd.MultiIndex.from_product([site_ids, visit_labels], names=[site_id_col, visit_col])
    obs_indexed = obs.set_index([site_id_col, visit_col])
    missing = expected.difference(obs_indexed.index)
    if len(missing):
        raise ValueError(f"obs_data is missing required site×visit rows: {list(missing)[:5]}")
    obs = obs_indexed.loc[expected].reset_index()
    obs[_INTERNAL_SITE_INDEX] = obs[site_id_col].map(site_order).astype(int)

    site_covs = site_data.drop(columns=count_cols, errors="ignore").copy()
    site_covs[_INTERNAL_SITE_INDEX] = range(len(site_covs))
    merge_cols = [
        col for col in site_covs.columns if col not in obs.columns or col == _INTERNAL_SITE_INDEX
    ]
    merged = obs.merge(site_covs[merge_cols], on=_INTERNAL_SITE_INDEX, how="left")
    merged["__visit_order__"] = merged[visit_col].map(visit_order).astype(int)
    merged = merged.sort_values([_INTERNAL_SITE_INDEX, "__visit_order__"]).drop(
        columns="__visit_order__"
    )
    return merged.reset_index(drop=True)


def build_pcount_matrices(
    *,
    site_data: pd.DataFrame,
    count_cols: list[str],
    abundance_formula: str = "~ 1",
    detection_formula: str = "~ 1",
    obs_data: pd.DataFrame | None = None,
    site_id_col: str | None = None,
    visit_col: str = "visit",
    visit_labels: list[Any] | None = None,
    drop_missing_sites: bool = False,
) -> PCountMatrices:
    """Build matrix/tensor inputs for ``pcount`` from pandas data and formulas."""

    site_df = _require_dataframe(site_data, "site_data")
    count_cols_list = _as_list(count_cols, "count_cols")
    abundance_formula = _validate_formula(abundance_formula, "abundance_formula")
    detection_formula = _validate_formula(detection_formula, "detection_formula")
    if visit_labels is None:
        visit_labels_list = list(count_cols_list)
    else:
        visit_labels_list = _as_list(visit_labels, "visit_labels")
        if len(visit_labels_list) != len(count_cols_list):
            raise ValueError("visit_labels must have the same length as count_cols")
    if site_id_col is not None and site_id_col not in site_df.columns:
        raise ValueError(f"site_data must contain site_id_col {site_id_col!r}")

    if drop_missing_sites:
        before = len(site_df)
        formula_vars = _formula_variables(abundance_formula) | _formula_variables(detection_formula)
        formula_cols = [
            col
            for col in formula_vars
            if col in site_df.columns and col not in count_cols_list and col != visit_col
        ]
        if formula_cols:
            site_df = site_df.dropna(subset=formula_cols).reset_index(drop=True)
        if len(site_df) == 0 and before > 0:
            raise ValueError("drop_missing_sites=True dropped all sites")

    y = _validate_counts(site_df, count_cols_list)
    site_ids = (
        site_df[site_id_col].tolist() if site_id_col is not None else list(range(len(site_df)))
    )

    X, abundance_names = _build_model_matrix(abundance_formula, site_df, "abundance")
    if obs_data is None:
        obs_df = _default_obs_data(
            site_df,
            count_cols=count_cols_list,
            site_ids=site_ids,
            site_id_col=site_id_col,
            visit_col=visit_col,
            visit_labels=visit_labels_list,
        )
    else:
        obs_df = _provided_obs_data(
            site_df,
            _require_dataframe(obs_data, "obs_data"),
            count_cols=count_cols_list,
            site_id_col=site_id_col,
            visit_col=visit_col,
            visit_labels=visit_labels_list,
            site_ids=site_ids,
        )
    obs_df[visit_col] = pd.Categorical(
        obs_df[visit_col], categories=visit_labels_list, ordered=True
    )
    W_flat, detection_names = _build_model_matrix(detection_formula, obs_df, "detection")
    n_sites = y.shape[0]
    n_visits = y.shape[1]
    if W_flat.shape[0] != n_sites * n_visits:
        raise ValueError("detection design does not have one row per site × visit")
    W = np.ascontiguousarray(W_flat.reshape(n_sites, n_visits, W_flat.shape[1]), dtype=np.float64)
    return PCountMatrices(
        y=y,
        X=X,
        W=W,
        abundance_column_names=abundance_names,
        detection_column_names=detection_names,
        site_ids=site_ids,
        visit_labels=visit_labels_list,
        site_data_used=site_df.reset_index(drop=True),
        obs_data_used=obs_df.reset_index(drop=True),
    )


def pcount_df(
    *,
    site_data: pd.DataFrame,
    count_cols: list[str],
    abundance_formula: str = "~ 1",
    detection_formula: str = "~ 1",
    obs_data: pd.DataFrame | None = None,
    site_id_col: str | None = None,
    visit_col: str = "visit",
    visit_labels: list[Any] | None = None,
    mixture: str = "poisson",
    K: int | None = None,
    start: Any = None,
    method: str = "BFGS",
    se: bool = False,
    cov_method: str | None = None,
    drop_missing_sites: bool = False,
):
    """Fit a pcount model from pandas site/observation data and RHS formulas."""

    matrices = build_pcount_matrices(
        site_data=site_data,
        count_cols=count_cols,
        abundance_formula=abundance_formula,
        detection_formula=detection_formula,
        obs_data=obs_data,
        site_id_col=site_id_col,
        visit_col=visit_col,
        visit_labels=visit_labels,
        drop_missing_sites=drop_missing_sites,
    )
    if K is None:
        observed = matrices.y[~np.isnan(matrices.y)]
        max_count = int(np.max(observed)) if observed.size else 0
        K = max(60, max_count + 20)
    fit = pcount(
        matrices.y,
        matrices.X,
        matrices.W,
        K=int(K),
        mixture=mixture,
        start=start,
        method=method,
        se=se,
        cov_method=cov_method,
        abundance_column_names=matrices.abundance_column_names,
        detection_column_names=matrices.detection_column_names,
        site_ids=matrices.site_ids,
        visit_labels=matrices.visit_labels,
        abundance_formula=abundance_formula,
        detection_formula=detection_formula,
        from_dataframe=True,
        data_info=matrices.data_info,
    )
    return fit
