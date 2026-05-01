#!/usr/bin/env python3
"""Generate the portfolio golf modeling demo output CSV artifact."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

# Adjust sys.path so we can run directly
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))

from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def generate_csv(output_path: Path) -> None:
    # Ensure parent dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Ball and environment setup ---
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

    # --- Launch conditions: driver shot ---
    launch = LaunchConditions(
        velocity=70.0,
        launch_angle=np.radians(12.0),
        azimuth_angle=0.0,
        spin_rate=2700.0,
    )

    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=15.0, dt=0.01)

    # Calculate outputs
    peak_height = max(p.height for p in trajectory)

    # Carry distance: exact interpolation where height crosses 0
    carry_m = 0.0
    flight_time = 0.0
    for i in range(1, len(trajectory)):
        p1 = trajectory[i - 1]
        p2 = trajectory[i]
        if p1.height >= 0 and p2.height < 0:
            # Linear interpolation
            t = p1.height / (p1.height - p2.height)
            carry_m = p1.position[0] + t * (p2.position[0] - p1.position[0])
            flight_time = p1.time + t * (p2.time - p1.time)
            break

    if carry_m == 0.0:
        # Fallback if it didn't land
        carry_m = float(trajectory[-1].position[0])
        flight_time = float(trajectory[-1].time)

    carry_yards = carry_m * 1.09361

    # Write CSV
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "category", "value", "unit", "source"])
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

        # Simulated outputs
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
                f"{carry_yards:.1f}",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=_project_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv",
        help="Path to output CSV",
    )
    args = parser.parse_args()
    generate_csv(args.output)
    print(f"Successfully generated {args.output}")


if __name__ == "__main__":
    main()
