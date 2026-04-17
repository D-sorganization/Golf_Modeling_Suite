# [HIGH] Pinocchio integration order + RK4 correctness break energy conservation for long swings

## Summary

The Pinocchio physics wrapper integrates rigid-body dynamics with an
out-of-order semi-implicit Euler step that accumulates energy error
across a multi-second golf swing. The Drake motion-optimization path
and the pendulum RK4 path have related defects. Together, these break
the suite's ability to perform hours-long training runs or
multi-engine parity comparisons.

## Findings

### 1. Out-of-order semi-implicit step

`src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:156-163`

The step computes `a = aba(q_n, v_n)`, then updates `v_{n+1} = v_n + a·dt`,
then `q_{n+1} = integrate(q_n, v_{n+1}·dt)`. A correct symplectic Euler
is fine, but this mixes orders: it uses the **new** velocity to
integrate the old configuration. Over a 1-second downswing with
high accelerations the energy drift is O(10 %) on a simple pendulum
(easy to confirm with `tests/physics_validation/test_pendulum_accuracy.py`
after tightening its current 20 % tolerance, see issue #027).

### 2. No implicit-integration option

No `implicit_euler`, `midpoint`, or `rk4` alternative is exposed on
`PinocchioPhysicsEngine.step()`. For stiff joint friction or for
training loops that need time-reversibility, this is a hard blocker.
A single `integrator="rk4"` kwarg pushed through the step() contract
in `src/engines/common/physics.py` would be sufficient.

### 3. Pendulum RK4 evaluates k4 at the wrong time when torque is time-varying

`src/engines/physics_engines/pendulum/python/golf_swing_physics_engine.py:221-263`

The torque closure captures `self._tau` at call time. For constant-torque
use-cases this is correct, but swing controllers will set `tau = τ(t)`;
the current implementation uses the old `τ` at `t + dt`, which biases
`k4` and produces systematic error in the driven swing.

### 4. No energy-conservation regression in CI

`tests/physics_validation/test_energy_conservation.py:83, 179` allows
0.05 J drift with semi-implicit Euler. No baseline is enforced; the
drift threshold has no derivation, and the test does not run on the
Pinocchio wrapper at all.

## Impact

Everything downstream that relies on the integrator being
energy-faithful is suspect: RL environments (`src/learning/rl/`)
reset-to-state and rollout reproducibility; MPC warm-start; motion
optimization (`src/engines/physics_engines/drake/python/motion_optimization.py`);
long-horizon trajectory prediction for launch-monitor calibration.

## Reproduction

```python
from src.engines.physics_engines.pinocchio.python.pinocchio_physics_engine import (
    PinocchioPhysicsEngine,
)

eng = PinocchioPhysicsEngine()
eng.load_from_path("src/shared/urdf/simple_humanoid.urdf")
eng.set_state(q0, v0)

E0 = eng.total_energy()
for _ in range(10_000):
    eng.step(dt=1e-3)  # 10 s of simulation
E = eng.total_energy()

assert abs(E - E0) / abs(E0) < 1e-3, f"drift: {(E-E0)/E0:.3%}"  # currently fails
```

## Acceptance Criteria

- [ ] Fix the integration order in `PinocchioPhysicsEngine.step()` to be correctly symplectic *or* swap to RK4 by default.
- [ ] Add a 10-s ballistic free-fall energy-conservation test to `tests/physics_validation/test_energy_conservation.py` and run it on Drake, MuJoCo, Pinocchio, OpenSim.
- [ ] Add an `integrator: Literal["semi_implicit", "rk4", "implicit_euler"]` parameter to the common `step()` API.
- [ ] Pendulum RK4 must sample torque `τ(t + c_i · dt)` correctly at each Butcher-tableau stage.
- [ ] Document the per-engine integrator in `docs/engines/` with accuracy vs. step-size tables.

## Related

- Issue #013 — other physics-convention bugs.
- Issue #028 — missing validation tests.
