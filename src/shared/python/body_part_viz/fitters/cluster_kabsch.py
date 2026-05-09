"""``ClusterKabschFitter`` — rigid Kabsch fit over a marker cluster."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import BodyPartShape
from src.shared.python.body_part_viz.fitters._kabsch import kabsch_rotation

__all__ = ["ClusterKabschFitter"]


def _stack_markers(
    binding: MarkerBinding,
    markers_xyz: dict[str, NDArray[np.floating]],
) -> NDArray[np.floating]:
    """Return ``(T, N, 3)`` array stacking the binding's markers in order.

    Validates name presence and time-axis agreement.
    """
    arrays: list[NDArray[np.floating]] = []
    t_ref: int | None = None
    for name in binding.marker_names:
        if name not in markers_xyz:
            raise ValueError(f"marker {name!r} not found in markers_xyz")
        arr = np.asarray(markers_xyz[name], dtype=float)
        if arr.ndim != 2 or arr.shape[1] != 3:
            raise ValueError(f"marker {name!r} must have shape (T, 3), got {arr.shape}")
        if t_ref is None:
            t_ref = arr.shape[0]
        elif arr.shape[0] != t_ref:
            raise ValueError(
                f"marker {name!r} has T={arr.shape[0]}; expected T={t_ref}"
            )
        arrays.append(arr)
    return np.stack(arrays, axis=1)


class ClusterKabschFitter:
    """Rigid Kabsch (rotation + translation) fit over a marker cluster.

    For each frame:

    - centroid = mean of the cluster markers,
    - rotation R from Kabsch against the rest-pose cluster (det == +1),
    - scale = (1, 1, 1).

    By default the fitter uses the *first valid frame* as its rest-pose
    reference. Pass ``rest_positions`` to override.

    Frames containing any non-finite marker sample are marked invalid;
    on those frames the centroid is held at the previous valid frame
    (or zeros if none yet), the rotation is the identity, and the scale
    is ``(1, 1, 1)``.
    """

    def __init__(self, rest_positions: NDArray[np.floating] | None = None) -> None:
        self._rest_override = (
            None if rest_positions is None else np.asarray(rest_positions, dtype=float)
        )

    def fit(
        self,
        shape: BodyPartShape,
        binding: MarkerBinding,
        markers_xyz: dict[str, NDArray[np.floating]],
    ) -> FittedShape:
        if binding.kind is not BindingKind.CLUSTER:
            raise ValueError(
                f"ClusterKabschFitter requires CLUSTER binding, got {binding.kind}"
            )

        markers = _stack_markers(binding, markers_xyz)
        n_frames, n_markers, _ = markers.shape

        rest = self._resolve_rest(markers)

        centroid = np.zeros((n_frames, 3), dtype=float)
        rotation = np.tile(np.eye(3), (n_frames, 1, 1))
        scale = np.ones((n_frames, 3), dtype=float)
        valid = np.zeros(n_frames, dtype=bool)

        last_centroid: NDArray[np.floating] | None = None
        for t in range(n_frames):
            frame = markers[t]
            if not np.all(np.isfinite(frame)):
                valid[t] = False
                if last_centroid is not None:
                    centroid[t] = last_centroid
                continue

            c = frame.mean(axis=0)
            centred = frame - c
            r = kabsch_rotation(rest, centred)
            centroid[t] = c
            rotation[t] = r
            valid[t] = True
            last_centroid = c

        return FittedShape(
            shape_id=shape.shape_id,
            binding=binding,
            centroid=centroid,
            rotation_matrix=rotation,
            scale=scale,
            valid_mask=valid,
        )

    def _resolve_rest(
        self,
        markers: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        n_markers = markers.shape[1]
        if self._rest_override is not None:
            rest = self._rest_override
            if rest.shape != (n_markers, 3):
                raise ValueError(
                    f"rest_positions must have shape ({n_markers}, 3), got {rest.shape}"
                )
            return rest - rest.mean(axis=0, keepdims=True)

        for t in range(markers.shape[0]):
            if np.all(np.isfinite(markers[t])):
                ref = markers[t]
                return ref - ref.mean(axis=0, keepdims=True)

        return np.zeros((n_markers, 3), dtype=float)
