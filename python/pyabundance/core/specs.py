from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, get_args

LinkName = Literal["identity", "log", "logit", "cloglog"]
ProcessLevel = Literal["site", "observation", "primary", "secondary", "global", "latent", "extra"]

_LINK_NAMES = set(get_args(LinkName))
_PROCESS_LEVELS = set(get_args(ProcessLevel))


@dataclass(frozen=True)
class ProcessSpec:
    """Metadata describing one model process and its link-scale design."""

    name: str
    formula: str | None
    link: LinkName
    level: ProcessLevel
    columns: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("process name must be a non-empty string")
        if self.formula is not None and not isinstance(self.formula, str):
            raise TypeError("process formula must be a string or None")
        if self.link not in _LINK_NAMES:
            raise ValueError(f"unsupported link {self.link!r}")
        if self.level not in _PROCESS_LEVELS:
            raise ValueError(f"unsupported process level {self.level!r}")
        if not all(isinstance(column, str) for column in self.columns):
            raise TypeError("process columns must be strings")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("process metadata must be mapping-like")
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class ParameterBlock:
    """Contiguous slice of a fitted parameter vector for one process."""

    name: str
    start: int
    stop: int
    link: LinkName
    columns: tuple[str, ...] = ()
    process: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("parameter block name must be a non-empty string")
        if not isinstance(self.start, int) or not isinstance(self.stop, int):
            raise TypeError("parameter block start and stop must be integers")
        if self.start < 0:
            raise ValueError("parameter block start must be non-negative")
        if self.stop < self.start:
            raise ValueError("parameter block stop must be greater than or equal to start")
        if self.link not in _LINK_NAMES:
            raise ValueError(f"unsupported link {self.link!r}")
        if self.process is not None and not isinstance(self.process, str):
            raise TypeError("parameter block process must be a string or None")
        if not all(isinstance(column, str) for column in self.columns):
            raise TypeError("parameter block columns must be strings")
        object.__setattr__(self, "columns", tuple(self.columns))
        if self.columns and len(self.columns) != self.size:
            raise ValueError("parameter block column count must match block size")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("parameter block metadata must be mapping-like")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def size(self) -> int:
        return self.stop - self.start

    @property
    def slice(self) -> slice:
        return slice(self.start, self.stop)


@dataclass(frozen=True)
class ModelSpec:
    """Model-family metadata shared by current and future pyabundance results."""

    model: str
    processes: Mapping[str, ProcessSpec]
    parameter_blocks: tuple[ParameterBlock, ...] = ()
    response: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not self.model:
            raise ValueError("model must be a non-empty string")
        if not isinstance(self.processes, Mapping):
            raise TypeError("processes must be mapping-like")
        if not self.processes:
            raise ValueError("model spec must include at least one process")
        processes = dict(self.processes)
        for key, process in processes.items():
            if not isinstance(key, str) or not key:
                raise ValueError("process keys must be non-empty strings")
            if not isinstance(process, ProcessSpec):
                raise TypeError("process values must be ProcessSpec instances")
            if key != process.name:
                raise ValueError("process keys must match ProcessSpec.name")
        object.__setattr__(self, "processes", MappingProxyType(processes))
        object.__setattr__(self, "parameter_blocks", tuple(self.parameter_blocks))
        for block in self.parameter_blocks:
            if not isinstance(block, ParameterBlock):
                raise TypeError("parameter_blocks must contain ParameterBlock instances")
        block_names = [block.name for block in self.parameter_blocks]
        if len(set(block_names)) != len(block_names):
            raise ValueError("parameter block names must be unique")
        for block in self.parameter_blocks:
            if block.process is not None and block.process not in self.processes:
                raise ValueError(f"parameter block process {block.process!r} is not in processes")
        sorted_blocks = sorted(self.parameter_blocks, key=lambda block: (block.start, block.stop))
        previous_stop = 0
        for block in sorted_blocks:
            if block.start < previous_stop:
                raise ValueError("parameter block ranges must not overlap")
            previous_stop = block.stop
        if self.response is not None and not isinstance(self.response, str):
            raise TypeError("response must be a string or None")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("model metadata must be mapping-like")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def process_names(self) -> tuple[str, ...]:
        return tuple(self.processes.keys())

    def process(self, name: str) -> ProcessSpec:
        return self.processes[name]

    def block(self, name: str) -> ParameterBlock:
        for block in self.parameter_blocks:
            if block.name == name:
                return block
        raise KeyError(name)
