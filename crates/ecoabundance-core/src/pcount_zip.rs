use crate::errors::{EcoError, Result};
use crate::math::{clamp_probability, dot, inv_logit, log_sum_exp};
use crate::pcount_poisson::PCountDims;

#[derive(Debug, Clone)]
struct SiteObservations {
    observed: Vec<(usize, usize)>,
    max_y: usize,
}

#[derive(Debug, Clone)]
pub struct PCountZIPProblem {
    y: Vec<f64>,
    x: Vec<f64>,
    w: Vec<f64>,
    dims: PCountDims,
    k: usize,
    sites: Vec<SiteObservations>,
    log_factorials: Vec<f64>,
}

impl PCountZIPProblem {
    pub fn new(y: Vec<f64>, x: Vec<f64>, w: Vec<f64>, k: usize, dims: PCountDims) -> Result<Self> {
        validate_lengths_without_theta(&y, &x, &w, dims)?;
        let mut sites = Vec::with_capacity(dims.n_sites);
        for site in 0..dims.n_sites {
            let y_start = site * dims.n_visits;
            let y_site = &y[y_start..y_start + dims.n_visits];
            let mut observed = Vec::with_capacity(dims.n_visits);
            let mut max_y = 0_usize;
            for (visit, value) in y_site.iter().enumerate() {
                if let Some(count) = parse_count(*value)? {
                    let count = count as usize;
                    max_y = max_y.max(count);
                    observed.push((visit, count));
                }
            }
            if max_y > k {
                return Err(EcoError::Truncation(format!(
                    "max observed count {max_y} exceeds K {k}"
                )));
            }
            sites.push(SiteObservations { observed, max_y });
        }
        Ok(Self {
            y,
            x,
            w,
            dims,
            k,
            sites,
            log_factorials: precompute_log_factorials(k),
        })
    }

    pub fn n_sites(&self) -> usize {
        self.dims.n_sites
    }

    pub fn n_visits(&self) -> usize {
        self.dims.n_visits
    }

    pub fn n_abundance_params(&self) -> usize {
        self.dims.n_abundance_params
    }

    pub fn n_detection_params(&self) -> usize {
        self.dims.n_detection_params
    }

    pub fn k(&self) -> usize {
        self.k
    }

    pub fn loglik(&self, theta: &[f64]) -> Result<f64> {
        let expected_theta = self.dims.n_abundance_params + self.dims.n_detection_params + 1;
        if theta.len() != expected_theta {
            return Err(EcoError::Shape(format!(
                "theta length {} does not match beta+detection+logit_psi length {expected_theta}",
                theta.len()
            )));
        }
        let beta_end = self.dims.n_abundance_params;
        let detection_end = beta_end + self.dims.n_detection_params;
        let beta = &theta[..beta_end];
        let detection = &theta[beta_end..detection_end];
        let logit_psi = theta[detection_end];
        if !logit_psi.is_finite() {
            return Err(EcoError::InvalidInput(format!(
                "logit_psi must be finite, got {logit_psi}"
            )));
        }
        let psi = inv_logit(logit_psi);
        validate_psi(psi)?;
        let mut total = 0.0;
        let mut detection_cache = vec![0.0; self.dims.n_visits];
        for site in 0..self.dims.n_sites {
            total += self.site_loglik(site, beta, detection, psi, &mut detection_cache)?;
        }
        Ok(total)
    }

    pub fn site_loglik(
        &self,
        site: usize,
        beta: &[f64],
        detection: &[f64],
        psi: f64,
        detection_cache: &mut [f64],
    ) -> Result<f64> {
        if site >= self.dims.n_sites {
            return Err(EcoError::Shape(format!(
                "site index {site} exceeds n_sites {}",
                self.dims.n_sites
            )));
        }
        if beta.len() != self.dims.n_abundance_params {
            return Err(EcoError::Shape(format!(
                "beta length {} does not match X columns {}",
                beta.len(),
                self.dims.n_abundance_params
            )));
        }
        if detection.len() != self.dims.n_detection_params {
            return Err(EcoError::Shape(format!(
                "detection length {} does not match W detection columns {}",
                detection.len(),
                self.dims.n_detection_params
            )));
        }
        if detection_cache.len() != self.dims.n_visits {
            return Err(EcoError::Shape(format!(
                "detection cache length {} does not match n_visits {}",
                detection_cache.len(),
                self.dims.n_visits
            )));
        }
        validate_psi(psi)?;

        let x_start = site * self.dims.n_abundance_params;
        let x_site = &self.x[x_start..x_start + self.dims.n_abundance_params];
        let lambda = dot(x_site, beta).exp();
        if !lambda.is_finite() || lambda <= 0.0 {
            return Err(EcoError::InvalidInput(format!(
                "ZIP lambda must be positive and finite, got {lambda}"
            )));
        }

        let w_start = site * self.dims.n_visits * self.dims.n_detection_params;
        let w_site = &self.w[w_start..w_start + self.dims.n_visits * self.dims.n_detection_params];
        for (visit, detection_value) in detection_cache.iter_mut().enumerate() {
            let start = visit * self.dims.n_detection_params;
            let end = start + self.dims.n_detection_params;
            *detection_value = inv_logit(dot(&w_site[start..end], detection));
        }

        let site_obs = &self.sites[site];
        let mut max_log_term = f64::NEG_INFINITY;
        let mut scaled_sum = 0.0;
        for n in site_obs.max_y..=self.k {
            let mut log_term = log_zip_pmf_precomputed(n, lambda, psi, &self.log_factorials)?;
            for (visit, count) in &site_obs.observed {
                log_term += log_binomial_pmf_precomputed(
                    *count,
                    n,
                    detection_cache[*visit],
                    &self.log_factorials,
                );
            }
            if log_term > max_log_term {
                scaled_sum = scaled_sum * (max_log_term - log_term).exp() + 1.0;
                max_log_term = log_term;
            } else {
                scaled_sum += (log_term - max_log_term).exp();
            }
        }
        Ok(max_log_term + scaled_sum.ln())
    }

    pub fn posterior_abundance(&self, theta: &[f64]) -> Result<Vec<Vec<f64>>> {
        let expected_theta = self.dims.n_abundance_params + self.dims.n_detection_params + 1;
        if theta.len() != expected_theta {
            return Err(EcoError::Shape(format!(
                "theta length {} does not match beta+detection+logit_psi length {expected_theta}",
                theta.len()
            )));
        }
        let beta_end = self.dims.n_abundance_params;
        let detection_end = beta_end + self.dims.n_detection_params;
        let beta = &theta[..beta_end];
        let detection = &theta[beta_end..detection_end];
        let logit_psi = theta[detection_end];
        if !logit_psi.is_finite() {
            return Err(EcoError::InvalidInput(format!(
                "logit_psi must be finite, got {logit_psi}"
            )));
        }
        let psi = inv_logit(logit_psi);
        validate_psi(psi)?;
        let mut out = Vec::with_capacity(self.dims.n_sites);
        let mut detection_cache = vec![0.0; self.dims.n_visits];
        for site in 0..self.dims.n_sites {
            let x_start = site * self.dims.n_abundance_params;
            let x_site = &self.x[x_start..x_start + self.dims.n_abundance_params];
            let lambda = dot(x_site, beta).exp();
            if !lambda.is_finite() || lambda <= 0.0 {
                return Err(EcoError::InvalidInput(format!(
                    "ZIP lambda must be positive and finite, got {lambda}"
                )));
            }
            let w_start = site * self.dims.n_visits * self.dims.n_detection_params;
            let w_site =
                &self.w[w_start..w_start + self.dims.n_visits * self.dims.n_detection_params];
            for (visit, detection_value) in detection_cache.iter_mut().enumerate() {
                let start = visit * self.dims.n_detection_params;
                let end = start + self.dims.n_detection_params;
                *detection_value = inv_logit(dot(&w_site[start..end], detection));
            }
            let site_obs = &self.sites[site];
            let mut log_probs = vec![f64::NEG_INFINITY; self.k + 1];
            for (n, log_prob) in log_probs
                .iter_mut()
                .enumerate()
                .skip(site_obs.max_y)
                .take(self.k + 1 - site_obs.max_y)
            {
                let mut log_term = log_zip_pmf_precomputed(n, lambda, psi, &self.log_factorials)?;
                for (visit, count) in &site_obs.observed {
                    log_term += log_binomial_pmf_precomputed(
                        *count,
                        n,
                        detection_cache[*visit],
                        &self.log_factorials,
                    );
                }
                *log_prob = log_term;
            }
            let normalizer = log_sum_exp(&log_probs);
            out.push(
                log_probs
                    .iter()
                    .map(|value| {
                        if value.is_finite() {
                            (value - normalizer).exp()
                        } else {
                            0.0
                        }
                    })
                    .collect(),
            );
        }
        Ok(out)
    }

    pub fn y_len(&self) -> usize {
        self.y.len()
    }
}

pub fn log_zero_inflated_poisson_pmf(n: u64, lambda: f64, psi: f64) -> Result<f64> {
    if !lambda.is_finite() || lambda <= 0.0 {
        return Err(EcoError::InvalidInput(format!(
            "ZIP lambda must be positive and finite, got {lambda}"
        )));
    }
    validate_psi(psi)?;
    let log_pois = (n as f64) * lambda.ln() - lambda - log_factorial(n as usize);
    if n == 0 {
        Ok(log_add_exp(psi.ln(), (-psi).ln_1p() + log_pois))
    } else {
        Ok((-psi).ln_1p() + log_pois)
    }
}

#[allow(clippy::too_many_arguments)]
pub fn pcount_zip_site_loglik(
    y_site: &[f64],
    x_site: &[f64],
    w_site: &[f64],
    beta: &[f64],
    detection: &[f64],
    logit_psi: f64,
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
    if !logit_psi.is_finite() {
        return Err(EcoError::InvalidInput(format!(
            "logit_psi must be finite, got {logit_psi}"
        )));
    }
    let psi = inv_logit(logit_psi);
    validate_psi(psi)?;

    let mut observed = Vec::with_capacity(n_visits);
    let mut max_y = 0_usize;
    for (visit, value) in y_site.iter().enumerate() {
        if let Some(count) = parse_count(*value)? {
            let count = count as usize;
            max_y = max_y.max(count);
            observed.push((visit, count));
        }
    }
    if max_y > k {
        return Err(EcoError::Truncation(format!(
            "max observed count {max_y} exceeds K {k}"
        )));
    }

    let lambda = dot(x_site, beta).exp();
    if !lambda.is_finite() || lambda <= 0.0 {
        return Err(EcoError::InvalidInput(format!(
            "ZIP lambda must be positive and finite, got {lambda}"
        )));
    }
    let mut detection_cache = vec![0.0; n_visits];
    for (visit, detection_value) in detection_cache.iter_mut().enumerate() {
        let start = visit * n_detection_params;
        let end = start + n_detection_params;
        *detection_value = inv_logit(dot(&w_site[start..end], detection));
    }
    let log_factorials = precompute_log_factorials(k);
    let mut terms = Vec::with_capacity(k + 1 - max_y);
    for n in max_y..=k {
        let mut log_term = log_zip_pmf_precomputed(n, lambda, psi, &log_factorials)?;
        for (visit, count) in &observed {
            log_term +=
                log_binomial_pmf_precomputed(*count, n, detection_cache[*visit], &log_factorials);
        }
        terms.push(log_term);
    }
    Ok(log_sum_exp(&terms))
}

pub fn pcount_zip_loglik(
    y: &[f64],
    x: &[f64],
    w: &[f64],
    theta: &[f64],
    k: usize,
    dims: PCountDims,
) -> Result<f64> {
    let expected_theta = dims.n_abundance_params + dims.n_detection_params + 1;
    if theta.len() != expected_theta {
        return Err(EcoError::Shape(format!(
            "theta length {} does not match beta+detection+logit_psi length {expected_theta}",
            theta.len()
        )));
    }
    let problem = PCountZIPProblem::new(y.to_vec(), x.to_vec(), w.to_vec(), k, dims)?;
    problem.loglik(theta)
}

fn validate_lengths_without_theta(y: &[f64], x: &[f64], w: &[f64], dims: PCountDims) -> Result<()> {
    let expected_y = dims.n_sites * dims.n_visits;
    let expected_x = dims.n_sites * dims.n_abundance_params;
    let expected_w = dims.n_sites * dims.n_visits * dims.n_detection_params;
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

fn precompute_log_factorials(k: usize) -> Vec<f64> {
    let mut out = vec![0.0; k + 1];
    for n in 1..=k {
        out[n] = out[n - 1] + (n as f64).ln();
    }
    out
}

fn log_factorial(n: usize) -> f64 {
    (1..=n).map(|k| (k as f64).ln()).sum()
}

fn log_poisson_pmf_precomputed(n: usize, lambda: f64, log_factorials: &[f64]) -> f64 {
    (n as f64) * lambda.ln() - lambda - log_factorials[n]
}

fn log_zip_pmf_precomputed(n: usize, lambda: f64, psi: f64, log_factorials: &[f64]) -> Result<f64> {
    if !lambda.is_finite() || lambda <= 0.0 {
        return Err(EcoError::InvalidInput(format!(
            "ZIP lambda must be positive and finite, got {lambda}"
        )));
    }
    validate_psi(psi)?;
    let log_pois = log_poisson_pmf_precomputed(n, lambda, log_factorials);
    if n == 0 {
        Ok(log_add_exp(psi.ln(), (-psi).ln_1p() + log_pois))
    } else {
        Ok((-psi).ln_1p() + log_pois)
    }
}

fn log_binomial_pmf_precomputed(y: usize, n: usize, p: f64, log_factorials: &[f64]) -> f64 {
    if y > n {
        return f64::NEG_INFINITY;
    }
    let p = clamp_probability(p);
    let log_choose = log_factorials[n] - log_factorials[y] - log_factorials[n - y];
    log_choose + (y as f64) * p.ln() + ((n - y) as f64) * (1.0 - p).ln()
}

fn validate_psi(psi: f64) -> Result<()> {
    if !psi.is_finite() || psi <= 0.0 || psi >= 1.0 {
        return Err(EcoError::InvalidInput(format!(
            "ZIP psi must be in (0, 1), got {psi}"
        )));
    }
    Ok(())
}

fn log_add_exp(a: f64, b: f64) -> f64 {
    let max_value = a.max(b);
    max_value + ((a - max_value).exp() + (b - max_value).exp()).ln()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn poisson_log(n: u64, lambda: f64) -> f64 {
        (n as f64) * lambda.ln() - lambda - log_factorial(n as usize)
    }

    #[test]
    fn zip_pmf_zero_includes_both_zero_masses() {
        let lambda = 2.0;
        let psi = 0.25;
        let got = log_zero_inflated_poisson_pmf(0, lambda, psi).unwrap();
        let expected = log_add_exp(psi.ln(), (1.0_f64 - psi).ln() + poisson_log(0, lambda));
        assert!((got - expected).abs() < 1.0e-12);
    }

    #[test]
    fn cached_problem_matches_public_loglik() {
        let y = vec![0.0, 0.0, 2.0, f64::NAN];
        let x = vec![1.0, -0.2, 1.0, 0.4];
        let w = vec![1.0, 1.0, 1.0, 1.0];
        let theta = vec![0.1, 0.3, -0.4, -1.2];
        let dims = PCountDims {
            n_sites: 2,
            n_visits: 2,
            n_abundance_params: 2,
            n_detection_params: 1,
        };
        let raw = pcount_zip_loglik(&y, &x, &w, &theta, 8, dims).unwrap();
        let problem = PCountZIPProblem::new(y, x, w, 8, dims).unwrap();
        let cached = problem.loglik(&theta).unwrap();
        assert!((raw - cached).abs() < 1.0e-12);
        assert_eq!(problem.y_len(), 4);
    }
}
