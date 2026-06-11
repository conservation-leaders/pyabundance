from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import minimize

from pyabundance import _core
from pyabundance.k_selection import KSuggestion, suggest_K
from pyabundance.result import MixtureName, PCountResult
from pyabundance.uncertainty import (
    covariance_diagnostics,
    extract_bfgs_covariance,
    finite_difference_hessian,
    safe_invert_hessian,
    standard_errors_from_covariance,
)

POISSON_ALIASES = {"poisson", "P"}
NEGBIN_ALIASES = {"negative_binomial", "negbin", "NB"}
ZIP_ALIASES = {"zero_inflated_poisson", "zip", "ZIP"}


def canonical_mixture(mixture: str) -> MixtureName:
    if mixture in POISSON_ALIASES:
        return "poisson"
    if mixture in NEGBIN_ALIASES:
        return "negative_binomial"
    if mixture in ZIP_ALIASES:
        return "zero_inflated_poisson"
    raise ValueError(
        "unknown mixture; supported values are 'poisson', 'P', "
        "'negative_binomial', 'negbin', 'NB', "
        "'zero_inflated_poisson', 'zip', and 'ZIP'"
    )


def _as_float_array(value: ArrayLike, name: str, ndim: int) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions, got {arr.ndim}")
    if not np.all(np.isfinite(arr) | np.isnan(arr)):
        raise ValueError(f"{name} must contain only finite values or NaN")
    return np.ascontiguousarray(arr, dtype=np.float64)


def validate_pcount_inputs(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    K: int,
    start: ArrayLike | None = None,
    *,
    mixture: str = "poisson",
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    y_arr = _as_float_array(y, "y", 2)
    x_arr = _as_float_array(X, "X", 2)
    w_arr = _as_float_array(W, "W", 3)
    if y_arr.shape[0] != x_arr.shape[0] or y_arr.shape[0] != w_arr.shape[0]:
        raise ValueError("y, X, and W must have the same number of sites")
    if y_arr.shape[1] != w_arr.shape[1]:
        raise ValueError("y and W must have the same number of visits")
    if K < 0:
        raise ValueError("K must be non-negative")
    observed = y_arr[~np.isnan(y_arr)]
    if np.any(observed < 0) or np.any(np.abs(observed - np.round(observed)) > 1.0e-12):
        raise ValueError("non-missing counts must be non-negative integers")
    if observed.size and np.max(observed) > K:
        raise ValueError(f"max observed count {np.max(observed):g} exceeds K {K}")
    canonical = canonical_mixture(mixture)
    n_params = x_arr.shape[1] + w_arr.shape[2]
    if canonical in {"negative_binomial", "zero_inflated_poisson"}:
        n_params += 1
    if start is None:
        start_arr = np.zeros(n_params, dtype=np.float64)
        if canonical == "zero_inflated_poisson":
            start_arr[-1] = np.log(0.2 / 0.8)
    else:
        start_arr = np.asarray(start, dtype=np.float64)
        if start_arr.ndim != 1 or start_arr.shape[0] != n_params:
            raise ValueError(f"start must be a vector of length {n_params}")
        if not np.all(np.isfinite(start_arr)):
            raise ValueError("start must contain only finite values")
        start_arr = np.ascontiguousarray(start_arr, dtype=np.float64)
    return y_arr, x_arr, w_arr, start_arr


def pcount_loglik(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    theta: ArrayLike,
    K: int,
) -> float:
    y_arr, x_arr, w_arr, _ = validate_pcount_inputs(y, X, W, K, theta, mixture="poisson")
    theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
    return float(_core.pcount_poisson_loglik(y_arr, x_arr, w_arr, theta_arr, int(K)))


def pcount_negbin_loglik(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    theta: ArrayLike,
    K: int,
) -> float:
    y_arr, x_arr, w_arr, _ = validate_pcount_inputs(y, X, W, K, theta, mixture="negative_binomial")
    theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
    return float(_core.pcount_negbin_loglik(y_arr, x_arr, w_arr, theta_arr, int(K)))


def pcount_zip_loglik(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    theta: ArrayLike,
    K: int,
) -> float:
    y_arr, x_arr, w_arr, _ = validate_pcount_inputs(
        y, X, W, K, theta, mixture="zero_inflated_poisson"
    )
    theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
    return float(_core.pcount_zip_loglik(y_arr, x_arr, w_arr, theta_arr, int(K)))


def pcount(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    K: int | str = 60,
    mixture: str = "poisson",
    start: ArrayLike | None = None,
    method: str = "BFGS",
    se: bool = False,
    *,
    cov_method: str | None = None,
    abundance_column_names: list[str] | None = None,
    detection_column_names: list[str] | None = None,
    site_ids: list[Any] | None = None,
    visit_labels: list[Any] | None = None,
    abundance_formula: str | None = None,
    detection_formula: str | None = None,
    from_dataframe: bool = False,
    data_info: dict[str, int] | None = None,
    K_info: KSuggestion | dict[str, Any] | None = None,
    visit_label_source: str | None = None,
    visit_label_message: str | None = None,
) -> PCountResult:
    """Fit a single-season N-mixture model using matrix/tensor inputs."""
    canonical = canonical_mixture(mixture)
    model_warnings: list[str] = []
    covariance_warnings: list[str] = []
    if isinstance(K, str):
        if K != "auto":
            raise ValueError("K must be an integer or 'auto'")
        K_suggestion = suggest_K(y, return_info=True)
        assert isinstance(K_suggestion, KSuggestion)
        K = K_suggestion.K
        K_info = K_suggestion
        model_warnings.append(K_suggestion.message)
    elif K_info is not None and hasattr(K_info, "message"):
        model_warnings.append(str(K_info.message))
    K_int = int(K)
    if cov_method is None:
        cov_method = "bfgs" if se else "none"
    if cov_method not in {"bfgs", "finite_difference", "none"}:
        raise ValueError("cov_method must be 'bfgs', 'finite_difference', or 'none'")
    if not se:
        cov_method = "none"
    y_arr, x_arr, w_arr, start_arr = validate_pcount_inputs(
        y, X, W, K_int, start, mixture=canonical
    )
    observed = y_arr[~np.isnan(y_arr)]
    if observed.size:
        max_observed = int(np.max(observed))
        if K_int - max_observed < 5:
            model_warnings.append(
                f"K={K_int} is close to the max observed count {max_observed}; "
                "consider a larger K and check sensitivity."
            )
    if canonical == "zero_inflated_poisson":
        model_warnings.append(
            "ZIP identifiability caution: many zeros can sometimes be explained by low "
            "abundance or low detection rather than structural zero inflation."
        )
    problem: Any
    if canonical == "poisson":
        problem = _core.PCountPoissonProblem(y_arr, x_arr, w_arr, K_int)
    elif canonical == "negative_binomial":
        problem = _core.PCountNegBinProblem(y_arr, x_arr, w_arr, K_int)
    else:
        problem = _core.PCountZIPProblem(y_arr, x_arr, w_arr, K_int)

    def objective(theta: NDArray[np.float64]) -> float:
        theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
        loglik = problem.loglik(theta_arr)
        if not np.isfinite(loglik):
            return np.inf
        return -float(loglik)

    minimize_options: dict[str, float | int] = {"maxiter": 1000}
    if method.upper() == "BFGS":
        minimize_options["gtol"] = 1.0e-3
    opt = minimize(objective, start_arr, method=method, options=minimize_options)
    params = np.asarray(opt.x, dtype=np.float64)
    loglik = -float(opt.fun) if np.isfinite(opt.fun) else float("nan")

    if not bool(opt.success):
        model_warnings.append(f"convergence warning: optimizer reported {opt.message}")
    covariance = None
    hessian = None
    pseudo_inverse_used = False
    if se and cov_method == "bfgs":
        covariance = extract_bfgs_covariance(opt, params.size)
        if covariance is None:
            covariance_warnings.append("BFGS inverse-Hessian covariance was unavailable")
    elif se and cov_method == "finite_difference":
        try:
            hessian = finite_difference_hessian(objective, params)
            covariance, pseudo_inverse_used, inversion_warnings = safe_invert_hessian(hessian)
            covariance_warnings.extend(inversion_warnings)
        except Exception as exc:
            covariance_warnings.append(f"finite-difference covariance failed: {exc}")
            covariance = None
    cov_diag = covariance_diagnostics(
        covariance,
        hessian,
        method=str(cov_method),
        pseudo_inverse_used=pseudo_inverse_used,
        warnings=covariance_warnings,
    )
    standard_errors = standard_errors_from_covariance(covariance, params.size)
    abundance_names = (
        abundance_column_names
        if abundance_column_names and len(abundance_column_names) == x_arr.shape[1]
        else [f"abundance[{i}]" for i in range(x_arr.shape[1])]
    )
    detection_names = (
        detection_column_names
        if detection_column_names and len(detection_column_names) == w_arr.shape[2]
        else [f"detection[{i}]" for i in range(w_arr.shape[2])]
    )
    param_names = list(abundance_names) + list(detection_names)
    if canonical == "negative_binomial":
        param_names.append("log_r")
    elif canonical == "zero_inflated_poisson":
        param_names.append("logit_psi")

    return PCountResult(
        params=params,
        n_abundance_params=x_arr.shape[1],
        n_detection_params=w_arr.shape[2],
        loglik=loglik,
        success=bool(opt.success),
        message=str(opt.message),
        K=K_int,
        mixture=canonical,
        X=x_arr,
        W=w_arr,
        method=method,
        nfev=int(opt.nfev) if getattr(opt, "nfev", None) is not None else None,
        nit=int(opt.nit) if getattr(opt, "nit", None) is not None else None,
        y=y_arr,
        abundance_column_names=abundance_column_names,
        detection_column_names=detection_column_names,
        site_ids=site_ids,
        visit_labels=visit_labels,
        abundance_formula=abundance_formula,
        detection_formula=detection_formula,
        from_dataframe=from_dataframe,
        data_info=data_info,
        K_info=K_info,
        visit_label_source=visit_label_source,
        visit_label_message=visit_label_message,
        covariance=covariance,
        standard_errors=standard_errors,
        cov_method=str(cov_method),
        covariance_diagnostics=cov_diag,
        param_names=param_names,
        warnings=model_warnings,
        objective_value=float(opt.fun) if np.isfinite(opt.fun) else None,
        _problem=problem,
    )
