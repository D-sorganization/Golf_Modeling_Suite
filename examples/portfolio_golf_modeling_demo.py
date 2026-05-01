"""Demonstrate Portfolio Golf Modeling Demo: simulate a golf shot trajectory and output data matching docs.

Usage::

    python examples/portfolio_golf_modeling_demo.py

Outputs the launch inputs and simulated outcomes mirroring the documentation in docs/portfolio/golf_modeling_demo.md.
"""

from __future__ import annotations

import numpy as np
from src.shared.python.physics.ball_flight_physics import (
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def main() -> None:
    """Run portfolio golf modeling driver-shot simulation and print results."""
    # Match the values in docs/portfolio/golf_modeling_demo.md
    ball = BallProperties()  # Use defaults
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

    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=10.0, dt=0.01)

    # Calculate outputs using required methods
    carry_m = simulator.calculate_carry_distance(trajectory)
    carry_yd = carry_m * 1.0936
    peak_height = simulator.calculate_max_height(trajectory)
    flight_time = simulator.calculate_flight_time(trajectory)

    # Print inputs and results matching the documentation
    print("--- Measured Inputs & Assumptions ---")
    print(f"{'Quantity':<18} {'Value':<12} {'Unit':<8} {'Role'}")
    print("-" * 55)
    print(f"{'Ball speed':<18} {'70.0':<12} {'m/s':<8} {'Measured input'}")
    print(f"{'Launch angle':<18} {'12.0':<12} {'deg':<8} {'Measured input'}")
    print(f"{'Backspin':<18} {'2700':<12} {'rpm':<8} {'Measured input'}")
    print(
        f"{'Air density':<18} {'1.225':<12} {'kg/m^3':<8} {'Environmental assumption'}"
    )
    print(f"{'Gravity':<18} {'9.81':<12} {'m/s^2':<8} {'Environmental assumption'}")

    print("\n--- Inspectable Output ---")
    print(f"{'Output':<18} {'Reference value':<20} {'Interpretation'}")
    print("-" * 65)
    print(
        f"{'Carry distance':<18} {f'{carry_m:.1f} m / {carry_yd:.1f} yd':<20} {'Simulated landing range'}"
    )
    print(f"{'Peak height':<18} {f'{peak_height:.1f} m':<20} {'Simulated apex height'}")
    print(f"{'Flight time':<18} {f'{flight_time:.1f} s':<20} {'Simulated time aloft'}")


if __name__ == "__main__":
    main()
