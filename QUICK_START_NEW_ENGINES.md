# Quick Start: Adding OpenSim, MyoSim, and OpenPose

**TL;DR:** Follow existing architecture patterns. OpenSim = new engine, MyoSim = OpenSim component, OpenPose = pose estimator implementation.

---

## Architecture Summary

```
Golf_Modeling_Suite/
├── engines/physics_engines/
│   ├── mujoco/          ✅ Existing
│   ├── drake/           ✅ Existing
│   ├── pinocchio/       ✅ Existing
│   └── opensim/         🆕 NEW ENGINE
│       ├── python/
│       │   └── opensim_golf/
│       │       ├── core.py              # Main wrapper
│       │       ├── inverse_kinematics.py
│       │       ├── inverse_dynamics.py
│       │       ├── myosim_bridge.py     # MyoSim integration
│       │       └── gui.py
│       ├── models/
│       │   ├── golfer_basic.osim
│       │   └── golfer_muscles.osim
│       └── myosim/                      # MyoSim muscle models
│           └── muscle_models/
│
├── shared/python/
│   ├── engine_manager.py     # UPDATE: Add OpenSim
│   ├── engine_probes.py      # UPDATE: Add OpenSimProbe
│   └── pose_estimation/
│       ├── interface.py      ✅ Existing interface
│       └── openpose_estimator.py  🆕 NEW: Implements interface
│
└── config/
    └── models.yaml          # UPDATE: Add OpenSim models
```

---

## Implementation Recommendation

### Phase 1: OpenPose (Week 1-2) ⚡ QUICK WIN

**Why start here:**
- Uses existing interface
- Immediate value (video → joint angles)
- No engine infrastructure needed

**Tasks:**
1. Create `shared/python/pose_estimation/openpose_estimator.py`
2. Implement `PoseEstimator` interface
3. Test with sample video
4. Create example script

**Code to write:** ~300 lines

---

### Phase 2: OpenSim Core (Week 3-6) 🏗️ FOUNDATION

**Why next:**
- Follows established engine pattern
- Foundation for MyoSim

**Tasks:**
1. Add `EngineType.OPENSIM` to `engine_manager.py`
2. Create `OpenSimProbe` in `engine_probes.py`
3. Implement `opensim_golf/core.py`
4. Add to launcher GUI
5. Create basic .osim model

**Code to write:** ~800 lines

---

### Phase 3: MyoSim Integration (Week 7-9) 🔬 ADVANCED

**Why last:**
- Requires OpenSim foundation
- Optional enhancement

**Tasks:**
1. Implement `myosim_bridge.py`
2. Create muscle configuration YAML
3. Coupled simulation loop
4. Validation

**Code to write:** ~500 lines

---

## Key Design Decisions

### ✅ DO: OpenSim as Separate Engine

**Rationale:** OpenSim is a complete biomechanics platform with its own solver

```python
# engine_manager.py
class EngineType(Enum):
    OPENSIM = "opensim"  # New engine type
```

### ✅ DO: MyoSim as OpenSim Component

**Rationale:** MyoSim provides muscle models, not skeleton dynamics

```
opensim/
├── python/opensim_golf/
│   └── myosim_bridge.py    # Integration layer
└── myosim/
    └── muscle_models/      # Muscle definitions
```

### ✅ DO: OpenPose Implements Existing Interface

**Rationale:** Interface already exists, just need implementation

```python
class OpenPoseEstimator(PoseEstimator):  # Implements existing interface
    def estimate_from_video(self, video_path: Path) -> list[PoseEstimationResult]:
        # Implementation
```

---

## Integration Points

### 1. Video → Simulation Pipeline

```
Video (.mp4)
    ↓
[OpenPose] → Joint angles
    ↓
[OpenSim IK] → Model pose
    ↓
[OpenSim/MyoSim Forward Dynamics] → Muscle forces & motion
```

### 2. Multi-Engine Comparison

```python
from shared.python.comparative_analysis import CompareEngines

results = CompareEngines(
    engines=[EngineType.MUJOCO, EngineType.OPENSIM, EngineType.DRAKE],
    initial_pose=openpose_result,
    duration=2.0,
)
```

---

## File Checklist

### Must Create

**OpenSim:**
- [ ] `engines/physics_engines/opensim/python/opensim_golf/core.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/inverse_kinematics.py`
- [ ] `engines/physics_engines/opensim/python/opensim_golf/myosim_bridge.py`
- [ ] `engines/physics_engines/opensim/models/golfer_basic.osim`

**OpenPose:**
- [ ] `shared/python/pose_estimation/openpose_estimator.py`

**Tests:**
- [ ] `tests/unit/test_opensim_core.py`
- [ ] `shared/python/pose_estimation/tests/test_openpose.py`

### Must Modify

- [ ] `shared/python/engine_manager.py` - Add `EngineType.OPENSIM`
- [ ] `shared/python/engine_probes.py` - Add `OpenSimProbe` class
- [ ] `config/models.yaml` - Add OpenSim model entries
- [ ] `launchers/golf_launcher.py` - Add OpenSim to GUI
- [ ] `pyproject.toml` - Add opensim dependencies

---

## Dependencies

### Python Packages

```toml
# Add to pyproject.toml

[project.optional-dependencies]
opensim = [
    "opensim>=4.4.0,<5.0.0",
    "myosim>=1.0.0",
]
pose = [
    "opencv-python>=4.8.0",
]
```

### External Installations

**OpenSim:**
```bash
conda install -c opensim-org opensim
```

**OpenPose:**
```bash
# Build from source
git clone https://github.com/CMU-Perceptual-Computing-Lab/openpose
# Follow build instructions
```

---

## Example Usage

### OpenPose

```python
from shared.python.pose_estimation.openpose_estimator import OpenPoseEstimator

estimator = OpenPoseEstimator()
estimator.load_model()

results = estimator.estimate_from_video("swing.mp4")
print(f"Detected {len(results)} frames")
```

### OpenSim

```python
from shared.python.engine_manager import EngineManager, EngineType

manager = EngineManager()
manager.switch_engine(EngineType.OPENSIM)

# Run IK, ID, or forward simulation
```

### MyoSim

```python
from engines.physics_engines.opensim.python.opensim_golf.myosim_bridge import (
    OpenSimMyoSimBridge
)

bridge = OpenSimMyoSimBridge(opensim_model, "myosim_config.yaml")
results = bridge.run_coupled_simulation(duration=2.0, muscle_controls=controls)
```

---

## Testing Strategy

### Unit Tests (70% coverage target)

```python
def test_opensim_loads():
    """Test OpenSim engine can be loaded."""
    manager = EngineManager()
    assert manager.switch_engine(EngineType.OPENSIM)

def test_openpose_processes_video():
    """Test OpenPose can process video."""
    estimator = OpenPoseEstimator()
    estimator.load_model()
    results = estimator.estimate_from_video("test.mp4")
    assert len(results) > 0
```

### Integration Tests

```python
def test_full_pipeline():
    """Test video → pose → simulation."""
    # OpenPose: Video → joint angles
    pose_results = openpose.estimate_from_video("swing.mp4")

    # OpenSim: Joint angles → IK
    ik_results = opensim.compute_inverse_kinematics(pose_results)

    # OpenSim+MyoSim: Forward simulation
    sim_results = myosim_bridge.run_coupled_simulation(...)

    assert sim_results["success"]
```

---

## Success Criteria

- [ ] OpenSim selectable in launcher
- [ ] OpenPose processes videos (>10 FPS)
- [ ] MyoSim muscle forces computed
- [ ] End-to-end pipeline works
- [ ] Tests pass (>70% coverage)
- [ ] Documentation complete

---

## Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| OpenPose | 1-2 weeks | ~300 LOC |
| OpenSim Core | 3-4 weeks | ~800 LOC |
| MyoSim | 2-3 weeks | ~500 LOC |
| **Total** | **6-9 weeks** | **~1600 LOC** |

---

## Next Steps

1. **Review** this plan and the detailed implementation plan
2. **Prioritize** which component to start with (recommend: OpenPose)
3. **Set up** development branch: `feature/opensim-myosim-openpose`
4. **Install** dependencies (OpenSim via conda, OpenPose from source)
5. **Start coding** following the established patterns

**Questions?** See full plan: `IMPLEMENTATION_PLAN_OPENSIM_MYOSIM_OPENPOSE.md`
