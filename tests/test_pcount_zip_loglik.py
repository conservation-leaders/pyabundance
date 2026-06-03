import math

import numpy as np
from pyabundance import _core


def inv_logit(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def logaddexp(a: float, b: float) -> float:
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def log_binom(y: int, n: int, p: float) -> float:
    return (
        math.lgamma(n + 1)
        - math.lgamma(y + 1)
        - math.lgamma(n - y + 1)
        + y * math.log(p)
        + (n - y) * math.log(1.0 - p)
    )


def log_zip(n: int, lam: float, psi: float) -> float:
    log_pois = n * math.log(lam) - lam - math.lgamma(n + 1)
    if n == 0:
        return logaddexp(math.log(psi), math.log1p(-psi) + log_pois)
    return math.log1p(-psi) + log_pois


def logsumexp(values: list[float]) -> float:
    m = max(values)
    return m + math.log(sum(math.exp(v - m) for v in values))


def reference_loglik(
    y: np.ndarray, X: np.ndarray, W: np.ndarray, theta: np.ndarray, K: int
) -> float:
    beta = theta[: X.shape[1]]
    detection = theta[X.shape[1] : X.shape[1] + W.shape[2]]
    psi = inv_logit(theta[-1])
    total = 0.0
    for i in range(y.shape[0]):
        lam = math.exp(float(X[i] @ beta))
        p = [inv_logit(float(W[i, j] @ detection)) for j in range(y.shape[1])]
        obs = [(j, int(y[i, j])) for j in range(y.shape[1]) if not np.isnan(y[i, j])]
        max_y = max((count for _, count in obs), default=0)
        terms = []
        for n in range(max_y, K + 1):
            value = log_zip(n, lam, psi)
            for j, count in obs:
                value += log_binom(count, n, p[j])
            terms.append(value)
        total += logsumexp(terms)
    return total


def test_zip_loglik_matches_slow_reference():
    y = np.array([[0.0, 0.0], [2.0, np.nan], [0.0, np.nan]], dtype=np.float64)
    X = np.array([[1.0, -0.2], [1.0, 0.4], [1.0, 0.1]], dtype=np.float64)
    W = np.array([[[1.0], [1.0]], [[1.0], [1.0]], [[1.0], [1.0]]], dtype=np.float64)
    theta = np.array([0.1, 0.3, -0.4, math.log(0.25 / 0.75)], dtype=np.float64)
    got = _core.pcount_zip_loglik(y, X, W, theta, 9)
    expected = reference_loglik(y, X, W, theta, 9)
    assert abs(got - expected) < 1.0e-8
