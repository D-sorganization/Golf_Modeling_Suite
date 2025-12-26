#!/usr/bin/env python3
"""
Physics Validation Suite

This script validates physics accuracy and consistency across different engines
in the Golf Modeling Suite. It performs cross-engine comparisons and accuracy
verification for biomechanical analysis.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np

from shared.python.core import setup_logging

logger = setup_logging(__name__)


class PhysicsValidator:
    """Validates physics accuracy across different engines."""

    def __init__(self):
        """Initialize the physics validator."""
        self.validation_results = {}
        self.tolerance = 1e-6
        self.relative_tolerance = 1e-3

    def validate_conservation_laws(
        self, engine_name: str, simulation_data: dict
    ) -> dict:
        """Validate conservation of energy and momentum."""
        results = {
            "energy_conservation": False,
            "momentum_conservation": False,
            "energy_drift": 0.0,
            "momentum_drift": 0.0,
        }

        try:
            # Extract time series data
            time = simulation_data.get("time", [])
            kinetic_energy = simulation_data.get("kinetic_energy", [])
            potential_energy = simulation_data.get("potential_energy", [])
            total_energy = simulation_data.get("total_energy", [])

            if not all([time, kinetic_energy, potential_energy, total_energy]):
                logger.warning(f"Incomplete energy data for {engine_name}")
                return results

            # Check energy conservation
            initial_energy = total_energy[0]
            final_energy = total_energy[-1]
            energy_drift = abs(final_energy - initial_energy) / abs(initial_energy)

            results["energy_drift"] = energy_drift
            results["energy_conservation"] = energy_drift < self.relative_tolerance

            # Check momentum conservation (if no external forces)
            momentum = simulation_data.get("linear_momentum", [])
            if momentum:
                initial_momentum = np.array(momentum[0])
                final_momentum = np.array(momentum[-1])
                momentum_drift = np.linalg.norm(final_momentum - initial_momentum)
                momentum_drift /= np.linalg.norm(initial_momentum) + 1e-12

                results["momentum_drift"] = momentum_drift
                results["momentum_conservation"] = (
                    momentum_drift < self.relative_tolerance
                )

            logger.info(
                f"{engine_name} - Energy drift: {energy_drift:.6f}, "
                f"Momentum drift: {results['momentum_drift']:.6f}"
            )

        except Exception as e:
            logger.error(f"Conservation law validation failed for {engine_name}: {e}")

        return results

    def validate_joint_constraints(
        self, engine_name: str, simulation_data: dict
    ) -> dict:
        """Validate joint constraint satisfaction."""
        results = {
            "constraint_violations": [],
            "max_violation": 0.0,
            "constraint_satisfaction": False,
        }

        try:
            # Check joint position constraints
            joint_positions = simulation_data.get("joint_positions", [])
            joint_limits = simulation_data.get("joint_limits", {})

            if not joint_positions or not joint_limits:
                logger.warning(f"Incomplete joint data for {engine_name}")
                return results

            violations = []
            for timestep, positions in enumerate(joint_positions):
                for joint_idx, pos in enumerate(positions):
                    if joint_idx in joint_limits:
                        min_limit, max_limit = joint_limits[joint_idx]
                        if pos < min_limit or pos > max_limit:
                            violation = max(min_limit - pos, pos - max_limit)
                            violations.append(
                                {
                                    "timestep": timestep,
                                    "joint": joint_idx,
                                    "position": pos,
                                    "violation": violation,
                                }
                            )

            results["constraint_violations"] = violations
            if violations:
                results["max_violation"] = max(v["violation"] for v in violations)
            results["constraint_satisfaction"] = (
                results["max_violation"] < self.tolerance
            )

            logger.info(
                f"{engine_name} - Joint constraint violations: {len(violations)}, "
                f"Max violation: {results['max_violation']:.6f}"
            )

        except Exception as e:
            logger.error(f"Joint constraint validation failed for {engine_name}: {e}")

        return results

    def validate_numerical_stability(
        self, engine_name: str, simulation_data: dict
    ) -> dict:
        """Validate numerical stability and integration accuracy."""
        results = {
            "stable": False,
            "max_velocity": 0.0,
            "max_acceleration": 0.0,
            "integration_error": 0.0,
        }

        try:
            velocities = simulation_data.get("joint_velocities", [])
            accelerations = simulation_data.get("joint_accelerations", [])

            if not velocities:
                logger.warning(f"No velocity data for {engine_name}")
                return results

            # Check for numerical explosions
            max_vel = max(np.max(np.abs(v)) for v in velocities)
            results["max_velocity"] = max_vel

            if accelerations:
                max_acc = max(np.max(np.abs(a)) for a in accelerations)
                results["max_acceleration"] = max_acc

            # Consider stable if velocities and accelerations are reasonable
            velocity_stable = max_vel < 1000.0  # Reasonable threshold
            acceleration_stable = results["max_acceleration"] < 10000.0

            results["stable"] = velocity_stable and acceleration_stable

            logger.info(
                f"{engine_name} - Max velocity: {max_vel:.3f}, "
                f"Max acceleration: {results['max_acceleration']:.3f}, "
                f"Stable: {results['stable']}"
            )

        except Exception as e:
            logger.error(
                f"Numerical stability validation failed for {engine_name}: {e}"
            )

        return results

    def compare_engines(self, engine_data: dict[str, dict]) -> dict:
        """Compare results between different physics engines."""
        comparison_results = {
            "engines_compared": list(engine_data.keys()),
            "position_agreement": {},
            "velocity_agreement": {},
            "energy_agreement": {},
            "overall_agreement": False,
        }

        try:
            engine_names = list(engine_data.keys())
            if len(engine_names) < 2:
                logger.warning("Need at least 2 engines for comparison")
                return comparison_results

            # Compare pairwise
            for i, engine1 in enumerate(engine_names):
                for engine2 in engine_names[i + 1 :]:
                    pair_key = f"{engine1}_vs_{engine2}"

                    # Compare positions
                    pos1 = engine_data[engine1].get("joint_positions", [])
                    pos2 = engine_data[engine2].get("joint_positions", [])

                    if pos1 and pos2:
                        pos_agreement = self._compare_trajectories(pos1, pos2)
                        comparison_results["position_agreement"][
                            pair_key
                        ] = pos_agreement

                    # Compare velocities
                    vel1 = engine_data[engine1].get("joint_velocities", [])
                    vel2 = engine_data[engine2].get("joint_velocities", [])

                    if vel1 and vel2:
                        vel_agreement = self._compare_trajectories(vel1, vel2)
                        comparison_results["velocity_agreement"][
                            pair_key
                        ] = vel_agreement

                    # Compare energies
                    energy1 = engine_data[engine1].get("total_energy", [])
                    energy2 = engine_data[engine2].get("total_energy", [])

                    if energy1 and energy2:
                        energy_agreement = self._compare_scalars(energy1, energy2)
                        comparison_results["energy_agreement"][
                            pair_key
                        ] = energy_agreement

            # Overall agreement if all comparisons are good
            all_agreements = []
            all_agreements.extend(comparison_results["position_agreement"].values())
            all_agreements.extend(comparison_results["velocity_agreement"].values())
            all_agreements.extend(comparison_results["energy_agreement"].values())

            if all_agreements:
                comparison_results["overall_agreement"] = all(
                    agreement > 0.9 for agreement in all_agreements
                )

        except Exception as e:
            logger.error(f"Engine comparison failed: {e}")

        return comparison_results

    def _compare_trajectories(self, traj1: list, traj2: list) -> float:
        """Compare two trajectory time series."""
        try:
            # Ensure same length
            min_len = min(len(traj1), len(traj2))
            traj1 = traj1[:min_len]
            traj2 = traj2[:min_len]

            # Convert to numpy arrays
            arr1 = np.array(traj1)
            arr2 = np.array(traj2)

            # Compute normalized RMS error
            diff = arr1 - arr2
            rms_error = np.sqrt(np.mean(diff**2))

            # Normalize by signal magnitude
            signal_magnitude = np.sqrt(np.mean(arr1**2)) + 1e-12
            normalized_error = rms_error / signal_magnitude

            # Agreement score (1.0 = perfect, 0.0 = no agreement)
            agreement = max(0.0, 1.0 - normalized_error)

            return agreement

        except Exception:
            return 0.0

    def _compare_scalars(self, series1: list, series2: list) -> float:
        """Compare two scalar time series."""
        try:
            min_len = min(len(series1), len(series2))
            arr1 = np.array(series1[:min_len])
            arr2 = np.array(series2[:min_len])

            # Compute relative error
            relative_error = np.mean(np.abs(arr1 - arr2) / (np.abs(arr1) + 1e-12))

            # Agreement score
            agreement = max(0.0, 1.0 - relative_error)

            return agreement

        except Exception:
            return 0.0

    def generate_validation_report(self, validation_data: dict) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("# Physics Validation Report")
        report.append("=" * 50)
        report.append("")

        # Individual engine results
        for engine_name, engine_results in validation_data.items():
            if engine_name == "comparison":
                continue

            report.append(f"## {engine_name.upper()} Engine")
            report.append("")

            # Conservation laws
            if "conservation" in engine_results:
                cons = engine_results["conservation"]
                report.append("### Conservation Laws")
                report.append(
                    f"- Energy Conservation: {'✅' if cons['energy_conservation'] else '❌'}"
                )
                report.append(f"- Energy Drift: {cons['energy_drift']:.6f}")
                report.append(
                    f"- Momentum Conservation: {'✅' if cons['momentum_conservation'] else '❌'}"
                )
                report.append(f"- Momentum Drift: {cons['momentum_drift']:.6f}")
                report.append("")

            # Joint constraints
            if "constraints" in engine_results:
                const = engine_results["constraints"]
                report.append("### Joint Constraints")
                report.append(
                    f"- Constraint Satisfaction: {'✅' if const['constraint_satisfaction'] else '❌'}"
                )
                report.append(f"- Max Violation: {const['max_violation']:.6f}")
                report.append(
                    f"- Total Violations: {len(const['constraint_violations'])}"
                )
                report.append("")

            # Numerical stability
            if "stability" in engine_results:
                stab = engine_results["stability"]
                report.append("### Numerical Stability")
                report.append(f"- Stable: {'✅' if stab['stable'] else '❌'}")
                report.append(f"- Max Velocity: {stab['max_velocity']:.3f}")
                report.append(f"- Max Acceleration: {stab['max_acceleration']:.3f}")
                report.append("")

        # Cross-engine comparison
        if "comparison" in validation_data:
            comp = validation_data["comparison"]
            report.append("## Cross-Engine Comparison")
            report.append("")
            report.append(f"- Engines Compared: {', '.join(comp['engines_compared'])}")
            report.append(
                f"- Overall Agreement: {'✅' if comp['overall_agreement'] else '❌'}"
            )
            report.append("")

            if comp["position_agreement"]:
                report.append("### Position Agreement")
                for pair, agreement in comp["position_agreement"].items():
                    report.append(f"- {pair}: {agreement:.3f}")
                report.append("")

            if comp["velocity_agreement"]:
                report.append("### Velocity Agreement")
                for pair, agreement in comp["velocity_agreement"].items():
                    report.append(f"- {pair}: {agreement:.3f}")
                report.append("")

        return "\n".join(report)

    def run_validation_suite(self, simulation_results: dict[str, dict]) -> dict:
        """Run the complete validation suite."""
        logger.info("Starting physics validation suite...")

        validation_results = {}

        # Validate each engine individually
        for engine_name, sim_data in simulation_results.items():
            logger.info(f"Validating {engine_name} engine...")

            engine_results = {}
            engine_results["conservation"] = self.validate_conservation_laws(
                engine_name, sim_data
            )
            engine_results["constraints"] = self.validate_joint_constraints(
                engine_name, sim_data
            )
            engine_results["stability"] = self.validate_numerical_stability(
                engine_name, sim_data
            )

            validation_results[engine_name] = engine_results

        # Cross-engine comparison
        if len(simulation_results) > 1:
            logger.info("Performing cross-engine comparison...")
            validation_results["comparison"] = self.compare_engines(simulation_results)

        logger.info("Physics validation suite completed")
        return validation_results


def create_mock_simulation_data():
    """Create mock simulation data for testing."""
    # Generate synthetic golf swing data
    time = np.linspace(0, 2.0, 200)  # 2 second swing

    # Simple pendulum-like motion for golf swing
    shoulder_angle = -1.2 * np.cos(2 * np.pi * time / 2.0) + 0.2 * np.sin(
        4 * np.pi * time / 2.0
    )
    wrist_angle = 1.3 * np.sin(2 * np.pi * time / 2.0) + 0.1 * np.cos(
        6 * np.pi * time / 2.0
    )

    joint_positions = [[shoulder_angle[i], wrist_angle[i]] for i in range(len(time))]

    # Compute velocities (numerical derivative)
    dt = time[1] - time[0]
    joint_velocities = []
    for i in range(1, len(joint_positions)):
        vel = [
            (joint_positions[i][j] - joint_positions[i - 1][j]) / dt for j in range(2)
        ]
        joint_velocities.append(vel)

    # Simple energy calculation (kinetic + potential)
    kinetic_energy = [0.5 * sum(v**2 for v in vel) for vel in joint_velocities]
    potential_energy = [
        9.81 * (np.sin(pos[0]) + np.sin(pos[1])) for pos in joint_positions[1:]
    ]
    total_energy = [
        ke + pe for ke, pe in zip(kinetic_energy, potential_energy, strict=True)
    ]

    return {
        "time": time[1:].tolist(),
        "joint_positions": joint_positions[1:],
        "joint_velocities": joint_velocities,
        "joint_accelerations": [[0.0, 0.0]] * len(joint_velocities),  # Simplified
        "kinetic_energy": kinetic_energy,
        "potential_energy": potential_energy,
        "total_energy": total_energy,
        "linear_momentum": [[0.0, 0.0, 0.0]] * len(time[1:]),  # Simplified
        "joint_limits": {0: [-np.pi, np.pi], 1: [-np.pi, np.pi]},
    }


def main():
    """Run physics validation tests."""
    print("🔬 Physics Validation Suite")
    print("=" * 50)

    # Create mock data for testing
    mock_data = {
        "mujoco": create_mock_simulation_data(),
        "drake": create_mock_simulation_data(),
        "pinocchio": create_mock_simulation_data(),
    }

    # Add some variation to drake data to test comparison
    for i in range(len(mock_data["drake"]["joint_positions"])):
        mock_data["drake"]["joint_positions"][i][0] += 0.001 * np.random.randn()

    # Run validation
    validator = PhysicsValidator()
    results = validator.run_validation_suite(mock_data)

    # Generate report
    report = validator.generate_validation_report(results)
    print(report)

    # Save results
    output_dir = Path("output/validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(
        output_dir / "physics_validation_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(results, f, indent=2, default=str)

    with open(output_dir / "physics_validation_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📊 Results saved to {output_dir}")


if __name__ == "__main__":
    main()
