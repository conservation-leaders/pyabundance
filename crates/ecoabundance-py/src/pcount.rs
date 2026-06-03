use ecoabundance_core::pcount_poisson::{
    pcount_poisson_loglik as core_loglik,
    pcount_poisson_predict_detection as core_predict_detection,
    pcount_poisson_predict_lambda as core_predict_lambda, PCountDims,
};
use numpy::{PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArrayDyn};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn value_error<E: std::fmt::Display>(err: E) -> PyErr {
    PyValueError::new_err(err.to_string())
}

#[pyfunction]
pub fn pcount_poisson_loglik(
    py: Python<'_>,
    y: PyReadonlyArray2<'_, f64>,
    x: PyReadonlyArray2<'_, f64>,
    w: PyReadonlyArrayDyn<'_, f64>,
    theta: PyReadonlyArray1<'_, f64>,
    k: usize,
) -> PyResult<f64> {
    let y_view = y.as_array();
    let x_view = x.as_array();
    let w_view = w.as_array();
    let theta_view = theta.as_array();

    let y_shape = y_view.shape();
    let x_shape = x_view.shape();
    let w_shape = w_view.shape();
    if w_shape.len() != 3 {
        return Err(PyValueError::new_err(format!(
            "W must be 3-dimensional, got {} dimensions",
            w_shape.len()
        )));
    }
    if y_shape[0] != x_shape[0] || y_shape[0] != w_shape[0] {
        return Err(PyValueError::new_err(
            "y, X, and W must have the same number of sites",
        ));
    }
    if y_shape[1] != w_shape[1] {
        return Err(PyValueError::new_err(
            "y and W must have the same number of visits",
        ));
    }

    let dims = PCountDims {
        n_sites: y_shape[0],
        n_visits: y_shape[1],
        n_abundance_params: x_shape[1],
        n_detection_params: w_shape[2],
    };
    if theta_view.len() != dims.n_abundance_params + dims.n_detection_params {
        return Err(PyValueError::new_err(format!(
            "theta length {} must equal X columns + W detection columns {}",
            theta_view.len(),
            dims.n_abundance_params + dims.n_detection_params
        )));
    }

    let y_vec: Vec<f64> = y_view.iter().copied().collect();
    let x_vec: Vec<f64> = x_view.iter().copied().collect();
    let w_vec: Vec<f64> = w_view.iter().copied().collect();
    let theta_vec: Vec<f64> = theta_view.iter().copied().collect();

    py.allow_threads(move || core_loglik(&y_vec, &x_vec, &w_vec, &theta_vec, k, dims))
        .map_err(value_error)
}

#[pyfunction]
pub fn pcount_poisson_predict_lambda(
    py: Python<'_>,
    x: PyReadonlyArray2<'_, f64>,
    beta: PyReadonlyArray1<'_, f64>,
) -> PyResult<Vec<f64>> {
    let x_view = x.as_array();
    let beta_view = beta.as_array();
    if x_view.shape()[1] != beta_view.len() {
        return Err(PyValueError::new_err(format!(
            "X has {} columns but beta has length {}",
            x_view.shape()[1],
            beta_view.len()
        )));
    }
    let n_sites = x_view.shape()[0];
    let x_vec: Vec<f64> = x_view.iter().copied().collect();
    let beta_vec: Vec<f64> = beta_view.iter().copied().collect();
    py.allow_threads(move || core_predict_lambda(&x_vec, &beta_vec, n_sites))
        .map_err(value_error)
}

#[pyfunction]
pub fn pcount_poisson_predict_detection(
    py: Python<'_>,
    w: PyReadonlyArrayDyn<'_, f64>,
    alpha: PyReadonlyArray1<'_, f64>,
) -> PyResult<Vec<f64>> {
    let w_view = w.as_array();
    let alpha_view = alpha.as_array();
    let w_shape = w_view.shape();
    if w_shape.len() != 3 {
        return Err(PyValueError::new_err(format!(
            "W must be 3-dimensional, got {} dimensions",
            w_shape.len()
        )));
    }
    if w_shape[2] != alpha_view.len() {
        return Err(PyValueError::new_err(format!(
            "W has {} detection columns but alpha has length {}",
            w_shape[2],
            alpha_view.len()
        )));
    }
    let n_sites = w_shape[0];
    let n_visits = w_shape[1];
    let w_vec: Vec<f64> = w_view.iter().copied().collect();
    let alpha_vec: Vec<f64> = alpha_view.iter().copied().collect();
    py.allow_threads(move || core_predict_detection(&w_vec, &alpha_vec, n_sites, n_visits))
        .map_err(value_error)
}
