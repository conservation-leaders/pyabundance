pub fn inv_logit(eta: f64) -> f64 {
    if eta >= 0.0 {
        let z = (-eta).exp();
        1.0 / (1.0 + z)
    } else {
        let z = eta.exp();
        z / (1.0 + z)
    }
}

pub fn clamp_probability(p: f64) -> f64 {
    const EPS: f64 = 1.0e-15;
    p.clamp(EPS, 1.0 - EPS)
}

pub fn log_sum_exp(values: &[f64]) -> f64 {
    if values.is_empty() {
        return f64::NEG_INFINITY;
    }
    let max_value = values.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    if !max_value.is_finite() {
        return max_value;
    }
    let sum: f64 = values.iter().map(|value| (*value - max_value).exp()).sum();
    max_value + sum.ln()
}

pub fn dot(row: &[f64], params: &[f64]) -> f64 {
    row.iter()
        .zip(params.iter())
        .map(|(x, beta)| x * beta)
        .sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn inverse_logit_is_stable() {
        assert!((inv_logit(0.0) - 0.5).abs() < 1.0e-15);
        assert!(inv_logit(1000.0) > 1.0 - 1.0e-12);
        assert!(inv_logit(-1000.0) < 1.0e-12);
    }

    #[test]
    fn logsumexp_matches_simple_case() {
        let got = log_sum_exp(&[0.0, 0.0]);
        assert!((got - 2.0_f64.ln()).abs() < 1.0e-15);
    }
}
