"""``ProcrustesAnisotropicFitter`` — Kabsch rotation plus per-axis scale."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz._types import FittedShape
from src.shared.python.body_part_viz.bindings import BindingKind, MarkerBinding
from src.shared.python.body_part_viz.contracts import BodyPartShape
from src.shared.python.body_part_viz.fitters._kabsch import (
    anisotropic_scale,
    kabsch_rotation,
)
from src.shared.python.body_part_viz.fitters.cluster_kabsch import _stack_markers

__all__ = ["ProcrustesAnisotropicFitter"]


class ProcrustesAnisotropicFitter:
    """Kabsch rotation + anisotropic scale ``(sx, sy, sz)`` along principal axes.

    For each frame, alternating minimisation between Kabsch (rotation
    given current scale) and per-axis least squares (scale given current
    rotation) is run to convergence; this jointly recovers ``R`` and
    ``diag(s)`` in the model ``current ≈ R diag(s) rest + t``.

    Frames with any non-finite marker are invalid; on those frames the
    centroid is held at the previous valid frame (or zeros), the rotation
    is the identity, and the scale is ``(1, 1, 1)``.
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
                f"ProcrustesAnisotropicFitter requires CLUSTER binding, "
                f"got {binding.kind}"
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
            r, s = self._fit_rotation_and_scale(rest, centred)

            centroid[t] = c
            rotation[t] = r
            scale[t] = s
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

    @staticmethod
    def _fit_rotation_and_scale(
        rest: NDArray[np.floating],
        centred: NDArray[np.floating],
    ) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Alternating-minimisation solve for ``R`` and ``diag(s)``."""
        s = np.ones(3, dtype=float)
        r = np.eye(3)
        for _ in range(30):
            scaled_rest = rest * s
            r_new = kabsch_rotation(scaled_rest, centred)
            q_in_rest = centred @ r_new
            s_new = anisotropic_scale(rest, q_in_rest)
            if np.linalg.norm(r_new - r) < 1e-12 and np.linalg.norm(s_new - s) < 1e-12:
                return r_new, s_new
            r = r_new
            s = s_new
        return r, s

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
