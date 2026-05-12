//! Primitive fitting kernels.
//!
//! This first primitive slice keeps the Python facade semantics intact:
//! Python still decides which primitive to try and supplies the reference
//! centroid/volume from `trimesh`, while Rust performs the O(n) vertex scan
//! for the bounding sphere radius.

use serde::{Deserialize, Serialize};

/// Fitted bounding sphere against a caller-supplied reference center.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingSphereFit {
    /// Sphere center in `(x, y, z)` order.
    pub center: [f32; 3],
    /// Maximum Euclidean distance from `center` to any input vertex.
    pub radius: f32,
    /// Volume of the fitted sphere.
    pub sphere_volume: f64,
    /// `mesh_volume / sphere_volume`.
    pub volume_ratio: f64,
    /// `1.0 - volume_ratio`, matching the Python primitive-fit scoring.
    pub error_metric: f64,
}

/// Errors returned by [`fit_bounding_sphere`].
#[derive(Debug)]
pub enum PrimitiveFitError {
    /// No vertices were supplied.
    EmptyVertices,
    /// An input vertex contained a non-finite coordinate.
    NonFiniteVertex { index: usize },
    /// The requested center contained a non-finite coordinate.
    NonFiniteCenter,
    /// The reference mesh volume was not positive and finite.
    InvalidMeshVolume,
}

impl core::fmt::Display for PrimitiveFitError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        match self {
            Self::EmptyVertices => write!(f, "bounding sphere fit requires at least one vertex"),
            Self::NonFiniteVertex { index } => {
                write!(f, "input vertex {index} contained non-finite coordinate")
            }
            Self::NonFiniteCenter => write!(f, "sphere center contained non-finite coordinate"),
            Self::InvalidMeshVolume => write!(f, "mesh volume must be positive and finite"),
        }
    }
}

impl std::error::Error for PrimitiveFitError {}

/// Fit a bounding sphere around `vertices` using a caller-supplied `center`.
///
/// # Preconditions
/// - `vertices` is non-empty.
/// - Every vertex coordinate and every center coordinate is finite.
/// - `mesh_volume` is positive and finite.
///
/// # Returns
/// A sphere whose radius is the maximum vertex distance from `center`, plus
/// the volume-ratio score used by `_cg_primitive_fitting.fit_sphere`.
pub fn fit_bounding_sphere(
    vertices: &[[f32; 3]],
    center: [f32; 3],
    mesh_volume: f64,
) -> Result<BoundingSphereFit, PrimitiveFitError> {
    if vertices.is_empty() {
        return Err(PrimitiveFitError::EmptyVertices);
    }
    if !center[0].is_finite() || !center[1].is_finite() || !center[2].is_finite() {
        return Err(PrimitiveFitError::NonFiniteCenter);
    }
    if !mesh_volume.is_finite() || mesh_volume <= 0.0 {
        return Err(PrimitiveFitError::InvalidMeshVolume);
    }

    let mut max_radius_sq = 0.0_f64;
    for (idx, vertex) in vertices.iter().enumerate() {
        if !vertex[0].is_finite() || !vertex[1].is_finite() || !vertex[2].is_finite() {
            return Err(PrimitiveFitError::NonFiniteVertex { index: idx });
        }

        let dx = (vertex[0] - center[0]) as f64;
        let dy = (vertex[1] - center[1]) as f64;
        let dz = (vertex[2] - center[2]) as f64;
        max_radius_sq = max_radius_sq.max(dx * dx + dy * dy + dz * dz);
    }

    let radius = max_radius_sq.sqrt() as f32;
    let radius_f64 = radius as f64;
    let sphere_volume = (4.0 / 3.0) * std::f64::consts::PI * radius_f64.powi(3);
    let volume_ratio = mesh_volume / sphere_volume;

    Ok(BoundingSphereFit {
        center,
        radius,
        sphere_volume,
        volume_ratio,
        error_metric: 1.0 - volume_ratio,
    })
}

#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Python-facing wrapper around [`BoundingSphereFit`].
#[cfg(feature = "python")]
#[pyclass(name = "BoundingSphereFit", module = "upstream_mesh", frozen)]
pub struct PyBoundingSphereFit {
    inner: BoundingSphereFit,
}

#[cfg(feature = "python")]
impl From<BoundingSphereFit> for PyBoundingSphereFit {
    fn from(inner: BoundingSphereFit) -> Self {
        Self { inner }
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl PyBoundingSphereFit {
    #[getter]
    fn center(&self) -> (f32, f32, f32) {
        (
            self.inner.center[0],
            self.inner.center[1],
            self.inner.center[2],
        )
    }

    #[getter]
    fn radius(&self) -> f32 {
        self.inner.radius
    }

    #[getter]
    fn sphere_volume(&self) -> f64 {
        self.inner.sphere_volume
    }

    #[getter]
    fn volume_ratio(&self) -> f64 {
        self.inner.volume_ratio
    }

    #[getter]
    fn error_metric(&self) -> f64 {
        self.inner.error_metric
    }

    fn __repr__(&self) -> String {
        format!(
            "BoundingSphereFit(radius={}, volume_ratio={})",
            self.inner.radius, self.inner.volume_ratio
        )
    }
}
