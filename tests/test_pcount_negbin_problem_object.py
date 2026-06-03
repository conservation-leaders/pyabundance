import math

import numpy as np
import pytest
from pyabundance import _core


def test_negbin_problem_object_matches_raw_function():
    y = np.array([[1.0, 0.0], [2.0, np.nan]], dtype=np.float64)
    X = np.array([[1.0, -0.2], [1.0, 0.4]], dtype=np.float64)
    W = np.array([[[1.0], [1.0]], [[1.0], [1.0]]], dtype=np.float64)
    theta = np.array([0.1, 0.3, -0.4, math.log(1.7)], dtype=np.float64)
    problem = _core.PCountNegBinProblem(y, X, W, 9)
    assert problem.n_sites == 2
    assert problem.n_visits == 2
    assert problem.K == 9
    raw = _core.pcount_negbin_loglik(y, X, W, theta, 9)
    cached = problem.loglik(theta)
    assert abs(raw - cached) < 1.0e-10
    with pytest.raises(ValueError, match="theta length"):
        problem.loglik(theta[:-1])
