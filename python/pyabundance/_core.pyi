from __future__ import annotations

from collections.abc import Sequence
from typing import Self, final

import numpy as np
from numpy.typing import NDArray

__version__: str
__all__ = [
    "PCountPoissonProblem",
    "PCountNegBinProblem",
    "PCountZIPProblem",
    "pcount_poisson_loglik",
    "pcount_poisson_predict_lambda",
    "pcount_negbin_loglik",
    "pcount_zip_loglik",
    "log_negative_binomial_pmf_mean_size",
    "log_zero_inflated_poisson_pmf",
    "pcount_poisson_predict_detection",
    "__version__",
]

@final
class PCountPoissonProblem:
    def __new__(
        cls,
        y: NDArray[np.float64],
        x: NDArray[np.float64],
        w: NDArray[np.float64],
        k: int,
    ) -> Self: ...
    @property
    def n_sites(self) -> int: ...
    @property
    def n_visits(self) -> int: ...
    @property
    def K(self) -> int: ...
    def loglik(self, theta: NDArray[np.float64]) -> float: ...
    def posterior_abundance(self, theta: NDArray[np.float64]) -> Sequence[Sequence[float]]: ...
    def predict_lambda(self, beta: NDArray[np.float64]) -> Sequence[float]: ...

@final
class PCountNegBinProblem:
    def __new__(
        cls,
        y: NDArray[np.float64],
        x: NDArray[np.float64],
        w: NDArray[np.float64],
        k: int,
    ) -> Self: ...
    @property
    def n_sites(self) -> int: ...
    @property
    def n_visits(self) -> int: ...
    @property
    def K(self) -> int: ...
    def loglik(self, theta: NDArray[np.float64]) -> float: ...
    def posterior_abundance(self, theta: NDArray[np.float64]) -> Sequence[Sequence[float]]: ...

@final
class PCountZIPProblem:
    def __new__(
        cls,
        y: NDArray[np.float64],
        x: NDArray[np.float64],
        w: NDArray[np.float64],
        k: int,
    ) -> Self: ...
    @property
    def n_sites(self) -> int: ...
    @property
    def n_visits(self) -> int: ...
    @property
    def K(self) -> int: ...
    def loglik(self, theta: NDArray[np.float64]) -> float: ...
    def posterior_abundance(self, theta: NDArray[np.float64]) -> Sequence[Sequence[float]]: ...

def pcount_poisson_loglik(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    w: NDArray[np.float64],
    theta: NDArray[np.float64],
    k: int,
) -> float: ...
def pcount_negbin_loglik(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    w: NDArray[np.float64],
    theta: NDArray[np.float64],
    k: int,
) -> float: ...
def pcount_zip_loglik(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    w: NDArray[np.float64],
    theta: NDArray[np.float64],
    k: int,
) -> float: ...
def log_negative_binomial_pmf_mean_size(n: int, mean: float, size: float) -> float: ...
def log_zero_inflated_poisson_pmf(n: int, lambda_: float, psi: float) -> float: ...
def pcount_poisson_predict_lambda(
    x: NDArray[np.float64], beta: NDArray[np.float64]
) -> Sequence[float]: ...
def pcount_poisson_predict_detection(
    w: NDArray[np.float64], alpha: NDArray[np.float64]
) -> Sequence[float]: ...
