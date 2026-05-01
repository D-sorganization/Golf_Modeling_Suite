"""Generate the reference output artifact for the golf portfolio demo.

This script runs the core physics models exactly as described in
docs/portfolio/golf_modeling_demo.md to generate the reference CSV output.
It avoids hardcoded output values to ensure the artifact remains in sync
with actual simulated physics behavior.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

# Adjust import path to support running from repo root
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def build_model_artifact(dest_path: Path) -> None:
    """Run the simulation and write the results to a CSV."""

    # 1. Setup exactly as described in docs
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

    # Environmental conditions from the demo fixture
    air_density = 1.225
    gravity = 9.81
    env = EnvironmentalConditions(
        gravity=gravity,
        air_density=air_density,
    )

    # Launch conditions from the demo fixture
    ball_speed = 70.0
    launch_angle_deg = 12.0
    backspin_rpm = 2700.0

    launch = LaunchConditions(
        velocity=ball_speed,
        launch_angle=np.radians(launch_angle_deg),
        azimuth_angle=0.0,
        spin_rate=backspin_rpm,
    )

    # 2. Run simulation
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.05)

    # 3. Extract outputs using simulator methods
    carry_m = simulator.calculate_carry_distance(trajectory)
    peak_m = simulator.calculate_max_height(trajectory)
    flight_time_s = simulator.calculate_flight_time(trajectory)

    carry_yd = carry_m * 1.0936

    # 4. Format rows for CSV
    rows = [
        ["quantity", "category", "value", "unit", "source"],
        [
            "ball_speed",
            "measured_input",
            f"{ball_speed:.1f}",
            "m/s",
            "driver launch-condition fixture",
        ],
        [
            "launch_angle",
            "measured_input",
            f"{launch_angle_deg:.1f}",
            "deg",
            "driver launch-condition fixture",
        ],
        [
            "backspin",
            "measured_input",
            f"{int(backspin_rpm)}",
            "rpm",
            "driver launch-condition fixture",
        ],
        [
            "air_density",
            "assumption",
            f"{air_density:.3f}",
            "kg/m^3",
            "sea-level standard atmosphere",
        ],
        [
            "gravity",
            "assumption",
            f"{gravity:.2f}",
            "m/s^2",
            "default simulation environment",
        ],
        [
            "carry_distance",
            "simulated_output",
            f"{carry_m:.1f}",
            "m",
            "portfolio reference fixture",
        ],
        [
            "carry_distance",
            "simulated_output",
            f"{carry_yd:.1f}",
            "yd",
            "portfolio reference fixture",
        ],
        [
            "peak_height",
            "simulated_output",
            f"{peak_m:.1f}",
            "m",
            "portfolio reference fixture",
        ],
        [
            "flight_time",
            "simulated_output",
            f"{flight_time_s:.1f}",
            "s",
            "portfolio reference fixture",
        ],
    ]

    # 5. Write to destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Successfully generated artifact at: {dest_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate portfolio demo artifact.")
    parser.add_argument(
        "--out",
        type=Path,
        default=_project_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv",
        help="Destination path for the CSV output.",
    )
    args = parser.parse_args()

    build_model_artifact(args.out)


if __name__ == "__main__":
    main()
