# engines.physics_engines.mujocothon.mujoco_humanoid_golf.control_system

Advanced control system for golf swing simulation.

Supports multiple control types including constant, polynomial, and time-based controls.

## Classes

### ControlType

Types of control inputs.

**Inherits from:** Enum

### ActuatorControl

Control configuration for a single actuator.

Supports multiple control types with parameters for each type.

#### Methods

##### compute_torque
```python
def compute_torque(self: Any, time: float, velocity: float) -> float
```

Compute control torque at given time.

Args:
    time: Current simulation time (seconds)
    velocity: Current joint velocity (for damping)

Returns:
    Control torque value

##### get_polynomial_coeffs
```python
def get_polynomial_coeffs(self: Any) -> np.ndarray
```

Get polynomial coefficients.

##### set_polynomial_coeffs
```python
def set_polynomial_coeffs(self: Any, coeffs: np.ndarray) -> None
```

Set polynomial coefficients.

### ControlSystem

Advanced control system managing all actuators.

Supports multiple control types per actuator, time-based evaluation,
and damping controls.

#### Methods

##### set_control_type
```python
def set_control_type(self: Any, actuator_index: int, control_type: ControlType) -> None
```

Set control type for an actuator.

Args:
    actuator_index: Index of actuator (0-based)
    control_type: Type of control to use

##### set_constant_value
```python
def set_constant_value(self: Any, actuator_index: int, value: float) -> None
```

Set constant value for an actuator.

Args:
    actuator_index: Index of actuator
    value: Constant torque value

##### set_polynomial_coeffs
```python
def set_polynomial_coeffs(self: Any, actuator_index: int, coeffs: np.ndarray) -> None
```

Set polynomial coefficients for an actuator.

Args:
    actuator_index: Index of actuator
    coeffs: Array of POLYNOMIAL_COEFFS_COUNT coefficients
        [c0, c1, c2, c3, c4, c5, c6]

##### set_damping
```python
def set_damping(self: Any, actuator_index: int, damping: float) -> None
```

Set damping coefficient for an actuator.

Args:
    actuator_index: Index of actuator
    damping: Damping coefficient (applied as -damping * velocity)

##### set_sine_wave_params
```python
def set_sine_wave_params(self: Any, actuator_index: int, amplitude: float, frequency: float, phase: float) -> None
```

Set sine wave parameters for an actuator.

Args:
    actuator_index: Index of actuator
    amplitude: Amplitude of sine wave
    frequency: Frequency in Hz
    phase: Phase offset in radians

##### set_step_params
```python
def set_step_params(self: Any, actuator_index: int, step_time: float, step_value: float) -> None
```

Set step function parameters for an actuator.

Args:
    actuator_index: Index of actuator
    step_time: Time at which step occurs
    step_value: Value after step

##### compute_control_vector
```python
def compute_control_vector(self: Any, velocities: Any) -> np.ndarray
```

Compute control torques for all actuators.

Args:
    velocities: Current joint velocities [nv] (optional, for damping)

Returns:
    Control torque vector [nu]

##### update_time
```python
def update_time(self: Any, time: float) -> None
```

Update simulation time.

Args:
    time: Current simulation time

##### advance_time
```python
def advance_time(self: Any, dt: float) -> None
```

Advance simulation time by dt.

Args:
    dt: Time step

##### reset
```python
def reset(self: Any) -> None
```

Reset control system (reset time to 0).

##### get_actuator_control
```python
def get_actuator_control(self: Any, actuator_index: int) -> ActuatorControl
```

Get control configuration for an actuator.

Args:
    actuator_index: Index of actuator

Returns:
    ActuatorControl object

##### export_coefficients
```python
def export_coefficients(self: Any) -> dict
```

Export all polynomial coefficients for optimization.

Returns:
    Dictionary mapping actuator indices to coefficient arrays

##### import_coefficients
```python
def import_coefficients(self: Any, coeffs_dict: dict) -> None
```

Import polynomial coefficients from optimization.

Args:
    coeffs_dict: Dictionary mapping actuator indices to coefficient arrays

## Constants

- `POLYNOMIAL_ORDER`
- `POLYNOMIAL_COEFFS_COUNT`
- `CONSTANT`
- `POLYNOMIAL`
- `SINE_WAVE`
- `STEP`
