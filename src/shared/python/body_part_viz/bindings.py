"""Marker bindings for body-part visualisation.

A :class:`MarkerBinding` describes how a body-part shape attaches to one
or more mocap markers. There are three binding kinds:

- :attr:`BindingKind.BETWEEN_TWO` — two markers; shape's primary axis
  spans the segment ``markers[0] -> markers[1]`` and rest length is the
  pair's distance.
- :attr:`BindingKind.CLUSTER` — three or more markers; rigid Kabsch
  registration with optional anisotropic scaling.
- :attr:`BindingKind.ON_MARKER` — single marker; shape sits at the
  marker location with no rotation.

The class is intentionally minimal and stateless. Per-frame placement
lives in :class:`body_part_viz.FittedShape`.

Design by Contract
------------------
``__post_init__`` validates every invariant. See :func:`MarkerBinding.__post_init__`
for the full list. Public callers should rely on construction-time
validation rather than re-validating downstream.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

__all__ = ["BindingKind", "MarkerBinding"]


class BindingKind(str, Enum):
    """How a shape attaches to mocap markers.

    Inherits ``str`` so that values serialise transparently through JSON
    and YAML without a custom encoder.
    """

    BETWEEN_TWO = "between_two"
    """Two markers; segment-style binding."""

    CLUSTER = "cluster"
    """Three or more markers; rigid + anisotropic-scale binding."""

    ON_MARKER = "on_marker"
    """Single marker; static placement."""


# --- Module-level invariant helpers (DbC). Kept top-level so they're
#     trivially unit-testable from test_contracts.py and reused by other
#     dataclasses in the package without circular imports.


def _check_unit_quaternion(q: tuple[float, float, float, float]) -> None:
    """Raise :class:`ValueError` if ``q`` is not a unit quaternion.

    Tolerance is ``1e-6`` on the sum-of-squares.
    """
    if len(q) != 4:
        raise ValueError(f"quaternion must have 4 components, got {len(q)}")
    norm_sq = sum(c * c for c in q)
    if not math.isfinite(norm_sq):
        raise ValueError(f"quaternion components must be finite, got {q}")
    if abs(norm_sq - 1.0) > 1e-6:
        raise ValueError(
            f"quaternion must be unit-norm (got |q|^2 = {norm_sq:.9f}, expected 1.0)"
        )


def _check_positive_rest_dimensions(rest: tuple[float, ...]) -> None:
    """Raise :class:`ValueError` if any rest dimension is non-positive or non-finite."""
    for i, d in enumerate(rest):
        if not math.isfinite(d):
            raise ValueError(f"rest_dimensions[{i}] must be finite, got {d}")
        if d <= 0.0:
            raise ValueError(f"rest_dimensions[{i}] must be positive, got {d}")


@dataclass(frozen=True)
class MarkerBinding:
    """Binding between a body-part shape and the markers that drive it.

    Attributes:
        kind: How the shape attaches; see :class:`BindingKind`.
        marker_names: Names of the markers (length depends on ``kind``).
        rest_dimensions: Rest-pose dimensions in metres. Semantics vary
            per shape but every component must be strictly positive.
        rest_orientation_quat: Unit quaternion ``(w, x, y, z)`` describing
            the shape's rest orientation in the binding's local frame.
            Defaults to identity.
    """

    kind: BindingKind
    marker_names: tuple[str, ...]
    rest_dimensions: tuple[float, ...] = ()
    rest_orientation_quat: tuple[float, float, float, float] = (
        1.0,
        0.0,
        0.0,
        0.0,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.kind, BindingKind):
            raise TypeError(f"kind must be BindingKind, got {type(self.kind).__name__}")

        # Marker count invariants per kind.
        n = len(self.marker_names)
        if self.kind is BindingKind.BETWEEN_TWO and n != 2:
            raise ValueError(f"BETWEEN_TWO binding requires exactly 2 markers, got {n}")
        if self.kind is BindingKind.CLUSTER and n < 3:
            raise ValueError(f"CLUSTER binding requires at least 3 markers, got {n}")
        if self.kind is BindingKind.ON_MARKER and n != 1:
            raise ValueError(f"ON_MARKER binding requires exactly 1 marker, got {n}")

        # Marker names must be non-empty strings.
        for i, name in enumerate(self.marker_names):
            if not isinstance(name, str):
                raise TypeError(
                    f"marker_names[{i}] must be str, got {type(name).__name__}"
                )
            if not name:
                raise ValueError(f"marker_names[{i}] must be non-empty")

        # Marker names must be unique.
        if len(set(self.marker_names)) != n:
            raise ValueError(f"marker_names must be unique, got {self.marker_names}")

        _check_positive_rest_dimensions(self.rest_dimensions)
        _check_unit_quaternion(self.rest_orientation_quat)
