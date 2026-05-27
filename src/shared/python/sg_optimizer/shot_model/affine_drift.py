"""AffineDrift biomechanical simulation integration for shot dispersion.

This module provides hooks to derive shot-model parameters from AffineDrift's
drift/control decomposition output.
"""

from __future__ import annotations

import math
from typing import Any

from src.shared.python.contracts import require
from src.shared.python.sg_optimizer.shot_model.distributions import (
    TiltedBivariateGaussian,
)


def derive_dispersion_from_simulation(
    sim_output: dict[str, Any],
    base_sigma_long: float,
    base_sigma_lat: float,
    base_rho: float = 0.2,
) -> TiltedBivariateGaussian:
    """Derive dispersion parameters from AffineDrift simulation output.

    Uses the drift/control decomposition to modulate the baseline dispersion.
    Higher control variance increases the lateral dispersion, while higher
    drift variance increases longitudinal dispersion.

    Args:
        sim_output: Dictionary containing AffineDrift simulation metrics, specifically
            'drift_variance' and 'control_variance'.
        base_sigma_long: Baseline longitudinal standard deviation (yards).
        base_sigma_lat: Baseline lateral standard deviation (yards).
        base_rho: Baseline correlation coefficient.

    Returns:
        A TiltedBivariateGaussian representing the derived shot dispersion.
    """
    require("drift_variance" in sim_output, "sim_output must contain 'drift_variance'")
    require(
        "control_variance" in sim_output, "sim_output must contain 'control_variance'"
    )

    drift_var = float(sim_output["drift_variance"])
    control_var = float(sim_output["control_variance"])

    require(drift_var >= 0, "drift_variance must be non-negative")
    require(control_var >= 0, "control_variance must be non-negative")

    # Scale base sigmas by the square root of normalized variances
    sigma_long = base_sigma_long * max(0.1, math.sqrt(drift_var))
    sigma_lat = base_sigma_lat * max(0.1, math.sqrt(control_var))

    return TiltedBivariateGaussian(
        sigma_long=sigma_long,
        sigma_lat=sigma_lat,
        rho=base_rho,
    )
