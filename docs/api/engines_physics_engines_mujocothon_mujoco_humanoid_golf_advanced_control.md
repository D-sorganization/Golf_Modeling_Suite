# engines.physics_engines.mujocothon.mujoco_humanoid_golf.advanced_control

Advanced control schemes for robotics applications.

This module implements state-of-the-art control strategies including:
- Impedance control (position-based)
- Admittance control (force-based)
- Hybrid force-position control
- Computed torque control (inverse dynamics)
- Task-space control with nullspace projection
- Operational space control

## Classes

### ControlMode

Control mode enumeration.

**Inherits from:** Enum

### ImpedanceParameters

Parameters for impedance control.

#### Methods

##### as_matrices
```python
def as_matrices(self: Any, dim: int) -> tuple[Any]
```

Convert to full matrices.

Args:
    dim: Dimension of control space

Returns:
    Tuple of (K_matrix, D_matrix, M_matrix)

### HybridControlMask

Mask for hybrid force-position control.

For each DOF: True = force control, False = position control

#### Methods

##### get_position_mask
```python
def get_position_mask(self: Any) -> np.ndarray
```

Get complementary position control mask.

##### get_force_selection_matrix
```python
def get_force_selection_matrix(self: Any) -> np.ndarray
```

Get force selection matrix S_f.

##### get_position_selection_matrix
```python
def get_position_selection_matrix(self: Any) -> np.ndarray
```

Get position selection matrix S_p.

### AdvancedController

Advanced controller implementing multiple control strategies.

This controller provides professional-grade control schemes used in
industrial robotics and research applications.

#### Methods

##### set_control_mode
```python
def set_control_mode(self: Any, mode: ControlMode) -> None
```

Set control mode.

Args:
    mode: Desired control mode

##### set_impedance_parameters
```python
def set_impedance_parameters(self: Any, params: ImpedanceParameters) -> None
```

Set impedance control parameters.

Args:
    params: Impedance parameters

##### set_hybrid_mask
```python
def set_hybrid_mask(self: Any, mask: HybridControlMask) -> None
```

Set hybrid force-position control mask.

Args:
    mask: Hybrid control mask

##### compute_control
```python
def compute_control(self: Any, target_position: Any, target_velocity: Any, target_force: Any, feedforward_torque: Any) -> np.ndarray
```

Compute control torques based on current mode.

Args:
    target_position: Desired position [nv] or task space [m]
    target_velocity: Desired velocity [nv] or task space [m]
    target_force: Desired force/torque [nv] or task space [m]
    feedforward_torque: Feedforward torque [nv]

Returns:
    Control torques [nu]

##### compute_operational_space_control
```python
def compute_operational_space_control(self: Any, target_position: np.ndarray, target_velocity: np.ndarray, target_acceleration: np.ndarray, body_id: int) -> np.ndarray
```

Compute operational space control (OSC).

OSC is an advanced task-space controller that accounts for
the configuration-dependent inertia:

F = Λ(q)(ẍ_d + K_d ė + K_p e) + μ(q,q̇) + p(q)
τ = J^T F + N^T τ_posture

where Λ is task-space inertia.

Args:
    target_position: Desired end-effector position [3]
    target_velocity: Desired end-effector velocity [3]
    target_acceleration: Desired end-effector acceleration [3]
    body_id: Body ID for end-effector

Returns:
    Control torques [nu]

### TrajectoryGenerator

Generate smooth trajectories for control.

Useful for generating reference trajectories for controllers.

#### Methods

##### minimum_jerk_trajectory
```python
def minimum_jerk_trajectory(start: np.ndarray, goal: np.ndarray, duration: float, dt: float) -> tuple[Any]
```

Generate minimum jerk trajectory.

Minimum jerk trajectories are smooth and human-like.

Args:
    start: Starting position [n]
    goal: Goal position [n]
    duration: Trajectory duration [s]
    dt: Time step [s]

Returns:
    Tuple of (positions, velocities, accelerations)
    Each is [num_steps x n]

##### quintic_spline
```python
def quintic_spline(waypoints: np.ndarray, duration: float, dt: float) -> tuple[Any]
```

Generate quintic spline through waypoints.

Args:
    waypoints: Waypoints [num_waypoints x n]
    duration: Total trajectory duration [s]
    dt: Time step [s]

Returns:
    Tuple of (positions, velocities, accelerations)

## Constants

- `TORQUE`
- `IMPEDANCE`
- `ADMITTANCE`
- `HYBRID`
- `COMPUTED_TORQUE`
- `TASK_SPACE`
