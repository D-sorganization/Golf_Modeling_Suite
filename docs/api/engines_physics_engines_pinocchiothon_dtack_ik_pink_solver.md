# engines.physics_engines.pinocchiothon.dtack.ik.pink_solver

Inverse Kinematics solver using Pink.

## Classes

### SolverSettings

Settings for the IK solver.

### PinkSolver

Inverse Kinematics solver wrapper for Pink.

#### Methods

##### solve
```python
def solve(self: Any, q_init: np.ndarray, tasks: list[Task], dt: float, settings: Any) -> np.ndarray
```

Solve differential IK for one step.

Args:
    q_init: Current joint configuration
    tasks: List of Pink tasks to satisfy (e.g. FrameTask, PostureTask)
    dt: Time step for velocity integration
    settings: Solver settings (algorithm, damping)

Returns:
    New joint configuration q_next
