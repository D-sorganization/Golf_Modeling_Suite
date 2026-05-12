use numpy::ndarray::{Array2, s};
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray1, PyReadonlyArray2};
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyfunction]
pub fn compute_finite_difference<'py>(
    py: Python<'py>,
    times: PyReadonlyArray1<'py, f64>,
    q: PyReadonlyArray2<'py, f64>,
) -> PyResult<(&'py PyArray2<f64>, &'py PyArray2<f64>)> {
    let times = times.as_slice()?;
    let q_arr = q.as_array();

    let n_frames = times.len();
    let n_dof = q_arr.shape()[1];

    let mut qdot = Array2::<f64>::zeros((n_frames, n_dof));
    let mut qddot = Array2::<f64>::zeros((n_frames, n_dof));

    if n_frames < 2 {
        return Ok((qdot.into_pyarray(py), qddot.into_pyarray(py)));
    }

    // qdot
    for i in 1..(n_frames - 1) {
        let dt = times[i + 1] - times[i - 1];
        if dt > 0.0 {
            for j in 0..n_dof {
                qdot[[i, j]] = (q_arr[[i + 1, j]] - q_arr[[i - 1, j]]) / dt;
            }
        }
    }

    let dt0 = (times[1] - times[0]).max(1e-9);
    for j in 0..n_dof {
        qdot[[0, j]] = (q_arr[[1, j]] - q_arr[[0, j]]) / dt0;
    }

    let dtn = (times[n_frames - 1] - times[n_frames - 2]).max(1e-9);
    for j in 0..n_dof {
        qdot[[n_frames - 1, j]] = (q_arr[[n_frames - 1, j]] - q_arr[[n_frames - 2, j]]) / dtn;
    }

    if n_frames >= 3 {
        // qddot
        for i in 1..(n_frames - 1) {
            let dt_b = times[i] - times[i - 1];
            let dt_f = times[i + 1] - times[i];
            if dt_b > 0.0 && dt_f > 0.0 {
                let den = dt_b * dt_f * (dt_b + dt_f);
                for j in 0..n_dof {
                    qddot[[i, j]] = 2.0
                        * (q_arr[[i + 1, j]] * dt_b - q_arr[[i, j]] * (dt_b + dt_f)
                            + q_arr[[i - 1, j]] * dt_f)
                        / den;
                }
            }
        }
        for j in 0..n_dof {
            qddot[[0, j]] = qddot[[1, j]];
            qddot[[n_frames - 1, j]] = qddot[[n_frames - 2, j]];
        }
    }

    Ok((qdot.into_pyarray(py), qddot.into_pyarray(py)))
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn pinocchio_rnea_loop<'py>(
    py: Python<'py>,
    rnea_func: PyObject,
    model: PyObject,
    data: PyObject,
    q: PyReadonlyArray2<'py, f64>,
    qdot: PyReadonlyArray2<'py, f64>,
    qddot: PyReadonlyArray2<'py, f64>,
) -> PyResult<&'py PyArray2<f64>> {
    let q_arr = q.as_array();
    let qdot_arr = qdot.as_array();
    let qddot_arr = qddot.as_array();

    let n_frames = q_arr.shape()[0];
    let n_dof = q_arr.shape()[1];

    let mut torques = Array2::<f64>::zeros((n_frames, n_dof));

    for i in 0..n_frames {
        let q_i = q_arr.row(i).to_owned().into_pyarray(py);
        let v_i = qdot_arr.row(i).to_owned().into_pyarray(py);
        let a_i = qddot_arr.row(i).to_owned().into_pyarray(py);

        let args = (model.clone_ref(py), data.clone_ref(py), q_i, v_i, a_i);
        let tau = rnea_func.call1(py, args)?;
        let tau_arr: PyReadonlyArray1<f64> = tau.extract(py)?;
        let tau_slice = tau_arr.as_slice()?;

        for j in 0..n_dof {
            let val = tau_slice[j];
            if !val.is_finite() {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "RNEA produced non-finite torques at frame {}",
                    i
                )));
            }
            torques[[i, j]] = val;
        }
    }

    Ok(torques.into_pyarray(py))
}
