"""Unit tests for ``BetweenTwoMarkersFitter``."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import ShapeFitter
from src.shared.python.body_part_viz.fitters import BetweenTwoMarkersFitter
from tests.unit.body_part_viz.fitters._stubs import StubShape


def _binding(rest_length: float = 1.0) -> MarkerBinding:
    return MarkerBinding(
        kind=BindingKind.BETWEEN_TWO,
        marker_names=("a", "b"),
        rest_dimensions=(rest_length,),
    )


@pytest.mark.unit
def test_satisfies_shape_fitter_protocol() -> None:
    assert isinstance(BetweenTwoMarkersFitter(), ShapeFitter)


@pytest.mark.unit
def test_centroid_is_midpoint() -> None:
    n = 7
    a = np.tile(np.array([0.0, 0.0, 0.0]), (n, 1))
    b = np.column_stack([np.linspace(1.0, 7.0, n), np.zeros(n), np.zeros(n)])
    fitter = BetweenTwoMarkersFitter()
    fit = fitter.fit(StubShape(), _binding(rest_length=2.0), {"a": a, "b": b})
    expected_mid = 0.5 * (a + b)
    np.testing.assert_allclose(fit.centroid, expected_mid, atol=1e-12)
    assert fit.shape_id == "stub"
    assert fit.valid_mask.all()


@pytest.mark.unit
def test_rotation_aligns_x_axis_to_segment_x() -> None:
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[3.0, 0.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(
        StubShape(), _binding(rest_length=1.0), {"a": a, "b": b}
    )
    r = fit.rotation_matrix[0]
    np.testing.assert_allclose(r[:, 0], np.array([1.0, 0.0, 0.0]), atol=1e-12)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-12)
    np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)
    np.testing.assert_allclose(fit.scale[0], np.array([3.0, 1.0, 1.0]), atol=1e-12)


@pytest.mark.unit
def test_rotation_aligns_x_axis_to_segment_y() -> None:
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[0.0, 2.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(
        StubShape(), _binding(rest_length=1.0), {"a": a, "b": b}
    )
    r = fit.rotation_matrix[0]
    np.testing.assert_allclose(r[:, 0], np.array([0.0, 1.0, 0.0]), atol=1e-12)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-12)
    np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)


@pytest.mark.unit
def test_rotation_aligns_x_axis_to_segment_z() -> None:
    """Near-Z axis should still produce a stable orthonormal basis."""
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[0.0, 0.0, 4.0]])
    fit = BetweenTwoMarkersFitter().fit(
        StubShape(), _binding(rest_length=2.0), {"a": a, "b": b}
    )
    r = fit.rotation_matrix[0]
    np.testing.assert_allclose(r[:, 0], np.array([0.0, 0.0, 1.0]), atol=1e-12)
    np.testing.assert_allclose(r.T @ r, np.eye(3), atol=1e-12)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-12)
    np.testing.assert_allclose(fit.scale[0], np.array([2.0, 1.0, 1.0]), atol=1e-12)


@pytest.mark.unit
def test_nan_marker_marks_frame_invalid() -> None:
    n = 5
    a = np.zeros((n, 3))
    b = np.column_stack([np.arange(1.0, n + 1), np.zeros(n), np.zeros(n)])
    a[2] = np.nan
    fit = BetweenTwoMarkersFitter().fit(StubShape(), _binding(), {"a": a, "b": b})
    assert not fit.valid_mask[2]
    assert fit.valid_mask[0] and fit.valid_mask[1] and fit.valid_mask[3]
    np.testing.assert_allclose(fit.rotation_matrix[2], np.eye(3))
    np.testing.assert_allclose(fit.scale[2], np.ones(3))


@pytest.mark.unit
def test_invalid_frame_centroid_falls_back_to_previous_valid() -> None:
    a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [np.nan, np.nan, np.nan]])
    b = np.array([[2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(StubShape(), _binding(), {"a": a, "b": b})
    np.testing.assert_allclose(fit.centroid[2], fit.centroid[1])


@pytest.mark.unit
def test_leading_invalid_frame_uses_zero_centroid() -> None:
    a = np.array([[np.nan, 0.0, 0.0], [1.0, 0.0, 0.0]])
    b = np.array([[1.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(StubShape(), _binding(), {"a": a, "b": b})
    assert not fit.valid_mask[0]
    np.testing.assert_allclose(fit.centroid[0], np.zeros(3))


@pytest.mark.unit
def test_coincident_markers_are_invalid() -> None:
    a = np.array([[1.0, 1.0, 1.0]])
    b = np.array([[1.0, 1.0, 1.0]])
    fit = BetweenTwoMarkersFitter().fit(StubShape(), _binding(), {"a": a, "b": b})
    assert not fit.valid_mask[0]
    np.testing.assert_allclose(fit.centroid[0], np.array([1.0, 1.0, 1.0]))


@pytest.mark.unit
def test_coincident_then_valid_holds_centroid() -> None:
    """Mid-trajectory coincident frame uses prior-valid centroid fallback."""
    a = np.array([[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]])
    b = np.array([[1.0, 0.0, 0.0], [2.0, 2.0, 2.0]])
    fit = BetweenTwoMarkersFitter().fit(StubShape(), _binding(), {"a": a, "b": b})
    assert fit.valid_mask[0]
    assert not fit.valid_mask[1]
    np.testing.assert_allclose(fit.centroid[1], fit.centroid[0])


@pytest.mark.unit
def test_wrong_binding_kind_raises() -> None:
    binding = MarkerBinding(kind=BindingKind.CLUSTER, marker_names=("a", "b", "c"))
    fitter = BetweenTwoMarkersFitter()
    with pytest.raises(ValueError, match="BETWEEN_TWO"):
        fitter.fit(
            StubShape(),
            binding,
            {
                "a": np.zeros((1, 3)),
                "b": np.zeros((1, 3)),
                "c": np.zeros((1, 3)),
            },
        )


@pytest.mark.unit
def test_missing_marker_raises() -> None:
    fitter = BetweenTwoMarkersFitter()
    with pytest.raises(ValueError, match="not found"):
        fitter.fit(StubShape(), _binding(), {"a": np.zeros((1, 3))})


@pytest.mark.unit
def test_marker_shape_mismatch_raises() -> None:
    fitter = BetweenTwoMarkersFitter()
    with pytest.raises(ValueError, match="disagree"):
        fitter.fit(
            StubShape(),
            _binding(),
            {"a": np.zeros((3, 3)), "b": np.zeros((4, 3))},
        )


@pytest.mark.unit
def test_marker_array_must_be_T3() -> None:
    fitter = BetweenTwoMarkersFitter()
    with pytest.raises(ValueError, match=r"\(T, 3\)"):
        fitter.fit(
            StubShape(),
            _binding(),
            {"a": np.zeros((3, 2)), "b": np.zeros((3, 2))},
        )


@pytest.mark.unit
def test_default_rest_length_when_unspecified() -> None:
    binding = MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))
    a = np.array([[0.0, 0.0, 0.0]])
    b = np.array([[5.0, 0.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(StubShape(), binding, {"a": a, "b": b})
    np.testing.assert_allclose(fit.scale[0], np.array([5.0, 1.0, 1.0]))


@pytest.mark.unit
def test_shape_id_propagates() -> None:
    a = np.zeros((1, 3))
    b = np.array([[1.0, 0.0, 0.0]])
    fit = BetweenTwoMarkersFitter().fit(
        StubShape("custom_id"), _binding(), {"a": a, "b": b}
    )
    assert fit.shape_id == "custom_id"
