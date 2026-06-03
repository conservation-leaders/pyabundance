use crate::errors::{EcoError, Result};
use crate::math::clamp_probability;

pub fn log_factorial(n: u64) -> f64 {
    (1..=n).map(|k| (k as f64).ln()).sum()
}

pub fn log_poisson_pmf(n: u64, lambda: f64) -> Result<f64> {
    if !lambda.is_finite() || lambda <= 0.0 {
        return Err(EcoError::InvalidInput(format!(
            "lambda must be positive and finite, got {lambda}"
        )));
    }
    Ok((n as f64) * lambda.ln() - lambda - log_factorial(n))
}

pub fn log_binomial_pmf(y: u64, n: u64, p: f64) -> Result<f64> {
    if y > n {
        return Ok(f64::NEG_INFINITY);
    }
    if !p.is_finite() {
        return Err(EcoError::InvalidInput(format!(
            "detection probability must be finite, got {p}"
        )));
    }
    let p = clamp_probability(p);
    let log_choose = log_factorial(n) - log_factorial(y) - log_factorial(n - y);
    Ok(log_choose + (y as f64) * p.ln() + ((n - y) as f64) * (1.0 - p).ln())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn log_poisson_pmf_matches_hand_value() {
        let got = log_poisson_pmf(2, 3.0).unwrap();
        let expected = 2.0 * 3.0_f64.ln() - 3.0 - 2.0_f64.ln();
        assert!((got - expected).abs() < 1.0e-15);
    }

    #[test]
    fn log_binomial_pmf_matches_hand_value() {
        let got = log_binomial_pmf(1, 3, 0.25).unwrap();
        let expected = 3.0_f64.ln() + 0.25_f64.ln() + 2.0 * 0.75_f64.ln();
        assert!((got - expected).abs() < 1.0e-15);
    }
}
