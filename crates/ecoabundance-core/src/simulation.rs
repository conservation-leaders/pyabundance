use rand::rngs::StdRng;
use rand::SeedableRng;
use rand_distr::{Binomial, Distribution, Poisson};

use crate::errors::{EcoError, Result};
use crate::pcount_poisson::{pcount_poisson_predict_detection, pcount_poisson_predict_lambda};

pub fn simulate_pcount_poisson(
    x: &[f64],
    w: &[f64],
    beta: &[f64],
    alpha: &[f64],
    n_sites: usize,
    n_visits: usize,
    seed: u64,
) -> Result<Vec<f64>> {
    let lambda = pcount_poisson_predict_lambda(x, beta, n_sites)?;
    let detection = pcount_poisson_predict_detection(w, alpha, n_sites, n_visits)?;
    let mut rng = StdRng::seed_from_u64(seed);
    let mut y = Vec::with_capacity(n_sites * n_visits);
    for site in 0..n_sites {
        let pois =
            Poisson::new(lambda[site]).map_err(|err| EcoError::InvalidInput(err.to_string()))?;
        let n = pois.sample(&mut rng) as u64;
        for visit in 0..n_visits {
            let p = detection[site * n_visits + visit];
            let bin = Binomial::new(n, p).map_err(|err| EcoError::InvalidInput(err.to_string()))?;
            y.push(bin.sample(&mut rng) as f64);
        }
    }
    Ok(y)
}
