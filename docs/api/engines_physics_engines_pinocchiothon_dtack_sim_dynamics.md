# engines.physics_engines.pinocchiothon.dtack.sim.dynamics

Dynamics simulation and counterfactual analysis.

## Classes

### DynamicsEngine

Wrapper for Pinocchio dynamics algorithms.

#### Methods

##### forward_dynamics
```python
def forward_dynamics(self: Any, q: np.ndarray, v: np.ndarray, tau: np.ndarray, f_ext: Any) -> np.ndarray
```

Compute forward dynamics (FD).

Equation: M(q)a + C(q,v)v + g(q) = tau + J^T f_ext
Returns: a (acceleration)

Args:
    q: Joint configuration
    v: Joint velocity
    tau: Joint torques
    f_ext: External forces (optional)

Returns:
    Joint acceleration 'a'

##### inverse_dynamics
```python
def inverse_dynamics(self: Any, q: np.ndarray, v: np.ndarray, a: np.ndarray, f_ext: Any) -> np.ndarray
```

Compute inverse dynamics (ID).

Returns: tau (torque)

##### compute_ztcf
```python
def compute_ztcf(self: Any, q: np.ndarray, v: np.ndarray, dt: float) -> tuple[Any]
```

Compute Zero Torque Counterfactual (ZTCF).

Simulates one step with tau=0.
Represents pure passive dynamics (drift).

Returns:
    (q_next, v_next)

##### compute_zvcf
```python
def compute_zvcf(self: Any, q: np.ndarray, tau: np.ndarray, dt: float) -> tuple[Any]
```

Compute Zero Velocity Counterfactual (ZVCF).

Computes acceleration assuming v=0 (no Coriolis/Centrifugal/Damping).
Represents pure control authority + static gravity.

Returns:
    (q_next, v_next) starting from v=0
