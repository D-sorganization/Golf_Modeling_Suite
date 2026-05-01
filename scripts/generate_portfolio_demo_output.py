import csv
import sys
from pathlib import Path

import numpy as np

_this_file = Path(__file__).resolve()
_project_root = _this_file.parents[1]
sys.path.insert(0, str(_project_root))
from src.shared.python.physics.ball_flight_physics import (  # noqa: E402
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def main(output_path=None):
    ball = BallProperties()
    env = EnvironmentalConditions(gravity=9.81, air_density=1.225)
    launch = LaunchConditions(
        velocity=70.0,
        launch_angle=np.radians(12.0),
        azimuth_angle=0.0,
        spin_rate=2700.0,
    )
    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=15.0, dt=0.05)
    carry_m = simulator.calculate_carry_distance(trajectory)
    carry_yd = carry_m * 1.09361
    peak_m = simulator.calculate_max_height(trajectory)
    flight_s = simulator.calculate_flight_time(trajectory)
    if output_path is None:
        output_path = (
            _project_root / "docs" / "portfolio" / "golf_modeling_demo_output.csv"
        )
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
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
                f"{peak_m:.1f}",
                "m",
                "portfolio reference fixture",
            ]
        )
        writer.writerow(
            [
                "flight_time",
                "simulated_output",
                f"{flight_s:.1f}",
                "s",
                "portfolio reference fixture",
            ]
        )


if __name__ == "__main__":
    main()
