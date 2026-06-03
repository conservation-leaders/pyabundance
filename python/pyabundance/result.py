from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from pyabundance import _core


@dataclass(frozen=True)
class PCountResult:
    params: NDArray[np.float64]
    n_abundance_params: int
    loglik: float
    success: bool
    message: str
    K: int
    mixture: Literal["poisson"]
    X: NDArray[np.float64]
    W: NDArray[np.float64]

    @property
    def beta(self) -> NDArray[np.float64]:
        return self.params[: self.n_abundance_params].copy()

    @property
    def alpha(self) -> NDArray[np.float64]:
        return self.params[self.n_abundance_params :].copy()

    @property
    def aic(self) -> float:
        return 2.0 * self.params.size - 2.0 * self.loglik

    def predict_lambda(self, X: NDArray[np.float64] | None = None) -> NDArray[np.float64]:
        x_arr = self.X if X is None else np.ascontiguousarray(X, dtype=np.float64)
        values = _core.pcount_poisson_predict_lambda(x_arr, self.beta)
        return np.asarray(values, dtype=np.float64)

    def predict_detection(self, W: NDArray[np.float64] | None = None) -> NDArray[np.float64]:
        w_arr = self.W if W is None else np.ascontiguousarray(W, dtype=np.float64)
        values = _core.pcount_poisson_predict_detection(w_arr, self.alpha)
        return np.asarray(values, dtype=np.float64).reshape(w_arr.shape[0], w_arr.shape[1])

    def summary(self) -> str:
        lines = [
            "PCountResult(mixture='poisson')",
            f"success: {self.success}",
            f"message: {self.message}",
            f"logLik: {self.loglik:.6g}",
            f"AIC: {self.aic:.6g}",
            f"K: {self.K}",
            f"beta: {np.array2string(self.beta, precision=6)}",
            f"alpha: {np.array2string(self.alpha, precision=6)}",
        ]
        return "\n".join(lines)
