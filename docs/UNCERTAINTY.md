# Uncertainty and Diagnostics

v0.5 adds explicit uncertainty tools for fitted pcount models. These tools are optional: `se=False` remains the default for speed.

## Standard errors

```python
fit = pcount(y, X, W, K=60, mixture="poisson", se=True, cov_method="bfgs")
print(fit.coef_table())
```

Supported covariance methods:

- `"bfgs"`: use SciPy's BFGS inverse-Hessian approximation when available.
- `"finite_difference"`: compute a central finite-difference Hessian of the negative log-likelihood at the optimum and invert it.
- `"none"`: do not estimate covariance or standard errors.

If covariance estimation fails, the fit is still returned. Standard errors are filled with `NaN`, and warnings are stored in `fit.warnings` and `fit.covariance_diagnostics`.

## Coefficient tables and confidence intervals

```python
table = fit.coef_table(level=0.95)
ci = fit.confint(level=0.95)
```

Intervals are Wald intervals on the unconstrained/link scale:

```text
theta_hat ± z * SE(theta_hat)
```

For negative-binomial and ZIP models, transformed parameters are available:

```python
fit.transformed_params()
```

- NB: `r = exp(log_r)` with intervals transformed from the log scale.
- ZIP: `psi = logistic(logit_psi)` with intervals transformed from the logit scale.

## Prediction confidence intervals

Expected abundance confidence intervals use the delta method on the log link:

```python
fit.predict_lambda(se=True, interval=True)
```

Detection confidence intervals use the delta method on the logit link:

```python
fit.predict_detection(se=True, interval=True)
```

For DataFrame/formula fits, stored design matrices are used when no new data are supplied.

## Residuals and fitted counts

```python
fit.fitted_counts()
fit.residuals(kind="raw")
fit.residuals(kind="pearson")
fit.sse()
fit.diagnostics()
```

Expected observed counts are `E[y_ij] = E[N_i] * p_ij`. Pearson residuals use an approximate marginal variance for observed counts.

## Parametric bootstrap

```python
boot = fit.parametric_bootstrap(nsim=20, statistic="sse", seed=1)
print(boot.summary())
print(boot.confint())
print(boot.gof_pvalue())
```

The v0.5 bootstrap is sequential (`n_jobs=1`). Each replicate simulates a new count matrix from the fitted model, refits the same model, and records parameters, log-likelihood, convergence, messages, and the requested statistic.

## Prediction intervals by simulation

```python
interval = fit.prediction_interval(kind="observed_counts", nsim=100, seed=1)
```

This simulates observed count matrices from the fitted model without refitting, then returns site × visit lower, median, and upper percentiles.

## Limitations

- Wald standard errors are asymptotic approximations and can be unreliable with weak data.
- ZIP models can be weakly identified because low detection, low abundance, and structural zeros can all produce many zeros.
- Finite-difference Hessians can be slow and numerically sensitive.
- Bootstrap is usually more robust but computationally expensive.
- Prediction and confidence intervals are not a substitute for model checking.
- v0.5 does not implement parallel bootstrap, random effects, offsets, or open/dynamic N-mixture models.

## Posterior abundance note

See `docs/POSTERIOR_ABUNDANCE.md` for ranef-like latent abundance summaries and posterior predictive checks. These condition on fitted parameters and should be interpreted separately from uncertainty intervals over fitted coefficients.
