import numpy as np
from pyabundance import _core
from pyabundance.pcount import pcount_loglik


def test_problem_object_loglik_matches_old_function():
    y = np.array([[1.0, 0.0], [2.0, np.nan]], dtype=np.float64)
    X = np.array([[1.0, -0.2], [1.0, 0.4]], dtype=np.float64)
    W = np.array([[[1.0], [1.0]], [[1.0], [1.0]]], dtype=np.float64)
    theta = np.array([0.1, 0.3, -0.4], dtype=np.float64)
    old = pcount_loglik(y, X, W, theta, K=8)
    problem = _core.PCountPoissonProblem(y, X, W, 8)
    assert problem.n_sites == 2
    assert problem.n_visits == 2
    assert problem.K == 8
    new = problem.loglik(theta)
    assert abs(old - new) < 1.0e-10
