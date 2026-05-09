"""Tests for :class:`body_part_viz.shapes.MeshShape`.

These tests verify the protocol conformance, DbC validation, file-loader
behaviour, and per-frame transform of :class:`MeshShape`.

Most tests construct meshes directly from numpy arrays via
:meth:`MeshShape.from_arrays`, which does **not** require trimesh. The
loader tests use :func:`pytest.importorskip` so they skip cleanly in
environments without trimesh installed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import BodyPartShape
from src.shared.python.body_part_viz.shapes import SUPPORTED_EXTENSIONS, MeshShape


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _unit_cube_arrays() -> tuple[np.ndarray, np.ndarray]:
    """Return (vertices, faces) for a 1x2x3 axis-aligned box."""
    # 8 corners spanning [-0.5, 0.5] x [-1, 1] x [-1.5, 1.5]
    vertices = np.array(
        [
            [-0.5, -1.0, -1.5],
            [0.5, -1.0, -1.5],
            [0.5, 1.0, -1.5],
            [-0.5, 1.0, -1.5],
            [-0.5, -1.0, 1.5],
            [0.5, -1.0, 1.5],
            [0.5, 1.0, 1.5],
            [-0.5, 1.0, 1.5],
        ],
        dtype=np.float64,
    )
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],  # -Z
            [4, 6, 5],
            [4, 7, 6],  # +Z
            [0, 4, 5],
            [0, 5, 1],  # -Y
            [2, 6, 7],
            [2, 7, 3],  # +Y
            [1, 5, 6],
            [1, 6, 2],  # +X
            [0, 3, 7],
            [0, 7, 4],  # -X
        ],
        dtype=np.int64,
    )
    return vertices, faces


@pytest.fixture
def box_shape() -> MeshShape:
    verts, faces = _unit_cube_arrays()
    return MeshShape.from_arrays("mesh:box", verts, faces)


def _identity_fit(shape_id: str, n_frames: int = 3) -> FittedShape:
    """Identity fit: zero centroid, identity rotation, unit scale."""
    centroid = np.zeros((n_frames, 3), dtype=np.float64)
    rot = np.broadcast_to(np.eye(3), (n_frames, 3, 3)).copy()
    scale = np.ones((n_frames, 3), dtype=np.float64)
    valid = np.ones((n_frames,), dtype=np.bool_)
    binding = MarkerBinding(
        kind=BindingKind.ON_MARKER,
        marker_names=("m1",),
        rest_dimensions=(1.0,),
    )
    return FittedShape(
        shape_id=shape_id,
        binding=binding,
        centroid=centroid,
        rotation_matrix=rot,
        scale=scale,
        valid_mask=valid,
    )


# ---------------------------------------------------------------------------
# from_arrays — happy paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_from_arrays_constructs_shape(box_shape: MeshShape) -> None:
    assert box_shape.shape_id == "mesh:box"
    assert box_shape.vertices.shape == (8, 3)
    assert box_shape.face_indices.shape == (12, 3)


@pytest.mark.unit
def test_from_arrays_recenters_vertices() -> None:
    # Off-centre cube — centroid should land at origin.
    verts = np.array(
        [
            [10.0, 10.0, 10.0],
            [11.0, 10.0, 10.0],
            [11.0, 11.0, 10.0],
            [10.0, 11.0, 10.0],
            [10.0, 10.0, 11.0],
            [11.0, 10.0, 11.0],
            [11.0, 11.0, 11.0],
            [10.0, 11.0, 11.0],
        ],
        dtype=np.float64,
    )
    faces = np.array([[0, 1, 2], [4, 5, 6]], dtype=np.int64)
    shape = MeshShape.from_arrays("mesh:offset", verts, faces)
    centre = shape.vertices.mean(axis=0)
    np.testing.assert_allclose(centre, np.zeros(3), atol=1e-12)


@pytest.mark.unit
def test_rest_dimensions_match_bbox(box_shape: MeshShape) -> None:
    assert box_shape.rest_dimensions == (1.0, 2.0, 3.0)


@pytest.mark.unit
def test_vertices_at_rest_extents_match_rest_dimensions(box_shape: MeshShape) -> None:
    v = box_shape.vertices_at_rest()
    extents = v.max(axis=0) - v.min(axis=0)
    np.testing.assert_allclose(extents, np.array(box_shape.rest_dimensions))


@pytest.mark.unit
def test_faces_returns_index_array(box_shape: MeshShape) -> None:
    f = box_shape.faces()
    assert f.shape == (12, 3)
    assert f.dtype.kind in ("i", "u")


@pytest.mark.unit
def test_vertices_array_is_read_only(box_shape: MeshShape) -> None:
    with pytest.raises(ValueError):
        box_shape.vertices[0, 0] = 999.0


@pytest.mark.unit
def test_faces_array_is_read_only(box_shape: MeshShape) -> None:
    with pytest.raises(ValueError):
        box_shape.face_indices[0, 0] = 999


# ---------------------------------------------------------------------------
# Protocol + frozen invariants
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_satisfies_body_part_shape_protocol(box_shape: MeshShape) -> None:
    assert isinstance(box_shape, BodyPartShape)


@pytest.mark.unit
def test_is_frozen_dataclass(box_shape: MeshShape) -> None:
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        box_shape.shape_id = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DbC: rejects malformed input
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_rejects_empty_vertices() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        MeshShape.from_arrays(
            "mesh:e",
            np.zeros((0, 3), dtype=np.float64),
            np.zeros((0, 3), dtype=np.int64),
        )


@pytest.mark.unit
def test_rejects_nan_vertices() -> None:
    verts, faces = _unit_cube_arrays()
    verts[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        MeshShape.from_arrays("mesh:nan", verts, faces)


@pytest.mark.unit
def test_rejects_inf_vertices() -> None:
    verts, faces = _unit_cube_arrays()
    verts[3, 1] = np.inf
    with pytest.raises(ValueError, match="finite"):
        MeshShape.from_arrays("mesh:inf", verts, faces)


@pytest.mark.unit
def test_rejects_wrong_vertex_shape() -> None:
    bad_verts = np.zeros((5, 4), dtype=np.float64)
    faces = np.array([[0, 1, 2]], dtype=np.int64)
    with pytest.raises(ValueError, match=r"\(V, 3\)"):
        MeshShape.from_arrays("mesh:bad", bad_verts, faces)


@pytest.mark.unit
def test_rejects_face_index_out_of_range() -> None:
    verts, _faces = _unit_cube_arrays()
    bad_faces = np.array([[0, 1, 99]], dtype=np.int64)
    with pytest.raises(ValueError, match="face_indices must reference"):
        MeshShape.from_arrays("mesh:oor", verts, bad_faces)


@pytest.mark.unit
def test_rejects_negative_face_index() -> None:
    verts, _faces = _unit_cube_arrays()
    bad_faces = np.array([[-1, 1, 2]], dtype=np.int64)
    with pytest.raises(ValueError, match="face_indices must reference"):
        MeshShape.from_arrays("mesh:neg", verts, bad_faces)


@pytest.mark.unit
def test_rejects_wrong_face_shape() -> None:
    verts, _faces = _unit_cube_arrays()
    bad_faces = np.array([[0, 1, 2, 3]], dtype=np.int64)
    with pytest.raises(ValueError, match=r"\(F, 3\)"):
        MeshShape.from_arrays("mesh:badface", verts, bad_faces)


@pytest.mark.unit
def test_rejects_empty_faces() -> None:
    verts, _faces = _unit_cube_arrays()
    with pytest.raises(ValueError, match="non-empty"):
        MeshShape.from_arrays("mesh:nofaces", verts, np.zeros((0, 3), dtype=np.int64))


@pytest.mark.unit
def test_rejects_empty_shape_id() -> None:
    verts, faces = _unit_cube_arrays()
    with pytest.raises(ValueError, match="shape_id"):
        MeshShape(
            shape_id="",
            vertices=verts,
            face_indices=faces,
            rest_dimensions=(1.0, 2.0, 3.0),
        )


@pytest.mark.unit
def test_rejects_degenerate_bbox() -> None:
    # A planar mesh (all z=0) — bbox extent on z is 0.
    verts = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        dtype=np.float64,
    )
    faces = np.array([[0, 1, 2]], dtype=np.int64)
    with pytest.raises(ValueError, match="positive extent"):
        MeshShape.from_arrays("mesh:planar", verts, faces)


@pytest.mark.unit
def test_rejects_non_float_vertices_in_direct_construction() -> None:
    int_verts = np.zeros((4, 3), dtype=np.int64)
    int_verts[1, 0] = 1
    int_verts[2, 1] = 1
    int_verts[3, 2] = 1
    faces = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.int64)
    with pytest.raises(TypeError, match="floating"):
        MeshShape(
            shape_id="mesh:int",
            vertices=int_verts,  # type: ignore[arg-type]
            face_indices=faces,
            rest_dimensions=(1.0, 1.0, 1.0),
        )


@pytest.mark.unit
def test_rejects_non_integer_faces_in_direct_construction() -> None:
    verts, _faces = _unit_cube_arrays()
    bad = np.zeros((1, 3), dtype=np.float64)
    with pytest.raises(TypeError, match="integer"):
        MeshShape(
            shape_id="mesh:floatfaces",
            vertices=verts,
            face_indices=bad,  # type: ignore[arg-type]
            rest_dimensions=(1.0, 2.0, 3.0),
        )


@pytest.mark.unit
def test_rejects_bad_rest_dimensions_length() -> None:
    verts, faces = _unit_cube_arrays()
    with pytest.raises(ValueError, match="length 3"):
        MeshShape(
            shape_id="mesh:rd",
            vertices=verts,
            face_indices=faces,
            rest_dimensions=(1.0, 2.0),
        )


@pytest.mark.unit
def test_rejects_negative_rest_dimension() -> None:
    verts, faces = _unit_cube_arrays()
    with pytest.raises(ValueError, match="positive"):
        MeshShape(
            shape_id="mesh:rd",
            vertices=verts,
            face_indices=faces,
            rest_dimensions=(1.0, -2.0, 3.0),
        )


@pytest.mark.unit
def test_rejects_non_finite_rest_dimension() -> None:
    verts, faces = _unit_cube_arrays()
    with pytest.raises(ValueError, match="finite"):
        MeshShape(
            shape_id="mesh:rd",
            vertices=verts,
            face_indices=faces,
            rest_dimensions=(1.0, float("nan"), 3.0),
        )


@pytest.mark.unit
def test_rejects_rest_dimensions_wrong_type() -> None:
    verts, faces = _unit_cube_arrays()
    with pytest.raises(TypeError, match="tuple"):
        MeshShape(
            shape_id="mesh:rd",
            vertices=verts,
            face_indices=faces,
            rest_dimensions=[1.0, 2.0, 3.0],  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# transform()
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_transform_identity_reproduces_vertices(box_shape: MeshShape) -> None:
    fit = _identity_fit(box_shape.shape_id, n_frames=4)
    out = box_shape.transform(fit)
    assert out.shape == (4, 8, 3)
    for t in range(4):
        np.testing.assert_allclose(out[t], box_shape.vertices_at_rest())


@pytest.mark.unit
def test_transform_translation_only(box_shape: MeshShape) -> None:
    fit = _identity_fit(box_shape.shape_id, n_frames=2)
    fit = FittedShape(
        shape_id=fit.shape_id,
        binding=fit.binding,
        centroid=np.array([[1.0, 2.0, 3.0], [-1.0, 0.0, 5.0]]),
        rotation_matrix=fit.rotation_matrix,
        scale=fit.scale,
        valid_mask=fit.valid_mask,
    )
    out = box_shape.transform(fit)
    np.testing.assert_allclose(
        out[0], box_shape.vertices_at_rest() + np.array([1.0, 2.0, 3.0])
    )
    np.testing.assert_allclose(
        out[1], box_shape.vertices_at_rest() + np.array([-1.0, 0.0, 5.0])
    )


@pytest.mark.unit
def test_transform_anisotropic_scale_stretches(box_shape: MeshShape) -> None:
    fit = _identity_fit(box_shape.shape_id, n_frames=1)
    fit = FittedShape(
        shape_id=fit.shape_id,
        binding=fit.binding,
        centroid=fit.centroid,
        rotation_matrix=fit.rotation_matrix,
        scale=np.array([[2.0, 0.5, 4.0]]),
        valid_mask=fit.valid_mask,
    )
    out = box_shape.transform(fit)
    extents = out[0].max(axis=0) - out[0].min(axis=0)
    expected = np.array(box_shape.rest_dimensions) * np.array([2.0, 0.5, 4.0])
    np.testing.assert_allclose(extents, expected)


@pytest.mark.unit
def test_transform_rotation_90_about_z(box_shape: MeshShape) -> None:
    rot = np.array(
        [
            [
                [0.0, -1.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        ]
    )
    fit = _identity_fit(box_shape.shape_id, n_frames=1)
    fit = FittedShape(
        shape_id=fit.shape_id,
        binding=fit.binding,
        centroid=fit.centroid,
        rotation_matrix=rot,
        scale=fit.scale,
        valid_mask=fit.valid_mask,
    )
    out = box_shape.transform(fit)
    rest = box_shape.vertices_at_rest()
    expected = (rot[0] @ rest.T).T
    np.testing.assert_allclose(out[0], expected, atol=1e-12)


@pytest.mark.unit
def test_transform_shape_id_mismatch_raises(box_shape: MeshShape) -> None:
    fit = _identity_fit("mesh:other")
    with pytest.raises(ValueError, match="shape_id"):
        box_shape.transform(fit)


@pytest.mark.unit
def test_transform_output_shape(box_shape: MeshShape) -> None:
    fit = _identity_fit(box_shape.shape_id, n_frames=7)
    out = box_shape.transform(fit)
    assert out.shape == (7, box_shape.vertices_at_rest().shape[0], 3)


# ---------------------------------------------------------------------------
# from_file — loader behaviour (requires trimesh)
# ---------------------------------------------------------------------------


def _write_box_via_trimesh(trimesh_mod: object, path: Path) -> None:
    box = trimesh_mod.creation.box(extents=(1.0, 2.0, 3.0))  # type: ignore[attr-defined]
    box.export(str(path))


@pytest.mark.unit
def test_from_file_stl(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    p = tmp_path / "head_v1.stl"
    _write_box_via_trimesh(trimesh, p)
    shape = MeshShape.from_file(p)
    assert shape.shape_id == "mesh:head_v1"
    assert shape.vertices.shape[1] == 3
    assert shape.face_indices.shape[1] == 3
    assert shape.source_path == p


@pytest.mark.unit
def test_from_file_obj(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    p = tmp_path / "torso.obj"
    _write_box_via_trimesh(trimesh, p)
    shape = MeshShape.from_file(p)
    assert shape.shape_id == "mesh:torso"
    np.testing.assert_allclose(
        np.array(shape.rest_dimensions),
        np.array([1.0, 2.0, 3.0]),
        atol=1e-9,
    )


@pytest.mark.unit
def test_from_file_ply(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    p = tmp_path / "limb.ply"
    _write_box_via_trimesh(trimesh, p)
    shape = MeshShape.from_file(p)
    assert shape.shape_id == "mesh:limb"
    assert isinstance(shape, BodyPartShape)


@pytest.mark.unit
def test_from_file_glb(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    p = tmp_path / "head.glb"
    _write_box_via_trimesh(trimesh, p)
    shape = MeshShape.from_file(p)
    assert shape.shape_id == "mesh:head"
    np.testing.assert_allclose(
        np.array(shape.rest_dimensions),
        np.array([1.0, 2.0, 3.0]),
        atol=1e-6,
    )


@pytest.mark.unit
def test_from_file_accepts_string_path(tmp_path: Path) -> None:
    trimesh = pytest.importorskip("trimesh")
    p = tmp_path / "leg.stl"
    _write_box_via_trimesh(trimesh, p)
    shape = MeshShape.from_file(str(p))
    assert shape.shape_id == "mesh:leg"


@pytest.mark.unit
def test_from_file_missing_raises_filenotfound(tmp_path: Path) -> None:
    p = tmp_path / "nope.stl"
    with pytest.raises(FileNotFoundError, match="not found"):
        MeshShape.from_file(p)


@pytest.mark.unit
def test_from_file_directory_raises_filenotfound(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not a file"):
        MeshShape.from_file(tmp_path)


@pytest.mark.unit
def test_from_file_unsupported_extension_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.xyz"
    p.write_text("dummy")
    with pytest.raises(ValueError, match="unsupported mesh extension"):
        MeshShape.from_file(p)


@pytest.mark.unit
def test_from_file_gltf_rejected_with_hint(tmp_path: Path) -> None:
    p = tmp_path / "model.gltf"
    p.write_text("{}")
    with pytest.raises(ValueError, match=r"\.gltf.*\.glb"):
        MeshShape.from_file(p)


@pytest.mark.unit
def test_supported_extensions_constant() -> None:
    assert ".stl" in SUPPORTED_EXTENSIONS
    assert ".obj" in SUPPORTED_EXTENSIONS
    assert ".ply" in SUPPORTED_EXTENSIONS
    assert ".glb" in SUPPORTED_EXTENSIONS
    assert ".gltf" not in SUPPORTED_EXTENSIONS


@pytest.mark.unit
def test_supported_extensions_class_var() -> None:
    assert MeshShape.SUPPORTED_EXTENSIONS == SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# Round-trip: bbox invariant after transform
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_bbox_invariant_after_identity_transform(box_shape: MeshShape) -> None:
    fit = _identity_fit(box_shape.shape_id, n_frames=1)
    out = box_shape.transform(fit)[0]
    extents = out.max(axis=0) - out.min(axis=0)
    np.testing.assert_allclose(extents, np.array(box_shape.rest_dimensions))
