use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub struct MuscleParameters {
    #[pyo3(get, set)]
    pub f_max: f64,
    #[pyo3(get, set)]
    pub l_opt: f64,
    #[pyo3(get, set)]
    pub l_slack: f64,
    #[pyo3(get, set)]
    pub v_max: f64,
    #[pyo3(get, set)]
    pub pennation_angle: f64,
    #[pyo3(get, set)]
    pub damping: f64,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl MuscleParameters {
    #[new]
    #[pyo3(signature = (f_max, l_opt, l_slack, v_max = 10.0, pennation_angle = 0.0, damping = 0.05))]
    fn py_new(f_max: f64, l_opt: f64, l_slack: f64, v_max: f64, pennation_angle: f64, damping: f64) -> pyo3::PyResult<Self> {
        let params = Self {
            f_max,
            l_opt,
            l_slack,
            v_max,
            pennation_angle,
            damping,
        };
        params.validate().map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        Ok(params)
    }
}

impl MuscleParameters {
    pub fn validate(&self) -> Result<(), String> {
        if self.f_max <= 0.0 { return Err(format!("f_max must be positive, got {}", self.f_max)); }
        if self.l_opt <= 0.0 { return Err(format!("l_opt must be positive, got {}", self.l_opt)); }
        if self.l_slack <= 0.0 { return Err(format!("l_slack must be positive, got {}", self.l_slack)); }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub struct MuscleState {
    #[pyo3(get, set)]
    pub activation: f64,
    #[pyo3(get, set)]
    pub l_ce: f64,
    #[pyo3(get, set)]
    pub v_ce: f64,
    #[pyo3(get, set)]
    pub l_mt: f64,
}

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl MuscleState {
    #[new]
    #[pyo3(signature = (activation = 0.0, l_ce = 0.0, v_ce = 0.0, l_mt = 0.0))]
    fn py_new(activation: f64, l_ce: f64, v_ce: f64, l_mt: f64) -> Self {
        Self { activation, l_ce, v_ce, l_mt }
    }
}

#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub struct HillMuscleModel {
    pub params: MuscleParameters,
    pub force_length_width: f64,
}

const DEFAULT_FORCE_LENGTH_WIDTH: f64 = 0.56;

#[cfg(feature = "python")]
#[pyo3::pymethods]
impl HillMuscleModel {
    #[new]
    #[pyo3(signature = (params, force_length_width = None))]
    fn py_new(params: MuscleParameters, force_length_width: Option<f64>) -> Self {
        Self {
            params,
            force_length_width: force_length_width.unwrap_or(DEFAULT_FORCE_LENGTH_WIDTH),
        }
    }

    #[pyo3(name = "force_length_active")]
    fn py_force_length_active(&self, l_norm: f64) -> f64 { self.force_length_active(l_norm) }

    #[pyo3(name = "force_length_passive")]
    fn py_force_length_passive(&self, l_norm: f64) -> f64 { self.force_length_passive(l_norm) }

    #[pyo3(name = "force_velocity")]
    fn py_force_velocity(&self, v_norm: f64) -> f64 { self.force_velocity(v_norm) }

    #[pyo3(name = "tendon_force")]
    fn py_tendon_force(&self, l_tendon_norm: f64) -> f64 { self.tendon_force(l_tendon_norm) }

    #[pyo3(name = "compute_force")]
    fn py_compute_force(&self, state: &MuscleState) -> pyo3::PyResult<f64> {
        if state.activation < 0.0 || state.activation > 1.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!("activation must be in [0, 1], got {}", state.activation)));
        }
        Ok(self.compute_force(state))
    }

    #[pyo3(name = "compute_force_batch")]
    fn py_compute_force_batch(&self, states: Vec<MuscleState>) -> pyo3::PyResult<Vec<f64>> {
        use rayon::prelude::*;
        let mut results = vec![0.0; states.len()];
        let mut err = None;
        states.par_iter().zip(results.par_iter_mut()).for_each(|(state, res)| {
            if state.activation < 0.0 || state.activation > 1.0 {
                // Not thread safe to update err, but good enough for this
            } else {
                *res = self.compute_force(state);
            }
        });
        
        for state in &states {
            if state.activation < 0.0 || state.activation > 1.0 {
                return Err(pyo3::exceptions::PyValueError::new_err(format!("activation must be in [0, 1], got {}", state.activation)));
            }
        }
        Ok(results)
    }

    #[getter]
    fn get_params(&self) -> MuscleParameters { self.params.clone() }
    #[getter]
    fn get_force_length_width(&self) -> f64 { self.force_length_width }
}

impl HillMuscleModel {
    pub fn force_length_active(&self, l_norm: f64) -> f64 {
        (-((l_norm - 1.0).powi(2)) / self.force_length_width.powi(2)).exp()
    }

    pub fn force_length_passive(&self, l_norm: f64) -> f64 {
        if l_norm <= 1.0 {
            0.0
        } else {
            let k_passive = 4.0_f64;
            ((k_passive * (l_norm - 1.0)).exp() - 1.0) / (k_passive.exp() - 1.0)
        }
    }

    pub fn force_velocity(&self, v_norm: f64) -> f64 {
        if v_norm < 0.0 {
            let v_norm_clamped = v_norm.max(-0.99);
            (1.0 + v_norm_clamped) / (1.0 - v_norm_clamped / 0.25)
        } else {
            (1.0 + v_norm * 1.4 / 0.10) / (1.0 + v_norm / 0.10)
        }
    }

    pub fn tendon_force(&self, l_tendon_norm: f64) -> f64 {
        if l_tendon_norm <= 1.0 {
            0.0
        } else {
            let strain = l_tendon_norm - 1.0;
            10.0 * strain.powi(2)
        }
    }

    pub fn compute_force(&self, state: &MuscleState) -> f64 {
        let l_norm = state.l_ce / self.params.l_opt;
        let v_norm = state.v_ce / (self.params.v_max * self.params.l_opt);

        let f_l = self.force_length_active(l_norm);
        let f_v = self.force_velocity(v_norm);
        let f_p = self.force_length_passive(l_norm);

        let f_active = self.params.f_max * state.activation * f_l * f_v;
        let f_passive = self.params.f_max * f_p;
        let f_damping = self.params.damping * state.v_ce;

        let cos_alpha = self.params.pennation_angle.cos();
        let f_total = (f_active + f_passive + f_damping) * cos_alpha;

        f_total.max(0.0)
    }
}
