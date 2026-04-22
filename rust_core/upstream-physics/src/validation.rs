//! Shared runtime validation helpers for public physics boundaries.

use tools_core::Vector3;

pub type PhysicsResult<T> = Result<T, String>;

pub fn positive_finite(name: &str, value: f64) -> PhysicsResult<()> {
    if value.is_finite() && value > 0.0 {
        return Ok(());
    }
    Err(format!("{name} must be finite and > 0, got {value}"))
}

pub fn non_negative_finite(name: &str, value: f64) -> PhysicsResult<()> {
    if value.is_finite() && value >= 0.0 {
        return Ok(());
    }
    Err(format!("{name} must be finite and >= 0, got {value}"))
}

pub fn finite_scalar(name: &str, value: f64) -> PhysicsResult<()> {
    if value.is_finite() {
        return Ok(());
    }
    Err(format!("{name} must be finite, got {value}"))
}

pub fn positive_steps(max_steps: usize) -> PhysicsResult<()> {
    if max_steps > 0 {
        return Ok(());
    }
    Err("max_steps must be > 0, got 0".to_string())
}

pub fn finite_slice(name: &str, values: &[f64]) -> PhysicsResult<()> {
    if values.iter().all(|value| value.is_finite()) {
        return Ok(());
    }
    Err(format!("{name} must contain only finite values"))
}

pub fn finite_vector(name: &str, value: &Vector3) -> PhysicsResult<()> {
    finite_slice(name, &[value.x, value.y, value.z])
}
