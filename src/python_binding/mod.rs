use pyo3::prelude::{pymodule, PyModule, PyResult, Python};
use pyo3::types::PyAnyMethods;
use pyo3::{intern, Bound};

#[pymodule]
fn _pagen(py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.setattr(intern!(py, "__doc__"), env!("CARGO_PKG_DESCRIPTION"))?;
    module.setattr(intern!(py, "__version__"), env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
