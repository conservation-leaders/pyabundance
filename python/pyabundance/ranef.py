from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from pyabundance import _core


@dataclass(frozen=True)
class TotalAbundancePosterior:
    samples: NDArray[np.float64]
    mean: float
    median: float
    lower: float
    upper: float
    level: float
    nsim: int

    def summary(self) -> str:
        return (
            "TotalAbundancePosterior("
            f"mean={self.mean:.6g}, median={self.median:.6g}, "
            f"{self.level:.1%} interval=({self.lower:.6g}, {self.upper:.6g}), "
            f"nsim={self.nsim})"
        )


def _problem_for_fit(fit: Any) -> Any:
    problem = getattr(fit, "_problem", None)
    if problem is not None:
        return problem
    if fit.mixture == "poisson":
        return _core.PCountPoissonProblem(fit.y, fit.X, fit.W, fit.K)
    if fit.mixture == "negative_binomial":
        return _core.PCountNegBinProblem(fit.y, fit.X, fit.W, fit.K)
    if fit.mixture == "zero_inflated_poisson":
        return _core.PCountZIPProblem(fit.y, fit.X, fit.W, fit.K)
    raise ValueError(f"unsupported mixture {fit.mixture!r}")


def posterior_abundance_matrix(fit: Any) -> NDArray[np.float64]:
    probs = _problem_for_fit(fit).posterior_abundance(fit.params)
    return np.asarray(probs, dtype=np.float64)


def observed_max_counts(y: NDArray[np.float64]) -> NDArray[np.int64]:
    out = np.zeros(y.shape[0], dtype=np.int64)
    for i in range(y.shape[0]):
        observed = y[i][~np.isnan(y[i])]
        out[i] = int(np.max(observed)) if observed.size else 0
    return out


def posterior_abundance_summary(fit: Any, level: float = 0.95) -> pd.DataFrame:
    probs = fit.posterior_abundance()
    support = np.arange(fit.K + 1, dtype=np.float64)
    max_counts = observed_max_counts(fit.y)
    alpha = 1.0 - level
    cdf = np.cumsum(probs, axis=1)
    means = probs @ support
    variances = np.sum(((support[None, :] - means[:, None]) ** 2) * probs, axis=1)
    sds = np.sqrt(np.maximum(variances, 0.0))
    modes = np.argmax(probs, axis=1).astype(int)
    medians = np.argmax(cdf >= 0.5, axis=1).astype(int)
    lowers = np.argmax(cdf >= alpha / 2.0, axis=1).astype(int)
    uppers = np.argmax(cdf >= 1.0 - alpha / 2.0, axis=1).astype(int)
    rows = []
    site_ids = fit.site_ids if fit.site_ids is not None else [None] * fit.y.shape[0]
    for i in range(fit.y.shape[0]):
        max_y = int(max_counts[i])
        row: dict[str, Any] = {
            "site_index": i,
            "observed_max_count": max_y,
            "posterior_mean": float(means[i]),
            "posterior_mode": int(modes[i]),
            "posterior_median": int(medians[i]),
            "lower": int(lowers[i]),
            "upper": int(uppers[i]),
            "level": float(level),
            "posterior_sd": float(sds[i]),
            "pr_N_eq_observed_max": float(probs[i, max_y]),
            "pr_N_gt_observed_max": float(np.sum(probs[i, max_y + 1 :])),
            "pr_N_eq_0": float(probs[i, 0]),
            "pr_N_gt_0": float(1.0 - probs[i, 0]),
            "mixture": fit.mixture,
            "K": int(fit.K),
        }
        if site_ids[i] is not None:
            row["site_id"] = site_ids[i]
        rows.append(row)
    cols = ["site_index"]
    if any(site_id is not None for site_id in site_ids):
        cols.append("site_id")
    cols += [
        "observed_max_count",
        "posterior_mean",
        "posterior_mode",
        "posterior_median",
        "lower",
        "upper",
        "level",
        "posterior_sd",
        "pr_N_eq_observed_max",
        "pr_N_gt_observed_max",
        "pr_N_eq_0",
        "pr_N_gt_0",
        "mixture",
        "K",
    ]
    return pd.DataFrame(rows)[cols]


def posterior_abundance_long_dataframe(fit: Any) -> pd.DataFrame:
    probs = fit.posterior_abundance()
    site_ids = fit.site_ids if fit.site_ids is not None else [None] * probs.shape[0]
    rows = []
    for i in range(probs.shape[0]):
        for n in range(probs.shape[1]):
            row: dict[str, Any] = {"site_index": i, "N": n, "probability": float(probs[i, n])}
            if site_ids[i] is not None:
                row["site_id"] = site_ids[i]
            rows.append(row)
    return pd.DataFrame(rows)


def posterior_abundance_samples(
    fit: Any, nsim: int = 100, seed: int | None = None
) -> NDArray[np.int64]:
    if nsim <= 0:
        raise ValueError("nsim must be positive")
    rng = np.random.default_rng(seed)
    probs = fit.posterior_abundance()
    support = np.arange(fit.K + 1, dtype=np.int64)
    samples = np.empty((nsim, probs.shape[0]), dtype=np.int64)
    for site in range(probs.shape[0]):
        samples[:, site] = rng.choice(support, size=nsim, p=probs[site])
    return samples


def total_abundance_posterior(
    fit: Any, nsim: int = 1000, seed: int | None = None, level: float = 0.95
) -> TotalAbundancePosterior:
    samples = posterior_abundance_samples(fit, nsim=nsim, seed=seed).sum(axis=1).astype(float)
    alpha = 1.0 - level
    return TotalAbundancePosterior(
        samples=samples,
        mean=float(np.mean(samples)),
        median=float(np.median(samples)),
        lower=float(np.quantile(samples, alpha / 2.0)),
        upper=float(np.quantile(samples, 1.0 - alpha / 2.0)),
        level=float(level),
        nsim=int(nsim),
    )


def posterior_predictive_counts(
    fit: Any, nsim: int = 100, seed: int | None = None
) -> NDArray[np.float64]:
    if nsim <= 0:
        raise ValueError("nsim must be positive")
    rng = np.random.default_rng(seed)
    n_samples = posterior_abundance_samples(fit, nsim=nsim, seed=seed)
    p = np.asarray(fit.predict_detection(), dtype=np.float64)
    out = np.empty((nsim, fit.y.shape[0], fit.y.shape[1]), dtype=np.float64)
    for s in range(nsim):
        out[s] = rng.binomial(n_samples[s, :, None], p).astype(np.float64)
    return out


def _statistic_value(fit: Any, y: NDArray[np.float64], statistic: str) -> float:
    if statistic == "total_count":
        return float(np.nansum(y))
    if statistic == "zero_count":
        observed = y[~np.isnan(y)]
        return float(np.sum(observed == 0.0))
    if statistic == "max_count":
        observed = y[~np.isnan(y)]
        return float(np.max(observed)) if observed.size else 0.0
    if statistic == "sse":
        return float(np.nansum((y - fit.fitted_counts()) ** 2))
    raise ValueError("statistic must be 'sse', 'total_count', 'zero_count', or 'max_count'")


def posterior_predictive_check(
    fit: Any, statistic: str = "sse", nsim: int = 100, seed: int | None = None
) -> dict[str, Any]:
    sims = posterior_predictive_counts(fit, nsim=nsim, seed=seed)
    observed = _statistic_value(fit, fit.y, statistic)
    simulated = np.asarray([_statistic_value(fit, sims[i], statistic) for i in range(nsim)])
    return {
        "observed": observed,
        "simulated": simulated,
        "p_value": float(np.mean(simulated >= observed)),
        "nsim": int(nsim),
        "statistic": statistic,
        "note": "conditional on fitted parameters and posterior latent abundance draws",
    }
