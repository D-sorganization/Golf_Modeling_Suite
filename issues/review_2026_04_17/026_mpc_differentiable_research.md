# [HIGH] MPC, differentiable physics, multi-robot coordination, deformables — correctness gaps

## Summary

`src/research/mpc/`, `src/research/differentiable/`,
`src/research/multi_robot/`, `src/research/deformable/`, and
`src/reinforcement_learning/trajectory_funnel_benchmark.py` contain
research-oriented algorithms. A number of them have correctness
defects that would silently produce wrong answers without any test
surface to catch them.

## Findings

### MPC

### 1. Dynamics linearization method signature appears truncated

`src/research/mpc/controller.py:251-308` — `_dynamics()` is nonlinear
and `_dynamics_linearize()` is invoked but its body is not visible in
the file. MPC optimizes a linearized model built from an unknown-state
linearization; if this is missing the result is meaningless.

### 2. No infeasibility propagation

`controller.py:299-308` — the solver returns `success=True` without
checking constraint feasibility. `MPCResult` has a
`constraint_violations` field that is never populated.

### 3. Cost matrices not validated positive-definite

`controller.py:70` — no eigenvalue check on `Q`, `R`. Solver can
diverge on indefinite costs.

### 4. Specialized MPC hardcodes `n_x = 9, n_contacts = 2`

`src/research/mpc/specialized.py:73-75` — hard-coded for a specific
humanoid. No assertion that the model matches.

### 5. Gravity sign suspicious in specialized MPC

`specialized.py:79` — `np.array([0, 0, -GRAVITY])` where GRAVITY is
a positive constant; this is fine only if the convention is z-up.
No check.

### 6. Euler integration without acceleration bounds

`specialized.py:176` — `com_new = com + com_vel · dt` with no
adaptive step or warning if acceleration is large. Trajectory
diverges silently.

### 7. Friction-cone constraint linearized around the origin, not relinearized

`specialized.py:182-213` — linearization is static. As the CoM moves,
the linearization becomes inaccurate; no relinearization step in the
solver loop.

### Differentiable physics

### 8. Finite-difference epsilon is fixed at 1e-5 for all dimensions

`src/research/differentiable/engine.py:175-189` — for an n-dim state
with widely varying scales, fixed epsilon yields catastrophic
cancellation in some dims and truncation in others. Use per-dim
scaled epsilon.

### 9. Silent fallback to identity integration if engine lacks `get_joint_*`

`engine.py:112-146` — if the wrapped engine doesn't expose the
expected methods, `simulate_trajectory()` uses the identity —
garbage-in, garbage-out. Should raise.

### 10. Gradient is taken only w.r.t. controls

`engine.py:148-189` — trajectory optimization needs gradients w.r.t.
initial state and parameters as well. Missing.

### 11. Inconsistent epsilon between state and control Jacobians

`engine.py:249-264` — state-Jac uses `1e-4`, control-Jac uses
something different (not shown). Result: inconsistent differentiation.

### Multi-robot / deformable / RL benchmark

### 12. Quaternion-to-rotation matrix is cut off / incomplete

`src/research/multi_robot/coordination.py:225-250` — visible code
stops mid-matrix.

### 13. Quaternion-to-rotation does not normalize input

`coordination.py:196` — unnormalized quaternions produce non-
orthogonal rotation matrices.

### 14. Deformable shape matrices computed but not used

`src/research/deformable/objects.py:211` — `_B_matrices` computed;
`compute_internal_forces()` never reads them.

### 15. Tet mesh not validated (negative volumes pass through)

`objects.py:233` — no check for inverted elements → NaN in FEM.

### 16. Trajectory-funnel reward: empty reference silently returns 0

`src/reinforcement_learning/trajectory_funnel_benchmark.py:52, 56` —
`np.argmin` on empty array returns 0; phase-velocity term has a
discontinuity at wraparound.

## Impact

MPC cannot be claimed as a reliable controller; differentiable
physics cannot be trained through end-to-end; deformable model will
produce NaNs; multi-robot coordination is not covered by tests.

## Acceptance Criteria

- [ ] Complete and unit-test `MPCController._dynamics_linearize`.
- [ ] MPC raises `MPCInfeasibleError` on detected constraint violations;
      populate `MPCResult.constraint_violations`.
- [ ] Assert `Q ≽ 0, R ≻ 0` on solver init.
- [ ] Remove hard-coded `n_x`/`n_contacts`; derive from model.
- [ ] Unit test gravity sign convention explicitly.
- [ ] Add adaptive step or fail-safe to MPC's Euler integration.
- [ ] Relinearize friction cone each MPC step; document frequency.
- [ ] Per-dimension scaled epsilon in finite-difference Jacobians.
- [ ] Differentiable engine raises on missing joint APIs.
- [ ] Extend finite-diff gradients to `x0` and parameters.
- [ ] Unified epsilon (or scaled epsilons) between state and control Jacs.
- [ ] Complete and unit-test the quaternion → rotation function with
      non-unit inputs.
- [ ] Use `_B_matrices` in `compute_internal_forces` (with reference).
- [ ] Validate tetrahedral mesh on load; raise on inverted elements.
- [ ] Trajectory-funnel reward rejects empty references; guard
      wraparound discontinuity.

## Related

- Issue #025 — broader learning-stack issues.
- Issue #013 — physics-convention bugs at the engine layer propagate
  into these modules.
