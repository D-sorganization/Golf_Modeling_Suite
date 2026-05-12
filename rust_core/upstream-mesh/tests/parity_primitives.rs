//! Primitive fitting parity and DbC tests.

use approx::assert_relative_eq;
use upstream_mesh::{fit_bounding_sphere, PrimitiveFitError};

#[test]
fn sphere_fit_matches_python_reference_formula() {
    let vertices = vec![
        [1.0_f32, 0.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, 2.0, 0.0],
        [0.0, 0.0, -3.0],
    ];
    let fit = fit_bounding_sphere(&vertices, [0.0, 0.0, 0.0], 10.0).expect("sphere fit");

    assert_relative_eq!(fit.radius, 3.0, max_relative = 1e-6);
    let expected_volume = (4.0 / 3.0) * std::f64::consts::PI * 27.0;
    assert_relative_eq!(fit.sphere_volume, expected_volume, max_relative = 1e-6);
    assert_relative_eq!(
        fit.volume_ratio,
        10.0 / expected_volume,
        max_relative = 1e-6
    );
    assert_relative_eq!(
        fit.error_metric,
        1.0 - 10.0 / expected_volume,
        max_relative = 1e-6
    );
}

#[test]
fn sphere_fit_respects_supplied_center() {
    let vertices = vec![[2.0_f32, 1.0, 1.0], [1.0, 4.0, 1.0]];
    let fit = fit_bounding_sphere(&vertices, [1.0, 1.0, 1.0], 4.0).expect("sphere fit");

    assert_eq!(fit.center, [1.0, 1.0, 1.0]);
    assert_relative_eq!(fit.radius, 3.0, max_relative = 1e-6);
}

#[test]
fn empty_vertices_return_error() {
    match fit_bounding_sphere(&[], [0.0, 0.0, 0.0], 1.0) {
        Err(PrimitiveFitError::EmptyVertices) => {}
        other => panic!("expected EmptyVertices, got {other:?}"),
    }
}

#[test]
fn non_finite_vertex_returns_indexed_error() {
    let vertices = vec![[0.0_f32, 0.0, 0.0], [f32::NAN, 0.0, 0.0]];
    match fit_bounding_sphere(&vertices, [0.0, 0.0, 0.0], 1.0) {
        Err(PrimitiveFitError::NonFiniteVertex { index: 1 }) => {}
        other => panic!("expected NonFiniteVertex {{ index: 1 }}, got {other:?}"),
    }
}

#[test]
fn invalid_volume_returns_error() {
    let vertices = vec![[0.0_f32, 0.0, 0.0]];
    match fit_bounding_sphere(&vertices, [0.0, 0.0, 0.0], 0.0) {
        Err(PrimitiveFitError::InvalidMeshVolume) => {}
        other => panic!("expected InvalidMeshVolume, got {other:?}"),
    }
}
