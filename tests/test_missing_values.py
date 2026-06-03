import numpy as np
import pytest
from pyabundance.pcount import pcount_loglik


def test_nan_visits_are_skipped():
    X = np.ones((1, 1), dtype=np.float64)
    W_one = np.ones((1, 1, 1), dtype=np.float64)
    W_two = np.ones((1, 2, 1), dtype=np.float64)
    theta = np.zeros(2, dtype=np.float64)
    with_missing = pcount_loglik(np.array([[1.0, np.nan]]), X, W_two, theta, K=6)
    without_missing = pcount_loglik(np.array([[1.0]]), X, W_one, theta, K=6)
    assert abs(with_missing - without_missing) < 1e-12


def test_non_integer_counts_raise_value_error():
    y = np.array([[1.5]], dtype=np.float64)
    X = np.ones((1, 1), dtype=np.float64)
    W = np.ones((1, 1, 1), dtype=np.float64)
    theta = np.zeros(2, dtype=np.float64)
    with pytest.raises(ValueError, match="non-negative integers"):
        pcount_loglik(y, X, W, theta, K=6)
