use pyo3::prelude::*;

mod pcount;
mod pcount_negbin;
mod pcount_zip;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<pcount::PyPCountPoissonProblem>()?;
    m.add_class::<pcount_negbin::PyPCountNegBinProblem>()?;
    m.add_class::<pcount_zip::PyPCountZIPProblem>()?;
    m.add_function(wrap_pyfunction!(pcount::pcount_poisson_loglik, m)?)?;
    m.add_function(wrap_pyfunction!(pcount::pcount_poisson_predict_lambda, m)?)?;
    m.add_function(wrap_pyfunction!(pcount_negbin::pcount_negbin_loglik, m)?)?;
    m.add_function(wrap_pyfunction!(pcount_zip::pcount_zip_loglik, m)?)?;
    m.add_function(wrap_pyfunction!(
        pcount_negbin::log_negative_binomial_pmf_mean_size,
        m
    )?)?;
    m.add_function(wrap_pyfunction!(
        pcount_zip::log_zero_inflated_poisson_pmf,
        m
    )?)?;
    m.add_function(wrap_pyfunction!(
        pcount::pcount_poisson_predict_detection,
        m
    )?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
