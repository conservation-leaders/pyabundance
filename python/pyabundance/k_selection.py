from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class KSuggestion:
    """Metadata describing an automatically selected upper integration limit ``K``."""

    K: int
    max_observed: int
    minimum_buffer: int
    multiplier: float
    message: str

    def __int__(self) -> int:
        return self.K


def suggest_K(
    y: Any,
    *,
    minimum_buffer: int = 50,
    multiplier: float = 3.0,
    min_K: int | None = None,
    max_K: int | None = None,
    return_info: bool = False,
) -> int | KSuggestion:
    """Suggest a conservative ``K`` for pcount-style N-mixture fitting.

    Missing counts are ignored. Non-missing counts must be non-negative integers.
    By default an integer is returned; use ``return_info=True`` for explanatory metadata.
    """

    if minimum_buffer < 0:
        raise ValueError("minimum_buffer must be non-negative")
    if multiplier < 1.0:
        raise ValueError("multiplier must be at least 1.0")
    if min_K is not None and min_K < 0:
        raise ValueError("min_K must be non-negative")
    if max_K is not None and max_K < 0:
        raise ValueError("max_K must be non-negative")

    arr = np.asarray(y, dtype=np.float64)
    if arr.size == 0:
        max_observed = 0
    else:
        observed = arr[~np.isnan(arr)]
        if np.any(~np.isfinite(observed)):
            raise ValueError("counts must be finite or NaN")
        if np.any(observed < 0) or np.any(np.abs(observed - np.round(observed)) > 1.0e-12):
            raise ValueError("non-missing counts must be non-negative integers")
        max_observed = int(np.max(observed)) if observed.size else 0

    buffered = int(max_observed + minimum_buffer)
    multiplied = int(np.ceil(max_observed * multiplier))
    K = max(buffered, multiplied)
    if min_K is not None:
        K = max(K, int(min_K))
    if max_K is not None and K > int(max_K):
        raise ValueError(
            f"suggested K {K} exceeds max_K {int(max_K)}; increase max_K or choose K explicitly"
        )
    message = (
        f"Auto-selected K={K} from max observed count {max_observed} "
        f"using max(max_count + {minimum_buffer}, ceil(max_count * {multiplier:g}))."
    )
    info = KSuggestion(
        K=int(K),
        max_observed=max_observed,
        minimum_buffer=int(minimum_buffer),
        multiplier=float(multiplier),
        message=message,
    )
    return info if return_info else info.K
