#!/usr/bin/env python3
"""Generate the portfolio demo output CSV to match the Rust-backed kernel outputs."""

import csv
import re
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_repo_root))

import numpy as np  # noqa: E402
from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def main() -> None:
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

    # Run the simulation with exact parameters matching basic_flight_simulation.py
    # but use dt=0.01 for more accurate trajectory bounds than the example's dt=0.05
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=8.0, dt=0.01)

    # Calculate output metrics
    landing_pts = [p for p in trajectory if p.height <= 0.0]
    if len(landing_pts) >= 2:
        # Get point just before landing or exact landing
        carry_m = float(landing_pts[-1].position[0])
    else:
        # Fallback to analysis tools if not explicitly caught
        analysis = simulator.analyze_trajectory(trajectory)
        carry_m = analysis["carry_distance"]

    analysis = simulator.analyze_trajectory(trajectory)
    carry_yd = carry_m * 1.0936
    peak_height = analysis["max_height"]
    flight_time = analysis["flight_time"]

    print("Computed metrics for portfolio demo:")
    print(f"Carry: {carry_m:.1f} m / {carry_yd:.1f} yd")
    print(f"Peak: {peak_height:.1f} m")
    print(f"Time: {flight_time:.1f} s")

    # Write output CSV
    output_path = _repo_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv"
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
    print(f"Wrote to {output_path}")

    # Read and update Markdown docs
    docs_path = _repo_root / "docs" / "portfolio" / "golf_modeling_demo.md"
    content = docs_path.read_text(encoding="utf-8")

    # | Carry distance | 218.4 m / 238.8 yd | Simulated landing range for the stated launch condition |
    content = re.sub(
        r"\| Carry distance \| [\d\.]+ m / [\d\.]+ yd \|",
        f"| Carry distance | {carry_m:.1f} m / {carry_yd:.1f} yd |",
        content,
    )
    # | Peak height | 31.6 m | Simulated apex height |
    content = re.sub(
        r"\| Peak height \| [\d\.]+ m \|",
        f"| Peak height | {peak_height:.1f} m |",
        content,
    )
    # | Flight time | 6.4 s | Simulated time aloft |
    content = re.sub(
        r"\| Flight time \| [\d\.]+ s \|",
        f"| Flight time | {flight_time:.1f} s |",
        content,
    )
    docs_path.write_text(content, encoding="utf-8")
    print(f"Updated {docs_path}")


if __name__ == "__main__":
    main()
