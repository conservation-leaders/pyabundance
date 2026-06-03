from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def extract_bfgs_covariance(optimize_result: Any, n_params: int) -> NDArray[np.float64] | None:
    """Extract SciPy's BFGS inverse-Hessian approximation as a covariance matrix."""
    hess_inv = getattr(optimize_result, "hess_inv", None)
    if hess_inv is None:
        return None
    try:
        if hasattr(hess_inv, "todense"):
            cov = np.asarray(hess_inv.todense(), dtype=np.float64)
        elif hasattr(hess_inv, "toarray"):
            cov = np.asarray(hess_inv.toarray(), dtype=np.float64)
        else:
            cov = np.asarray(hess_inv, dtype=np.float64)
    except Exception:
        return None
    if cov.shape != (n_params, n_params):
        return None
    return 0.5 * (cov + cov.T)


def finite_difference_hessian(
    objective,
    theta: NDArray[np.float64],
    rel_step: float = 1.0e-4,
    abs_step: float = 1.0e-5,
) -> NDArray[np.float64]:
    """Central finite-difference Hessian of a scalar objective."""
    theta = np.asarray(theta, dtype=np.float64)
    n_params = theta.size
    steps = np.maximum(abs_step, rel_step * np.maximum(1.0, np.abs(theta)))
    hessian = np.empty((n_params, n_params), dtype=np.float64)
    f0 = float(objective(theta))
    if not np.isfinite(f0):
        raise ValueError("objective is non-finite at optimum")

    for i in range(n_params):
        ei = np.zeros(n_params, dtype=np.float64)
        ei[i] = steps[i]
        f_plus = float(objective(theta + ei))
        f_minus = float(objective(theta - ei))
        hessian[i, i] = (f_plus - 2.0 * f0 + f_minus) / (steps[i] ** 2)
        for j in range(i + 1, n_params):
            ej = np.zeros(n_params, dtype=np.float64)
            ej[j] = steps[j]
            f_pp = float(objective(theta + ei + ej))
            f_pm = float(objective(theta + ei - ej))
            f_mp = float(objective(theta - ei + ej))
            f_mm = float(objective(theta - ei - ej))
            value = (f_pp - f_pm - f_mp + f_mm) / (4.0 * steps[i] * steps[j])
            hessian[i, j] = value
            hessian[j, i] = value
    return 0.5 * (hessian + hessian.T)


def safe_invert_hessian(
    hessian: NDArray[np.float64], rcond: float = 1.0e-10
) -> tuple[NDArray[np.float64] | None, bool, list[str]]:
    """Invert a Hessian, falling back to pseudo-inverse when needed."""
    warnings: list[str] = []
    hessian = np.asarray(hessian, dtype=np.float64)
    if hessian.ndim != 2 or hessian.shape[0] != hessian.shape[1]:
        return None, False, ["hessian is not square"]
    if not np.all(np.isfinite(hessian)):
        return None, False, ["hessian contains non-finite values"]
    hessian = 0.5 * (hessian + hessian.T)
    try:
        eigvals = np.linalg.eigvalsh(hessian)
        if np.min(eigvals) <= 0.0:
            warnings.append("hessian is not positive definite")
    except Exception:
        eigvals = None
        warnings.append("hessian eigenvalues could not be computed")
    try:
        cov = np.linalg.inv(hessian)
        pseudo_inverse_used = False
    except np.linalg.LinAlgError:
        cov = np.linalg.pinv(hessian, rcond=rcond)
        pseudo_inverse_used = True
        warnings.append("hessian was singular; pseudo-inverse used")
    if eigvals is not None:
        try:
            cond = np.linalg.cond(hessian)
            if not np.isfinite(cond) or cond > 1.0 / rcond:
                warnings.append("hessian is ill-conditioned")
        except Exception:
            warnings.append("hessian condition number could not be computed")
    return 0.5 * (cov + cov.T), pseudo_inverse_used, warnings


def covariance_diagnostics(
    covariance: NDArray[np.float64] | None,
    hessian: NDArray[np.float64] | None = None,
    *,
    method: str = "none",
    pseudo_inverse_used: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Return conservative diagnostics for a covariance estimate."""
    warn = list(warnings or [])
    diag: dict[str, Any] = {
        "available": covariance is not None,
        "method": method,
        "finite": False,
        "symmetric": False,
        "positive_diagonal": False,
        "minimum_eigenvalue": None,
        "maximum_eigenvalue": None,
        "condition_number": None,
        "pseudo_inverse_used": bool(pseudo_inverse_used),
        "warnings": warn,
    }
    if covariance is None:
        warn.append("covariance is unavailable")
        return diag
    cov = np.asarray(covariance, dtype=np.float64)
    diag["finite"] = bool(np.all(np.isfinite(cov)))
    diag["symmetric"] = bool(cov.ndim == 2 and np.allclose(cov, cov.T, rtol=1.0e-7, atol=1.0e-9))
    if cov.ndim == 2 and cov.shape[0] == cov.shape[1]:
        diagonal = np.diag(cov)
        diag["positive_diagonal"] = bool(np.all(diagonal > 0.0))
        if not diag["positive_diagonal"]:
            warn.append("covariance has non-positive diagonal entries")
        try:
            eigvals = np.linalg.eigvalsh(0.5 * (cov + cov.T))
            diag["minimum_eigenvalue"] = float(np.min(eigvals))
            diag["maximum_eigenvalue"] = float(np.max(eigvals))
            if np.min(eigvals) <= 0.0:
                warn.append("covariance is not positive definite")
        except Exception:
            warn.append("covariance eigenvalues could not be computed")
        try:
            cond = np.linalg.cond(cov)
            diag["condition_number"] = float(cond)
            if not np.isfinite(cond):
                warn.append("covariance condition number is non-finite")
        except Exception:
            warn.append("covariance condition number could not be computed")
    else:
        warn.append("covariance is not a square matrix")
    if hessian is not None and not np.all(np.isfinite(hessian)):
        warn.append("hessian contains non-finite values")
    return diag


def standard_errors_from_covariance(
    covariance: NDArray[np.float64] | None, n_params: int
) -> NDArray[np.float64]:
    if covariance is None:
        return np.full(n_params, np.nan, dtype=np.float64)
    diag = np.diag(np.asarray(covariance, dtype=np.float64))
    se = np.full(n_params, np.nan, dtype=np.float64)
    valid = np.isfinite(diag) & (diag >= 0.0)
    se[valid] = np.sqrt(diag[valid])
    return se
