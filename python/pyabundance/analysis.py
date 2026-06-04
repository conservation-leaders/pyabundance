from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from pyabundance.formula import build_pcount_matrices
from pyabundance.k_selection import KSuggestion, suggest_K
from pyabundance.model_selection import _dataframe_to_markdown, aic_table
from pyabundance.pcount import canonical_mixture, pcount
from pyabundance.reporting import _json_default
from pyabundance.result import PCountResult


@dataclass(frozen=True)
class PCountAnalysis:
    """Result object returned by :func:`analyze_pcount` guided workflows."""

    fits: dict[str, PCountResult]
    failed: dict[str, Any]
    table: pd.DataFrame
    best_model_name: str | None
    best_model: PCountResult | None
    K: int
    K_info: KSuggestion | None
    count_cols: list[Any]
    visit_labels: list[Any]
    abundance_formula: str
    detection_formula: str
    warnings: list[str]
    data_info: dict[str, Any]

    def __repr__(self) -> str:
        return (
            "PCountAnalysis("
            f"best_model_name={self.best_model_name!r}, "
            f"successful={len(self.fits)}, failed={len(self.failed)}, K={self.K})"
        )

    def compare_table(self) -> pd.DataFrame:
        """Return the AIC model-comparison table."""

        return self.table.copy()

    def model(self, name: str) -> PCountResult:
        """Return a fitted model by analysis name."""

        return self.fits[name]

    def diagnostics(self) -> dict[str, Any]:
        """Return diagnostics for successfully fitted candidate models."""

        return {name: fit.diagnostics() for name, fit in self.fits.items()}

    def posterior_abundance_summary(self, **kwargs: Any):
        """Return posterior abundance summary for the best model."""

        if self.best_model is None:
            raise ValueError("no successful model is available")
        return self.best_model.posterior_abundance_summary(**kwargs)

    def warning_summary(self) -> str:
        if not self.warnings:
            return "No warnings."
        return "\n".join(f"- {warning}" for warning in self.warnings)

    def summary(self) -> str:
        lines = [
            "PCountAnalysis",
            f"sites: {self.data_info.get('n_sites')}",
            f"visits: {self.data_info.get('n_visits')}",
            f"K: {self.K}",
            f"candidate models: {', '.join(self.data_info.get('candidate_models', []))}",
            f"successful models: {', '.join(self.fits) if self.fits else 'none'}",
            f"failed models: {', '.join(self.failed) if self.failed else 'none'}",
            f"best model: {self.best_model_name or 'none'}",
            f"abundance formula: {self.abundance_formula}",
            f"detection formula: {self.detection_formula}",
            f"visit labels: {self.visit_labels}",
        ]
        if not self.table.empty:
            lines.extend(["", "AIC table:", self.table.to_string(index=False)])
        if self.warnings:
            lines.extend(["", "Warnings:", self.warning_summary()])
        return "\n".join(lines)

    def explain(self) -> str:
        if self.best_model_name is None:
            return (
                "No candidate model fitted successfully. Inspect failed model messages and data "
                "validation warnings before interpreting results."
            )
        pieces = [
            f"The {self.best_model_name} model had the lowest AIC among the successful "
            "candidate models."
        ]
        mixtures = {name: fit.mixture for name, fit in self.fits.items()}
        poisson_names = [name for name, mix in mixtures.items() if mix == "poisson"]
        nb_names = [name for name, mix in mixtures.items() if mix == "negative_binomial"]
        zip_names = [name for name, mix in mixtures.items() if mix == "zero_inflated_poisson"]
        if poisson_names and nb_names and self.best_model_name in nb_names:
            pieces.append(
                "This suggests overdispersion relative to the Poisson model, but it is an "
                "AIC-based model comparison rather than proof of a biological mechanism."
            )
        if zip_names:
            if self.best_model_name in zip_names:
                pieces.append("The ZIP model was competitive by AIC.")
            pieces.append(
                "ZIP models can be weakly identified when many zeros can be explained by low "
                "abundance or low detection."
            )
        if self.failed:
            pieces.append(
                "Some candidate models failed and were excluded from best-model selection: "
                + ", ".join(self.failed.keys())
                + "."
            )
        if self.K_info is not None:
            pieces.append(self.K_info.message)
        pieces.append(
            "Posterior abundance summaries condition on fitted parameters and should be "
            "interpreted with diagnostics and uncertainty outputs."
        )
        pieces.append(
            "Inspect convergence, covariance, residual, and posterior predictive diagnostics."
        )
        return " ".join(pieces)

    def report(
        self,
        *,
        include_best_model: bool = True,
        include_posterior_abundance: bool = False,
    ) -> str:
        return self.to_markdown(
            include_best_model=include_best_model,
            include_posterior_abundance=include_posterior_abundance,
        )

    def to_markdown(
        self,
        path: str | Path | None = None,
        *,
        include_best_model: bool = True,
        include_posterior_abundance: bool = False,
    ) -> str:
        lines = [
            "# pyabundance guided pcount analysis",
            "",
            "## Summary",
            "",
            self.summary(),
            "",
            "## Candidate models",
            "",
            f"- requested candidates: {len(self.data_info.get('candidate_models', []))}",
            f"- successful candidates: {len(self.fits)}",
            f"- failed candidates: {len(self.failed)}",
            f"- best model: {self.best_model_name or 'none'}",
            f"- K: {self.K}",
            "",
            "## Explanation",
            "",
            self.explain(),
        ]
        if self.K_info is not None:
            lines.extend(["", "## K selection", "", self.K_info.message])
        if not self.table.empty:
            lines.extend(["", "## AIC table", "", _dataframe_to_markdown(self.table)])
        if include_best_model and self.best_model is not None:
            lines.extend(
                [
                    "",
                    "## Best model",
                    "",
                    f"- name: {self.best_model_name}",
                    f"- mixture: {self.best_model.mixture}",
                    f"- logLik: {self.best_model.loglik:.6g}",
                    f"- AIC: {self.best_model.aic:.6g}",
                    "",
                    "### Coefficients",
                    "",
                    _dataframe_to_markdown(self.best_model.coef_table(include_z=False)),
                ]
            )
            transformed = self.best_model.transformed_params()
            if not transformed.empty:
                lines.extend(
                    ["", "### Transformed parameters", "", _dataframe_to_markdown(transformed)]
                )
        if include_posterior_abundance and self.best_model is not None:
            posterior_summary = self.best_model.posterior_abundance_summary()
            assert isinstance(posterior_summary, pd.DataFrame)
            posterior = posterior_summary.head(10)
            lines.extend(
                [
                    "",
                    "## Posterior abundance",
                    "",
                    "Posterior abundance summaries condition on fitted parameters and do not "
                    "include full parameter uncertainty.",
                    "",
                    "First 10 site-level summaries:",
                    "",
                    _dataframe_to_markdown(posterior),
                ]
            )
        if self.failed:
            lines.extend(["", "## Failed models", ""])
            for name, failure in self.failed.items():
                lines.append(f"- {name}: {failure}")
        if self.warnings:
            lines.extend(["", "## Warnings", "", self.warning_summary()])
        text = "\n".join(lines) + "\n"
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text

    def export_report(
        self,
        path: str | Path,
        *,
        include_best_model: bool = True,
        include_posterior_abundance: bool = False,
    ) -> None:
        self.to_markdown(
            path,
            include_best_model=include_best_model,
            include_posterior_abundance=include_posterior_abundance,
        )

    def to_json(self, path: str | Path | None = None) -> str:
        payload = {
            "K": self.K,
            "K_info": self.K_info,
            "count_cols": self.count_cols,
            "visit_labels": self.visit_labels,
            "abundance_formula": self.abundance_formula,
            "detection_formula": self.detection_formula,
            "best_model_name": self.best_model_name,
            "table": self.table,
            "failed": self.failed,
            "warnings": self.warnings,
            "data_info": self.data_info,
        }
        text = json.dumps(payload, indent=2, default=_json_default) + "\n"
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text


def _candidate_mixtures(mixtures: Iterable[str], fit_zip: bool) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for mixture in mixtures:
        canonical = canonical_mixture(str(mixture))
        if canonical == "zero_inflated_poisson" and not fit_zip:
            continue
        name = {
            "poisson": "poisson",
            "negative_binomial": "negative_binomial",
            "zero_inflated_poisson": "zero_inflated_poisson",
        }[canonical]
        if name not in [existing for existing, _ in out]:
            out.append((name, canonical))
    if not out:
        raise ValueError("at least one candidate mixture is required")
    return out


def _start_for_candidate(start: Any, *, mixture: str, n_candidates: int) -> Any:
    if start is None:
        return None
    if isinstance(start, dict):
        starts_by_mixture: dict[str, Any] = {}
        for key, value in start.items():
            starts_by_mixture[canonical_mixture(str(key))] = value
        return starts_by_mixture.get(mixture)
    if n_candidates == 1:
        return start
    raise ValueError(
        "analyze_pcount received one start vector for multiple mixtures. Pass start as a "
        "dict keyed by mixture name, or use start=None."
    )


def analyze_pcount(
    *,
    site_data: pd.DataFrame,
    count_cols: list[str],
    abundance_formula: str = "~ 1",
    detection_formula: str = "~ 1",
    obs_data: pd.DataFrame | None = None,
    site_id_col: str | None = None,
    visit_col: str = "visit",
    visit_labels: list[Any] | str | None = "auto",
    mixtures: Iterable[str] = ("poisson", "negative_binomial", "zero_inflated_poisson"),
    K: int | str = "auto",
    se: bool = True,
    cov_method: str | None = "bfgs",
    method: str = "BFGS",
    start: Any = None,
    drop_missing_sites: bool = False,
    fit_zip: bool = True,
    report_warnings: bool = True,
) -> PCountAnalysis:
    """Run a guided pcount analysis with candidate models, AIC comparison, and report UX."""

    candidates = _candidate_mixtures(mixtures, fit_zip=fit_zip)
    if start is not None and not isinstance(start, dict) and len(candidates) > 1:
        raise ValueError(
            "analyze_pcount received one start vector for multiple mixtures. Pass start as a "
            "dict keyed by mixture name, or use start=None."
        )
    matrices = build_pcount_matrices(
        site_data=site_data,
        count_cols=count_cols,
        abundance_formula=abundance_formula,
        detection_formula=detection_formula,
        obs_data=obs_data,
        site_id_col=site_id_col,
        visit_col=visit_col,
        visit_labels=visit_labels,
        drop_missing_sites=drop_missing_sites,
    )
    warnings: list[str] = []
    if matrices.visit_label_message:
        warnings.append(matrices.visit_label_message)

    K_info: KSuggestion | None = None
    if K == "auto":
        K_suggestion = suggest_K(matrices.y, return_info=True)
        assert isinstance(K_suggestion, KSuggestion)
        K_info = K_suggestion
        K_int = K_suggestion.K
        warnings.append(K_suggestion.message)
    else:
        K_int = int(K)

    fits: dict[str, PCountResult] = {}
    failed: dict[str, Any] = {}
    for name, mixture in candidates:
        try:
            fit = pcount(
                matrices.y,
                matrices.X,
                matrices.W,
                K=K_int,
                mixture=mixture,
                start=_start_for_candidate(start, mixture=mixture, n_candidates=len(candidates)),
                method=method,
                se=se,
                cov_method=cov_method,
                abundance_column_names=matrices.abundance_column_names,
                detection_column_names=matrices.detection_column_names,
                site_ids=matrices.site_ids,
                visit_labels=matrices.visit_labels,
                abundance_formula=abundance_formula,
                detection_formula=detection_formula,
                from_dataframe=True,
                data_info=matrices.data_info,
                K_info=K_info,
                visit_label_source=matrices.visit_label_source,
                visit_label_message=matrices.visit_label_message,
            )
            if fit.success:
                fits[name] = fit
            else:
                failed[name] = fit.message
                if report_warnings:
                    warnings.append(f"{name} convergence warning: {fit.message}")
        except Exception as exc:  # keep guided workflow resilient
            failed[name] = str(exc)
            if report_warnings:
                warnings.append(f"{name} failed: {exc}")

    if fits:
        table = aic_table(fits, sort=True, include_warnings=True)
        best_model_name = str(table.iloc[0]["model"])
        best_model = fits[best_model_name]
        for name, fit in fits.items():
            for warning in fit.warnings or []:
                if warning not in warnings:
                    warnings.append(f"{name}: {warning}")
    else:
        table = pd.DataFrame(
            columns=[
                "rank",
                "model",
                "mixture",
                "n_params",
                "logLik",
                "AIC",
                "delta_AIC",
                "AIC_weight",
                "K",
                "success",
            ]
        )
        best_model_name = None
        best_model = None

    data_info: dict[str, Any] = dict(matrices.data_info)
    data_info.update(
        {
            "candidate_models": [name for name, _ in candidates],
            "visit_label_source": matrices.visit_label_source,
            "visit_label_message": matrices.visit_label_message,
        }
    )
    return PCountAnalysis(
        fits=fits,
        failed=failed,
        table=table,
        best_model_name=best_model_name,
        best_model=best_model,
        K=K_int,
        K_info=K_info,
        count_cols=list(matrices.count_cols),
        visit_labels=list(matrices.visit_labels),
        abundance_formula=abundance_formula,
        detection_formula=detection_formula,
        warnings=warnings,
        data_info=data_info,
    )
