pub mod activation_dynamics;
pub mod hill_muscle;
pub mod muscle_equilibrium;
pub mod multi_muscle;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn upstream_muscle(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<activation_dynamics::ActivationDynamics>()?;
    m.add_class::<hill_muscle::MuscleParameters>()?;
    m.add_class::<hill_muscle::MuscleState>()?;
    m.add_class::<hill_muscle::HillMuscleModel>()?;
    
    m.add_class::<muscle_equilibrium::PyEquilibriumSolver>()?;
    m.add_function(wrap_pyfunction!(muscle_equilibrium::compute_equilibrium_state, m)?)?;
    
    m.add_class::<multi_muscle::MuscleAttachment>()?;
    m.add_class::<multi_muscle::MuscleGroup>()?;
    m.add_class::<multi_muscle::AntagonistPair>()?;
    Ok(())
}
