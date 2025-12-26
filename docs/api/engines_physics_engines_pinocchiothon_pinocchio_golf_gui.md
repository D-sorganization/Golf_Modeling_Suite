# engines.physics_engines.pinocchiothon.pinocchio_golf.gui

Pinocchio GUI Wrapper (PyQt6 + meshcat).

## Classes

### LogPanel

Log panel widget for displaying messages.

**Inherits from:** QtWidgets.QTextEdit

#### Methods

### SignalBlocker

Context manager to block signals for a set of widgets.

#### Methods

### PinocchioRecorder

Records time-series data from Pinocchio simulation.

#### Methods

##### reset
```python
def reset(self: Any) -> None
```

Clear all recorded data.

##### start_recording
```python
def start_recording(self: Any) -> None
```

Start recording data.

##### stop_recording
```python
def stop_recording(self: Any) -> None
```

Stop recording data.

##### get_num_frames
```python
def get_num_frames(self: Any) -> int
```

Get number of recorded frames.

##### record_frame
```python
def record_frame(self: Any, time: float, q: np.ndarray, v: np.ndarray, tau: Any, kinetic_energy: float, potential_energy: float, club_head_position: Any, club_head_velocity: Any) -> None
```

Add a frame of data to the recording.

Args:
    time: Current simulation time
    q: Joint positions
    v: Joint velocities
    tau: Joint torques (optional)
    kinetic_energy: System kinetic energy
    potential_energy: System potential energy
    club_head_position: Club head position (3,)
    club_head_velocity: Club head linear velocity (3,)

##### get_time_series
```python
def get_time_series(self: Any, field_name: str) -> tuple[Any]
```

Extract time series for a specific field.

Args:
    field_name: Name of the field in BiomechanicalData

Returns:
    Tuple of (times, values)

### PinocchioGUI

Main GUI widget for Pinocchio robot visualization and computation.

**Inherits from:** QtWidgets.QMainWindow

#### Methods

##### log_write
```python
def log_write(self: Any, text: str) -> None
```

##### load_urdf
```python
def load_urdf(self: Any, fname: Any) -> None
```

## Constants

- `DT_DEFAULT`
- `SLIDER_RANGE_RAD`
- `SLIDER_SCALE`
- `COM_SPHERE_RADIUS`
- `COM_COLOR`
- `J`
- `M`
- `J`
- `M`
- `T`
