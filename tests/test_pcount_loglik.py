import math

import numpy as np
from pyabundance.pcount import pcount_loglik


def inv_logit(x):
    return 1.0 / (1.0 + math.exp(-x))


def log_factorial(n):
    return sum(math.log(k) for k in range(1, n + 1))


def log_poisson(n, lam):
    return n * math.log(lam) - lam - log_factorial(n)


def log_binom(y, n, p):
    return (
        log_factorial(n)
        - log_factorial(y)
        - log_factorial(n - y)
        + y * math.log(p)
        + (n - y) * math.log(1 - p)
    )


def logsumexp(values):
    m = max(values)
    return m + math.log(sum(math.exp(v - m) for v in values))


def reference_loglik(y, X, W, theta, K):
    beta = theta[: X.shape[1]]
    alpha = theta[X.shape[1] :]
    total = 0.0
    for i in range(y.shape[0]):
        lam = math.exp(float(X[i] @ beta))
        p = [inv_logit(float(W[i, j] @ alpha)) for j in range(y.shape[1])]
        obs = [(j, int(y[i, j])) for j in range(y.shape[1]) if not np.isnan(y[i, j])]
        max_y = max((count for _, count in obs), default=0)
        terms = []
        for n in range(max_y, K + 1):
            val = log_poisson(n, lam)
            for j, count in obs:
                val += log_binom(count, n, p[j])
            terms.append(val)
        total += logsumexp(terms)
    return total


def test_loglik_matches_slow_reference():
    y = np.array([[1.0, 0.0], [2.0, np.nan]], dtype=np.float64)
    X = np.array([[1.0, -0.2], [1.0, 0.4]], dtype=np.float64)
    W = np.array([[[1.0], [1.0]], [[1.0], [1.0]]], dtype=np.float64)
    theta = np.array([0.1, 0.3, -0.4], dtype=np.float64)
    got = pcount_loglik(y, X, W, theta, K=8)
    expected = reference_loglik(y, X, W, theta, K=8)
    assert abs(got - expected) < 1e-8
