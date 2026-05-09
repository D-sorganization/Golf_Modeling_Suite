"""Primitive ``BodyPartShape`` implementations.

This module provides five concrete shapes:

- :class:`LineShape` — a 1-D segment, useful for stick-figure rendering.
- :class:`CylinderShape` — a closed cylinder along the local x-axis.
- :class:`EllipsoidShape` — a UV-sphere triangulation scaled to ``(a, b, c)``.
- :class:`CapsuleShape` — a cylinder capped by two hemispheres.
- :class:`CompositeShape` — a concatenation of child shapes.

All shapes conform to the :class:`~body_part_viz.contracts.BodyPartShape`
runtime-checkable Protocol. They are immutable frozen dataclasses and
validate their inputs via Design-by-Contract in ``__post_init__``.

Conventions
-----------
- The local rest-pose coordinate frame puts the primary axis on +x.
- ``vertices_at_rest`` returns a read-only ``(V, 3)`` array of float64.
- ``transform`` consumes a :class:`FittedShape` whose ``shape_id`` matches
  ``self.shape_id`` and returns a ``(T, V, 3)`` float64 array obtained
  by applying per-frame anisotropic scale, rotation, and centroid
  translation:

      world = centroid[t] + R[t] @ diag(scale[t]) @ rest

This module is pure NumPy — no matplotlib, trimesh, or Qt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape

__all__ = [
    "CapsuleShape",
    "CompositeShape",
    "CylinderShape",
    "EllipsoidShape",
    "LineShape",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _check_positive(name: str, value: float) -> None:
    """DbC: raise ``ValueError`` unless ``value`` is finite and > 0."""
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be a positive finite number, got {value!r}")


def _check_segments(name: str, value: int, minimum: int = 3) -> None:
    """DbC: raise ``TypeError``/``ValueError`` for invalid segment counts."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def _validate_fitted_for(shape_id: str, fitted: FittedShape) -> None:
    """DbC: ensure ``fitted`` is compatible with the shape."""
    if not isinstance(fitted, FittedShape):
        raise TypeError(f"fitted must be FittedShape, got {type(fitted).__name__}")
    if fitted.shape_id != shape_id:
        raise ValueError(
            f"fitted.shape_id {fitted.shape_id!r} does not match "
            f"shape.shape_id {shape_id!r}"
        )


def _apply_per_frame(
    rest: NDArray[np.floating], fitted: FittedShape
) -> NDArray[np.floating]:
    """Apply per-frame ``centroid + R @ diag(scale) @ rest``.

    Args:
        rest: ``(V, 3)`` rest-pose vertices.
        fitted: per-frame placement.

    Returns:
        ``(T, V, 3)`` float64 array of world-frame vertices.
    """
    rest = np.asarray(rest, dtype=np.float64)
    centroid = np.asarray(fitted.centroid, dtype=np.float64)
    rotation = np.asarray(fitted.rotation_matrix, dtype=np.float64)
    scale = np.asarray(fitted.scale, dtype=np.float64)

    # scaled[t, v, c] = rest[v, c] * scale[t, c]
    scaled = rest[np.newaxis, :, :] * scale[:, np.newaxis, :]
    # rotated[t, v, c] = sum_k R[t, c, k] * scaled[t, v, k]
    rotated = np.einsum("tck,tvk->tvc", rotation, scaled)
    return rotated + centroid[:, np.newaxis, :]


def _readonly(arr: NDArray[np.floating]) -> NDArray[np.floating]:
    """Mark an ndarray read-only and return it."""
    arr.setflags(write=False)
    return arr


# ---------------------------------------------------------------------------
# UV-sphere helper (used by EllipsoidShape)
# ---------------------------------------------------------------------------


def _uv_sphere(n_lat: int, n_lon: int) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Build a unit UV-sphere with duplicated poles and seam.

    Args:
        n_lat: number of latitude bands (>= 2).
        n_lon: number of longitude segments (>= 3).

    Returns:
        ``(vertices, faces)``. Vertex grid has shape
        ``(n_lat + 1, n_lon + 1)`` flattened to ``((n_lat + 1) * (n_lon + 1), 3)``.
        ``2 * n_lat * n_lon`` triangle faces.
    """
    phi = np.linspace(0.0, np.pi, n_lat + 1)
    theta = np.linspace(0.0, 2.0 * np.pi, n_lon + 1)
    phi_grid, theta_grid = np.meshgrid(phi, theta, indexing="ij")

    x = np.sin(phi_grid) * np.cos(theta_grid)
    y = np.sin(phi_grid) * np.sin(theta_grid)
    z = np.cos(phi_grid)
    vertices = np.stack([x, y, z], axis=-1).reshape(-1, 3).astype(np.float64)

    n_cols = n_lon + 1
    faces: list[tuple[int, int, int]] = []
    for i in range(n_lat):
        for j in range(n_lon):
            v00 = i * n_cols + j
            v01 = i * n_cols + (j + 1)
            v10 = (i + 1) * n_cols + j
            v11 = (i + 1) * n_cols + (j + 1)
            faces.append((v00, v10, v11))
            faces.append((v00, v11, v01))
    faces_arr = np.asarray(faces, dtype=np.int64)
    return vertices, faces_arr


# ---------------------------------------------------------------------------
# LineShape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineShape:
    """A 1-D line segment along the local x-axis.

    The rest-pose vertices are ``[(-L/2, 0, 0), (+L/2, 0, 0)]`` so the
    centroid sits at the local origin — this matches the convention used
    by between-two-marker fitters which place the centroid at the segment
    midpoint.
    """

    rest_length: float
    shape_id: str = field(default="line", init=False)
    rest_dimensions: tuple[float, ...] = field(init=False)

    def __post_init__(self) -> None:
        _check_positive("rest_length", self.rest_length)
        object.__setattr__(self, "rest_dimensions", (float(self.rest_length),))

    def vertices_at_rest(self) -> NDArray[np.float64]:
        half = 0.5 * float(self.rest_length)
        return _readonly(
            np.array([[-half, 0.0, 0.0], [half, 0.0, 0.0]], dtype=np.float64)
        )

    def faces(self) -> NDArray[np.int64]:
        return _readonly(np.zeros((0, 3), dtype=np.int64))  # type: ignore[return-value]

    def transform(self, fitted: FittedShape) -> NDArray[np.float64]:
        _validate_fitted_for(self.shape_id, fitted)
        return _apply_per_frame(self.vertices_at_rest(), fitted)


# ---------------------------------------------------------------------------
# CylinderShape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CylinderShape:
    """Closed cylinder of length ``rest_length`` and radius ``rest_radius``.

    The cylinder lies along the local x-axis, centred at the origin.
    Vertex layout (for ``n_segments = N``):

    - ``0 .. N-1``         : bottom ring at ``x = -L/2``
    - ``N .. 2N-1``        : top ring at ``x = +L/2``
    - ``2N``               : bottom cap centre
    - ``2N + 1``           : top cap centre

    Total: ``2 * n_segments + 2`` vertices.
    Faces: ``2 * n_segments`` side triangles + ``2 * n_segments`` cap
    triangles = ``4 * n_segments``.
    """

    rest_length: float
    rest_radius: float
    n_segments: int = 16
    shape_id: str = field(default="cylinder", init=False)
    rest_dimensions: tuple[float, ...] = field(init=False)

    def __post_init__(self) -> None:
        _check_positive("rest_length", self.rest_length)
        _check_positive("rest_radius", self.rest_radius)
        _check_segments("n_segments", self.n_segments, minimum=3)
        object.__setattr__(
            self,
            "rest_dimensions",
            (float(self.rest_length), float(self.rest_radius)),
        )

    def vertices_at_rest(self) -> NDArray[np.float64]:
        n = self.n_segments
        half = 0.5 * float(self.rest_length)
        r = float(self.rest_radius)
        theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        bottom_ring = np.column_stack([np.full(n, -half), r * cos_t, r * sin_t])
        top_ring = np.column_stack([np.full(n, +half), r * cos_t, r * sin_t])
        bottom_centre = np.array([[-half, 0.0, 0.0]])
        top_centre = np.array([[+half, 0.0, 0.0]])
        verts = np.concatenate(
            [bottom_ring, top_ring, bottom_centre, top_centre], axis=0
        ).astype(np.float64)
        return _readonly(verts)

    def faces(self) -> NDArray[np.int64]:
        n = self.n_segments
        bottom_centre = 2 * n
        top_centre = 2 * n + 1
        faces: list[tuple[int, int, int]] = []
        for i in range(n):
            j = (i + 1) % n
            # Side: two triangles per segment.
            faces.append((i, n + i, n + j))
            faces.append((i, n + j, j))
            # Bottom cap (winding so normals face -x).
            faces.append((bottom_centre, j, i))
            # Top cap.
            faces.append((top_centre, n + i, n + j))
        return _readonly(np.asarray(faces, dtype=np.int64))  # type: ignore[return-value]

    def transform(self, fitted: FittedShape) -> NDArray[np.float64]:
        _validate_fitted_for(self.shape_id, fitted)
        return _apply_per_frame(self.vertices_at_rest(), fitted)


# ---------------------------------------------------------------------------
# EllipsoidShape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EllipsoidShape:
    """Triaxial ellipsoid with semi-axes ``(a, b, c)`` along ``(x, y, z)``.

    Triangulation is a UV-sphere with ``n_lat`` latitude bands and
    ``n_lon`` longitude segments, scaled anisotropically. Total
    vertices: ``(n_lat + 1) * (n_lon + 1)``; total faces:
    ``2 * n_lat * n_lon``.
    """

    a: float
    b: float
    c: float
    n_lat: int = 12
    n_lon: int = 24
    shape_id: str = field(default="ellipsoid", init=False)
    rest_dimensions: tuple[float, ...] = field(init=False)

    def __post_init__(self) -> None:
        _check_positive("a", self.a)
        _check_positive("b", self.b)
        _check_positive("c", self.c)
        _check_segments("n_lat", self.n_lat, minimum=2)
        _check_segments("n_lon", self.n_lon, minimum=3)
        object.__setattr__(
            self,
            "rest_dimensions",
            (float(self.a), float(self.b), float(self.c)),
        )

    def vertices_at_rest(self) -> NDArray[np.float64]:
        unit, _ = _uv_sphere(self.n_lat, self.n_lon)
        scaled = unit * np.array([self.a, self.b, self.c], dtype=np.float64)
        return _readonly(scaled)

    def faces(self) -> NDArray[np.int64]:
        _, faces = _uv_sphere(self.n_lat, self.n_lon)
        return _readonly(faces)  # type: ignore[return-value]

    def transform(self, fitted: FittedShape) -> NDArray[np.float64]:
        _validate_fitted_for(self.shape_id, fitted)
        return _apply_per_frame(self.vertices_at_rest(), fitted)


# ---------------------------------------------------------------------------
# CapsuleShape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapsuleShape:
    """A capsule: a cylinder of length ``rest_length`` capped by two
    hemispheres of radius ``rest_radius`` along the local x-axis.

    End-to-end height is ``rest_length + 2 * rest_radius``. The capsule
    is centred at the local origin. ``rest_dimensions`` reports
    ``(rest_length, rest_radius)`` to match :class:`CylinderShape`.

    Vertex layout:

    - cylinder rings: ``2 * n_segments`` (bottom ring then top ring)
    - top hemisphere grid: ``(n_lat + 1) * (n_segments + 1)`` vertices
      placed at ``x = +L/2``
    - bottom hemisphere grid: same, mirrored

    The hemispheres are full UV grids (with duplicated apex and seam) so
    indexing is regular and predictable.
    """

    rest_length: float
    rest_radius: float
    n_segments: int = 16
    n_lat: int = 6
    shape_id: str = field(default="capsule", init=False)
    rest_dimensions: tuple[float, ...] = field(init=False)

    def __post_init__(self) -> None:
        _check_positive("rest_length", self.rest_length)
        _check_positive("rest_radius", self.rest_radius)
        _check_segments("n_segments", self.n_segments, minimum=3)
        _check_segments("n_lat", self.n_lat, minimum=2)
        object.__setattr__(
            self,
            "rest_dimensions",
            (float(self.rest_length), float(self.rest_radius)),
        )

    def _hemisphere_unit(
        self, sign: float
    ) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
        """Build a unit hemisphere with apex at ``sign * x = +1``.

        ``sign`` must be +1 or -1. The hemisphere uses ``n_lat`` rings
        from the apex to the equator, and ``n_segments`` longitudes.
        """
        n_lat = self.n_lat
        n_lon = self.n_segments
        # phi from 0 (apex) to pi/2 (equator).
        phi = np.linspace(0.0, 0.5 * np.pi, n_lat + 1)
        theta = np.linspace(0.0, 2.0 * np.pi, n_lon + 1)
        phi_grid, theta_grid = np.meshgrid(phi, theta, indexing="ij")
        # x is the polar axis (apex direction).
        x = sign * np.cos(phi_grid)
        y = np.sin(phi_grid) * np.cos(theta_grid)
        z = np.sin(phi_grid) * np.sin(theta_grid)
        verts = np.stack([x, y, z], axis=-1).reshape(-1, 3).astype(np.float64)

        n_cols = n_lon + 1
        faces: list[tuple[int, int, int]] = []
        for i in range(n_lat):
            for j in range(n_lon):
                v00 = i * n_cols + j
                v01 = i * n_cols + (j + 1)
                v10 = (i + 1) * n_cols + j
                v11 = (i + 1) * n_cols + (j + 1)
                faces.append((v00, v10, v11))
                faces.append((v00, v11, v01))
        return verts, np.asarray(faces, dtype=np.int64)

    def vertices_at_rest(self) -> NDArray[np.float64]:
        n = self.n_segments
        half = 0.5 * float(self.rest_length)
        r = float(self.rest_radius)
        theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        bottom_ring = np.column_stack([np.full(n, -half), r * cos_t, r * sin_t])
        top_ring = np.column_stack([np.full(n, +half), r * cos_t, r * sin_t])

        top_hemi_unit, _ = self._hemisphere_unit(+1.0)
        bot_hemi_unit, _ = self._hemisphere_unit(-1.0)
        # Scale by r and translate apex outward by ±L/2.
        top_hemi = top_hemi_unit * r + np.array([half, 0.0, 0.0])
        bot_hemi = bot_hemi_unit * r + np.array([-half, 0.0, 0.0])

        verts = np.concatenate(
            [bottom_ring, top_ring, top_hemi, bot_hemi], axis=0
        ).astype(np.float64)
        return _readonly(verts)

    def faces(self) -> NDArray[np.int64]:
        n = self.n_segments
        # Side faces (cylinder side only — hemispheres replace the caps).
        faces: list[tuple[int, int, int]] = []
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, n + i, n + j))
            faces.append((i, n + j, j))

        _, top_hemi_faces = self._hemisphere_unit(+1.0)
        _, bot_hemi_faces = self._hemisphere_unit(-1.0)
        hemi_n = (self.n_lat + 1) * (self.n_segments + 1)
        top_offset = 2 * n
        bot_offset = 2 * n + hemi_n
        for f in top_hemi_faces:
            faces.append(
                (top_offset + int(f[0]), top_offset + int(f[1]), top_offset + int(f[2]))
            )
        for f in bot_hemi_faces:
            faces.append(
                (bot_offset + int(f[0]), bot_offset + int(f[1]), bot_offset + int(f[2]))
            )
        return _readonly(np.asarray(faces, dtype=np.int64))  # type: ignore[return-value]

    def transform(self, fitted: FittedShape) -> NDArray[np.float64]:
        _validate_fitted_for(self.shape_id, fitted)
        return _apply_per_frame(self.vertices_at_rest(), fitted)


# ---------------------------------------------------------------------------
# CompositeShape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompositeShape:
    """Concatenation of multiple child :class:`BodyPartShape` instances.

    The composite presents itself as a single shape: its
    ``vertices_at_rest`` is the vertical concatenation of the children's
    rest vertices, and its ``faces`` are the children's faces re-indexed
    to the combined vertex range. ``transform`` applies the same
    per-frame placement to every child — the children share one
    :class:`FittedShape`.

    ``rest_dimensions`` is the concatenation of the children's
    ``rest_dimensions``.
    """

    parts: tuple[object, ...]
    shape_id: str = field(default="composite", init=False)
    rest_dimensions: tuple[float, ...] = field(init=False)

    _MIN_PARTS: ClassVar[int] = 1

    def __post_init__(self) -> None:
        if not isinstance(self.parts, tuple):
            raise TypeError(f"parts must be a tuple, got {type(self.parts).__name__}")
        if len(self.parts) < self._MIN_PARTS:
            raise ValueError("CompositeShape requires at least one part")

        for idx, part in enumerate(self.parts):
            for attr in (
                "shape_id",
                "rest_dimensions",
                "vertices_at_rest",
                "faces",
                "transform",
            ):
                if not hasattr(part, attr):
                    raise TypeError(
                        f"parts[{idx}] does not satisfy BodyPartShape "
                        f"(missing {attr!r})"
                    )

        dims: list[float] = []
        for part in self.parts:
            dims.extend(float(d) for d in part.rest_dimensions)
        object.__setattr__(self, "rest_dimensions", tuple(dims))

    def vertices_at_rest(self) -> NDArray[np.float64]:
        chunks = [
            np.asarray(p.vertices_at_rest(), dtype=np.float64) for p in self.parts
        ]
        return _readonly(np.concatenate(chunks, axis=0))

    def faces(self) -> NDArray[np.int64]:
        face_chunks: list[NDArray[np.int64]] = []
        offset = 0
        for p in self.parts:
            v = np.asarray(p.vertices_at_rest())
            f = np.asarray(p.faces(), dtype=np.int64)
            if f.size > 0:
                face_chunks.append(f + offset)
            offset += v.shape[0]
        if not face_chunks:
            return _readonly(np.zeros((0, 3), dtype=np.int64))  # type: ignore[return-value]
        return _readonly(np.concatenate(face_chunks, axis=0))  # type: ignore[return-value]

    def transform(self, fitted: FittedShape) -> NDArray[np.float64]:
        _validate_fitted_for(self.shape_id, fitted)
        return _apply_per_frame(self.vertices_at_rest(), fitted)
