# engines.physics_engines.mujocothon.mujoco_humanoid_golf.biomechanics

Biomechanical analysis module for golf swing simulations.

This module provides comprehensive force, torque, and kinematic analysis
for golf swing models. It extracts data from MuJoCo simulations and computes
derived biomechanical quantities.

## Classes

### BiomechanicalAnalyzer

Analyzes MuJoCo simulation data for biomechanical insights.

This class extracts forces, torques, kinematics, and energetics
from a MuJoCo model and data structure.

Attributes:
    _prev_club_vel: Previous club velocity for acceleration calculation.
        Initialized to None and updated during state extraction.

#### Methods

##### compute_joint_accelerations
```python
def compute_joint_accelerations(self: Any) -> np.ndarray
```

Compute joint accelerations using finite differences.

Returns:
    Array of joint accelerations [rad/s^2 or m/s^2]

##### get_club_head_data
```python
def get_club_head_data(self: Any) -> tuple[Any]
```

Get club head position, velocity, and speed.

Returns:
    Tuple of (position [3], velocity [3], speed [m/s])
    Returns (None, None, 0.0) if club head not found

##### get_ground_reaction_forces
```python
def get_ground_reaction_forces(self: Any) -> tuple[Any]
```

Get ground reaction forces for left and right feet.

Returns:
    Tuple of (left_foot_force [3], right_foot_force [3])
    Returns (None, None) if feet not found or no contacts

##### get_center_of_mass
```python
def get_center_of_mass(self: Any) -> tuple[Any]
```

Get center of mass position and velocity.

Returns:
    Tuple of (position [3], velocity [3])

##### compute_energies
```python
def compute_energies(self: Any) -> tuple[Any]
```

Compute kinetic, potential, and total energy.

Returns:
    Tuple of (kinetic_energy [J], potential_energy [J], total_energy [J])

##### get_actuator_powers
```python
def get_actuator_powers(self: Any) -> np.ndarray
```

Compute mechanical power for each actuator.

Power = torque * angular_velocity (or force * linear_velocity)

Returns:
    Array of actuator powers [W]

##### extract_full_state
```python
def extract_full_state(self: Any) -> BiomechanicalData
```

Extract complete biomechanical state at current time.

Returns:
    BiomechanicalData object with all available measurements

### SwingRecorder

Records time-series biomechanical data during a golf swing.

This class accumulates BiomechanicalData snapshots over time
for later analysis and visualization.

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

##### record_frame
```python
def record_frame(self: Any, data: BiomechanicalData) -> None
```

Add a frame of data to the recording.

Args:
    data: BiomechanicalData snapshot to record

##### get_time_series
```python
def get_time_series(self: Any, field_name: str) -> tuple[Any]
```

Extract time series for a specific field.

Args:
    field_name: Name of the field in BiomechanicalData

Returns:
    Tuple of (times, values) where values may be 1D or 2D array or list

##### get_num_frames
```python
def get_num_frames(self: Any) -> int
```

Get number of recorded frames.

##### get_duration
```python
def get_duration(self: Any) -> float
```

Get duration of recording in seconds.

##### export_to_dict
```python
def export_to_dict(self: Any) -> dict
```

Export all recorded data to a dictionary for JSON/CSV export.

Returns:
    Dictionary with time series for all fields
