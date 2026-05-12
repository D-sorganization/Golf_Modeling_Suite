pub mod activation_dynamics;
pub mod hill_muscle;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn upstream_muscle(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<activation_dynamics::ActivationDynamics>()?;
    m.add_class::<hill_muscle::MuscleParameters>()?;
    m.add_class::<hill_muscle::MuscleState>()?;
    m.add_class::<hill_muscle::HillMuscleModel>()?;
    Ok(())
}
