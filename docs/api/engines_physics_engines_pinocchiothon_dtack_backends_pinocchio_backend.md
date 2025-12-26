# engines.physics_engines.pinocchiothon.dtack.backends.pinocchio_backend

Pinocchio backend wrapper for dynamics computations.

## Classes

### PinocchioBackend

Pinocchio backend for forward/inverse dynamics and kinematics.

This backend provides:
- URDF model loading
- Forward dynamics (ABA)
- Inverse dynamics (RNEA)
- Mass matrix computation (CRBA)
- Jacobian computation
- Frame placement updates

#### Methods

##### compute_inverse_dynamics
```python
def compute_inverse_dynamics(self: Any, q: npt.NDArray[np.float64], v: npt.NDArray[np.float64], a: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Compute inverse dynamics (RNEA).

Args:
    q: Joint positions [nq]
    v: Joint velocities [nv]
    a: Joint accelerations [nv]

Returns:
    Joint torques [nv]

##### compute_forward_dynamics
```python
def compute_forward_dynamics(self: Any, q: npt.NDArray[np.float64], v: npt.NDArray[np.float64], tau: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Compute forward dynamics (ABA).

Args:
    q: Joint positions [nq]
    v: Joint velocities [nv]
    tau: Joint torques [nv]

Returns:
    Joint accelerations [nv]

##### compute_mass_matrix
```python
def compute_mass_matrix(self: Any, q: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Compute mass matrix (CRBA).

Args:
    q: Joint positions [nq]

Returns:
    Mass matrix [nv x nv]

##### compute_bias_forces
```python
def compute_bias_forces(self: Any, q: npt.NDArray[np.float64], v: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Compute bias forces (gravity + Coriolis + centrifugal).

Args:
    q: Joint positions [nq]
    v: Joint velocities [nv]

Returns:
    Bias forces [nv]

##### compute_frame_jacobian
```python
def compute_frame_jacobian(self: Any, q: npt.NDArray[np.float64], frame_id: Any, reference_frame: int) -> npt.NDArray[np.float64]
```

Compute frame Jacobian.

Args:
    q: Joint positions [nq]
    frame_id: Frame ID (int) or frame name (str)
    reference_frame: Reference frame for Jacobian

Returns:
    Jacobian matrix [6 x nv]

##### forward_kinematics
```python
def forward_kinematics(self: Any, q: npt.NDArray[np.float64]) -> list[pin.SE3]
```

Compute forward kinematics for all frames.

Args:
    q: Joint positions [nq]

Returns:
    List of frame placements

### DummyPin

Dummy class to prevent NameError when Pinocchio is missing.

Any attribute or method access raises ImportError with a clear message.

#### Methods

### ReferenceFrame

Dummy ReferenceFrame enum.

#### Methods

### SE3

Dummy SE3 class.

#### Methods

## Constants

- `PINOCCHIO_AVAILABLE`
- `PINOCCHIO_AVAILABLE`
- `LOCAL_WORLD_ALIGNED`
