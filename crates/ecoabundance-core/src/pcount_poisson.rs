use crate::distributions::{log_binomial_pmf, log_poisson_pmf};
use crate::errors::{EcoError, Result};
use crate::math::{dot, inv_logit, log_sum_exp};

#[derive(Debug, Clone, Copy)]
pub struct PCountDims {
    pub n_sites: usize,
    pub n_visits: usize,
    pub n_abundance_params: usize,
    pub n_detection_params: usize,
}

pub fn validate_lengths(
    y: &[f64],
    x: &[f64],
    w: &[f64],
    theta: &[f64],
    dims: PCountDims,
) -> Result<()> {
    let expected_y = dims.n_sites * dims.n_visits;
    let expected_x = dims.n_sites * dims.n_abundance_params;
    let expected_w = dims.n_sites * dims.n_visits * dims.n_detection_params;
    let expected_theta = dims.n_abundance_params + dims.n_detection_params;
    if y.len() != expected_y {
        return Err(EcoError::Shape(format!(
            "y length {} does not match n_sites*n_visits {expected_y}",
            y.len()
        )));
    }
    if x.len() != expected_x {
        return Err(EcoError::Shape(format!(
            "X length {} does not match n_sites*n_abundance_params {expected_x}",
            x.len()
        )));
    }
    if w.len() != expected_w {
        return Err(EcoError::Shape(format!(
            "W length {} does not match n_sites*n_visits*n_detection_params {expected_w}",
            w.len()
        )));
    }
    if theta.len() != expected_theta {
        return Err(EcoError::Shape(format!(
            "theta length {} does not match beta+alpha length {expected_theta}",
            theta.len()
        )));
    }
    Ok(())
}

fn parse_count(value: f64) -> Result<Option<u64>> {
    if value.is_nan() {
        return Ok(None);
    }
    if !value.is_finite() {
        return Err(EcoError::InvalidInput(format!(
            "counts must be finite or NaN, got {value}"
        )));
    }
    if value < 0.0 || value.fract().abs() > 1.0e-12 {
        return Err(EcoError::InvalidInput(format!(
            "non-missing counts must be non-negative integers, got {value}"
        )));
    }
    Ok(Some(value as u64))
}

#[allow(clippy::too_many_arguments)]
pub fn pcount_poisson_site_loglik(
    y_site: &[f64],
    x_site: &[f64],
    w_site: &[f64],
    beta: &[f64],
    alpha: &[f64],
    n_visits: usize,
    n_detection_params: usize,
    k: usize,
) -> Result<f64> {
    if y_site.len() != n_visits {
        return Err(EcoError::Shape(
            "site count row has wrong length".to_string(),
        ));
    }
    if w_site.len() != n_visits * n_detection_params {
        return Err(EcoError::Shape(
            "site detection design has wrong length".to_string(),
        ));
    }

    let mut observed = Vec::with_capacity(n_visits);
    let mut max_y: u64 = 0;
    for (visit, value) in y_site.iter().enumerate() {
        if let Some(count) = parse_count(*value)? {
            max_y = max_y.max(count);
            observed.push((visit, count));
        }
    }
    if max_y as usize > k {
        return Err(EcoError::Truncation(format!(
            "max observed count {max_y} exceeds K {k}"
        )));
    }

    let eta_lambda = dot(x_site, beta);
    let lambda = eta_lambda.exp();
    if !lambda.is_finite() || lambda <= 0.0 {
        return Err(EcoError::InvalidInput(format!(
            "lambda must be positive and finite, got {lambda}"
        )));
    }

    let mut detection = vec![0.0; n_visits];
    for (visit, detection_value) in detection.iter_mut().enumerate() {
        let start = visit * n_detection_params;
        let end = start + n_detection_params;
        *detection_value = inv_logit(dot(&w_site[start..end], alpha));
    }

    let mut terms = Vec::with_capacity(k + 1 - max_y as usize);
    for n in max_y..=k as u64 {
        let mut log_term = log_poisson_pmf(n, lambda)?;
        for (visit, count) in &observed {
            log_term += log_binomial_pmf(*count, n, detection[*visit])?;
        }
        terms.push(log_term);
    }
    Ok(log_sum_exp(&terms))
}

pub fn pcount_poisson_loglik(
    y: &[f64],
    x: &[f64],
    w: &[f64],
    theta: &[f64],
    k: usize,
    dims: PCountDims,
) -> Result<f64> {
    validate_lengths(y, x, w, theta, dims)?;
    let (beta, alpha) = theta.split_at(dims.n_abundance_params);
    let mut total = 0.0;
    for site in 0..dims.n_sites {
        let y_start = site * dims.n_visits;
        let x_start = site * dims.n_abundance_params;
        let w_start = site * dims.n_visits * dims.n_detection_params;
        total += pcount_poisson_site_loglik(
            &y[y_start..y_start + dims.n_visits],
            &x[x_start..x_start + dims.n_abundance_params],
            &w[w_start..w_start + dims.n_visits * dims.n_detection_params],
            beta,
            alpha,
            dims.n_visits,
            dims.n_detection_params,
            k,
        )?;
    }
    Ok(total)
}

pub fn pcount_poisson_predict_lambda(x: &[f64], beta: &[f64], n_sites: usize) -> Result<Vec<f64>> {
    if beta.is_empty() {
        return Err(EcoError::Shape(
            "beta must contain at least one parameter".to_string(),
        ));
    }
    let p = beta.len();
    if x.len() != n_sites * p {
        return Err(EcoError::Shape(format!(
            "X length {} does not match n_sites*beta_len {}",
            x.len(),
            n_sites * p
        )));
    }
    Ok((0..n_sites)
        .map(|site| dot(&x[site * p..site * p + p], beta).exp())
        .collect())
}

pub fn pcount_poisson_predict_detection(
    w: &[f64],
    alpha: &[f64],
    n_sites: usize,
    n_visits: usize,
) -> Result<Vec<f64>> {
    if alpha.is_empty() {
        return Err(EcoError::Shape(
            "alpha must contain at least one parameter".to_string(),
        ));
    }
    let p = alpha.len();
    if w.len() != n_sites * n_visits * p {
        return Err(EcoError::Shape(format!(
            "W length {} does not match n_sites*n_visits*alpha_len {}",
            w.len(),
            n_sites * n_visits * p
        )));
    }
    let mut out = Vec::with_capacity(n_sites * n_visits);
    for row in w.chunks_exact(p) {
        out.push(inv_logit(dot(row, alpha)));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tiny_site_likelihood_is_finite() {
        let y = [1.0, 0.0];
        let x = [1.0];
        let w = [1.0, 1.0];
        let beta = [0.0];
        let alpha = [0.0];
        let got = pcount_poisson_site_loglik(&y, &x, &w, &beta, &alpha, 2, 1, 5).unwrap();
        assert!(got.is_finite());
        let lambda = 1.0_f64;
        let p = 0.5_f64;
        let mut terms = Vec::new();
        for n in 1..=5_u64 {
            terms.push(
                log_poisson_pmf(n, lambda).unwrap()
                    + log_binomial_pmf(1, n, p).unwrap()
                    + log_binomial_pmf(0, n, p).unwrap(),
            );
        }
        let expected = log_sum_exp(&terms);
        assert!((got - expected).abs() < 1.0e-12);
    }
}
