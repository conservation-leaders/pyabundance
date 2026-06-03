use std::time::Instant;

use ecoabundance_core::math::log_sum_exp;
use ecoabundance_core::pcount_poisson::{PCountDims, PCountPoissonProblem};

fn benchmark_problem() -> (PCountPoissonProblem, Vec<f64>) {
    let n_sites = 500;
    let n_visits = 3;
    let k = 60;
    let beta = [0.2_f64, 0.6_f64];
    let alpha = [-0.8_f64, -0.2_f64, 0.4_f64];
    let theta = [beta.as_slice(), alpha.as_slice()].concat();
    let mut y = Vec::with_capacity(n_sites * n_visits);
    let mut x = Vec::with_capacity(n_sites * 2);
    let mut w = vec![0.0; n_sites * n_visits * n_visits];
    for site in 0..n_sites {
        let cov = ((site % 101) as f64 - 50.0) / 50.0;
        x.push(1.0);
        x.push(cov);
        let lambda = (beta[0] + beta[1] * cov).exp();
        let base_count = lambda.round().clamp(0.0, 8.0);
        for visit in 0..n_visits {
            y.push((base_count * (visit as f64 + 1.0) / 4.0).floor());
            w[(site * n_visits + visit) * n_visits + visit] = 1.0;
        }
    }
    let dims = PCountDims {
        n_sites,
        n_visits,
        n_abundance_params: 2,
        n_detection_params: 3,
    };
    (
        PCountPoissonProblem::new(y, x, w, k, dims).expect("benchmark problem is valid"),
        theta,
    )
}

fn median(values: &mut [f64]) -> f64 {
    values.sort_by(|a, b| a.total_cmp(b));
    values[values.len() / 2]
}

fn main() {
    let (problem, theta) = benchmark_problem();
    let repeats = 1000;
    let mut loglik_timings = Vec::with_capacity(repeats);
    let mut site_timings = Vec::with_capacity(repeats);
    let mut lse_timings = Vec::with_capacity(repeats);
    let (beta, alpha) = theta.split_at(2);
    let values: Vec<f64> = (0..=60).map(|n| -(n as f64) / 3.0).collect();

    for _ in 0..20 {
        let _ = problem.loglik(&theta).unwrap();
    }

    for _ in 0..repeats {
        let start = Instant::now();
        let _ = problem.loglik(&theta).unwrap();
        loglik_timings.push(start.elapsed().as_secs_f64() * 1_000_000.0);

        let mut detection_cache = vec![0.0; problem.n_visits()];
        let start = Instant::now();
        let _ = problem
            .site_loglik(0, beta, alpha, &mut detection_cache)
            .unwrap();
        site_timings.push(start.elapsed().as_secs_f64() * 1_000_000.0);

        let start = Instant::now();
        let _ = log_sum_exp(&values);
        lse_timings.push(start.elapsed().as_secs_f64() * 1_000_000.0);
    }

    println!("pcount Poisson core example benchmark");
    println!("repeats: {repeats}");
    println!(
        "full loglik median: {:.3} microseconds",
        median(&mut loglik_timings)
    );
    println!(
        "site loglik median: {:.3} microseconds",
        median(&mut site_timings)
    );
    println!(
        "log_sum_exp median: {:.3} microseconds",
        median(&mut lse_timings)
    );
}
