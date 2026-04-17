# [HIGH] Pinocchio and pendulum integration need calibrated energy-regression coverage

## Summary

The Pinocchio physics wrapper uses a standard semi-implicit Euler step,
but the repository does not appear to have a calibrated, engine-wide
energy-regression baseline that validates it under the swing conditions
this project cares about. The Drake motion-optimization path and the
pendulum RK4 path have related coverage gaps. Together, these weaken the
suite's ability to perform hours-long training runs or multi-engine
parity comparisons.

## Findings

### 1. Energy drift is unbounded by a per-engine regression

`src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:156-163`

The current update is the standard semi-implicit (symplectic) Euler
form: compute `a = aba(q_n, v_n)`, update `v_{n+1} = v_n + a·dt`, then
integrate `q_{n+1}` from `v_{n+1}`. That is not itself a defect. The
gap is that this integrator does not appear to be exercised by a
calibrated energy-conservation regression for the swing scenarios this
repository targets, so the acceptable drift budget is effectively
unreviewed.

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

- [ ] Add a 10-s ballistic free-fall energy-conservation test to `tests/physics_validation/test_energy_conservation.py` and run it on Drake, MuJoCo, Pinocchio, OpenSim.
- [ ] Add an `integrator: Literal["semi_implicit", "rk4", "implicit_euler"]` parameter to the common `step()` API.
- [ ] Pendulum RK4 must sample torque `τ(t + c_i · dt)` correctly at each Butcher-tableau stage.
- [ ] Document the per-engine integrator in `docs/engines/` with accuracy vs. step-size tables.

## Related

- Issue #013 — other physics-convention bugs.
- Issue #028 — missing validation tests.
