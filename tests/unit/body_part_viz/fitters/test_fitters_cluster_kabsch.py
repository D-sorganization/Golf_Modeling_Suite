"""Unit tests for ``ClusterKabschFitter``."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import ShapeFitter
from src.shared.python.body_part_viz.fitters import ClusterKabschFitter
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


def _binding(n: int = 4) -> MarkerBinding:
    names = tuple(f"m{i}" for i in range(n))
    return MarkerBinding(kind=BindingKind.CLUSTER, marker_names=names)


@pytest.mark.unit
def test_satisfies_shape_fitter_protocol() -> None:
    assert isinstance(ClusterKabschFitter(), ShapeFitter)


@pytest.mark.unit
def test_recovers_known_rotation_and_translation() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    r_true = _rotation_about(np.array([0.0, 0.0, 1.0]), np.pi / 4)
    t_true = np.array([10.0, -3.0, 2.0])
    moved = (rest @ r_true.T) + t_true

    binding = _binding(4)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(4)}
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)

    assert fit.valid_mask.all()
    np.testing.assert_allclose(fit.rotation_matrix[0], np.eye(3), atol=1e-9)
    np.testing.assert_allclose(fit.centroid[0], rest.mean(axis=0), atol=1e-12)
    np.testing.assert_allclose(fit.rotation_matrix[1], r_true, atol=1e-9)
    expected_centroid = rest.mean(axis=0) @ r_true.T + t_true
    np.testing.assert_allclose(fit.centroid[1], expected_centroid, atol=1e-9)
    np.testing.assert_allclose(fit.scale, np.ones_like(fit.scale))


@pytest.mark.unit
def test_determinant_is_plus_one() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [-1.0, -1.0, -1.0],
        ]
    )
    r_true = _rotation_about(np.array([1.0, 1.0, 0.0]), 0.7)
    moved = rest @ r_true.T
    binding = _binding(4)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(4)}
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)
    for r in fit.rotation_matrix:
        assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.unit
def test_reflection_input_yields_proper_rotation() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
        ]
    )
    reflect = np.diag([-1.0, 1.0, 1.0])
    moved = rest @ reflect.T
    binding = _binding(4)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(4)}
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)
    for r in fit.rotation_matrix:
        assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.unit
def test_coplanar_markers_still_produce_valid_rotation() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
        ]
    )
    r_true = _rotation_about(np.array([0.0, 0.0, 1.0]), 0.5)
    moved = rest @ r_true.T
    binding = _binding(3)
    markers = {f"m{i}": np.array([rest[i], moved[i]]) for i in range(3)}
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)
    np.testing.assert_allclose(fit.rotation_matrix[1], r_true, atol=1e-9)


@pytest.mark.unit
def test_nan_in_frame_marks_invalid() -> None:
    rest = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    binding = _binding(3)
    markers = {
        "m0": np.array([rest[0], rest[0], [np.nan, np.nan, np.nan]]),
        "m1": np.array([rest[1], rest[1], rest[1]]),
        "m2": np.array([rest[2], rest[2], rest[2]]),
    }
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)
    assert fit.valid_mask[0]
    assert fit.valid_mask[1]
    assert not fit.valid_mask[2]
    np.testing.assert_allclose(fit.centroid[2], fit.centroid[1])
    np.testing.assert_allclose(fit.rotation_matrix[2], np.eye(3))


@pytest.mark.unit
def test_leading_invalid_frame_uses_zero_centroid() -> None:
    binding = _binding(3)
    markers = {
        "m0": np.array([[np.nan, 0.0, 0.0], [1.0, 0.0, 0.0]]),
        "m1": np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]]),
        "m2": np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]),
    }
    fit = ClusterKabschFitter().fit(StubShape(), binding, markers)
    assert not fit.valid_mask[0]
    np.testing.assert_allclose(fit.centroid[0], np.zeros(3))


@pytest.mark.unit
def test_wrong_binding_kind_raises() -> None:
    binding = MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))
    with pytest.raises(ValueError, match="CLUSTER"):
        ClusterKabschFitter().fit(
            StubShape(),
            binding,
            {"a": np.zeros((1, 3)), "b": np.zeros((1, 3))},
        )


@pytest.mark.unit
def test_missing_marker_raises() -> None:
    binding = _binding(3)
    with pytest.raises(ValueError, match="not found"):
        ClusterKabschFitter().fit(
            StubShape(), binding, {"m0": np.zeros((1, 3)), "m1": np.zeros((1, 3))}
        )


@pytest.mark.unit
def test_time_axis_mismatch_raises() -> None:
    binding = _binding(3)
    with pytest.raises(ValueError, match="expected T="):
        ClusterKabschFitter().fit(
            StubShape(),
            binding,
            {
                "m0": np.zeros((3, 3)),
                "m1": np.zeros((3, 3)),
                "m2": np.zeros((4, 3)),
            },
        )


@pytest.mark.unit
def test_marker_must_be_T3() -> None:
    binding = _binding(3)
    with pytest.raises(ValueError, match=r"\(T, 3\)"):
        ClusterKabschFitter().fit(
            StubShape(),
            binding,
            {
                "m0": np.zeros((3, 2)),
                "m1": np.zeros((3, 2)),
                "m2": np.zeros((3, 2)),
            },
        )


@pytest.mark.unit
def test_explicit_rest_positions_override() -> None:
    rest_override = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
        ]
    )
    r_true = _rotation_about(np.array([0.0, 0.0, 1.0]), np.pi / 6)
    moved = rest_override @ r_true.T
    binding = _binding(4)
    markers = {f"m{i}": moved[i : i + 1] for i in range(4)}
    fit = ClusterKabschFitter(rest_positions=rest_override).fit(
        StubShape(), binding, markers
    )
    np.testing.assert_allclose(fit.rotation_matrix[0], r_true, atol=1e-9)


@pytest.mark.unit
def test_explicit_rest_positions_shape_validated() -> None:
    bad = np.zeros((2, 3))
    binding = _binding(3)
    markers = {
        "m0": np.zeros((1, 3)),
        "m1": np.zeros((1, 3)),
        "m2": np.zeros((1, 3)),
    }
    with pytest.raises(ValueError, match="rest_positions"):
        ClusterKabschFitter(rest_positions=bad).fit(StubShape(), binding, markers)


@pytest.mark.unit
def test_all_invalid_frames_are_handled() -> None:
    binding = _binding(3)
    nan = np.full((2, 3), np.nan)
    fit = ClusterKabschFitter().fit(
        StubShape(), binding, {"m0": nan, "m1": nan, "m2": nan}
    )
    assert not fit.valid_mask.any()
    np.testing.assert_allclose(fit.centroid, np.zeros((2, 3)))
