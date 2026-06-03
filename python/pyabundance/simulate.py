from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _logistic(x: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def _design_values(
    X: ArrayLike, W: ArrayLike, beta: ArrayLike, detection: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    x_arr = np.asarray(X, dtype=np.float64)
    w_arr = np.asarray(W, dtype=np.float64)
    beta_arr = np.asarray(beta, dtype=np.float64)
    detection_arr = np.asarray(detection, dtype=np.float64)
    if x_arr.ndim != 2 or w_arr.ndim != 3:
        raise ValueError("X must be 2D and W must be 3D")
    if x_arr.shape[0] != w_arr.shape[0]:
        raise ValueError("X and W must have the same number of sites")
    if x_arr.shape[1] != beta_arr.size or w_arr.shape[2] != detection_arr.size:
        raise ValueError("design matrices and parameter vectors have incompatible shapes")
    lam = np.exp(x_arr @ beta_arr)
    det = _logistic(np.einsum("ijk,k->ij", w_arr, detection_arr))
    return lam, det


def simulate_pcount(
    X: ArrayLike,
    W: ArrayLike,
    beta: ArrayLike,
    alpha: ArrayLike,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Simulate counts from the Poisson N-mixture model."""
    rng = np.random.default_rng(seed)
    lam, det = _design_values(X, W, beta, alpha)
    n = rng.poisson(lam)
    y = rng.binomial(n[:, None], det)
    return y.astype(np.float64)


def simulate_pcount_negbin(
    X: ArrayLike,
    W: ArrayLike,
    beta: ArrayLike,
    detection: ArrayLike,
    r: float,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Simulate counts from the negative-binomial N-mixture model.

    Latent abundance is generated with a Gamma-Poisson mixture using
    Gamma(shape=r, scale=lambda/r), then Poisson(gamma_rate).
    """
    if not np.isfinite(r) or r <= 0.0:
        raise ValueError("r must be positive and finite")
    rng = np.random.default_rng(seed)
    lam, det = _design_values(X, W, beta, detection)
    gamma_rate = rng.gamma(shape=float(r), scale=lam / float(r))
    n = rng.poisson(gamma_rate)
    y = rng.binomial(n[:, None], det)
    return y.astype(np.float64)


def simulate_pcount_zip(
    X: ArrayLike,
    W: ArrayLike,
    beta: ArrayLike,
    detection: ArrayLike,
    psi: float,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Simulate counts from the zero-inflated Poisson N-mixture model."""
    if not np.isfinite(psi) or psi <= 0.0 or psi >= 1.0:
        raise ValueError("psi must be in (0, 1)")
    rng = np.random.default_rng(seed)
    lam, det = _design_values(X, W, beta, detection)
    structural_zero = np.asarray(rng.binomial(1, float(psi), size=lam.shape[0])).astype(bool)
    n = rng.poisson(lam)
    n[structural_zero] = 0
    y = rng.binomial(n[:, None], det)
    return y.astype(np.float64)
