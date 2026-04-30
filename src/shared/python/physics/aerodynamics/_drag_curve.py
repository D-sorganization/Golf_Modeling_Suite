"""Drag-crisis-aware Cd(Re) curve for dimpled spheres.

Provides an empirical drag coefficient as a function of Reynolds number,
capturing the drag crisis typical of dimpled spheres (golf balls).
Dimples trip the boundary layer earlier than on a smooth sphere, producing
a sharp Cd drop near Re ~= 4e4-6e4 followed by a shallow basin and a
gentle rise into the post-critical regime.

Sources:
    - Bearman, P.W. & Harvey, J.K. (1976). Golf ball aerodynamics.
      Aeronautical Quarterly, 27(2), 112-122.
    - Achenbach, E. (1972). Experiments on the flow past spheres at very
      high Reynolds numbers. J. Fluid Mech., 54(3), 565-575.
    - Smits, A.J. & Ogg, S. (2004). Golf ball aerodynamics. Physics Today.
"""

from __future__ import annotations

import math

import numpy as np

from src.shared.python.core.physics_constants import GOLF_BALL_DRAG_COEFFICIENT

# Empirical lookup table for a dimpled sphere. Anchor points were chosen so
# np.interp produces a continuous, monotone transition through the crisis
# region and a smooth rise post-critical.
_CD_DIMPLED_RE_TABLE: tuple[float, ...] = (
    1.0e3,
    1.0e4,
    3.0e4,
    4.0e4,
    5.0e4,
    6.0e4,
    8.0e4,
    1.0e5,
    1.5e5,
    2.0e5,
    2.5e5,
    3.0e5,
    5.0e5,
    1.0e6,
)
_CD_DIMPLED_CD_TABLE: tuple[float, ...] = (
    0.50,
    0.50,
    0.48,
    0.42,
    0.26,
    0.22,
    0.21,
    0.22,
    0.23,
    0.25,
    0.26,
    0.27,
    0.28,
    0.30,
)


def _cd_dimpled_sphere(re: float) -> float:
    """Drag coefficient for a dimpled sphere as a function of Reynolds number.

    Uses piecewise-linear interpolation over an empirical lookup table that
    captures the drag crisis (sharp Cd drop near Re ~= 4e4-6e4) and the
    subsequent post-crisis rise. Values outside the tabulated range clamp
    to the nearest endpoint, the standard ``np.interp`` behaviour.

    Args:
        re: Reynolds number based on ball diameter (must be non-negative
            and finite).

    Returns:
        Drag coefficient (dimensionless), clamped to ``[0.10, 0.55]``.

    Raises:
        ValueError: If ``re`` is negative or non-finite.
    """
    re_value = float(re)
    if not math.isfinite(re_value):
        raise ValueError(f"Reynolds number must be finite, got {re!r}")
    if re_value < 0.0:
        raise ValueError(f"Reynolds number must be non-negative, got {re!r}")

    cd = float(np.interp(re_value, _CD_DIMPLED_RE_TABLE, _CD_DIMPLED_CD_TABLE))
    # Defensive clamp; np.interp output is already bounded by the table,
    # but keep the postcondition explicit so future edits cannot silently
    # break callers.
    return float(np.clip(cd, 0.10, 0.55))


def drag_coefficient(re: float, base_coefficient: float | None = None) -> float:
    """Public drag coefficient as a function of Reynolds number.

    Returns the dimpled-sphere base curve, optionally rescaled so the
    high-Re asymptote matches a user-specified ``base_coefficient`` (the
    Cd value used in the legacy "fully turbulent" regime). The curve
    shape is preserved across the entire Re range under rescaling, so
    callers that tune ``base_coefficient`` get a consistent, smooth
    response.

    Args:
        re: Reynolds number based on ball diameter.
        base_coefficient: Optional Cd anchor for the post-critical regime.
            When ``None``, the canonical project default is used.

    Returns:
        Drag coefficient (dimensionless).
    """
    cd_curve = _cd_dimpled_sphere(re)
    if base_coefficient is None:
        return cd_curve

    anchor = float(GOLF_BALL_DRAG_COEFFICIENT)
    scale = float(base_coefficient) / anchor if anchor > 0 else 1.0
    return float(np.clip(cd_curve * scale, 0.05, 0.80))


def _validate_cd_curve() -> dict[str, float]:
    """Sanity-check helper: sample the dimpled-sphere Cd(Re) curve.

    Not invoked automatically. Intended for ad-hoc REPL inspection so a
    human can confirm the curve still respects the empirical bands at
    canonical Reynolds numbers (pre-crisis, crisis trough, post-crisis
    basin, post-critical).

    Returns:
        Mapping ``{regime_label: cd}`` for inspection.
    """
    return {
        "pre_crisis_re_1e4": _cd_dimpled_sphere(1.0e4),
        "crisis_trough_re_5e4": _cd_dimpled_sphere(5.0e4),
        "post_crisis_basin_re_1e5": _cd_dimpled_sphere(1.0e5),
        "post_critical_re_3e5": _cd_dimpled_sphere(3.0e5),
    }
