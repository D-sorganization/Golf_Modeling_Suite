"""Launch conditions, environmental conditions, and trajectory data structures.

This submodule contains dataclasses representing the inputs and outputs of
ball flight simulation, extracted from ball_flight_physics.py as part of P1
sprint decomposition (issue #2486).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.shared.python.core.constants import AIR_DENSITY_SEA_LEVEL_KG_M3, GRAVITY_M_S2


@dataclass(frozen=True)
class LaunchConditions:
    """Initial launch conditions."""

    velocity: float
    launch_angle: float
    azimuth_angle: float = 0.0
    spin_rate: float = 0.0
    spin_axis: np.ndarray = field(default_factory=lambda: np.array([0.0, -1.0, 0.0]))


@dataclass(frozen=True)
class EnvironmentalConditions:
    """Environmental settings."""

    air_density: float = float(AIR_DENSITY_SEA_LEVEL_KG_M3)
    wind_velocity: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.0]))
    gravity: float = float(GRAVITY_M_S2)
    altitude: float = 0.0
    temperature: float = 15.0

    @classmethod
    def from_altitude(
        cls,
        altitude_m: float,
        wind_velocity: np.ndarray | None = None,
    ) -> EnvironmentalConditions:
        """Create conditions with ISA-derived air density for the given altitude.

        Uses the International Standard Atmosphere (ISA) troposphere model
        (valid up to ~11 km). At sea level this reproduces ρ = 1.225 kg/m³.
        At Denver (~1609 m) this gives ρ ≈ 1.045 kg/m³, ~15% lower than
        sea level — consistent with observed carry-distance gains at altitude.

        Args:
            altitude_m: Altitude above sea level [m].
            wind_velocity: Optional wind vector [m/s]; defaults to zero.

        Returns:
            EnvironmentalConditions with density and temperature set from ISA.
        """
        if altitude_m < 0:
            raise ValueError("altitude_m must be non-negative")
        T0, P0 = 288.15, 101325.0  # K, Pa
        L, g, M, R = 0.0065, 9.80665, 0.0289644, 8.31447
        T_k = T0 - L * altitude_m
        P = P0 * (T_k / T0) ** (g * M / (R * L))
        rho = P * M / (R * T_k)
        return cls(
            air_density=rho,
            altitude=altitude_m,
            temperature=T_k - 273.15,
            wind_velocity=wind_velocity if wind_velocity is not None else np.zeros(3),
        )


@dataclass
class TrajectoryPoint:
    """Single point in trajectory."""

    time: float
    position: np.ndarray
    velocity: np.ndarray
    acceleration: np.ndarray
    forces: dict[str, np.ndarray]

    @property
    def speed(self) -> float:
        """Return the scalar speed from the velocity vector."""
        return float(np.linalg.norm(self.velocity))

    @property
    def height(self) -> float:
        """Return the vertical position component."""
        return float(self.position[2])
