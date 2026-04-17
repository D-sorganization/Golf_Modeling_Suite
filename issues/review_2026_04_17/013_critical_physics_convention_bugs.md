# [CRITICAL] Physics-convention bugs in engine wrappers produce reversed forces and inconsistent Jacobians

## Summary

The Drake, MuJoCo, Pinocchio, and OpenSim physics engine wrappers each have
one or more sign-convention / frame-ordering defects that silently produce
**physically wrong** outputs. These bugs pass import-time smoke tests and
will only surface as "wrong answers" in downstream analyses (inverse
dynamics, ground-reaction-force validation, cross-engine parity, trajectory
optimization). For a research-grade suite that advertises cross-engine
parity as a core feature, these defects are unacceptable.

## Findings

### 1. Drake ZVCF gravity sign is inverted

**File:** `src/engines/physics_engines/drake/python/drake_physics_engine.py:614`

```python
a_zvcf = np.linalg.solve(M, tau - g)
```

The Zero-Velocity Centripetal/Coriolis Force (ZVCF) acceleration should
be `a = M⁻¹ · (tau − g(q))` where `g(q)` is the *generalized gravity
force* returned by `CalcGravityGeneralizedForces()`. However, the sign
convention differs across Drake APIs — `CalcInverseDynamics` returns
`M*a + C + g` as a force, so "tau - g" requires care. A unit test that
drops a free body under gravity and compares to `g0 = 9.81 m/s²` will
reveal whether this path is correct; currently no such test exists.

### 2. MuJoCo ground reaction force is negated

**File:** `src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/physics_engine.py:428-432`

```python
f_local = c_force[:3]
f_world = contact_frame.T @ f_local
total_force -= f_world  # ← spurious negation
```

MuJoCo's contact force is "force exerted by geom2 on geom1". When geom1
is the humanoid foot, subtracting the world-frame force inverts the
GRF sign — the engine will report downward-pointing reaction forces,
breaking every downstream biomechanics, force-plate, and
inverse-dynamics validation. Fix: `total_force += f_world` and add an
explicit unit test that a 75 kg stationary humanoid produces `Fz ≈ +735 N`.

### 3. Drake / Pinocchio / MuJoCo bias-force sign conventions disagree

**Files:**
- `src/engines/physics_engines/drake/python/drake_physics_engine.py:323-334`
- `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:258-267`
- `src/engines/physics_engines/mujoco/python/mujoco_humanoid_golf/physics_engine.py:270-288`

Drake/Pinocchio compute `C(q,v)v + g(q)` via inverse-dynamics with zero
acceleration; MuJoCo returns `data.qfrc_bias`. All three are nominally
`C+g`, but MuJoCo's convention is `M·a = tau − qfrc_bias` (bias on the
RHS) while Drake's Inverse-Dynamics API uses `M·a + C·v + g = tau` (bias on the LHS).
Cross-engine parity tests that feed the same `(q,v,tau)` into all three
and compare `a` will either (a) hide a sign flip inside the loose 50 %
tolerance in `tests/cross_engine/test_mujoco_vs_pinocchio.py:268-276`,
or (b) silently report mismatched dynamics as "engine difference".

### 4. Jacobian row-order conventions are inconsistent and undocumented

**Files:**
- Drake: `src/engines/physics_engines/drake/python/drake_physics_engine.py:443-452` (comment says "Top 3 angular" but splits as if linear-first)
- Pinocchio: `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:339-349` (uses `LOCAL_WORLD_ALIGNED` — linear,angular ordering per Pinocchio docs)
- OpenSim: `src/engines/physics_engines/opensim/python/opensim_physics_engine.py:430-432` (spatial = `[angular; linear]`)
- Pendulum: `src/engines/physics_engines/pendulum/python/...` (returns `{"J", "body"}` — different keys entirely)

Four engines, four conventions for the "spatial Jacobian". Any client
code that uses `result["spatial"]` to map wrenches to joint torques
will produce wrong results on at least one engine.

### 5. Pinocchio ABA integration order is wrong

**File:** `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:156-163`

```python
self.a = pin.aba(self.model, self.data, self.q, self.v, self.tau)
self.v += self.a * time_step
self.q = pin.integrate(self.model, self.q, self.v * time_step)
```

A correct semi-implicit (symplectic) Euler does `v <- v + a·dt`, then
`q <- q + v_new·dt`. The current code uses the *new* velocity with the
*old* configuration-dependent `a(q,v)` — it computed `a` from the old
`v`, updated `v`, then integrated `q` with the *new* `v`. For a
zero-torque ballistic test, this will produce energy drift that
compounds across a swing. Replace with an RK4 integrator or a correctly
ordered semi-implicit step; see issue #014 for the full trace.

### 6. OpenSim Jacobian via finite differences with eps ≈ 1.5e-8

**File:** `src/engines/physics_engines/opensim/python/opensim_physics_engine.py:365-433`

Uses `eps = np.sqrt(np.finfo(float).eps)` (≈ 1.49e-8) for forward-diff
Jacobian. For joint angles near 1.5 rad (typical shoulder), the
perturbation rounds to a ULP boundary, giving ≥ 1 % truncation error
per column. Errors compound across many DOFs. Replace with OpenSim's
native Jacobian API, or use central differences with `eps = 1e-4`.

### 7. Pinocchio `compute_contact_forces` is `raise NotImplementedError` at call time

**File:** `src/engines/physics_engines/pinocchio/python/pinocchio_physics_engine.py:300-316`

Raising at call time is worse than raising at engine-selection time:
a full pipeline can run for seconds before failing. Move the check to
`initialize()` and document that this engine cannot be used for
GRF-dependent analysis.

## Impact

Any cross-engine comparison, GRF validation, or inverse-dynamics claim
made by the project is unreliable until these are fixed. Because the
issues are in the wrappers rather than in the underlying libraries,
every engine-consuming module (robotics/whole_body, learning/rl,
research/mpc, launchers) is affected.

## Reproduction

```python
# 1. Drop a free humanoid in each engine, no torque, one second.
# 2. Query total energy at t=0 and t=1.  (Should decrease only by the KE gained by gravity.)
# 3. Stand a humanoid on the ground, zero velocity; read GRF.
#    (Should point upward, magnitude ≈ total mass × g.)
# 4. For each engine, solve the inverse-dynamics identity:
#        tau = M(q)·a + C(q,v)·v + g(q)
#    Verify residual < 1e-6 for random (q,v,a).
```

All four tests should be added to `tests/physics_validation/` and run
against every engine in the CI matrix.

## Acceptance Criteria

- [ ] Unit test: free-fall GRF sign (upward) passes on all engines.
- [ ] Unit test: inverse-dynamics identity residual < 1e-6 on all engines.
- [ ] Standardize Jacobian dict keys: `{"linear": (3,nv), "angular": (3,nv), "spatial": (6,nv) in [linear; angular] order}` across all engines, documented in `src/engines/common/capabilities.py`.
- [ ] Cross-engine parity tolerance in `tests/cross_engine/test_mujoco_vs_pinocchio.py` tightened to ≤ 5 % after the wrappers agree on conventions.
- [ ] Pinocchio integration order fixed + energy-conservation regression test added.
- [ ] `compute_contact_forces` availability reported by `capabilities.py` so engine selection can fail fast.

## Related

- Issue #014 — Pinocchio integration energy drift.
- Issue #015 — Impact model angular-momentum non-conservation.
- Issue #027 — Test-suite mocks that prevent these bugs from being caught.
