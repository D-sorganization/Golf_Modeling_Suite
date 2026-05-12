use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub struct ActivationDynamics {
    pub tau_act: f64,
    pub tau_deact: f64,
    pub min_activation: f64,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl ActivationDynamics {
    #[new]
    #[pyo3(signature = (tau_act = 0.010, tau_deact = 0.040, min_activation = 0.001))]
    fn py_new(tau_act: f64, tau_deact: f64, min_activation: f64) -> pyo3::PyResult<Self> {
        let dynamics = Self {
            tau_act,
            tau_deact,
            min_activation,
        };
        dynamics.validate().map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        Ok(dynamics)
    }

    #[pyo3(name = "compute_derivative")]
    fn py_compute_derivative(&self, u: f64, a: f64) -> f64 {
        self.compute_derivative(u, a)
    }

    #[pyo3(name = "update")]
    fn py_update(&self, u: f64, a: f64, dt: f64) -> pyo3::PyResult<f64> {
        if dt <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err("dt must be positive"));
        }
        Ok(self.update(u, a, dt))
    }

    // Batched update for RL inner loops
    #[pyo3(name = "update_batch")]
    fn py_update_batch(&self, u_batch: Vec<f64>, a_batch: Vec<f64>, dt: f64) -> pyo3::PyResult<Vec<f64>> {
        if dt <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err("dt must be positive"));
        }
        if u_batch.len() != a_batch.len() {
            return Err(pyo3::exceptions::PyValueError::new_err("Batch sizes must match"));
        }

        // Rayon is great for large batches, but we might just use a regular iter if small
        // For simplicity and to avoid GIL issues in parallel, we compute normally
        let mut results = Vec::with_capacity(u_batch.len());
        for (u, a) in u_batch.into_iter().zip(a_batch.into_iter()) {
            results.push(self.update(u, a, dt));
        }
        Ok(results)
    }

    #[getter]
    fn get_tau_act(&self) -> f64 { self.tau_act }
    #[getter]
    fn get_tau_deact(&self) -> f64 { self.tau_deact }
    #[getter]
    fn get_min_activation(&self) -> f64 { self.min_activation }
}

impl ActivationDynamics {
    pub fn validate(&self) -> Result<(), String> {
        if self.tau_act <= 0.0 { return Err(format!("tau_act must be positive, got {}", self.tau_act)); }
        if self.tau_deact <= 0.0 { return Err(format!("tau_deact must be positive, got {}", self.tau_deact)); }
        if self.min_activation <= 0.0 || self.min_activation >= 1.0 { return Err(format!("min_activation must be in (0, 1), got {}", self.min_activation)); }
        Ok(())
    }

    pub fn compute_derivative(&self, u: f64, a: f64) -> f64 {
        let u_clamped = u.clamp(self.min_activation, 1.0);
        let a_clamped = a.clamp(self.min_activation, 1.0);

        let tau = if u_clamped > a_clamped {
            self.tau_act * (0.5 + 1.5 * a_clamped)
        } else {
            self.tau_deact / (0.5 + 1.5 * a_clamped)
        };

        (u_clamped - a_clamped) / tau
    }

    pub fn update(&self, u: f64, a: f64, dt: f64) -> f64 {
        let dadt = self.compute_derivative(u, a);
        let a_new = a + dadt * dt;
        a_new.clamp(self.min_activation, 1.0)
    }
}
