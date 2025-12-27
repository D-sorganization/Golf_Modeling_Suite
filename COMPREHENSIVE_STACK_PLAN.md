# Comprehensive Biomechanics-Robotics Integration Plan

**Created:** 2025-12-27
**Author:** Golf Modeling Suite Architecture Team
**Status:** Strategic Planning Phase

---

## Executive Summary

This plan integrates **9 specialized tools** to create a unified Biomechanics-Robotics pipeline for golf swing analysis. The key insight is bridging two worldviews:

- **Robotics View:** Joint torques, motors, contact dynamics (Drake, Pinocchio, MuJoCo)
- **Biomechanics View:** Muscle forces, moment arms, metabolic cost (OpenSim, MyoSim)

**Goal:** Build the "Ultimate Python Golf Pipeline" that can:
1. Extract kinematics from video (OpenPose)
2. Optimize motion (CasADi + Pinocchio)
3. Analyze muscle forces (OpenSim + MyoSim)
4. Simulate contact dynamics (MuJoCo)
5. Bridge between muscle and motor models (MyoConverter)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Tool Integration Matrix](#2-tool-integration-matrix)
3. [The Ultimate Pipeline](#3-the-ultimate-pipeline)
4. [Updated Technology Stack](#4-updated-technology-stack)
5. [Critical Additions to Original Plan](#5-critical-additions-to-original-plan)
6. [Implementation Phases (Revised)](#6-implementation-phases-revised)
7. [Integration Strategies](#7-integration-strategies)
8. [Code Architecture](#8-code-architecture)
9. [Testing & Validation](#9-testing--validation)
10. [Success Metrics](#10-success-metrics)

---

## 1. Architecture Overview

### 1.1 The Robotics-Biomechanics Spectrum

```
ROBOTICS DOMAIN                 HYBRID ZONE              BIOMECHANICS DOMAIN
================================================================================
Joint Torques (τ)       ←→      Muscle-to-Torque      ←→  Muscle Forces (F)
Ideal Motors            ←→      Hill-Type Muscles     ←→  Cross-Bridge Dynamics
Rigid Body Dynamics     ←→      Musculoskeletal       ←→  Sarcomere Mechanics
Contact Forces          ←→      Ground Reaction       ←→  Metabolic Cost

TOOLS:                          TOOLS:                    TOOLS:
- Drake                         - MyoConverter            - OpenSim
- Pinocchio                     - MyoSuite                - MyoSim
- MuJoCo                        - CasADi (optimization)   - Pyomeca
```

### 1.2 Unified Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER (Kinematics)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Video (.mp4)] ──→ [OpenPose] ──→ [2D Keypoints]                     │
│                          ↓                                              │
│                    [Pyomeca] (Signal Processing)                        │
│                          ↓                                              │
│                    [BTK/C3D Reader] ←── [Motion Capture Data]          │
│                          ↓                                              │
│                 [CasADi + Pinocchio] (Inverse Kinematics)              │
│                          ↓                                              │
│                    [3D Joint Angles]                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      DYNAMICS LAYER (Simulation)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ROBOTICS PATH              HYBRID PATH              BIOMECHANICS PATH  │
│  ══════════════              ════════════            ═══════════════    │
│                                                                         │
│  [Pinocchio]                [MyoConverter]           [OpenSim]         │
│  • Inverse Dynamics         • OSIM → MJCF            • Muscle Forces   │
│  • Joint Torques (τ)        • Bridge Layer           • Moment Arms     │
│  • Fast (1000+ Hz)          ↓        ↑               • Metabolic Cost  │
│       ↓                     ↓        ↑                    ↓            │
│                                                                         │
│  [Drake]                    [MuJoCo + MyoSuite]      [MyoSim]          │
│  • Trajectory Opt           • Contact Dynamics       • Sarcomere       │
│  • Constraints              • Muscle Models          • Cross-Bridge    │
│  • Control                  • Fast Simulation        • Fatigue         │
│                                   ↓                                     │
│                                                                         │
│                         [CasADi Optimizer]                              │
│                         • Trajectory Optimization                       │
│                         • Optimal Control                               │
│                         • Parameter Fitting                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       ANALYSIS LAYER (Output)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Comparative Analysis] ──→ Compare Robotics vs Biomechanics           │
│  [Visualization]        ──→ Joint torques, Muscle forces, Kinematics   │
│  [Export]               ──→ C3D, CSV, JSON, HDF5                       │
│  [Reports]              ──→ Biomechanics reports, Optimization results  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tool Integration Matrix

| Tool | Primary Role | Outputs To | Inputs From | Priority |
|------|-------------|------------|-------------|----------|
| **OpenPose** | Vision → Keypoints | Pyomeca, CasADi | Video files | ⭐⭐⭐ High |
| **Pyomeca** | Signal Processing | OpenSim, CasADi | OpenPose, BTK | ⭐⭐⭐ High |
| **BTK** | C3D File Reading | Pyomeca, OpenSim | .c3d files | ⭐⭐ Medium |
| **CasADi** | Optimization | All engines | Pyomeca, Dynamics | ⭐⭐⭐ Critical |
| **Pinocchio** | Fast Dynamics | CasADi, Analysis | Joint angles | ✅ Existing |
| **Drake** | Control/Optimization | Analysis | Joint angles | ✅ Existing |
| **OpenSim** | Muscle Dynamics | MyoConverter, Analysis | Pyomeca, BTK | ⭐⭐⭐ High |
| **MyoSim** | Sarcomere Dynamics | OpenSim | OpenSim muscles | ⭐ Low |
| **MyoSuite** | MuJoCo Muscles | Analysis | Joint angles | ⭐⭐ Medium |
| **MyoConverter** | OSIM → MuJoCo | MuJoCo | OpenSim models | ⭐⭐⭐ Critical |
| **MuJoCo** | Contact Dynamics | Analysis | MyoConverter | ✅ Existing |

**Priority Key:**
- ⭐⭐⭐ Critical/High - Essential for complete pipeline
- ⭐⭐ Medium - Valuable enhancement
- ⭐ Low - Optional/Research-focused
- ✅ Existing - Already in suite

---

## 3. The Ultimate Pipeline

### 3.1 Complete Workflow

```python
"""
The Ultimate Golf Swing Analysis Pipeline
Combines Vision, Optimization, Robotics, and Biomechanics
"""

# ============================================================================
# STAGE 1: KINEMATICS ACQUISITION
# ============================================================================

# 1A. Vision-Based (OpenPose)
from shared.python.pose_estimation.openpose_estimator import OpenPoseEstimator

estimator = OpenPoseEstimator()
estimator.load_model()
keypoints_2d = estimator.estimate_from_video("swing.mp4")

# 1B. Motion Capture (BTK) - Alternative Input
from shared.python.data_io.btk_reader import C3DReader

c3d_reader = C3DReader()
markers_3d = c3d_reader.read("swing_vicon.c3d")

# ============================================================================
# STAGE 2: SIGNAL PROCESSING
# ============================================================================

from shared.python.signal_processing.pyomeca_processor import PyomecaProcessor

processor = PyomecaProcessor()

# Filter noisy keypoints
keypoints_filtered = processor.filter_butterworth(
    keypoints_2d,
    cutoff_freq=6.0,  # Hz
    order=4
)

# Normalize to swing cycle (0-100%)
swing_normalized = processor.normalize_cycle(
    keypoints_filtered,
    event_detection="club_parallel_to_ground"
)

# ============================================================================
# STAGE 3: INVERSE KINEMATICS (2D → 3D Joint Angles)
# ============================================================================

from shared.python.optimization.casadi_ik import CasADiInverseKinematics

ik_solver = CasADiInverseKinematics(
    model_path="models/golfer.osim",
    dynamics_engine="pinocchio"  # Fast derivatives
)

# Optimization-based IK (globally optimal)
joint_angles_3d = ik_solver.solve(
    keypoints_2d=keypoints_filtered,
    camera_params=camera_calibration,
    constraints={
        "joint_limits": True,
        "marker_weights": marker_confidence,
    }
)

# ============================================================================
# STAGE 4A: ROBOTICS ANALYSIS (Joint Torques)
# ============================================================================

from shared.python.engine_manager import EngineManager, EngineType

# 4A.1: Inverse Dynamics (Pinocchio - Fast)
manager = EngineManager()
manager.switch_engine(EngineType.PINOCCHIO)

joint_torques = manager.compute_inverse_dynamics(
    q=joint_angles_3d["positions"],
    dq=joint_angles_3d["velocities"],
    ddq=joint_angles_3d["accelerations"],
)

# 4A.2: Trajectory Optimization (Drake + CasADi)
from shared.python.optimization.trajectory_optimizer import TrajectoryOptimizer

optimizer = TrajectoryOptimizer(engine=EngineType.DRAKE)

optimal_swing = optimizer.solve(
    objective="maximize_club_head_speed",
    constraints={
        "joint_limits": True,
        "torque_limits": {"shoulder": 150.0, "elbow": 80.0},  # Nm
        "final_position": club_impact_pose,
    },
    initial_guess=joint_angles_3d,
)

# ============================================================================
# STAGE 4B: BIOMECHANICS ANALYSIS (Muscle Forces)
# ============================================================================

# 4B.1: OpenSim Muscle Analysis
manager.switch_engine(EngineType.OPENSIM)

opensim_results = manager.run_analysis(
    model="golfer_muscles.osim",
    joint_angles=joint_angles_3d,
    analysis_types=["InverseDynamics", "MuscleAnalysis", "StaticOptimization"]
)

muscle_forces = opensim_results["muscle_forces"]
moment_arms = opensim_results["moment_arms"]

# 4B.2: MyoSim Detailed Muscle Dynamics (Optional)
from engines.physics_engines.opensim.python.opensim_golf.myosim_bridge import (
    OpenSimMyoSimBridge
)

myosim_bridge = OpenSimMyoSimBridge(
    opensim_model=manager._opensim_model,
    myosim_config="myosim/golfer_muscles.yaml"
)

# Simulate with sarcomere-level detail
detailed_muscle_results = myosim_bridge.run_coupled_simulation(
    duration=2.0,
    muscle_activations=opensim_results["muscle_activations"],
    dt=0.001
)

# ============================================================================
# STAGE 4C: HYBRID ANALYSIS (Muscle-Driven MuJoCo via MyoConverter)
# ============================================================================

# Convert OpenSim muscle model to MuJoCo
from shared.python.model_conversion.myoconverter_bridge import MyoConverterBridge

converter = MyoConverterBridge()

mujoco_muscle_model = converter.convert_opensim_to_mujoco(
    osim_path="models/golfer_muscles.osim",
    output_path="models/golfer_muscles_mujoco.xml",
    preserve_muscles=True,
    preserve_geometry=True
)

# Run MuJoCo with muscle actuation + contact dynamics
manager.switch_engine(EngineType.MUJOCO)

mujoco_results = manager.run_forward_simulation(
    model=mujoco_muscle_model,
    muscle_controls=opensim_results["muscle_activations"],
    duration=2.0,
    include_contact=True,  # Club-ball-ground contact
)

# ============================================================================
# STAGE 5: COMPARATIVE ANALYSIS
# ============================================================================

from shared.python.comparative_analysis import MultiEngineComparison

comparison = MultiEngineComparison(
    results={
        "Pinocchio (Torques)": joint_torques,
        "OpenSim (Muscles)": muscle_forces,
        "MuJoCo (Hybrid)": mujoco_results,
        "Drake (Optimal)": optimal_swing,
    }
)

# Generate comparison report
comparison.plot_joint_trajectories()
comparison.plot_torque_vs_muscle_forces()
comparison.compute_correlation_matrix()
comparison.export_report("swing_analysis_report.pdf")

# ============================================================================
# STAGE 6: OPTIMIZATION & INSIGHTS
# ============================================================================

from shared.python.optimization.casadi_optimizer import CasADiOptimizer

# Find optimal muscle activation pattern
optimizer = CasADiOptimizer()

optimal_activations = optimizer.optimize(
    objective="minimize_effort",
    constraints={
        "club_head_speed_min": 45.0,  # m/s (100 mph)
        "joint_angles": joint_angle_limits,
        "muscle_forces_max": muscle_strength_limits,
    },
    dynamics_engine=EngineType.OPENSIM,
    solver="ipopt"
)

print(f"Optimal swing effort: {optimal_activations['objective_value']:.2f} J")
print(f"Club head speed: {optimal_activations['club_speed']:.1f} m/s")
```

---

## 4. Updated Technology Stack

### 4.1 Complete Tool List (Extended from Original Plan)

| Category | Tool | Status | Integration Priority |
|----------|------|--------|---------------------|
| **Input** | OpenPose | 🆕 New | ⭐⭐⭐ High |
| **Input** | BTK (C3D Reader) | 🆕 New | ⭐⭐ Medium |
| **Processing** | Pyomeca | 🆕 New | ⭐⭐⭐ High |
| **Optimization** | CasADi | 🆕 New | ⭐⭐⭐ **CRITICAL** |
| **Dynamics (Robotics)** | Pinocchio | ✅ Existing | Enhance |
| **Dynamics (Robotics)** | Drake | ✅ Existing | Enhance |
| **Dynamics (Robotics)** | MuJoCo | ✅ Existing | Enhance |
| **Dynamics (Bio)** | OpenSim | 🆕 New | ⭐⭐⭐ High |
| **Dynamics (Bio)** | MyoSim | 🆕 New | ⭐ Low |
| **Dynamics (Hybrid)** | MyoSuite | 🆕 New | ⭐⭐ Medium |
| **Bridge** | MyoConverter | 🆕 New | ⭐⭐⭐ **CRITICAL** |
| **Visualization** | Existing Suite | ✅ Existing | Extend |

### 4.2 Dependency Graph

```
OpenPose ──────┐
               ├──→ Pyomeca ──→ CasADi ──┬──→ Pinocchio ──→ Analysis
BTK ───────────┘                         │
                                         ├──→ Drake ──────→ Analysis
OpenSim ────────→ MyoConverter ──→ MuJoCo ──→ Analysis
                       ↑
                   MyoSuite
```

---

## 5. Critical Additions to Original Plan

### 5.1 CasADi Integration (HIGHEST PRIORITY)

**Why Critical:** Your original plan had **no optimization layer**. CasADi is the missing piece that enables:
- Trajectory optimization
- Inverse kinematics (globally optimal)
- Parameter identification
- Optimal control

**Architecture:**

```
shared/python/optimization/
├── __init__.py
├── casadi_optimizer.py           # Main CasADi wrapper
├── casadi_ik.py                   # Inverse kinematics solver
├── trajectory_optimizer.py        # Trajectory optimization
├── parameter_fitting.py           # System identification
└── optimal_control.py             # Optimal control problems
```

**Implementation:**

```python
# shared/python/optimization/casadi_optimizer.py

"""CasADi-based optimization for golf swing dynamics."""

import casadi as ca
import numpy as np
from pathlib import Path

from shared.python.common_utils import GolfModelingError, setup_logging
from shared.python.engine_manager import EngineManager, EngineType

logger = setup_logging(__name__)


class CasADiOptimizer:
    """CasADi optimization wrapper for golf swing analysis."""

    def __init__(self, dynamics_engine: EngineType = EngineType.PINOCCHIO):
        """Initialize optimizer.

        Args:
            dynamics_engine: Which physics engine to use for dynamics
        """
        self.engine_type = dynamics_engine
        self.engine_manager = EngineManager()

        # CasADi symbolic variables
        self.opti = ca.Opti()

        logger.info(f"Initialized CasADi optimizer with {dynamics_engine.value}")

    def setup_trajectory_optimization(
        self,
        n_timesteps: int,
        dt: float,
        n_joints: int,
        objective: str = "minimize_effort"
    ):
        """Set up trajectory optimization problem.

        Args:
            n_timesteps: Number of discretization points
            dt: Time step (seconds)
            n_joints: Number of joints
            objective: Objective function type
        """
        # Decision variables
        self.q = self.opti.variable(n_joints, n_timesteps)     # Positions
        self.dq = self.opti.variable(n_joints, n_timesteps)    # Velocities
        self.ddq = self.opti.variable(n_joints, n_timesteps)   # Accelerations
        self.tau = self.opti.variable(n_joints, n_timesteps)   # Torques

        # Dynamics constraints (using Pinocchio)
        if self.engine_type == EngineType.PINOCCHIO:
            self._setup_pinocchio_dynamics(dt)

        # Objective function
        if objective == "minimize_effort":
            # Minimize squared torques (energy)
            effort = ca.sum1(ca.sum2(self.tau**2))
            self.opti.minimize(effort)
        elif objective == "maximize_club_head_speed":
            # Maximize final velocity of club head
            # (This requires forward kinematics to club tip)
            club_speed = self._compute_club_head_speed(self.q[:, -1], self.dq[:, -1])
            self.opti.minimize(-club_speed)  # Negative for maximization

        logger.info(f"Set up trajectory optimization: {n_timesteps} steps, {dt}s timestep")

    def _setup_pinocchio_dynamics(self, dt: float):
        """Set up Pinocchio dynamics constraints."""
        # Get Pinocchio model derivatives
        # This is where CasADi + Pinocchio integration happens

        # For each timestep, enforce:
        # tau = M(q) * ddq + C(q, dq) + G(q)

        for k in range(self.q.shape[1]):
            # Get dynamics from Pinocchio
            # (This requires pinocchio with casadi support)
            M_k = self._mass_matrix(self.q[:, k])
            C_k = self._coriolis(self.q[:, k], self.dq[:, k])
            G_k = self._gravity(self.q[:, k])

            # Enforce dynamics constraint
            self.opti.subject_to(
                self.tau[:, k] == M_k @ self.ddq[:, k] + C_k + G_k
            )

            # Enforce integration constraints (Euler)
            if k < self.q.shape[1] - 1:
                self.opti.subject_to(
                    self.q[:, k+1] == self.q[:, k] + dt * self.dq[:, k]
                )
                self.opti.subject_to(
                    self.dq[:, k+1] == self.dq[:, k] + dt * self.ddq[:, k]
                )

    def add_joint_limits(self, q_min: np.ndarray, q_max: np.ndarray):
        """Add joint limit constraints."""
        for k in range(self.q.shape[1]):
            self.opti.subject_to(self.opti.bounded(q_min, self.q[:, k], q_max))

    def add_torque_limits(self, tau_max: np.ndarray):
        """Add torque limit constraints."""
        for k in range(self.tau.shape[1]):
            self.opti.subject_to(self.opti.bounded(-tau_max, self.tau[:, k], tau_max))

    def solve(self, initial_guess: dict | None = None) -> dict:
        """Solve optimization problem.

        Args:
            initial_guess: Optional initial guess for decision variables

        Returns:
            Dictionary with optimal solution
        """
        # Set initial guess if provided
        if initial_guess:
            self.opti.set_initial(self.q, initial_guess.get("q"))
            self.opti.set_initial(self.dq, initial_guess.get("dq"))

        # Solver options
        self.opti.solver("ipopt", {
            "ipopt.max_iter": 1000,
            "ipopt.print_level": 3,
        })

        # Solve
        try:
            sol = self.opti.solve()

            result = {
                "q": sol.value(self.q),
                "dq": sol.value(self.dq),
                "ddq": sol.value(self.ddq),
                "tau": sol.value(self.tau),
                "objective_value": sol.value(self.opti.f),
                "success": True,
            }

            logger.info(f"Optimization succeeded. Objective: {result['objective_value']:.2f}")
            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {"success": False, "error": str(e)}
```

### 5.2 Pyomeca Integration (Signal Processing)

**Why Critical:** OpenPose and C3D data are **noisy**. You need proper biomechanics signal processing.

**Architecture:**

```
shared/python/signal_processing/
├── __init__.py              # Existing
├── pyomeca_processor.py     # NEW: Biomechanics-specific processing
└── filters.py               # Existing filters
```

**Implementation:**

```python
# shared/python/signal_processing/pyomeca_processor.py

"""Biomechanics signal processing using Pyomeca."""

import numpy as np
import pyomeca

from shared.python.common_utils import setup_logging

logger = setup_logging(__name__)


class PyomecaProcessor:
    """Pyomeca-based signal processing for biomechanics data."""

    def __init__(self):
        """Initialize processor."""
        logger.info("Initialized Pyomeca processor")

    def filter_butterworth(
        self,
        data: np.ndarray,
        cutoff_freq: float,
        sampling_freq: float = 120.0,
        order: int = 4
    ) -> np.ndarray:
        """Apply Butterworth low-pass filter.

        Args:
            data: Input data (N_frames, N_markers, 3)
            cutoff_freq: Cutoff frequency (Hz)
            sampling_freq: Sampling frequency (Hz)
            order: Filter order

        Returns:
            Filtered data
        """
        # Convert to pyomeca DataArray
        data_xr = pyomeca.Markers(data)

        # Apply filter
        filtered = data_xr.meca.low_pass(
            freq=cutoff_freq,
            order=order,
            freq_sampling=sampling_freq
        )

        return filtered.values

    def normalize_cycle(
        self,
        data: np.ndarray,
        event_detection: str = "automatic"
    ) -> np.ndarray:
        """Normalize swing cycle to 0-100%.

        Args:
            data: Input trajectory data
            event_detection: Method for detecting swing start/end

        Returns:
            Normalized data (101 points, 0-100%)
        """
        # Detect swing events
        if event_detection == "automatic":
            swing_start, swing_end = self._detect_swing_events(data)
        elif event_detection == "club_parallel_to_ground":
            swing_start, swing_end = self._detect_club_parallel(data)

        # Extract swing cycle
        swing_data = data[swing_start:swing_end]

        # Interpolate to 101 points (0%, 1%, ..., 100%)
        normalized = pyomeca.Markers(swing_data).meca.time_normalize(
            n_frames=101
        )

        return normalized.values

    def _detect_swing_events(self, data: np.ndarray) -> tuple[int, int]:
        """Automatically detect swing start and end frames."""
        # Simple velocity-based detection
        # Start: First significant movement
        # End: Return to near-zero velocity

        velocity = np.linalg.norm(np.diff(data, axis=0), axis=-1)
        mean_velocity = np.mean(velocity, axis=-1)

        # Start: Velocity exceeds threshold
        threshold = 0.1 * np.max(mean_velocity)
        start_candidates = np.where(mean_velocity > threshold)[0]
        swing_start = start_candidates[0] if len(start_candidates) > 0 else 0

        # End: Peak velocity + return to low velocity
        peak_idx = np.argmax(mean_velocity)
        end_candidates = np.where(
            (np.arange(len(mean_velocity)) > peak_idx) &
            (mean_velocity < threshold)
        )[0]
        swing_end = end_candidates[0] if len(end_candidates) > 0 else len(data) - 1

        logger.info(f"Detected swing: frames {swing_start} to {swing_end}")
        return swing_start, swing_end
```

### 5.3 MyoConverter Integration (OpenSim ↔ MuJoCo Bridge)

**Why Critical:** This is the **key bridge** between biomechanics and robotics worlds.

**Architecture:**

```
shared/python/model_conversion/
├── __init__.py
├── myoconverter_bridge.py       # MyoConverter wrapper
├── osim_to_mjcf.py              # OpenSim → MuJoCo converter
└── urdf_tools.py                # Existing URDF utilities
```

**Implementation:**

```python
# shared/python/model_conversion/myoconverter_bridge.py

"""MyoConverter bridge for OpenSim to MuJoCo model conversion."""

import subprocess
from pathlib import Path

from shared.python.common_utils import GolfModelingError, setup_logging

logger = setup_logging(__name__)


class MyoConverterBridge:
    """Bridge for converting OpenSim models to MuJoCo format."""

    def __init__(self, myoconverter_path: Path | None = None):
        """Initialize MyoConverter bridge.

        Args:
            myoconverter_path: Path to MyoConverter executable
        """
        if myoconverter_path is None:
            # Try to find in PATH
            myoconverter_path = self._find_myoconverter()

        self.myoconverter_path = Path(myoconverter_path)

        if not self.myoconverter_path.exists():
            raise GolfModelingError(
                f"MyoConverter not found at {myoconverter_path}. "
                "Install from: https://github.com/MyoHub/myoconverter"
            )

        logger.info(f"Initialized MyoConverter: {self.myoconverter_path}")

    def convert_opensim_to_mujoco(
        self,
        osim_path: Path | str,
        output_path: Path | str,
        preserve_muscles: bool = True,
        preserve_geometry: bool = True,
        muscle_model: str = "hill"
    ) -> Path:
        """Convert OpenSim model to MuJoCo MJCF format.

        Args:
            osim_path: Path to .osim file
            output_path: Path for output .xml file
            preserve_muscles: Keep muscle definitions
            preserve_geometry: Keep visual geometry
            muscle_model: Muscle model type ("hill", "simple", "detailed")

        Returns:
            Path to generated MJCF file
        """
        osim_path = Path(osim_path)
        output_path = Path(output_path)

        if not osim_path.exists():
            raise GolfModelingError(f"OpenSim model not found: {osim_path}")

        # Build MyoConverter command
        cmd = [
            str(self.myoconverter_path),
            "--input", str(osim_path),
            "--output", str(output_path),
            "--format", "mjcf",
        ]

        if preserve_muscles:
            cmd.extend(["--muscles", muscle_model])

        if preserve_geometry:
            cmd.append("--geometry")

        # Run conversion
        logger.info(f"Converting {osim_path.name} to MuJoCo format...")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"Conversion successful: {output_path}")
            logger.debug(f"MyoConverter output: {result.stdout}")

            return output_path

        except subprocess.CalledProcessError as e:
            raise GolfModelingError(
                f"MyoConverter failed: {e.stderr}"
            ) from e

    def _find_myoconverter(self) -> Path:
        """Try to find MyoConverter in common locations."""
        search_paths = [
            Path.home() / "myoconverter" / "bin" / "myoconverter",
            Path("/usr/local/bin/myoconverter"),
            Path("/opt/myoconverter/bin/myoconverter"),
        ]

        for path in search_paths:
            if path.exists():
                return path

        raise GolfModelingError(
            "MyoConverter not found. Install from: "
            "https://github.com/MyoHub/myoconverter"
        )
```

### 5.4 BTK (Biomechanical ToolKit) Integration

**Why Needed:** Industry-standard motion capture data is in C3D format.

**Architecture:**

```
shared/python/data_io/
├── __init__.py
├── btk_reader.py               # NEW: C3D file reader
└── motion_capture.py           # Existing motion capture utilities
```

**Implementation:**

```python
# shared/python/data_io/btk_reader.py

"""Biomechanical ToolKit (BTK) wrapper for C3D file reading."""

import numpy as np
from pathlib import Path

from shared.python.common_utils import GolfModelingError, setup_logging

logger = setup_logging(__name__)


class C3DReader:
    """Read C3D motion capture files using BTK."""

    def __init__(self):
        """Initialize C3D reader."""
        try:
            import btk
            self.btk = btk
        except ImportError:
            raise GolfModelingError(
                "BTK not installed. Install with: pip install btk"
            )

        logger.info("Initialized BTK C3D reader")

    def read(self, c3d_path: Path | str) -> dict:
        """Read C3D file and extract markers and forces.

        Args:
            c3d_path: Path to .c3d file

        Returns:
            Dictionary with markers, forces, and metadata
        """
        c3d_path = Path(c3d_path)

        if not c3d_path.exists():
            raise GolfModelingError(f"C3D file not found: {c3d_path}")

        logger.info(f"Reading C3D file: {c3d_path}")

        # Read file
        reader = self.btk.btkAcquisitionFileReader()
        reader.SetFilename(str(c3d_path))
        reader.Update()

        acquisition = reader.GetOutput()

        # Extract markers
        markers = self._extract_markers(acquisition)

        # Extract forces (ground reaction forces)
        forces = self._extract_forces(acquisition)

        # Extract metadata
        metadata = self._extract_metadata(acquisition)

        return {
            "markers": markers,
            "forces": forces,
            "metadata": metadata,
            "file_path": c3d_path,
        }

    def _extract_markers(self, acquisition) -> dict:
        """Extract marker trajectories."""
        markers_dict = {}

        for i in range(acquisition.GetPointCount()):
            marker = acquisition.GetPoint(i)

            if marker.GetType() == self.btk.btkPoint.Marker:
                marker_name = marker.GetLabel()
                marker_data = marker.GetValues()  # (N_frames, 3)

                markers_dict[marker_name] = marker_data

        logger.info(f"Extracted {len(markers_dict)} markers")
        return markers_dict

    def _extract_forces(self, acquisition) -> dict:
        """Extract force plate data."""
        forces_dict = {}

        # BTK force extraction
        # (Implementation depends on force plate configuration)

        return forces_dict

    def _extract_metadata(self, acquisition) -> dict:
        """Extract file metadata."""
        metadata = {
            "sample_rate": acquisition.GetPointFrequency(),
            "n_frames": acquisition.GetPointFrameNumber(),
            "first_frame": acquisition.GetFirstFrame(),
            "last_frame": acquisition.GetLastFrame(),
            "units": acquisition.GetPointUnit(),
        }

        return metadata
```

---

## 6. Implementation Phases (Revised)

### Phase 1: Foundation & Optimization (Weeks 1-3) ⭐⭐⭐ CRITICAL

**Goal:** Establish optimization infrastructure and basic I/O

**Tasks:**
1. **CasADi Integration** (Week 1-2)
   - [ ] Install CasADi
   - [ ] Create `shared/python/optimization/casadi_optimizer.py`
   - [ ] Implement basic trajectory optimization
   - [ ] Test with Pinocchio derivatives
   - [ ] Example: Optimize simple 2-link arm swing

2. **Pyomeca Integration** (Week 1)
   - [ ] Install Pyomeca
   - [ ] Create `shared/python/signal_processing/pyomeca_processor.py`
   - [ ] Implement filtering and normalization
   - [ ] Test with synthetic marker data

3. **BTK Integration** (Week 2)
   - [ ] Install BTK
   - [ ] Create `shared/python/data_io/btk_reader.py`
   - [ ] Test with sample C3D files
   - [ ] Document C3D → Analysis pipeline

**Deliverables:**
- CasADi working with Pinocchio
- Pyomeca filtering pipeline operational
- C3D files readable
- Example optimization script

**Success Criteria:**
- Optimize 2-link arm in <5 seconds
- Filter noisy marker data
- Read standard C3D files

---

### Phase 2: Vision & Kinematics (Weeks 4-5) ⭐⭐⭐ HIGH VALUE

**Goal:** Video → 3D Joint Angles pipeline

**Tasks:**
1. **OpenPose Integration** (Week 4)
   - [ ] Install OpenPose
   - [ ] Create `shared/python/pose_estimation/openpose_estimator.py`
   - [ ] Test with sample golf videos
   - [ ] Validate keypoint detection

2. **CasADi Inverse Kinematics** (Week 5)
   - [ ] Create `shared/python/optimization/casadi_ik.py`
   - [ ] Implement optimization-based IK (2D → 3D)
   - [ ] Test with OpenPose data
   - [ ] Compare with OpenSim IK

**Deliverables:**
- Video → 2D keypoints working
- 2D → 3D joint angles working
- End-to-end: Video → Joint angles

**Success Criteria:**
- Process 120 FPS video in <2 minutes
- IK converges for >90% of frames
- Joint angles match ground truth (if available)

---

### Phase 3: Biomechanics Core (Weeks 6-9) ⭐⭐⭐ HIGH PRIORITY

**Goal:** OpenSim + MyoSim integration

**Tasks:**
1. **OpenSim Engine** (Week 6-8)
   - [ ] Follow original plan (see IMPLEMENTATION_PLAN_OPENSIM_MYOSIM_OPENPOSE.md)
   - [ ] Integrate with Pyomeca pipeline
   - [ ] Integrate with CasADi optimization

2. **MyoConverter Bridge** (Week 9)
   - [ ] Install MyoConverter
   - [ ] Create `shared/python/model_conversion/myoconverter_bridge.py`
   - [ ] Convert OpenSim golfer model to MuJoCo
   - [ ] Test muscle actuation in MuJoCo

**Deliverables:**
- OpenSim running inverse dynamics
- MyoConverter producing valid MuJoCo models
- Muscle-driven MuJoCo simulation

---

### Phase 4: Advanced Features (Weeks 10-12) ⭐⭐ MEDIUM PRIORITY

**Goal:** MyoSim, MyoSuite, and optimization enhancements

**Tasks:**
1. **MyoSim Integration** (Week 10)
   - [ ] Follow original MyoSim plan
   - [ ] Couple with OpenSim

2. **MyoSuite Exploration** (Week 11)
   - [ ] Install MyoSuite
   - [ ] Test MyoSuite environments
   - [ ] Integrate with existing MuJoCo setup

3. **Advanced Optimization** (Week 12)
   - [ ] Parameter identification (fit model to data)
   - [ ] Multi-objective optimization
   - [ ] Robust optimization (uncertainty)

---

### Phase 5: Integration & Validation (Weeks 13-14)

**Goal:** Complete pipeline integration and validation

**Tasks:**
1. **Full Pipeline Testing**
   - [ ] Video → Optimization → Biomechanics analysis
   - [ ] Cross-engine validation
   - [ ] Performance benchmarking

2. **Documentation**
   - [ ] Pipeline tutorials
   - [ ] API documentation
   - [ ] Example notebooks

3. **GUI Integration**
   - [ ] Add all new tools to launcher
   - [ ] Workflow presets (e.g., "Video to Muscle Analysis")

---

## 7. Integration Strategies

### 7.1 Pinocchio + CasADi Integration

**Challenge:** Get Pinocchio dynamics into CasADi symbolic form

**Solution:** Use `pinocchio.casadi` interface

```python
import pinocchio as pin
import pinocchio.casadi as cpin
import casadi as ca

# Load model with CasADi support
model = pin.buildModelFromUrdf("golfer.urdf")
cmodel = cpin.Model(model)

# Create CasADi function for dynamics
q_sym = ca.SX.sym("q", model.nq)
v_sym = ca.SX.sym("v", model.nv)
a_sym = ca.SX.sym("a", model.nv)

# Compute dynamics symbolically
data = cmodel.createData()
tau_sym = cpin.rnea(cmodel, data, q_sym, v_sym, a_sym)

# Create CasADi function
dynamics_fn = ca.Function(
    "dynamics",
    [q_sym, v_sym, a_sym],
    [tau_sym],
    ["q", "v", "a"],
    ["tau"]
)

# Use in optimization
opti = ca.Opti()
q = opti.variable(model.nq, N)
# ... etc
```

### 7.2 OpenSim + MuJoCo via MyoConverter

**Workflow:**

```
1. Design in OpenSim GUI
   ↓
2. Export: golfer.osim
   ↓
3. MyoConverter: .osim → .xml
   ↓
4. Load in MuJoCo with muscles
   ↓
5. Simulate with muscle controls
```

### 7.3 OpenPose + Pyomeca + CasADi IK

**Pipeline:**

```python
# 1. Extract keypoints
openpose_results = openpose.estimate_from_video("swing.mp4")

# 2. Filter noise
processor = PyomecaProcessor()
filtered_keypoints = processor.filter_butterworth(
    openpose_results,
    cutoff_freq=6.0
)

# 3. Optimization-based IK
ik_solver = CasADiInverseKinematics(model="golfer.osim")
joint_angles = ik_solver.solve(
    keypoints_2d=filtered_keypoints,
    camera_params=camera_calibration
)

# 4. Use joint angles in any engine
manager.switch_engine(EngineType.OPENSIM)
muscle_forces = manager.compute_inverse_dynamics(joint_angles)
```

---

## 8. Code Architecture

### 8.1 Updated Directory Structure

```
Golf_Modeling_Suite/
├── shared/python/
│   ├── optimization/              # NEW: CasADi integration
│   │   ├── __init__.py
│   │   ├── casadi_optimizer.py
│   │   ├── casadi_ik.py
│   │   ├── trajectory_optimizer.py
│   │   └── parameter_fitting.py
│   ├── signal_processing/
│   │   ├── pyomeca_processor.py   # NEW: Biomechanics processing
│   │   └── filters.py             # Existing
│   ├── data_io/                   # NEW: Data I/O
│   │   ├── btk_reader.py
│   │   └── motion_capture.py
│   ├── model_conversion/          # NEW: Model conversion
│   │   ├── myoconverter_bridge.py
│   │   └── osim_to_mjcf.py
│   └── pose_estimation/
│       ├── openpose_estimator.py  # From original plan
│       └── interface.py
│
├── engines/physics_engines/
│   ├── opensim/                   # From original plan
│   ├── myosuite/                  # NEW: MyoSuite integration
│   │   ├── environments/
│   │   └── python/
│   └── ... (existing engines)
│
└── examples/
    ├── optimization/               # NEW: Optimization examples
    │   ├── 01_simple_trajectory_opt.py
    │   ├── 02_inverse_kinematics.py
    │   └── 03_parameter_identification.py
    └── pipelines/                  # NEW: Full pipeline examples
        ├── video_to_muscle_analysis.py
        └── optimize_swing_technique.py
```

### 8.2 Dependencies Update

```toml
# pyproject.toml

[project.optional-dependencies]

# Optimization (CRITICAL NEW ADDITION)
optimization = [
    "casadi>=3.6.0",          # Optimization framework
]

# Biomechanics I/O
bio-io = [
    "pyomeca>=1.0.0",         # Biomechanics signal processing
    "btk>=0.4.0",             # C3D file reading
]

# Model conversion
conversion = [
    # MyoConverter installed separately (C++ tool)
]

# OpenSim (from original plan)
opensim = [
    "opensim>=4.4.0,<5.0.0",
    "myosim>=1.0.0",
]

# MyoSuite (alternative to MyoSim)
myosuite = [
    "myosuite>=2.0.0",        # MuJoCo-based musculoskeletal RL
]

# Pose estimation (from original plan)
pose = [
    "opencv-python>=4.8.0",
    # OpenPose installed separately
]

# Complete stack
all-new = [
    "golf-modeling-suite[optimization,bio-io,opensim,myosuite,pose]"
]
```

---

## 9. Testing & Validation

### 9.1 Integration Test: Full Pipeline

```python
# tests/integration/test_full_pipeline.py

import pytest
from pathlib import Path

def test_video_to_muscle_analysis_pipeline():
    """Test complete pipeline: Video → Muscles."""

    # Stage 1: OpenPose
    from shared.python.pose_estimation.openpose_estimator import OpenPoseEstimator

    estimator = OpenPoseEstimator()
    estimator.load_model()

    keypoints = estimator.estimate_from_video(
        Path("tests/data/sample_swing.mp4")
    )

    assert len(keypoints) > 0

    # Stage 2: Pyomeca filtering
    from shared.python.signal_processing.pyomeca_processor import PyomecaProcessor

    processor = PyomecaProcessor()
    filtered = processor.filter_butterworth(keypoints, cutoff_freq=6.0)

    # Stage 3: CasADi IK
    from shared.python.optimization.casadi_ik import CasADiInverseKinematics

    ik = CasADiInverseKinematics(model="golfer.osim")
    joint_angles = ik.solve(keypoints_2d=filtered)

    assert joint_angles["success"]

    # Stage 4: OpenSim muscle analysis
    from shared.python.engine_manager import EngineManager, EngineType

    manager = EngineManager()
    manager.switch_engine(EngineType.OPENSIM)

    muscle_results = manager.run_analysis(
        model="golfer_muscles.osim",
        joint_angles=joint_angles["q"]
    )

    assert "muscle_forces" in muscle_results
    assert len(muscle_results["muscle_forces"]) > 0

    print("✅ Full pipeline test passed!")
```

### 9.2 Validation: CasADi Optimization

```python
# tests/validation/test_casadi_optimization.py

def test_trajectory_optimization_converges():
    """Test that trajectory optimization finds a solution."""

    from shared.python.optimization.trajectory_optimizer import TrajectoryOptimizer
    from shared.python.engine_manager import EngineType

    optimizer = TrajectoryOptimizer(engine=EngineType.PINOCCHIO)

    result = optimizer.solve(
        objective="minimize_effort",
        n_timesteps=50,
        duration=1.0,
        constraints={
            "joint_limits": True,
            "final_position": target_pose,
        }
    )

    assert result["success"]
    assert result["objective_value"] < 1000.0  # Reasonable effort

def test_ik_matches_opensim():
    """Validate CasADi IK against OpenSim IK."""

    # Run CasADi IK
    casadi_ik = CasADiInverseKinematics(model="golfer.osim")
    casadi_result = casadi_ik.solve(markers=test_markers)

    # Run OpenSim IK
    opensim_ik = OpenSimIKTool()
    opensim_result = opensim_ik.run(markers=test_markers)

    # Compare joint angles
    diff = np.abs(casadi_result["q"] - opensim_result["q"])
    assert np.max(diff) < 0.05  # <3 degrees difference
```

---

## 10. Success Metrics

### 10.1 Functional Success Criteria

- [ ] **Pipeline Completeness:** Video → Keypoints → IK → Dynamics → Analysis
- [ ] **Optimization Speed:** Trajectory optimization <10 seconds for 2-second swing
- [ ] **IK Accuracy:** <5° difference from OpenSim IK
- [ ] **Model Conversion:** OpenSim → MuJoCo preserves muscle geometry
- [ ] **Cross-Engine Agreement:** Joint torques agree within 10% across engines

### 10.2 Quality Metrics

- [ ] **Test Coverage:** >70% for new modules
- [ ] **Performance:** Real-time or faster for forward simulation
- [ ] **Documentation:** Complete API docs for all new modules
- [ ] **Examples:** 10+ working examples covering all pipelines

### 10.3 Research Impact Metrics

- [ ] **Novelty:** Bridges robotics and biomechanics (unique contribution)
- [ ] **Usability:** Researchers can run full pipeline in <10 lines of code
- [ ] **Extensibility:** Easy to add new optimization objectives
- [ ] **Validation:** Results match published literature

---

## Appendix A: Recommended Reading Order for Implementation

1. **Start Here:** CasADi documentation (optimization fundamentals)
2. **Then:** Pinocchio + CasADi integration examples
3. **Then:** OpenPose setup and Python API
4. **Then:** Pyomeca biomechanics processing
5. **Then:** MyoConverter documentation
6. **Finally:** Full pipeline integration

---

## Appendix B: External Resources

- **CasADi:** https://web.casadi.org/
- **Pyomeca:** https://pyomeca.github.io/
- **BTK:** https://biomechanical-toolkit.github.io/
- **MyoConverter:** https://github.com/MyoHub/myoconverter
- **MyoSuite:** https://sites.google.com/view/myosuite
- **OpenPose:** https://github.com/CMU-Perceptual-Computing-Lab/openpose

---

**End of Comprehensive Stack Plan**

This plan incorporates all recommended tools and creates a unified Biomechanics-Robotics pipeline for state-of-the-art golf swing analysis.
