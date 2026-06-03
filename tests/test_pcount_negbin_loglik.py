import math

import numpy as np
from pyabundance import _core


def inv_logit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def log_factorial(n: int) -> float:
    return math.lgamma(n + 1)


def log_binom(y: int, n: int, p: float) -> float:
    return (
        log_factorial(n)
        - log_factorial(y)
        - log_factorial(n - y)
        + y * math.log(p)
        + (n - y) * math.log(1 - p)
    )


def log_nb(n: int, mu: float, r: float) -> float:
    return (
        math.lgamma(n + r)
        - math.lgamma(r)
        - math.lgamma(n + 1)
        + r * (math.log(r) - math.log(r + mu))
        + n * (math.log(mu) - math.log(r + mu))
    )


def logsumexp(values: list[float]) -> float:
    m = max(values)
    return m + math.log(sum(math.exp(v - m) for v in values))


def reference_loglik(
    y: np.ndarray, X: np.ndarray, W: np.ndarray, theta: np.ndarray, K: int
) -> float:
    beta = theta[: X.shape[1]]
    detection = theta[X.shape[1] : X.shape[1] + W.shape[2]]
    r = math.exp(theta[-1])
    total = 0.0
    for i in range(y.shape[0]):
        mu = math.exp(float(X[i] @ beta))
        p = [inv_logit(float(W[i, j] @ detection)) for j in range(y.shape[1])]
        obs = [(j, int(y[i, j])) for j in range(y.shape[1]) if not np.isnan(y[i, j])]
        max_y = max((count for _, count in obs), default=0)
        terms = []
        for n in range(max_y, K + 1):
            value = log_nb(n, mu, r)
            for j, count in obs:
                value += log_binom(count, n, p[j])
            terms.append(value)
        total += logsumexp(terms)
    return total


def test_negbin_loglik_matches_slow_reference():
    y = np.array([[1.0, 0.0], [2.0, np.nan]], dtype=np.float64)
    X = np.array([[1.0, -0.2], [1.0, 0.4]], dtype=np.float64)
    W = np.array([[[1.0], [1.0]], [[1.0], [1.0]]], dtype=np.float64)
    theta = np.array([0.1, 0.3, -0.4, math.log(1.7)], dtype=np.float64)
    got = _core.pcount_negbin_loglik(y, X, W, theta, 9)
    expected = reference_loglik(y, X, W, theta, 9)
    assert abs(got - expected) < 1.0e-8
