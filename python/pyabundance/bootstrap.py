from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def _simulate_from_fit(fit: Any, seed: int | None = None) -> NDArray[np.float64]:
    from pyabundance.simulate import simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip

    if fit.mixture == "poisson":
        return simulate_pcount(fit.X, fit.W, fit.beta, fit.detection, seed=seed)
    if fit.mixture == "negative_binomial":
        return simulate_pcount_negbin(fit.X, fit.W, fit.beta, fit.detection, fit.r, seed=seed)
    if fit.mixture == "zero_inflated_poisson":
        return simulate_pcount_zip(fit.X, fit.W, fit.beta, fit.detection, fit.psi, seed=seed)
    raise ValueError(f"unsupported mixture {fit.mixture!r}")


@dataclass(frozen=True)
class BootstrapResult:
    params: NDArray[np.float64]
    param_names: list[str]
    statistics: NDArray[np.float64] | None
    success: NDArray[np.bool_]
    messages: list[str]
    logliks: NDArray[np.float64]
    nsim: int
    seed: int | None
    mixture: str
    observed_statistic: float | None = None

    def confint(self, level: float = 0.95, method: str = "percentile") -> pd.DataFrame:
        if method != "percentile":
            raise ValueError("only percentile bootstrap intervals are implemented")
        alpha = 1.0 - level
        lower = np.nanpercentile(self.params, 100.0 * alpha / 2.0, axis=0)
        upper = np.nanpercentile(self.params, 100.0 * (1.0 - alpha / 2.0), axis=0)
        estimate = np.nanmedian(self.params, axis=0)
        return pd.DataFrame(
            {"parameter": self.param_names, "estimate": estimate, "lower": lower, "upper": upper}
        )

    def gof_pvalue(self, observed_statistic: float | None = None) -> float | None:
        if self.statistics is None:
            return None
        observed = self.observed_statistic if observed_statistic is None else observed_statistic
        if observed is None or not np.isfinite(observed):
            return None
        return float(np.mean(self.statistics >= observed))

    def summary(self) -> str:
        lines = [
            f"BootstrapResult(mixture='{self.mixture}', nsim={self.nsim})",
            f"successful refits: {int(np.sum(self.success))}/{self.nsim}",
        ]
        pvalue = self.gof_pvalue()
        if pvalue is not None:
            lines.append(f"GOF p-value: {pvalue:.6g}")
        return "\n".join(lines)


def parametric_bootstrap(
    fit: Any,
    nsim: int = 100,
    statistic: str | None = "sse",
    seed: int | None = None,
    refit: bool = True,
    start: str = "fit",
    n_jobs: int = 1,
    progress: bool = False,
) -> BootstrapResult:
    if n_jobs != 1:
        raise NotImplementedError("parallel bootstrap is not implemented in v0.5; use n_jobs=1")
    if callable(statistic):
        raise NotImplementedError("callable bootstrap statistics are not implemented in v0.5")
    if statistic not in {"sse", None}:
        raise ValueError("statistic must be 'sse' or None")
    if start not in {"fit", "zeros"}:
        raise ValueError("start must be 'fit' or 'zeros'")
    if nsim <= 0:
        raise ValueError("nsim must be positive")
    if not refit:
        raise NotImplementedError("refit=False is not implemented in v0.5")
    if progress:
        # Keep the implementation dependency-free and quiet by default.
        pass

    from pyabundance.pcount import pcount

    rng = np.random.default_rng(seed)
    param_samples = np.full((nsim, fit.params.size), np.nan, dtype=np.float64)
    logliks = np.full(nsim, np.nan, dtype=np.float64)
    stats = np.full(nsim, np.nan, dtype=np.float64) if statistic == "sse" else None
    success = np.zeros(nsim, dtype=bool)
    messages: list[str] = []
    start_values = fit.params if start == "fit" else None

    for i in range(nsim):
        sim_seed = int(rng.integers(0, np.iinfo(np.int32).max))
        y_sim = _simulate_from_fit(fit, seed=sim_seed)
        try:
            boot_fit = pcount(
                y_sim,
                fit.X,
                fit.W,
                K=fit.K,
                mixture=fit.mixture,
                start=start_values,
                method=fit.method,
                se=False,
            )
            param_samples[i, :] = boot_fit.params
            logliks[i] = boot_fit.loglik
            success[i] = bool(boot_fit.success)
            messages.append(boot_fit.message)
            if stats is not None:
                stats[i] = boot_fit.sse()
        except Exception as exc:  # pragma: no cover - rare optimizer failures are data dependent
            messages.append(str(exc))
    observed = fit.sse() if statistic == "sse" else None
    return BootstrapResult(
        params=param_samples,
        param_names=fit.param_names,
        statistics=stats,
        success=success,
        messages=messages,
        logliks=logliks,
        nsim=int(nsim),
        seed=seed,
        mixture=fit.mixture,
        observed_statistic=observed,
    )
