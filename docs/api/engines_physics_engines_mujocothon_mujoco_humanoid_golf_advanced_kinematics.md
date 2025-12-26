# engines.physics_engines.mujocothon.mujoco_humanoid_golf.advanced_kinematics

Advanced kinematics analysis for parallel mechanisms and redundant manipulators.

This module provides state-of-the-art robotics analysis tools including:
- Constraint Jacobian analysis for closed-chain systems
- Manipulability and singularity analysis
- Inverse kinematics solvers
- Task-space control frameworks
- Nullspace projection for redundancy resolution

## Classes

### ManipulabilityMetrics

Metrics for manipulability analysis.

### ConstraintJacobianData

Data structure for constraint Jacobian analysis.

### AdvancedKinematicsAnalyzer

Advanced kinematics analysis for robotics applications.

This class provides professional-grade robotics analysis tools for:
- Parallel mechanisms (golf swing has closed-chain constraints)
- Manipulability and singularity analysis
- Inverse kinematics
- Task-space control

#### Methods

##### compute_body_jacobian
```python
def compute_body_jacobian(self: Any, body_id: int, point_offset: Any) -> tuple[Any]
```

Compute Jacobian for a body (or point on body).

Args:
    body_id: ID of the body
    point_offset: Offset from body frame origin (default: [0,0,0])

Returns:
    Tuple of (position_jacobian [3 x nv], rotation_jacobian [3 x nv])

##### compute_constraint_jacobian
```python
def compute_constraint_jacobian(self: Any) -> ConstraintJacobianData
```

Compute constraint Jacobian for closed-chain analysis.

For golf swing: Two hands on club creates a closed kinematic chain.
This is a parallel mechanism requiring constraint analysis.

Returns:
    ConstraintJacobianData with constraint analysis

##### compute_manipulability
```python
def compute_manipulability(self: Any, jacobian: np.ndarray, metric_type: str) -> ManipulabilityMetrics
```

Compute manipulability metrics for singularity analysis.

Args:
    jacobian: Jacobian matrix (m x n)
    metric_type: Type of metric ("yoshikawa" or "condition")

Returns:
    ManipulabilityMetrics with comprehensive analysis

##### solve_inverse_kinematics
```python
def solve_inverse_kinematics(self: Any, target_body_id: int, target_position: np.ndarray, target_orientation: Any, q_init: Any, nullspace_objective: Any) -> tuple[Any]
```

Solve inverse kinematics using Damped Least-Squares (DLS).

This is a professional-grade IK solver with:
- Damped least-squares for singularity robustness
- Nullspace projection for redundancy resolution
- Joint limit avoidance

Args:
    target_body_id: Body to position
    target_position: Desired position [3]
    target_orientation: Desired orientation quaternion [4] (optional)
    q_init: Initial joint configuration (default: current state)
    nullspace_objective: Desired nullspace configuration (default: current)

Returns:
    Tuple of (joint_config, success, iterations)

##### compute_manipulability_ellipsoid
```python
def compute_manipulability_ellipsoid(self: Any, body_id: int, scaling: float) -> tuple[Any]
```

Compute manipulability ellipsoid for visualization.

The manipulability ellipsoid shows the directional manipulability
of the end-effector.

Args:
    body_id: Body to analyze
    scaling: Scaling factor for ellipsoid size

Returns:
    Tuple of (center [3], radii [3], axes [3x3])

##### analyze_singularities
```python
def analyze_singularities(self: Any, body_id: int, q_samples: Any, num_samples: int) -> tuple[Any]
```

Analyze workspace for singularities.

Args:
    body_id: Body to analyze
    q_samples: Joint configurations to sample (default: random)
    num_samples: Number of samples if q_samples not provided

Returns:
    Tuple of (singular_configs, condition_numbers)

##### compute_nullspace_projection
```python
def compute_nullspace_projection(self: Any, jacobian: np.ndarray) -> np.ndarray
```

Compute nullspace projection matrix.

P_null = I - J^+ J

This projects vectors into the nullspace of J, useful for
redundancy resolution.

Args:
    jacobian: Jacobian matrix [m x n]

Returns:
    Nullspace projection matrix [n x n]

##### compute_task_space_inertia
```python
def compute_task_space_inertia(self: Any, jacobian: np.ndarray) -> np.ndarray
```

Compute task-space inertia matrix.

Λ = (J M^{-1} J^T)^{-1}

This is important for task-space control.

Args:
    jacobian: Jacobian matrix [m x n]

Returns:
    Task-space inertia matrix [m x m]

## Constants

- `J`
