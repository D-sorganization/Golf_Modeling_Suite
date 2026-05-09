"""Data-driven color resolver.

A :class:`DataDrivenColorResolver` maps the scalar values of a
:class:`DataChannel` through a ``vmin``/``vmax`` normalisation and a
matplotlib colormap. The bulk path
:meth:`DataDrivenColorResolver.resolve_array` pre-computes the LUT once
and applies it to the entire ``(n_frames, [n_markers,] 4)`` block in a
single vectorised pass — no per-frame Python loop in the hot path.

Performance contract
--------------------
On a 38-marker × 654-frame dataset, :meth:`resolve_array` completes
within 5 ms on a recent laptop. The implementation never iterates
over individual frames or markers — normalisation, NaN masking, and
LUT sampling are all expressed as ``numpy`` operations.

Equivalence contract
--------------------
The three lookup paths must agree to 1e-12 atol on finite inputs:

1. ``resolve_one(scale, frame, marker)`` (per (frame, marker)).
2. ``resolve_one(scale, frame, None)`` (per frame, marker-mean).
3. ``resolve_array(scale, n_frames, n_markers)[frame, marker]``.

NaN inputs map to ``scale.nan_color`` on every path.
"""

from __future__ import annotations

import math
from typing import Any, cast

import numpy as np
from matplotlib import cm, colormaps
from matplotlib.colors import Colormap, is_color_like, to_rgba

from .._types import RGBATuple
from ..colormaps import ColormapId, resolve_colormap_alias
from ..colors import ColorScale, DataDrivenColor

__all__ = ["DataDrivenColorResolver"]


# Cached colormap lookup table keyed by (matplotlib name, lut_size).
_LUT_CACHE: dict[tuple[str, int], np.ndarray] = {}


def _hex_to_rgba(hex_value: str) -> RGBATuple:
    """Parse a matplotlib-recognised color string."""
    rgba = to_rgba(cast(Any, hex_value))
    return (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))


def _get_colormap(cmap_id: ColormapId) -> Colormap:
    """Return the ``Colormap`` for ``cmap_id`` resolving semantic aliases."""
    resolved = resolve_colormap_alias(cmap_id)
    try:
        return cast(Colormap, colormaps[resolved.value])
    except (KeyError, ValueError):
        return cast(Colormap, cm.get_cmap(resolved.value))


def _get_lut(cmap_id: ColormapId, lut_size: int = 256) -> np.ndarray:
    """Return a cached ``(lut_size, 4)`` RGBA LUT for ``cmap_id``.

    The LUT is the colormap evaluated at ``lut_size`` evenly-spaced
    points in ``[0, 1]``. Sampling is then a single ``np.searchsorted``
    or integer-index call away — no per-element Python overhead.
    """
    resolved = resolve_colormap_alias(cmap_id).value
    key = (resolved, lut_size)
    cached = _LUT_CACHE.get(key)
    if cached is not None:
        return cached
    cmap = _get_colormap(cmap_id)
    samples = np.linspace(0.0, 1.0, lut_size, dtype=np.float64)
    lut = np.asarray(cmap(samples), dtype=np.float64)
    if lut.ndim != 2 or lut.shape[1] != 4:
        # Defensive: matplotlib always returns (N, 4); guard anyway.
        raise RuntimeError(
            f"unexpected colormap LUT shape {lut.shape} for {resolved!r}"
        )
    _LUT_CACHE[key] = lut
    return lut


def _resolved_bounds(scale: DataDrivenColor) -> tuple[float, float]:
    """Return ``(vmin, vmax)`` with auto-detect filled in."""
    if scale.vmin is not None and scale.vmax is not None:
        return (float(scale.vmin), float(scale.vmax))
    auto_lo, auto_hi = scale.channel.auto_range()
    lo = float(scale.vmin) if scale.vmin is not None else auto_lo
    hi = float(scale.vmax) if scale.vmax is not None else auto_hi
    return (lo, hi)


def _sample_lut(lut: np.ndarray, normalised: np.ndarray) -> np.ndarray:
    """Sample ``lut`` at fractional positions in ``normalised``.

    ``normalised`` is an ndarray of values in ``[0, 1]``; the function
    returns an ``(*normalised.shape, 4)`` array of RGBA values.
    """
    lut_size = lut.shape[0]
    # Clip just in case — caller already clipped, but cheap insurance.
    clipped = np.clip(normalised, 0.0, 1.0)
    indices = np.minimum(
        (clipped * (lut_size - 1)).astype(np.intp),
        lut_size - 1,
    )
    return lut[indices]


class DataDrivenColorResolver:
    """Resolver for :class:`DataDrivenColor` scales.

    Implements the
    :class:`~src.shared.python.plot_style.contracts.ColorResolver`
    Protocol.
    """

    def __init__(self, lut_size: int = 256) -> None:
        if not isinstance(lut_size, int) or lut_size < 2:
            raise ValueError(f"lut_size must be an int ≥ 2; got {lut_size!r}")
        self._lut_size = lut_size

    # ------------------------------------------------------------------
    # Single-pair resolution
    # ------------------------------------------------------------------

    def resolve_one(
        self,
        scale: ColorScale,
        frame_idx: int,
        marker_idx: int | None = None,
    ) -> tuple[float, float, float, float]:
        """Resolve one ``(frame_idx, marker_idx)`` pair."""
        if not isinstance(scale, DataDrivenColor):
            raise TypeError(
                "DataDrivenColorResolver only accepts DataDrivenColor; "
                f"got {type(scale).__name__}"
            )
        scalar = scale.channel.value_at(frame_idx, marker_idx)
        if not math.isfinite(scalar):
            return _hex_to_rgba(scale.nan_color)
        lo, hi = _resolved_bounds(scale)
        if not (math.isfinite(lo) and math.isfinite(hi)):
            return _hex_to_rgba(scale.nan_color)
        if hi == lo:
            # vmin == vmax: degenerate range. Map every value to the
            # midpoint of the colormap.
            normalised = 0.5
        else:
            normalised = (scalar - lo) / (hi - lo)
            normalised = float(np.clip(normalised, 0.0, 1.0))
        lut = _get_lut(scale.colormap, self._lut_size)
        # Use the same integer-truncation scheme as the bulk path so
        # ``resolve_one`` and ``resolve_array`` agree to 1e-12 on every
        # (frame, marker) pair.
        index = min(int(normalised * (self._lut_size - 1)), self._lut_size - 1)
        rgba = lut[index]
        return (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(rgba[3]))

    # ------------------------------------------------------------------
    # Bulk resolution
    # ------------------------------------------------------------------

    def resolve_array(
        self,
        scale: ColorScale,
        n_frames: int,
        n_markers: int | None = None,
    ) -> np.ndarray:
        """Bulk-resolve the entire ``(n_frames, [n_markers,] 4)`` block.

        The colormap LUT is computed once (and cached), then applied to
        all values in a single vectorised pass. No Python-level loops
        run over frames or markers.
        """
        if not isinstance(scale, DataDrivenColor):
            raise TypeError(
                "DataDrivenColorResolver only accepts DataDrivenColor; "
                f"got {type(scale).__name__}"
            )
        if not isinstance(n_frames, int) or n_frames <= 0:
            raise ValueError(f"n_frames must be a positive int; got {n_frames!r}")
        if n_markers is not None and (not isinstance(n_markers, int) or n_markers <= 0):
            raise ValueError(
                f"n_markers must be a positive int or None; got {n_markers!r}"
            )
        if not isinstance(scale.nan_color, str) or not is_color_like(scale.nan_color):
            # Defensive: dataclass already validated; check anyway.
            raise ValueError(
                f"nan_color {scale.nan_color!r} is not a parseable matplotlib color"
            )

        nan_rgba = np.asarray(_hex_to_rgba(scale.nan_color), dtype=np.float64)

        # ----- Build the per-(frame, marker) scalar grid --------------
        values = scale.channel.values
        channel_n_frames = scale.channel.n_frames
        channel_n_markers = scale.channel.n_markers

        if n_markers is None:
            # 1-D output. Use frame scalars: for 1-D channel direct,
            # for 2-D channel use NaN-aware mean across markers.
            grid = np.full(n_frames, np.nan, dtype=np.float64)
            usable = min(n_frames, channel_n_frames)
            if usable > 0:
                if values.ndim == 1:
                    grid[:usable] = values[:usable].astype(np.float64, copy=False)
                else:
                    block = values[:usable].astype(np.float64, copy=False)
                    # NaN-aware mean across the marker axis.
                    with np.errstate(invalid="ignore"):
                        mean = np.nanmean(block, axis=1)
                    grid[:usable] = mean
        else:
            # 2-D output (n_frames, n_markers).
            grid = np.full((n_frames, n_markers), np.nan, dtype=np.float64)
            usable_frames = min(n_frames, channel_n_frames)
            if usable_frames > 0:
                if values.ndim == 1:
                    # Broadcast the same scalar across every marker.
                    grid[:usable_frames, :] = values[:usable_frames, None].astype(
                        np.float64, copy=False
                    )
                else:
                    assert channel_n_markers is not None  # ndim == 2 invariant
                    usable_markers = min(n_markers, channel_n_markers)
                    if usable_markers > 0:
                        grid[:usable_frames, :usable_markers] = values[
                            :usable_frames, :usable_markers
                        ].astype(np.float64, copy=False)

        # ----- Normalise + sample LUT ---------------------------------
        lo, hi = _resolved_bounds(scale)
        bounds_finite = math.isfinite(lo) and math.isfinite(hi)

        finite_mask = np.isfinite(grid)
        if not bounds_finite:
            # No usable bounds — every output is the NaN color.
            out_shape = (*grid.shape, 4)
            return np.broadcast_to(nan_rgba, out_shape).copy()

        if hi == lo:
            # Degenerate range: every finite value collapses to the
            # midpoint of the colormap.
            normalised = np.where(finite_mask, 0.5, 0.0)
        else:
            with np.errstate(invalid="ignore"):
                normalised = (grid - lo) / (hi - lo)
            normalised = np.clip(np.where(finite_mask, normalised, 0.0), 0.0, 1.0)

        lut = _get_lut(scale.colormap, self._lut_size)
        rgba = _sample_lut(lut, normalised)

        # Apply NaN color where the scalar was non-finite.
        rgba[~finite_mask] = nan_rgba
        return rgba
