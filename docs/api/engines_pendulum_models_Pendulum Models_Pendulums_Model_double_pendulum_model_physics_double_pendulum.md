# engines.pendulum_models.Pendulum Models.Pendulums_Model.double_pendulum_model.physics.double_pendulum

Driven double pendulum dynamics with control-affine structure.

This module models a two-link planar manipulator (shoulder + wrist) swinging on a
user-specified plane (e.g., a golf swing plane). It exposes control-affine
dynamics, supports arbitrary user forcing functions, and reports joint torques
for educational demonstrations of chaos and control.

## Classes

### ExpressionFunction

Safe evaluation of user-provided expressions.

The expression can use standard math functions, state variables, and time
(``t``). Only a curated subset of ``ast`` nodes are accepted to prevent
arbitrary code execution.

#### Methods

### SegmentProperties

Physical properties of a single pendulum segment.

#### Methods

##### center_of_mass_distance
```python
def center_of_mass_distance(self: Any) -> float
```

##### inertia_about_proximal_joint
```python
def inertia_about_proximal_joint(self: Any) -> float
```

### LowerSegmentProperties

Composite properties for a golf-club-like lower segment.

#### Methods

##### total_mass
```python
def total_mass(self: Any) -> float
```

##### center_of_mass_distance
```python
def center_of_mass_distance(self: Any) -> float
```

##### inertia_about_com
```python
def inertia_about_com(self: Any) -> float
```

##### inertia_about_proximal_joint
```python
def inertia_about_proximal_joint(self: Any) -> float
```

### DoublePendulumParameters

Configuration for the double pendulum.

#### Methods

##### default
```python
def default(cls: Any) -> DoublePendulumParameters
```

##### plane_inclination_rad
```python
def plane_inclination_rad(self: Any) -> float
```

##### projected_gravity
```python
def projected_gravity(self: Any) -> float
```

### DoublePendulumState

Dynamic state of the pendulum.

### JointTorques

Torque decomposition at the joints.

### DoublePendulumDynamics

Control-affine driven double pendulum.

#### Methods

##### mass_matrix
```python
def mass_matrix(self: Any, theta2: float) -> tuple[Any]
```

##### coriolis_vector
```python
def coriolis_vector(self: Any, theta2: float, omega1: float, omega2: float) -> tuple[Any]
```

##### gravity_vector
```python
def gravity_vector(self: Any, theta1: float, theta2: float) -> tuple[Any]
```

##### damping_vector
```python
def damping_vector(self: Any, omega1: float, omega2: float) -> tuple[Any]
```

##### control_affine
```python
def control_affine(self: Any, state: DoublePendulumState) -> tuple[Any]
```

##### applied_torques
```python
def applied_torques(self: Any, t: float, state: DoublePendulumState) -> tuple[Any]
```

##### inverse_dynamics
```python
def inverse_dynamics(self: Any, state: DoublePendulumState, accelerations: tuple[Any]) -> tuple[Any]
```

Compute joint torques required to realize the provided accelerations.

##### joint_torque_breakdown
```python
def joint_torque_breakdown(self: Any, state: DoublePendulumState, control: tuple[Any]) -> JointTorques
```

##### derivatives
```python
def derivatives(self: Any, t: float, state: DoublePendulumState) -> tuple[Any]
```

##### step
```python
def step(self: Any, t: float, state: DoublePendulumState, dt: float) -> DoublePendulumState
```

## Constants

- `GRAVITATIONAL_ACCELERATION`
- `DEFAULT_ARM_LENGTH_M`
- `DEFAULT_ARM_MASS_KG`
- `DEFAULT_ARM_CENTER_OF_MASS_RATIO`
- `DEFAULT_ARM_INERTIA_SCALING`
- `DEFAULT_SHAFT_LENGTH_M`
- `DEFAULT_SHAFT_MASS_KG`
- `DEFAULT_CLUBHEAD_MASS_KG`
- `DEFAULT_SHAFT_COM_RATIO`
- `DEFAULT_PLANE_INCLINATION_DEG`
- `DEFAULT_DAMPING_SHOULDER`
- `DEFAULT_DAMPING_WRIST`
- `MASS_MATRIX_SINGULAR_TOLERANCE`
- `_ALLOWED_NODES`
- `_ALLOWED_NAMES`
