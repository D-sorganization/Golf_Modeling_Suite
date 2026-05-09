"""Tests for ``body_part_viz.shapes.primitives``.

Covers vertex/face counts, bounding boxes, transform round-trips,
DbC validation, and Protocol conformance for all five primitive shapes.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import BodyPartShape
from src.shared.python.body_part_viz.shapes import (
    CapsuleShape,
    CompositeShape,
    CylinderShape,
    EllipsoidShape,
    LineShape,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _binding() -> MarkerBinding:
    return MarkerBinding(BindingKind.BETWEEN_TWO, ("a", "b"))


def _identity_fit(shape_id: str, n_frames: int = 3) -> FittedShape:
    return FittedShape(
        shape_id=shape_id,
        binding=_binding(),
        centroid=np.zeros((n_frames, 3)),
        rotation_matrix=np.tile(np.eye(3), (n_frames, 1, 1)),
        scale=np.ones((n_frames, 3)),
        valid_mask=np.ones(n_frames, dtype=bool),
    )


def _placed_fit(
    shape_id: str,
    centroid: np.ndarray,
    rotation: np.ndarray,
    scale: np.ndarray,
) -> FittedShape:
    return FittedShape(
        shape_id=shape_id,
        binding=_binding(),
        centroid=centroid,
        rotation_matrix=rotation,
        scale=scale,
        valid_mask=np.ones(centroid.shape[0], dtype=bool),
    )


def _bbox(verts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Axis-aligned bounding box ``(lo, hi)``.

    Uses Python's builtin ``min``/``max`` over a tolist() copy to
    sidestep a numpy reload + ``_NoValue`` sentinel issue that
    pytest-cov can trigger when other extension modules (e.g. mujoco)
    re-import numpy.
    """
    cols = [[row[i] for row in verts.tolist()] for i in range(3)]
    lo = np.array([min(c) for c in cols])
    hi = np.array([max(c) for c in cols])
    return lo, hi


# ---------------------------------------------------------------------------
# LineShape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_line_shape_id_and_dims() -> None:
    s = LineShape(2.5)
    assert s.shape_id == "line"
    assert s.rest_dimensions == (2.5,)


@pytest.mark.unit
def test_line_vertex_and_face_counts() -> None:
    s = LineShape(1.0)
    assert s.vertices_at_rest().shape == (2, 3)
    assert s.faces().shape == (0, 3)


@pytest.mark.unit
def test_line_bbox_at_rest_matches_length() -> None:
    s = LineShape(3.0)
    lo, hi = _bbox(s.vertices_at_rest())
    assert hi[0] - lo[0] == pytest.approx(3.0)
    assert lo[1] == 0.0 and hi[1] == 0.0
    assert lo[2] == 0.0 and hi[2] == 0.0


@pytest.mark.unit
def test_line_centred_at_origin() -> None:
    s = LineShape(4.0)
    rows = s.vertices_at_rest().tolist()
    centroid = np.array([sum(r[i] for r in rows) / len(rows) for i in range(3)])
    assert np.allclose(centroid, 0.0)


@pytest.mark.unit
def test_line_transform_identity_round_trip() -> None:
    s = LineShape(1.0)
    fitted = _identity_fit("line", n_frames=4)
    out = s.transform(fitted)
    assert out.shape == (4, 2, 3)
    rest = s.vertices_at_rest()
    for t in range(4):
        np.testing.assert_allclose(out[t], rest)


@pytest.mark.unit
def test_line_transform_rotation_about_z() -> None:
    """A 90° rotation about z swaps x→y and -x→-y."""
    s = LineShape(2.0)
    R = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    rot = R[np.newaxis]
    fit = _placed_fit(
        "line",
        centroid=np.zeros((1, 3)),
        rotation=rot,
        scale=np.ones((1, 3)),
    )
    out = s.transform(fit)
    np.testing.assert_allclose(out[0, 0], [0.0, -1.0, 0.0], atol=1e-12)
    np.testing.assert_allclose(out[0, 1], [0.0, +1.0, 0.0], atol=1e-12)


@pytest.mark.unit
def test_line_transform_centroid_translation() -> None:
    s = LineShape(2.0)
    centroid = np.array([[10.0, 20.0, 30.0]])
    fit = _placed_fit(
        "line",
        centroid=centroid,
        rotation=np.eye(3)[np.newaxis],
        scale=np.ones((1, 3)),
    )
    out = s.transform(fit)
    np.testing.assert_allclose(out[0, 0], [9.0, 20.0, 30.0])
    np.testing.assert_allclose(out[0, 1], [11.0, 20.0, 30.0])


@pytest.mark.unit
def test_line_rejects_negative_length() -> None:
    with pytest.raises(ValueError, match="rest_length"):
        LineShape(-1.0)


@pytest.mark.unit
def test_line_rejects_zero_length() -> None:
    with pytest.raises(ValueError, match="rest_length"):
        LineShape(0.0)


@pytest.mark.unit
def test_line_rejects_nan_length() -> None:
    with pytest.raises(ValueError, match="rest_length"):
        LineShape(float("nan"))


@pytest.mark.unit
def test_line_transform_rejects_wrong_shape_id() -> None:
    s = LineShape(1.0)
    fit = _identity_fit("cylinder")
    with pytest.raises(ValueError, match="shape_id"):
        s.transform(fit)


@pytest.mark.unit
def test_line_transform_rejects_non_fitted() -> None:
    s = LineShape(1.0)
    with pytest.raises(TypeError, match="FittedShape"):
        s.transform("not a fit")  # type: ignore[arg-type]


@pytest.mark.unit
def test_line_satisfies_protocol() -> None:
    assert isinstance(LineShape(1.0), BodyPartShape)


@pytest.mark.unit
def test_line_is_frozen() -> None:
    s = LineShape(1.0)
    with pytest.raises(Exception):  # noqa: B017
        s.rest_length = 2.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CylinderShape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cylinder_shape_id_and_dims() -> None:
    s = CylinderShape(2.0, 0.3)
    assert s.shape_id == "cylinder"
    assert s.rest_dimensions == (2.0, 0.3)


@pytest.mark.unit
def test_cylinder_default_vertex_face_counts() -> None:
    s = CylinderShape(1.0, 0.1)  # n_segments default 16
    assert s.vertices_at_rest().shape == (2 * 16 + 2, 3)
    assert s.faces().shape == (4 * 16, 3)


@pytest.mark.unit
@pytest.mark.parametrize("n", [3, 8, 32])
def test_cylinder_counts_scale_with_segments(n: int) -> None:
    s = CylinderShape(1.0, 0.1, n_segments=n)
    assert s.vertices_at_rest().shape == (2 * n + 2, 3)
    assert s.faces().shape == (4 * n, 3)


@pytest.mark.unit
def test_cylinder_bbox_matches_length_and_radius() -> None:
    s = CylinderShape(2.0, 0.5)
    lo, hi = _bbox(s.vertices_at_rest())
    assert hi[0] - lo[0] == pytest.approx(2.0)
    assert hi[1] - lo[1] == pytest.approx(1.0)
    assert hi[2] - lo[2] == pytest.approx(1.0)


@pytest.mark.unit
def test_cylinder_face_indices_in_range() -> None:
    s = CylinderShape(1.0, 0.5, n_segments=8)
    n_v = s.vertices_at_rest().shape[0]
    f = s.faces()
    flat = [int(x) for row in f.tolist() for x in row]
    assert min(flat) >= 0 and max(flat) < n_v


@pytest.mark.unit
def test_cylinder_transform_identity_round_trip() -> None:
    s = CylinderShape(1.0, 0.1, n_segments=6)
    fit = _identity_fit("cylinder", n_frames=2)
    out = s.transform(fit)
    rest = s.vertices_at_rest()
    assert out.shape == (2, rest.shape[0], 3)
    np.testing.assert_allclose(out[0], rest)
    np.testing.assert_allclose(out[1], rest)


@pytest.mark.unit
def test_cylinder_transform_anisotropic_scale() -> None:
    """Length scale on x, radius scale on y/z."""
    s = CylinderShape(1.0, 1.0, n_segments=4)
    fit = _placed_fit(
        "cylinder",
        centroid=np.zeros((1, 3)),
        rotation=np.eye(3)[np.newaxis],
        scale=np.array([[2.0, 3.0, 3.0]]),
    )
    out = s.transform(fit)[0]
    rest = s.vertices_at_rest()
    np.testing.assert_allclose(out[:, 0], rest[:, 0] * 2.0)
    np.testing.assert_allclose(out[:, 1], rest[:, 1] * 3.0)
    np.testing.assert_allclose(out[:, 2], rest[:, 2] * 3.0)


@pytest.mark.unit
def test_cylinder_rejects_negative_length() -> None:
    with pytest.raises(ValueError, match="rest_length"):
        CylinderShape(-1.0, 0.1)


@pytest.mark.unit
def test_cylinder_rejects_negative_radius() -> None:
    with pytest.raises(ValueError, match="rest_radius"):
        CylinderShape(1.0, -0.1)


@pytest.mark.unit
def test_cylinder_rejects_zero_radius() -> None:
    with pytest.raises(ValueError, match="rest_radius"):
        CylinderShape(1.0, 0.0)


@pytest.mark.unit
def test_cylinder_rejects_too_few_segments() -> None:
    with pytest.raises(ValueError, match="n_segments"):
        CylinderShape(1.0, 0.1, n_segments=2)


@pytest.mark.unit
def test_cylinder_rejects_non_int_segments() -> None:
    with pytest.raises(TypeError, match="n_segments"):
        CylinderShape(1.0, 0.1, n_segments=8.0)  # type: ignore[arg-type]


@pytest.mark.unit
def test_cylinder_rejects_bool_segments() -> None:
    with pytest.raises(TypeError, match="n_segments"):
        CylinderShape(1.0, 0.1, n_segments=True)  # type: ignore[arg-type]


@pytest.mark.unit
def test_cylinder_satisfies_protocol() -> None:
    assert isinstance(CylinderShape(1.0, 0.1), BodyPartShape)


# ---------------------------------------------------------------------------
# EllipsoidShape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ellipsoid_shape_id_and_dims() -> None:
    s = EllipsoidShape(1.0, 2.0, 3.0)
    assert s.shape_id == "ellipsoid"
    assert s.rest_dimensions == (1.0, 2.0, 3.0)


@pytest.mark.unit
def test_ellipsoid_vertex_count_default() -> None:
    s = EllipsoidShape(1.0, 1.0, 1.0)  # default n_lat=12, n_lon=24
    assert s.vertices_at_rest().shape == ((12 + 1) * (24 + 1), 3)
    assert s.faces().shape == (2 * 12 * 24, 3)


@pytest.mark.unit
@pytest.mark.parametrize(("n_lat", "n_lon"), [(2, 3), (4, 8), (16, 32)])
def test_ellipsoid_counts_scale(n_lat: int, n_lon: int) -> None:
    s = EllipsoidShape(1.0, 1.0, 1.0, n_lat=n_lat, n_lon=n_lon)
    assert s.vertices_at_rest().shape == ((n_lat + 1) * (n_lon + 1), 3)
    assert s.faces().shape == (2 * n_lat * n_lon, 3)


@pytest.mark.unit
def test_ellipsoid_bbox_matches_axes() -> None:
    s = EllipsoidShape(1.5, 2.5, 0.5)
    lo, hi = _bbox(s.vertices_at_rest())
    assert hi[0] - lo[0] == pytest.approx(2 * 1.5, abs=1e-12)
    assert hi[1] - lo[1] == pytest.approx(2 * 2.5, abs=1e-12)
    assert hi[2] - lo[2] == pytest.approx(2 * 0.5, abs=1e-12)


@pytest.mark.unit
def test_ellipsoid_vertices_lie_on_surface() -> None:
    """All vertices satisfy ``(x/a)^2 + (y/b)^2 + (z/c)^2 == 1``."""
    a, b, c = 1.5, 2.5, 0.5
    s = EllipsoidShape(a, b, c)
    v = s.vertices_at_rest()
    rsq = (v[:, 0] / a) ** 2 + (v[:, 1] / b) ** 2 + (v[:, 2] / c) ** 2
    np.testing.assert_allclose(rsq, 1.0, atol=1e-9)


@pytest.mark.unit
def test_ellipsoid_face_indices_in_range() -> None:
    s = EllipsoidShape(1.0, 1.0, 1.0, n_lat=3, n_lon=4)
    n_v = s.vertices_at_rest().shape[0]
    f = s.faces()
    flat = [int(x) for row in f.tolist() for x in row]
    assert min(flat) >= 0 and max(flat) < n_v


@pytest.mark.unit
def test_ellipsoid_transform_identity_round_trip() -> None:
    s = EllipsoidShape(1.0, 2.0, 3.0, n_lat=3, n_lon=4)
    fit = _identity_fit("ellipsoid", n_frames=2)
    out = s.transform(fit)
    rest = s.vertices_at_rest()
    assert out.shape == (2, rest.shape[0], 3)
    np.testing.assert_allclose(out[0], rest)


@pytest.mark.unit
def test_ellipsoid_transform_with_rotation_centroid() -> None:
    s = EllipsoidShape(1.0, 1.0, 1.0, n_lat=2, n_lon=3)
    # Rotate 180° about z and translate by (5, 0, 0).
    R = np.array([[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])
    fit = _placed_fit(
        "ellipsoid",
        centroid=np.array([[5.0, 0.0, 0.0]]),
        rotation=R[np.newaxis],
        scale=np.ones((1, 3)),
    )
    out = s.transform(fit)[0]
    rest = s.vertices_at_rest()
    expected = rest @ R.T + np.array([5.0, 0.0, 0.0])
    np.testing.assert_allclose(out, expected, atol=1e-12)


@pytest.mark.unit
def test_ellipsoid_rejects_negative_axis() -> None:
    with pytest.raises(ValueError, match="^a"):
        EllipsoidShape(-1.0, 1.0, 1.0)
    with pytest.raises(ValueError, match="^b"):
        EllipsoidShape(1.0, -1.0, 1.0)
    with pytest.raises(ValueError, match="^c"):
        EllipsoidShape(1.0, 1.0, -1.0)


@pytest.mark.unit
def test_ellipsoid_rejects_too_few_lat() -> None:
    with pytest.raises(ValueError, match="n_lat"):
        EllipsoidShape(1.0, 1.0, 1.0, n_lat=1, n_lon=4)


@pytest.mark.unit
def test_ellipsoid_rejects_too_few_lon() -> None:
    with pytest.raises(ValueError, match="n_lon"):
        EllipsoidShape(1.0, 1.0, 1.0, n_lat=4, n_lon=2)


@pytest.mark.unit
def test_ellipsoid_satisfies_protocol() -> None:
    assert isinstance(EllipsoidShape(1.0, 2.0, 3.0), BodyPartShape)


# ---------------------------------------------------------------------------
# CapsuleShape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_capsule_shape_id_and_dims() -> None:
    s = CapsuleShape(2.0, 0.3)
    assert s.shape_id == "capsule"
    assert s.rest_dimensions == (2.0, 0.3)


@pytest.mark.unit
def test_capsule_vertex_face_counts_default() -> None:
    s = CapsuleShape(1.0, 0.1)  # default n_segments=16, n_lat=6
    n_seg = 16
    n_lat = 6
    expected_v = 2 * n_seg + 2 * (n_lat + 1) * (n_seg + 1)
    expected_f = 2 * n_seg + 2 * (2 * n_lat * n_seg)
    assert s.vertices_at_rest().shape == (expected_v, 3)
    assert s.faces().shape == (expected_f, 3)


@pytest.mark.unit
def test_capsule_bbox_matches_full_extent() -> None:
    """End-to-end x-extent is L + 2r; cross-section is 2r."""
    L, r = 1.0, 0.4
    s = CapsuleShape(L, r)
    lo, hi = _bbox(s.vertices_at_rest())
    assert hi[0] - lo[0] == pytest.approx(L + 2 * r, abs=1e-12)
    assert hi[1] - lo[1] == pytest.approx(2 * r, abs=1e-12)
    assert hi[2] - lo[2] == pytest.approx(2 * r, abs=1e-12)


@pytest.mark.unit
def test_capsule_centred_at_origin() -> None:
    s = CapsuleShape(2.0, 0.5)
    lo, hi = _bbox(s.vertices_at_rest())
    np.testing.assert_allclose(lo + hi, 0.0, atol=1e-12)


@pytest.mark.unit
def test_capsule_face_indices_in_range() -> None:
    s = CapsuleShape(1.0, 0.5, n_segments=4, n_lat=3)
    n_v = s.vertices_at_rest().shape[0]
    f = s.faces()
    flat = [int(x) for row in f.tolist() for x in row]
    assert min(flat) >= 0 and max(flat) < n_v


@pytest.mark.unit
def test_capsule_transform_identity_round_trip() -> None:
    s = CapsuleShape(1.0, 0.2, n_segments=4, n_lat=2)
    fit = _identity_fit("capsule", n_frames=3)
    out = s.transform(fit)
    rest = s.vertices_at_rest()
    assert out.shape == (3, rest.shape[0], 3)
    for t in range(3):
        np.testing.assert_allclose(out[t], rest)


@pytest.mark.unit
def test_capsule_hemispheres_on_surface() -> None:
    """Hemisphere vertices lie on the spheres centred at ±L/2."""
    L, r = 2.0, 0.3
    s = CapsuleShape(L, r, n_segments=4, n_lat=3)
    n = 4
    v = s.vertices_at_rest()
    # Top hemisphere block.
    n_hemi = (3 + 1) * (4 + 1)
    top_block = v[2 * n : 2 * n + n_hemi]
    bot_block = v[2 * n + n_hemi : 2 * n + 2 * n_hemi]
    top_centre = np.array([L / 2, 0.0, 0.0])
    bot_centre = np.array([-L / 2, 0.0, 0.0])
    np.testing.assert_allclose(
        np.linalg.norm(top_block - top_centre, axis=1), r, atol=1e-12
    )
    np.testing.assert_allclose(
        np.linalg.norm(bot_block - bot_centre, axis=1), r, atol=1e-12
    )


@pytest.mark.unit
def test_capsule_rejects_negative_length() -> None:
    with pytest.raises(ValueError, match="rest_length"):
        CapsuleShape(-1.0, 0.1)


@pytest.mark.unit
def test_capsule_rejects_negative_radius() -> None:
    with pytest.raises(ValueError, match="rest_radius"):
        CapsuleShape(1.0, -0.1)


@pytest.mark.unit
def test_capsule_rejects_too_few_segments() -> None:
    with pytest.raises(ValueError, match="n_segments"):
        CapsuleShape(1.0, 0.1, n_segments=2)


@pytest.mark.unit
def test_capsule_rejects_too_few_lat() -> None:
    with pytest.raises(ValueError, match="n_lat"):
        CapsuleShape(1.0, 0.1, n_lat=1)


@pytest.mark.unit
def test_capsule_satisfies_protocol() -> None:
    assert isinstance(CapsuleShape(1.0, 0.1), BodyPartShape)


# ---------------------------------------------------------------------------
# CompositeShape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_composite_shape_id_and_dims() -> None:
    parts = (LineShape(1.0), CylinderShape(2.0, 0.3))
    c = CompositeShape(parts)
    assert c.shape_id == "composite"
    assert c.rest_dimensions == (1.0, 2.0, 0.3)


@pytest.mark.unit
def test_composite_vertex_count_is_sum() -> None:
    line = LineShape(1.0)
    cyl = CylinderShape(2.0, 0.5, n_segments=4)
    c = CompositeShape((line, cyl))
    expected = line.vertices_at_rest().shape[0] + cyl.vertices_at_rest().shape[0]
    assert c.vertices_at_rest().shape == (expected, 3)


@pytest.mark.unit
def test_composite_face_count_is_sum() -> None:
    cyl1 = CylinderShape(1.0, 0.1, n_segments=4)
    cyl2 = CylinderShape(2.0, 0.2, n_segments=4)
    c = CompositeShape((cyl1, cyl2))
    expected = cyl1.faces().shape[0] + cyl2.faces().shape[0]
    assert c.faces().shape == (expected, 3)


@pytest.mark.unit
def test_composite_face_reindexing() -> None:
    """Child faces must be re-indexed by the running vertex offset."""
    cyl = CylinderShape(1.0, 0.1, n_segments=4)
    line = LineShape(1.0)  # 0 faces, 2 verts
    c = CompositeShape((line, cyl))
    # First-child faces are line's (none); cyl faces should be offset by 2.
    expected = cyl.faces() + 2
    np.testing.assert_array_equal(c.faces(), expected)


@pytest.mark.unit
def test_composite_face_offsets_with_three_parts() -> None:
    a = CylinderShape(1.0, 0.1, n_segments=3)
    b = CylinderShape(2.0, 0.2, n_segments=3)
    d = CylinderShape(3.0, 0.3, n_segments=3)
    c = CompositeShape((a, b, d))
    fa = a.faces()
    fb = b.faces()
    fd = d.faces()
    n_a = a.vertices_at_rest().shape[0]
    n_b = b.vertices_at_rest().shape[0]
    expected = np.concatenate([fa, fb + n_a, fd + n_a + n_b], axis=0)
    np.testing.assert_array_equal(c.faces(), expected)


@pytest.mark.unit
def test_composite_transform_identity_round_trip() -> None:
    c = CompositeShape((LineShape(1.0), CylinderShape(2.0, 0.3, n_segments=4)))
    fit = _identity_fit("composite", n_frames=2)
    out = c.transform(fit)
    rest = c.vertices_at_rest()
    assert out.shape == (2, rest.shape[0], 3)
    np.testing.assert_allclose(out[0], rest)


@pytest.mark.unit
def test_composite_transform_with_translation() -> None:
    c = CompositeShape((LineShape(1.0),))
    centroid = np.array([[1.0, 2.0, 3.0]])
    fit = _placed_fit(
        "composite",
        centroid=centroid,
        rotation=np.eye(3)[np.newaxis],
        scale=np.ones((1, 3)),
    )
    out = c.transform(fit)
    rest = c.vertices_at_rest()
    np.testing.assert_allclose(out[0], rest + centroid[0])


@pytest.mark.unit
def test_composite_rejects_empty_parts() -> None:
    with pytest.raises(ValueError, match="at least one part"):
        CompositeShape(())


@pytest.mark.unit
def test_composite_rejects_non_tuple() -> None:
    with pytest.raises(TypeError, match="parts must be a tuple"):
        CompositeShape([LineShape(1.0)])  # type: ignore[arg-type]


@pytest.mark.unit
def test_composite_rejects_non_shape_part() -> None:
    with pytest.raises(TypeError, match="BodyPartShape"):
        CompositeShape((LineShape(1.0), "not a shape"))  # type: ignore[arg-type]


@pytest.mark.unit
def test_composite_satisfies_protocol() -> None:
    c = CompositeShape((LineShape(1.0), CylinderShape(2.0, 0.5)))
    assert isinstance(c, BodyPartShape)


@pytest.mark.unit
def test_composite_nested() -> None:
    """A composite of composites is allowed."""
    inner = CompositeShape((LineShape(1.0), LineShape(2.0)))
    outer = CompositeShape((inner, CylinderShape(1.0, 0.1, n_segments=3)))
    assert outer.shape_id == "composite"
    n_inner = inner.vertices_at_rest().shape[0]
    n_cyl = 2 * 3 + 2
    assert outer.vertices_at_rest().shape == (n_inner + n_cyl, 3)


# ---------------------------------------------------------------------------
# Cross-shape Protocol sweep
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_all_primitive_shapes_satisfy_protocol() -> None:
    shapes = [
        LineShape(1.0),
        CylinderShape(1.0, 0.1),
        EllipsoidShape(1.0, 1.0, 1.0),
        CapsuleShape(1.0, 0.1),
        CompositeShape((LineShape(1.0),)),
    ]
    for s in shapes:
        assert isinstance(s, BodyPartShape), s.shape_id


@pytest.mark.unit
def test_all_shapes_return_float_vertices() -> None:
    shapes = [
        LineShape(1.0),
        CylinderShape(1.0, 0.1),
        EllipsoidShape(1.0, 1.0, 1.0),
        CapsuleShape(1.0, 0.1),
        CompositeShape((LineShape(1.0),)),
    ]
    for s in shapes:
        assert s.vertices_at_rest().dtype.kind == "f", s.shape_id


@pytest.mark.unit
def test_all_shapes_return_int_faces() -> None:
    shapes = [
        LineShape(1.0),
        CylinderShape(1.0, 0.1),
        EllipsoidShape(1.0, 1.0, 1.0),
        CapsuleShape(1.0, 0.1),
        CompositeShape((CylinderShape(1.0, 0.1, n_segments=3),)),
    ]
    for s in shapes:
        assert s.faces().dtype.kind in ("i", "u"), s.shape_id
        assert s.faces().shape[1] == 3


@pytest.mark.unit
def test_all_shapes_vertices_readonly() -> None:
    shapes = [
        LineShape(1.0),
        CylinderShape(1.0, 0.1),
        EllipsoidShape(1.0, 1.0, 1.0),
        CapsuleShape(1.0, 0.1),
        CompositeShape((LineShape(1.0),)),
    ]
    for s in shapes:
        v = s.vertices_at_rest()
        assert not v.flags.writeable, s.shape_id


@pytest.mark.unit
def test_all_shapes_zero_frames_returns_empty_t_axis() -> None:
    """Transforming with a 0-frame fit yields a (0, V, 3) array."""
    pairs = [
        (LineShape(1.0), "line"),
        (CylinderShape(1.0, 0.1, n_segments=3), "cylinder"),
        (EllipsoidShape(1.0, 1.0, 1.0, n_lat=2, n_lon=3), "ellipsoid"),
        (CapsuleShape(1.0, 0.1, n_segments=3, n_lat=2), "capsule"),
        (CompositeShape((LineShape(1.0),)), "composite"),
    ]
    for shape, sid in pairs:
        fit = _identity_fit(sid, n_frames=0)
        out = shape.transform(fit)
        assert out.shape[0] == 0
        assert out.shape[1] == shape.vertices_at_rest().shape[0]
        assert out.shape[2] == 3
