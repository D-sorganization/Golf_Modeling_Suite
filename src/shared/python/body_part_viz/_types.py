"""Internal types and dataclasses for body-part visualisation.

These are the runtime artefacts produced by fitters and consumed by
renderers. The public-facing :class:`MarkerBinding`, :class:`ShapeTheme`,
and the protocols live in their own modules; this one holds the
:class:`FittedShape` trajectory representation that is shared across
fitters and renderers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.shared.python.body_part_viz.bindings import MarkerBinding

__all__ = ["FittedShape"]


@dataclass(frozen=True)
class FittedShape:
    """Per-frame placement of a body-part shape.

    Attributes:
        shape_id: ``BodyPartShape.shape_id`` of the source shape.
        binding: Marker binding that produced this fit.
        centroid: ``(T, 3)`` world-frame centroid per frame, in metres.
        rotation_matrix: ``(T, 3, 3)`` proper rotation per frame.
            Each ``R[t]`` is a right-handed orthonormal frame.
        scale: ``(T, 3)`` anisotropic scale per frame. All entries
            strictly positive.
        valid_mask: ``(T,)`` boolean array. ``valid_mask[t]`` is True iff
            every source marker provided a finite position at frame ``t``.

    All arrays must agree on the leading time axis ``T``. Validation
    happens in ``__post_init__``.
    """

    shape_id: str
    binding: MarkerBinding
    centroid: NDArray[np.floating]
    rotation_matrix: NDArray[np.floating]
    scale: NDArray[np.floating]
    valid_mask: NDArray[np.bool_]

    def __post_init__(self) -> None:
        if not isinstance(self.shape_id, str) or not self.shape_id:
            raise ValueError("shape_id must be a non-empty string")
        if not isinstance(self.binding, MarkerBinding):
            raise TypeError(
                f"binding must be MarkerBinding, got {type(self.binding).__name__}"
            )

        # Each array must be a numpy.ndarray with the documented shape.
        for name in ("centroid", "rotation_matrix", "scale", "valid_mask"):
            arr = getattr(self, name)
            if not isinstance(arr, np.ndarray):
                raise TypeError(
                    f"{name} must be numpy.ndarray, got {type(arr).__name__}"
                )

        if self.centroid.ndim != 2 or self.centroid.shape[1] != 3:
            raise ValueError(
                f"centroid must have shape (T, 3), got {self.centroid.shape}"
            )
        n_frames = self.centroid.shape[0]

        if self.rotation_matrix.shape != (n_frames, 3, 3):
            raise ValueError(
                f"rotation_matrix must have shape ({n_frames}, 3, 3), "
                f"got {self.rotation_matrix.shape}"
            )
        if self.scale.shape != (n_frames, 3):
            raise ValueError(
                f"scale must have shape ({n_frames}, 3), got {self.scale.shape}"
            )
        if self.valid_mask.shape != (n_frames,):
            raise ValueError(
                f"valid_mask must have shape ({n_frames},), got {self.valid_mask.shape}"
            )

        if self.valid_mask.dtype != np.bool_:
            raise TypeError(
                f"valid_mask must have dtype bool, got {self.valid_mask.dtype}"
            )

        # Scales must be strictly positive on valid frames; nan-safe check.
        if n_frames > 0:
            valid_scales = self.scale[self.valid_mask]
            if valid_scales.size > 0 and not np.all(np.isfinite(valid_scales)):
                raise ValueError(
                    "scale must contain only finite values on valid frames"
                )
            if valid_scales.size > 0 and not np.all(valid_scales > 0.0):
                raise ValueError("scale must be strictly positive on valid frames")

    @property
    def n_frames(self) -> int:
        """Number of frames in this trajectory."""
        return int(self.centroid.shape[0])
