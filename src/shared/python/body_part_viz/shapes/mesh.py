"""Triangle-mesh body-part shape backed by trimesh.

This module provides :class:`MeshShape`, a concrete implementation of
the :class:`BodyPartShape` protocol that wraps a triangle mesh loaded
from disk (or constructed in-memory from raw vertex/face arrays).

Loaders for ``.stl``, ``.obj``, ``.ply``, and ``.glb`` are exposed via
:meth:`MeshShape.from_file`. ``trimesh`` is an **optional** dependency
imported lazily — direct construction from numpy arrays does not require
trimesh and is convenient for unit tests.

Design by Contract
------------------
- Construction validates that ``vertices`` is ``(V, 3)`` finite float,
  ``faces`` is ``(F, 3)`` integer, and every face index is in
  ``range(V)``.
- Empty meshes (``V == 0`` or ``F == 0``) are rejected.
- The shape is a frozen dataclass; the stored arrays are made read-only
  to discourage post-construction mutation.

Geometry conventions
--------------------
- ``vertices_at_rest()`` returns the centroid-recentred vertices (so the
  mesh is centred on its bounding-box centroid).
- ``rest_dimensions`` is the axis-aligned bounding-box extent of the
  recentred vertices.
- :meth:`transform` applies, per frame: anisotropic scale, rotation, and
  centroid translation, in that order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape

if TYPE_CHECKING:  # pragma: no cover - import only for type hints
    pass


__all__ = ["MeshShape", "SUPPORTED_EXTENSIONS"]


SUPPORTED_EXTENSIONS: tuple[str, ...] = (".stl", ".obj", ".ply", ".glb")
"""File extensions accepted by :meth:`MeshShape.from_file`."""

_TRIMESH_INSTALL_HINT = (
    "trimesh is required for MeshShape.from_file(). Install with "
    "'pip install trimesh' (and optionally 'pip install trimesh[easy]' "
    "for full format support)."
)


def _load_trimesh_module() -> Any:
    """Import :mod:`trimesh` lazily and raise a helpful error if missing."""
    try:
        import trimesh  # noqa: PLC0415 - intentional lazy import
    except ImportError as exc:  # pragma: no cover - exercised only without trimesh
        raise RuntimeError(_TRIMESH_INSTALL_HINT) from exc
    return trimesh


@dataclass(frozen=True)
class MeshShape:
    """Triangle-mesh body-part shape.

    Attributes:
        shape_id: Stable, human-readable identifier (e.g. ``"mesh:head_v1"``).
        vertices: ``(V, 3)`` float vertex array, already centred on the
            bounding-box centroid.
        face_indices: ``(F, 3)`` integer triangle index array. Stored under
            this name (rather than ``faces``) to avoid colliding with the
            :meth:`faces` accessor required by the protocol.
        rest_dimensions: Axis-aligned bounding-box extent of ``vertices``,
            ``(extent_x, extent_y, extent_z)``.
        source_path: Optional path the mesh was loaded from. ``None`` for
            in-memory construction.
    """

    shape_id: str
    vertices: NDArray[np.floating] = field(repr=False)
    face_indices: NDArray[np.integer] = field(repr=False)
    rest_dimensions: tuple[float, ...]
    source_path: Path | None = None

    SUPPORTED_EXTENSIONS: ClassVar[tuple[str, ...]] = SUPPORTED_EXTENSIONS

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.shape_id, str) or not self.shape_id:
            raise ValueError("shape_id must be a non-empty string")

        verts = np.asarray(self.vertices)
        faces = np.asarray(self.face_indices)

        if verts.ndim != 2 or verts.shape[1] != 3:
            raise ValueError(f"vertices must have shape (V, 3), got {verts.shape}")
        if verts.shape[0] == 0:
            raise ValueError("vertices must be non-empty (got V=0)")
        if verts.dtype.kind != "f":
            raise TypeError(f"vertices must have a floating dtype, got {verts.dtype}")
        if not np.all(np.isfinite(verts)):
            raise ValueError("vertices must contain only finite values")

        if faces.ndim != 2 or faces.shape[1] != 3:
            raise ValueError(f"face_indices must have shape (F, 3), got {faces.shape}")
        if faces.shape[0] == 0:
            raise ValueError("face_indices must be non-empty (got F=0)")
        if faces.dtype.kind not in ("i", "u"):
            raise TypeError(
                f"face_indices must have an integer dtype, got {faces.dtype}"
            )
        v_max = int(verts.shape[0])
        if int(faces.min()) < 0 or int(faces.max()) >= v_max:
            raise ValueError(
                f"face_indices must reference vertex indices in [0, {v_max}); "
                f"got min={int(faces.min())}, max={int(faces.max())}"
            )

        if not isinstance(self.rest_dimensions, tuple):
            raise TypeError(
                f"rest_dimensions must be a tuple, got {type(self.rest_dimensions).__name__}"
            )
        if len(self.rest_dimensions) != 3:
            raise ValueError(
                f"rest_dimensions must have length 3, got {len(self.rest_dimensions)}"
            )
        for i, d in enumerate(self.rest_dimensions):
            if not np.isfinite(d):
                raise ValueError(f"rest_dimensions[{i}] must be finite, got {d}")
            if d <= 0.0:
                raise ValueError(f"rest_dimensions[{i}] must be positive, got {d}")

        # Make arrays read-only so the frozen dataclass invariant extends to
        # the underlying buffers.
        verts.setflags(write=False)
        faces.setflags(write=False)
        # Use object.__setattr__ to bypass the frozen guard.
        object.__setattr__(self, "vertices", verts)
        object.__setattr__(self, "face_indices", faces)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_arrays(
        cls,
        shape_id: str,
        vertices: NDArray[np.floating],
        faces: NDArray[np.integer],
        *,
        source_path: Path | None = None,
    ) -> MeshShape:
        """Construct a :class:`MeshShape` from raw vertex/face arrays.

        The vertices are recentred on their axis-aligned bounding-box
        centroid; ``rest_dimensions`` is computed from the recentred
        bounding-box extent.

        Args:
            shape_id: Stable identifier (e.g. ``"mesh:head_v1"``).
            vertices: ``(V, 3)`` float array.
            faces: ``(F, 3)`` integer array.
            source_path: Optional source path for traceability.

        Raises:
            ValueError: If the arrays violate the documented contract.
        """
        verts = np.asarray(vertices, dtype=np.float64).copy()
        if verts.ndim != 2 or verts.shape[1] != 3:
            raise ValueError(f"vertices must have shape (V, 3), got {verts.shape}")
        if verts.shape[0] == 0:
            raise ValueError("vertices must be non-empty (got V=0)")
        if not np.all(np.isfinite(verts)):
            raise ValueError("vertices must contain only finite values")

        # Centre on bounding-box centroid (mid-point of min/max per axis)
        mins = verts.min(axis=0)
        maxs = verts.max(axis=0)
        centroid = (mins + maxs) * 0.5
        centred = verts - centroid
        extents = maxs - mins
        if np.any(extents <= 0.0):
            raise ValueError(
                f"mesh bounding box must have positive extent on every axis, got {tuple(extents)}"
            )
        rest = (float(extents[0]), float(extents[1]), float(extents[2]))

        face_arr = np.asarray(faces)
        if face_arr.dtype.kind not in ("i", "u"):
            face_arr = face_arr.astype(np.int64)
        else:
            face_arr = face_arr.copy()

        return cls(
            shape_id=shape_id,
            vertices=centred,
            face_indices=face_arr,
            rest_dimensions=rest,
            source_path=source_path,
        )

    @classmethod
    def from_file(cls, path: Path | str) -> MeshShape:
        """Load a mesh from disk via :mod:`trimesh`.

        Supported extensions: ``.stl``, ``.obj``, ``.ply``, ``.glb``.
        ``.gltf`` is rejected with a hint to use ``.glb``.

        Args:
            path: Filesystem path to the mesh file.

        Returns:
            A :class:`MeshShape` whose ``shape_id`` is
            ``"mesh:<basename_without_ext>"``.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            ValueError: If the extension is unsupported, or the loaded
                mesh is empty/degenerate.
            RuntimeError: If :mod:`trimesh` is not installed.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"mesh file not found: {p}")
        if not p.is_file():
            raise FileNotFoundError(f"mesh path is not a file: {p}")

        ext = p.suffix.lower()
        if ext == ".gltf":
            raise ValueError(
                f"unsupported extension '.gltf' for {p.name}; "
                "convert to .glb (binary glTF) and try again"
            )
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"unsupported mesh extension '{ext}' for {p.name}; "
                f"supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        trimesh = _load_trimesh_module()

        loaded = trimesh.load(str(p), force="mesh")
        if loaded is None:
            raise ValueError(f"trimesh returned no mesh for {p}")

        # ``trimesh.load`` may return a Scene when the file contains
        # multiple geometries (common for .glb). Concatenate to a single
        # mesh in that case.
        if hasattr(loaded, "geometry") and not hasattr(loaded, "vertices"):
            geometries = list(loaded.geometry.values())
            if not geometries:
                raise ValueError(f"mesh file {p} contains no geometry")
            loaded = trimesh.util.concatenate(geometries)

        verts = np.asarray(loaded.vertices, dtype=np.float64)
        faces = np.asarray(loaded.faces, dtype=np.int64)
        if verts.size == 0 or faces.size == 0:
            raise ValueError(f"mesh file {p} produced an empty mesh")

        shape_id = f"mesh:{p.stem}"
        return cls.from_arrays(
            shape_id=shape_id,
            vertices=verts,
            faces=faces,
            source_path=p,
        )

    # ------------------------------------------------------------------
    # BodyPartShape protocol
    # ------------------------------------------------------------------

    def vertices_at_rest(self) -> NDArray[np.floating]:
        """Return ``(V, 3)`` centred, scale-normalised vertex array (read-only)."""
        return self.vertices

    def faces(self) -> NDArray[np.integer]:
        """Return the ``(F, 3)`` triangle index array (read-only)."""
        return self.face_indices

    def transform(self, fitted: FittedShape) -> NDArray[np.floating]:
        """Apply per-frame scale, rotation, and translation to rest vertices.

        Args:
            fitted: Per-frame placement. ``fitted.shape_id`` must match
                ``self.shape_id``.

        Returns:
            ``(T, V, 3)`` array of world-frame vertices.

        Raises:
            ValueError: If ``fitted.shape_id != self.shape_id``.
        """
        if fitted.shape_id != self.shape_id:
            raise ValueError(
                f"fitted.shape_id={fitted.shape_id!r} does not match "
                f"self.shape_id={self.shape_id!r}"
            )

        verts = self.vertices  # (V, 3)
        # Anisotropic scale: (T, V, 3) = (V, 3) * (T, 1, 3)
        scaled = verts[None, :, :] * fitted.scale[:, None, :]
        # Rotation: (T, V, 3) = einsum('tij,tvj->tvi', R, scaled)
        rotated = np.einsum("tij,tvj->tvi", fitted.rotation_matrix, scaled)
        # Translation
        return rotated + fitted.centroid[:, None, :]
