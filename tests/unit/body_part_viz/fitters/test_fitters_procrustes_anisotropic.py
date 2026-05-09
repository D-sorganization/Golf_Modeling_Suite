"""Unit tests for ``ProcrustesAnisotropicFitter``."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import ShapeFitter
from src.shared.python.body_part_viz.fitters import ProcrustesAnisotropicFitter
from tests.unit.body_part_viz.fitters._stubs import StubShape


def _rotation_about(axis: np.ndarray, angle: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    k = np.array(
        [
            [0.0, -axis[2], axis[1]],
            [axis[2], 0.0, -axis[0]],
            [-axis[1], axis[0], 0.0],
        ]
    )
    return np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * (k @ k)


def _binding(n: int = 6) -> MarkerBinding:
    return MarkerBinding(BindingKind.CLUSTER, tuple(f"m{i}" for i in range(n)))


@pytest.mark.unit
def test_satisfies_shape_fitter_protocol() -> None:
    assert isinstance(ProcrustesAnisotropicFitter(), ShapeFitter)


@pytest.mark.unit
def test_recovers_anisotropic_scale_only() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )
    s_true = np.array([2.0, 0.5, 1.5])
    moved = rest * s_true
    binding = _binding(6)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(6)}
    fit = ProcrustesAnisotropicFitter().fit(StubShape(), binding, markers)
    np.testing.assert_allclose(fit.rotation_matrix[0], np.eye(3), atol=1e-9)
    np.testing.assert_allclose(fit.scale[0], np.ones(3), atol=1e-9)
    np.testing.assert_allclose(fit.rotation_matrix[1], np.eye(3), atol=1e-9)
    np.testing.assert_allclose(fit.scale[1], s_true, atol=1e-9)


@pytest.mark.unit
def test_recovers_rotation_plus_anisotropic_scale() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )
    s_true = np.array([1.5, 2.0, 0.7])
    r_true = _rotation_about(np.array([0.0, 0.0, 1.0]), np.pi / 3)
    t_true = np.array([4.0, -2.0, 0.5])
    moved = ((rest * s_true) @ r_true.T) + t_true

    binding = _binding(6)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(6)}
    fit = ProcrustesAnisotropicFitter().fit(StubShape(), binding, markers)

    np.testing.assert_allclose(fit.rotation_matrix[1], r_true, atol=1e-6)
    np.testing.assert_allclose(fit.scale[1], s_true, atol=1e-6)
    np.testing.assert_allclose(fit.centroid[1], t_true, atol=1e-9)


@pytest.mark.unit
def test_nan_handling() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    binding = _binding(3)
    markers = {
        "m0": np.array([rest[0], [np.nan, np.nan, np.nan]]),
        "m1": np.array([rest[1], rest[1]]),
        "m2": np.array([rest[2], rest[2]]),
    }
    fit = ProcrustesAnisotropicFitter().fit(StubShape(), binding, markers)
    assert fit.valid_mask[0]
    assert not fit.valid_mask[1]
    np.testing.assert_allclose(fit.scale[1], np.ones(3))
    np.testing.assert_allclose(fit.rotation_matrix[1], np.eye(3))
    np.testing.assert_allclose(fit.centroid[1], fit.centroid[0])


@pytest.mark.unit
def test_wrong_binding_kind_raises() -> None:
    with pytest.raises(ValueError, match="CLUSTER"):
        ProcrustesAnisotropicFitter().fit(
            StubShape(),
            MarkerBinding(BindingKind.ON_MARKER, ("a",)),
            {"a": np.zeros((1, 3))},
        )


@pytest.mark.unit
def test_missing_marker_raises() -> None:
    binding = _binding(3)
    with pytest.raises(ValueError, match="not found"):
        ProcrustesAnisotropicFitter().fit(
            StubShape(), binding, {"m0": np.zeros((1, 3)), "m1": np.zeros((1, 3))}
        )


@pytest.mark.unit
def test_time_axis_mismatch_raises() -> None:
    binding = _binding(3)
    with pytest.raises(ValueError, match="expected T="):
        ProcrustesAnisotropicFitter().fit(
            StubShape(),
            binding,
            {
                "m0": np.zeros((3, 3)),
                "m1": np.zeros((4, 3)),
                "m2": np.zeros((3, 3)),
            },
        )


@pytest.mark.unit
def test_explicit_rest_positions_override() -> None:
    rest_override = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )
    s_true = np.array([3.0, 1.0, 0.25])
    moved = rest_override * s_true
    binding = _binding(6)
    markers = {f"m{i}": moved[i : i + 1] for i in range(6)}
    fit = ProcrustesAnisotropicFitter(rest_positions=rest_override).fit(
        StubShape(), binding, markers
    )
    np.testing.assert_allclose(fit.scale[0], s_true, atol=1e-9)


@pytest.mark.unit
def test_explicit_rest_positions_shape_validated() -> None:
    binding = _binding(3)
    markers = {f"m{i}": np.zeros((1, 3)) for i in range(3)}
    with pytest.raises(ValueError, match="rest_positions"):
        ProcrustesAnisotropicFitter(rest_positions=np.zeros((4, 3))).fit(
            StubShape(), binding, markers
        )


@pytest.mark.unit
def test_all_invalid_frames_are_handled() -> None:
    binding = _binding(3)
    nan = np.full((2, 3), np.nan)
    fit = ProcrustesAnisotropicFitter().fit(
        StubShape(), binding, {"m0": nan, "m1": nan, "m2": nan}
    )
    assert not fit.valid_mask.any()
    np.testing.assert_allclose(fit.scale, np.ones((2, 3)))
