"""Per-frame (and per-(frame, marker)) scalar data channels.

A :class:`DataChannel` wraps a numeric ``numpy`` array of shape ``(T,)``
or ``(T, M)`` and exposes safe ``value_at`` / ``auto_range`` helpers used
by :class:`~src.shared.python.plot_style.colors.DataDrivenColor`.

Design-by-Contract
------------------
``DataChannel`` is frozen and validates every field in ``__post_init__``.
``value_at`` returns ``NaN`` for out-of-bounds indices instead of
raising — callers may safely vectorise without bounds-guarding.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = ["DataChannel"]


def _is_numeric_dtype(dtype: np.dtype[Any]) -> bool:
    """Return True if ``dtype`` is a real numeric kind (i, u, f)."""
    return dtype.kind in ("i", "u", "f")


@dataclass(frozen=True)
class DataChannel:
    """A per-frame (or per-(frame, marker)) scalar source.

    Attributes
    ----------
    name:
        Non-empty unique identifier (e.g. ``"clubhead_speed"``).
    values:
        ``numpy.ndarray`` with ``ndim`` in ``{1, 2}``. A 1-D array of
        shape ``(T,)`` denotes one scalar per frame. A 2-D array of
        shape ``(T, M)`` denotes one scalar per (frame, marker).
    unit:
        Display unit string. May be empty.
    """

    name: str
    values: np.ndarray = field(repr=False)
    unit: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError(f"name must be a non-empty string; got {self.name!r}")
        if not isinstance(self.unit, str):
            raise TypeError(f"unit must be a string; got {type(self.unit).__name__}")
        if not isinstance(self.values, np.ndarray):
            raise TypeError(
                f"values must be a numpy.ndarray; got {type(self.values).__name__}"
            )
        if self.values.ndim not in (1, 2):
            raise ValueError(
                "values must have ndim in {1, 2}; "
                f"got ndim={self.values.ndim} (shape={self.values.shape})"
            )
        if not _is_numeric_dtype(self.values.dtype):
            raise TypeError(
                "values dtype must be numeric (int / uint / float); "
                f"got {self.values.dtype}"
            )

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_array(
        cls,
        name: str,
        values: np.ndarray,
        unit: str = "",
    ) -> DataChannel:
        """Construct a :class:`DataChannel` from an ``ndarray``.

        Equivalent to the regular constructor; provided as an explicit
        factory for readability at call sites.
        """
        return cls(name=name, values=values, unit=unit)

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    @property
    def n_frames(self) -> int:
        """Number of frames (length of axis 0)."""
        return int(self.values.shape[0])

    @property
    def n_markers(self) -> int | None:
        """Number of markers (length of axis 1) or ``None`` for 1-D channels."""
        if self.values.ndim == 1:
            return None
        return int(self.values.shape[1])

    @property
    def is_per_marker(self) -> bool:
        """True iff the channel has a marker axis (2-D)."""
        return self.values.ndim == 2

    def value_at(self, frame_idx: int, marker_idx: int | None = None) -> float:
        """Return the scalar value at ``(frame_idx, marker_idx)``.

        Returns ``NaN`` for out-of-bounds indices. For a 1-D channel,
        ``marker_idx`` is ignored. For a 2-D channel, ``marker_idx`` of
        ``None`` returns the *mean* over the marker axis (excluding NaN).
        """
        if not isinstance(frame_idx, int):
            raise TypeError(f"frame_idx must be int; got {type(frame_idx).__name__}")
        if marker_idx is not None and not isinstance(marker_idx, int):
            raise TypeError(
                f"marker_idx must be int or None; got {type(marker_idx).__name__}"
            )

        if frame_idx < 0 or frame_idx >= self.n_frames:
            return float("nan")

        if self.values.ndim == 1:
            return float(self.values[frame_idx])

        # 2-D path
        n_markers = self.n_markers
        assert n_markers is not None  # noqa: S101 — invariant guarded above
        if marker_idx is None:
            row = self.values[frame_idx]
            finite_mask = np.isfinite(row)
            if not bool(finite_mask.any()):
                return float("nan")
            return float(np.mean(row[finite_mask]))
        if marker_idx < 0 or marker_idx >= n_markers:
            return float("nan")
        return float(self.values[frame_idx, marker_idx])

    def auto_range(self) -> tuple[float, float]:
        """Return ``(min, max)`` over all finite values.

        Returns ``(NaN, NaN)`` if the channel contains no finite values.
        """
        finite = self.values[np.isfinite(self.values)]
        if finite.size == 0:
            nan = float("nan")
            return (nan, nan)
        return (float(np.min(finite)), float(np.max(finite)))

    def has_finite_range(self) -> bool:
        """True iff :meth:`auto_range` returns finite values."""
        lo, hi = self.auto_range()
        return math.isfinite(lo) and math.isfinite(hi)
