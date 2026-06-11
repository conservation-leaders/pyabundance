from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from pyabundance.core.specs import ModelSpec, ParameterBlock


@runtime_checkable
class LikelihoodProblemProtocol(Protocol):
    """Minimal protocol implemented by likelihood problem objects."""

    def loglik(self, theta: NDArray[np.float64]) -> float: ...


@runtime_checkable
class FitResultProtocol(Protocol):
    """Common result surface expected from fitted model-family results."""

    params: NDArray[np.float64]
    loglik: float
    success: bool
    message: str

    @property
    def aic(self) -> float: ...

    @property
    def model_spec(self) -> ModelSpec: ...

    @property
    def parameter_blocks(self) -> tuple[ParameterBlock, ...]: ...

    def coef_table(self, *args: Any, **kwargs: Any) -> pd.DataFrame | list[dict[str, Any]]: ...

    def vcov(self) -> NDArray[np.float64]: ...
