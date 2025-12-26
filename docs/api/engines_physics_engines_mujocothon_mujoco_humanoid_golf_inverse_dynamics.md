# engines.physics_engines.mujocothon.mujoco_humanoid_golf.inverse_dynamics

Inverse dynamics computation for golf swing analysis.

This module provides inverse dynamics solvers for computing required joint
torques from desired motion. Includes:

- Full inverse dynamics for open-chain systems
- Partial inverse dynamics for parallel mechanisms (closed-chain)
- Recursive Newton-Euler algorithm
- Composite rigid body algorithm
- Force decomposition analysis

## Classes

### InducedAccelerationResult

Result of induced acceleration analysis.

### InverseDynamicsResult

Result of inverse dynamics computation.

### ForceDecomposition

Decomposition of forces/torques into components.

### InverseDynamicsSolver

Solve inverse dynamics for golf swing models.

This class computes the joint torques required to achieve a desired
motion trajectory. Handles both open-chain and closed-chain (parallel
mechanism) systems.

Key Methods:
- solve_inverse_dynamics(): Main method for full trajectory
- compute_required_torques(): Single time step
- decompose_forces(): Break down torques into components

#### Methods

##### compute_required_torques
```python
def compute_required_torques(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray, external_forces: Any) -> InverseDynamicsResult
```

Compute required joint torques for desired motion.

Uses the equation of motion:
M(q)q̈ + C(q,q̇)q̇ + g(q) = τ + τ_ext

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]
    external_forces: External forces [nv] (optional)

Returns:
    InverseDynamicsResult with computed torques

##### compute_induced_accelerations
```python
def compute_induced_accelerations(self: Any, qpos: np.ndarray, qvel: np.ndarray, ctrl: np.ndarray) -> InducedAccelerationResult
```

Compute acceleration components induced by different forces.

Using M(q)q_ddot = tau - C(q,q_dot)q_dot - G(q)
q_ddot = M^-1 * (tau - C - G)

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    ctrl: Applied control torques [nu] (or nv if full actuation)

Returns:
    InducedAccelerationResult with component accelerations.

##### solve_inverse_dynamics_trajectory
```python
def solve_inverse_dynamics_trajectory(self: Any, times: np.ndarray, positions: np.ndarray, velocities: np.ndarray, accelerations: np.ndarray) -> list[InverseDynamicsResult]
```

Solve inverse dynamics for entire trajectory.

Args:
    times: Time array [N]
    positions: Joint positions [N x nv]
    velocities: Joint velocities [N x nv]
    accelerations: Joint accelerations [N x nv]

Returns:
    List of InverseDynamicsResult for each time step

##### compute_partial_inverse_dynamics
```python
def compute_partial_inverse_dynamics(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray, constrained_joints: list[int]) -> InverseDynamicsResult
```

Compute partial inverse dynamics for parallel mechanisms.

For closed-chain systems, some joints may be constrained.
This computes torques for actuated joints while respecting
constraint forces.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]
    constrained_joints: List of constrained joint indices

Returns:
    InverseDynamicsResult with partial solution

##### decompose_forces
```python
def decompose_forces(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray) -> ForceDecomposition
```

Decompose total forces into components.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]

Returns:
    ForceDecomposition with all components

##### compute_end_effector_forces
```python
def compute_end_effector_forces(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray, body_id: int) -> np.ndarray
```

Compute forces at end-effector (e.g., club head).

Maps joint torques to task-space forces: F = (J^T)^{-1} τ

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]
    body_id: Body ID for end-effector

Returns:
    End-effector force [3]

##### validate_solution
```python
def validate_solution(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray, computed_torques: np.ndarray) -> dict[Any]
```

Validate inverse dynamics solution.

Checks if computed torques actually produce desired acceleration.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Desired accelerations [nv]
    computed_torques: Computed torques [nv]

Returns:
    Validation metrics

##### compute_actuator_efficiency
```python
def compute_actuator_efficiency(self: Any, result: InverseDynamicsResult) -> dict[Any]
```

Compute efficiency metrics for actuators.

Args:
    result: Inverse dynamics result

Returns:
    Efficiency metrics

### RecursiveNewtonEuler

Recursive Newton-Euler algorithm for inverse dynamics.

More efficient than matrix-based approach for serial chains.
Useful for real-time applications.

#### Methods

##### compute
```python
def compute(self: Any, qpos: np.ndarray, qvel: np.ndarray, qacc: np.ndarray) -> np.ndarray
```

Compute inverse dynamics using RNE.

Args:
    qpos: Joint positions [nv]
    qvel: Joint velocities [nv]
    qacc: Joint accelerations [nv]

Returns:
    Joint torques [nv]

### InverseDynamicsAnalyzer

High-level analyzer combining inverse dynamics and kinematic forces.

This class provides the complete analysis pipeline for understanding
swing dynamics from motion capture data.

#### Methods

##### analyze_captured_motion
```python
def analyze_captured_motion(self: Any, times: np.ndarray, positions: np.ndarray, velocities: np.ndarray, accelerations: np.ndarray) -> dict
```

Complete analysis of captured motion.

This is the main method for analyzing motion capture data.
Computes both kinematic forces (Coriolis, centrifugal) and
inverse dynamics (required torques).

Args:
    times: Time array [N]
    positions: Joint positions [N x nv]
    velocities: Joint velocities [N x nv]
    accelerations: Joint accelerations [N x nv]

Returns:
    Dictionary with comprehensive analysis

##### compare_swings
```python
def compare_swings(self: Any, swing1_data: dict, swing2_data: dict) -> dict
```

Compare two swing analyses.

Args:
    swing1_data: First swing analysis
    swing2_data: Second swing analysis

Returns:
    Comparison metrics
