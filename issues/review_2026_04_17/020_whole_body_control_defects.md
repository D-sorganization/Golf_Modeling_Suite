# [CRITICAL] Whole-body controller: no damped pseudo-inverse, broken hierarchical QP, silent QP failures

## Summary

`src/robotics/control/whole_body/wbc_controller.py` is the core
controller for humanoid-under-contact. Three defects make it unsafe
for fast arm motion: the pseudo-inverse is undamped, the hierarchical
QP does not filter lower-priority tasks by accumulated higher-priority
constraints, and QP infeasibility is swallowed silently. A fast golf
downswing passes through multiple arm singularities and generates
large accelerations that will trip all three.

## Findings

### 1. Undamped pseudo-inverse in nullspace projector

`src/robotics/control/whole_body/wbc_controller.py:802`

```python
N = np.eye(n) - A.T @ np.linalg.pinv(A.T)
```

`np.linalg.pinv` with default tolerance blows up near singularities,
producing extreme joint accelerations. Replace with damped
least-squares: `N = I − A.T (A A.T + λ² I)⁻¹ A` with `λ = 1e-3` or
adaptive based on the smallest singular value. Add a unit test that
the nullspace projector has unit operator norm near a singularity.

### 2. Hierarchical QP does not accumulate constraints

`src/robotics/control/whole_body/wbc_controller.py:393-414, 440-444`

The HQP loop stacks Jacobians per-priority but never uses
`accumulated_A` to filter tasks at lower priorities. Priority-3 tasks
can override priority-1 tasks. This is not hierarchical control —
it's weighted multi-objective QP with a soft priority.

**Fix:** use Kanoun-style projection: task `i` is projected into
`N_{i−1} = N_{i−2} · (I − A_{i−1}⁺ A_{i−1})`, and the constraint
`A_i · x = b_i` is solved in the image of `N_{i−1}`.

### 3. QP infeasibility is swallowed

`src/robotics/control/whole_body/wbc_controller.py:364-366, 409-414, 670-676`

On solver failure, `success=False` is set but `_extract_solution`
returns zero accelerations. The controller will command "hold still"
exactly when it most needs error escalation. Propagate infeasibility
out of the controller (logged at WARNING with the offending task
constraints) and let the calling layer decide whether to fall back.

### 4. Contact-point Jacobian time-derivative term is ignored

`src/robotics/control/whole_body/task.py:342-375`

`create_contact_constraint()` sets contact acceleration to zero
(`J·qdd = 0`) assuming stationary contact. In a fast swing with
end-effector Jacobian time-derivative `J̇`, the correct constraint
is `J·qdd + J̇·v = 0`. Missing this term lets the controller command
accelerations that break non-slip contact on paper, producing
unphysical forces.

### 5. Jacobian column-width mismatch is silently dropped

`src/robotics/control/whole_body/wbc_controller.py:311-331` — if
`J.shape[1] != n_v` the loop `continue`s without raising. Tasks
silently disappear; user sees "controller succeeded" with a tracking
error they cannot explain.

### 6. Acceleration bounds can invert sign on velocity reversal

`src/robotics/control/whole_body/wbc_controller.py:632-638`

```python
qdd_lb_from_v = (-v_lim - qd) / dt
qdd_ub_from_v = ( v_lim - qd) / dt
```

When the joint is at positive velocity and we want to brake hard,
`qdd_lb_from_v` is correctly negative, but if `qd > v_lim` (e.g., a
perturbation pushed us outside the bound already) the lower bound is
further negative than the upper, which can flip the inequality.

### 7. Max contact normal force is hard-coded to 10 000 N

`src/robotics/control/whole_body/wbc_controller.py:641-644`

Real foot-ground reaction peaks are ~2× bodyweight (~1500 N) for
walking and ~4× for impacts. The 10 000 N bound is effectively
unlimited — it is there only to give the QP a finite box. Make it
`max_normal_force_N: float` parameter or compute it from surface
properties.

### 8. Golf-swing-specific missing controllers

The robotics subsystem contains a whole-body controller intended for
walking humanoids. For a golf swing:

- There is **no static-stance** gait that holds feet planted (Issue #022).
- There is **no redundancy resolution** that prioritises clubhead
  trajectory over elbow-flexion comfort.
- There is **no impact-transition** logic. `WholeBodyController`
  cannot handle the instant a club contacts a ball.

## Impact

Any experiment that drives a humanoid through a fast swing using the
WBC stack is at risk of instability. Because the QP failures are silent,
experiments that "work" might be producing zero-torque dummies.

## Acceptance Criteria

- [ ] Replace bare pseudo-inverse with damped least-squares; unit
      test with a near-singular Jacobian.
- [ ] Re-implement hierarchical QP using accumulated nullspace
      projections; regression test: priority-1 task tracks to
      tolerance even when priority-3 task pulls opposite.
- [ ] QP infeasibility raises `WBCInfeasibleError` (new class in
      `src/robotics/core/exceptions.py`); caller has to handle it.
- [ ] Add `J̇·v` term to contact-constraint targets and regression
      test on a moving end-effector.
- [ ] Raise on Jacobian column-width mismatch.
- [ ] Add a `SwingStanceTask` (feet pinned, no ZMP walking gait) and
      a `ClubPathTask` (primary) with arm-comfort secondary.
- [ ] Parametrize `max_contact_normal_force` per task / per contact.

## Related

- Issue #021 — contact / friction-cone defects.
- Issue #022 — ZMP / gait mismatch with golf stance.
- Issue #013 — Jacobian convention inconsistency.
