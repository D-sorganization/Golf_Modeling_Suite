# engines.physics_engines.pinocchiothon.pinocchio_golf.induced_acceleration

## Classes

### InducedAccelerationAnalyzer

Analyzes induced accelerations (Gravity, Velocity, Control) for a Pinocchio model.
Based on the equation of motion: M(q)q_ddot + C(q, q_dot)q_dot + G(q) = tau

Induced Accelerations:
- Gravity: q_ddot_g = -M^(-1) * G(q)
- Velocity (Coriolis/Centrifugal): q_ddot_v = -M^(-1) * C(q, q_dot)q_dot
- Control (Torque): q_ddot_t = M^(-1) * tau
- Total: q_ddot = q_ddot_g + q_ddot_v + q_ddot_t

#### Methods

##### compute_components
```python
def compute_components(self: Any, q: np.ndarray, v: np.ndarray, tau: np.ndarray) -> dict[Any]
```

Compute induced acceleration components.

Args:
    q: Joint configurations
    v: Joint velocities
    tau: Joint torques

Returns:
    Dictionary with keys 'gravity', 'velocity', 'control', 'total'
    mapping to acceleration arrays.
