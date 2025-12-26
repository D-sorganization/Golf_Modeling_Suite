# engines.physics_engines.mujocothon.mujoco_humanoid_golf.kinematic_forces

Kinematic-dependent force analysis for golf swing biomechanics.

This module computes motion-dependent forces that can be calculated from
kinematics alone, WITHOUT requiring full inverse dynamics:

- Coriolis forces
- Centrifugal forces
- Centripetal accelerations
- Velocity-dependent forces
- Gravitational forces (configuration-dependent)

These forces are critical for understanding swing dynamics and can be computed
even for parallel mechanisms where full inverse dynamics is challenging.

## Classes

### KinematicForceData

Container for kinematic-dependent forces at a single time point.

### KinematicForceAnalyzer

Analyze kinematic-dependent forces in golf swing.

This class computes Coriolis, centrifugal, and other velocity-dependent
forces that can be determined from kinematics alone. These forces are
essential for understanding swing dynamics without requiring full
inverse dynamics.

Key Applications:
- Analyze forces in captured motion data (from motion capture)
- Understand velocity-dependent effects
- Study energy transfer mechanisms
- Evaluate dynamic coupling between joints

#### Methods

##### compute_coriolis_forces
```python
def compute_coriolis_forces(self: Any, qpos: np.ndarray, qvel: np.ndarray) -> np.ndarray
```

Compute Coriolis and centrifugal forces.

These are the velocity-dependent forces in the equations of motion:
M(q)q̈ + C(q,q̇)q̇ + g(q) = τ

The term C(q,q̇)q̇ represents Coriolis and centrifugal forces.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]

Returns:
    Coriolis forces [nv]

##### compute_gravity_forces
```python
def compute_gravity_forces(self: Any, qpos: np.ndarray) -> np.ndarray
```

Compute gravitational forces.

Args:
    qpos: Joint positions [nv]

Returns:
    Gravity forces [nv]

##### decompose_coriolis_forces
```python
def decompose_coriolis_forces(self: Any, qpos: np.ndarray, qvel: np.ndarray) -> tuple[Any]
```

Decompose Coriolis forces into centrifugal and velocity coupling.

Coriolis matrix C(q,q̇) can be decomposed:
- Centrifugal terms: Diagonal terms (q̇ᵢ²)
- Velocity coupling: Off-diagonal terms (q̇ᵢq̇ⱼ)

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]

Returns:
    Tuple of (centrifugal_forces [nv], coupling_forces [nv])

##### compute_mass_matrix
```python
def compute_mass_matrix(self: Any, qpos: np.ndarray) -> np.ndarray
```

Compute configuration-dependent mass matrix M(q).

Args:
    qpos: Joint positions [nv]

Returns:
    Mass matrix [nv x nv]

##### compute_coriolis_matrix
```python
def compute_coriolis_matrix(self: Any, qpos: np.ndarray, qvel: np.ndarray) -> np.ndarray
```

Compute Coriolis matrix C(q,q̇).

The Coriolis matrix satisfies: C(q,q̇)q̇ = coriolis forces

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]

Returns:
    Coriolis matrix [nv x nv]

##### compute_club_head_apparent_forces
```python
def compute_club_head_apparent_forces(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray) -> tuple[Any]
```

Compute apparent forces at club head (Coriolis, centrifugal, etc.).

These are the "fictitious" forces experienced in the rotating
reference frame attached to the golfer.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]

Returns:
    Tuple of (coriolis_force [3], centrifugal_force [3], total_apparent [3])

##### compute_kinematic_power
```python
def compute_kinematic_power(self: Any, qpos: np.ndarray, qvel: np.ndarray) -> dict[Any]
```

Compute power contributions from kinematic forces.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]

Returns:
    Dictionary with power contributions

##### compute_kinetic_energy_components
```python
def compute_kinetic_energy_components(self: Any, qpos: np.ndarray, qvel: np.ndarray) -> dict[Any]
```

Decompose kinetic energy into rotational and translational.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]

Returns:
    Dictionary with kinetic energy components

##### analyze_trajectory
```python
def analyze_trajectory(self: Any, times: np.ndarray, positions: np.ndarray, velocities: np.ndarray, accelerations: np.ndarray) -> list[KinematicForceData]
```

Analyze kinematic forces along a trajectory.

This is the main function for analyzing captured motion data.

Args:
    times: Time array [N]
    positions: Joint positions [N x nv]
    velocities: Joint velocities [N x nv]
    accelerations: Joint accelerations [N x nv]

Returns:
    List of KinematicForceData for each time step

##### compute_effective_mass
```python
def compute_effective_mass(self: Any, qpos: np.ndarray, direction: np.ndarray, body_id: Any) -> float
```

Compute effective mass in a given direction.

Effective mass determines how difficult it is to accelerate
in a specific direction.

Args:
    qpos: Joint positions [nv]
    direction: Direction vector [3]
    body_id: Body to compute for (default: club head)

Returns:
    Effective mass in that direction [kg]

##### compute_centripetal_acceleration
```python
def compute_centripetal_acceleration(self: Any, qpos: np.ndarray, qvel: np.ndarray, body_id: Any) -> np.ndarray
```

Compute centripetal acceleration at a body.

Centripetal acceleration = v²/r pointing toward center of rotation

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    body_id: Body ID (default: club head)

Returns:
    Centripetal acceleration [3]

## Constants

- `M`
- `C`
- `M`
