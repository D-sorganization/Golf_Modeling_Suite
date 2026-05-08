"""Canonical ``BodyTarget`` dataclass and validation.

A first-class, validated, immutable target dataclass for full-body marker
trajectories — parallel to :class:`ClubTarget`. Loaders and downstream cost
functions, visualisers, and exporters can rely on the validated artifact
without re-parsing raw motion-capture files.

The dataclass and its validation are source-agnostic: nothing here references
a specific motion-capture vendor, study, lab, or person. Provenance lives in
the free-form :class:`SourceProvenance` ``format`` field set by the loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .club_target import TIME_EPS, SourceProvenance

# Schema-version constant (bump on any breaking field/semantics change).
BODY_TARGET_SCHEMA_VERSION = 1

# Per-marker position-norm sanity bound for human-scale motion (metres).
MAX_BODY_POSITION_NORM_M = 3.0

# Minimum fraction of markers that must be finite in at least one frame.
_MIN_FINITE_MARKER_FRACTION = 0.5

BodyCoordinateFrame = Literal["z_up_right_handed"]


@dataclass(frozen=True)
class BodyEvent:
    """Named event on the resampled body-marker timegrid.

    Attributes:
        label:  Free-form non-empty event label (e.g. ``"address"``,
                ``"top"``, ``"impact"``).
        frame:  Frame index on the resampled grid; must lie in ``[0, N)``.
        time_s: Wall-clock seconds since the first sample (``time[0] == 0``).
    """

    label: str
    frame: int
    time_s: float


@dataclass(frozen=True)
class BodyTarget:
    """Canonical full-body marker trajectory.

    Validated at construction; any violation of the validation rules raises
    :class:`ValueError` (or :class:`TypeError` for the source-type check).
    Frozen so loaders are forced to produce a fully-formed, validated artifact
    rather than mutating one in place.

    Attributes:
        time:         ``(N,)`` seconds, strictly increasing, ``time[0] == 0``.
        marker_xyz:   ``(N, M, 3)`` metres; NaN allowed for occluded samples.
        marker_names: Length-``M`` tuple of unique non-empty marker names.
        impact_idx:   Frame index of impact on the resampled grid; ``[0, N)``.
        events:       Named events with frame indices on the resampled grid.
        source:       File-level provenance metadata.
        coordinate_frame: World-frame convention; only ``"z_up_right_handed"``
                          is currently supported.
    """

    time: np.ndarray
    marker_xyz: np.ndarray
    marker_names: tuple[str, ...]
    impact_idx: int
    events: tuple[BodyEvent, ...]
    source: SourceProvenance
    coordinate_frame: BodyCoordinateFrame = "z_up_right_handed"

    def __post_init__(self) -> None:
        """Run all postcondition checks at construction."""
        _validate_bodytarget(self)


def _validate_time(time: np.ndarray) -> int:
    """Check the time vector and return its length ``N``."""
    if not isinstance(time, np.ndarray) or time.ndim != 1:
        raise ValueError(
            f"time must be a 1-D ndarray, got shape "
            f"{getattr(time, 'shape', type(time).__name__)!r}"
        )
    n = int(time.shape[0])
    if n < 2:
        raise ValueError(f"time must have at least 2 samples (got {n})")
    if abs(float(time[0])) > TIME_EPS:
        raise ValueError(f"time[0] must be 0 within {TIME_EPS}, got {time[0]!r}")
    if not np.all(np.diff(time) > 0):
        raise ValueError("time must be strictly increasing")
    return n


def _validate_marker_names(marker_names: tuple[str, ...]) -> int:
    """Check marker_names; return its length ``M``."""
    if not isinstance(marker_names, tuple):
        raise ValueError(
            f"marker_names must be a tuple, got {type(marker_names).__name__}"
        )
    m = len(marker_names)
    for i, name in enumerate(marker_names):
        if not isinstance(name, str):
            raise ValueError(
                f"marker_names[{i}] must be a string, got {type(name).__name__}"
            )
        if name == "":
            raise ValueError(f"marker_names[{i}] must be non-empty")
    if len(set(marker_names)) != m:
        raise ValueError("marker_names must be unique")
    return m


def _validate_marker_xyz_shape(marker_xyz: np.ndarray, n: int, m: int) -> None:
    """Check that ``marker_xyz`` has the expected ``(N, M, 3)`` shape."""
    if not isinstance(marker_xyz, np.ndarray):
        raise ValueError(
            f"marker_xyz must be an ndarray, got {type(marker_xyz).__name__}"
        )
    if m < 3:
        raise ValueError(f"marker count M must be >= 3, got {m}")
    if marker_xyz.shape != (n, m, 3):
        raise ValueError(
            f"marker_xyz must have shape ({n}, {m}, 3), got {marker_xyz.shape}"
        )


def _validate_marker_norms(marker_xyz: np.ndarray) -> None:
    """Reject finite samples whose per-marker position norm is implausible."""
    finite_mask = np.all(np.isfinite(marker_xyz), axis=2)
    if not np.any(finite_mask):
        return
    # Compute norms only on finite samples to avoid NaN propagation.
    safe_xyz = np.where(finite_mask[..., None], marker_xyz, 0.0)
    norms = np.linalg.norm(safe_xyz, axis=2)
    # Mask out non-finite frames so they do not register as violations.
    masked_norms = np.where(finite_mask, norms, 0.0)
    if np.any(masked_norms >= MAX_BODY_POSITION_NORM_M):
        max_norm = float(masked_norms.max())
        raise ValueError(
            f"marker_xyz has |r| >= {MAX_BODY_POSITION_NORM_M} m on a finite "
            f"sample (max {max_norm:.3f})"
        )


def _validate_finite_coverage(marker_xyz: np.ndarray, m: int) -> None:
    """At least one frame must be finite for >= 50% of markers."""
    finite_per_frame = np.all(np.isfinite(marker_xyz), axis=2).sum(axis=1)
    threshold = _MIN_FINITE_MARKER_FRACTION * m
    if not np.any(finite_per_frame >= threshold):
        raise ValueError(
            "no frame has at least "
            f"{int(np.ceil(threshold))} of {m} markers finite "
            f"(>= {_MIN_FINITE_MARKER_FRACTION:.0%} coverage required); "
            "loader must crop leading/trailing all-NaN windows"
        )


def _validate_events(events: tuple[BodyEvent, ...], n: int) -> None:
    """Check events tuple: types, frame range, non-empty unique labels."""
    if not isinstance(events, tuple):
        raise ValueError(f"events must be a tuple, got {type(events).__name__}")
    seen: set[str] = set()
    for i, event in enumerate(events):
        if not isinstance(event, BodyEvent):
            raise ValueError(
                f"events[{i}] must be a BodyEvent, got {type(event).__name__}"
            )
        if not isinstance(event.label, str) or event.label == "":
            raise ValueError(f"events[{i}].label must be a non-empty string")
        if event.label in seen:
            raise ValueError(
                f"events labels must be unique (duplicate {event.label!r})"
            )
        seen.add(event.label)
        if not (0 <= int(event.frame) < n):
            raise ValueError(
                f"events[{i}].frame must be in [0, {n}), got {event.frame}"
            )


def _validate_bodytarget(t: BodyTarget) -> None:
    """Enforce the BodyTarget validation rules (see issue spec)."""
    n = _validate_time(t.time)
    m = _validate_marker_names(t.marker_names)
    _validate_marker_xyz_shape(t.marker_xyz, n, m)
    _validate_marker_norms(t.marker_xyz)
    _validate_finite_coverage(t.marker_xyz, m)
    if not (0 <= int(t.impact_idx) < n):
        raise ValueError(f"impact_idx must be in [0, {n}), got {t.impact_idx}")
    _validate_events(t.events, n)
    if not isinstance(t.source, SourceProvenance):
        raise TypeError("source must be a SourceProvenance instance")
