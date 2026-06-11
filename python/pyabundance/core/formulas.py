from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd
from formulaic import model_matrix
from numpy.typing import NDArray

from pyabundance.core.specs import LinkName, ProcessLevel, ProcessSpec


@dataclass(frozen=True)
class ProcessDesign:
    """Fixed-effect design matrix for one experimental shared-core process."""

    process: str
    level: ProcessLevel
    link: LinkName
    formula: str
    matrix: NDArray[np.float64]
    columns: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.process, str) or not self.process:
            raise ValueError("process name must be a non-empty string")
        formula = validate_rhs_formula(self.formula)
        matrix = np.asarray(self.matrix, dtype=np.float64)
        if matrix.ndim != 2:
            raise ValueError("process design matrix must be 2D")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("process design matrix contains missing or non-finite values")
        columns = tuple(str(column) for column in self.columns)
        if len(columns) != matrix.shape[1]:
            raise ValueError("process design column count must match matrix width")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("process design metadata must be mapping-like")

        object.__setattr__(self, "formula", formula)
        object.__setattr__(self, "matrix", np.ascontiguousarray(matrix, dtype=np.float64))
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def validate_rhs_formula(formula: str, name: str = "formula") -> str:
    """Validate and normalize a fixed-effect RHS-only formula string.

    This intentionally mirrors the current pcount DataFrame formula restrictions:
    RHS-only fixed effects are supported, while response-side formulas, random
    effects, offsets, spline helpers, and dot expansion are not.
    """

    if not isinstance(formula, str) or not formula.strip():
        raise ValueError(f"{name} must be a non-empty RHS-only formula string")
    formula = formula.strip()
    if formula.count("~") != 1:
        raise ValueError(f"{name} must be RHS-only and start with '~'")
    lhs, rhs = formula.split("~", 1)
    if lhs.strip():
        raise ValueError(f"{name} must be RHS-only; response-side formulas are not supported")
    if not rhs.strip():
        raise ValueError(f"{name} must include a non-empty right-hand side")

    unsupported_tokens = ["|", "offset(", "bs(", "cs(", "cr(", "s(", "."]
    for token in unsupported_tokens:
        if token in rhs:
            raise ValueError(
                f"{name} uses unsupported formula feature {token!r}; "
                "only fixed-effect RHS formulas such as '~ x', '~ visit - 1', "
                "'~ x:visit', and '~ x * visit' are supported"
            )
    return formula


def build_process_design(spec: ProcessSpec, data: pd.DataFrame) -> ProcessDesign:
    """Build one fixed-effect design matrix from a ``ProcessSpec`` and DataFrame."""

    if not isinstance(spec, ProcessSpec):
        raise TypeError("spec must be a ProcessSpec instance")
    if spec.formula is None:
        raise ValueError(
            f"process {spec.name!r} at level {spec.level!r} has no formula; "
            "cannot build a design matrix"
        )
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f"data for process {spec.name!r} must be a pandas DataFrame")

    formula = validate_rhs_formula(spec.formula, f"{spec.name} formula")
    try:
        matrix = model_matrix(formula, data, na_action="raise")
    except Exception as exc:
        raise ValueError(f"failed to build process {spec.name!r} design matrix: {exc}") from exc

    columns = tuple(str(column) for column in matrix.columns)
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"process {spec.name!r} design matrix must be 2D")
    if not np.all(np.isfinite(arr)):
        raise ValueError(
            f"process {spec.name!r} design matrix contains missing or non-finite values"
        )

    return ProcessDesign(
        process=spec.name,
        level=spec.level,
        link=spec.link,
        formula=formula,
        matrix=np.ascontiguousarray(arr, dtype=np.float64),
        columns=columns,
        metadata=spec.metadata,
    )


def build_process_designs(
    processes: Mapping[str, ProcessSpec],
    data_by_level: Mapping[str, pd.DataFrame],
    *,
    process_names: Iterable[str] | None = None,
) -> dict[str, ProcessDesign]:
    """Build process designs for formula-bearing processes.

    By default, formula-less processes are skipped. If ``process_names`` is
    supplied, each requested process must be buildable; requesting a formula-less
    global process raises a clear error instead of silently inventing a design.
    """

    if not isinstance(processes, Mapping):
        raise TypeError("processes must be mapping-like")
    if not isinstance(data_by_level, Mapping):
        raise TypeError("data_by_level must be mapping-like")

    requested = _requested_process_names(processes, process_names)
    designs: dict[str, ProcessDesign] = {}
    for name in requested:
        spec = processes[name]
        if not isinstance(spec, ProcessSpec):
            raise TypeError(f"process {name!r} must be a ProcessSpec instance")
        if name != spec.name:
            raise ValueError("process keys must match ProcessSpec.name")
        if spec.formula is None:
            if process_names is None:
                continue
            raise ValueError(
                f"process {name!r} at level {spec.level!r} has no formula; "
                "cannot build a design matrix"
            )
        if spec.level not in data_by_level:
            raise ValueError(
                f"missing data for process level {spec.level!r} "
                f"needed by process {name!r}"
            )
        designs[name] = build_process_design(spec, data_by_level[spec.level])
    return designs


def _requested_process_names(
    processes: Mapping[str, ProcessSpec], process_names: Iterable[str] | None
) -> tuple[str, ...]:
    if process_names is None:
        return tuple(processes.keys())
    if isinstance(process_names, str) or not hasattr(process_names, "__iter__"):
        raise TypeError("process_names must be an iterable of process names")
    names = tuple(process_names)
    for name in names:
        if name not in processes:
            raise KeyError(name)
    return names
