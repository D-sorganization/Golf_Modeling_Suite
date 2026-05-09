"""Static color resolver.

A :class:`StaticColorResolver` is the trivial resolver: it returns the
constant color carried by a :class:`StaticColor` for every
``(frame_idx, marker_idx)`` query, and broadcasts that single RGBA
tuple to a fully populated array on the bulk path.

Design-by-Contract
------------------
* :meth:`resolve_one` ignores ``frame_idx`` and ``marker_idx`` —
  they exist solely for Protocol compatibility.
* :meth:`resolve_array` always returns a freshly allocated array;
  callers may mutate it without affecting the resolver state.
* The resolver only accepts :class:`StaticColor` instances. Passing any
  other :data:`ColorScale` variant raises :class:`TypeError` listing the
  unexpected type — early failure beats silent wrong behaviour.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from matplotlib.colors import is_color_like, to_rgba

from .._types import RGBATuple
from ..colors import ColorScale, StaticColor

__all__ = ["StaticColorResolver"]


def _hex_to_rgba(hex_value: str) -> RGBATuple:
    """Parse a matplotlib-recognised color string.

    Raises
    ------
    ValueError
        If ``hex_value`` is not a parseable matplotlib color. The error
        message includes the offending input verbatim so callers can
        spot typos at a glance.
    """
    if not isinstance(hex_value, str) or not hex_value:
        raise ValueError(f"hex_value must be a non-empty string; got {hex_value!r}")
    if not is_color_like(hex_value):
        raise ValueError(f"hex_value {hex_value!r} is not a parseable matplotlib color")
    rgba = to_rgba(cast(Any, hex_value))
    return (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))


class StaticColorResolver:
    """Resolver for :class:`StaticColor` scales.

    Implements the
    :class:`~src.shared.python.plot_style.contracts.ColorResolver`
    Protocol.
    """

    def resolve_one(
        self,
        scale: ColorScale,
        frame_idx: int,
        marker_idx: int | None = None,
    ) -> tuple[float, float, float, float]:
        """Return the constant RGBA for ``scale``.

        Parameters
        ----------
        scale:
            Must be a :class:`StaticColor`.
        frame_idx, marker_idx:
            Accepted for Protocol compatibility and ignored.
        """
        del frame_idx, marker_idx  # interface compatibility
        if not isinstance(scale, StaticColor):
            raise TypeError(
                "StaticColorResolver only accepts StaticColor; "
                f"got {type(scale).__name__}"
            )
        return _hex_to_rgba(scale.hex_value)

    def resolve_array(
        self,
        scale: ColorScale,
        n_frames: int,
        n_markers: int | None = None,
    ) -> np.ndarray:
        """Return a broadcast ``(n_frames, [n_markers,] 4)`` RGBA array.

        Parameters
        ----------
        scale:
            Must be a :class:`StaticColor`.
        n_frames:
            Number of frames; must be ``> 0``.
        n_markers:
            Optional marker-axis size. ``None`` returns a 2-D
            ``(n_frames, 4)`` array; an integer returns
            ``(n_frames, n_markers, 4)``.
        """
        if not isinstance(scale, StaticColor):
            raise TypeError(
                "StaticColorResolver only accepts StaticColor; "
                f"got {type(scale).__name__}"
            )
        if not isinstance(n_frames, int) or n_frames <= 0:
            raise ValueError(f"n_frames must be a positive int; got {n_frames!r}")
        if n_markers is not None and (not isinstance(n_markers, int) or n_markers <= 0):
            raise ValueError(
                f"n_markers must be a positive int or None; got {n_markers!r}"
            )

        rgba = np.asarray(_hex_to_rgba(scale.hex_value), dtype=np.float64)
        if n_markers is None:
            out = np.broadcast_to(rgba, (n_frames, 4)).copy()
        else:
            out = np.broadcast_to(rgba, (n_frames, n_markers, 4)).copy()
        return out
