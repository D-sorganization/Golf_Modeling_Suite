#!/usr/bin/env python3
"""Generate the portfolio demo output artifact from the physics simulation."""

import csv
import sys
from pathlib import Path

import numpy as np

_project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_project_root))

from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)

OUTPUT_FILE = _project_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv"


def main() -> None:
    # Set up environment and ball properties matching the demo
    env = EnvironmentalConditions(gravity=9.81, air_density=1.225)
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

    # Set up launch conditions matching the demo inputs
    launch = LaunchConditions(
        velocity=70.0,
        launch_angle=np.radians(12.0),
        azimuth_angle=0.0,
        spin_rate=2700.0,
    )

    # Run simulation
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.05)

    # Extract outcomes
    landing_pts = [p for p in trajectory if p.height <= 0.0]
    carry_m = 0.0
    carry_yd = 0.0
    if len(landing_pts) >= 2:
        carry_m = float(landing_pts[-1].position[0])
        carry_yd = carry_m * 1.0936133

    peak_height = max([p.height for p in trajectory])
    flight_time = float(trajectory[-1].time)
    if landing_pts:
        flight_time = float(landing_pts[-1].time)

    # Write output to CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["quantity", "category", "value", "unit", "source"])

        # Write inputs
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
                "2700.0",
                "rpm",
                "driver launch-condition fixture",
            ]
        )

        # Write assumptions
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

        # Write simulated outputs
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
                f"{peak_height:.1f}",
                "m",
                "portfolio reference fixture",
            ]
        )
        writer.writerow(
            [
                "flight_time",
                "simulated_output",
                f"{flight_time:.1f}",
                "s",
                "portfolio reference fixture",
            ]
        )


if __name__ == "__main__":
    main()
