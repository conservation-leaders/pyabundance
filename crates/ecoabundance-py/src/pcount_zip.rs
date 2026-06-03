use ecoabundance_core::pcount_poisson::PCountDims;
use ecoabundance_core::pcount_zip::{
    log_zero_inflated_poisson_pmf as core_log_zip_pmf, pcount_zip_loglik as core_loglik,
    PCountZIPProblem as CorePCountZIPProblem,
};
use numpy::{PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArrayDyn};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn value_error<E: std::fmt::Display>(err: E) -> PyErr {
    PyValueError::new_err(err.to_string())
}

fn dims_from_arrays(
    y_shape: &[usize],
    x_shape: &[usize],
    w_shape: &[usize],
) -> PyResult<PCountDims> {
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
    Ok(PCountDims {
        n_sites: y_shape[0],
        n_visits: y_shape[1],
        n_abundance_params: x_shape[1],
        n_detection_params: w_shape[2],
    })
}

#[pyclass(name = "PCountZIPProblem", module = "pyabundance._core")]
pub struct PyPCountZIPProblem {
    problem: CorePCountZIPProblem,
}

#[pymethods]
impl PyPCountZIPProblem {
    #[new]
    pub fn new(
        y: PyReadonlyArray2<'_, f64>,
        x: PyReadonlyArray2<'_, f64>,
        w: PyReadonlyArrayDyn<'_, f64>,
        k: usize,
    ) -> PyResult<Self> {
        let y_view = y.as_array();
        let x_view = x.as_array();
        let w_view = w.as_array();
        let dims = dims_from_arrays(y_view.shape(), x_view.shape(), w_view.shape())?;
        let y_vec: Vec<f64> = y_view.iter().copied().collect();
        let x_vec: Vec<f64> = x_view.iter().copied().collect();
        let w_vec: Vec<f64> = w_view.iter().copied().collect();
        let problem =
            CorePCountZIPProblem::new(y_vec, x_vec, w_vec, k, dims).map_err(value_error)?;
        Ok(Self { problem })
    }

    pub fn loglik(&self, py: Python<'_>, theta: PyReadonlyArray1<'_, f64>) -> PyResult<f64> {
        let theta_view = theta.as_array();
        let theta_vec: Vec<f64> = theta_view.iter().copied().collect();
        py.allow_threads(|| self.problem.loglik(&theta_vec))
            .map_err(value_error)
    }
    pub fn posterior_abundance(
        &self,
        py: Python<'_>,
        theta: PyReadonlyArray1<'_, f64>,
    ) -> PyResult<Vec<Vec<f64>>> {
        let theta_view = theta.as_array();
        let theta_vec: Vec<f64> = theta_view.iter().copied().collect();
        py.allow_threads(|| self.problem.posterior_abundance(&theta_vec))
            .map_err(value_error)
    }

    #[getter]
    pub fn n_sites(&self) -> usize {
        self.problem.n_sites()
    }

    #[getter]
    pub fn n_visits(&self) -> usize {
        self.problem.n_visits()
    }

    #[getter(K)]
    pub fn k_upper(&self) -> usize {
        self.problem.k()
    }
}

#[pyfunction]
pub fn pcount_zip_loglik(
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

    let dims = dims_from_arrays(y_view.shape(), x_view.shape(), w_view.shape())?;
    let expected_theta = dims.n_abundance_params + dims.n_detection_params + 1;
    if theta_view.len() != expected_theta {
        return Err(PyValueError::new_err(format!(
            "theta length {} must equal X columns + W detection columns + logit_psi {expected_theta}",
            theta_view.len()
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
pub fn log_zero_inflated_poisson_pmf(n: u64, lambda: f64, psi: f64) -> PyResult<f64> {
    core_log_zip_pmf(n, lambda, psi).map_err(value_error)
}
