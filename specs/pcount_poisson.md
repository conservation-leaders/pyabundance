# Poisson N-mixture / pcount Model

## Model

For site `i = 1..M` and visit `j = 1..J`:

```text
N_i ~ Poisson(lambda_i)
y_ij | N_i ~ Binomial(N_i, p_ij)
log(lambda_i) = X_i beta
logit(p_ij) = W_ij alpha
```

## Input shapes

- `y`: sites × visits count matrix, passed as `float64`; `NaN` means missing visit.
- `X`: sites × abundance-parameter design matrix. Include the intercept column explicitly.
- `W`: sites × visits × detection-parameter design tensor.
- `K`: finite upper truncation for latent abundance summation.

## Parameter ordering

`theta = [beta..., alpha...]`, where `len(beta) = X.shape[1]` and `len(alpha) = W.shape[2]`.

## Likelihood

For one site:

```text
L_i = sum_{N=max(y_i observed)}^K Poisson(N | lambda_i)
      product_{j observed} Binomial(y_ij | N, p_ij)
```

Overall log-likelihood:

```text
logL = sum_i log(L_i)
```

The implementation evaluates terms in log space and uses log-sum-exp over latent `N`.

## Missing data

- `NaN` counts are skipped in the detection product.
- Non-missing counts must be non-negative integers.
- Infinite values are invalid.

## K truncation guidance

`K` must be at least the maximum observed count. Larger values reduce truncation error at additional cost. If a site has an observed count above `K`, the implementation raises a clear error.

## Validation expectations

- Shape consistency is checked at the Python and Rust boundaries.
- Stable inverse-logit is used for detection probabilities.
- Probabilities are clamped away from exact 0 and 1 only for finite logarithms.
