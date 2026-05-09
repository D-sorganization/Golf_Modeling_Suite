"""Unit tests for ``body_part_viz.fitters._kabsch``."""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz.fitters._kabsch import (
    anisotropic_scale,
    kabsch_rotation,
)


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


@pytest.mark.unit
def test_kabsch_recovers_known_rotation_z() -> None:
    rng = np.random.default_rng(0)
    p = rng.standard_normal((20, 3))
    p = p - p.mean(axis=0)
    r_true = _rotation_about(np.array([0.0, 0.0, 1.0]), np.pi / 3)
    q = p @ r_true.T
    r = kabsch_rotation(p, q)
    np.testing.assert_allclose(r, r_true, atol=1e-9)


@pytest.mark.unit
def test_kabsch_recovers_known_rotation_general() -> None:
    rng = np.random.default_rng(7)
    p = rng.standard_normal((10, 3))
    p = p - p.mean(axis=0)
    r_true = _rotation_about(np.array([1.0, 2.0, -3.0]), 1.234)
    q = p @ r_true.T
    r = kabsch_rotation(p, q)
    np.testing.assert_allclose(r, r_true, atol=1e-9)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.unit
def test_kabsch_reflection_guard() -> None:
    """Reflected target must yield a proper rotation (no determinant -1)."""
    p = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
        ]
    )
    reflect = np.diag([-1.0, 1.0, 1.0])
    q = p @ reflect.T
    r = kabsch_rotation(p, q)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.unit
def test_kabsch_collinear_input_does_not_crash() -> None:
    """Degenerate (collinear) input still returns a proper rotation."""
    p = np.array([[-1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    r_true = _rotation_about(np.array([0.0, 1.0, 0.0]), np.pi / 4)
    q = p @ r_true.T
    r = kabsch_rotation(p, q)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)
    np.testing.assert_allclose(p @ r.T, q, atol=1e-9)


@pytest.mark.unit
def test_kabsch_shape_validation() -> None:
    with pytest.raises(ValueError, match="same shape"):
        kabsch_rotation(np.zeros((3, 3)), np.zeros((4, 3)))
    with pytest.raises(ValueError, match=r"shape \(N, 3\)"):
        kabsch_rotation(np.zeros((3, 2)), np.zeros((3, 2)))
    with pytest.raises(ValueError, match="at least one point"):
        kabsch_rotation(np.zeros((0, 3)), np.zeros((0, 3)))


@pytest.mark.unit
def test_anisotropic_scale_recovers_known_factors() -> None:
    rng = np.random.default_rng(2)
    p = rng.standard_normal((20, 3))
    p = p - p.mean(axis=0)
    s_true = np.array([2.0, 0.5, 1.5])
    q = p * s_true
    s = anisotropic_scale(p, q)
    np.testing.assert_allclose(s, s_true, atol=1e-9)


@pytest.mark.unit
def test_anisotropic_scale_falls_back_on_degenerate_axis() -> None:
    p = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    q = np.array([[2.0, 5.0, 5.0], [-2.0, -5.0, 5.0]])
    s = anisotropic_scale(p, q)
    assert s[0] == pytest.approx(2.0)
    assert s[1] == pytest.approx(1.0)
    assert s[2] == pytest.approx(1.0)
