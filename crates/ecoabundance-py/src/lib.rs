use pyo3::prelude::*;

mod pcount;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pcount::pcount_poisson_loglik, m)?)?;
    m.add_function(wrap_pyfunction!(pcount::pcount_poisson_predict_lambda, m)?)?;
    m.add_function(wrap_pyfunction!(
        pcount::pcount_poisson_predict_detection,
        m
    )?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
