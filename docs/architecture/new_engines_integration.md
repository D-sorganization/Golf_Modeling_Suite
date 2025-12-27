# Integration Plan: OpenPose, OpenSim, and MyoSim

## Overview

This document outlines the coherent integration of three new engine types into the Golf Modeling Suite:

1. **OpenPose** - Motion capture and pose estimation
2. **OpenSim** - Musculoskeletal biomechanics simulation
3. **MyoSim** - Muscle fiber-level simulation

## Architectural Categorization

### Engine Taxonomy

The Golf Modeling Suite now supports three categories of engines:

```
Golf Modeling Suite Engines
├── Physics Engines (existing)
│   ├── MuJoCo - Contact dynamics
│   ├── Drake - Trajectory optimization
│   ├── Pinocchio - Rigid body dynamics
│   ├── MATLAB Simscape - Multibody simulation
│   └── Pendulum Models - Simplified models
│
├── Biomechanics Engines (NEW)
│   ├── OpenSim - Musculoskeletal modeling
│   └── MyoSim - Muscle fiber simulation
│
└── Input Processing (NEW)
    └── OpenPose - Motion capture & pose estimation
```

### Functional Roles

| Engine | Category | Role | Input | Output |
|--------|----------|------|-------|--------|
| OpenPose | Input | Pose estimation | Video/images | Joint positions |
| OpenSim | Biomechanics | Musculoskeletal sim | Kinematics | Forces, moments, muscle activations |
| MyoSim | Biomechanics | Muscle simulation | Muscle parameters | Fiber-level forces |
| MuJoCo/Drake/etc | Physics | Forward dynamics | Forces | Motion |

## Directory Structure

### Proposed Layout

```
Golf_Modeling_Suite/
├── engines/
│   ├── physics_engines/ (existing)
│   │   ├── mujoco/
│   │   ├── drake/
│   │   └── pinocchio/
│   │
│   ├── biomechanics_engines/ (NEW)
│   │   ├── opensim/
│   │   │   ├── models/          # .osim model files
│   │   │   ├── python/
│   │   │   │   ├── src/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── opensim_wrapper.py
│   │   │   │   │   ├── inverse_kinematics.py
│   │   │   │   │   ├── inverse_dynamics.py
│   │   │   │   │   └── muscle_analysis.py
│   │   │   │   ├── tests/
│   │   │   │   └── requirements.txt
│   │   │   ├── assets/
│   │   │   │   ├── golfer_model.osim
│   │   │   │   └── muscle_parameters.xml
│   │   │   └── README.md
│   │   │
│   │   └── myosim/
│   │       ├── python/
│   │       │   ├── src/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── myosim_wrapper.py
│   │       │   │   ├── half_sarcomere.py
│   │       │   │   └── muscle_model.py
│   │       │   └── tests/
│   │       ├── models/
│   │       └── README.md
│   │
│   ├── input_processing/ (NEW)
│   │   └── openpose/
│   │       ├── python/
│   │       │   ├── src/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── openpose_wrapper.py
│   │       │   │   ├── pose_estimator.py
│   │       │   │   ├── video_processor.py
│   │       │   │   └── skeleton_converter.py
│   │       │   ├── tests/
│   │       │   └── requirements.txt
│   │       ├── models/          # Pre-trained pose models
│   │       │   ├── body_25/
│   │       │   └── coco/
│   │       ├── assets/
│   │       │   └── sample_golf_swings/
│   │       └── README.md
│   │
│   ├── Simscape_Multibody_Models/ (existing)
│   └── pendulum_models/ (existing)
│
└── shared/
    └── python/
        ├── engine_manager.py (UPDATE)
        ├── engine_probes.py (UPDATE)
        └── pipeline_manager.py (NEW)
```

## Code Integration

### 1. Update EngineType Enum

**File:** `shared/python/engine_manager.py`

```python
from enum import Enum

class EngineCategory(Enum):
    """Engine categories by function."""
    PHYSICS = "physics"
    BIOMECHANICS = "biomechanics"
    INPUT_PROCESSING = "input_processing"

class EngineType(Enum):
    """Available engine types with category metadata."""

    # Physics engines (existing)
    MUJOCO = ("mujoco", EngineCategory.PHYSICS)
    DRAKE = ("drake", EngineCategory.PHYSICS)
    PINOCCHIO = ("pinocchio", EngineCategory.PHYSICS)
    MATLAB_2D = ("matlab_2d", EngineCategory.PHYSICS)
    MATLAB_3D = ("matlab_3d", EngineCategory.PHYSICS)
    PENDULUM = ("pendulum", EngineCategory.PHYSICS)

    # Biomechanics engines (NEW)
    OPENSIM = ("opensim", EngineCategory.BIOMECHANICS)
    MYOSIM = ("myosim", EngineCategory.BIOMECHANICS)

    # Input processing (NEW)
    OPENPOSE = ("openpose", EngineCategory.INPUT_PROCESSING)

    def __init__(self, engine_id: str, category: EngineCategory):
        self.engine_id = engine_id
        self.category = category

    @property
    def is_physics_engine(self) -> bool:
        return self.category == EngineCategory.PHYSICS

    @property
    def is_biomechanics_engine(self) -> bool:
        return self.category == EngineCategory.BIOMECHANICS

    @property
    def is_input_processor(self) -> bool:
        return self.category == EngineCategory.INPUT_PROCESSING
```

### 2. Extend EngineManager

```python
class EngineManager:
    """Manages different engines for golf swing modeling."""

    def __init__(self, suite_root: Path | None = None):
        # ... existing initialization ...

        # Add new engine paths
        self.engine_paths = {
            # Existing paths...
            EngineType.MUJOCO: self.engines_root / "physics_engines" / "mujoco",
            EngineType.DRAKE: self.engines_root / "physics_engines" / "drake",
            EngineType.PINOCCHIO: self.engines_root / "physics_engines" / "pinocchio",

            # NEW: Biomechanics engines
            EngineType.OPENSIM: self.engines_root / "biomechanics_engines" / "opensim",
            EngineType.MYOSIM: self.engines_root / "biomechanics_engines" / "myosim",

            # NEW: Input processing
            EngineType.OPENPOSE: self.engines_root / "input_processing" / "openpose",
        }

        # Add new probes
        from .engine_probes import (
            OpenPoseProbe,
            OpenSimProbe,
            MyoSimProbe,
            # ... existing probes
        )

        self.probes = {
            # Existing probes...
            EngineType.OPENPOSE: OpenPoseProbe(self.suite_root),
            EngineType.OPENSIM: OpenSimProbe(self.suite_root),
            EngineType.MYOSIM: MyoSimProbe(self.suite_root),
        }

        # Engine storage
        self._openpose_module: Any = None
        self._opensim_module: Any = None
        self._myosim_module: Any = None

    def get_engines_by_category(
        self, category: EngineCategory
    ) -> list[EngineType]:
        """Get all engines in a specific category."""
        return [
            engine for engine in EngineType
            if engine.category == category
            and self.get_engine_status(engine) == EngineStatus.AVAILABLE
        ]

    def _load_opensim_engine(self) -> None:
        """Load OpenSim with validation."""
        try:
            import opensim as osim

            logger.info(f"OpenSim version {osim.GetVersion()} imported")

            # Verify model directory
            model_dir = self.engine_paths[EngineType.OPENSIM] / "models"
            if not model_dir.exists():
                raise GolfModelingError(f"OpenSim models not found: {model_dir}")

            # Test load a model
            model_files = list(model_dir.glob("*.osim"))
            if model_files:
                test_model = osim.Model(str(model_files[0]))
                logger.info(f"Validated OpenSim model: {model_files[0].name}")

            self._opensim_module = osim
            logger.info("OpenSim engine loaded successfully")

        except ImportError as e:
            raise GolfModelingError(
                "OpenSim not installed. Install with: conda install -c opensim-org opensim"
            ) from e

    def _load_myosim_engine(self) -> None:
        """Load MyoSim with validation."""
        try:
            import myosim

            logger.info(f"MyoSim version {myosim.__version__} imported")

            # MyoSim is often used as a component with OpenSim
            # Verify it can create muscle models
            _ = myosim.HalfSarcomere()
            logger.info("MyoSim muscle model creation validated")

            self._myosim_module = myosim
            logger.info("MyoSim engine loaded successfully")

        except ImportError as e:
            raise GolfModelingError(
                "MyoSim not installed. Install with: pip install myosim"
            ) from e

    def _load_openpose_engine(self) -> None:
        """Load OpenPose with validation."""
        try:
            # OpenPose Python API (if using official bindings)
            import pyopenpose as op

            logger.info("OpenPose imported successfully")

            # Verify model files exist
            model_dir = self.engine_paths[EngineType.OPENPOSE] / "models"
            if not model_dir.exists():
                raise GolfModelingError(f"OpenPose models not found: {model_dir}")

            # Check for required model files
            required_models = ["body_25", "hand", "face"]
            for model in required_models:
                model_path = model_dir / model
                if not model_path.exists():
                    logger.warning(f"OpenPose model missing: {model}")

            self._openpose_module = op
            logger.info("OpenPose engine loaded successfully")

        except ImportError as e:
            raise GolfModelingError(
                "OpenPose not installed. See: https://github.com/CMU-Perceptual-Computing-Lab/openpose"
            ) from e
```

### 3. Create Engine Probes

**File:** `shared/python/engine_probes.py`

```python
class OpenPoseProbe:
    """Probe for OpenPose availability."""

    def __init__(self, suite_root: Path):
        self.suite_root = suite_root

    def probe(self) -> EngineProbeResult:
        """Check if OpenPose is available."""
        missing_deps = []

        # Check Python bindings
        try:
            import pyopenpose
        except ImportError:
            missing_deps.append("pyopenpose")

        # Check models
        model_dir = self.suite_root / "engines" / "input_processing" / "openpose" / "models"
        if not model_dir.exists():
            return EngineProbeResult(
                engine_name="OpenPose",
                status=ProbeStatus.MISSING_ASSETS,
                version=None,
                missing_dependencies=missing_deps,
                diagnostic_message="OpenPose model files not found"
            )

        if missing_deps:
            return EngineProbeResult(
                engine_name="OpenPose",
                status=ProbeStatus.NOT_INSTALLED,
                version=None,
                missing_dependencies=missing_deps,
                diagnostic_message="OpenPose Python bindings not installed"
            )

        return EngineProbeResult(
            engine_name="OpenPose",
            status=ProbeStatus.AVAILABLE,
            version="1.7.0",  # Detect actual version
            missing_dependencies=[],
            diagnostic_message="OpenPose ready"
        )

class OpenSimProbe:
    """Probe for OpenSim availability."""

    def __init__(self, suite_root: Path):
        self.suite_root = suite_root

    def probe(self) -> EngineProbeResult:
        """Check if OpenSim is available."""
        missing_deps = []
        version = None

        try:
            import opensim as osim
            version = osim.GetVersion()
        except ImportError:
            missing_deps.append("opensim")

        if missing_deps:
            return EngineProbeResult(
                engine_name="OpenSim",
                status=ProbeStatus.NOT_INSTALLED,
                version=None,
                missing_dependencies=missing_deps,
                diagnostic_message="OpenSim not installed. Install with: conda install -c opensim-org opensim"
            )

        # Check for models
        model_dir = self.suite_root / "engines" / "biomechanics_engines" / "opensim" / "models"
        if not model_dir.exists() or not list(model_dir.glob("*.osim")):
            return EngineProbeResult(
                engine_name="OpenSim",
                status=ProbeStatus.MISSING_ASSETS,
                version=version,
                missing_dependencies=[],
                diagnostic_message="OpenSim installed but no .osim models found"
            )

        return EngineProbeResult(
            engine_name="OpenSim",
            status=ProbeStatus.AVAILABLE,
            version=version,
            missing_dependencies=[],
            diagnostic_message="OpenSim ready with musculoskeletal models"
        )

class MyoSimProbe:
    """Probe for MyoSim availability."""

    def __init__(self, suite_root: Path):
        self.suite_root = suite_root

    def probe(self) -> EngineProbeResult:
        """Check if MyoSim is available."""
        missing_deps = []
        version = None

        try:
            import myosim
            version = getattr(myosim, '__version__', 'unknown')
        except ImportError:
            missing_deps.append("myosim")

        if missing_deps:
            return EngineProbeResult(
                engine_name="MyoSim",
                status=ProbeStatus.NOT_INSTALLED,
                version=None,
                missing_dependencies=missing_deps,
                diagnostic_message="MyoSim not installed. Install with: pip install myosim"
            )

        return EngineProbeResult(
            engine_name="MyoSim",
            status=ProbeStatus.AVAILABLE,
            version=version,
            missing_dependencies=[],
            diagnostic_message="MyoSim ready for muscle fiber simulation"
        )
```

### 4. Create Pipeline Manager (NEW)

**File:** `shared/python/pipeline_manager.py`

```python
"""Pipeline manager for chaining engines together.

This enables workflows like:
OpenPose → OpenSim → MuJoCo
(video → pose → biomechanics → physics)
"""

from pathlib import Path
from typing import Any, Protocol
from dataclasses import dataclass

from .engine_manager import EngineManager, EngineType


class PipelineStage(Protocol):
    """Protocol for pipeline stages."""

    def process(self, input_data: Any) -> Any:
        """Process data through this stage."""
        ...


@dataclass
class PipelineConfig:
    """Configuration for analysis pipeline."""

    input_stage: EngineType  # e.g., OPENPOSE
    biomechanics_stage: EngineType | None  # e.g., OPENSIM
    physics_stage: EngineType | None  # e.g., MUJOCO
    output_format: str = "json"


class AnalysisPipeline:
    """Manage multi-engine analysis pipelines."""

    def __init__(self, engine_manager: EngineManager):
        self.engine_manager = engine_manager

    def create_full_pipeline(
        self,
        video_path: Path,
        config: PipelineConfig
    ) -> dict[str, Any]:
        """Run complete analysis pipeline.

        Workflow:
        1. OpenPose: Extract pose from video
        2. OpenSim: Compute inverse kinematics/dynamics
        3. Physics engine: Validate/forward simulate

        Args:
            video_path: Input golf swing video
            config: Pipeline configuration

        Returns:
            Analysis results from all stages
        """
        results = {}

        # Stage 1: Pose estimation
        if config.input_stage == EngineType.OPENPOSE:
            results['pose'] = self._run_openpose(video_path)

        # Stage 2: Biomechanical analysis
        if config.biomechanics_stage == EngineType.OPENSIM:
            results['biomechanics'] = self._run_opensim(results['pose'])

        # Stage 3: Physics validation (optional)
        if config.physics_stage:
            results['physics'] = self._run_physics_engine(
                config.physics_stage,
                results.get('biomechanics', results['pose'])
            )

        return results

    def _run_openpose(self, video_path: Path) -> dict[str, Any]:
        """Extract pose from video using OpenPose."""
        # Ensure OpenPose is loaded
        self.engine_manager.switch_engine(EngineType.OPENPOSE)

        # Process video (implementation details)
        return {
            'keypoints': [],  # Joint positions over time
            'confidence': [],  # Confidence scores
            'frames': []      # Frame-by-frame data
        }

    def _run_opensim(self, pose_data: dict[str, Any]) -> dict[str, Any]:
        """Run OpenSim biomechanical analysis."""
        self.engine_manager.switch_engine(EngineType.OPENSIM)

        # Convert pose to OpenSim format
        # Run inverse kinematics
        # Run inverse dynamics
        # Analyze muscle activations

        return {
            'joint_angles': [],
            'joint_moments': [],
            'muscle_forces': [],
            'muscle_activations': []
        }

    def _run_physics_engine(
        self,
        engine_type: EngineType,
        input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Run physics simulation for validation."""
        self.engine_manager.switch_engine(engine_type)

        # Forward simulate with computed forces
        # Compare to measured kinematics

        return {
            'simulated_trajectory': [],
            'validation_error': 0.0
        }


# Example usage workflow
def example_golf_swing_analysis():
    """Example: Full golf swing analysis pipeline."""

    # Initialize managers
    engine_mgr = EngineManager()
    pipeline = AnalysisPipeline(engine_mgr)

    # Configure pipeline
    config = PipelineConfig(
        input_stage=EngineType.OPENPOSE,
        biomechanics_stage=EngineType.OPENSIM,
        physics_stage=EngineType.MUJOCO
    )

    # Run analysis
    video_path = Path("data/golf_swing_001.mp4")
    results = pipeline.create_full_pipeline(video_path, config)

    # Results contain:
    # - Pose estimation from OpenPose
    # - Biomechanical analysis from OpenSim
    # - Physics validation from MuJoCo

    return results
```

## Integration with Launcher

Update `launchers/golf_launcher.py` to include new engines:

```python
MODELS_DICT = {
    # Existing
    "MuJoCo Humanoid": "engines/physics_engines/mujoco",
    "Drake Golf Model": "engines/physics_engines/drake",
    "Pinocchio Golf Model": "engines/physics_engines/pinocchio",

    # NEW: Biomechanics
    "OpenSim Musculoskeletal": "engines/biomechanics_engines/opensim",
    "MyoSim Muscle Fiber": "engines/biomechanics_engines/myosim",

    # NEW: Input Processing
    "OpenPose Motion Capture": "engines/input_processing/openpose",

    # NEW: Pipeline
    "Full Analysis Pipeline": "pipelines/complete_workflow",
}

MODEL_DESCRIPTIONS = {
    # ... existing ...

    "OpenSim Musculoskeletal":
        "Biomechanical analysis using OpenSim musculoskeletal models. "
        "Performs inverse kinematics, inverse dynamics, and muscle analysis. "
        "Ideal for understanding joint loads, muscle forces, and biomechanical "
        "efficiency during the golf swing.",

    "MyoSim Muscle Fiber":
        "Fiber-level muscle simulation using MyoSim. Models cross-bridge dynamics, "
        "calcium kinetics, and force generation. Can be coupled with OpenSim for "
        "multi-scale musculoskeletal analysis.",

    "OpenPose Motion Capture":
        "Real-time pose estimation from video using OpenPose. Extracts 2D/3D "
        "joint positions from golf swing videos for downstream biomechanical "
        "or physics analysis. No markers required!",

    "Full Analysis Pipeline":
        "Complete workflow: OpenPose extracts pose from video → OpenSim computes "
        "biomechanics → MuJoCo validates with physics simulation. One-click "
        "comprehensive golf swing analysis.",
}
```

## Dependencies

### pyproject.toml Updates

```toml
[project.optional-dependencies]
# ... existing ...

biomechanics = [
    "opensim>=4.4",  # Via conda: conda install -c opensim-org opensim
    "myosim>=1.0.0",
]

input-processing = [
    "opencv-python>=4.8.0",
    "pyopenpose>=1.7.0",  # May need manual build
]

# Convenience: all new engines
new-engines = [
    "golf-modeling-suite[biomechanics,input-processing]",
]
```

## Installation Instructions

### OpenSim
```bash
# OpenSim requires conda
conda create -n golf-suite python=3.11
conda activate golf-suite
conda install -c opensim-org opensim=4.4
```

### MyoSim
```bash
pip install myosim
```

### OpenPose
```bash
# OpenPose requires manual build (complex)
# See: https://github.com/CMU-Perceptual-Computing-Lab/openpose

# Alternative: Use pre-built bindings if available
pip install pyopenpose  # If available for your platform
```

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_new_engines.py
def test_opensim_engine_loads():
    """Test OpenSim engine loading."""
    mgr = EngineManager()
    success = mgr.switch_engine(EngineType.OPENSIM)
    assert success
    assert mgr.current_engine == EngineType.OPENSIM

def test_pipeline_creation():
    """Test pipeline manager creation."""
    mgr = EngineManager()
    pipeline = AnalysisPipeline(mgr)

    config = PipelineConfig(
        input_stage=EngineType.OPENPOSE,
        biomechanics_stage=EngineType.OPENSIM
    )

    assert config.input_stage == EngineType.OPENPOSE
```

### Integration Tests

```python
# tests/integration/test_biomechanics_pipeline.py
@pytest.mark.slow
def test_full_analysis_pipeline():
    """Test complete OpenPose → OpenSim → MuJoCo pipeline."""
    mgr = EngineManager()
    pipeline = AnalysisPipeline(mgr)

    # Use sample data
    video_path = Path("tests/fixtures/golf_swing_sample.mp4")

    config = PipelineConfig(
        input_stage=EngineType.OPENPOSE,
        biomechanics_stage=EngineType.OPENSIM,
        physics_stage=EngineType.MUJOCO
    )

    results = pipeline.create_full_pipeline(video_path, config)

    assert 'pose' in results
    assert 'biomechanics' in results
    assert 'physics' in results
```

## Migration Path

### Phase 1: Structure (Week 1)
1. Create directory structure
2. Add EngineType enums
3. Create probe classes
4. Update EngineManager

### Phase 2: Engines (Weeks 2-3)
1. Implement OpenSim wrapper
2. Implement MyoSim wrapper
3. Implement OpenPose wrapper
4. Add tests

### Phase 3: Pipeline (Week 4)
1. Create PipelineManager
2. Implement workflows
3. Add GUI integration
4. Documentation

## Summary

**Key Design Principles:**

1. **Categorical Organization** - Engines grouped by function
2. **Consistent Structure** - Same patterns as existing engines
3. **Pipeline Support** - Engines can be chained
4. **Probe-based Discovery** - Automatic availability checking
5. **Backwards Compatible** - Existing code continues to work

**New Capabilities:**

- Video → Pose → Biomechanics → Physics pipeline
- Musculoskeletal analysis via OpenSim
- Muscle fiber simulation via MyoSim
- Marker-free motion capture via OpenPose

This architecture maintains consistency while enabling powerful new workflows!
