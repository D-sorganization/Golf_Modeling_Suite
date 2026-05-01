#!/usr/bin/env python3
"""
Generate the output artifact for the golf modeling portfolio demo.

This script runs the ball flight simulator and persists the actual
computed outputs into `docs/portfolio/golf_modeling_demo_output.csv`.
It uses the simulation model dynamically rather than hardcoding outputs
to prevent hiding regressions.
"""

import csv
import sys
from pathlib import Path

# Need to ensure the repo root is in path if run outside module mode
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def generate_output(output_path: Path) -> None:
    # Setup ball and environment
    ball = BallProperties(
        mass=0.0459,
        diameter=0.04267,
        cd0=0.25,
        cd1=0.0,
        cd2=0.0,
        cl0=0.15,
        cl1=0.0,
        cl2=0.0,
    )
    env = EnvironmentalConditions(
        gravity=9.81,
        air_density=1.225,
    )

    # Launch conditions
    launch = LaunchConditions(
        velocity=70.0,
        launch_angle=12.0 * (3.141592653589793 / 180.0),  # radians
        azimuth_angle=0.0,
        spin_rate=2700.0,
    )

    # Run simulation
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.05)

    # Calculate metrics
    # Follow basic_flight_simulation.py logic for carry distance
    landing_pts = [p for p in trajectory if p.height <= 0.0]
    carry_m = float(landing_pts[-1].position[0]) if len(landing_pts) >= 2 else 0.0
    carry_yd = carry_m * 1.0936
    peak_m = float(max(p.height for p in trajectory))
    time_s = trajectory[-1].time

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["quantity", "category", "value", "unit", "source"])

        # Inputs
        writer.writerow(
            [
                "ball_speed",
                "measured_input",
                "70.0",
                "m/s",
                "driver launch-condition fixture",
            ]
        )
        writer.writerow(
            [
                "launch_angle",
                "measured_input",
                "12.0",
                "deg",
                "driver launch-condition fixture",
            ]
        )
        writer.writerow(
            [
                "backspin",
                "measured_input",
                "2700",
                "rpm",
                "driver launch-condition fixture",
            ]
        )

        # Assumptions
        writer.writerow(
            [
                "air_density",
                "assumption",
                "1.225",
                "kg/m^3",
                "sea-level standard atmosphere",
            ]
        )
        writer.writerow(
            ["gravity", "assumption", "9.81", "m/s^2", "default simulation environment"]
        )

        # Outputs
        writer.writerow(
            [
                "carry_distance",
                "simulated_output",
                f"{carry_m:.1f}",
                "m",
                "portfolio reference fixture",
            ]
        )
        writer.writerow(
            [
                "carry_distance",
                "simulated_output",
                f"{carry_yd:.1f}",
                "yd",
                "portfolio reference fixture",
            ]
        )
        writer.writerow(
            [
                "peak_height",
                "simulated_output",
                f"{peak_m:.1f}",
                "m",
                "portfolio reference fixture",
            ]
        )
        writer.writerow(
            [
                "flight_time",
                "simulated_output",
                f"{time_s:.1f}",
                "s",
                "portfolio reference fixture",
            ]
        )


if __name__ == "__main__":
    output_path = repo_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv"
    generate_output(output_path)
