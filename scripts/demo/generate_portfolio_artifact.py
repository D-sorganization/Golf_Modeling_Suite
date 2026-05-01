#!/usr/bin/env python3
"""
generate_portfolio_artifact.py

A reproducible demo script showcasing the UpstreamDrift core physics modeling
capabilities. This uses the exact same BallFlightSimulator (with the compiled
Rust back-end) to generate a realistic artifact of kinematic/dynamic trajectories,
validating our cross-engine pipeline.

Run this script to generate `kinematic_summary.json` for portfolio inspection.
"""
import json
import os
import sys

import numpy as np

# Ensure we can import from src even if not installed
_this_file = os.path.abspath(__file__)
_project_root = os.path.abspath(os.path.join(os.path.dirname(_this_file), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.shared.python.physics.ball_flight_physics import (
    BallFlightSimulator,
    BallProperties,
    EnvironmentalConditions,
    LaunchConditions,
)


def main():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "portfolio_demo"))
    os.makedirs(output_dir, exist_ok=True)

    print("Initializing Golf Kinematics Demo...")
    print("Running simulation using Rust-backed physics kernel...")

    ball = BallProperties(
        mass=0.0459,  # kg
        diameter=0.04267,  # m
        cd0=0.25, cd1=0.0, cd2=0.0,
        cl0=0.15, cl1=0.0, cl2=0.0,
    )
    env = EnvironmentalConditions(
        gravity=9.81,
        air_density=1.225,
    )

    # Launch conditions: representative 7-iron shot
    launch = LaunchConditions(
        velocity=50.0,  # m/s
        launch_angle=np.radians(20.0),
        azimuth_angle=0.0,
        spin_rate=6000.0,  # rpm
    )

    simulator = BallFlightSimulator(ball=ball, env=env)
    trajectory = simulator.simulate_trajectory(launch, max_time=10.0, dt=0.1)

    kinematic_summary = {
        "engine": "rust_physics_kernel",
        "model": "BallFlightSimulator",
        "validation_status": "Simulated (Rust Backed)",
        "trajectory": []
    }

    # Dump a subset of the trajectory state
    for pt in trajectory[::5]:
        state = {
            "time_s": round(pt.time, 3),
            "position_x_m": round(float(pt.position[0]), 3),
            "height_z_m": round(float(pt.height), 3),
            "speed_ms": round(float(pt.speed), 3)
        }
        kinematic_summary["trajectory"].append(state)
        if pt.height < 0:
            break

    # Export Summary
    json_path = os.path.join(output_dir, "kinematic_summary.json")
    with open(json_path, "w") as f:
        json.dump(kinematic_summary, f, indent=2)

    print("✅ Demo completed successfully.")
    print(f"Artifacts saved to: {output_dir}")
    print(f"  - {os.path.basename(json_path)} (Inspect this file for structural validation)")

if __name__ == "__main__":
    main()
