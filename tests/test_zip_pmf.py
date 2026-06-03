import math

from pyabundance import _core


def logaddexp(a: float, b: float) -> float:
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def ref_log_zip(n: int, lam: float, psi: float) -> float:
    log_pois = n * math.log(lam) - lam - math.lgamma(n + 1)
    if n == 0:
        return logaddexp(math.log(psi), math.log1p(-psi) + log_pois)
    return math.log1p(-psi) + log_pois


def test_zip_log_pmf_matches_reference():
    for n in [0, 1, 2, 10]:
        for lam in [0.5, 2.0, 10.0]:
            for psi in [0.05, 0.2, 0.6]:
                got = _core.log_zero_inflated_poisson_pmf(n, lam, psi)
                expected = ref_log_zip(n, lam, psi)
                assert abs(got - expected) < 1.0e-10


def test_zip_zero_mass_includes_structural_and_poisson_zero():
    lam = 2.0
    psi = 0.2
    got = math.exp(_core.log_zero_inflated_poisson_pmf(0, lam, psi))
    expected = psi + (1.0 - psi) * math.exp(-lam)
    assert abs(got - expected) < 1.0e-12
