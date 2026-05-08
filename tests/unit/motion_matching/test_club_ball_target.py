"""Unit tests for the ``ClubBallTarget`` dataclass and validation rules."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from src.shared.python.motion_matching.club_ball_target import (
    DEFAULT_ELASTICITY_FACTOR,
    LAUNCH_SPEED_MAX_MPS,
    BallImpactState,
    ClubBallTarget,
    extract_ball_impact_from_clubtarget,
)

from ._fixtures import make_provenance, make_target


def _good_ball_impact() -> BallImpactState:
    """A valid BallImpactState for use in unit tests."""
    return BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=60.0,
        spin_rpm=3000.0,
    )


def test_club_ball_target_happy_path() -> None:
    cbt = ClubBallTarget(club=make_target(), ball_impact=_good_ball_impact())
    assert isinstance(cbt.club.time, np.ndarray)
    # Property delegates.
    np.testing.assert_array_equal(cbt.time, cbt.club.time)
    assert cbt.impact_idx == cbt.club.impact_idx


def test_club_ball_target_immutable() -> None:
    cbt = ClubBallTarget(club=make_target(), ball_impact=_good_ball_impact())
    with pytest.raises(dataclasses.FrozenInstanceError):
        cbt.ball_impact = _good_ball_impact()  # type: ignore[misc]


def test_ball_impact_state_immutable() -> None:
    bi = _good_ball_impact()
    with pytest.raises(dataclasses.FrozenInstanceError):
        bi.launch_speed_mps = 50.0  # type: ignore[misc]


def test_validation_rejects_non_clubtarget_club() -> None:
    with pytest.raises(TypeError, match="ClubTarget"):
        ClubBallTarget(
            club="not-a-target",  # type: ignore[arg-type]
            ball_impact=_good_ball_impact(),
        )


def test_validation_rejects_non_ballimpactstate_ball_impact() -> None:
    with pytest.raises(TypeError, match="BallImpactState"):
        ClubBallTarget(
            club=make_target(),
            ball_impact="not-a-ball-state",  # type: ignore[arg-type]
        )


def test_validation_rejects_position_wrong_shape() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.zeros((3, 1)),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="position_at_impact_m must have shape"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_position_with_nan() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([np.nan, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="NaN or Inf"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_position_too_large() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([99.0, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match=">="):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_position_non_ndarray() -> None:
    bi = BallImpactState(
        position_at_impact_m=[0.5, 0.0, 0.0],  # type: ignore[arg-type]
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(TypeError, match="position_at_impact_m must be a numpy"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_launch_direction_wrong_shape() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="launch_direction must have shape"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_partial_nan_launch_direction() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([np.nan, 0.0, 1.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="fully finite or all-NaN"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_non_unit_launch_direction() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([2.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="unit-norm"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_accepts_all_nan_launch_direction() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.full(3, np.nan),
        launch_speed_mps=float("nan"),
        spin_rpm=float("nan"),
    )
    cbt = ClubBallTarget(club=make_target(), ball_impact=bi)
    assert np.all(np.isnan(cbt.ball_impact.launch_direction))


def test_validation_rejects_inf_launch_direction() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([np.inf, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="Inf"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_launch_speed_negative() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=-1.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="launch_speed_mps must be in"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_launch_speed_too_large() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=LAUNCH_SPEED_MAX_MPS + 1.0,
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="launch_speed_mps must be in"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_launch_speed_inf() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=float("inf"),
        spin_rpm=float("nan"),
    )
    with pytest.raises(ValueError, match="launch_speed_mps must be finite or NaN"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_accepts_nan_launch_speed() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=float("nan"),
        spin_rpm=float("nan"),
    )
    cbt = ClubBallTarget(club=make_target(), ball_impact=bi)
    assert np.isnan(cbt.ball_impact.launch_speed_mps)


def test_validation_rejects_spin_negative() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=-1.0,
    )
    with pytest.raises(ValueError, match="spin_rpm must be in"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_spin_too_large() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=99999.0,
    )
    with pytest.raises(ValueError, match="spin_rpm must be in"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_validation_rejects_spin_inf() -> None:
    bi = BallImpactState(
        position_at_impact_m=np.array([0.5, 0.0, 0.0]),
        launch_direction=np.array([1.0, 0.0, 0.0]),
        launch_speed_mps=10.0,
        spin_rpm=float("inf"),
    )
    with pytest.raises(ValueError, match="spin_rpm must be finite or NaN"):
        ClubBallTarget(club=make_target(), ball_impact=bi)


def test_extract_ball_impact_from_clubtarget_happy_path() -> None:
    target = make_target()
    bi = extract_ball_impact_from_clubtarget(target)
    assert isinstance(bi, BallImpactState)
    # Position lives at the clubhead's impact-frame location (1-based -> 0-based).
    expected_pos = target.clubhead[target.impact_idx - 1]
    np.testing.assert_allclose(bi.position_at_impact_m, expected_pos)
    # Direction is unit-norm because the synthetic clubhead has a non-zero v.
    assert np.all(np.isfinite(bi.launch_direction))
    np.testing.assert_allclose(np.linalg.norm(bi.launch_direction), 1.0, atol=1e-9)
    # Speed is finite, in [0, 100], and equal to elasticity * |v_impact|
    # (or clamped).
    assert 0.0 <= bi.launch_speed_mps <= LAUNCH_SPEED_MAX_MPS
    assert np.isnan(bi.spin_rpm)
    # Verify the resulting state is acceptable to ClubBallTarget validation.
    ClubBallTarget(club=target, ball_impact=bi)


def test_extract_ball_impact_clamps_launch_speed() -> None:
    target = make_target(n=5)
    # Build a degenerate target with huge clubhead velocity (>> 100/elasticity).
    huge_speed = LAUNCH_SPEED_MAX_MPS * 10.0  # m/s
    bi = extract_ball_impact_from_clubtarget(_target_with_constant_velocity(huge_speed))
    assert bi.launch_speed_mps == LAUNCH_SPEED_MAX_MPS
    assert target.time.shape[0] == 5  # sanity: didn't mutate fixture target


def test_extract_ball_impact_zero_velocity_yields_nan_direction() -> None:
    target = _target_with_constant_velocity(0.0)
    bi = extract_ball_impact_from_clubtarget(target)
    assert np.all(np.isnan(bi.launch_direction))
    assert bi.launch_speed_mps == 0.0


def test_extract_ball_impact_uses_elasticity_factor() -> None:
    speed_mps = 10.0
    target = _target_with_constant_velocity(speed_mps)
    bi = extract_ball_impact_from_clubtarget(target)
    expected = speed_mps * DEFAULT_ELASTICITY_FACTOR
    assert bi.launch_speed_mps == pytest.approx(expected)


def test_extract_ball_impact_rejects_non_clubtarget() -> None:
    with pytest.raises(TypeError, match="ClubTarget"):
        extract_ball_impact_from_clubtarget("not-a-target")  # type: ignore[arg-type]


def _target_with_constant_velocity(speed_mps: float):
    """A small ClubTarget whose clubhead moves at constant +x velocity.

    Centered around t = 0 so positions stay within the ``MAX_POSITION_NORM_M``
    bound regardless of the requested speed (the bound is 5 m and the time
    span used here is short enough that position remains bounded).
    """
    from src.shared.python.motion_matching.club_target import ClubTarget

    n = 11
    # 1 ms keeps |x| <= speed * 0.5 ms strictly < 5 m for the tested speeds
    # (max speed in tests is 1000 m/s -> max |x| = 0.5 m).
    duration = 0.001
    time = np.linspace(0.0, duration, n)
    centered = time - duration / 2.0
    butt = np.zeros((n, 3))
    butt[:, 0] = speed_mps * centered
    clubhead = butt + np.array([0.0, 0.0, 1.0])
    quat = np.tile(np.array([1.0, 0.0, 0.0, 0.0]), (n, 1))
    return ClubTarget(
        time=time,
        butt=butt,
        clubhead=clubhead,
        club_quat=quat,
        impact_idx=n // 2,
        source=make_provenance(),
    )
