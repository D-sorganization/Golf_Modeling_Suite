"""Drag-crisis-aware Cd(Re) tests for the dimpled-sphere aerodynamics model.

These tests pin the empirical bands a real dimpled golf ball obeys across
the canonical Reynolds number regimes (pre-crisis, crisis trough,
post-crisis basin, post-critical) and assert that the curve is continuous
to within a small jump tolerance over a logarithmic Re sweep.

References:
    - Bearman, P.W. & Harvey, J.K. (1976). Golf ball aerodynamics.
    - Achenbach, E. (1972). Experiments on the flow past spheres at very
      high Reynolds numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.shared.python.physics.aerodynamics import drag_coefficient
from src.shared.python.physics.aerodynamics._drag_curve import _cd_dimpled_sphere


@pytest.mark.unit
@pytest.mark.parametrize(
    ("re", "low", "high"),
    [
        (1e4, 0.45, 0.55),  # pre-crisis: laminar, Cd ~ 0.5
        (5e4, 0.18, 0.30),  # drag-crisis trough
        (1e5, 0.18, 0.28),  # post-crisis basin
        (3e5, 0.25, 0.32),  # post-critical
    ],
)
def test_drag_coefficient_within_empirical_band(
    re: float, low: float, high: float
) -> None:
    """Cd lies within the empirical band at canonical Reynolds numbers."""
    cd = drag_coefficient(re)
    assert low <= cd <= high, f"Cd={cd} out of band [{low}, {high}] at Re={re}"


@pytest.mark.unit
def test_drag_coefficient_continuous() -> None:
    """No discontinuities > 0.1 Cd between adjacent Re samples (log-spaced)."""
    res = np.logspace(3, 6, 200)
    cds = [drag_coefficient(float(r)) for r in res]
    diffs = np.abs(np.diff(cds))
    assert diffs.max() < 0.1, f"Max jump {diffs.max()} too large"


@pytest.mark.unit
def test_drag_crisis_drop_present() -> None:
    """Cd at the crisis trough is markedly below the pre-crisis plateau."""
    cd_pre = drag_coefficient(1e4)
    cd_trough = drag_coefficient(6e4)
    assert cd_pre - cd_trough > 0.20, (
        f"Expected drag crisis drop > 0.20, got {cd_pre - cd_trough:.3f}"
    )


@pytest.mark.unit
def test_post_crisis_rises_into_post_critical() -> None:
    """Cd rises gently from the post-crisis basin into post-critical Re."""
    cd_basin = drag_coefficient(1e5)
    cd_post_critical = drag_coefficient(3e5)
    assert cd_post_critical > cd_basin, (
        f"Expected post-critical Cd ({cd_post_critical}) > "
        f"post-crisis basin ({cd_basin})"
    )


@pytest.mark.unit
def test_helper_rejects_negative_re() -> None:
    """The internal helper rejects negative Reynolds numbers."""
    with pytest.raises(ValueError, match="non-negative"):
        _cd_dimpled_sphere(-1.0)


@pytest.mark.unit
def test_helper_rejects_non_finite_re() -> None:
    """The internal helper rejects non-finite Reynolds numbers."""
    with pytest.raises(ValueError, match="finite"):
        _cd_dimpled_sphere(float("nan"))


@pytest.mark.unit
def test_base_coefficient_rescales_curve() -> None:
    """Tuning ``base_coefficient`` linearly rescales the dimpled-sphere curve."""
    re = 1.5e5
    default_cd = drag_coefficient(re)
    tuned_cd = drag_coefficient(re, base_coefficient=0.20)
    # 0.20 / 0.25 (canonical anchor) = 0.8
    assert tuned_cd == pytest.approx(default_cd * 0.8, rel=1e-6)
