from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "y", np.asarray(self.y, dtype=np.float64))
        object.__setattr__(self, "site_ids", tuple(self.site_ids))
        if not isinstance(self.metadata, Mapping):
            raise TypeError("model frame metadata must be mapping-like")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def response_shape(self) -> tuple[int, ...]:
        return tuple(int(dim) for dim in self.y.shape)

    @property
    def n_sites(self) -> int:
        return int(self.y.shape[0]) if self.y.ndim > 0 else 0
