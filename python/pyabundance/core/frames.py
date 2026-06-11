from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Self

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray

if TYPE_CHECKING:
    from pyabundance.formula import PCountMatrices


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


def _as_float_array(value: ArrayLike, name: str, ndim: int) -> NDArray[np.float64]:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions, got {arr.ndim}")
    return np.ascontiguousarray(arr, dtype=np.float64)


def _optional_tuple(value: Any, name: str) -> tuple[Any, ...]:
    if isinstance(value, str) or not hasattr(value, "__iter__"):
        raise TypeError(f"{name} must be list-like when provided")
    return tuple(value)


def _optional_string_tuple(value: Any, name: str) -> tuple[str, ...]:
    return tuple(str(item) for item in _optional_tuple(value, name))


@dataclass(frozen=True)
class FramePCount:
    """Experimental pcount-specific frame adapter for shared-core metadata plumbing.

    ``FramePCount`` carries the response matrix and pcount design arrays using the
    shared-core frame vocabulary. It is not a fitting object and does not replace
    :class:`pyabundance.formula.PCountMatrices`.
    """

    y: NDArray[np.float64]
    X: NDArray[np.float64]
    W: NDArray[np.float64]
    site_data: pd.DataFrame | None = None
    obs_data: pd.DataFrame | None = None
    site_ids: tuple[Any, ...] | None = None
    visit_labels: tuple[Any, ...] | None = None
    abundance_column_names: tuple[str, ...] | None = None
    detection_column_names: tuple[str, ...] | None = None
    count_cols: tuple[Any, ...] | None = None
    abundance_formula: str | None = None
    detection_formula: str | None = None
    visit_label_source: str | None = None
    visit_label_message: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        y_arr = _as_float_array(self.y, "y", 2)
        x_arr = _as_float_array(self.X, "X", 2)
        w_arr = _as_float_array(self.W, "W", 3)
        if y_arr.shape[0] != x_arr.shape[0] or y_arr.shape[0] != w_arr.shape[0]:
            raise ValueError("y, X, and W must have the same number of sites")
        if y_arr.shape[1] != w_arr.shape[1]:
            raise ValueError("y and W must have the same number of visits")

        site_ids = None if self.site_ids is None else _optional_tuple(self.site_ids, "site_ids")
        visit_labels = (
            None
            if self.visit_labels is None
            else _optional_tuple(self.visit_labels, "visit_labels")
        )
        abundance_column_names = (
            None
            if self.abundance_column_names is None
            else _optional_string_tuple(self.abundance_column_names, "abundance_column_names")
        )
        detection_column_names = (
            None
            if self.detection_column_names is None
            else _optional_string_tuple(self.detection_column_names, "detection_column_names")
        )
        count_cols = (
            None if self.count_cols is None else _optional_tuple(self.count_cols, "count_cols")
        )

        if site_ids is not None and len(site_ids) != y_arr.shape[0]:
            raise ValueError("site_ids must have length n_sites")
        if visit_labels is not None and len(visit_labels) != y_arr.shape[1]:
            raise ValueError("visit_labels must have length n_visits")
        if count_cols is not None and len(count_cols) != y_arr.shape[1]:
            raise ValueError("count_cols must have length n_visits")
        if abundance_column_names is not None and len(abundance_column_names) != x_arr.shape[1]:
            raise ValueError("abundance_column_names must have length X.shape[1]")
        if detection_column_names is not None and len(detection_column_names) != w_arr.shape[2]:
            raise ValueError("detection_column_names must have length W.shape[2]")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("frame metadata must be mapping-like")

        object.__setattr__(self, "y", y_arr)
        object.__setattr__(self, "X", x_arr)
        object.__setattr__(self, "W", w_arr)
        object.__setattr__(self, "site_ids", site_ids)
        object.__setattr__(self, "visit_labels", visit_labels)
        object.__setattr__(self, "abundance_column_names", abundance_column_names)
        object.__setattr__(self, "detection_column_names", detection_column_names)
        object.__setattr__(self, "count_cols", count_cols)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_matrices(
        cls,
        y: ArrayLike,
        X: ArrayLike,
        W: ArrayLike,
        *,
        site_ids: list[Any] | tuple[Any, ...] | None = None,
        visit_labels: list[Any] | tuple[Any, ...] | None = None,
        abundance_column_names: list[str] | tuple[str, ...] | None = None,
        detection_column_names: list[str] | tuple[str, ...] | None = None,
        count_cols: list[Any] | tuple[Any, ...] | None = None,
        abundance_formula: str | None = None,
        detection_formula: str | None = None,
        site_data: pd.DataFrame | None = None,
        obs_data: pd.DataFrame | None = None,
        visit_label_source: str | None = None,
        visit_label_message: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Self:
        """Create a pcount frame from existing response/design arrays."""

        return cls(
            y=np.asarray(y, dtype=np.float64),
            X=np.asarray(X, dtype=np.float64),
            W=np.asarray(W, dtype=np.float64),
            site_data=site_data,
            obs_data=obs_data,
            site_ids=None if site_ids is None else tuple(site_ids),
            visit_labels=None if visit_labels is None else tuple(visit_labels),
            abundance_column_names=None
            if abundance_column_names is None
            else tuple(abundance_column_names),
            detection_column_names=None
            if detection_column_names is None
            else tuple(detection_column_names),
            count_cols=None if count_cols is None else tuple(count_cols),
            abundance_formula=abundance_formula,
            detection_formula=detection_formula,
            visit_label_source=visit_label_source,
            visit_label_message=visit_label_message,
            metadata={} if metadata is None else metadata,
        )

    @classmethod
    def from_pcount_matrices(cls, matrices: PCountMatrices) -> Self:
        """Create a ``FramePCount`` from ``build_pcount_matrices`` output."""

        return cls.from_matrices(
            y=matrices.y,
            X=matrices.X,
            W=matrices.W,
            site_ids=matrices.site_ids,
            visit_labels=matrices.visit_labels,
            abundance_column_names=matrices.abundance_column_names,
            detection_column_names=matrices.detection_column_names,
            count_cols=matrices.count_cols,
            abundance_formula=getattr(matrices, "abundance_formula", None),
            detection_formula=getattr(matrices, "detection_formula", None),
            site_data=matrices.site_data_used,
            obs_data=matrices.obs_data_used,
            visit_label_source=matrices.visit_label_source,
            visit_label_message=matrices.visit_label_message,
        )

    @property
    def n_sites(self) -> int:
        return int(self.y.shape[0])

    @property
    def n_visits(self) -> int:
        return int(self.y.shape[1])

    @property
    def n_abundance_params(self) -> int:
        return int(self.X.shape[1])

    @property
    def n_detection_params(self) -> int:
        return int(self.W.shape[2])

    @property
    def response_shape(self) -> tuple[int, int]:
        return (self.n_sites, self.n_visits)

    @property
    def data_info(self) -> dict[str, int]:
        return {
            "n_sites": self.n_sites,
            "n_visits": self.n_visits,
            "n_abundance_params": self.n_abundance_params,
            "n_detection_params": self.n_detection_params,
        }
