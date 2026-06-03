from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

__version__: str

class PCountPoissonProblem:
    def __init__(
        self,
        y: NDArray[np.float64],
        X: NDArray[np.float64],
        W: NDArray[np.float64],
        K: int,
    ) -> None: ...
    @property
    def n_sites(self) -> int: ...
    @property
    def n_visits(self) -> int: ...
    @property
    def K(self) -> int: ...
    def loglik(self, theta: NDArray[np.float64]) -> float: ...
    def posterior_abundance(self, theta: NDArray[np.float64]) -> Sequence[Sequence[float]]: ...
    def predict_lambda(self, beta: NDArray[np.float64]) -> Sequence[float]: ...

class PCountNegBinProblem:
    def __init__(
        self,
        y: NDArray[np.float64],
        X: NDArray[np.float64],
        W: NDArray[np.float64],
        K: int,
    ) -> None: ...
    @property
    def n_sites(self) -> int: ...
    @property
    def n_visits(self) -> int: ...
    @property
    def K(self) -> int: ...
    def loglik(self, theta: NDArray[np.float64]) -> float: ...
    def posterior_abundance(self, theta: NDArray[np.float64]) -> Sequence[Sequence[float]]: ...

class PCountZIPProblem:
    def __init__(
        self,
        y: NDArray[np.float64],
        X: NDArray[np.float64],
        W: NDArray[np.float64],
        K: int,
    ) -> None: ...
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
    X: NDArray[np.float64],
    W: NDArray[np.float64],
    theta: NDArray[np.float64],
    K: int,
) -> float: ...
def pcount_negbin_loglik(
    y: NDArray[np.float64],
    X: NDArray[np.float64],
    W: NDArray[np.float64],
    theta: NDArray[np.float64],
    K: int,
) -> float: ...
def pcount_zip_loglik(
    y: NDArray[np.float64],
    X: NDArray[np.float64],
    W: NDArray[np.float64],
    theta: NDArray[np.float64],
    K: int,
) -> float: ...
def log_negative_binomial_pmf_mean_size(n: int, mean: float, size: float) -> float: ...
def log_zero_inflated_poisson_pmf(n: int, lambda_: float, psi: float) -> float: ...
def pcount_poisson_predict_lambda(
    X: NDArray[np.float64], beta: NDArray[np.float64]
) -> Sequence[float]: ...
def pcount_poisson_predict_detection(
    W: NDArray[np.float64], detection: NDArray[np.float64]
) -> Sequence[float]: ...
