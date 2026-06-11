"""Experimental shared prediction dispatch for fitted model results.

This module intentionally provides only a small dispatch layer. It does not
implement new prediction math or formula/newdata prediction; registered model
handlers delegate to existing result methods.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Predictor = Callable[[Any, str, dict[str, Any]], Any]

_PREDICTORS: dict[str, Predictor] = {}
_NEWDATA_KEYS = ("newdata", "new_site_data", "new_obs_data")
_MATRIX_NEWDATA_KEYS = ("X", "W")
_PCOUNT_TYPES = {
    "lambda": "lambda",
    "abundance": "abundance",
    "p": "p",
    "detection": "detection",
    "fitted": "fitted",
}


def register_predictor(model: str, handler: Predictor) -> Predictor:
    """Register an experimental prediction handler for a model name.

    Parameters
    ----------
    model:
        Shared-core ``ModelSpec.model`` value, such as ``"pcount"``.
    handler:
        Callable receiving ``(result, prediction_type, kwargs)`` and returning
        the model-specific prediction object.

    Returns
    -------
    Callable
        The registered handler, allowing callers to retain or re-export it.
    """

    if not isinstance(model, str) or not model:
        raise ValueError("model must be a non-empty string")
    if not callable(handler):
        raise TypeError("handler must be callable")
    _PREDICTORS[model] = handler
    return handler


def predict(
    result: Any,
    type: str = "lambda",
    *,
    newdata: Any = None,
    new_site_data: Any = None,
    new_obs_data: Any = None,
    **kwargs: Any,
) -> Any:
    """Dispatch an experimental prediction request for a fitted result.

    Stage 4 supports only existing-data pcount predictions. Formula/newdata
    prediction is intentionally rejected until a later shared-core stage.
    """

    _reject_newdata(
        {
            "newdata": newdata,
            "new_site_data": new_site_data,
            "new_obs_data": new_obs_data,
            **kwargs,
        }
    )
    if not isinstance(type, str) or not type:
        raise ValueError("prediction type must be a non-empty string")
    model = _result_model(result)
    if model is None:
        raise TypeError(
            "unsupported result object for generic predict dispatch; "
            "expected a fitted result with shared-core model_spec metadata"
        )
    handler = _PREDICTORS.get(model)
    if handler is None:
        raise TypeError(f"unsupported result object for generic predict dispatch: model {model!r}")
    return handler(result, type, dict(kwargs))


def _reject_newdata(values: dict[str, Any]) -> None:
    requested = [key for key in _NEWDATA_KEYS if values.get(key) is not None]
    requested += [key for key in _MATRIX_NEWDATA_KEYS if values.get(key) is not None]
    if requested:
        names = ", ".join(requested)
        raise ValueError(
            f"generic predict dispatch supports existing-data predictions only; "
            f"{names} prediction is not implemented yet"
        )


def _result_model(result: Any) -> str | None:
    spec = getattr(result, "model_spec", None)
    model = getattr(spec, "model", None)
    if isinstance(model, str) and model:
        return model
    if _looks_like_pcount_result(result):
        return "pcount"
    return None


def _looks_like_pcount_result(result: Any) -> bool:
    return all(
        callable(getattr(result, name, None))
        for name in ("predict_lambda", "predict_abundance", "predict_detection", "fitted_counts")
    )


def _predict_pcount(result: Any, prediction_type: str, kwargs: dict[str, Any]) -> Any:
    canonical = _PCOUNT_TYPES.get(prediction_type)
    if canonical is None:
        supported = ", ".join(sorted(_PCOUNT_TYPES))
        raise ValueError(
            f"unsupported prediction type {prediction_type!r} for pcount result; "
            f"supported types are: {supported}"
        )
    _require_pcount_methods(result)
    if canonical == "lambda":
        return result.predict_lambda(**kwargs)
    if canonical == "abundance":
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise TypeError(
                "type='abundance' delegates to PCountResult.predict_abundance(), "
                f"which does not accept: {names}"
            )
        return result.predict_abundance()
    if canonical in {"p", "detection"}:
        return result.predict_detection(**kwargs)
    if kwargs:
        names = ", ".join(sorted(kwargs))
        raise TypeError(
            "type='fitted' delegates to PCountResult.fitted_counts(), "
            f"which does not accept: {names}"
        )
    return result.fitted_counts()


def _require_pcount_methods(result: Any) -> None:
    missing = [
        name
        for name in ("predict_lambda", "predict_abundance", "predict_detection", "fitted_counts")
        if not callable(getattr(result, name, None))
    ]
    if missing:
        names = ", ".join(missing)
        raise TypeError(
            f"unsupported pcount result object for generic predict dispatch; missing {names}"
        )


register_predictor("pcount", _predict_pcount)
