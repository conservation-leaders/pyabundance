from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Integral
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from pyabundance.result import PCountResult

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


@dataclass(frozen=True)
class KSuggestion:
    """Metadata describing an automatically selected upper integration limit ``K``."""

    K: int
    max_observed: int
    minimum_buffer: int
    multiplier: float
    message: str

    def __int__(self) -> int:
        return self.K


@dataclass(frozen=True)
class PCountKSensitivityResult:
    """Result from refitting one pcount specification across candidate ``K`` values.

    The helper is intentionally pcount-specific. Rows are sorted by increasing
    ``K`` for deterministic comparison, and ``fits`` is keyed by the same integer
    ``K`` values shown in ``table``.
    """

    table: pd.DataFrame
    fits: dict[int, PCountResult]
    reference_fit: PCountResult
    best_K: int | None

    @property
    def best_fit(self) -> PCountResult | None:
        """Return the lowest-AIC refit, or ``None`` when no finite AIC exists."""

        if self.best_K is None:
            return None
        return self.fits[self.best_K]

    def summary(self) -> str:
        """Return a concise text summary of K-sensitivity results."""

        lines = [
            "PCountKSensitivityResult",
            f"reference K: {self.reference_fit.K}",
            f"candidate Ks: {list(self.table['K'].astype(int))}",
            f"best K: {self.best_K}",
        ]
        display_cols = [
            col
            for col in ["K", "AIC", "delta_AIC", "logLik", "success", "max_abs_param_delta"]
            if col in self.table.columns
        ]
        if display_cols:
            lines.append(self.table[display_cols].to_string(index=False))
        return "\n".join(lines)


def suggest_K(
    y: Any,
    *,
    minimum_buffer: int = 50,
    multiplier: float = 3.0,
    min_K: int | None = None,
    max_K: int | None = None,
    return_info: bool = False,
) -> int | KSuggestion:
    """Suggest a conservative ``K`` for pcount-style N-mixture fitting.

    Missing counts are ignored. Non-missing counts must be non-negative integers.
    By default an integer is returned; use ``return_info=True`` for explanatory metadata.
    """

    if minimum_buffer < 0:
        raise ValueError("minimum_buffer must be non-negative")
    if multiplier < 1.0:
        raise ValueError("multiplier must be at least 1.0")
    if min_K is not None and min_K < 0:
        raise ValueError("min_K must be non-negative")
    if max_K is not None and max_K < 0:
        raise ValueError("max_K must be non-negative")

    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        max_observed = 0
    else:
        observed = arr[~np.isnan(arr)]
        if np.any(~np.isfinite(observed)):
            raise ValueError("counts must be finite or NaN")
        if np.any(observed < 0) or np.any(np.abs(observed - np.round(observed)) > 1.0e-12):
            raise ValueError("non-missing counts must be non-negative integers")
        max_observed = int(np.max(observed)) if observed.size else 0

    buffered = int(max_observed + minimum_buffer)
    multiplied = int(np.ceil(max_observed * multiplier))
    K = max(buffered, multiplied)
    if min_K is not None:
        K = max(K, int(min_K))
    if max_K is not None and K > int(max_K):
        raise ValueError(
            f"suggested K {K} exceeds max_K {int(max_K)}; increase max_K or choose K explicitly"
        )
    message = (
        f"Auto-selected K={K} from max observed count {max_observed} "
        f"using max(max_count + {minimum_buffer}, ceil(max_count * {multiplier:g}))."
    )
    info = KSuggestion(
        K=int(K),
        max_observed=max_observed,
        minimum_buffer=int(minimum_buffer),
        multiplier=float(multiplier),
        message=message,
    )
    return info if return_info else info.K


def _coerce_k_value(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} values must be integers")
    return int(value)


def _candidate_Ks(
    Ks: Sequence[int] | None,
    *,
    min_K: int | None,
    max_K: int | None,
    step: int,
) -> list[int]:
    if Ks is not None:
        if min_K is not None or max_K is not None:
            raise ValueError("pass either explicit Ks or min_K/max_K, not both")
        values = [_coerce_k_value(value, "K") for value in Ks]
    else:
        if min_K is None or max_K is None:
            raise ValueError("provide non-empty Ks or both min_K and max_K")
        min_value = _coerce_k_value(min_K, "min_K")
        max_value = _coerce_k_value(max_K, "max_K")
        step_value = _coerce_k_value(step, "step")
        if step_value <= 0:
            raise ValueError("step must be a positive integer")
        if min_value > max_value:
            raise ValueError("min_K must be less than or equal to max_K")
        values = list(range(min_value, max_value + 1, step_value))

    if not values:
        raise ValueError("Ks must contain at least one candidate K")
    seen: set[int] = set()
    duplicates: list[int] = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        duplicate_text = ", ".join(str(value) for value in sorted(set(duplicates)))
        raise ValueError(f"duplicate K values are not allowed: {duplicate_text}")
    return sorted(values)


def _max_observed_count(y: Any) -> int:
    arr = np.asarray(y, dtype=np.float64)
    observed = arr[~np.isnan(arr)]
    if np.any(~np.isfinite(observed)):
        raise ValueError("reference fit counts must be finite or NaN")
    return int(np.max(observed)) if observed.size else 0


def _copy_list(value: list[Any] | None) -> list[Any] | None:
    return None if value is None else list(value)


def _copy_dict(value: dict[str, int] | None) -> dict[str, int] | None:
    return None if value is None else dict(value)


def pcount_k_sensitivity(
    reference_fit: PCountResult,
    Ks: Sequence[int] | None = None,
    *,
    min_K: int | None = None,
    max_K: int | None = None,
    step: int = 1,
    start: ArrayLike | None = None,
    method: str | None = None,
    se: bool = False,
    cov_method: str | None = None,
) -> PCountKSensitivityResult:
    """Refit an existing pcount specification across candidate ``K`` values.

    Parameters
    ----------
    reference_fit:
        Existing :class:`pyabundance.result.PCountResult` whose pcount data,
        mixture, formulas, matrix columns, site IDs, and visit labels should be
        reused for refits.
    Ks:
        Explicit candidate ``K`` values. Values are sorted by increasing ``K``
        for deterministic output. Duplicate values are rejected.
    min_K, max_K, step:
        Optional convenience generation for inclusive ``range(min_K, max_K + 1,
        step)`` when ``Ks`` is not supplied.
    start:
        Optional optimizer start vector for every refit. By default, the
        reference fit's parameter vector is copied and reused when compatible.
    method:
        Optimizer method. Defaults to ``reference_fit.method``.
    se, cov_method:
        Passed through to :func:`pyabundance.pcount.pcount`. Standard errors are
        off by default to keep sensitivity checks lightweight.

    Returns
    -------
    PCountKSensitivityResult
        A compact object with a summary table, integer-``K`` keyed refit mapping,
        the original reference fit, and lowest-AIC convenience accessors.

    Notes
    -----
    This helper is pcount-specific and delegates all numerical fitting to the
    existing :func:`pyabundance.pcount.pcount` implementation. It does not change
    likelihood math, Rust likelihood formulas, or Rust likelihood hot paths.
    """

    if not isinstance(reference_fit, PCountResult):
        raise TypeError("reference_fit must be a PCountResult from a pcount fit")

    candidate_values = _candidate_Ks(Ks, min_K=min_K, max_K=max_K, step=step)
    max_observed = _max_observed_count(reference_fit.y)
    below_observed = [value for value in candidate_values if value < max_observed]
    if below_observed:
        raise ValueError(
            f"candidate K values must be >= max observed count {max_observed}; "
            f"invalid values: {below_observed}"
        )

    from pyabundance.pcount import pcount

    start_values = np.asarray(
        reference_fit.params if start is None else start,
        dtype=np.float64,
    ).copy()
    refit_method = reference_fit.method if method is None else method
    fits: dict[int, PCountResult] = {}
    rows: list[dict[str, Any]] = []
    for K in candidate_values:
        fit = pcount(
            reference_fit.y,
            reference_fit.X,
            reference_fit.W,
            K=K,
            mixture=reference_fit.mixture,
            start=start_values,
            method=refit_method,
            se=se,
            cov_method=cov_method,
            abundance_column_names=_copy_list(reference_fit.abundance_column_names),
            detection_column_names=_copy_list(reference_fit.detection_column_names),
            site_ids=_copy_list(reference_fit.site_ids),
            visit_labels=_copy_list(reference_fit.visit_labels),
            abundance_formula=reference_fit.abundance_formula,
            detection_formula=reference_fit.detection_formula,
            from_dataframe=reference_fit.from_dataframe,
            data_info=_copy_dict(reference_fit.data_info),
            visit_label_source=reference_fit.visit_label_source,
            visit_label_message=reference_fit.visit_label_message,
        )
        fits[K] = fit
        if fit.params.shape == reference_fit.params.shape:
            max_abs_param_delta = float(np.max(np.abs(fit.params - reference_fit.params)))
        else:  # pragma: no cover - pcount refits preserve parameter length
            max_abs_param_delta = float("nan")
        rows.append(
            {
                "K": int(K),
                "logLik": float(fit.loglik),
                "AIC": float(fit.aic),
                "delta_AIC": float("nan"),
                "n_params": int(fit.params.size),
                "success": bool(fit.success),
                "message": str(fit.message),
                "nfev": fit.nfev,
                "nit": fit.nit,
                "max_abs_param_delta": max_abs_param_delta,
            }
        )

    table = pd.DataFrame(rows)
    finite_aic = table["AIC"].replace([np.inf, -np.inf], np.nan).dropna()
    best_K: int | None = None
    if not finite_aic.empty:
        min_aic = float(finite_aic.min())
        table["delta_AIC"] = table["AIC"] - min_aic
        best_rows = table.loc[table["AIC"] == min_aic, "K"]
        best_K = int(best_rows.iloc[0])
    return PCountKSensitivityResult(
        table=table,
        fits=fits,
        reference_fit=reference_fit,
        best_K=best_K,
    )
