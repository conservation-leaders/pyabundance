"""Experimental descriptive parameter mapping helpers for fitted pcount models.

These helpers summarize how the existing :class:`pyabundance.result.PCountResult`
coefficient vector maps to pyabundance pcount process names, shared-core
parameter blocks, link functions, and common pcount/unmarked-style terminology.
They are descriptive only and do not affect likelihoods, fitting, prediction,
simulation, bootstrap, or model-selection behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from pyabundance.result import PCountResult

MappingTableOrientation = Literal["dict", "records", "list", "series", "split", "tight", "index"]


@dataclass(frozen=True)
class ParameterMappingRow:
    """One row in a descriptive pcount parameter mapping table."""

    index: int
    parameter: str
    pyabundance_name: str
    process: str
    block: str
    block_start: int
    block_stop: int
    block_index: int
    parameter_vector_index: int
    link: str
    level: str
    estimate: float
    transformed_name: str | None
    transformed_estimate: float | None
    formula: str | None
    column: str
    process_columns: tuple[str, ...]
    coefficient_source: str
    fitted_block: str
    mixture: str
    K: int
    model: str
    model_spec_process: dict[str, Any]
    model_metadata: dict[str, Any]
    unmarked_term: str
    notes: str


@dataclass(frozen=True)
class PCountParameterMapping:
    """Descriptive mapping for a fitted pcount parameter vector.

    The mapping is experimental, pcount-specific metadata. It is intended for
    inspection, documentation, and validation of naming conventions only.
    """

    rows: tuple[ParameterMappingRow, ...]

    @property
    def table(self) -> pd.DataFrame:
        """Return the mapping as a pandas ``DataFrame``."""

        return pd.DataFrame([asdict(row) for row in self.rows])

    def summary(self) -> dict[str, Any]:
        """Return compact metadata about the fitted pcount mapping."""

        if not self.rows:
            return {
                "model": "pcount",
                "mixture": None,
                "K": None,
                "n_parameters": 0,
                "processes": [],
                "blocks": [],
            }
        blocks: list[dict[str, Any]] = []
        seen_blocks: set[str] = set()
        processes: list[str] = []
        seen_processes: set[str] = set()
        for row in self.rows:
            if row.process not in seen_processes:
                processes.append(row.process)
                seen_processes.add(row.process)
            if row.block not in seen_blocks:
                blocks.append(
                    {
                        "block": row.block,
                        "process": row.process,
                        "start": row.block_start,
                        "stop": row.block_stop,
                        "link": row.link,
                        "level": row.level,
                    }
                )
                seen_blocks.add(row.block)
        first = self.rows[0]
        return {
            "model": first.model,
            "mixture": first.mixture,
            "K": first.K,
            "n_parameters": len(self.rows),
            "processes": processes,
            "blocks": blocks,
        }

    def to_dict(self, orient: MappingTableOrientation = "records") -> Any:
        """Return ``table.to_dict(orient=...)`` for convenience."""

        return self.table.to_dict(orient=orient)


_PROCESS_METADATA = {
    "lambda": {
        "coefficient_source": "result.beta",
        "unmarked_term": "abundance state / lambda coefficients",
        "notes": "Site-level abundance intensity coefficients on the log link.",
    },
    "p": {
        "coefficient_source": "result.detection / result.alpha",
        "unmarked_term": "detection probability coefficients",
        "notes": "Observation-level detection probability coefficients on the logit link.",
    },
    "r": {
        "coefficient_source": "result.log_r",
        "unmarked_term": "negative-binomial dispersion / size parameter",
        "notes": "Global negative-binomial extra parameter; transformed value is result.r.",
    },
    "psi": {
        "coefficient_source": "result.logit_psi",
        "unmarked_term": "zero-inflation probability parameter",
        "notes": "Global ZIP extra parameter; transformed value is result.psi.",
    },
}


def _require_pcount_result(result: object) -> PCountResult:
    if not isinstance(result, PCountResult):
        raise TypeError("pcount_parameter_mapping() requires a PCountResult")
    return result


def _validate_parameter_blocks(result: PCountResult) -> None:
    params = np.asarray(result.params, dtype=np.float64)
    if params.ndim != 1:
        raise ValueError("PCountResult.params must be a one-dimensional vector")
    blocks = tuple(result.parameter_blocks)
    if not blocks:
        raise ValueError("PCountResult.parameter_blocks must not be empty")
    sorted_blocks = sorted(blocks, key=lambda block: (block.start, block.stop, block.name))
    expected_start = 0
    for block in sorted_blocks:
        if block.start != expected_start:
            raise ValueError(
                "PCountResult.parameter_blocks must cover the parameter vector without gaps "
                "or overlap"
            )
        if block.stop > params.size:
            raise ValueError("PCountResult.parameter_blocks exceed result.params length")
        if block.size != len(block.columns):
            raise ValueError(
                f"parameter block {block.name!r} has {block.size} parameters but "
                f"{len(block.columns)} columns"
            )
        expected_start = block.stop
    if expected_start != params.size:
        raise ValueError(
            "PCountResult.parameter_blocks must cover the full result.params vector"
        )


def _as_plain_metadata(mapping: Any) -> dict[str, Any]:
    return dict(mapping) if mapping is not None else {}


def _transformed_value(result: PCountResult, process: str) -> tuple[str | None, float | None]:
    if process == "r":
        return "r", None if result.r is None else float(result.r)
    if process == "psi":
        return "psi", None if result.psi is None else float(result.psi)
    return None, None


def pcount_parameter_mapping(result: object) -> PCountParameterMapping:
    """Return a descriptive parameter mapping for a fitted pcount result.

    Parameters
    ----------
    result:
        A fitted :class:`pyabundance.result.PCountResult`.

    Returns
    -------
    PCountParameterMapping
        A compact object with a ``.table`` DataFrame and ``.summary()`` method.

    Raises
    ------
    TypeError
        If ``result`` is not a ``PCountResult``.
    ValueError
        If the fitted result's parameter blocks do not exactly cover the
        parameter vector.

    Notes
    -----
    The mapping is descriptive only. It does not change likelihood, fitting,
    prediction, simulation, bootstrap, or model-selection behavior.
    """

    fit = _require_pcount_result(result)
    _validate_parameter_blocks(fit)
    spec = fit.model_spec
    params = np.asarray(fit.params, dtype=np.float64)
    rows: list[ParameterMappingRow] = []
    model_metadata = _as_plain_metadata(spec.metadata)

    for block in fit.parameter_blocks:
        process_name = block.process or block.name
        process = spec.process(process_name)
        process_metadata = _as_plain_metadata(process.metadata)
        process_metadata.update(
            {
                "name": process.name,
                "formula": process.formula,
                "link": process.link,
                "level": process.level,
                "columns": tuple(process.columns),
            }
        )
        mapping_metadata = _PROCESS_METADATA.get(
            process_name,
            {
                "coefficient_source": f"result.params[{block.start}:{block.stop}]",
                "unmarked_term": process_name,
                "notes": "Descriptive pcount parameter mapping row.",
            },
        )
        transformed_name, transformed_estimate = _transformed_value(fit, process_name)
        for offset, param_index in enumerate(range(block.start, block.stop)):
            column = (
                block.columns[offset] if offset < len(block.columns) else f"param[{param_index}]"
            )
            rows.append(
                ParameterMappingRow(
                    index=param_index,
                    parameter=column,
                    pyabundance_name=process_name,
                    process=process_name,
                    block=block.name,
                    block_start=block.start,
                    block_stop=block.stop,
                    block_index=offset,
                    parameter_vector_index=param_index,
                    link=block.link,
                    level=process.level,
                    estimate=float(params[param_index]),
                    transformed_name=transformed_name if block.size == 1 else None,
                    transformed_estimate=transformed_estimate if block.size == 1 else None,
                    formula=process.formula,
                    column=column,
                    process_columns=tuple(process.columns),
                    coefficient_source=str(mapping_metadata["coefficient_source"]),
                    fitted_block=f"{block.name} ParameterBlock",
                    mixture=str(fit.mixture),
                    K=int(fit.K),
                    model=spec.model,
                    model_spec_process=process_metadata,
                    model_metadata=model_metadata,
                    unmarked_term=str(mapping_metadata["unmarked_term"]),
                    notes=str(mapping_metadata["notes"]),
                )
            )
    return PCountParameterMapping(rows=tuple(rows))


def pcount_parameter_mapping_table(result: object) -> pd.DataFrame:
    """Return :func:`pcount_parameter_mapping` as a pandas ``DataFrame``."""

    return pcount_parameter_mapping(result).table


def pcount_parameter_map(result: object) -> PCountParameterMapping:
    """Alias for :func:`pcount_parameter_mapping`."""

    return pcount_parameter_mapping(result)


__all__ = [
    "ParameterMappingRow",
    "PCountParameterMapping",
    "pcount_parameter_map",
    "pcount_parameter_mapping",
    "pcount_parameter_mapping_table",
]
