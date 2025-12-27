# Quick Start: Adding OpenPose, OpenSim, and MyoSim

This guide shows you how to integrate the new engines into your workflow.

## 📋 Summary

**New Engines:**
- **OpenPose** - Motion capture from video (no markers!)
- **OpenSim** - Musculoskeletal biomechanics
- **MyoSim** - Muscle fiber simulation

**Key Insight:** These engines work differently than physics engines:
- OpenPose = INPUT (video → joint positions)
- OpenSim = BIOMECHANICS (positions → forces)
- MyoSim = MUSCLE DETAIL (forces → fiber dynamics)
- MuJoCo/Drake = VALIDATION (forces → simulated motion)

## 🚀 Quick Usage Examples

### Example 1: Video to Pose (OpenPose)

```python
from pathlib import Path
from shared.python.engine_manager import EngineManager
from shared.python.engine_categories import ExtendedEngineType

# Initialize
mgr = EngineManager()
mgr.switch_engine(ExtendedEngineType.OPENPOSE)

# Process video
video_path = Path("data/golf_swing.mp4")
pose_data = mgr.extract_pose(video_path)

# Results
print(f"Detected {len(pose_data['keypoints'])} frames")
print(f"Joints: {pose_data['joint_names']}")
```

### Example 2: Biomechanics Analysis (OpenSim)

```python
from shared.python.engine_manager import EngineManager
from shared.python.engine_categories import ExtendedEngineType

# Initialize
mgr = EngineManager()
mgr.switch_engine(ExtendedEngineType.OPENSIM)

# Load model
model_path = Path("models/golfer_musculoskeletal.osim")
mgr.load_opensim_model(model_path)

# Run inverse kinematics
kinematics_data = mgr.run_inverse_kinematics(pose_data)

# Run inverse dynamics
dynamics_data = mgr.run_inverse_dynamics(kinematics_data)

# Get muscle forces
muscle_forces = dynamics_data['muscle_forces']
```

### Example 3: Complete Pipeline

```python
from pathlib import Path
from shared.python.engine_manager import EngineManager
from shared.python.pipeline_manager import AnalysisPipeline, PipelineConfig

# Setup
mgr = EngineManager()
pipeline = AnalysisPipeline(mgr)

# Configure full workflow
config = PipelineConfig(
    use_openpose=True,
    use_opensim=True,
    opensim_model_path=Path("models/golfer.osim"),
    run_inverse_kinematics=True,
    run_inverse_dynamics=True,
    run_muscle_analysis=True,
    use_physics_engine=True,
    physics_engine_type="mujoco"
)

# Run complete analysis
results = pipeline.run_full_pipeline(
    input_path=Path("data/golf_swing_001.mp4"),
    config=config
)

# Access results
print(f"Pose data: {results.pose_data is not None}")
print(f"Joint angles: {results.kinematics is not None}")
print(f"Joint moments: {results.dynamics is not None}")
print(f"Muscle forces: {results.muscle_analysis is not None}")
print(f"Physics validation: {results.physics_validation is not None}")
```

### Example 4: Convenience Workflows

```python
# Video → Biomechanics (automatic)
results = pipeline.run_openpose_to_opensim(
    video_path=Path("swing.mp4"),
    opensim_model_path=Path("golfer.osim")
)

# Biomechanics → Physics Validation
results = pipeline.run_opensim_to_mujoco(
    kinematics_path=Path("joint_angles.mot"),
    opensim_model_path=Path("golfer.osim")
)
```

## 📁 Directory Setup

Create the following structure:

```bash
# Create new engine directories
mkdir -p engines/biomechanics_engines/opensim/{models,python/src,assets}
mkdir -p engines/biomechanics_engines/myosim/{python/src,models}
mkdir -p engines/input_processing/openpose/{models,python/src,assets}

# Verify structure
tree engines/ -L 3 -d
```

## 📦 Installation

### OpenPose

```bash
# OpenPose requires manual build (complex)
# See: https://github.com/CMU-Perceptual-Computing-Lab/openpose

# For Ubuntu:
sudo apt install libopencv-dev
git clone https://github.com/CMU-Perceptual-Computing-Lab/openpose
cd openpose
mkdir build && cd build
cmake ..
make -j`nproc`

# Python bindings
cd ../python
pip install -e .
```

### OpenSim

```bash
# OpenSim requires conda
conda create -n golf-suite python=3.11
conda activate golf-suite
conda install -c opensim-org opensim=4.4

# Verify installation
python -c "import opensim; print(opensim.GetVersion())"
```

### MyoSim

```bash
# MyoSim is pip-installable
pip install myosim

# Verify installation
python -c "import myosim; print(myosim.__version__)"
```

## 🔧 Configuration

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
biomechanics = [
    "opensim>=4.4",      # Install via conda
    "myosim>=1.0.0",
]

input-processing = [
    "opencv-python>=4.8.0",
    "pyopenpose>=1.7.0",  # May need manual build
]

new-engines = [
    "golf-modeling-suite[biomechanics,input-processing]",
]
```

## 🧪 Testing

```bash
# Test engine availability
python -c "
from shared.python.engine_manager import EngineManager
from shared.python.engine_categories import ExtendedEngineType

mgr = EngineManager()
mgr.probe_all_engines()
report = mgr.get_diagnostic_report()
print(report)
"

# Should show:
# ✅ OPENSIM - Status: available
# ✅ MYOSIM - Status: available
# ✅ OPENPOSE - Status: available
```

## 📊 Workflow Decision Tree

```
Do you have video?
├─ YES → Use OpenPose
│   └─ Want biomechanics?
│       ├─ YES → Use OpenSim
│       │   └─ Want muscle detail?
│       │       ├─ YES → Use MyoSim
│       │       └─ NO → Stop at OpenSim
│       └─ NO → Use pose data directly
│
└─ NO → Do you have motion capture data?
    ├─ YES → Use OpenSim directly
    └─ NO → Use physics engines (MuJoCo/Drake)
```

## 🎯 Common Workflows

### Workflow A: Video Analysis
```
Video → OpenPose → Joint positions → Analysis
```

### Workflow B: Biomechanical Analysis
```
Motion capture → OpenSim → Joint moments → Muscle forces
```

### Workflow C: Complete Analysis
```
Video → OpenPose → OpenSim → MyoSim → MuJoCo
(pose)   (IK/ID)    (muscles)  (fiber)   (validation)
```

### Workflow D: Model Validation
```
Measured kinematics → OpenSim → Forces → MuJoCo → Compare
```

## 📚 Next Steps

1. **Read full integration guide:** `docs/architecture/new_engines_integration.md`
2. **Install engines** using instructions above
3. **Try examples** in this quickstart
4. **Check engine status** with diagnostic report
5. **Build your workflow** using PipelineManager

## 🆘 Troubleshooting

### OpenPose not found
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add OpenPose to path
export PYTHONPATH="/path/to/openpose/build/python:$PYTHONPATH"
```

### OpenSim import error
```bash
# Must use conda environment
conda activate golf-suite
python -c "import opensim"  # Should work

# Outside conda will fail
deactivate
python -c "import opensim"  # ImportError
```

### Missing models
```bash
# Download OpenPose models
cd engines/input_processing/openpose/models
wget https://github.com/CMU-Perceptual-Computing-Lab/openpose_train/tree/master/experimental_models/body_25/

# OpenSim models - use built-in or custom
python -c "
import opensim
model = opensim.Model()
model.print('default_gait_model.osim')
"
```

## 💡 Tips

1. **Start simple** - Try OpenPose alone first
2. **Use pipelines** - PipelineManager handles complexity
3. **Check probes** - Always verify engines are available
4. **Save intermediate** - Set `save_intermediate_results=True`
5. **Parallel engines** - Different engines can run simultaneously

## 🔗 Resources

- **OpenPose:** https://github.com/CMU-Perceptual-Computing-Lab/openpose
- **OpenSim:** https://opensim.stanford.edu/
- **MyoSim:** https://github.com/Campbell-Muscle-Lab/MyoSim
- **Full docs:** `docs/architecture/new_engines_integration.md`

---

Happy modeling! 🏌️‍♂️
