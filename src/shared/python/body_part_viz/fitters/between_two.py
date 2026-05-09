"""``BetweenTwoMarkersFitter`` — fits a line/cylinder/capsule shape to two markers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import BodyPartShape

__all__ = ["BetweenTwoMarkersFitter"]


def _stable_basis_from_axis(axis: NDArray[np.floating]) -> NDArray[np.floating]:
    """Build a right-handed orthonormal basis whose +x column is ``axis``.

    Picks an up-vector via Gram-Schmidt against world Z, falling back to
    world Y when ``axis`` is near-parallel to Z.
    """
    x = axis / np.linalg.norm(axis)
    world_z = np.array([0.0, 0.0, 1.0])
    ref = np.array([0.0, 1.0, 0.0]) if abs(float(np.dot(x, world_z))) > 0.9 else world_z
    y = ref - np.dot(ref, x) * x
    y = y / np.linalg.norm(y)
    z = np.cross(x, y)
    return np.column_stack([x, y, z])


class BetweenTwoMarkersFitter:
    """Fits a shape's local +x axis along the segment between two markers.

    Per-frame transform:

    - ``centroid = (a + b) / 2``
    - ``axis = (b - a) / ||b - a||``
    - ``rotation`` aligns the shape's local +x to ``axis`` with a stable
      up-vector chosen via Gram-Schmidt against world Z (or world Y when
      ``axis`` is near-parallel to Z).
    - ``scale = (||b - a|| / rest_length, 1.0, 1.0)``

    Frames where either marker is non-finite are marked invalid; on those
    frames the centroid is held at the previous valid frame's centroid
    (or zeros if there is no prior valid frame), the rotation is the
    identity, and the scale is ``(1, 1, 1)``.
    """

    def fit(
        self,
        shape: BodyPartShape,
        binding: MarkerBinding,
        markers_xyz: dict[str, NDArray[np.floating]],
    ) -> FittedShape:
        if binding.kind is not BindingKind.BETWEEN_TWO:
            raise ValueError(
                f"BetweenTwoMarkersFitter requires BETWEEN_TWO binding, "
                f"got {binding.kind}"
            )

        for name in binding.marker_names:
            if name not in markers_xyz:
                raise ValueError(f"marker {name!r} not found in markers_xyz")

        a_name, b_name = binding.marker_names
        a = np.asarray(markers_xyz[a_name], dtype=float)
        b = np.asarray(markers_xyz[b_name], dtype=float)

        if a.ndim != 2 or a.shape[1] != 3:
            raise ValueError(f"marker {a_name!r} must have shape (T, 3), got {a.shape}")
        if b.shape != a.shape:
            raise ValueError(
                f"marker arrays disagree on shape: {a_name!r}={a.shape}, "
                f"{b_name!r}={b.shape}"
            )

        n_frames = a.shape[0]
        rest_length = (
            float(binding.rest_dimensions[0]) if binding.rest_dimensions else 1.0
        )

        centroid = np.zeros((n_frames, 3), dtype=float)
        rotation = np.tile(np.eye(3), (n_frames, 1, 1))
        scale = np.ones((n_frames, 3), dtype=float)
        valid = np.zeros(n_frames, dtype=bool)

        last_valid_centroid: NDArray[np.floating] | None = None

        for t in range(n_frames):
            a_t = a[t]
            b_t = b[t]
            if not (np.all(np.isfinite(a_t)) and np.all(np.isfinite(b_t))):
                valid[t] = False
                if last_valid_centroid is not None:
                    centroid[t] = last_valid_centroid
                continue

            mid = 0.5 * (a_t + b_t)
            diff = b_t - a_t
            length = float(np.linalg.norm(diff))
            if length < 1e-12:
                valid[t] = False
                if last_valid_centroid is not None:
                    centroid[t] = last_valid_centroid
                else:
                    centroid[t] = mid
                continue

            axis = diff / length
            centroid[t] = mid
            rotation[t] = _stable_basis_from_axis(axis)
            scale[t] = np.array([length / rest_length, 1.0, 1.0])
            valid[t] = True
            last_valid_centroid = mid

        return FittedShape(
            shape_id=shape.shape_id,
            binding=binding,
            centroid=centroid,
            rotation_matrix=rotation,
            scale=scale,
            valid_mask=valid,
        )
