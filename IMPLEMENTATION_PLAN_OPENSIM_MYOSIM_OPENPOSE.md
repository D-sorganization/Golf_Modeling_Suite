# Implementation Plan: OpenSim, MyoSim, and OpenPose Integration

**Created:** 2025-12-27
**Author:** Golf Modeling Suite Architecture Team
**Status:** Planning Phase

---

## Executive Summary

This document outlines the implementation strategy for integrating three new components into the Golf Modeling Suite:

1. **OpenSim** - Musculoskeletal modeling engine for biomechanical analysis
2. **MyoSim** - Muscle simulation framework (integrates with OpenSim)
3. **OpenPose** - Pose estimation module for motion capture

**Architecture Decision:** Following the existing multi-engine pattern with shared utilities and standardized interfaces.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [OpenSim Engine Implementation](#2-opensim-engine-implementation)
3. [MyoSim Integration](#3-myosim-integration)
4. [OpenPose Module Implementation](#4-openpose-module-implementation)
5. [Integration with Existing Systems](#5-integration-with-existing-systems)
6. [Implementation Phases](#6-implementation-phases)
7. [Testing Strategy](#7-testing-strategy)
8. [Documentation Requirements](#8-documentation-requirements)

---

## 1. Current Architecture Analysis

### 1.1 Existing Engine Pattern

The Golf Modeling Suite uses a **multi-engine architecture** with:

```
engines/physics_engines/
├── mujoco/          # High-fidelity biomechanics
├── drake/           # Control-theoretic optimization
├── pinocchio/       # Ultra-fast rigid body dynamics
└── [NEW] opensim/   # Musculoskeletal modeling
```

**Key Components:**
- `shared/python/engine_manager.py` - Unified engine management
- `shared/python/engine_probes.py` - Engine readiness checking
- `config/models.yaml` - Model registry

### 1.2 Existing Pose Estimation Interface

**Location:** `shared/python/pose_estimation/interface.py`

**Abstract Interface:**
```python
class PoseEstimator(ABC):
    def load_model(self, model_path: Path | None = None) -> None
    def estimate_from_image(self, image: np.ndarray) -> PoseEstimationResult
    def estimate_from_video(self, video_path: Path) -> list[PoseEstimationResult]
```

**Standardized Output:**
```python
@dataclass
class PoseEstimationResult:
    joint_angles: dict[str, float]  # Joint name -> angle (radians)
    confidence: float                # 0.0 to 1.0
    timestamp: float
    raw_keypoints: dict[str, np.ndarray] | None
```

### 1.3 Motion Capture Integration Points

The suite already has motion capture functionality in MuJoCo:
- `engines/physics_engines/mujoco/python/mujoco_humanoid_golf/motion_capture.py`
- `examples_motion_capture.py`

OpenPose will **complement** this by providing vision-based pose estimation.

---

## 2. OpenSim Engine Implementation

### 2.1 Overview

**OpenSim** is an open-source platform for musculoskeletal modeling, simulation, and analysis.

**Key Features:**
- Muscle-driven simulations
- Inverse kinematics and inverse dynamics
- Forward dynamics with muscle actuation
- Contact modeling
- Integration with experimental data

**Why Add OpenSim:**
- Industry-standard in biomechanics research
- Extensive validated muscle models
- Interoperability with C3D motion capture data
- Complementary to MuJoCo (different solver, muscle models)

### 2.2 Directory Structure

```
engines/physics_engines/opensim/
├── README.md                          # OpenSim-specific documentation
├── python/
│   ├── __init__.py
│   ├── opensim_golf/                  # Main package
│   │   ├── __init__.py
│   │   ├── __main__.py                # CLI entry point
│   │   ├── core.py                    # Core OpenSim wrapper
│   │   ├── model_builder.py           # Build golf swing models
│   │   ├── muscle_controller.py       # Muscle activation control
│   │   ├── inverse_kinematics.py      # IK solver
│   │   ├── inverse_dynamics.py        # ID solver
│   │   ├── forward_dynamics.py        # Forward simulation
│   │   ├── data_import.py             # C3D, TRC, MOT file readers
│   │   ├── visualization.py           # OpenSim visualizer integration
│   │   ├── gui.py                     # PyQt6 GUI (following existing pattern)
│   │   └── myosim_bridge.py           # MyoSim integration (see Section 3)
│   ├── src/
│   │   └── logger_utils.py            # Logging (will use shared after consolidation)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_opensim_core.py
│   │   ├── test_model_builder.py
│   │   ├── test_ik.py
│   │   ├── test_id.py
│   │   └── test_myosim_integration.py
│   └── examples/
│       ├── basic_ik.py
│       ├── muscle_driven_swing.py
│       └── compare_with_mujoco.py
├── models/                            # OpenSim model files
│   ├── golfer_basic.osim              # Basic rigid body model
│   ├── golfer_muscles.osim            # Full musculoskeletal model
│   ├── golfer_detailed.osim           # High-detail anatomical model
│   └── geometry/                      # Mesh files for visualization
│       ├── pelvis.vtp
│       ├── femur_r.vtp
│       └── ...
├── myosim/                            # MyoSim integration (see Section 3)
│   └── muscle_models/
│       ├── simple_hill.xml
│       ├── detailed_hill.xml
│       └── multi_scale.xml
└── docs/
    ├── getting_started.md
    ├── model_development.md
    └── api_reference.md
```

### 2.3 Engine Manager Integration

**Step 1: Update `EngineType` Enum**

```python
# shared/python/engine_manager.py

class EngineType(Enum):
    """Available physics engine types."""
    MUJOCO = "mujoco"
    DRAKE = "drake"
    PINOCCHIO = "pinocchio"
    MATLAB_2D = "matlab_2d"
    MATLAB_3D = "matlab_3d"
    PENDULUM = "pendulum"
    OPENSIM = "opensim"          # NEW
```

**Step 2: Add Engine Path**

```python
# shared/python/engine_manager.py

self.engine_paths = {
    # ... existing paths ...
    EngineType.OPENSIM: (self.engines_root / "physics_engines" / "opensim"),
}
```

**Step 3: Add Loader Method**

```python
# shared/python/engine_manager.py

def _load_opensim_engine(self) -> None:
    """Load OpenSim engine with full initialization."""
    try:
        # 1. Run probe
        from .engine_probes import OpenSimProbe

        probe = OpenSimProbe(self.suite_root)
        result = probe.probe()

        if not result.is_available():
            raise GolfModelingError(
                f"OpenSim not ready:\n{result.diagnostic_message}\n"
                f"Fix: {result.get_fix_instructions()}"
            )

        # 2. Import OpenSim
        import opensim

        logger.info(f"OpenSim version {opensim.GetVersion()} imported")

        # 3. Verify model directory
        model_dir = self.engine_paths[EngineType.OPENSIM] / "models"
        if not model_dir.exists():
            raise GolfModelingError(
                f"OpenSim model directory not found: {model_dir}"
            )

        # 4. Find and validate at least one model file
        model_files = list(model_dir.glob("*.osim"))
        if not model_files:
            raise GolfModelingError(
                f"No OpenSim model files (.osim) found in {model_dir}"
            )

        logger.info(f"Found {len(model_files)} OpenSim models in {model_dir}")

        # 5. Test load a model
        test_model = model_files[0]
        try:
            _ = opensim.Model(str(test_model))
            logger.info(
                f"Successfully validated OpenSim with test model: {test_model.name}"
            )
        except Exception as e:
            raise GolfModelingError(
                f"OpenSim model validation failed for {test_model.name}: {e}"
            ) from e

        # 6. Store loaded state
        self._opensim_module = opensim
        self._opensim_model_dir = model_dir

        logger.info("OpenSim engine fully loaded and validated")

    except ImportError as e:
        raise GolfModelingError(
            "OpenSim not installed. Install with: conda install -c opensim-org opensim"
        ) from e
```

**Step 4: Update `_load_engine()` dispatcher**

```python
# shared/python/engine_manager.py

def _load_engine(self, engine_type: EngineType) -> None:
    # ... existing code ...

    if engine_type == EngineType.MUJOCO:
        self._load_mujoco_engine()
    elif engine_type == EngineType.DRAKE:
        self._load_drake_engine()
    elif engine_type == EngineType.PINOCCHIO:
        self._load_pinocchio_engine()
    elif engine_type in [EngineType.MATLAB_2D, EngineType.MATLAB_3D]:
        self._load_matlab_engine(engine_type)
    elif engine_type == EngineType.PENDULUM:
        self._load_pendulum_engine()
    elif engine_type == EngineType.OPENSIM:       # NEW
        self._load_opensim_engine()                # NEW
```

### 2.4 Engine Probe Implementation

**Create:** `shared/python/engine_probes.py` (add new class)

```python
class OpenSimProbe(EngineProbe):
    """Probe for OpenSim musculoskeletal modeling engine."""

    def __init__(self, suite_root: Path) -> None:
        """Initialize OpenSim probe."""
        super().__init__("OpenSim", suite_root)

    def probe(self) -> EngineProbeResult:
        """Check OpenSim readiness."""
        missing = []

        # Check for opensim package
        try:
            import opensim
            version = opensim.GetVersion()
        except ImportError:
            return EngineProbeResult(
                engine_name=self.engine_name,
                status=ProbeStatus.NOT_INSTALLED,
                version=None,
                missing_dependencies=["opensim"],
                diagnostic_message="OpenSim Python package not installed. "
                                 "Install with: conda install -c opensim-org opensim",
            )
        except Exception as e:
            return EngineProbeResult(
                engine_name=self.engine_name,
                status=ProbeStatus.MISSING_BINARY,
                version=None,
                missing_dependencies=["OpenSim libraries"],
                diagnostic_message=f"OpenSim import error: {e}. "
                                 "Binaries may be missing or incompatible.",
            )

        # Check for engine directory
        engine_dir = self.suite_root / "engines" / "physics_engines" / "opensim"
        if not engine_dir.exists():
            missing.append("engine directory")

        # Check for Python modules
        python_dir = engine_dir / "python"
        if python_dir.exists():
            key_modules = ["opensim_golf"]
            for module in key_modules:
                if not (python_dir / module).exists():
                    missing.append(f"module: {module}")
        else:
            missing.append("python directory")

        # Check for models
        models_dir = engine_dir / "models"
        if models_dir.exists():
            models = list(models_dir.glob("**/*.osim"))
            if not models:
                missing.append("OpenSim model files (.osim)")
        else:
            missing.append("models directory")

        if missing:
            return EngineProbeResult(
                engine_name=self.engine_name,
                status=ProbeStatus.MISSING_ASSETS,
                version=version,
                missing_dependencies=missing,
                diagnostic_message=f"OpenSim {version} installed but missing: "
                                 f"{', '.join(missing)}",
            )

        return EngineProbeResult(
            engine_name=self.engine_name,
            status=ProbeStatus.AVAILABLE,
            version=version,
            missing_dependencies=[],
            diagnostic_message=f"OpenSim {version} ready",
            details={
                "engine_dir": str(engine_dir),
                "models_dir": str(models_dir),
            },
        )
```

### 2.5 Model Registry Updates

**Update:** `config/models.yaml`

```yaml
# Add OpenSim models
  - id: opensim_basic
    name: "OpenSim Basic Golfer"
    description: "Basic rigid body golf model in OpenSim."
    type: "opensim"
    path: "engines/physics_engines/opensim/models/golfer_basic.osim"

  - id: opensim_muscles
    name: "OpenSim Muscle Golfer"
    description: "Full musculoskeletal model with Hill-type muscles."
    type: "opensim"
    path: "engines/physics_engines/opensim/models/golfer_muscles.osim"

  - id: opensim_myosim
    name: "OpenSim + MyoSim Golfer"
    description: "Advanced multi-scale muscle model using MyoSim integration."
    type: "opensim"
    path: "engines/physics_engines/opensim/models/golfer_myosim.osim"
```

### 2.6 Core OpenSim Wrapper

**Create:** `engines/physics_engines/opensim/python/opensim_golf/core.py`

```python
"""Core OpenSim wrapper for Golf Modeling Suite."""

from pathlib import Path
from typing import Any

import numpy as np
import opensim

from shared.python.common_utils import GolfModelingError, setup_logging

logger = setup_logging(__name__)


class OpenSimGolfModel:
    """Wrapper for OpenSim golf swing models."""

    def __init__(self, model_path: Path | str):
        """Initialize OpenSim model.

        Args:
            model_path: Path to .osim model file
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise GolfModelingError(f"Model file not found: {model_path}")

        logger.info(f"Loading OpenSim model: {self.model_path}")
        self.model = opensim.Model(str(self.model_path))
        self.state = self.model.initSystem()

        # Extract model info
        self.n_coords = self.model.getNumCoordinates()
        self.n_muscles = self.model.getNumMuscles() if self.has_muscles() else 0

        logger.info(
            f"Model loaded: {self.n_coords} coordinates, "
            f"{self.n_muscles} muscles"
        )

    def has_muscles(self) -> bool:
        """Check if model has muscles."""
        return self.model.getMuscles().getSize() > 0

    def get_coordinate_names(self) -> list[str]:
        """Get list of coordinate (joint) names."""
        coords = []
        for i in range(self.n_coords):
            coord = self.model.getCoordinateSet().get(i)
            coords.append(coord.getName())
        return coords

    def get_muscle_names(self) -> list[str]:
        """Get list of muscle names."""
        if not self.has_muscles():
            return []

        muscles = []
        for i in range(self.n_muscles):
            muscle = self.model.getMuscles().get(i)
            muscles.append(muscle.getName())
        return muscles

    def set_pose(self, joint_angles: dict[str, float]) -> None:
        """Set model pose from joint angles.

        Args:
            joint_angles: Dictionary mapping coordinate names to values (radians)
        """
        for coord_name, angle in joint_angles.items():
            try:
                coord = self.model.getCoordinateSet().get(coord_name)
                coord.setValue(self.state, angle)
            except Exception as e:
                logger.warning(f"Could not set {coord_name}: {e}")

        self.model.realizePosition(self.state)

    def get_pose(self) -> dict[str, float]:
        """Get current model pose.

        Returns:
            Dictionary mapping coordinate names to values (radians)
        """
        pose = {}
        for i in range(self.n_coords):
            coord = self.model.getCoordinateSet().get(i)
            pose[coord.getName()] = coord.getValue(self.state)
        return pose

    def compute_inverse_kinematics(
        self,
        marker_data: dict[str, np.ndarray],
        time_range: tuple[float, float] | None = None
    ) -> dict[str, np.ndarray]:
        """Solve inverse kinematics from marker trajectories.

        Args:
            marker_data: Dictionary mapping marker names to positions (N, 3)
            time_range: Optional (start_time, end_time) tuple

        Returns:
            Dictionary mapping coordinate names to trajectories
        """
        # Implementation will use OpenSim's InverseKinematicsTool
        # This is a placeholder for the structure
        raise NotImplementedError("IK implementation in inverse_kinematics.py")

    def compute_inverse_dynamics(
        self,
        joint_angles: dict[str, np.ndarray],
        external_forces: dict[str, np.ndarray] | None = None
    ) -> dict[str, np.ndarray]:
        """Solve inverse dynamics to compute joint torques.

        Args:
            joint_angles: Joint angle trajectories
            external_forces: Optional external force data

        Returns:
            Dictionary mapping coordinate names to torque trajectories
        """
        # Implementation will use OpenSim's InverseDynamicsTool
        raise NotImplementedError("ID implementation in inverse_dynamics.py")

    def simulate_forward_dynamics(
        self,
        duration: float,
        muscle_controls: dict[str, np.ndarray] | None = None,
        timestep: float = 0.001
    ) -> dict[str, Any]:
        """Run forward dynamics simulation.

        Args:
            duration: Simulation duration (seconds)
            muscle_controls: Optional muscle activation controls
            timestep: Integration timestep

        Returns:
            Dictionary with simulation results (states, forces, etc.)
        """
        # Implementation will use OpenSim's Manager
        raise NotImplementedError("Forward dynamics in forward_dynamics.py")
```

---

## 3. MyoSim Integration

### 3.1 Overview

**MyoSim** is a library for multi-scale muscle simulation with spatially-explicit representation of sarcomeres.

**Integration Strategy:**
MyoSim should be **integrated with OpenSim** rather than a standalone engine, because:
- MyoSim provides muscle models that replace OpenSim's default Hill models
- OpenSim handles skeleton kinematics and dynamics
- MyoSim handles detailed muscle fiber dynamics

### 3.2 Architecture Decision

**Option 1: MyoSim as OpenSim Component** ✅ **RECOMMENDED**
```
engines/physics_engines/opensim/
├── python/opensim_golf/
│   └── myosim_bridge.py        # Bridge to MyoSim
└── myosim/
    ├── muscle_models/          # MyoSim muscle definitions
    └── configurations/         # Muscle arrangement configs
```

**Option 2: MyoSim as Separate Engine** ❌ Not Recommended
- Unnecessary duplication
- MyoSim requires skeletal model (OpenSim provides this)
- Complicates workflow

### 3.3 MyoSim Bridge Implementation

**Create:** `engines/physics_engines/opensim/python/opensim_golf/myosim_bridge.py`

```python
"""Bridge between OpenSim and MyoSim for multi-scale muscle simulation."""

from pathlib import Path
from typing import Any

import numpy as np

from shared.python.common_utils import GolfModelingError, setup_logging

logger = setup_logging(__name__)


class MyoSimMuscle:
    """Wrapper for a single MyoSim muscle."""

    def __init__(self, muscle_def_path: Path):
        """Initialize MyoSim muscle from definition file.

        Args:
            muscle_def_path: Path to MyoSim muscle XML definition
        """
        self.muscle_def_path = muscle_def_path

        try:
            import myosim
            self.myosim = myosim
        except ImportError:
            raise GolfModelingError(
                "MyoSim not installed. Install with: pip install myosim"
            )

        # Load muscle model
        self.muscle = self.myosim.Muscle(str(muscle_def_path))
        logger.info(f"Loaded MyoSim muscle from {muscle_def_path}")

    def compute_force(
        self,
        length: float,
        velocity: float,
        activation: float,
        dt: float
    ) -> tuple[float, dict[str, Any]]:
        """Compute muscle force for given kinematics and activation.

        Args:
            length: Muscle length (m)
            velocity: Muscle lengthening velocity (m/s)
            activation: Neural activation (0-1)
            dt: Time step (s)

        Returns:
            Tuple of (force, state_dict)
        """
        # MyoSim-specific force calculation
        # Returns force and internal state (sarcomere lengths, etc.)
        force, state = self.muscle.calculate_force(
            length, velocity, activation, dt
        )
        return force, state


class OpenSimMyoSimBridge:
    """Bridge connecting OpenSim model with MyoSim muscles."""

    def __init__(self, opensim_model, myosim_config_path: Path):
        """Initialize bridge.

        Args:
            opensim_model: OpenSimGolfModel instance
            myosim_config_path: Path to MyoSim muscle configuration
        """
        self.opensim_model = opensim_model
        self.myosim_config_path = myosim_config_path

        # Load muscle mappings
        self.muscle_map = self._load_muscle_mappings()

        # Initialize MyoSim muscles
        self.myosim_muscles: dict[str, MyoSimMuscle] = {}
        self._initialize_myosim_muscles()

        logger.info(
            f"Initialized {len(self.myosim_muscles)} MyoSim muscles"
        )

    def _load_muscle_mappings(self) -> dict[str, dict[str, Any]]:
        """Load mapping from OpenSim muscles to MyoSim models."""
        import yaml

        with open(self.myosim_config_path) as f:
            config = yaml.safe_load(f)

        return config.get("muscle_mappings", {})

    def _initialize_myosim_muscles(self) -> None:
        """Initialize MyoSim muscle objects."""
        myosim_dir = self.myosim_config_path.parent / "muscle_models"

        for muscle_name, mapping in self.muscle_map.items():
            model_file = mapping.get("myosim_model")
            if model_file:
                model_path = myosim_dir / model_file
                self.myosim_muscles[muscle_name] = MyoSimMuscle(model_path)

    def compute_muscle_forces(
        self,
        muscle_lengths: dict[str, float],
        muscle_velocities: dict[str, float],
        activations: dict[str, float],
        dt: float
    ) -> dict[str, float]:
        """Compute forces for all MyoSim muscles.

        Args:
            muscle_lengths: Muscle lengths from OpenSim
            muscle_velocities: Muscle velocities from OpenSim
            activations: Neural activations (0-1)
            dt: Timestep

        Returns:
            Dictionary mapping muscle names to forces
        """
        forces = {}

        for muscle_name, myosim_muscle in self.myosim_muscles.items():
            length = muscle_lengths.get(muscle_name, 0.0)
            velocity = muscle_velocities.get(muscle_name, 0.0)
            activation = activations.get(muscle_name, 0.0)

            force, _ = myosim_muscle.compute_force(
                length, velocity, activation, dt
            )
            forces[muscle_name] = force

        return forces

    def run_coupled_simulation(
        self,
        duration: float,
        muscle_controls: dict[str, np.ndarray],
        dt: float = 0.001
    ) -> dict[str, Any]:
        """Run coupled OpenSim-MyoSim simulation.

        Args:
            duration: Simulation duration (s)
            muscle_controls: Muscle activation signals
            dt: Timestep (s)

        Returns:
            Simulation results with detailed muscle states
        """
        # Coupled simulation loop:
        # 1. OpenSim computes kinematics
        # 2. Extract muscle lengths/velocities
        # 3. MyoSim computes detailed muscle forces
        # 4. Apply forces back to OpenSim
        # 5. Integrate OpenSim dynamics

        # This is the main integration point
        raise NotImplementedError("Coupled simulation implementation")
```

### 3.4 MyoSim Configuration Example

**Create:** `engines/physics_engines/opensim/myosim/configurations/golfer_muscles.yaml`

```yaml
# MyoSim muscle configuration for golf swing model

muscle_mappings:
  # Upper body muscles
  pectoralis_major:
    opensim_muscle: "pect_maj_r"
    myosim_model: "detailed_hill.xml"
    parameters:
      max_force: 750.0  # N
      optimal_length: 0.15  # m

  latissimus_dorsi:
    opensim_muscle: "lat_dorsi_r"
    myosim_model: "detailed_hill.xml"
    parameters:
      max_force: 850.0
      optimal_length: 0.28

  deltoid_anterior:
    opensim_muscle: "delt_ant_r"
    myosim_model: "simple_hill.xml"
    parameters:
      max_force: 380.0
      optimal_length: 0.11

  # Add more muscles as needed...
```

### 3.5 Dependencies

**Add to `pyproject.toml`:**

```toml
[project.optional-dependencies]
opensim = [
    "opensim>=4.4.0,<5.0.0",
    "myosim>=1.0.0",  # If available on PyPI
]
```

---

## 4. OpenPose Module Implementation

### 4.1 Overview

**OpenPose** is a real-time multi-person keypoint detection library for body, face, hands, and foot pose estimation.

**Integration Point:** Implements the existing `PoseEstimator` interface in `shared/python/pose_estimation/`

### 4.2 Directory Structure

```
shared/python/pose_estimation/
├── __init__.py
├── interface.py                    # Existing abstract interface
├── openpose_estimator.py           # NEW: OpenPose implementation
├── mediapipe_estimator.py          # OPTIONAL: Alternative estimator
├── utils.py                        # Shared utilities
└── tests/
    ├── __init__.py
    ├── test_openpose.py
    └── test_interface_compliance.py
```

### 4.3 OpenPose Implementation

**Create:** `shared/python/pose_estimation/openpose_estimator.py`

```python
"""OpenPose implementation of PoseEstimator interface."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .interface import PoseEstimationResult, PoseEstimator
from ..common_utils import GolfModelingError, setup_logging

logger = setup_logging(__name__)


class OpenPoseEstimator(PoseEstimator):
    """OpenPose-based pose estimator for golf swing analysis."""

    # OpenPose body keypoint indices (BODY_25 model)
    KEYPOINT_MAP = {
        "nose": 0,
        "neck": 1,
        "right_shoulder": 2,
        "right_elbow": 3,
        "right_wrist": 4,
        "left_shoulder": 5,
        "left_elbow": 6,
        "left_wrist": 7,
        "mid_hip": 8,
        "right_hip": 9,
        "right_knee": 10,
        "right_ankle": 11,
        "left_hip": 12,
        "left_knee": 13,
        "left_ankle": 14,
        # ... full BODY_25 mapping
    }

    def __init__(self):
        """Initialize OpenPose estimator."""
        self.openpose = None
        self.params = None
        self.model_loaded = False

    def load_model(self, model_path: Path | None = None) -> None:
        """Load OpenPose model and configuration.

        Args:
            model_path: Path to OpenPose models directory.
                       If None, uses default OpenPose installation path.
        """
        try:
            # Import OpenPose Python API
            import sys
            sys.path.append('/usr/local/python')  # Default OpenPose install
            from openpose import pyopenpose as op

            self.openpose = op

        except ImportError:
            raise GolfModelingError(
                "OpenPose Python API not found. "
                "Install OpenPose with Python bindings: "
                "https://github.com/CMU-Perceptual-Computing-Lab/openpose"
            )

        # Configure OpenPose parameters
        self.params = self.openpose.WrapperPython()

        if model_path:
            self.params.configure({
                "model_folder": str(model_path),
                "model_pose": "BODY_25",
                "number_people_max": 1,  # Golf swing - single person
            })
        else:
            # Use default configuration
            self.params.configure({
                "model_pose": "BODY_25",
                "number_people_max": 1,
            })

        self.params.start()
        self.model_loaded = True

        logger.info("OpenPose model loaded successfully")

    def estimate_from_image(self, image: np.ndarray) -> PoseEstimationResult:
        """Estimate pose from a single image frame.

        Args:
            image: Input image (H, W, 3) in BGR format (OpenCV convention)

        Returns:
            PoseEstimationResult with joint angles and keypoints
        """
        if not self.model_loaded:
            raise GolfModelingError("Model not loaded. Call load_model() first.")

        # Process image with OpenPose
        datum = self.openpose.Datum()
        datum.cvInputData = image
        self.params.emplaceAndPop(op.VectorDatum([datum]))

        # Extract keypoints
        keypoints = datum.poseKeypoints

        if keypoints is None or len(keypoints) == 0:
            logger.warning("No person detected in frame")
            return PoseEstimationResult(
                joint_angles={},
                confidence=0.0,
                timestamp=0.0,
                raw_keypoints=None,
            )

        # Get first person (single golfer)
        person_keypoints = keypoints[0]

        # Convert keypoints to dictionary
        raw_keypoints = self._parse_keypoints(person_keypoints)

        # Compute joint angles from keypoints
        joint_angles = self._compute_joint_angles(raw_keypoints)

        # Compute average confidence
        confidence = self._compute_confidence(person_keypoints)

        return PoseEstimationResult(
            joint_angles=joint_angles,
            confidence=confidence,
            timestamp=0.0,  # Set by caller if from video
            raw_keypoints=raw_keypoints,
        )

    def estimate_from_video(
        self,
        video_path: Path
    ) -> list[PoseEstimationResult]:
        """Process an entire video file.

        Args:
            video_path: Path to video file

        Returns:
            List of PoseEstimationResult for each frame
        """
        if not self.model_loaded:
            raise GolfModelingError("Model not loaded. Call load_model() first.")

        results = []

        # Open video
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        logger.info(
            f"Processing video: {frame_count} frames at {fps} FPS"
        )

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Estimate pose for this frame
            result = self.estimate_from_image(frame)
            result.timestamp = frame_idx / fps

            results.append(result)
            frame_idx += 1

            if frame_idx % 100 == 0:
                logger.info(f"Processed {frame_idx}/{frame_count} frames")

        cap.release()

        logger.info(f"Video processing complete: {len(results)} frames")
        return results

    def _parse_keypoints(
        self,
        keypoints: np.ndarray
    ) -> dict[str, np.ndarray]:
        """Parse OpenPose keypoints array into dictionary.

        Args:
            keypoints: OpenPose keypoints array (N, 3) with (x, y, confidence)

        Returns:
            Dictionary mapping keypoint names to (x, y, conf) arrays
        """
        parsed = {}
        for name, idx in self.KEYPOINT_MAP.items():
            if idx < len(keypoints):
                parsed[name] = keypoints[idx]
        return parsed

    def _compute_joint_angles(
        self,
        keypoints: dict[str, np.ndarray]
    ) -> dict[str, float]:
        """Compute joint angles from keypoints.

        Args:
            keypoints: Dictionary of keypoint positions

        Returns:
            Dictionary mapping joint names to angles (radians)
        """
        joint_angles = {}

        # Right elbow angle
        if all(k in keypoints for k in ["right_shoulder", "right_elbow", "right_wrist"]):
            shoulder = keypoints["right_shoulder"][:2]
            elbow = keypoints["right_elbow"][:2]
            wrist = keypoints["right_wrist"][:2]

            angle = self._compute_angle_3points(shoulder, elbow, wrist)
            joint_angles["right_elbow_flexion"] = angle

        # Left elbow angle
        if all(k in keypoints for k in ["left_shoulder", "left_elbow", "left_wrist"]):
            shoulder = keypoints["left_shoulder"][:2]
            elbow = keypoints["left_elbow"][:2]
            wrist = keypoints["left_wrist"][:2]

            angle = self._compute_angle_3points(shoulder, elbow, wrist)
            joint_angles["left_elbow_flexion"] = angle

        # Right shoulder abduction (approximate from 2D)
        if all(k in keypoints for k in ["neck", "right_shoulder", "right_elbow"]):
            neck = keypoints["neck"][:2]
            shoulder = keypoints["right_shoulder"][:2]
            elbow = keypoints["right_elbow"][:2]

            angle = self._compute_angle_3points(neck, shoulder, elbow)
            joint_angles["right_shoulder_abduction"] = angle

        # Add more joint angle calculations...
        # - Hip angles
        # - Knee angles
        # - Spine angles (if visible)
        # - Wrist angles

        return joint_angles

    def _compute_angle_3points(
        self,
        p1: np.ndarray,
        p2: np.ndarray,
        p3: np.ndarray
    ) -> float:
        """Compute angle at p2 formed by p1-p2-p3.

        Args:
            p1, p2, p3: 2D points

        Returns:
            Angle in radians
        """
        v1 = p1 - p2
        v2 = p3 - p2

        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        angle = np.arccos(cos_angle)
        return angle

    def _compute_confidence(self, keypoints: np.ndarray) -> float:
        """Compute average confidence across all keypoints.

        Args:
            keypoints: Keypoint array with confidence values

        Returns:
            Average confidence (0-1)
        """
        confidences = keypoints[:, 2]
        valid_conf = confidences[confidences > 0]

        if len(valid_conf) == 0:
            return 0.0

        return float(np.mean(valid_conf))
```

### 4.4 Usage Example

**Create:** `examples/03_openpose_motion_capture.py`

```python
"""Example: Using OpenPose for golf swing motion capture."""

from pathlib import Path

from shared.python.pose_estimation.openpose_estimator import OpenPoseEstimator
from shared.python.engine_manager import EngineManager, EngineType

# Initialize OpenPose
estimator = OpenPoseEstimator()
estimator.load_model()

# Process golf swing video
video_path = Path("data/sample_swing.mp4")
results = estimator.estimate_from_video(video_path)

print(f"Processed {len(results)} frames")

# Extract joint angles over time
import matplotlib.pyplot as plt

times = [r.timestamp for r in results]
right_elbow_angles = [
    r.joint_angles.get("right_elbow_flexion", 0.0) for r in results
]

plt.plot(times, right_elbow_angles)
plt.xlabel("Time (s)")
plt.ylabel("Right Elbow Flexion (rad)")
plt.title("Golf Swing - Elbow Angle")
plt.show()

# Use results to drive OpenSim inverse kinematics
engine_manager = EngineManager()
engine_manager.switch_engine(EngineType.OPENSIM)

# Convert OpenPose results to marker data for OpenSim IK
# ... (implementation specific)
```

### 4.5 Dependencies

**Add to `pyproject.toml`:**

```toml
[project.optional-dependencies]
pose = [
    "opencv-python>=4.8.0",
    # OpenPose installed separately (not on PyPI)
    # Users install from: https://github.com/CMU-Perceptual-Computing-Lab/openpose
]
```

---

## 5. Integration with Existing Systems

### 5.1 Motion Capture Workflow

**Current:** MuJoCo motion capture (marker-based)
**New:** OpenPose vision-based pose estimation

**Integration Point:** Both produce joint angle trajectories

```
Video Input
    ↓
[OpenPose] → Joint Angles (2D/3D)
    ↓
[Inverse Kinematics] → Model Pose
    ↓
[OpenSim/MuJoCo/Drake] → Dynamics Analysis
```

### 5.2 Comparative Analysis Pipeline

Enable comparison between:
- OpenSim muscle-driven simulation
- MuJoCo contact-rich simulation
- Drake optimization-based solution

**Example Workflow:**

```python
from shared.python.comparative_analysis import CompareEngines

# Run same swing in multiple engines
results = CompareEngines(
    engines=[EngineType.MUJOCO, EngineType.OPENSIM, EngineType.DRAKE],
    initial_pose=openpose_ik_result,
    duration=2.0,
)

# Compare joint torques
results.plot_comparison("joint_torques")

# Statistical analysis
results.compute_correlation_matrix()
```

### 5.3 GUI Integration

**Update:** `launchers/golf_launcher.py`

Add OpenSim models to the launcher:

```python
MODELS_DICT = {
    "MuJoCo Humanoid": "engines/physics_engines/mujoco",
    "MuJoCo Dashboard": "engines/physics_engines/mujoco",
    "Drake Golf Model": "engines/physics_engines/drake",
    "Pinocchio Golf Model": "engines/physics_engines/pinocchio",
    "OpenSim Basic": "engines/physics_engines/opensim",          # NEW
    "OpenSim + MyoSim": "engines/physics_engines/opensim",       # NEW
}

MODEL_IMAGES = {
    # ... existing ...
    "OpenSim Basic": "opensim_basic.png",
    "OpenSim + MyoSim": "opensim_myosim.png",
}

MODEL_DESCRIPTIONS = {
    # ... existing ...
    "OpenSim Basic": "Musculoskeletal modeling with OpenSim. Industry-standard "
                     "biomechanics platform with inverse kinematics, inverse dynamics, "
                     "and muscle-driven forward simulation.",
    "OpenSim + MyoSim": "Advanced multi-scale muscle simulation. Combines OpenSim "
                        "skeletal dynamics with MyoSim detailed muscle fiber models for "
                        "research-grade musculoskeletal analysis.",
}
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**OpenSim Core**
- [ ] Create directory structure
- [ ] Implement `OpenSimProbe`
- [ ] Update `EngineManager` with OpenSim support
- [ ] Implement `OpenSimGolfModel` core wrapper
- [ ] Basic model loading and visualization
- [ ] Unit tests for core functionality

**OpenPose Integration**
- [ ] Implement `OpenPoseEstimator` class
- [ ] Compliance tests with `PoseEstimator` interface
- [ ] Video processing pipeline
- [ ] Example script

**Deliverables:**
- OpenSim engine loadable via EngineManager
- OpenPose can process videos and output joint angles
- Basic tests passing

### Phase 2: Kinematics & Dynamics (Weeks 3-4)

**OpenSim IK/ID**
- [ ] Implement `inverse_kinematics.py`
- [ ] Implement `inverse_dynamics.py`
- [ ] C3D/TRC/MOT file readers (`data_import.py`)
- [ ] Integration tests with sample data

**OpenPose → OpenSim Pipeline**
- [ ] Convert OpenPose keypoints to OpenSim markers
- [ ] Automated IK from video
- [ ] Validation against ground truth

**Deliverables:**
- End-to-end: Video → OpenPose → IK → Joint angles
- OpenSim IK/ID working with test data

### Phase 3: MyoSim Integration (Weeks 5-6)

**MyoSim Bridge**
- [ ] Implement `MyoSimMuscle` wrapper
- [ ] Implement `OpenSimMyoSimBridge`
- [ ] Muscle configuration YAML system
- [ ] Coupled simulation loop

**Model Development**
- [ ] Create basic OpenSim golf model (.osim)
- [ ] Add muscle definitions
- [ ] MyoSim muscle model files

**Deliverables:**
- Coupled OpenSim-MyoSim simulation running
- Example golf swing with detailed muscle dynamics

### Phase 4: GUI & Documentation (Weeks 7-8)

**GUI Development**
- [ ] OpenSim GUI following existing pattern
- [ ] Model selection interface
- [ ] Real-time visualization
- [ ] Results export

**Documentation**
- [ ] OpenSim engine docs
- [ ] MyoSim integration guide
- [ ] OpenPose usage guide
- [ ] API documentation
- [ ] Tutorial notebooks

**Deliverables:**
- Fully functional GUI
- Complete documentation
- Example workflows

### Phase 5: Testing & Validation (Week 9)

**Comprehensive Testing**
- [ ] Unit tests (target 80% coverage for new code)
- [ ] Integration tests
- [ ] Cross-engine comparison tests
- [ ] Performance benchmarks

**Validation**
- [ ] Physics validation (energy conservation, etc.)
- [ ] Compare with literature values
- [ ] Validate against experimental data

**Deliverables:**
- Test coverage >70% for new modules
- Validation report

### Phase 6: Integration & Polish (Week 10)

**Final Integration**
- [ ] Update launcher with OpenSim models
- [ ] Update model registry
- [ ] Cross-engine comparative analysis
- [ ] Performance optimization

**Code Quality**
- [ ] Ruff/Black/MyPy compliance
- [ ] Remove any duplication
- [ ] Type annotations complete
- [ ] Documentation review

**Deliverables:**
- Production-ready OpenSim/MyoSim/OpenPose integration
- All tests passing
- Documentation complete

---

## 7. Testing Strategy

### 7.1 Unit Tests

**OpenSim Core Tests**
```python
# tests/unit/test_opensim_core.py

def test_opensim_model_loading():
    """Test OpenSim model can be loaded."""
    model_path = Path("engines/physics_engines/opensim/models/golfer_basic.osim")
    model = OpenSimGolfModel(model_path)

    assert model.n_coords > 0
    assert model.model is not None

def test_opensim_coordinate_access():
    """Test getting/setting coordinates."""
    model = OpenSimGolfModel("golfer_basic.osim")

    # Set pose
    model.set_pose({"hip_flexion_r": 0.5})

    # Get pose
    pose = model.get_pose()
    assert "hip_flexion_r" in pose
    assert np.isclose(pose["hip_flexion_r"], 0.5)
```

**OpenPose Tests**
```python
# shared/python/pose_estimation/tests/test_openpose.py

def test_openpose_image_processing(sample_image):
    """Test OpenPose can process a single image."""
    estimator = OpenPoseEstimator()
    estimator.load_model()

    result = estimator.estimate_from_image(sample_image)

    assert isinstance(result, PoseEstimationResult)
    assert result.confidence >= 0.0
    assert result.confidence <= 1.0

def test_openpose_interface_compliance():
    """Test OpenPose implements PoseEstimator interface."""
    assert issubclass(OpenPoseEstimator, PoseEstimator)

    # Verify required methods
    assert hasattr(OpenPoseEstimator, 'load_model')
    assert hasattr(OpenPoseEstimator, 'estimate_from_image')
    assert hasattr(OpenPoseEstimator, 'estimate_from_video')
```

### 7.2 Integration Tests

**Cross-Engine Tests**
```python
# tests/integration/test_opensim_integration.py

def test_opensim_engine_loading():
    """Test OpenSim loads via EngineManager."""
    manager = EngineManager()
    success = manager.switch_engine(EngineType.OPENSIM)

    assert success
    assert manager.get_current_engine() == EngineType.OPENSIM

def test_openpose_to_opensim_pipeline():
    """Test full pipeline: Video → OpenPose → OpenSim IK."""
    # Process video with OpenPose
    estimator = OpenPoseEstimator()
    estimator.load_model()
    results = estimator.estimate_from_video("sample_swing.mp4")

    # Convert to OpenSim markers
    markers = convert_openpose_to_opensim_markers(results)

    # Run IK
    model = OpenSimGolfModel("golfer_basic.osim")
    joint_angles = model.compute_inverse_kinematics(markers)

    assert len(joint_angles) > 0
```

### 7.3 Physics Validation Tests

```python
# tests/physics_validation/test_opensim_physics.py

def test_opensim_energy_conservation():
    """Test energy conservation in OpenSim forward dynamics."""
    model = OpenSimGolfModel("golfer_basic.osim")

    results = model.simulate_forward_dynamics(
        duration=1.0,
        muscle_controls=None,  # Passive simulation
    )

    # Check energy conservation
    energy = results["total_energy"]
    energy_variation = np.std(energy) / np.mean(energy)

    assert energy_variation < 0.01  # <1% variation
```

---

## 8. Documentation Requirements

### 8.1 User Documentation

**Create:**
- `docs/engines/opensim.md` - OpenSim engine guide
- `docs/engines/myosim.md` - MyoSim integration guide
- `docs/user_guide/openpose.md` - OpenPose usage guide
- `docs/tutorials/video_to_simulation.md` - End-to-end tutorial

### 8.2 API Documentation

**Generate with Sphinx:**
```bash
sphinx-apidoc -f -o docs/api/opensim engines/physics_engines/opensim/python
sphinx-apidoc -f -o docs/api/pose_estimation shared/python/pose_estimation
```

### 8.3 Example Notebooks

**Create Jupyter notebooks:**
- `examples/notebooks/01_opensim_basic.ipynb`
- `examples/notebooks/02_opensim_myosim_muscle_analysis.ipynb`
- `examples/notebooks/03_openpose_video_analysis.ipynb`
- `examples/notebooks/04_full_pipeline_video_to_dynamics.ipynb`

---

## 9. Dependencies Summary

### 9.1 Python Packages

**Add to `pyproject.toml`:**

```toml
[project.optional-dependencies]
opensim = [
    "opensim>=4.4.0,<5.0.0",     # OpenSim API
    "myosim>=1.0.0",              # MyoSim (if on PyPI)
]

pose = [
    "opencv-python>=4.8.0",       # Video processing
    # OpenPose installed separately
]

all = [
    "golf-modeling-suite[dev,engines,analysis,opensim,pose]",
]
```

### 9.2 External Dependencies

**OpenSim:**
- Install via conda: `conda install -c opensim-org opensim`
- Or build from source: https://github.com/opensim-org/opensim-core

**MyoSim:**
- Install via pip: `pip install myosim` (if available)
- Or from source: https://github.com/Campbell-Muscle-Lab/MATMyoSim

**OpenPose:**
- Build from source: https://github.com/CMU-Perceptual-Computing-Lab/openpose
- Install Python bindings
- Not available on PyPI

---

## 10. Recommended Implementation Order

### Priority 1: OpenPose (Fastest ROI)

**Rationale:**
- Implements existing interface
- Immediate value (video → joint angles)
- No new engine infrastructure needed
- 1-2 weeks implementation

**Steps:**
1. Implement `OpenPoseEstimator`
2. Write tests
3. Create example scripts
4. Document usage

### Priority 2: OpenSim Core (Essential Foundation)

**Rationale:**
- Core musculoskeletal capability
- Foundation for MyoSim
- 3-4 weeks implementation

**Steps:**
1. Engine infrastructure (probe, manager integration)
2. Core wrapper (`OpenSimGolfModel`)
3. IK/ID implementation
4. Basic GUI
5. Documentation

### Priority 3: MyoSim Integration (Advanced Feature)

**Rationale:**
- Requires OpenSim foundation
- Research-grade feature
- 2-3 weeks implementation

**Steps:**
1. MyoSim bridge implementation
2. Coupled simulation
3. Example muscle models
4. Validation

---

## 11. Success Criteria

### Functional Requirements

- [ ] OpenSim engine selectable in launcher
- [ ] OpenSim models load and simulate
- [ ] MyoSim muscle forces computed correctly
- [ ] OpenPose processes videos and outputs joint angles
- [ ] End-to-end pipeline: Video → Pose → IK → Dynamics

### Quality Requirements

- [ ] Test coverage >70% for new code
- [ ] All tests passing in CI
- [ ] Ruff/Black/MyPy compliant
- [ ] No code duplication
- [ ] Type annotations complete

### Documentation Requirements

- [ ] User guides for all three components
- [ ] API documentation auto-generated
- [ ] Example scripts/notebooks
- [ ] Integration with existing docs

### Performance Requirements

- [ ] OpenPose: >10 FPS on CPU, >30 FPS on GPU
- [ ] OpenSim IK: <1s per frame
- [ ] MyoSim coupled sim: Real-time or faster

---

## 12. Risk Mitigation

### Risk: OpenPose Installation Complexity

**Mitigation:**
- Provide Docker image with OpenPose pre-installed
- Detailed installation guide
- Alternative: MediaPipe as fallback

### Risk: OpenSim-MyoSim Coupling Complexity

**Mitigation:**
- Start with OpenSim-only implementation
- MyoSim as optional enhancement
- Extensive testing of coupled simulation

### Risk: Model Development Effort

**Mitigation:**
- Start with simple models
- Reuse existing OpenSim models from literature
- Community contributions

---

## Appendix A: File Checklist

### New Files to Create

**OpenSim Engine:**
- [ ] `engines/physics_engines/opensim/python/opensim_golf/__init__.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/__main__.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/core.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/model_builder.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/inverse_kinematics.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/inverse_dynamics.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/forward_dynamics.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/myosim_bridge.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/gui.py`
- [ ] `engines/physics_engines/opensim/README.md`

**OpenPose:**
- [ ] `shared/python/pose_estimation/openpose_estimator.py`
- [ ] `shared/python/pose_estimation/utils.py`

**Tests:**
- [ ] `tests/unit/test_opensim_core.py`
- [ ] `tests/integration/test_opensim_integration.py`
- [ ] `shared/python/pose_estimation/tests/test_openpose.py`

**Documentation:**
- [ ] `docs/engines/opensim.md`
- [ ] `docs/engines/myosim.md`
- [ ] `docs/user_guide/openpose.md`

### Files to Modify

- [ ] `shared/python/engine_manager.py` - Add OpenSim support
- [ ] `shared/python/engine_probes.py` - Add `OpenSimProbe`
- [ ] `config/models.yaml` - Add OpenSim models
- [ ] `pyproject.toml` - Add dependencies
- [ ] `launchers/golf_launcher.py` - Add OpenSim to GUI

---

**End of Implementation Plan**

This plan provides a comprehensive roadmap for integrating OpenSim, MyoSim, and OpenPose into the Golf Modeling Suite following established architectural patterns.

**Next Steps:**
1. Review and approve this plan
2. Set up development branches
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews
