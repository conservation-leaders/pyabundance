from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _logistic(x: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def simulate_pcount(
    X: ArrayLike,
    W: ArrayLike,
    beta: ArrayLike,
    alpha: ArrayLike,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Simulate counts from the Poisson N-mixture model."""
    rng = np.random.default_rng(seed)
    x_arr = np.asarray(X, dtype=np.float64)
    w_arr = np.asarray(W, dtype=np.float64)
    beta_arr = np.asarray(beta, dtype=np.float64)
    alpha_arr = np.asarray(alpha, dtype=np.float64)
    if x_arr.ndim != 2 or w_arr.ndim != 3:
        raise ValueError("X must be 2D and W must be 3D")
    if x_arr.shape[0] != w_arr.shape[0]:
        raise ValueError("X and W must have the same number of sites")
    if x_arr.shape[1] != beta_arr.size or w_arr.shape[2] != alpha_arr.size:
        raise ValueError("design matrices and parameter vectors have incompatible shapes")
    lam = np.exp(x_arr @ beta_arr)
    det = _logistic(np.einsum("ijk,k->ij", w_arr, alpha_arr))
    n = rng.poisson(lam)
    y = rng.binomial(n[:, None], det)
    return y.astype(np.float64)
