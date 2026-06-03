pub mod distributions;
pub mod errors;
pub mod math;
pub mod pcount_negbin;
pub mod pcount_poisson;
pub mod pcount_zip;
pub mod simulation;

pub use errors::{EcoError, Result};
pub use pcount_poisson::{
    pcount_poisson_loglik, pcount_poisson_predict_detection, pcount_poisson_predict_lambda,
    pcount_poisson_site_loglik, PCountDims, PCountPoissonProblem,
};
pub use simulation::simulate_pcount_poisson;

pub use pcount_negbin::{
    log_negative_binomial_pmf_mean_size, pcount_negbin_loglik, pcount_negbin_site_loglik,
    PCountNegBinProblem,
};

pub use pcount_zip::{
    log_zero_inflated_poisson_pmf, pcount_zip_loglik, pcount_zip_site_loglik, PCountZIPProblem,
};
