# engines.physics_engines.pinocchiothon.dtack.backends.pink_backend

PINK backend wrapper for inverse kinematics.

## Classes

### PINKBackend

PINK backend for inverse kinematics.

This backend provides:
- IK task definition
- Closed-loop IK solving
- Task-space control

#### Methods

##### solve_ik
```python
def solve_ik(self: Any, _tasks: dict[Any], _q_init: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]
```

Solve inverse kinematics for given tasks.

Args:
    tasks: Dictionary of task names to target poses/positions
    q_init: Initial joint configuration

Returns:
    Joint configuration satisfying tasks

## Constants

- `PINK_AVAILABLE`
- `PINK_AVAILABLE`
