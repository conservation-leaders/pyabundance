from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

__version__: str

def pcount_poisson_loglik(
    y: NDArray[np.float64],
    X: NDArray[np.float64],
    W: NDArray[np.float64],
    theta: NDArray[np.float64],
    K: int,
) -> float: ...

def pcount_poisson_predict_lambda(
    X: NDArray[np.float64], beta: NDArray[np.float64]
) -> Sequence[float]: ...

def pcount_poisson_predict_detection(
    W: NDArray[np.float64], alpha: NDArray[np.float64]
) -> Sequence[float]: ...
