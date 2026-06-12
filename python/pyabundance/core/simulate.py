"""Experimental shared simulation dispatch.

This module is an intentionally small facade over existing model-specific
simulation helpers.  The stable pcount simulation functions in
:mod:`pyabundance.simulate` remain the source of truth for simulation math.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Simulator = Callable[[dict[str, Any]], Any]

_SIMULATORS: dict[str, Simulator] = {}
_PCOUNT_DIRECT_KEYS = {"X", "W", "beta", "detection", "alpha", "mixture", "r", "psi", "seed"}


def register_simulator(model: str, handler: Simulator) -> Simulator:
    """Register an experimental simulation handler for a model family.

    Parameters
    ----------
    model:
        Shared-core model family name, such as ``"pcount"``.
    handler:
        Callable receiving a mutable dictionary of simulation keyword arguments
        and returning the model-specific simulated object.

    Returns
    -------
    Callable
        The registered handler, allowing callers to retain or re-export it.
    """

    if not isinstance(model, str) or not model:
        raise ValueError("model must be a non-empty string")
    if not callable(handler):
        raise TypeError("handler must be callable")
    _SIMULATORS[model] = handler
    return handler


def simulate(model: str, **kwargs: Any) -> Any:
    """Dispatch an experimental simulation request by model family.

    Currently only ``model="pcount"`` is supported.  The pcount handler accepts
    ``X``, ``W``, ``beta``, ``mixture`` (default ``"poisson"``), and either
    ``detection`` or the backward-compatible alias ``alpha`` for detection
    coefficients.  It delegates directly to ``simulate_pcount``,
    ``simulate_pcount_negbin``, or ``simulate_pcount_zip`` and returns the same
    array type and shape as those stable helpers.
    """

    if not isinstance(model, str) or not model:
        raise TypeError("model family must be a non-empty string")
    handler = _SIMULATORS.get(model)
    if handler is None:
        raise ValueError(f"unsupported model family {model!r} for generic simulate dispatch")
    return handler(dict(kwargs))


def _simulate_pcount(kwargs: dict[str, Any]) -> Any:
    extras = sorted(set(kwargs) - _PCOUNT_DIRECT_KEYS)
    if extras:
        names = ", ".join(extras)
        raise TypeError(f"invalid extra arguments for pcount simulation: {names}")

    mixture = kwargs.pop("mixture", "poisson")
    canonical = _canonical_pcount_mixture(mixture)
    X = _pop_required(kwargs, "X")
    W = _pop_required(kwargs, "W")
    beta = _pop_required(kwargs, "beta")
    detection = _pop_detection(kwargs)
    seed = kwargs.pop("seed", None)

    from pyabundance.simulate import simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip

    if canonical == "poisson":
        _reject_remaining(kwargs)
        return simulate_pcount(X=X, W=W, beta=beta, alpha=detection, seed=seed)
    if canonical == "negative_binomial":
        r = _pop_required(
            kwargs, "r", message="r is required for negative-binomial pcount simulation"
        )
        _reject_remaining(kwargs)
        return simulate_pcount_negbin(X=X, W=W, beta=beta, detection=detection, r=r, seed=seed)
    psi = _pop_required(kwargs, "psi", message="psi is required for ZIP pcount simulation")
    _reject_remaining(kwargs)
    return simulate_pcount_zip(X=X, W=W, beta=beta, detection=detection, psi=psi, seed=seed)


def _canonical_pcount_mixture(mixture: Any) -> str:
    if not isinstance(mixture, str) or not mixture:
        raise ValueError("pcount mixture must be a non-empty string")
    from pyabundance.pcount import canonical_mixture

    try:
        return canonical_mixture(mixture)
    except ValueError as exc:
        raise ValueError(f"unsupported pcount mixture {mixture!r}") from exc


def _pop_required(kwargs: dict[str, Any], name: str, *, message: str | None = None) -> Any:
    if name not in kwargs:
        raise TypeError(message or f"{name} is required for pcount simulation")
    return kwargs.pop(name)


def _pop_detection(kwargs: dict[str, Any]) -> Any:
    has_detection = "detection" in kwargs
    has_alpha = "alpha" in kwargs
    if has_detection and has_alpha:
        raise TypeError("provide only one of detection or alpha for pcount simulation")
    if has_detection:
        return kwargs.pop("detection")
    if has_alpha:
        return kwargs.pop("alpha")
    raise TypeError("detection is required for pcount simulation; alpha is accepted as an alias")


def _reject_remaining(kwargs: dict[str, Any]) -> None:
    if kwargs:
        names = ", ".join(sorted(kwargs))
        raise TypeError(f"invalid extra arguments for pcount simulation: {names}")


register_simulator("pcount", _simulate_pcount)
