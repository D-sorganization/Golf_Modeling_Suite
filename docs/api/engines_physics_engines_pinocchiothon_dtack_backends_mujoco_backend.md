# engines.physics_engines.pinocchiothon.dtack.backends.mujoco_backend

MuJoCo backend wrapper for simulation and contact dynamics.

## Classes

### MuJoCoBackend

MuJoCo backend for forward simulation and contact dynamics.

This backend provides:
- MJCF model loading
- Forward simulation with contacts
- Contact force computation
- Sensor data access
- Forward/inverse dynamics via MuJoCo

#### Methods

##### step
```python
def step(self: Any, ctrl: Any) -> None
```

Step simulation forward.

Args:
    ctrl: Control input [nu]. If None, uses current data.ctrl

##### forward
```python
def forward(self: Any) -> None
```

Compute forward dynamics without stepping.

##### get_qpos
```python
def get_qpos(self: Any) -> npt.NDArray[np.float64]
```

Get joint positions.

Returns:
    Joint positions [nq]

##### get_qvel
```python
def get_qvel(self: Any) -> npt.NDArray[np.float64]
```

Get joint velocities.

Returns:
    Joint velocities [nv]

##### get_qacc
```python
def get_qacc(self: Any) -> npt.NDArray[np.float64]
```

Get joint accelerations.

Returns:
    Joint accelerations [nv]

##### set_qpos
```python
def set_qpos(self: Any, q: npt.NDArray[np.float64]) -> None
```

Set joint positions.

Args:
    q: Joint positions [nq]

##### set_qvel
```python
def set_qvel(self: Any, v: npt.NDArray[np.float64]) -> None
```

Set joint velocities.

Args:
    v: Joint velocities [nv]

##### compute_inverse_dynamics
```python
def compute_inverse_dynamics(self: Any, q: npt.NDArray[np.float64], v: npt.NDArray[np.float64], a: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Compute inverse dynamics.

Args:
    q: Joint positions [nq]
    v: Joint velocities [nv]
    a: Joint accelerations [nv]

Returns:
    Joint torques [nv]

##### get_contact_forces
```python
def get_contact_forces(self: Any) -> npt.NDArray[np.float64]
```

Get contact forces.

Returns:
    Contact forces [ncon * 6] (force + torque for each contact)
