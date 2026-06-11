"""Experimental FitList wrapper for fitted model collections.

``FitList`` is a small convenience layer over existing fitted results. It
preserves model order, delegates model-selection work to the established
``pyabundance.model_selection`` functions, and optionally delegates prediction
for one selected model to the shared-core generic prediction dispatcher.
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, KeysView, Mapping, ValuesView
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, init=False)
class FitList:
    """Experimental ordered wrapper around fitted model results.

    The wrapper is additive only: it does not fit, refit, average, stack, or
    mutate models. Model comparison delegates to ``compare_models`` and
    ``aic_table``; prediction delegates to ``pyabundance.core.predict`` for one
    selected model only.
    """

    _models: Mapping[str, Any]

    def __init__(
        self,
        fits: Mapping[Any, Any] | Iterable[Any],
        *,
        names: Iterable[Any] | None = None,
    ) -> None:
        named = _normalize_named_fits(fits, names=names)
        object.__setattr__(self, "_models", MappingProxyType(dict(named)))

    @property
    def names(self) -> tuple[str, ...]:
        """Model names in insertion order."""

        return tuple(self._models.keys())

    @property
    def models(self) -> Mapping[str, Any]:
        """Read-only mapping of model name to fitted model."""

        return self._models

    def __len__(self) -> int:
        return len(self._models)

    def __iter__(self) -> Iterator[str]:
        return iter(self._models)

    def __getitem__(self, name: Any) -> Any:
        key = str(name)
        try:
            return self._models[key]
        except KeyError as exc:
            available = ", ".join(self.names)
            raise KeyError(f"unknown model name {key!r}; available models: {available}") from exc

    def keys(self) -> KeysView[str]:
        return self._models.keys()

    def items(self) -> ItemsView[str, Any]:
        return self._models.items()

    def values(self) -> ValuesView[Any]:
        return self._models.values()

    def aic_table(self, **kwargs: Any) -> Any:
        """Return an AIC table by delegating to ``pyabundance.model_selection.aic_table``."""

        from pyabundance.model_selection import aic_table

        return aic_table(dict(self._models), **kwargs)

    def compare(self, **kwargs: Any) -> Any:
        """Compare models by delegating to ``pyabundance.model_selection.compare_models``."""

        from pyabundance.model_selection import compare_models

        return compare_models(dict(self._models), **kwargs)

    @property
    def best_model_name(self) -> str:
        """Name of the lowest-AIC model under the default AIC table settings."""

        return str(self.aic_table().iloc[0]["model"])

    @property
    def best_model(self) -> Any:
        """Lowest-AIC fitted model under the default AIC table settings."""

        return self[self.best_model_name]

    def summary(self) -> str:
        """Return the delegated model-comparison summary string."""

        return self.compare().summary()

    def predict(self, type: str = "lambda", *, model: Any | None = None, **kwargs: Any) -> Any:
        """Predict from one selected model via shared-core generic dispatch.

        If ``model`` is omitted, the current default ``best_model`` is used.
        This method intentionally does not perform model averaging, ensemble
        prediction, stacking, refitting, or formula/newdata prediction.
        """

        from pyabundance.core.predict import predict

        selected = self.best_model if model is None else self[model]
        return predict(selected, type=type, **kwargs)


def _normalize_named_fits(
    fits: Mapping[Any, Any] | Iterable[Any],
    *,
    names: Iterable[Any] | None = None,
) -> list[tuple[str, Any]]:
    if isinstance(fits, Mapping):
        if names is not None:
            raise ValueError("names cannot be used when fits is a dict; use dict keys instead")
        named = [(str(name), fit) for name, fit in fits.items()]
        _validate_named_fits(named)
        return named

    fits_list = list(fits)
    if names is None:
        named = [(f"model_{idx + 1}", fit) for idx, fit in enumerate(fits_list)]
    else:
        name_list = [str(name) for name in names]
        if len(name_list) != len(fits_list):
            raise ValueError("names must have the same length as fits")
        named = list(zip(name_list, fits_list, strict=True))
    _validate_named_fits(named)
    return named


def _validate_named_fits(named: list[tuple[str, Any]]) -> None:
    if not named:
        raise ValueError("at least one fitted model is required")
    names = [name for name, _ in named]
    if len(set(names)) != len(names):
        raise ValueError("model names must be unique")
