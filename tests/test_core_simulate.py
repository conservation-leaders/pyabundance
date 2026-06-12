from __future__ import annotations

import numpy as np
import pyabundance
import pytest
from pyabundance import simulate_pcount, simulate_pcount_negbin, simulate_pcount_zip
from pyabundance.core import register_simulator, simulate


def _designs() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    X = np.asarray(
        [
            [1.0, -0.5],
            [1.0, 0.0],
            [1.0, 0.5],
            [1.0, 1.0],
        ],
        dtype=np.float64,
    )
    W = np.ones((4, 3, 2), dtype=np.float64)
    W[:, :, 1] = np.asarray(
        [
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0],
        ],
        dtype=np.float64,
    )
    beta = np.asarray([0.25, 0.15], dtype=np.float64)
    detection = np.asarray([-0.4, 0.1], dtype=np.float64)
    return X, W, beta, detection


def test_generic_pcount_poisson_matches_existing_simulator_with_same_seed():
    X, W, beta, detection = _designs()

    actual = simulate("pcount", X=X, W=W, beta=beta, detection=detection, seed=101)
    expected = simulate_pcount(X=X, W=W, beta=beta, alpha=detection, seed=101)

    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == (X.shape[0], W.shape[1])


def test_generic_pcount_poisson_accepts_alpha_alias():
    X, W, beta, detection = _designs()

    actual = simulate("pcount", X=X, W=W, beta=beta, alpha=detection, mixture="P", seed=102)
    expected = simulate_pcount(X=X, W=W, beta=beta, alpha=detection, seed=102)

    np.testing.assert_array_equal(actual, expected)


def test_generic_pcount_negbin_matches_existing_simulator_with_same_seed():
    X, W, beta, detection = _designs()

    actual = simulate(
        "pcount",
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        mixture="negative_binomial",
        r=1.8,
        seed=103,
    )
    expected = simulate_pcount_negbin(
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        r=1.8,
        seed=103,
    )

    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("alias", ["negbin", "NB"])
def test_generic_pcount_negbin_aliases_match_existing_simulator(alias: str):
    X, W, beta, detection = _designs()

    actual = simulate(
        "pcount",
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        mixture=alias,
        r=1.8,
        seed=104,
    )
    expected = simulate_pcount_negbin(X, W, beta, detection, r=1.8, seed=104)

    np.testing.assert_array_equal(actual, expected)


def test_generic_pcount_zip_matches_existing_simulator_with_same_seed():
    X, W, beta, detection = _designs()

    actual = simulate(
        "pcount",
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        mixture="zero_inflated_poisson",
        psi=0.25,
        seed=105,
    )
    expected = simulate_pcount_zip(
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        psi=0.25,
        seed=105,
    )

    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("alias", ["zip", "ZIP"])
def test_generic_pcount_zip_aliases_match_existing_simulator(alias: str):
    X, W, beta, detection = _designs()

    actual = simulate(
        "pcount",
        X=X,
        W=W,
        beta=beta,
        detection=detection,
        mixture=alias,
        psi=0.25,
        seed=106,
    )
    expected = simulate_pcount_zip(X, W, beta, detection, psi=0.25, seed=106)

    np.testing.assert_array_equal(actual, expected)


def test_generic_simulate_rejects_unsupported_model_family():
    with pytest.raises(ValueError, match="unsupported model family 'occu'"):
        simulate("occu")


def test_generic_pcount_rejects_unsupported_mixture():
    X, W, beta, detection = _designs()

    with pytest.raises(ValueError, match="unsupported pcount mixture 'geometric'"):
        simulate("pcount", X=X, W=W, beta=beta, detection=detection, mixture="geometric")


def test_generic_pcount_requires_r_for_negative_binomial():
    X, W, beta, detection = _designs()

    with pytest.raises(TypeError, match="r is required"):
        simulate("pcount", X=X, W=W, beta=beta, detection=detection, mixture="negbin")


def test_generic_pcount_requires_psi_for_zip():
    X, W, beta, detection = _designs()

    with pytest.raises(TypeError, match="psi is required"):
        simulate("pcount", X=X, W=W, beta=beta, detection=detection, mixture="ZIP")


def test_generic_pcount_rejects_invalid_extra_arguments():
    X, W, beta, detection = _designs()

    with pytest.raises(TypeError, match="invalid extra arguments.*foo"):
        simulate("pcount", X=X, W=W, beta=beta, detection=detection, foo=1)


def test_generic_pcount_requires_detection_or_alpha():
    X, W, beta, _ = _designs()

    with pytest.raises(TypeError, match="detection is required"):
        simulate("pcount", X=X, W=W, beta=beta)


def test_existing_pcount_simulators_still_work_unchanged():
    X, W, beta, detection = _designs()

    poisson = simulate_pcount(X, W, beta, detection, seed=107)
    negbin = simulate_pcount_negbin(X, W, beta, detection, r=1.8, seed=108)
    zip_counts = simulate_pcount_zip(X, W, beta, detection, psi=0.25, seed=109)

    assert poisson.shape == (X.shape[0], W.shape[1])
    assert negbin.shape == poisson.shape
    assert zip_counts.shape == poisson.shape
    assert poisson.dtype == np.float64
    assert negbin.dtype == np.float64
    assert zip_counts.dtype == np.float64


def test_generic_simulate_names_are_core_only_not_top_level_all():
    assert simulate is not None
    assert register_simulator is not None
    assert "simulate" not in pyabundance.__all__
    assert "register_simulator" not in pyabundance.__all__
