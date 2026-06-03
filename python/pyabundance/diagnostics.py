from __future__ import annotations

from typing import Any

import numpy as np


def result_diagnostics(fit: Any) -> dict[str, Any]:
    warnings = list(fit.warnings)
    cov_diag = fit.covariance_diagnostics or {}
    if not fit.success:
        warnings.append(f"optimizer failed: {fit.message}")
    if fit.standard_errors is not None and np.any(~np.isfinite(fit.standard_errors)):
        warnings.append("one or more standard errors are non-finite")
    if fit.cov_method != "none" and not cov_diag.get("available", False):
        warnings.append("covariance is unavailable")
    y = fit.y
    observed = y[~np.isnan(y)]
    zero_prop = float(np.mean(observed == 0.0)) if observed.size else float("nan")
    return {
        "success": fit.success,
        "message": fit.message,
        "nfev": fit.nfev,
        "nit": fit.nit,
        "loglik": fit.loglik,
        "aic": fit.aic,
        "K": fit.K,
        "mixture": fit.mixture,
        "n_sites": int(fit.X.shape[0]),
        "n_visits": int(fit.W.shape[1]),
        "n_params": int(fit.params.size),
        "covariance_available": bool(cov_diag.get("available", False)),
        "covariance_method": fit.cov_method,
        "covariance_condition_number": cov_diag.get("condition_number"),
        "covariance_warnings": list(cov_diag.get("warnings", [])),
        "nonfinite_standard_errors": int(np.sum(~np.isfinite(fit.standard_errors)))
        if fit.standard_errors is not None
        else fit.params.size,
        "residual_sse": fit.sse(),
        "observed_zero_proportion": zero_prop,
        "warnings": warnings,
    }
