pub mod distributions;
pub mod errors;
pub mod math;
pub mod pcount_poisson;
pub mod simulation;

pub use errors::{EcoError, Result};
pub use pcount_poisson::{
    pcount_poisson_loglik, pcount_poisson_predict_detection, pcount_poisson_predict_lambda,
    pcount_poisson_site_loglik, PCountDims,
};
pub use simulation::simulate_pcount_poisson;
