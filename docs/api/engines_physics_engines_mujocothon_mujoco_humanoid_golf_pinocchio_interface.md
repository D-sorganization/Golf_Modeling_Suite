# engines.physics_engines.mujocothon.mujoco_humanoid_golf.pinocchio_interface

Pinocchio interface for advanced dynamics algorithms.

This module provides a bridge between MuJoCo and Pinocchio, enabling:
- Fast inverse dynamics (RNEA)
- Forward dynamics (ABA)
- Analytical Jacobians and derivatives
- Mass matrix computation
- Trajectory optimization support

Pinocchio is used for analytical dynamics computations while MuJoCo handles
simulation, contacts, and constraints.

Usage:
    >>> from mujoco_humanoid_golf.pinocchio_interface import PinocchioWrapper
    >>> wrapper = PinocchioWrapper(model, data)
    >>> torques = wrapper.compute_inverse_dynamics(q, v, a)
    >>> jacobian = wrapper.compute_end_effector_jacobian(q, "club_head")

## Classes

### PinocchioWrapper

Wrapper for Pinocchio dynamics computations with MuJoCo models.

This class maintains both MuJoCo and Pinocchio representations of the same
model, allowing you to use Pinocchio's fast analytical algorithms while
leveraging MuJoCo for simulation.

Attributes:
    model: MuJoCo model
    data: MuJoCo data
    pin_model: Pinocchio model (built from MuJoCo model)
    pin_data: Pinocchio data

#### Methods

##### sync_mujoco_to_pinocchio
```python
def sync_mujoco_to_pinocchio(self: Any) -> None
```

Synchronize state from MuJoCo to Pinocchio.

This updates Pinocchio's configuration and velocity to match MuJoCo.

##### sync_pinocchio_to_mujoco
```python
def sync_pinocchio_to_mujoco(self: Any) -> None
```

Synchronize state from Pinocchio to MuJoCo.

This updates MuJoCo's configuration to match Pinocchio.
Note: Pinocchio doesn't store configuration state, so this method
maintains MuJoCo's current state. For proper synchronization,
use sync_mujoco_to_pinocchio after updating MuJoCo state.

##### compute_inverse_dynamics
```python
def compute_inverse_dynamics(self: Any, q: Any, v: Any, a: Any) -> np.ndarray
```

Compute inverse dynamics (RNEA) using Pinocchio.

Computes joint torques required to achieve desired accelerations.

Args:
    q: Joint positions (if None, uses current MuJoCo state)
    v: Joint velocities (if None, uses current MuJoCo state)
    a: Joint accelerations (required)

Returns:
    Joint torques [nq]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> # Option 1: Use None to auto-convert from MuJoCo state
    >>> a = np.zeros(model.nv)
    >>> torques = wrapper.compute_inverse_dynamics(None, None, a)
    >>> # Option 2: Manually convert quaternions if passing q explicitly
    >>> q = wrapper._mujoco_q_to_pinocchio_q(data.qpos.copy())
    >>> v = data.qvel.copy()
    >>> torques = wrapper.compute_inverse_dynamics(q, v, a)

##### compute_forward_dynamics
```python
def compute_forward_dynamics(self: Any, q: Any, v: Any, tau: Any) -> np.ndarray
```

Compute forward dynamics (ABA) using Pinocchio.

Computes joint accelerations from applied torques.

Args:
    q: Joint positions (if None, uses current MuJoCo state)
    v: Joint velocities (if None, uses current MuJoCo state)
    tau: Joint torques (if None, uses zero torques)

Returns:
    Joint accelerations [nv]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> # Option 1: Use None to auto-convert from MuJoCo state
    >>> tau = np.zeros(model.nu)
    >>> a = wrapper.compute_forward_dynamics(None, None, tau)
    >>> # Option 2: Manually convert quaternions if passing q explicitly
    >>> q = wrapper._mujoco_q_to_pinocchio_q(data.qpos.copy())
    >>> v = data.qvel.copy()
    >>> a = wrapper.compute_forward_dynamics(q, v, tau)

##### compute_mass_matrix
```python
def compute_mass_matrix(self: Any, q: Any) -> np.ndarray
```

Compute mass matrix using Pinocchio.

Args:
    q: Joint positions (if None, uses current MuJoCo state)

Returns:
    Mass matrix [nv x nv]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> M = wrapper.compute_mass_matrix()

##### compute_coriolis_matrix
```python
def compute_coriolis_matrix(self: Any, q: Any, v: Any) -> np.ndarray
```

Compute Coriolis matrix using Pinocchio.

Args:
    q: Joint positions (if None, uses current MuJoCo state)
    v: Joint velocities (if None, uses current MuJoCo state)

Returns:
    Coriolis matrix [nv x nv]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> C = wrapper.compute_coriolis_matrix()

##### compute_gravity_vector
```python
def compute_gravity_vector(self: Any, q: Any) -> np.ndarray
```

Compute gravity vector using Pinocchio.

Args:
    q: Joint positions (if None, uses current MuJoCo state)

Returns:
    Gravity vector [nv]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> g = wrapper.compute_gravity_vector()

##### compute_end_effector_jacobian
```python
def compute_end_effector_jacobian(self: Any, frame_name: str, q: Any) -> np.ndarray
```

Compute end-effector Jacobian using Pinocchio.

Args:
    frame_name: Name of the end-effector frame (e.g., "club_head")
    q: Joint positions (if None, uses current MuJoCo state)
    local: If True, returns local Jacobian. If False, returns world Jacobian.

Returns:
    Jacobian matrix [6 x nv] (linear and angular)

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> J = wrapper.compute_end_effector_jacobian("club_head")

##### compute_dynamics_derivatives
```python
def compute_dynamics_derivatives(self: Any, q: Any, v: Any, tau: Any) -> tuple[Any]
```

Compute analytical derivatives of dynamics.

Computes ∂f/∂q, ∂f/∂v, ∂f/∂τ, ∂f/∂u (for control).

Args:
    q: Joint positions (if None, uses current MuJoCo state)
    v: Joint velocities (if None, uses current MuJoCo state)
    tau: Joint torques (if None, uses zero torques)

Returns:
    Tuple of (df_dq, df_dv, df_dtau, df_du) derivatives

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> df_dq, df_dv, df_dtau, df_du = wrapper.compute_dynamics_derivatives()

##### compute_kinetic_energy
```python
def compute_kinetic_energy(self: Any, q: Any, v: Any) -> float
```

Compute kinetic energy using Pinocchio.

Args:
    q: Joint positions (if None, uses current MuJoCo state)
    v: Joint velocities (if None, uses current MuJoCo state)

Returns:
    Kinetic energy [J]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> KE = wrapper.compute_kinetic_energy()

##### compute_potential_energy
```python
def compute_potential_energy(self: Any, q: Any) -> float
```

Compute potential energy using Pinocchio.

Args:
    q: Joint positions (if None, uses current MuJoCo state)

Returns:
    Potential energy [J]

Example:
    >>> wrapper = PinocchioWrapper(model, data)
    >>> PE = wrapper.compute_potential_energy()

## Constants

- `PINOCCHIO_AVAILABLE`
- `PINOCCHIO_AVAILABLE`
