import math

from pyabundance import _core


def ref_log_nb(n: int, mu: float, r: float) -> float:
    return (
        math.lgamma(n + r)
        - math.lgamma(r)
        - math.lgamma(n + 1)
        + r * (math.log(r) - math.log(r + mu))
        + n * (math.log(mu) - math.log(r + mu))
    )


def test_negbin_log_pmf_matches_reference():
    for n in [0, 1, 2, 10]:
        for mu in [0.5, 2.0, 10.0]:
            for r in [0.5, 1.0, 5.0]:
                got = _core.log_negative_binomial_pmf_mean_size(n, mu, r)
                expected = ref_log_nb(n, mu, r)
                assert abs(got - expected) < 1.0e-10
