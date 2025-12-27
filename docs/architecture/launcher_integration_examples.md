# Launcher Integration Examples

How to add OpenPose, OpenSim, and MyoSim to the GUI launcher.

## Update golf_launcher.py

### 1. Add to MODELS_DICT

```python
# launchers/golf_launcher.py

MODELS_DICT = {
    # === PHYSICS ENGINES (Existing) ===
    "MuJoCo Humanoid": "engines/physics_engines/mujoco",
    "MuJoCo Dashboard": "engines/physics_engines/mujoco",
    "Drake Golf Model": "engines/physics_engines/drake",
    "Pinocchio Golf Model": "engines/physics_engines/pinocchio",

    # === BIOMECHANICS ENGINES (NEW) ===
    "OpenSim Musculoskeletal": "engines/biomechanics_engines/opensim",
    "MyoSim Muscle Fiber": "engines/biomechanics_engines/myosim",

    # === INPUT PROCESSING (NEW) ===
    "OpenPose Motion Capture": "engines/input_processing/openpose",

    # === INTEGRATED WORKFLOWS (NEW) ===
    "Complete Analysis Pipeline": "pipelines/complete_workflow",
}
```

### 2. Add Images

```python
MODEL_IMAGES = {
    # Existing...
    "MuJoCo Humanoid": "mujoco_humanoid.png",
    "Drake Golf Model": "drake.png",
    "Pinocchio Golf Model": "pinocchio.png",

    # NEW
    "OpenSim Musculoskeletal": "opensim_model.png",
    "MyoSim Muscle Fiber": "myosim_fiber.png",
    "OpenPose Motion Capture": "openpose_skeleton.png",
    "Complete Analysis Pipeline": "pipeline_workflow.png",
}
```

### 3. Add Descriptions

```python
MODEL_DESCRIPTIONS = {
    # Existing descriptions...

    # NEW: Biomechanics
    "OpenSim Musculoskeletal":
        "Biomechanical analysis using OpenSim musculoskeletal models. "
        "Performs inverse kinematics to compute joint angles from motion capture, "
        "inverse dynamics to calculate joint moments and ground reaction forces, "
        "and muscle analysis to estimate muscle forces and activations. "
        "Ideal for understanding joint loads, biomechanical efficiency, and "
        "injury risk during the golf swing.",

    "MyoSim Muscle Fiber":
        "Fiber-level muscle simulation using MyoSim. Models individual sarcomere "
        "dynamics including cross-bridge kinetics, calcium transients, and "
        "length-tension-velocity relationships. Can be coupled with OpenSim "
        "for multi-scale musculoskeletal analysis from whole-body biomechanics "
        "down to molecular mechanisms of force generation.",

    # NEW: Input Processing
    "OpenPose Motion Capture":
        "Real-time pose estimation and motion capture from video using OpenPose. "
        "Extracts 2D/3D joint positions from golf swing videos without markers. "
        "Supports body, hand, and face keypoint detection. Perfect for analyzing "
        "swing videos from smartphone cameras or broadcast footage. Output can feed "
        "directly into biomechanical (OpenSim) or physics (MuJoCo) analysis.",

    # NEW: Pipeline
    "Complete Analysis Pipeline":
        "End-to-end workflow combining all engines: "
        "(1) OpenPose extracts pose from video, "
        "(2) OpenSim computes biomechanics (IK, ID, muscle forces), "
        "(3) MyoSim simulates muscle fiber dynamics (optional), "
        "(4) MuJoCo validates with forward physics simulation. "
        "One-click comprehensive golf swing analysis from raw video to detailed "
        "biomechanical and physical insights.",
}
```

### 4. Add Custom Launch Methods

```python
# In GolfLauncher class

def _custom_launch_opensim(self, abs_repo_path):
    """Launch OpenSim GUI."""
    script = abs_repo_path / "python/opensim_launcher.py"
    if not script.exists():
        raise FileNotFoundError(f"OpenSim launcher not found: {script}")

    logger.info(f"Launching OpenSim GUI: {script}")
    subprocess.Popen([sys.executable, str(script)], cwd=script.parent)

def _custom_launch_openpose(self, abs_repo_path):
    """Launch OpenPose video processor."""
    script = abs_repo_path / "python/openpose_launcher.py"
    if not script.exists():
        raise FileNotFoundError(f"OpenPose launcher not found: {script}")

    logger.info(f"Launching OpenPose processor: {script}")
    subprocess.Popen([sys.executable, str(script)], cwd=script.parent)

def _custom_launch_pipeline(self, abs_repo_path):
    """Launch complete analysis pipeline GUI."""
    script = self.REPOS_ROOT / "launchers" / "pipeline_launcher.py"
    if not script.exists():
        raise FileNotFoundError(f"Pipeline launcher not found: {script}")

    logger.info(f"Launching analysis pipeline: {script}")
    subprocess.Popen([sys.executable, str(script)], cwd=script.parent)

def launch_simulation(self):
    """Launch the selected simulation."""
    # ... existing code ...

    # Update custom launchers dict
    custom_launchers = {
        "MuJoCo Humanoid": self._custom_launch_humanoid,
        "MuJoCo Dashboard": self._custom_launch_comprehensive,
        "OpenSim Musculoskeletal": self._custom_launch_opensim,  # NEW
        "OpenPose Motion Capture": self._custom_launch_openpose,  # NEW
        "Complete Analysis Pipeline": self._custom_launch_pipeline,  # NEW
    }

    launcher = custom_launchers.get(model_name)
    if launcher:
        launcher(abs_repo_path)
    else:
        self._launch_docker_container(model_name, abs_repo_path)
```

## Organized Grid Layout

Update the grid to group engines by category:

```python
# In GolfLauncher.init_ui()

# Organize models by category
physics_models = [
    "MuJoCo Humanoid", "MuJoCo Dashboard",
    "Drake Golf Model", "Pinocchio Golf Model"
]

biomech_models = [
    "OpenSim Musculoskeletal", "MyoSim Muscle Fiber"
]

input_models = [
    "OpenPose Motion Capture"
]

pipeline_models = [
    "Complete Analysis Pipeline"
]

# Create categorized grid
row, col = 0, 0

# Add section header
lbl_physics = QLabel("Physics Engines")
lbl_physics.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
self.grid_layout.addWidget(lbl_physics, row, 0, 1, GRID_COLUMNS)
row += 1

# Add physics models
for name in physics_models:
    card = self.create_model_card(name)
    self.model_cards[name] = card
    self.grid_layout.addWidget(card, row, col)
    col += 1
    if col >= GRID_COLUMNS:
        col = 0
        row += 1

# Reset for next section
if col != 0:
    col = 0
    row += 1

# Biomechanics section
lbl_biomech = QLabel("Biomechanics Engines")
lbl_biomech.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
self.grid_layout.addWidget(lbl_biomech, row, 0, 1, GRID_COLUMNS)
row += 1

for name in biomech_models:
    card = self.create_model_card(name)
    self.model_cards[name] = card
    self.grid_layout.addWidget(card, row, col)
    col += 1
    if col >= GRID_COLUMNS:
        col = 0
        row += 1

# ... continue for other categories ...
```

## Simple Launcher Scripts

### engines/biomechanics_engines/opensim/python/opensim_launcher.py

```python
#!/usr/bin/env python3
"""Simple OpenSim launcher GUI."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class OpenSimLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenSim Musculoskeletal Analysis")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        btn_ik = QPushButton("Run Inverse Kinematics")
        btn_ik.clicked.connect(self.run_ik)
        layout.addWidget(btn_ik)

        btn_id = QPushButton("Run Inverse Dynamics")
        btn_id.clicked.connect(self.run_id)
        layout.addWidget(btn_id)

        btn_muscle = QPushButton("Analyze Muscles")
        btn_muscle.clicked.connect(self.run_muscle_analysis)
        layout.addWidget(btn_muscle)

    def run_ik(self):
        print("Running inverse kinematics...")
        # Implementation

    def run_id(self):
        print("Running inverse dynamics...")
        # Implementation

    def run_muscle_analysis(self):
        print("Running muscle analysis...")
        # Implementation

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenSimLauncher()
    window.show()
    sys.exit(app.exec())
```

### engines/input_processing/openpose/python/openpose_launcher.py

```python
#!/usr/bin/env python3
"""Simple OpenPose launcher GUI."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QFileDialog, QLabel
)

class OpenPoseLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenPose Motion Capture")
        self.resize(800, 600)
        self.video_path = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.lbl_video = QLabel("No video selected")
        layout.addWidget(self.lbl_video)

        btn_select = QPushButton("Select Video")
        btn_select.clicked.connect(self.select_video)
        layout.addWidget(btn_select)

        btn_process = QPushButton("Extract Pose")
        btn_process.clicked.connect(self.process_video)
        layout.addWidget(btn_process)

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mp4 *.avi *.mov)"
        )
        if path:
            self.video_path = Path(path)
            self.lbl_video.setText(f"Selected: {self.video_path.name}")

    def process_video(self):
        if not self.video_path:
            return
        print(f"Processing video: {self.video_path}")
        # Implementation

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpenPoseLauncher()
    window.show()
    sys.exit(app.exec())
```

### launchers/pipeline_launcher.py

```python
#!/usr/bin/env python3
"""Complete analysis pipeline launcher."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QCheckBox, QPushButton, QFileDialog, QLabel, QGroupBox
)

from shared.python.engine_manager import EngineManager
from shared.python.pipeline_manager import AnalysisPipeline, PipelineConfig

class PipelineLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Complete Golf Analysis Pipeline")
        self.resize(900, 700)
        self.video_path = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # File selection
        self.lbl_file = QLabel("No video selected")
        layout.addWidget(self.lbl_file)

        btn_select = QPushButton("Select Golf Swing Video")
        btn_select.clicked.connect(self.select_video)
        layout.addWidget(btn_select)

        # Pipeline stages
        stages_group = QGroupBox("Analysis Stages")
        stages_layout = QVBoxLayout()

        self.chk_openpose = QCheckBox("1. OpenPose (Pose Estimation)")
        self.chk_openpose.setChecked(True)
        stages_layout.addWidget(self.chk_openpose)

        self.chk_opensim = QCheckBox("2. OpenSim (Biomechanics)")
        self.chk_opensim.setChecked(True)
        stages_layout.addWidget(self.chk_opensim)

        self.chk_myosim = QCheckBox("3. MyoSim (Muscle Fibers)")
        stages_layout.addWidget(self.chk_myosim)

        self.chk_physics = QCheckBox("4. MuJoCo (Physics Validation)")
        stages_layout.addWidget(self.chk_physics)

        stages_group.setLayout(stages_layout)
        layout.addWidget(stages_group)

        # Run button
        btn_run = QPushButton("Run Complete Analysis")
        btn_run.clicked.connect(self.run_pipeline)
        layout.addWidget(btn_run)

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "",
            "Video Files (*.mp4 *.avi *.mov)"
        )
        if path:
            self.video_path = Path(path)
            self.lbl_file.setText(f"Selected: {self.video_path.name}")

    def run_pipeline(self):
        if not self.video_path:
            return

        # Create configuration
        config = PipelineConfig(
            use_openpose=self.chk_openpose.isChecked(),
            use_opensim=self.chk_opensim.isChecked(),
            use_myosim=self.chk_myosim.isChecked(),
            use_physics_engine=self.chk_physics.isChecked(),
        )

        # Run pipeline
        engine_mgr = EngineManager()
        pipeline = AnalysisPipeline(engine_mgr)

        print("Running analysis pipeline...")
        results = pipeline.run_full_pipeline(self.video_path, config)

        if results.success:
            print("✓ Analysis complete!")
        else:
            print(f"✗ Analysis failed: {results.errors}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PipelineLauncher()
    window.show()
    sys.exit(app.exec())
```

## Summary

**Integration Steps:**

1. ✅ Add engine paths to `MODELS_DICT`
2. ✅ Add images to `MODEL_IMAGES`
3. ✅ Add descriptions to `MODEL_DESCRIPTIONS`
4. ✅ Create custom launch methods
5. ✅ Organize grid by category (optional)
6. ✅ Create simple launcher scripts

**Result:** Users can launch OpenPose, OpenSim, MyoSim, and complete pipelines directly from the main GUI!
