from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

Mixture = Literal["poisson", "negative_binomial", "zero_inflated_poisson"]

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "pcount_validation"
MIXTURES: tuple[Mixture, ...] = ("poisson", "negative_binomial", "zero_inflated_poisson")
_REQUIRED_KEYS = {
    "name",
    "mixture",
    "K",
    "y_shape",
    "X_shape",
    "W_shape",
    "y",
    "X",
    "W",
    "theta",
    "expected_loglik",
    "tolerances",
    "provenance",
}
_EXTRA_PARAMS = {"poisson": 0, "negative_binomial": 1, "zero_inflated_poisson": 1}


@dataclass(frozen=True)
class PCountValidationFixture:
    """Validated, test-only pcount likelihood fixture."""

    name: str
    mixture: Mixture
    K: int
    y: NDArray[np.float64]
    X: NDArray[np.float64]
    W: NDArray[np.float64]
    theta: NDArray[np.float64]
    expected_loglik: float
    absolute_tolerance: float
    relative_tolerance: float
    provenance: str
    path: Path


def fixture_names() -> tuple[Mixture, ...]:
    """Return the checked-in pcount validation fixture names."""

    return MIXTURES


def load_pcount_validation_fixture(name: str) -> PCountValidationFixture:
    """Load and validate one checked-in pcount validation fixture."""

    path = FIXTURE_DIR / f"{name}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    _validate_raw_schema(raw, path)
    y = np.asarray(raw["y"], dtype=np.float64)
    x = np.asarray(raw["X"], dtype=np.float64)
    w = np.asarray(raw["W"], dtype=np.float64)
    theta = np.asarray(raw["theta"], dtype=np.float64)
    mixture = _as_mixture(raw["mixture"], path)
    _validate_arrays(raw, y, x, w, theta, mixture, path)
    tolerances = raw["tolerances"]
    return PCountValidationFixture(
        name=str(raw["name"]),
        mixture=mixture,
        K=int(raw["K"]),
        y=np.ascontiguousarray(y, dtype=np.float64),
        X=np.ascontiguousarray(x, dtype=np.float64),
        W=np.ascontiguousarray(w, dtype=np.float64),
        theta=np.ascontiguousarray(theta, dtype=np.float64),
        expected_loglik=float(raw["expected_loglik"]),
        absolute_tolerance=float(tolerances["absolute"]),
        relative_tolerance=float(tolerances["relative"]),
        provenance=str(raw["provenance"]),
        path=path,
    )


def _validate_raw_schema(raw: dict[str, Any], path: Path) -> None:
    missing = _REQUIRED_KEYS.difference(raw)
    if missing:
        raise AssertionError(f"{path} is missing required keys: {sorted(missing)}")
    unknown = set(raw).difference(_REQUIRED_KEYS)
    if unknown:
        raise AssertionError(f"{path} has unknown keys: {sorted(unknown)}")
    if not isinstance(raw["name"], str) or not raw["name"]:
        raise AssertionError(f"{path} requires a non-empty fixture name")
    if not isinstance(raw["K"], int) or raw["K"] < 0:
        raise AssertionError(f"{path} requires a non-negative integer K")
    tolerances = raw["tolerances"]
    if not isinstance(tolerances, dict):
        raise AssertionError(f"{path} requires a tolerances object")
    for key in ("absolute", "relative"):
        if key not in tolerances or float(tolerances[key]) <= 0.0:
            raise AssertionError(f"{path} requires a positive {key} tolerance")
    provenance = raw["provenance"]
    if not isinstance(provenance, str) or "clean-room" not in provenance.lower():
        raise AssertionError(f"{path} requires a clean-room provenance note")


def _as_mixture(value: object, path: Path) -> Mixture:
    if value not in MIXTURES:
        raise AssertionError(f"{path} has unsupported mixture {value!r}")
    return value  # type: ignore[return-value]


def _validate_arrays(
    raw: dict[str, Any],
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    w: NDArray[np.float64],
    theta: NDArray[np.float64],
    mixture: Mixture,
    path: Path,
) -> None:
    if y.ndim != 2 or x.ndim != 2 or w.ndim != 3:
        raise AssertionError(f"{path} must contain 2D y, 2D X, and 3D W arrays")
    if tuple(raw["y_shape"]) != y.shape:
        raise AssertionError(f"{path} y_shape does not match y")
    if tuple(raw["X_shape"]) != x.shape:
        raise AssertionError(f"{path} X_shape does not match X")
    if tuple(raw["W_shape"]) != w.shape:
        raise AssertionError(f"{path} W_shape does not match W")
    if y.shape[0] != x.shape[0] or y.shape[:2] != w.shape[:2]:
        raise AssertionError(f"{path} has inconsistent pcount dimensions")
    observed = y[~np.isnan(y)]
    if np.any(observed < 0.0) or np.any(np.abs(observed - np.round(observed)) > 1.0e-12):
        raise AssertionError(f"{path} has non-integer or negative observed counts")
    if observed.size and np.max(observed) > int(raw["K"]):
        raise AssertionError(f"{path} has observed counts greater than K")
    expected_params = x.shape[1] + w.shape[2] + _EXTRA_PARAMS[mixture]
    if theta.ndim != 1 or theta.shape[0] != expected_params:
        raise AssertionError(f"{path} theta must be length {expected_params}")
    finite_arrays = (x, w, theta, np.asarray([raw["expected_loglik"]], dtype=np.float64))
    if not all(np.all(np.isfinite(arr)) for arr in finite_arrays):
        raise AssertionError(f"{path} contains non-finite X, W, theta, or expected_loglik values")
