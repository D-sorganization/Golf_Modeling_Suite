# engines.physics_engines.mujocothon.mujoco_humanoid_golf.motion_capture

Motion capture integration and retargeting for golf swing analysis.

This module provides comprehensive motion capture data handling, including:
- Loading mocap data from multiple formats (BVH, C3D, CSV, JSON)
- Motion retargeting to MuJoCo models using IK
- Kinematic trajectory extraction and processing
- Marker-based and markerless mocap support
- Temporal alignment and filtering

## Classes

### MotionCaptureFrame

Single frame of motion capture data.

### MotionCaptureSequence

Complete motion capture sequence.

#### Methods

##### num_frames
```python
def num_frames(self: Any) -> int
```

Get number of frames.

##### duration
```python
def duration(self: Any) -> float
```

Get sequence duration in seconds.

##### get_marker_trajectory
```python
def get_marker_trajectory(self: Any, marker_name: str) -> tuple[Any]
```

Get trajectory for a specific marker.

Args:
    marker_name: Name of marker

Returns:
    Tuple of (times [N], positions [N x 3])

### MarkerSet

Marker set configuration for motion capture.

#### Methods

##### golf_swing_marker_set
```python
def golf_swing_marker_set(cls: Any) -> MarkerSet
```

Standard marker set for golf swing capture.

Based on common motion capture protocols for golf biomechanics.

### MotionCaptureLoader

Load motion capture data from various file formats.

#### Methods

##### load_csv
```python
def load_csv(filepath: Any, frame_rate: float, marker_names: Any) -> MotionCaptureSequence
```

Load motion capture data from CSV file.

Expected format:
time, marker1_x, marker1_y, marker1_z, marker2_x, marker2_y, marker2_z, ...

Args:
    filepath: Path to CSV file
    frame_rate: Frame rate in Hz
    marker_names: List of marker names (if None, auto-detect from header)

Returns:
    MotionCaptureSequence

##### load_json
```python
def load_json(filepath: Any) -> MotionCaptureSequence
```

Load motion capture data from JSON file.

Expected format:
{
    "frame_rate": 120.0,
    "marker_names": ["LSHO", "RSHO", ...],
    "frames": [
        {
            "time": 0.0,
            "markers": {
                "LSHO": [x, y, z],
                # ...
                # ...
            }
        },
        # ...
    ]
}

Args:
    filepath: Path to JSON file

Returns:
    MotionCaptureSequence

##### load_bvh
```python
def load_bvh(filepath: Any) -> Any
```

Load motion capture data from BVH file.

BVH (Biovision Hierarchy) is a common format for motion capture.
This is a simplified parser - for production use, consider using
a dedicated BVH library.

Args:
    filepath: Path to BVH file

Returns:
    MotionCaptureSequence

### MotionRetargeting

Retarget motion capture data to MuJoCo model.

This class maps motion capture markers to the model's body positions
and solves inverse kinematics to generate joint trajectories.

#### Methods

##### retarget_sequence
```python
def retarget_sequence(self: Any, mocap_sequence: MotionCaptureSequence, use_markers: Any, ik_iterations: int) -> tuple[Any]
```

Retarget motion capture sequence to model joint trajectories.

Args:
    mocap_sequence: Motion capture sequence
    use_markers: List of markers to use (default: all available)
    ik_iterations: Max IK iterations per frame

Returns:
    Tuple of (times [N], joint_trajectories [N x nv], success_flags [N])

##### compute_marker_errors
```python
def compute_marker_errors(self: Any, frame: MotionCaptureFrame, q: np.ndarray) -> dict[Any]
```

Compute marker position errors for a configuration.

Args:
    frame: Motion capture frame with target marker positions
    q: Joint configuration to evaluate

Returns:
    Dictionary of marker_name -> error (m)

### MotionCaptureProcessor

Process and filter motion capture data.

#### Methods

##### filter_trajectory
```python
def filter_trajectory(times: np.ndarray, positions: np.ndarray, cutoff_frequency: float, sampling_rate: float) -> np.ndarray
```

Apply low-pass Butterworth filter to trajectory.

Args:
    times: Time array [N]
    positions: Position array [N x 3] or [N x nv]
    cutoff_frequency: Cutoff frequency in Hz
    sampling_rate: Sampling rate in Hz

Returns:
    Filtered positions [N x 3] or [N x nv]

##### compute_velocities
```python
def compute_velocities(times: np.ndarray, positions: np.ndarray, method: str) -> np.ndarray
```

Compute velocities from position data.

Args:
    times: Time array [N]
    positions: Position array [N x d]
    method: Method ("finite_difference", "spline")

Returns:
    Velocities [N x d]

##### compute_accelerations
```python
def compute_accelerations(times: np.ndarray, velocities: np.ndarray, method: str) -> np.ndarray
```

Compute accelerations from velocity data.

Args:
    times: Time array [N]
    velocities: Velocity array [N x d]
    method: Method ("finite_difference", "spline")

Returns:
    Accelerations [N x d]

##### resample_trajectory
```python
def resample_trajectory(times: np.ndarray, trajectory: np.ndarray, new_times: np.ndarray, method: str) -> np.ndarray
```

Resample trajectory to new time points.

Args:
    times: Original time array [N]
    trajectory: Original trajectory [N x d]
    new_times: New time points [M]
    method: Interpolation method ("linear", "cubic")

Returns:
    Resampled trajectory [M x d]

##### time_normalize
```python
def time_normalize(times: np.ndarray, trajectory: np.ndarray, num_samples: int) -> tuple[Any]
```

Time-normalize trajectory to 0-100% of motion.

Useful for comparing motions of different durations.

Args:
    times: Time array [N]
    trajectory: Trajectory [N x d]
    num_samples: Number of samples in normalized trajectory

Returns:
    Tuple of (normalized_times [M], normalized_trajectory [M x d])

### MotionCaptureValidator

Validate motion capture data quality.

#### Methods

##### detect_gaps
```python
def detect_gaps(mocap_sequence: MotionCaptureSequence, marker_name: str, gap_threshold: float) -> list[tuple[Any]]
```

Detect gaps in marker trajectory.

Args:
    mocap_sequence: Motion capture sequence
    marker_name: Marker to check
    gap_threshold: Gap threshold in seconds

Returns:
    List of (start_frame, end_frame) for gaps

##### compute_marker_velocity_stats
```python
def compute_marker_velocity_stats(mocap_sequence: MotionCaptureSequence, marker_name: str) -> dict[Any]
```

Compute velocity statistics for marker.

Args:
    mocap_sequence: Motion capture sequence
    marker_name: Marker to analyze

Returns:
    Dictionary with velocity statistics or error message

##### check_marker_visibility
```python
def check_marker_visibility(mocap_sequence: MotionCaptureSequence, marker_name: str) -> dict[Any]
```

Check marker visibility statistics.

Args:
    mocap_sequence: Motion capture sequence
    marker_name: Marker to check

Returns:
    Visibility statistics

## Constants

- `J`
