"""Canonical ``ClubBallTarget`` dataclass and ball-impact extraction.

Extends :class:`ClubTarget` with a ball boundary condition (position at
impact, launch direction, launch speed, spin). Frozen and validated at
construction so loaders are forced to produce a fully-formed artifact.

Public API:
    BallImpactState                       -- frozen dataclass for ball state
                                              at impact.
    ClubBallTarget                        -- composite ``ClubTarget`` +
                                              ``BallImpactState``.
    extract_ball_impact_from_clubtarget   -- approximate ball-impact extractor
                                              from clubhead kinematics.

The naming policy is source-agnostic: no reference to specific launch
monitors, brand names, ball makes, or studies anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .club_target import MAX_POSITION_NORM_M, ClubTarget

# Validation bounds (frozen here; documented in the issue rationale).
LAUNCH_SPEED_MAX_MPS = 100.0
SPIN_RPM_MAX = 15000.0
UNIT_NORM_TOL = 1.0e-6

# Default elasticity stand-in used when approximating ball launch speed
# from clubhead speed in the absence of a real launch-monitor feed.
DEFAULT_ELASTICITY_FACTOR = 1.5


@dataclass(frozen=True)
class BallImpactState:
    """Ball state at the moment of impact (boundary condition).

    Attributes:
        position_at_impact_m: World-frame Z-up ball position at impact, in
            metres. Shape ``(3,)``. All components must be finite.
        launch_direction: Unit vector giving the launch direction in the
            world frame. Shape ``(3,)``. If unknown, all three components
            must be NaN (no partial unknowns are allowed).
        launch_speed_mps: Ball launch speed in metres per second. NaN if
            unknown; if finite, must lie in ``[0, 100]``.
        spin_rpm: Total spin rate in revolutions per minute. NaN if unknown;
            if finite, must lie in ``[0, 15000]``.
    """

    position_at_impact_m: np.ndarray
    launch_direction: np.ndarray
    launch_speed_mps: float
    spin_rpm: float


@dataclass(frozen=True)
class ClubBallTarget:
    """Composite target combining a :class:`ClubTarget` with a ball boundary.

    Validated at construction; any rule violation raises ``ValueError`` or
    ``TypeError`` with a descriptive message.
    """

    club: ClubTarget
    ball_impact: BallImpactState

    def __post_init__(self) -> None:
        """Run all postcondition checks at construction."""
        _validate_club_ball_target(self)

    @property
    def time(self) -> np.ndarray:
        """Delegate to the wrapped ``ClubTarget.time``."""
        return self.club.time

    @property
    def impact_idx(self) -> int:
        """Delegate to the wrapped ``ClubTarget.impact_idx``."""
        return self.club.impact_idx


def _validate_position_at_impact(position: np.ndarray) -> None:
    """Check ``position_at_impact_m`` shape, finiteness, and norm bound."""
    if not isinstance(position, np.ndarray):
        raise TypeError(
            "position_at_impact_m must be a numpy ndarray, "
            f"got {type(position).__name__}"
        )
    if position.shape != (3,):
        raise ValueError(
            f"position_at_impact_m must have shape (3,), got {position.shape}"
        )
    if not np.all(np.isfinite(position)):
        raise ValueError("position_at_impact_m contains NaN or Inf")
    norm = float(np.linalg.norm(position))
    if norm >= MAX_POSITION_NORM_M:
        raise ValueError(
            f"position_at_impact_m has |r| >= {MAX_POSITION_NORM_M} m (got {norm:.3f})"
        )


def _validate_launch_direction(direction: np.ndarray) -> None:
    """Check ``launch_direction`` shape and unit-norm-or-all-NaN rule."""
    if not isinstance(direction, np.ndarray):
        raise TypeError(
            f"launch_direction must be a numpy ndarray, got {type(direction).__name__}"
        )
    if direction.shape != (3,):
        raise ValueError(
            f"launch_direction must have shape (3,), got {direction.shape}"
        )
    nan_mask = np.isnan(direction)
    if np.any(nan_mask):
        if not np.all(nan_mask):
            raise ValueError(
                "launch_direction must be either fully finite or all-NaN; "
                "partial NaN components are not allowed"
            )
        return
    if not np.all(np.isfinite(direction)):
        raise ValueError("launch_direction contains Inf")
    norm = float(np.linalg.norm(direction))
    if abs(norm - 1.0) > UNIT_NORM_TOL:
        raise ValueError(
            "launch_direction must be unit-norm to within "
            f"{UNIT_NORM_TOL} (got |v|={norm:.6f})"
        )


def _validate_finite_or_nan_in_range(
    value: float, name: str, lo: float, hi: float
) -> None:
    """Validate a scalar that may be NaN, else must lie in ``[lo, hi]``."""
    fvalue = float(value)
    if np.isnan(fvalue):
        return
    if not np.isfinite(fvalue):
        raise ValueError(f"{name} must be finite or NaN, got {fvalue!r}")
    if not (lo <= fvalue <= hi):
        raise ValueError(f"{name} must be in [{lo}, {hi}], got {fvalue!r}")


def _validate_club_ball_target(t: ClubBallTarget) -> None:
    """Enforce the ``ClubBallTarget`` validation rules."""
    if not isinstance(t.club, ClubTarget):
        raise TypeError(
            f"club must be a ClubTarget instance, got {type(t.club).__name__}"
        )
    if not isinstance(t.ball_impact, BallImpactState):
        raise TypeError(
            "ball_impact must be a BallImpactState instance, "
            f"got {type(t.ball_impact).__name__}"
        )
    bi = t.ball_impact
    _validate_position_at_impact(bi.position_at_impact_m)
    _validate_launch_direction(bi.launch_direction)
    _validate_finite_or_nan_in_range(
        bi.launch_speed_mps, "launch_speed_mps", 0.0, LAUNCH_SPEED_MAX_MPS
    )
    _validate_finite_or_nan_in_range(bi.spin_rpm, "spin_rpm", 0.0, SPIN_RPM_MAX)


def extract_ball_impact_from_clubtarget(target: ClubTarget) -> BallImpactState:
    """Approximate a :class:`BallImpactState` from a :class:`ClubTarget`.

    This is a stand-in extractor for use when a real launch-monitor feed is
    unavailable. The approximation collapses the ball position to the
    clubhead position at impact (within a ball radius, fine for visual
    overlays) and derives launch direction and speed from the numerical
    clubhead-velocity gradient at the impact frame.

    Approximation details:
        * ``position_at_impact_m`` := ``target.clubhead[impact_idx_0]``,
          where ``impact_idx_0`` is the 0-based index. The MATLAB-style
          ``ClubTarget.impact_idx`` is 1-based, so we subtract one.
        * ``launch_direction`` := unit vector of the clubhead velocity at
          impact, computed via ``np.gradient`` on the resampled grid. If
          the clubhead is stationary at impact (zero velocity), the
          direction collapses to all-NaN.
        * ``launch_speed_mps`` := ``|v_clubhead at impact|`` multiplied by
          :data:`DEFAULT_ELASTICITY_FACTOR`, clamped to
          :data:`LAUNCH_SPEED_MAX_MPS`. This is a documented stand-in
          pending real launch-monitor data.
        * ``spin_rpm`` := ``NaN`` (no kinematic estimator implemented).

    Args:
        target: A validated :class:`ClubTarget`.

    Returns:
        A validated :class:`BallImpactState`.

    Raises:
        TypeError: If ``target`` is not a :class:`ClubTarget`.
    """
    if not isinstance(target, ClubTarget):
        raise TypeError(
            f"target must be a ClubTarget instance, got {type(target).__name__}"
        )
    impact_idx_0 = int(target.impact_idx) - 1
    n = target.time.shape[0]
    if not (0 <= impact_idx_0 < n):
        raise ValueError(
            f"impact_idx {target.impact_idx} maps to out-of-range "
            f"0-based index {impact_idx_0} for time length {n}"
        )
    position = np.asarray(target.clubhead[impact_idx_0], dtype=float).copy()
    velocity = np.gradient(target.clubhead, target.time, axis=0)
    v_impact = np.asarray(velocity[impact_idx_0], dtype=float)
    speed = float(np.linalg.norm(v_impact))
    direction = v_impact / speed if speed > 0.0 else np.full(3, np.nan, dtype=float)
    launch_speed = min(speed * DEFAULT_ELASTICITY_FACTOR, LAUNCH_SPEED_MAX_MPS)
    return BallImpactState(
        position_at_impact_m=position,
        launch_direction=direction,
        launch_speed_mps=launch_speed,
        spin_rpm=float("nan"),
    )
