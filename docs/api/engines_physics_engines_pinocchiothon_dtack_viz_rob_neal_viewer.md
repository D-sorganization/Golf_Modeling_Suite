# engines.physics_engines.pinocchiothon.dtack.viz.rob_neal_viewer

Python wrapper for Rob Neal club data visualization.

This module provides visualization capabilities for Rob Neal golf club data,
inspired by the MATLAB ClubDataGUI_v2.m functionality.

Features:
- Load .mat files with club data
- 3D visualization of club shaft and hands
- Playback controls
- Velocity/acceleration vector visualization
- Multiple view angles (isometric, face-on, down-the-line, top-down)
- Trace visualization

## Classes

### RobNealDataViewer

Visualize Rob Neal golf club data in MeshCat.

This viewer loads .mat files containing club motion data and displays
them in an interactive 3D viewer with playback controls.

#### Methods

##### load_data
```python
def load_data(self: Any, mat_file: Any) -> None
```

Load Rob Neal .mat file.

Args:
    mat_file: Path to .mat file containing 'data' and 'params' structures

Raises:
    FileNotFoundError: If file does not exist
    ValueError: If file doesn't contain required structures

##### visualize_frame
```python
def visualize_frame(self: Any, frame: int, show_trace: bool, show_velocity: bool, show_acceleration: bool) -> None
```

Visualize a single frame of data.

Args:
    frame: Frame index (0-based)
    show_trace: Whether to show trajectory trace
    show_velocity: Whether to show velocity vectors
    show_acceleration: Whether to show acceleration vectors

##### set_view
```python
def set_view(self: Any, view_type: str) -> None
```

Set camera view angle.

Args:
    view_type: One of 'isometric', 'face-on', 'down-the-line', 'top-down'

##### close
```python
def close(self: Any) -> None
```

Close viewer.

## Constants

- `SCIPY_AVAILABLE`
- `MESHCAT_AVAILABLE`
- `SCIPY_AVAILABLE`
- `MESHCAT_AVAILABLE`
