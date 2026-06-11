from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray


@dataclass(frozen=True)
class ModelFrame:
    """Generic response/covariate container for model-family-specific frames."""

    y: NDArray[np.float64]
    site_data: pd.DataFrame | None = None
    obs_data: pd.DataFrame | None = None
    site_ids: tuple[Any, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def response_shape(self) -> tuple[int, ...]:
        return tuple(int(dim) for dim in self.y.shape)

    @property
    def n_sites(self) -> int:
        return int(self.y.shape[0]) if self.y.ndim > 0 else 0
