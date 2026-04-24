"""Demonstrate BallFlightSimulator: simulate a golf shot trajectory.

Usage::

    python3 examples/basic_flight_simulation.py

Prints a summary table of trajectory points (time, x, z, speed) and
the estimated carry distance to landing.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root without installing the package
_this_file = Path(__file__).resolve()
_project_root = _this_file.parents[1]
sys.path.insert(0, str(_project_root))

import numpy as np  # noqa: E402

from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def main() -> None:
    """Run a basic driver-shot simulation and print results."""
    # --- Ball and environment setup ---
    ball = BallProperties(
        mass=0.0459,  # kg (regulation golf ball)
        diameter=0.04267,  # m (regulation diameter)
        cd0=0.25,
        cd1=0.0,
        cd2=0.0,
        cl0=0.15,
        cl1=0.0,
        cl2=0.0,
    )
    env = EnvironmentalConditions(
        gravity=9.81,
        air_density=1.225,  # kg/m³ at sea level
    )

    # --- Launch conditions: driver shot ---
    launch = LaunchConditions(
        velocity=70.0,  # m/s (~157 mph ball speed)
        launch_angle=np.radians(12.0),
        azimuth_angle=0.0,
        spin_rate=2700.0,  # rpm (back-spin)
    )

    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.05)

    # --- Print summary every 0.5 s ---
    print("\n--- Trajectory Summary (every 0.5 s) ---")
    print(f"{'Time (s)':<10} {'X (m)':<10} {'Z (m)':<10} {'Speed (m/s)':<12}")
    print("-" * 42)
    for pt in trajectory[::10]:
        speed = float(np.linalg.norm(pt.velocity))
        print(
            f"{pt.time:<10.2f} {pt.position[0]:<10.2f} {pt.height:<10.2f} {speed:<12.2f}"
        )

    # --- Carry distance: last point before height < 0 ---
    landing_pts = [p for p in trajectory if p.height <= 0.0]
    if len(landing_pts) >= 2:
        carry_m = float(landing_pts[-1].position[0])
        carry_yards = carry_m * 1.0936
        print("\n--- Results ---")
        print(f"Carry Distance: {carry_m:.1f} m ({carry_yards:.1f} yd)")
        print(f"Peak Height: {max(p.height for p in trajectory):.2f} m")
    else:
        print("\n--- Results ---")
        print("No landing detected (ball still in flight at max time)")


if __name__ == "__main__":
    main()
