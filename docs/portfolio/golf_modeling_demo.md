# Golf Modeling Demo: Physics & Kinematic Validation

This document provides a single, reproducible, and narrowly-scoped demonstration of the UpstreamDrift physics modeling capabilities. It is designed to run out-of-the-box on a fresh clone using our supported continuous-integration physics engine (MuJoCo).

## What This Demonstrates
- **Physics Modeling**: Contact dynamics, forward/inverse kinematics, and multi-body constraints.
- **Validation Discipline**: Comparing generated swing kinematics and simulated outputs against measured or reference physical benchmarks.
- **AI/ML Readiness**: Generation of clean, structured kinematic and dynamic datasets (forces, torques, velocities) suitable for training imitation learning or reinforcement learning policies.

**Limitations to Note**:
- *Speculative Coaching*: The engine accurately simulates physics based on the provided parameters, but bridging simulation outputs to actionable golf coaching requires separate domain expertise. Outputs generated here are simulated physical measurements, not swing advice.
- *Inferred Quantities*: Some outputs (like internal muscle forces) are heavily conditioned on the rigid-body abstractions of the specific engine and model provided.

## Reproducing the Demo

### 1. Setup the Environment

We use the default, CI-supported MuJoCo environment profile.

```bash
# From the repository root:
# Install the core suite and supported MuJoCo tier
python -m pip install -e ".[dev]"
```

*Note: If you encounter issues or want to run on alternative engines (e.g., Drake, Pinocchio), refer to [docs/engines/support_tiers.md](../engines/support_tiers.md) for alternative install commands.*

### 2. Run the Demo Artifact

Run the validation script to generate an inspectable kinematic summary and model artifact. This script simulates a basic kinematic path and logs the output.

```bash
# Run the demo script (Runtime: ~5-15 seconds)
python scripts/demo/generate_portfolio_artifact.py
```

### 3. Inspecting the Outputs

The command above generates output artifacts in the `output/portfolio_demo/` directory.

- `kinematic_summary.json`: Contains the exact joint positions, velocities, and simulated forces.
- `trajectory_plot.png` (or equivalent): Visualizes the modeled path or kinematic constraints over the simulated timeline.

This structured output is the foundational layer upon which we build cross-engine validation and AI/ML model training.
