from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import norm

from pyabundance import _core

MixtureName = Literal["poisson", "negative_binomial", "zero_inflated_poisson"]

if TYPE_CHECKING:
    from pyabundance.core.specs import ModelSpec, ParameterBlock


def _unique_preserving_order(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value)
        if text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _logistic_array(x: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.where(x >= 0.0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def _logistic(x: float) -> float:
    return float(_logistic_array(np.asarray(x, dtype=np.float64)))


def _matrix_diag_quadratic(
    design: NDArray[np.float64], cov: NDArray[np.float64]
) -> NDArray[np.float64]:
    return np.einsum("ij,jk,ik->i", design, cov, design, optimize=True)


@dataclass(frozen=True)
class PCountResult:
    params: NDArray[np.float64]
    n_abundance_params: int
    n_detection_params: int
    loglik: float
    success: bool
    message: str
    K: int
    mixture: MixtureName
    X: NDArray[np.float64]
    W: NDArray[np.float64]
    method: str
    nfev: int | None
    nit: int | None
    y: NDArray[np.float64]
    abundance_column_names: list[str] | None = None
    detection_column_names: list[str] | None = None
    site_ids: list[Any] | None = None
    visit_labels: list[Any] | None = None
    abundance_formula: str | None = None
    detection_formula: str | None = None
    from_dataframe: bool = False
    data_info: dict[str, int] | None = None
    K_info: Any | None = None
    visit_label_source: str | None = None
    visit_label_message: str | None = None
    covariance: NDArray[np.float64] | None = None
    standard_errors: NDArray[np.float64] | None = None
    cov_method: str = "none"
    covariance_diagnostics: dict[str, Any] | None = None
    param_names: list[str] | None = None
    warnings: list[str] | None = None
    objective_value: float | None = None
    _problem: Any | None = None

    def __repr__(self) -> str:
        status = "success" if self.success else "failed"
        se_status = "available" if self.has_covariance else "not_available"
        return (
            f"PCountResult(mixture={self.mixture!r}, loglik={self.loglik:.6g}, "
            f"aic={self.aic:.6g}, K={self.K}, status={status}, se={se_status})"
        )

    @property
    def beta(self) -> NDArray[np.float64]:
        return self.params[: self.n_abundance_params].copy()

    @property
    def detection(self) -> NDArray[np.float64]:
        start = self.n_abundance_params
        end = start + self.n_detection_params
        return self.params[start:end].copy()

    @property
    def alpha(self) -> NDArray[np.float64]:
        """Backward-compatible alias for detection coefficients."""
        return self.detection

    @property
    def log_r(self) -> float | None:
        if self.mixture != "negative_binomial":
            return None
        return float(self.params[self.n_abundance_params + self.n_detection_params])

    @property
    def r(self) -> float | None:
        log_r = self.log_r
        if log_r is None:
            return None
        return float(np.exp(log_r))

    @property
    def logit_psi(self) -> float | None:
        if self.mixture != "zero_inflated_poisson":
            return None
        return float(self.params[self.n_abundance_params + self.n_detection_params])

    @property
    def psi(self) -> float | None:
        logit_psi = self.logit_psi
        if logit_psi is None:
            return None
        return _logistic(logit_psi)

    @property
    def aic(self) -> float:
        return 2.0 * self.params.size - 2.0 * self.loglik

    def _resolved_param_names(self) -> list[str]:
        if self.param_names is not None and len(self.param_names) == self.params.size:
            return list(self.param_names)
        return self._default_param_names()

    @property
    def parameter_blocks(self) -> tuple[ParameterBlock, ...]:
        """Shared-core parameter blocks for the fitted pcount coefficient vector."""

        from pyabundance.core.specs import ParameterBlock

        names = self._resolved_param_names()
        abundance_stop = self.n_abundance_params
        detection_stop = abundance_stop + self.n_detection_params
        blocks = [
            ParameterBlock(
                name="lambda",
                start=0,
                stop=abundance_stop,
                link="log",
                columns=tuple(names[:abundance_stop]),
                process="lambda",
            ),
            ParameterBlock(
                name="p",
                start=abundance_stop,
                stop=detection_stop,
                link="logit",
                columns=tuple(names[abundance_stop:detection_stop]),
                process="p",
            ),
        ]
        if self.mixture == "negative_binomial":
            blocks.append(
                ParameterBlock(
                    name="r",
                    start=detection_stop,
                    stop=detection_stop + 1,
                    link="log",
                    columns=("log_r",),
                    process="r",
                )
            )
        elif self.mixture == "zero_inflated_poisson":
            blocks.append(
                ParameterBlock(
                    name="psi",
                    start=detection_stop,
                    stop=detection_stop + 1,
                    link="logit",
                    columns=("logit_psi",),
                    process="psi",
                )
            )
        return tuple(blocks)

    @property
    def model_spec(self) -> ModelSpec:
        """Experimental shared-core model metadata for this pcount fit."""

        from pyabundance.core.specs import ModelSpec, ProcessSpec

        names = self._resolved_param_names()
        abundance_stop = self.n_abundance_params
        detection_stop = abundance_stop + self.n_detection_params
        processes = {
            "lambda": ProcessSpec(
                name="lambda",
                formula=self.abundance_formula,
                link="log",
                level="site",
                columns=tuple(names[:abundance_stop]),
            ),
            "p": ProcessSpec(
                name="p",
                formula=self.detection_formula,
                link="logit",
                level="observation",
                columns=tuple(names[abundance_stop:detection_stop]),
            ),
        }
        if self.mixture == "negative_binomial":
            processes["r"] = ProcessSpec(
                name="r",
                formula=None,
                link="log",
                level="global",
                columns=("log_r",),
            )
        elif self.mixture == "zero_inflated_poisson":
            processes["psi"] = ProcessSpec(
                name="psi",
                formula=None,
                link="logit",
                level="global",
                columns=("logit_psi",),
            )
        n_sites = int(self.y.shape[0]) if self.y.ndim > 0 else 0
        n_visits = int(self.y.shape[1]) if self.y.ndim > 1 else 0
        return ModelSpec(
            model="pcount",
            response="count",
            processes=processes,
            parameter_blocks=self.parameter_blocks,
            metadata={
                "mixture": self.mixture,
                "K": int(self.K),
                "from_dataframe": bool(self.from_dataframe),
                "n_sites": n_sites,
                "n_visits": n_visits,
            },
        )

    @property
    def has_covariance(self) -> bool:
        return self.covariance is not None and bool(
            (self.covariance_diagnostics or {}).get("available", False)
        )

    def vcov(self) -> NDArray[np.float64]:
        if self.covariance is None:
            raise ValueError("covariance is unavailable; fit with se=True")
        return self.covariance.copy()

    def _require_standard_errors(self) -> NDArray[np.float64]:
        if self.standard_errors is None or not np.any(np.isfinite(self.standard_errors)):
            raise ValueError("standard errors are unavailable; fit with se=True")
        return self.standard_errors.copy()

    def _require_covariance(self) -> NDArray[np.float64]:
        if self.covariance is None:
            raise ValueError("covariance is unavailable; fit with se=True")
        return self.covariance.copy()

    def coef_table(
        self,
        level: float = 0.95,
        include_z: bool = True,
        include_p: bool = False,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]]:
        se = (
            self.standard_errors.copy()
            if self.standard_errors is not None
            else np.full(self.params.size, np.nan, dtype=np.float64)
        )
        zcrit = float(norm.ppf(1.0 - (1.0 - level) / 2.0))
        lower = self.params - zcrit * se
        upper = self.params + zcrit * se
        rows = {
            "parameter": self.param_names or self._default_param_names(),
            "block": self._param_blocks(),
            "estimate": self.params,
            "std.error": se,
            "lower": lower,
            "upper": upper,
        }
        z_values = np.divide(
            self.params,
            se,
            out=np.full_like(self.params, np.nan),
            where=np.isfinite(se) & (se > 0.0),
        )
        if include_z:
            rows["z"] = z_values
        if include_p:
            rows["p"] = 2.0 * norm.sf(np.abs(z_values))
        table = pd.DataFrame(rows)
        if as_dataframe:
            return table
        return table.to_dict(orient="records")

    def coefficients(self, **kwargs: Any) -> pd.DataFrame | list[dict[str, Any]]:
        """Alias for :meth:`coef_table`."""

        return self.coef_table(**kwargs)

    def confint(
        self, level: float = 0.95, method: str = "wald", scale: str = "link"
    ) -> pd.DataFrame:
        if method != "wald":
            raise ValueError("only Wald confidence intervals are implemented")
        if scale != "link":
            raise ValueError("only link-scale coefficient intervals are implemented")
        table = self.coef_table(level=level, include_z=False, include_p=False, as_dataframe=True)
        assert isinstance(table, pd.DataFrame)
        return table[["parameter", "estimate", "lower", "upper"]]

    def transformed_params(self, level: float = 0.95) -> pd.DataFrame:
        if self.mixture == "poisson":
            return pd.DataFrame(columns=["parameter", "estimate", "lower", "upper"])
        ci = self.confint(level=level)
        if self.mixture == "negative_binomial":
            row = ci.loc[ci["parameter"] == "log_r"]
            if row.empty:
                return pd.DataFrame(columns=["parameter", "estimate", "lower", "upper"])
            return pd.DataFrame(
                {
                    "parameter": ["r"],
                    "estimate": [self.r],
                    "lower": [float(np.exp(row["lower"].iloc[0]))],
                    "upper": [float(np.exp(row["upper"].iloc[0]))],
                }
            )
        row = ci.loc[ci["parameter"] == "logit_psi"]
        if row.empty:
            return pd.DataFrame(columns=["parameter", "estimate", "lower", "upper"])
        return pd.DataFrame(
            {
                "parameter": ["psi"],
                "estimate": [self.psi],
                "lower": [_logistic(float(row["lower"].iloc[0]))],
                "upper": [_logistic(float(row["upper"].iloc[0]))],
            }
        )

    def _default_param_names(self) -> list[str]:
        abundance_names = (
            self.abundance_column_names
            if self.abundance_column_names
            and len(self.abundance_column_names) == self.n_abundance_params
            else [f"abundance[{i}]" for i in range(self.n_abundance_params)]
        )
        detection_names = (
            self.detection_column_names
            if self.detection_column_names
            and len(self.detection_column_names) == self.n_detection_params
            else [f"detection[{i}]" for i in range(self.n_detection_params)]
        )
        names = list(abundance_names) + list(detection_names)
        if self.mixture == "negative_binomial":
            names.append("log_r")
        if self.mixture == "zero_inflated_poisson":
            names.append("logit_psi")
        return names

    def _param_blocks(self) -> list[str]:
        blocks = ["abundance"] * self.n_abundance_params
        blocks += ["detection"] * self.n_detection_params
        if self.mixture in {"negative_binomial", "zero_inflated_poisson"}:
            blocks.append("extra")
        return blocks

    def predict_lambda(
        self,
        X: NDArray[np.float64] | None = None,
        *,
        se: bool = False,
        interval: bool = False,
        level: float = 0.95,
        as_dataframe: bool = False,
    ) -> NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame:
        x_arr = self.X if X is None else np.ascontiguousarray(X, dtype=np.float64)
        values = np.asarray(_core.pcount_poisson_predict_lambda(x_arr, self.beta), dtype=np.float64)
        if not se and not interval:
            if as_dataframe:
                df_data: dict[str, Any] = {"estimate": values}
                if self.site_ids is not None and len(self.site_ids) == values.size:
                    df_data["site_id"] = self.site_ids
                columns = ["site_id"] if "site_id" in df_data else []
                columns.append("estimate")
                return pd.DataFrame(df_data)[columns]
            return values
        cov = self._require_covariance()[: self.n_abundance_params, : self.n_abundance_params]
        eta = x_arr @ self.beta
        var_eta = np.maximum(_matrix_diag_quadratic(x_arr, cov), 0.0)
        se_eta = np.sqrt(var_eta)
        zcrit = float(norm.ppf(1.0 - (1.0 - level) / 2.0))
        out: dict[str, NDArray[np.float64]] = {"estimate": values}
        if se:
            out["se"] = values * se_eta
        if interval:
            out["lower"] = np.exp(eta - zcrit * se_eta)
            out["upper"] = np.exp(eta + zcrit * se_eta)
        if as_dataframe:
            interval_data: dict[str, Any] = {"estimate": out["estimate"]}
            if self.site_ids is not None and len(self.site_ids) == values.size:
                interval_data["site_id"] = self.site_ids
            for key in ["se", "lower", "upper"]:
                if key in out:
                    interval_data[key] = out[key]
            columns = ["site_id"] if "site_id" in interval_data else []
            columns += [key for key in ["estimate", "se", "lower", "upper"] if key in interval_data]
            return pd.DataFrame(interval_data)[columns]
        return out

    def predict_abundance(self, new_site_data: Any = None) -> NDArray[np.float64]:
        if new_site_data is not None:
            raise NotImplementedError(
                "new data prediction from formulas is not implemented in v0.5"
            )
        return np.asarray(self.predict_lambda(), dtype=np.float64)

    def predict_detection(
        self,
        W: NDArray[np.float64] | None = None,
        *,
        se: bool = False,
        interval: bool = False,
        level: float = 0.95,
        as_dataframe: bool = False,
    ) -> NDArray[np.float64] | dict[str, NDArray[np.float64]] | pd.DataFrame:
        w_arr = self.W if W is None else np.ascontiguousarray(W, dtype=np.float64)
        values = np.asarray(
            _core.pcount_poisson_predict_detection(w_arr, self.detection), dtype=np.float64
        )
        values = values.reshape(w_arr.shape[0], w_arr.shape[1])
        if not se and not interval:
            if as_dataframe:
                rows = []
                site_ids = self.site_ids or list(range(values.shape[0]))
                visit_labels = self.visit_labels or list(range(values.shape[1]))
                for i, site_id in enumerate(site_ids):
                    for j, visit in enumerate(visit_labels):
                        rows.append({"site_id": site_id, "visit": visit, "estimate": values[i, j]})
                return pd.DataFrame(rows)
            return values
        start = self.n_abundance_params
        end = start + self.n_detection_params
        cov = self._require_covariance()[start:end, start:end]
        flat_w = w_arr.reshape(-1, w_arr.shape[2])
        eta = flat_w @ self.detection
        p = _logistic_array(eta).reshape(w_arr.shape[0], w_arr.shape[1])
        var_eta = np.maximum(_matrix_diag_quadratic(flat_w, cov), 0.0).reshape(p.shape)
        se_eta = np.sqrt(var_eta)
        zcrit = float(norm.ppf(1.0 - (1.0 - level) / 2.0))
        out: dict[str, NDArray[np.float64]] = {"estimate": values}
        if se:
            out["se"] = p * (1.0 - p) * se_eta
        if interval:
            out["lower"] = _logistic_array(eta - zcrit * se_eta.ravel()).reshape(p.shape)
            out["upper"] = _logistic_array(eta + zcrit * se_eta.ravel()).reshape(p.shape)
        if as_dataframe:
            rows = []
            site_ids = self.site_ids or list(range(p.shape[0]))
            visit_labels = self.visit_labels or list(range(p.shape[1]))
            for i, site_id in enumerate(site_ids):
                for j, visit in enumerate(visit_labels):
                    row: dict[str, Any] = {"site_id": site_id, "visit": visit}
                    for key, arr in out.items():
                        row[key] = float(arr[i, j])
                    rows.append(row)
            return pd.DataFrame(rows)
        return out

    def latent_mean(self) -> NDArray[np.float64]:
        lam = np.asarray(self.predict_lambda(), dtype=np.float64)
        if self.mixture == "zero_inflated_poisson":
            return lam * (1.0 - float(self.psi or 0.0))
        return lam

    def latent_variance(self) -> NDArray[np.float64]:
        lam = np.asarray(self.predict_lambda(), dtype=np.float64)
        if self.mixture == "poisson":
            return lam
        if self.mixture == "negative_binomial":
            return lam + lam**2 / float(self.r or np.nan)
        psi = float(self.psi or 0.0)
        return (1.0 - psi) * lam * (1.0 + psi * lam)

    def fitted_counts(self) -> NDArray[np.float64]:
        return self.latent_mean()[:, None] * np.asarray(self.predict_detection(), dtype=np.float64)

    def residuals(self, kind: str = "raw") -> NDArray[np.float64]:
        expected = self.fitted_counts()
        residual = self.y - expected
        residual[np.isnan(self.y)] = np.nan
        if kind == "raw":
            return residual
        if kind != "pearson":
            raise ValueError("kind must be 'raw' or 'pearson'")
        p = np.asarray(self.predict_detection(), dtype=np.float64)
        mean_n = self.latent_mean()
        var_n = self.latent_variance()
        var_y = mean_n[:, None] * p * (1.0 - p) + var_n[:, None] * p**2
        denom = np.sqrt(np.maximum(var_y, np.finfo(float).tiny))
        out = residual / denom
        out[np.isnan(self.y)] = np.nan
        return out

    def sse(self, kind: str = "raw") -> float:
        residual = self.residuals(kind=kind)
        return float(np.nansum(residual**2))

    def abundance_dataframe(
        self,
        *,
        se: bool = False,
        interval: bool = False,
        level: float = 0.95,
        include_posterior: bool = False,
    ) -> pd.DataFrame:
        """Return expected abundance predictions as a site-level DataFrame."""
        out = pd.DataFrame(
            self.predict_lambda(se=se, interval=interval, level=level, as_dataframe=True)
        )
        if not include_posterior:
            return out
        out = out.rename(
            columns={
                "estimate": "predicted_lambda",
                "lower": "predicted_lambda_lower",
                "upper": "predicted_lambda_upper",
                "se": "predicted_lambda_se",
            }
        )
        posterior = pd.DataFrame(self.posterior_abundance_summary(level=level)).rename(
            columns={
                "posterior_mean": "posterior_mean_N",
                "lower": "posterior_lower",
                "upper": "posterior_upper",
            }
        )
        merge_cols = ["site_index"]
        out = out.copy()
        if "site_id" in out.columns and "site_id" in posterior.columns:
            out["site_index"] = range(len(out))
            merge_cols = ["site_index", "site_id"]
        elif "site_id" not in out.columns:
            out.insert(0, "site_index", range(len(out)))
        keep = merge_cols + [
            "observed_max_count",
            "posterior_mean_N",
            "posterior_lower",
            "posterior_upper",
            "posterior_sd",
        ]
        return out.merge(posterior[keep], on=merge_cols, how="left")

    def detection_dataframe(
        self, *, se: bool = False, interval: bool = False, level: float = 0.95
    ) -> pd.DataFrame:
        """Return detection predictions as a site × visit DataFrame."""
        return self.predict_detection(se=se, interval=interval, level=level, as_dataframe=True)

    def fitted_counts_dataframe(self) -> pd.DataFrame:
        """Return observed counts, fitted expected counts, and residuals in long format."""
        fitted = self.fitted_counts()
        raw = self.residuals(kind="raw")
        pearson = self.residuals(kind="pearson")
        site_ids = self.site_ids or list(range(self.y.shape[0]))
        visit_labels = self.visit_labels or list(range(self.y.shape[1]))
        rows = []
        for i, site_id in enumerate(site_ids):
            for j, visit in enumerate(visit_labels):
                rows.append(
                    {
                        "site_id": site_id,
                        "visit": visit,
                        "observed": self.y[i, j],
                        "fitted": fitted[i, j],
                        "raw_residual": raw[i, j],
                        "pearson_residual": pearson[i, j],
                        "missing": bool(np.isnan(self.y[i, j])),
                    }
                )
        return pd.DataFrame(rows)

    def residuals_dataframe(self, kind: str = "raw") -> pd.DataFrame:
        """Return residuals in long site × visit format."""
        residual = self.residuals(kind=kind)
        site_ids = self.site_ids or list(range(self.y.shape[0]))
        visit_labels = self.visit_labels or list(range(self.y.shape[1]))
        rows = []
        for i, site_id in enumerate(site_ids):
            for j, visit in enumerate(visit_labels):
                rows.append({"site_id": site_id, "visit": visit, "residual": residual[i, j]})
        return pd.DataFrame(rows)

    def to_report(self, *, include_posterior_abundance: bool = False) -> dict[str, Any]:
        from pyabundance.reporting import model_report

        return model_report(self, include_posterior_abundance=include_posterior_abundance)

    def report(self, *, include_posterior_abundance: bool = False) -> dict[str, Any]:
        return self.to_report(include_posterior_abundance=include_posterior_abundance)

    def to_markdown(self, *, include_posterior_abundance: bool = False) -> str:
        from pyabundance.reporting import report_markdown

        return report_markdown(self, include_posterior_abundance=include_posterior_abundance)

    def export_summary(
        self,
        path: str,
        *,
        format: str | None = None,
        include_posterior_abundance: bool = False,
    ) -> None:
        from pyabundance.reporting import export_model_report

        export_model_report(
            self,
            path,
            format=format,
            include_posterior_abundance=include_posterior_abundance,
        )

    def posterior_abundance(
        self, *, return_support: bool = False, normalize: bool = True
    ) -> NDArray[np.float64] | tuple[NDArray[np.int64], NDArray[np.float64]]:
        from pyabundance.ranef import posterior_abundance_matrix

        probs = posterior_abundance_matrix(self)
        if normalize:
            row_sums = probs.sum(axis=1, keepdims=True)
            probs = np.divide(probs, row_sums, out=np.zeros_like(probs), where=row_sums > 0.0)
        if return_support:
            return np.arange(self.K + 1, dtype=np.int64), probs
        return probs

    def posterior_abundance_summary(
        self, *, level: float = 0.95, as_dataframe: bool = True
    ) -> pd.DataFrame | list[dict[str, Any]]:
        from pyabundance.ranef import posterior_abundance_summary

        summary = posterior_abundance_summary(self, level=level)
        if as_dataframe:
            return summary
        return summary.to_dict(orient="records")

    def ranef(self, *, level: float = 0.95) -> pd.DataFrame:
        return self.posterior_abundance_summary(level=level)

    def posterior_abundance_dataframe(self, *, long: bool = False) -> pd.DataFrame:
        from pyabundance.ranef import posterior_abundance_long_dataframe

        if long:
            return posterior_abundance_long_dataframe(self)
        return self.posterior_abundance_summary()

    def posterior_abundance_samples(
        self, nsim: int = 100, seed: int | None = None
    ) -> NDArray[np.int64]:
        from pyabundance.ranef import posterior_abundance_samples

        return posterior_abundance_samples(self, nsim=nsim, seed=seed)

    def total_abundance_posterior(
        self, nsim: int = 1000, seed: int | None = None, level: float = 0.95
    ):
        from pyabundance.ranef import total_abundance_posterior

        return total_abundance_posterior(self, nsim=nsim, seed=seed, level=level)

    def total_abundance_summary(
        self, nsim: int = 1000, seed: int | None = None, level: float = 0.95
    ) -> str:
        return self.total_abundance_posterior(nsim=nsim, seed=seed, level=level).summary()

    def posterior_predictive_counts(
        self, nsim: int = 100, seed: int | None = None
    ) -> NDArray[np.float64]:
        from pyabundance.ranef import posterior_predictive_counts

        return posterior_predictive_counts(self, nsim=nsim, seed=seed)

    def posterior_predictive_check(
        self, statistic: str = "sse", nsim: int = 100, seed: int | None = None
    ) -> dict[str, Any]:
        from pyabundance.ranef import posterior_predictive_check

        return posterior_predictive_check(self, statistic=statistic, nsim=nsim, seed=seed)

    def diagnostics(self) -> dict[str, Any]:
        from pyabundance.diagnostics import result_diagnostics

        return result_diagnostics(self)

    def warning_summary(self) -> str:
        warnings = _unique_preserving_order(list(self.warnings or []))
        cov_warnings = _unique_preserving_order(
            list((self.covariance_diagnostics or {}).get("warnings", []))
        )
        lines = [f"- {warning}" for warning in warnings]
        lines.extend(
            f"- covariance: {warning}" for warning in cov_warnings if warning not in warnings
        )
        if not lines:
            return "No warnings."
        return "\n".join(lines)

    def parametric_bootstrap(self, *args: Any, **kwargs: Any):
        from pyabundance.bootstrap import parametric_bootstrap

        return parametric_bootstrap(self, *args, **kwargs)

    def prediction_interval(
        self,
        kind: str = "observed_counts",
        nsim: int = 100,
        level: float = 0.95,
        seed: int | None = None,
    ) -> dict[str, Any]:
        if kind != "observed_counts":
            raise ValueError("only kind='observed_counts' is implemented in v0.5")
        if nsim <= 0:
            raise ValueError("nsim must be positive")
        from pyabundance.bootstrap import _simulate_from_fit

        rng = np.random.default_rng(seed)
        sims = np.empty((nsim, self.y.shape[0], self.y.shape[1]), dtype=np.float64)
        for i in range(nsim):
            sim_seed = int(rng.integers(0, np.iinfo(np.int32).max))
            sims[i] = _simulate_from_fit(self, seed=sim_seed)
        alpha = 1.0 - level
        return {
            "lower": np.nanpercentile(sims, 100.0 * alpha / 2.0, axis=0),
            "median": np.nanpercentile(sims, 50.0, axis=0),
            "upper": np.nanpercentile(sims, 100.0 * (1.0 - alpha / 2.0), axis=0),
            "level": level,
            "kind": kind,
        }

    def summary(self) -> str:
        info = self.data_info or {
            "n_sites": int(self.X.shape[0]),
            "n_visits": int(self.W.shape[1]),
            "n_abundance_params": int(self.n_abundance_params),
            "n_detection_params": int(self.n_detection_params),
        }
        lines = [
            f"PCountResult(mixture='{self.mixture}')",
            f"sites: {info.get('n_sites')}",
            f"visits: {info.get('n_visits')}",
            f"K: {self.K}",
            f"success: {self.success}",
            f"method: {self.method}",
            f"function evaluations: {self.nfev}",
            f"iterations: {self.nit}",
            f"message: {self.message}",
            f"logLik: {self.loglik:.6g}",
            f"AIC: {self.aic:.6g}",
            f"covariance method: {self.cov_method}",
        ]
        if self.from_dataframe:
            lines.extend(
                [
                    f"abundance formula: {self.abundance_formula}",
                    f"detection formula: {self.detection_formula}",
                ]
            )
        if self.visit_labels is not None:
            lines.append(f"visit labels: {self.visit_labels}")
        if self.visit_label_message:
            lines.append(self.visit_label_message)
        table = self.coef_table(include_z=False, as_dataframe=True)
        assert isinstance(table, pd.DataFrame)
        lines.append("coefficients:")
        has_se = np.any(np.isfinite(table["std.error"].to_numpy(dtype=np.float64)))
        for _, row in table.iterrows():
            if has_se:
                lines.append(
                    f"  {row['block']} {row['parameter']}: estimate={row['estimate']:.6g}, "
                    f"std.error={row['std.error']:.6g}, "
                    f"95% CI=({row['lower']:.6g}, {row['upper']:.6g})"
                )
            else:
                lines.append(f"  {row['block']} {row['parameter']}: {row['estimate']:.6g}")
        if self.mixture == "negative_binomial":
            lines.extend([f"log_r: {self.log_r:.6g}", f"r: {self.r:.6g}"])
        if self.mixture == "zero_inflated_poisson":
            lines.extend([f"logit_psi: {self.logit_psi:.6g}", f"psi: {self.psi:.6g}"])
        cov_warnings = _unique_preserving_order(
            list((self.covariance_diagnostics or {}).get("warnings", []))
        )
        if cov_warnings:
            lines.append("covariance warnings: " + "; ".join(str(w) for w in cov_warnings))
        if self.warnings:
            model_warnings = _unique_preserving_order(list(self.warnings))
            lines.append("warnings: " + "; ".join(str(w) for w in model_warnings))
        return "\n".join(lines)
