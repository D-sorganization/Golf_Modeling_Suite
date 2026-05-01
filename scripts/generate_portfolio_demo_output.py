#!/usr/bin/env python3
"""Generate the golf modeling portfolio demo output fixture.

This script simulates a driver shot using the Rust-backed ball flight kernel
and writes the simulated metrics alongside the input assumptions to a CSV file.
The output acts as a verifiable artifact for the portfolio demo documentation.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Allow running from repo root
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
    """Run simulation and generate CSV artifact."""
    output_path = _project_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Setup mirroring basic_flight_simulation.py ---
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
    launch = LaunchConditions(
        velocity=70.0,
        launch_angle=np.radians(12.0),
        azimuth_angle=0.0,
        spin_rate=2700.0,
    )

    # --- Simulate ---
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.05)

    # --- Extract metrics using model methods ---
    carry_m = simulator.calculate_carry_distance(trajectory)
    carry_yd = carry_m * 1.0936
    peak_m = simulator.calculate_max_height(trajectory)
    time_s = simulator.calculate_flight_time(trajectory)

    # --- Write CSV ---
    rows = [
        {
            "quantity": "ball_speed",
            "category": "measured_input",
            "value": "70.0",
            "unit": "m/s",
            "source": "driver launch-condition fixture",
        },
        {
            "quantity": "launch_angle",
            "category": "measured_input",
            "value": "12.0",
            "unit": "deg",
            "source": "driver launch-condition fixture",
        },
        {
            "quantity": "backspin",
            "category": "measured_input",
            "value": "2700",
            "unit": "rpm",
            "source": "driver launch-condition fixture",
        },
        {
            "quantity": "air_density",
            "category": "assumption",
            "value": "1.225",
            "unit": "kg/m^3",
            "source": "sea-level standard atmosphere",
        },
        {
            "quantity": "gravity",
            "category": "assumption",
            "value": "9.81",
            "unit": "m/s^2",
            "source": "default simulation environment",
        },
        {
            "quantity": "carry_distance",
            "category": "simulated_output",
            "value": f"{carry_m:.1f}",
            "unit": "m",
            "source": "portfolio reference fixture",
        },
        {
            "quantity": "carry_distance",
            "category": "simulated_output",
            "value": f"{carry_yd:.1f}",
            "unit": "yd",
            "source": "portfolio reference fixture",
        },
        {
            "quantity": "peak_height",
            "category": "simulated_output",
            "value": f"{peak_m:.1f}",
            "unit": "m",
            "source": "portfolio reference fixture",
        },
        {
            "quantity": "flight_time",
            "category": "simulated_output",
            "value": f"{time_s:.1f}",
            "unit": "s",
            "source": "portfolio reference fixture",
        },
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["quantity", "category", "value", "unit", "source"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {output_path.relative_to(_project_root)}")


if __name__ == "__main__":
    main()
