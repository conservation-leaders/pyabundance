from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import minimize

from pyabundance import _core
from pyabundance.result import PCountResult


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
    n_params = x_arr.shape[1] + w_arr.shape[2]
    if start is None:
        start_arr = np.zeros(n_params, dtype=np.float64)
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
    y_arr, x_arr, w_arr, _ = validate_pcount_inputs(y, X, W, K, theta)
    theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
    return float(_core.pcount_poisson_loglik(y_arr, x_arr, w_arr, theta_arr, int(K)))


def pcount(
    y: ArrayLike,
    X: ArrayLike,
    W: ArrayLike,
    K: int = 60,
    mixture: Literal["poisson"] = "poisson",
    start: ArrayLike | None = None,
    method: str = "BFGS",
    se: bool = False,
) -> PCountResult:
    """Fit a single-season Poisson N-mixture model using matrix/tensor inputs."""
    if mixture != "poisson":
        raise NotImplementedError("v0.1 implements only mixture='poisson'")
    if se:
        raise NotImplementedError("standard errors are not implemented in v0.1")
    y_arr, x_arr, w_arr, start_arr = validate_pcount_inputs(y, X, W, K, start)
    problem = _core.PCountPoissonProblem(y_arr, x_arr, w_arr, int(K))

    def objective(theta: NDArray[np.float64]) -> float:
        theta_arr = np.ascontiguousarray(theta, dtype=np.float64)
        loglik = problem.loglik(theta_arr)
        if not np.isfinite(loglik):
            return np.inf
        return -float(loglik)

    minimize_options = {"maxiter": 1000}
    if method.upper() == "BFGS":
        # Numerical finite-difference BFGS can report precision loss after reaching a stable
        # ecological MLE. A moderate gradient tolerance avoids false non-convergence for v0.1.
        minimize_options["gtol"] = 1.0e-3
    opt = minimize(objective, start_arr, method=method, options=minimize_options)
    params = np.asarray(opt.x, dtype=np.float64)
    loglik = -float(opt.fun) if np.isfinite(opt.fun) else float("nan")
    return PCountResult(
        params=params,
        n_abundance_params=x_arr.shape[1],
        loglik=loglik,
        success=bool(opt.success),
        message=str(opt.message),
        K=int(K),
        mixture=mixture,
        X=x_arr,
        W=w_arr,
        method=method,
        nfev=int(opt.nfev) if getattr(opt, "nfev", None) is not None else None,
        nit=int(opt.nit) if getattr(opt, "nit", None) is not None else None,
    )
